package handlers

import (
	"context"
	"database/sql"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/redis/go-redis/v9"
	"go.uber.org/zap"
)

type HealthHandler struct {
	db     *sql.DB
	redis  *redis.Client
	logger *zap.SugaredLogger
}

func NewHealthHandler(db *sql.DB, redis *redis.Client, logger *zap.SugaredLogger) *HealthHandler {
	return &HealthHandler{
		db:     db,
		redis:  redis,
		logger: logger,
	}
}

func (h *HealthHandler) HealthCheck(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{
		"status":  "healthy",
		"service": "gateway",
		"time":    time.Now().Unix(),
	})
}

func (h *HealthHandler) ReadinessCheck(c *fiber.Ctx) error {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Check database
	if err := h.db.PingContext(ctx); err != nil {
		h.logger.Errorw("Database is not ready", "error", err)
		return c.Status(fiber.StatusServiceUnavailable).JSON(fiber.Map{
			"status":  "not ready",
			"service": "gateway",
			"error":   "database connection failed",
		})
	}

	// Check Redis
	if err := h.redis.Ping(ctx).Err(); err != nil {
		h.logger.Errorw("Redis is not ready", "error", err)
		return c.Status(fiber.StatusServiceUnavailable).JSON(fiber.Map{
			"status":  "not ready",
			"service": "gateway",
			"error":   "redis connection failed",
		})
	}

	return c.JSON(fiber.Map{
		"status":  "ready",
		"service": "gateway",
		"time":    time.Now().Unix(),
	})
}