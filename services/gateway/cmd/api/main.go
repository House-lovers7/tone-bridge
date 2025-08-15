package main

import (
	"log"
	"os"
	"os/signal"
	"strings"
	"syscall"

	"github.com/tonebridge/gateway/internal/config"
	"github.com/tonebridge/gateway/internal/handlers"
	"github.com/tonebridge/gateway/internal/middleware"
	"github.com/tonebridge/gateway/internal/repository"
	"github.com/tonebridge/gateway/internal/services"
	"github.com/tonebridge/gateway/pkg/db"
	"github.com/tonebridge/gateway/pkg/utils"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cors"
	"github.com/gofiber/fiber/v2/middleware/logger"
	"github.com/gofiber/fiber/v2/middleware/recover"
	"github.com/joho/godotenv"
	"go.uber.org/zap"
)

func main() {
	// Load environment variables
	if err := godotenv.Load(); err != nil {
		log.Println("No .env file found")
	}

	// Initialize logger
	zapLogger, err := zap.NewProduction()
	if err != nil {
		log.Fatal("Failed to initialize logger:", err)
	}
	defer zapLogger.Sync()
	sugar := zapLogger.Sugar()

	// Load configuration
	cfg := config.LoadConfig()

	// Initialize database
	database, err := db.InitPostgres(cfg.DatabaseURL)
	if err != nil {
		sugar.Fatal("Failed to connect to database:", err)
	}
	defer database.Close()

	// Initialize Redis
	redisClient := db.InitRedis(cfg.RedisAddr)
	defer redisClient.Close()

	// Initialize repositories
	userRepo := repository.NewUserRepository(database)
	transformRepo := repository.NewTransformationRepository(database)

	// Initialize services
	authService := services.NewAuthService(userRepo, cfg.JWTSecret)
	transformService := services.NewTransformationService(
		transformRepo,
		redisClient,
		cfg.LLMServiceURL,
		sugar,
	)
	// TODO: Implement caching
	// cacheService := services.NewCacheService(redisClient)

	// Initialize handlers
	authHandler := handlers.NewAuthHandler(authService, sugar)
	transformHandler := handlers.NewTransformHandler(transformService, sugar)
	healthHandler := handlers.NewHealthHandler(database, redisClient, sugar)
	previewHandler := handlers.NewPreviewHandler(transformService, sugar)

	// Create Fiber app
	app := fiber.New(fiber.Config{
		AppName:      "ToneBridge Gateway",
		ServerHeader: "ToneBridge",
		ErrorHandler: utils.CustomErrorHandler,
	})

	// Global middleware
	app.Use(recover.New())
	app.Use(logger.New(logger.Config{
		Format: "[${time}] ${status} - ${latency} ${method} ${path}\n",
	}))
	// Configure CORS
	corsOrigins := strings.Join(cfg.AllowedOrigins, ",")
	// Check if wildcard is present
	for _, origin := range cfg.AllowedOrigins {
		if origin == "*" {
			corsOrigins = "*"
			break
		}
	}
	
	app.Use(cors.New(cors.Config{
		AllowOrigins: corsOrigins,
		AllowMethods: "GET,POST,PUT,DELETE,OPTIONS",
		AllowHeaders: "Content-Type,Authorization",
	}))

	// Rate limiting middleware
	rateLimiter := middleware.NewRateLimiter(redisClient)
	app.Use(rateLimiter.Limit())

	// Health check routes (no auth required)
	app.Get("/health", healthHandler.HealthCheck)
	app.Get("/ready", healthHandler.ReadinessCheck)

	// API v1 routes
	v1 := app.Group("/api/v1")

	// Auth routes (no auth required)
	auth := v1.Group("/auth")
	auth.Post("/register", authHandler.Register)
	auth.Post("/login", authHandler.Login)
	auth.Post("/refresh", authHandler.RefreshToken)

	// Preview routes (no auth required, but rate limited)
	preview := v1.Group("/preview")
	previewLimiter := middleware.NewPreviewRateLimiter(redisClient)
	preview.Use(previewLimiter.Limit())
	preview.Get("/info", previewHandler.GetPreviewInfo)
	preview.Post("/transform", previewHandler.PreviewTransform)
	preview.Post("/analyze", previewHandler.PreviewAnalyze)

	// Protected routes
	protected := v1.Use(middleware.JWTAuth(cfg.JWTSecret))

	// Transformation routes
	protected.Post("/transform", transformHandler.TransformMessage)
	protected.Post("/analyze", transformHandler.AnalyzeMessage)
	protected.Get("/history", transformHandler.GetHistory)

	// Dictionary routes
	protected.Get("/dictionaries", transformHandler.GetDictionaries)
	protected.Post("/dictionaries", transformHandler.CreateDictionary)
	protected.Put("/dictionaries/:id", transformHandler.UpdateDictionary)
	protected.Delete("/dictionaries/:id", transformHandler.DeleteDictionary)

	// User profile routes
	protected.Get("/profile", authHandler.GetProfile)
	protected.Put("/profile", authHandler.UpdateProfile)

	// Graceful shutdown
	go func() {
		if err := app.Listen(":" + cfg.Port); err != nil {
			sugar.Fatal("Failed to start server:", err)
		}
	}()

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	sugar.Info("Shutting down server...")
	if err := app.Shutdown(); err != nil {
		sugar.Fatal("Server forced to shutdown:", err)
	}
}