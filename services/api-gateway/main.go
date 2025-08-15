package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cache"
	"github.com/gofiber/fiber/v2/middleware/compress"
	"github.com/gofiber/fiber/v2/middleware/cors"
	"github.com/gofiber/fiber/v2/middleware/helmet"
	"github.com/gofiber/fiber/v2/middleware/limiter"
	"github.com/gofiber/fiber/v2/middleware/logger"
	"github.com/gofiber/fiber/v2/middleware/monitor"
	"github.com/gofiber/fiber/v2/middleware/recover"
	"github.com/gofiber/fiber/v2/middleware/requestid"
	jwtware "github.com/gofiber/jwt/v3"
	"github.com/joho/godotenv"
	"go.uber.org/zap"

	"github.com/tonebridge/api-gateway/internal/config"
	"github.com/tonebridge/api-gateway/internal/handlers"
	"github.com/tonebridge/api-gateway/internal/middleware"
	"github.com/tonebridge/api-gateway/internal/services"
)

func main() {
	// Load environment variables
	if err := godotenv.Load(); err != nil {
		log.Println("No .env file found")
	}

	// Initialize logger
	logger, _ := zap.NewProduction()
	defer logger.Sync()
	sugar := logger.Sugar()

	// Load configuration
	cfg := config.Load()

	// Initialize services
	services := initializeServices(cfg, sugar)

	// Create Fiber app with optimized settings
	app := fiber.New(fiber.Config{
		Prefork:               cfg.Prefork,
		ServerHeader:          "ToneBridge",
		AppName:               "ToneBridge API Gateway v1.0.0",
		DisableStartupMessage: false,
		EnablePrintRoutes:     cfg.Debug,
		BodyLimit:             10 * 1024 * 1024, // 10MB
		ReadTimeout:           10 * time.Second,
		WriteTimeout:          10 * time.Second,
		IdleTimeout:           120 * time.Second,
		EnableTrustedProxyCheck: true,
		TrustedProxies:         []string{"10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"},
		ProxyHeader:            fiber.HeaderXForwardedFor,
	})

	// Global middleware
	setupMiddleware(app, cfg, services, sugar)

	// Routes
	setupRoutes(app, services, cfg, sugar)

	// Health check endpoint (no auth required)
	app.Get("/health", handlers.HealthCheck(services))
	app.Get("/metrics", monitor.New(monitor.Config{Title: "ToneBridge Metrics"}))

	// Graceful shutdown
	go gracefulShutdown(app, sugar)

	// Start server
	port := cfg.Port
	if port == "" {
		port = "8000"
	}

	sugar.Infof("🚀 API Gateway starting on port %s", port)
	if err := app.Listen(":" + port); err != nil {
		sugar.Fatal("Failed to start server:", err)
	}
}

func initializeServices(cfg *config.Config, logger *zap.SugaredLogger) *services.Container {
	// Initialize Redis client
	redisClient := services.NewRedisClient(cfg.RedisURL)
	
	// Initialize cache service
	cacheService := services.NewCacheService(redisClient, logger)
	
	// Initialize queue service
	queueService := services.NewQueueService(cfg.RedisURL, logger)
	
	// Initialize proxy service for backend communication
	proxyService := services.NewProxyService(cfg, logger)
	
	// Initialize auth service
	authService := services.NewAuthService(cfg.JWTSecret, cacheService, logger)
	
	// Initialize rate limiter
	rateLimiter := services.NewRateLimiter(redisClient, logger)
	
	// Initialize circuit breaker
	circuitBreaker := services.NewCircuitBreaker(logger)

	return &services.Container{
		Cache:          cacheService,
		Queue:          queueService,
		Proxy:          proxyService,
		Auth:           authService,
		RateLimiter:    rateLimiter,
		CircuitBreaker: circuitBreaker,
		Logger:         logger,
	}
}

func setupMiddleware(app *fiber.App, cfg *config.Config, svcs *services.Container, logger *zap.SugaredLogger) {
	// Security headers
	app.Use(helmet.New())
	
	// Request ID
	app.Use(requestid.New())
	
	// Logger
	app.Use(logger.New(logger.Config{
		Format:     "[${time}] ${status} - ${latency} ${method} ${path}\n",
		TimeFormat: "2006/01/02 15:04:05",
		TimeZone:   "UTC",
	}))
	
	// Recover from panics
	app.Use(recover.New(recover.Config{
		EnableStackTrace: cfg.Debug,
	}))
	
	// CORS
	app.Use(cors.New(cors.Config{
		AllowOrigins:     cfg.CORSOrigins,
		AllowMethods:     "GET,POST,PUT,DELETE,OPTIONS,PATCH",
		AllowHeaders:     "Origin, Content-Type, Accept, Authorization, X-Request-ID, X-API-Key",
		AllowCredentials: true,
		MaxAge:           86400,
	}))
	
	// Compression
	app.Use(compress.New(compress.Config{
		Level: compress.LevelBestSpeed,
	}))
	
	// Rate limiting (global)
	app.Use(limiter.New(limiter.Config{
		Max:               100,
		Expiration:        1 * time.Minute,
		LimiterMiddleware: limiter.SlidingWindow{},
		KeyGenerator: func(c *fiber.Ctx) string {
			return c.IP()
		},
		LimitReached: func(c *fiber.Ctx) error {
			return c.Status(429).JSON(fiber.Map{
				"error": "Too many requests",
			})
		},
	}))
	
	// Cache for GET requests
	app.Use(cache.New(cache.Config{
		Next: func(c *fiber.Ctx) bool {
			// Skip cache for non-GET requests and authenticated endpoints
			return c.Method() != "GET" || c.Path() == "/health" || c.Path() == "/metrics"
		},
		Expiration:   5 * time.Minute,
		CacheControl: true,
		KeyGenerator: func(c *fiber.Ctx) string {
			return c.OriginalURL()
		},
		Storage: svcs.Cache,
	}))
}

