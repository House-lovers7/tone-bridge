package config

import (
	"os"
	"strconv"
	"strings"
)

type Config struct {
	// Server
	Port    string
	Prefork bool
	Debug   bool
	
	// Security
	JWTSecret           string
	APIKeyHeader        string
	SlackSigningSecret  string
	TeamsAppID          string
	DiscordPublicKey    string
	GitHubSecret        string
	
	// Redis
	RedisURL      string
	RedisPassword string
	RedisDB       int
	
	// Backend Services
	TransformServiceURL     string
	AnalyzeServiceURL       string
	AutoTransformServiceURL string
	MLServiceURL            string
	WebSocketURL            string
	
	// Database
	DatabaseURL string
	
	// CORS
	CORSOrigins string
	
	// Rate Limiting
	RateLimitRequests int
	RateLimitWindow   int // seconds
	
	// Cache
	CacheTTL int // seconds
	
	// Monitoring
	PrometheusEnabled bool
	TracingEnabled    bool
	
	// Feature Flags
	EnableCache        bool
	EnableRateLimit    bool
	EnableCircuitBreaker bool
}

func Load() *Config {
	return &Config{
		Port:    getEnv("PORT", "8000"),
		Prefork: getEnvBool("PREFORK", false),
		Debug:   getEnvBool("DEBUG", false),
		
		JWTSecret:           getEnv("JWT_SECRET", "your-secret-key"),
		APIKeyHeader:        getEnv("API_KEY_HEADER", "X-API-Key"),
		SlackSigningSecret:  getEnv("SLACK_SIGNING_SECRET", ""),
		TeamsAppID:          getEnv("TEAMS_APP_ID", ""),
		DiscordPublicKey:    getEnv("DISCORD_PUBLIC_KEY", ""),
		GitHubSecret:        getEnv("GITHUB_SECRET", ""),
		
		RedisURL:      getEnv("REDIS_URL", "localhost:6379"),
		RedisPassword: getEnv("REDIS_PASSWORD", ""),
		RedisDB:       getEnvInt("REDIS_DB", 0),
		
		TransformServiceURL:     getEnv("TRANSFORM_SERVICE_URL", "http://localhost:8001"),
		AnalyzeServiceURL:       getEnv("ANALYZE_SERVICE_URL", "http://localhost:8002"),
		AutoTransformServiceURL: getEnv("AUTO_TRANSFORM_SERVICE_URL", "http://localhost:8003"),
		MLServiceURL:            getEnv("ML_SERVICE_URL", "http://localhost:8004"),
		WebSocketURL:            getEnv("WEBSOCKET_URL", "ws://localhost:3001"),
		
		DatabaseURL: getEnv("DATABASE_URL", "postgres://tonebridge:password@localhost:5432/tonebridge"),
		
		CORSOrigins: getEnv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080"),
		
		RateLimitRequests: getEnvInt("RATE_LIMIT_REQUESTS", 100),
		RateLimitWindow:   getEnvInt("RATE_LIMIT_WINDOW", 60),
		
		CacheTTL: getEnvInt("CACHE_TTL", 300),
		
		PrometheusEnabled: getEnvBool("PROMETHEUS_ENABLED", true),
		TracingEnabled:    getEnvBool("TRACING_ENABLED", false),
		
		EnableCache:          getEnvBool("ENABLE_CACHE", true),
		EnableRateLimit:      getEnvBool("ENABLE_RATE_LIMIT", true),
		EnableCircuitBreaker: getEnvBool("ENABLE_CIRCUIT_BREAKER", true),
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intVal, err := strconv.Atoi(value); err == nil {
			return intVal
		}
	}
	return defaultValue
}

func getEnvBool(key string, defaultValue bool) bool {
	if value := os.Getenv(key); value != "" {
		value = strings.ToLower(value)
		return value == "true" || value == "1" || value == "yes"
	}
	return defaultValue
}