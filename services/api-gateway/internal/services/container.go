package services

import (
	"go.uber.org/zap"
)

// Container holds all service dependencies
type Container struct {
	Cache          *CacheService
	Queue          *QueueService
	Proxy          *ProxyService
	Auth           *AuthService
	RateLimiter    *RateLimiter
	CircuitBreaker *CircuitBreaker
	Logger         *zap.SugaredLogger
}