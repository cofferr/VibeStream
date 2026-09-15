package database

import (
	"database/sql"
	"history-service/config"
	"log"
	"sync"
	"time"

	_ "github.com/lib/pq" // driver PostgreSQL
)

var (
	db   *sql.DB
	once sync.Once
)

// initDB inicializa la conexión a PostgreSQL solo una vez.
func initDB() {
	cfg := config.GetConfig()

	conn, err := sql.Open("postgres", cfg.DBURL)
	if err != nil {
		log.Fatalf("❌ Error al abrir conexión a PostgreSQL: %v", err)
	}

	// Verificar que la base de datos está accesible
	if err := conn.Ping(); err != nil {
		log.Fatalf("❌ No se pudo conectar a PostgreSQL: %v", err)
	}

	// Ajustar pool de conexiones
	conn.SetMaxOpenConns(10)                  // máximo conexiones abiertas
	conn.SetMaxIdleConns(5)                   // máximo conexiones inactivas
	conn.SetConnMaxLifetime(30 * time.Minute) // tiempo máximo de vida de la conexión

	db = conn
	log.Println("✅ Conexión a PostgreSQL establecida y pool creado")
}

// GetDB devuelve la instancia de la conexión.
// Inicializa la conexión la primera vez que se llama.
func GetDB() *sql.DB {
	once.Do(initDB)
	return db
}

// CloseDB cierra la conexión a la base de datos (útil para tests o shutdowns controlados)
func CloseDB() error {
	if db != nil {
		return db.Close()
	}
	return nil
}
