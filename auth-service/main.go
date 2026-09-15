package main

import (
	"auth-service/config"
	"auth-service/handlers"
	"auth-service/middleware"
	"auth-service/repositories"
	"auth-service/services"
	"fmt"
	"log"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

func main() {
	// Cargar variables de entorno (.env opcional en desarrollo)
	if err := godotenv.Load(); err != nil {
		log.Println("⚠️ No se encontró archivo .env, usando variables de entorno del sistema")
	} else {
		log.Println("✅ Archivo .env cargado")
	}

	cfg := config.LoadConfig()

	// Conexión a PostgreSQL
	db, err := gorm.Open(postgres.Open(cfg.DatabaseURL), &gorm.Config{
		PrepareStmt: false,
	})
	if err != nil {
		log.Fatalf("❌ Error conectando a PostgreSQL: %v", err)
	}
	log.Println("✅ PostgreSQL conectado")

	// Repositorios
	userRepo := repositories.NewUserRepository(db)
	refreshTokenRepo := repositories.NewRefreshTokenRepository(db)

	// Servicios
	userService := services.NewUserService(userRepo)
	authService := services.NewAuthService(userRepo, refreshTokenRepo)

	// Router
	r := gin.Default()

	// Configurar trusted proxies (confiar en Nginx y Docker)
	r.SetTrustedProxies([]string{"172.16.0.0/12", "10.0.0.0/8", "192.168.0.0/16"})

	// Configuración de CORS dinámica desde .env
	allowedOrigins := cfg.AllowedOrigins
	if len(allowedOrigins) == 0 {
		allowedOrigins = []string{"*"} // Permitir todos si no está configurado
	}
	r.Use(cors.New(cors.Config{
		AllowOrigins:     allowedOrigins,
		AllowMethods:     []string{"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Content-Length", "Content-Type", "Authorization", "X-Requested-With"},
		ExposeHeaders:    []string{"Content-Length", "Content-Type", "Authorization"},
		AllowCredentials: true,
		MaxAge:           12 * time.Hour,
	}))

	// Rutas públicas
	r.POST("/register", handlers.Register(userService))
	r.POST("/login", handlers.Login(authService))
	r.POST("/refresh", handlers.Refresh(authService))
	// Lectura pública de campos básicos de usuario, consumida por otros
	// servicios internos (playlist-service, subscription-service) que no
	// tienen un JWT de usuario para reenviar.
	r.GET("/users/:id", handlers.GetPublicUser(userService))

	// Rutas protegidas
	auth := r.Group("/", middleware.AuthMiddleware(cfg.JWTSecret))
	auth.POST("/logout", handlers.Logout(authService))
	auth.PUT("/update", handlers.UpdateUser(userService))
	auth.GET("/user/me", handlers.GetCurrentUser(userService))

	fmt.Printf("🚀 Auth-Service corriendo en http://localhost:%s\n", cfg.Port)
	if err := r.Run(":" + cfg.Port); err != nil {
		log.Fatal("❌ Error arrancando servidor:", err)
	}
}