func setupRoutes(app *fiber.App, svcs *services.Container, cfg *config.Config, logger *zap.SugaredLogger) {
	// Public routes
	public := app.Group("/api/v1")
	
	// Authentication endpoints
	public.Post("/auth/login", handlers.Login(svcs))
	public.Post("/auth/register", handlers.Register(svcs))
	public.Post("/auth/refresh", handlers.RefreshToken(svcs))
	
	// Protected routes with JWT middleware
	protected := app.Group("/api/v1", jwtware.New(jwtware.Config{
		SigningKey:   []byte(cfg.JWTSecret),
		ErrorHandler: middleware.JWTError,
		TokenLookup:  "header:Authorization,query:token",
		AuthScheme:   "Bearer",
	}))
	
	// API Key authentication alternative
	apiKey := app.Group("/api/v1", middleware.APIKeyAuth(svcs.Auth))
	
	// Transform endpoints
	transformGroup := protected.Group("/transform")
	transformGroup.Post("/", handlers.Transform(svcs))
	transformGroup.Post("/batch", handlers.BatchTransform(svcs))
	transformGroup.Get("/history", handlers.GetTransformHistory(svcs))
	
	// Analyze endpoints
	analyzeGroup := protected.Group("/analyze")
	analyzeGroup.Post("/", handlers.Analyze(svcs))
	analyzeGroup.Post("/tone", handlers.AnalyzeTone(svcs))
	analyzeGroup.Post("/clarity", handlers.AnalyzeClarity(svcs))
	analyzeGroup.Post("/sentiment", handlers.AnalyzeSentiment(svcs))
	analyzeGroup.Post("/priority", handlers.AnalyzePriority(svcs))
	
	// Auto-transform endpoints
	autoTransformGroup := protected.Group("/auto-transform")
	autoTransformGroup.Get("/config", handlers.GetAutoTransformConfig(svcs))
	autoTransformGroup.Put("/config", handlers.UpdateAutoTransformConfig(svcs))
	autoTransformGroup.Post("/evaluate", handlers.EvaluateAutoTransform(svcs))
	autoTransformGroup.Post("/apply", handlers.ApplyAutoTransform(svcs))
	autoTransformGroup.Get("/rules", handlers.ListAutoTransformRules(svcs))
	autoTransformGroup.Post("/rules", handlers.CreateAutoTransformRule(svcs))
	autoTransformGroup.Put("/rules/:id", handlers.UpdateAutoTransformRule(svcs))
	autoTransformGroup.Delete("/rules/:id", handlers.DeleteAutoTransformRule(svcs))
	
	// Webhook endpoints (with signature verification)
	webhooks := app.Group("/webhooks")
	webhooks.Post("/slack", middleware.SlackVerification(cfg.SlackSigningSecret), handlers.SlackWebhook(svcs))
	webhooks.Post("/teams", middleware.TeamsVerification(), handlers.TeamsWebhook(svcs))
	webhooks.Post("/discord", middleware.DiscordVerification(cfg.DiscordPublicKey), handlers.DiscordWebhook(svcs))
	webhooks.Post("/github", middleware.GitHubVerification(cfg.GitHubSecret), handlers.GitHubWebhook(svcs))
	
	// WebSocket endpoint
	protected.Get("/ws", handlers.WebSocketHandler(svcs))
	
	// Admin endpoints
	admin := protected.Group("/admin", middleware.RequireRole("admin"))
	admin.Get("/stats", handlers.GetSystemStats(svcs))
	admin.Get("/users", handlers.ListUsers(svcs))
	admin.Put("/users/:id", handlers.UpdateUser(svcs))
	admin.Delete("/cache", handlers.ClearCache(svcs))
	
	// 404 handler
	app.Use(func(c *fiber.Ctx) error {
		return c.Status(404).JSON(fiber.Map{
			"error": "Endpoint not found",
			"path":  c.Path(),
		})
	})
}

func gracefulShutdown(app *fiber.App, logger *zap.SugaredLogger) {
	// Create channel to listen for interrupt signals
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, os.Interrupt, syscall.SIGTERM)
	
	// Wait for signal
	<-quit
	
	logger.Info("Gracefully shutting down...")
	
	// Create deadline for shutdown
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	
	// Shutdown server
	if err := app.ShutdownWithContext(ctx); err != nil {
		logger.Error("Error during shutdown:", err)
	}
	
	logger.Info("Server shutdown complete")
}