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
	"time"

	"github.com/gin-contrib/cors"
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
	if err := r.SetTrustedProxies([]string{"172.16.0.0/12", "10.0.0.0/8", "192.168.0.0/16"}); err != nil {
		log.Fatalf("❌ Error configurando trusted proxies: %v", err)
	}

	// CORS (Fase 5: el CORS manual anterior reflejaba cualquier header
	// Origin del request sin validarlo contra allowedOrigins — la
	// variable se calculaba pero nunca se usaba, así que el allowlist no
	// se aplicaba de verdad. gin-contrib/cors es el mismo paquete que ya
	// usan auth-service y streaming-service, cerrando la única
	// divergencia de CORS en Go que quedaba pendiente de Fase 2.)
	allowedOrigins := cfg.AllowedOrigins
	if len(allowedOrigins) == 0 {
		allowedOrigins = []string{"*"}
	}
	r.Use(cors.New(cors.Config{
		AllowOrigins:     allowedOrigins,
		AllowMethods:     []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Content-Type", "Authorization"},
		AllowCredentials: true,
		MaxAge:           12 * time.Hour,
	}))

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
