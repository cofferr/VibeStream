package main

import (
	"context"
	"history-service/config"
	"history-service/database"
	"history-service/events"
	"history-service/handlers"
	"history-service/middleware"
	"history-service/repositories"
	"history-service/services"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/gin-gonic/gin"
)

func main() {
	// Cargar configuración
	cfg := config.GetConfig()

	// Inicializar conexión a la base de datos
	db := database.GetDB()

	// Crear repositorio de historial
	historyRepo := repositories.NewHistoryRepository(db)

	// Crear servicio de historial
	historyService := services.NewHistoryService(historyRepo)

	// Crear handler
	historyHandler := handlers.NewHistoryHandler(historyService)

	// Gin router
	r := gin.Default()

	// Configurar trusted proxies (confiar en Nginx y Docker)
	r.SetTrustedProxies([]string{"172.16.0.0/12", "10.0.0.0/8", "192.168.0.0/16"})

	// CORS
	allowedOrigins := cfg.AllowedOrigins
	if len(allowedOrigins) == 0 {
		allowedOrigins = []string{"*"}
	}
	r.Use(func(c *gin.Context) {
		origin := c.Request.Header.Get("Origin")
		if origin != "" {
			c.Writer.Header().Set("Access-Control-Allow-Origin", origin)
			c.Writer.Header().Set("Access-Control-Allow-Credentials", "true")
			c.Writer.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
			c.Writer.Header().Set("Access-Control-Allow-Headers", "Origin, Content-Type, Authorization")
		}
		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}
		c.Next()
	})

	// Middleware de autenticación
	r.Use(middleware.AuthMiddleware(cfg.JWTSecret))

	// Rutas
	r.GET("/history", historyHandler.GetHistoryHandler)

	// Arrancar consumidor de eventos en segundo plano
	ctx, cancel := context.WithCancel(context.Background())
	go func() {
		if err := events.StartConsumer(ctx, historyService); err != nil {
			log.Printf("❌ Error en consumidor de eventos: %v", err)
		}
	}()

	// Capturar señales para cierre graceful
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		if err := r.Run(":" + cfg.Port); err != nil {
			log.Fatalf("❌ Error arrancando servidor HTTP: %v", err)
		}
	}()

	log.Printf("✅ History service corriendo en puerto %s", cfg.Port)
	<-stop
	log.Println("⚡ Deteniendo servicio...")

	// Cancelar consumidor de eventos
	cancel()

	// Cerrar DB
	if err := db.Close(); err != nil {
		log.Println("❌ Error cerrando DB:", err)
	}

	log.Println("👋 Servicio detenido correctamente")
}
