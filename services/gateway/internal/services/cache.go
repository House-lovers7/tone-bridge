package services

import (
	"context"
	"encoding/json"
	"time"

	"github.com/redis/go-redis/v9"
)

type CacheService struct {
	client *redis.Client
}

func NewCacheService(client *redis.Client) *CacheService {
	return &CacheService{
		client: client,
	}
}

func (s *CacheService) Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error {
	data, err := json.Marshal(value)
	if err != nil {
		return err
	}
	
	return s.client.Set(ctx, key, data, ttl).Err()
}

func (s *CacheService) Get(ctx context.Context, key string, dest interface{}) error {
	data, err := s.client.Get(ctx, key).Result()
	if err != nil {
		return err
	}
	
	return json.Unmarshal([]byte(data), dest)
}

func (s *CacheService) Delete(ctx context.Context, key string) error {
	return s.client.Del(ctx, key).Err()
}

func (s *CacheService) Exists(ctx context.Context, key string) (bool, error) {
	result, err := s.client.Exists(ctx, key).Result()
	if err != nil {
		return false, err
	}
	
	return result > 0, nil
}

func (s *CacheService) SetWithTags(ctx context.Context, key string, value interface{}, tags []string, ttl time.Duration) error {
	// Set the main value
	if err := s.Set(ctx, key, value, ttl); err != nil {
		return err
	}
	
	// Add to tag sets for easy invalidation
	for _, tag := range tags {
		tagKey := "tag:" + tag
		s.client.SAdd(ctx, tagKey, key)
		s.client.Expire(ctx, tagKey, ttl)
	}
	
	return nil
}

func (s *CacheService) InvalidateByTag(ctx context.Context, tag string) error {
	tagKey := "tag:" + tag
	
	// Get all keys with this tag
	keys, err := s.client.SMembers(ctx, tagKey).Result()
	if err != nil {
		return err
	}
	
	// Delete all keys
	if len(keys) > 0 {
		if err := s.client.Del(ctx, keys...).Err(); err != nil {
			return err
		}
	}
	
	// Delete the tag set itself
	return s.client.Del(ctx, tagKey).Err()
}