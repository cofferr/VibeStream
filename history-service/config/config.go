package config

import (
	"os"
	"sync"

	"github.com/joho/godotenv"
)

type Config struct {
	Port           string
	JWTSecret      string
	DBURL          string
	RabbitURL      string
	AllowedOrigins []string
}

var (
	instance *Config
	once     sync.Once
)

// GetConfig devuelve la instancia singleton de Config
func GetConfig() *Config {
	once.Do(func() {
		// Cargar .env solo si existe
		_ = godotenv.Load()

		instance = &Config{
			Port:           getEnv("HISTORY_PORT", "8005"),
			JWTSecret:      getEnv("JWT_SECRET", "defaultsecret"),
			DBURL:          getEnv("DB_URL", "postgres://user:pass@localhost:5432/dbname?sslmode=disable"),
			// Por defecto en docker-compose el host del broker es `rabbitmq` y el puerto 5672
			RabbitURL:      getEnv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/"),
			AllowedOrigins: parseOrigins(getEnv("ALLOWED_ORIGINS", "*")),
		}
	})
	return instance
}

// parseOrigins parsea la lista de orígenes
func parseOrigins(origins string) []string {
	if origins == "*" || origins == "" {
		return []string{"*"}
	}
	var result []string
	for i := 0; i < len(origins); i++ {
		start := i
		for i < len(origins) && origins[i] != ',' {
			i++
		}
		if origin := origins[start:i]; origin != "" {
			result = append(result, origin)
		}
	}
	return result
}

// getEnv devuelve la variable de entorno o un valor por defecto
func getEnv(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}
