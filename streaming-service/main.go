package main

import (
	"streaming-service/aws"
	"streaming-service/config"
	"streaming-service/database"
	"streaming-service/handlers"
	"streaming-service/middleware"
	"streaming-service/services"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/schema"
)

func main() {
	cfg := config.GetConfig()

	// Inicializar cliente S3
	if err := aws.InitS3(); err != nil {
		panic("❌ Error al inicializar S3: " + err.Error())
	}

	// Obtener conexión base (sql.DB del pool)
	sqlDB := database.GetDB()

	gormDB, err := gorm.Open(postgres.New(postgres.Config{
		Conn: sqlDB,
	}), &gorm.Config{
		NamingStrategy: schema.NamingStrategy{
			TablePrefix:   "music_streaming.",
			SingularTable: false,
		},
	})
	if err != nil {
		panic("❌ Error al inicializar GORM")
	}

	songService := services.NewSongService(gormDB)
	r := gin.Default()

	// Configurar trusted proxies (confiar en Nginx y Docker)
	r.SetTrustedProxies([]string{"172.16.0.0/12", "10.0.0.0/8", "192.168.0.0/16"})

	// CORS
	r.Use(cors.New(cors.Config{
		AllowOrigins:     cfg.AllowedOrigins,
		AllowMethods:     []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Content-Type", "Authorization", "Range"},
		ExposeHeaders:    []string{"Content-Length", "Content-Range", "Accept-Ranges"},
		AllowCredentials: true,
	}))

	// Rutas
	r.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "ok", "service": "streaming"})
	})
	protected := r.Group("/")
	protected.Use(middleware.AuthMiddleware(cfg.JWTSecret))
	protected.GET("/stream", handlers.StreamSongHandler(songService))

	r.GET("/song/:id/info", handlers.GetSongInfoHandler(songService))

	r.Run(":" + cfg.Port)
}
