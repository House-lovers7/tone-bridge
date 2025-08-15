package config

import (
	"os"
	"strings"
)

type Config struct {
	Port           string
	DatabaseURL    string
	RedisAddr      string
	LLMServiceURL  string
	JWTSecret      string
	AllowedOrigins []string
	LogLevel       string
	Environment    string
}

func LoadConfig() *Config {
	return &Config{
		Port:          getEnv("PORT", "8080"),
		DatabaseURL:   getEnv("DATABASE_URL", "postgres://localhost/tonebridge_db"),
		RedisAddr:     getEnv("REDIS_ADDR", "localhost:6379"),
		LLMServiceURL: getEnv("LLM_SERVICE_URL", "http://localhost:8000"),
		JWTSecret:     getEnv("JWT_SECRET", "your-secret-key"),
		AllowedOrigins: strings.Split(
			getEnv("ALLOWED_ORIGINS", "http://localhost:3001,http://localhost:3000,http://localhost:8080,http://localhost:8082"),
			",",
		),
		LogLevel:    getEnv("LOG_LEVEL", "info"),
		Environment: getEnv("ENV", "development"),
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}