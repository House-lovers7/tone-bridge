package middleware

import (
	"context"
	"fmt"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/redis/go-redis/v9"
	"github.com/tonebridge/gateway/pkg/utils"
)

// PreviewRateLimiter implements rate limiting for preview endpoints
type PreviewRateLimiter struct {
	redisClient *redis.Client
}

// NewPreviewRateLimiter creates a new preview rate limiter
func NewPreviewRateLimiter(redisClient *redis.Client) *PreviewRateLimiter {
	return &PreviewRateLimiter{
		redisClient: redisClient,
	}
}

// Limit implements rate limiting for preview endpoints
// - 3 requests per minute
// - 10 requests per day
func (r *PreviewRateLimiter) Limit() fiber.Handler {
	return func(c *fiber.Ctx) error {
		ctx := context.Background()
		clientIP := c.IP()
		
		// Create Redis keys for rate limiting
		minuteKey := fmt.Sprintf("preview:rate:minute:%s", clientIP)
		dailyKey := fmt.Sprintf("preview:rate:daily:%s", clientIP)
		
		// Check minute limit (3 requests per minute)
		minuteCount, err := r.redisClient.Incr(ctx, minuteKey).Result()
		if err != nil {
			return utils.SendError(c, fiber.StatusInternalServerError, "Rate limiting error")
		}
		
		// Set expiration for minute key if it's the first request
		if minuteCount == 1 {
			r.redisClient.Expire(ctx, minuteKey, time.Minute)
		}
		
		if minuteCount > 3 {
			remaining, _ := r.redisClient.TTL(ctx, minuteKey).Result()
			return c.Status(fiber.StatusTooManyRequests).JSON(fiber.Map{
				"success": false,
				"error": "Rate limit exceeded",
				"message": fmt.Sprintf("Too many requests. Please wait %d seconds.", int(remaining.Seconds())),
				"limits": fiber.Map{
					"per_minute": 3,
					"per_day": 10,
				},
			})
		}
		
		// Check daily limit (10 requests per day)
		dailyCount, err := r.redisClient.Incr(ctx, dailyKey).Result()
		if err != nil {
			return utils.SendError(c, fiber.StatusInternalServerError, "Rate limiting error")
		}
		
		// Set expiration for daily key if it's the first request
		if dailyCount == 1 {
			r.redisClient.Expire(ctx, dailyKey, 24*time.Hour)
		}
		
		if dailyCount > 10 {
			remaining, _ := r.redisClient.TTL(ctx, dailyKey).Result()
			hours := int(remaining.Hours())
			minutes := int(remaining.Minutes()) % 60
			return c.Status(fiber.StatusTooManyRequests).JSON(fiber.Map{
				"success": false,
				"error": "Daily limit exceeded",
				"message": fmt.Sprintf("Daily limit reached. Please wait %dh %dm or sign up for unlimited access.", hours, minutes),
				"limits": fiber.Map{
					"per_minute": 3,
					"per_day": 10,
				},
				"signup_url": "/api/v1/auth/register",
			})
		}
		
		// Add rate limit headers
		c.Set("X-RateLimit-Limit-Minute", "3")
		c.Set("X-RateLimit-Remaining-Minute", fmt.Sprintf("%d", 3-minuteCount))
		c.Set("X-RateLimit-Limit-Daily", "10")
		c.Set("X-RateLimit-Remaining-Daily", fmt.Sprintf("%d", 10-dailyCount))
		
		return c.Next()
	}
}