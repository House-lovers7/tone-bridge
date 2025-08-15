package services

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
	"go.uber.org/zap"
	lru "github.com/hashicorp/golang-lru/v2"
)

type CacheService struct {
	redis      *redis.Client
	localCache *lru.Cache[string, []byte]
	logger     *zap.SugaredLogger
	ttl        time.Duration
}

func NewRedisClient(redisURL string) *redis.Client {
	opt, err := redis.ParseURL(redisURL)
	if err != nil {
		opt = &redis.Options{
			Addr:     redisURL,
			Password: "",
			DB:       0,
		}
	}
	
	client := redis.NewClient(opt)
	
	// Test connection
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	
	if err := client.Ping(ctx).Err(); err != nil {
		// Redis not available, will use local cache only
		return nil
	}
	
	return client
}

func NewCacheService(redisClient *redis.Client, logger *zap.SugaredLogger) *CacheService {
	// Create local LRU cache as L1 cache
	localCache, _ := lru.New[string, []byte](10000) // 10k items
	
	return &CacheService{
		redis:      redisClient,
		localCache: localCache,
		logger:     logger,
		ttl:        5 * time.Minute,
	}
}

// Get retrieves a value from cache (L1 -> L2)
func (s *CacheService) Get(key string) ([]byte, error) {
	// Check L1 cache first
	if value, ok := s.localCache.Get(key); ok {
		s.logger.Debugf("Cache hit (L1): %s", key)
		return value, nil
	}
	
	// Check L2 cache (Redis) if available
	if s.redis != nil {
		ctx := context.Background()
		value, err := s.redis.Get(ctx, key).Bytes()
		if err == nil {
			s.logger.Debugf("Cache hit (L2): %s", key)
			// Update L1 cache
			s.localCache.Add(key, value)
			return value, nil
		}
		if err != redis.Nil {
			s.logger.Warnf("Redis error: %v", err)
		}
	}
	
	s.logger.Debugf("Cache miss: %s", key)
	return nil, fmt.Errorf("cache miss")
}

// Set stores a value in cache (L1 + L2)
func (s *CacheService) Set(key string, value []byte, ttl time.Duration) error {
	// Store in L1 cache
	s.localCache.Add(key, value)
	
	// Store in L2 cache (Redis) if available
	if s.redis != nil {
		ctx := context.Background()
		if ttl == 0 {
			ttl = s.ttl
		}
		err := s.redis.Set(ctx, key, value, ttl).Err()
		if err != nil {
			s.logger.Warnf("Failed to set Redis cache: %v", err)
			// Don't return error as L1 cache is still working
		}
	}
	
	s.logger.Debugf("Cache set: %s (ttl: %v)", key, ttl)
	return nil
}

// Delete removes a value from cache
func (s *CacheService) Delete(key string) error {
	// Remove from L1 cache
	s.localCache.Remove(key)
	
	// Remove from L2 cache (Redis) if available
	if s.redis != nil {
		ctx := context.Background()
		err := s.redis.Del(ctx, key).Err()
		if err != nil {
			s.logger.Warnf("Failed to delete from Redis: %v", err)
		}
	}
	
	s.logger.Debugf("Cache deleted: %s", key)
	return nil
}

// Clear removes all values from cache
func (s *CacheService) Clear() error {
	// Clear L1 cache
	s.localCache.Purge()
	
	// Clear L2 cache (Redis) if available
	if s.redis != nil {
		ctx := context.Background()
		err := s.redis.FlushDB(ctx).Err()
		if err != nil {
			s.logger.Warnf("Failed to clear Redis: %v", err)
		}
	}
	
	s.logger.Info("Cache cleared")
	return nil
}

// GetJSON retrieves and unmarshals a JSON value from cache
func (s *CacheService) GetJSON(key string, dest interface{}) error {
	data, err := s.Get(key)
	if err != nil {
		return err
	}
	
	return json.Unmarshal(data, dest)
}

// SetJSON marshals and stores a JSON value in cache
func (s *CacheService) SetJSON(key string, value interface{}, ttl time.Duration) error {
	data, err := json.Marshal(value)
	if err != nil {
		return err
	}
	
	return s.Set(key, data, ttl)
}

// Increment increments a counter in cache
func (s *CacheService) Increment(key string) (int64, error) {
	if s.redis != nil {
		ctx := context.Background()
		return s.redis.Incr(ctx, key).Result()
	}
	
	// Fallback to local implementation
	var count int64 = 1
	if data, err := s.Get(key); err == nil {
		json.Unmarshal(data, &count)
		count++
	}
	
	s.SetJSON(key, count, 1*time.Hour)
	return count, nil
}

// GetMany retrieves multiple values from cache
func (s *CacheService) GetMany(keys []string) (map[string][]byte, error) {
	result := make(map[string][]byte)
	
	// Try to get from L1 cache first
	var missingKeys []string
	for _, key := range keys {
		if value, ok := s.localCache.Get(key); ok {
			result[key] = value
		} else {
			missingKeys = append(missingKeys, key)
		}
	}
	
	// Get missing keys from Redis
	if s.redis != nil && len(missingKeys) > 0 {
		ctx := context.Background()
		values, err := s.redis.MGet(ctx, missingKeys...).Result()
		if err == nil {
			for i, key := range missingKeys {
				if values[i] != nil {
					if str, ok := values[i].(string); ok {
						data := []byte(str)
						result[key] = data
						// Update L1 cache
						s.localCache.Add(key, data)
					}
				}
			}
		}
	}
	
	return result, nil
}

// SetMany stores multiple values in cache
func (s *CacheService) SetMany(items map[string][]byte, ttl time.Duration) error {
	// Store in L1 cache
	for key, value := range items {
		s.localCache.Add(key, value)
	}
	
	// Store in Redis if available
	if s.redis != nil {
		ctx := context.Background()
		pipe := s.redis.Pipeline()
		
		for key, value := range items {
			if ttl == 0 {
				ttl = s.ttl
			}
			pipe.Set(ctx, key, value, ttl)
		}
		
		_, err := pipe.Exec(ctx)
		if err != nil {
			s.logger.Warnf("Failed to set many in Redis: %v", err)
		}
	}
	
	return nil
}

// Storage interface implementation for Fiber cache middleware
func (s *CacheService) Get(key string) ([]byte, error) {
	return s.Get(key)
}

func (s *CacheService) Set(key string, val []byte, exp time.Duration) error {
	return s.Set(key, val, exp)
}

func (s *CacheService) Delete(key string) error {
	return s.Delete(key)
}

func (s *CacheService) Reset() error {
	return s.Clear()
}

func (s *CacheService) Close() error {
	if s.redis != nil {
		return s.redis.Close()
	}
	return nil
}