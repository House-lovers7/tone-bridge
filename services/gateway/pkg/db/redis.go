package db

import (
	"context"
	"time"

	"github.com/redis/go-redis/v9"
)

func InitRedis(addr string) *redis.Client {
	client := redis.NewClient(&redis.Options{
		Addr:         addr,
		Password:     "", // no password
		DB:           0,  // default DB
		PoolSize:     10,
		MinIdleConns: 5,
		MaxRetries:   3,
	})

	// Test the connection
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := client.Ping(ctx).Err(); err != nil {
		panic("Failed to connect to Redis: " + err.Error())
	}

	return client
}