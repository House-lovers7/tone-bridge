package middleware

import (
	"context"
	"fmt"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/redis/go-redis/v9"
)

type RateLimiter struct {
	client *redis.Client
	limit  int
	window time.Duration
}

func NewRateLimiter(client *redis.Client) *RateLimiter {
	return &RateLimiter{
		client: client,
		limit:  100, // 100 requests
		window: time.Minute, // per minute
	}
}

func (r *RateLimiter) Limit() fiber.Handler {
	return func(c *fiber.Ctx) error {
		// Get client identifier (IP address or user ID if authenticated)
		identifier := c.IP()
		if userID := c.Locals("user_id"); userID != nil {
			identifier = fmt.Sprintf("user:%v", userID)
		}

		key := fmt.Sprintf("rate_limit:%s", identifier)
		ctx := context.Background()

		// Increment counter
		count, err := r.client.Incr(ctx, key).Result()
		if err != nil {
			// If Redis is down, allow the request
			return c.Next()
		}

		// Set expiry on first request
		if count == 1 {
			r.client.Expire(ctx, key, r.window)
		}

		// Check if limit exceeded
		if count > int64(r.limit) {
			ttl, _ := r.client.TTL(ctx, key).Result()
			return c.Status(fiber.StatusTooManyRequests).JSON(fiber.Map{
				"error":        "Rate limit exceeded",
				"retry_after":  ttl.Seconds(),
			})
		}

		// Add rate limit headers
		c.Set("X-RateLimit-Limit", fmt.Sprintf("%d", r.limit))
		c.Set("X-RateLimit-Remaining", fmt.Sprintf("%d", r.limit-int(count)))
		c.Set("X-RateLimit-Reset", fmt.Sprintf("%d", time.Now().Add(r.window).Unix()))

		return c.Next()
	}
}