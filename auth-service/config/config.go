// Package config centraliza la obtencion de variables de entorno y la configuracion de la aplicacion.
package config

import (
	"log"
	"os"
	"time"
)

type Config struct {
	DatabaseURL     string
	JWTSecret       string
	AccessTokenTTL  time.Duration
	RefreshTokenTTL time.Duration
	Port            string
	AllowedOrigins  []string
}

var AppConfig *Config

// LoadConfig carga todas las variables de entorno y las valida
func LoadConfig() *Config {
	config := &Config{
		DatabaseURL:    getEnvOrDefault("DB_URL", ""),
		JWTSecret:      getEnvOrDefault("JWT_SECRET", "HolaMundoo"),
		Port:           getEnvOrDefault("AUTH_PORT", getEnvOrDefault("PORT", "8080")),
		AllowedOrigins: parseOrigins(getEnvOrDefault("ALLOWED_ORIGINS", "*")),
	}

	var err error
	accessTTLStr := getEnvOrDefault("ACCESS_TOKEN_TTL", "15m")
	config.AccessTokenTTL, err = time.ParseDuration(accessTTLStr)
	if err != nil {
		log.Printf("⚠️ ACCESS_TOKEN_TTL inválido (%s), usando 15m por defecto", accessTTLStr)
		config.AccessTokenTTL = 15 * time.Minute
	}

	refreshTTLStr := getEnvOrDefault("REFRESH_TOKEN_TTL", "168h")
	config.RefreshTokenTTL, err = time.ParseDuration(refreshTTLStr)
	if err != nil {
		log.Printf("⚠️ REFRESH_TOKEN_TTL inválido (%s), usando 168h por defecto", refreshTTLStr)
		config.RefreshTokenTTL = 168 * time.Hour
	}

	if config.DatabaseURL == "" {
		log.Fatal("❌ DB_URL es requerido")
	}

	AppConfig = config

	log.Printf("✅ Configuración cargada:")
	log.Printf("   - Puerto: %s", config.Port)
	log.Printf("   - Access Token TTL: %v", config.AccessTokenTTL)
	log.Printf("   - Refresh Token TTL: %v", config.RefreshTokenTTL)
	log.Printf("   - Base de datos: configurada")

	return config
}

// getEnvOrDefault obtiene una variable de entorno o devuelve un valor por defecto
func getEnvOrDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// parseOrigins parsea la lista de orígenes separados por coma
func parseOrigins(origins string) []string {
	if origins == "*" || origins == "" {
		return []string{"*"}
	}
	var result []string
	current := ""
	for i := 0; i < len(origins); i++ {
		if origins[i] == ',' {
			if current != "" {
				result = append(result, current)
				current = ""
			}
		} else if origins[i] != ' ' {
			current += string(origins[i])
		}
	}
	if current != "" {
		result = append(result, current)
	}
	if len(result) == 0 {
		return []string{"*"}
	}
	return result
}

// GetAccessTokenTTLSeconds retorna el TTL del access token en segundos
func (c *Config) GetAccessTokenTTLSeconds() int {
	return int(c.AccessTokenTTL.Seconds())
}

// GetRefreshTokenTTLSeconds retorna el TTL del refresh token en segundos
func (c *Config) GetRefreshTokenTTLSeconds() int {
	return int(c.RefreshTokenTTL.Seconds())
}
