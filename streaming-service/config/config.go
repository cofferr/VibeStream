package config

import (
	"os"
	"strings"
	"sync"

	"github.com/joho/godotenv"
)

type Config struct {
	Port           string
	JWTSecret      string
	DBURL          string
	RabbitURL      string
	AllowedOrigins []string

	AWSAccessKeyID     string
	AWSSecretAccessKey string
	AWSSessionToken    string
	AWSRegion          string
	AWSS3Bucket        string
}

var (
	instance *Config
	once     sync.Once
)

func GetConfig() *Config {
	once.Do(func() {
		_ = godotenv.Load()

		origins := getEnv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000")
		allowedOrigins := strings.Split(origins, ",")

		instance = &Config{
			Port:           getEnv("STREAMING_PORT", "8001"),
			JWTSecret:      getEnv("JWT_SECRET", "defaultsecret"),
			DBURL:          getEnv("DB_URL", "postgres://user:pass@localhost:5432/dbname?sslmode=disable"),
			// Por defecto apuntar al broker 'rabbitmq' presente en docker-compose
			RabbitURL:      getEnv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/"),
			AllowedOrigins: allowedOrigins,

			AWSAccessKeyID:     getEnv("AWS_ACCESS_KEY_ID", ""),
			AWSSecretAccessKey: getEnv("AWS_SECRET_ACCESS_KEY", ""),
			AWSSessionToken:    getEnv("AWS_SESSION_TOKEN", ""),
			AWSRegion:          getEnv("AWS_REGION", "us-east-1"),
			AWSS3Bucket:        getEnv("AWS_S3_BUCKET", ""),
		}

		println("🔧 Streaming Service Config:")
		println("   Port:", instance.Port)
		println("   Allowed Origins:", strings.Join(instance.AllowedOrigins, ", "))
		println("   DB URL:", maskDBURL(instance.DBURL))

		println("🔧 AWS Config:")
		println("   Region:", instance.AWSRegion)
		println("   Bucket:", instance.AWSS3Bucket)
	})

	return instance
}

// getEnv obtiene una variable de entorno o retorna el valor por defecto
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// maskDBURL enmascara la contraseña en la URL de la base de datos para logs seguros
func maskDBURL(dbURL string) string {
	// Busca el patrón "://usuario:contraseña@" y lo reemplaza con "://usuario:***@"
	parts := strings.Split(dbURL, "@")
	if len(parts) > 1 {
		userPassParts := strings.Split(parts[0], ":")
		if len(userPassParts) >= 3 {
			// Reconstruye la URL con la contraseña enmascarada
			maskedURL := userPassParts[0] + ":" + userPassParts[1] + ":***@" + strings.Join(parts[1:], "@")
			return maskedURL
		}
	}
	return dbURL
}
