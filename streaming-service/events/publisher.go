package events

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"streaming-service/config"
	"sync"
	"time"

	amqp "github.com/rabbitmq/amqp091-go"
)

// Estructura del evento
type SongPlayedEvent struct {
	UserID uint `json:"user_id"`
	SongID uint `json:"song_id"`
}

// EventPublisher maneja la conexión y canal reutilizable
type EventPublisher struct {
	conn    *amqp.Connection
	channel *amqp.Channel
	mutex   sync.RWMutex
	cfg     *config.Config
}

// Publisher global (singleton)
var (
	publisher *EventPublisher
	once      sync.Once
)

// GetPublisher obtiene la instancia singleton del publisher
func GetPublisher() *EventPublisher {
	once.Do(func() {
		publisher = &EventPublisher{
			cfg: config.GetConfig(),
		}
		if err := publisher.connect(); err != nil {
			log.Printf("❌ Error al inicializar publisher: %v", err)
		}
	})
	return publisher
}

// connect establece la conexión y canal con RabbitMQ
func (p *EventPublisher) connect() error {
	p.mutex.Lock()
	defer p.mutex.Unlock()

	fmt.Println("🔌 Conectando a RabbitMQ...")

	// Establecer conexión
	conn, err := amqp.Dial(p.cfg.RabbitURL)
	if err != nil {
		return fmt.Errorf("error al conectar con RabbitMQ: %w", err)
	}

	// Abrir canal
	ch, err := conn.Channel()
	if err != nil {
		conn.Close()
		return fmt.Errorf("error al abrir canal: %w", err)
	}

	// Configurar infraestructura (exchange, cola)
	if err := p.setupInfrastructure(ch); err != nil {
		ch.Close()
		conn.Close()
		return fmt.Errorf("error al configurar infraestructura: %w", err)
	}

	p.conn = conn
	p.channel = ch

	// Manejar reconexión automática
	go p.handleReconnection()

	fmt.Println("✅ Conectado a RabbitMQ exitosamente")
	return nil
}

// setupInfrastructure declara exchange, cola y binding
func (p *EventPublisher) setupInfrastructure(ch *amqp.Channel) error {
	// Declarar exchange (fanout)
	err := ch.ExchangeDeclare(
		"song_events", // nombre
		"fanout",      // tipo
		true,          // durable
		false,         // auto-delete
		false,         // internal
		false,         // no-wait
		nil,           // argumentos
	)
	if err != nil {
		return fmt.Errorf("error al declarar exchange: %w", err)
	}

	// Declarar cola
	queue, err := ch.QueueDeclare(
		"song_events_queue", // nombre
		true,                // durable
		false,               // delete when unused
		false,               // exclusive
		false,               // no-wait
		nil,                 // argumentos
	)
	if err != nil {
		return fmt.Errorf("error al declarar cola: %w", err)
	}

	// Enlazar cola al exchange
	err = ch.QueueBind(
		queue.Name,    // queue name
		"",            // routing key
		"song_events", // exchange
		false,         // no-wait
		nil,           // argumentos
	)
	if err != nil {
		return fmt.Errorf("error al enlazar cola: %w", err)
	}

	return nil
}

// handleReconnection maneja la reconexión automática
func (p *EventPublisher) handleReconnection() {
	connClose := make(chan *amqp.Error)
	p.conn.NotifyClose(connClose)

	chClose := make(chan *amqp.Error)
	p.channel.NotifyClose(chClose)

	select {
	case err := <-connClose:
		if err != nil {
			log.Printf("⚠️ Conexión cerrada: %v. Reconectando...", err)
			p.reconnect()
		}
	case err := <-chClose:
		if err != nil {
			log.Printf("⚠️ Canal cerrado: %v. Reconectando...", err)
			p.reconnect()
		}
	}
}

// reconnect reestablece la conexión
func (p *EventPublisher) reconnect() {
	for {
		log.Println("🔄 Intentando reconectar...")

		if err := p.connect(); err != nil {
			log.Printf("❌ Error en reconexión: %v. Reintentando en 5s...", err)
			time.Sleep(5 * time.Second)
			continue
		}

		log.Println("✅ Reconectado exitosamente")
		break
	}
}

// isConnected verifica si la conexión está activa
func (p *EventPublisher) isConnected() bool {
	p.mutex.RLock()
	defer p.mutex.RUnlock()

	return p.conn != nil && !p.conn.IsClosed() && p.channel != nil
}

// PublishSongPlayed publica el evento usando la conexión reutilizable
func (p *EventPublisher) PublishSongPlayed(userID, songID uint) error {
	fmt.Printf("🚀 Enviando evento: userID=%d, songID=%d\n", userID, songID)

	// Verificar conexión
	if !p.isConnected() {
		if err := p.connect(); err != nil {
			return fmt.Errorf("error al conectar: %w", err)
		}
	}

	// Crear evento
	event := SongPlayedEvent{
		UserID: userID,
		SongID: songID,
	}

	body, err := json.Marshal(event)
	if err != nil {
		return fmt.Errorf("error al serializar evento: %w", err)
	}

	// Contexto con timeout
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Publicar con lock de lectura (thread-safe)
	p.mutex.RLock()
	defer p.mutex.RUnlock()

	err = p.channel.PublishWithContext(
		ctx,
		"song_events", // exchange
		"",            // routing key
		false,         // mandatory
		false,         // immediate
		amqp.Publishing{
			ContentType: "application/json",
			Body:        body,
			Timestamp:   time.Now(),
			MessageId:   fmt.Sprintf("%d-%d-%d", userID, songID, time.Now().Unix()),
		},
	)
	if err != nil {
		return fmt.Errorf("error al publicar mensaje: %w", err)
	}

	log.Printf("📨 Evento enviado: %+v", event)
	return nil
}

// Close cierra la conexión y canal
func (p *EventPublisher) Close() error {
	p.mutex.Lock()
	defer p.mutex.Unlock()

	var errs []error

	if p.channel != nil {
		if err := p.channel.Close(); err != nil {
			errs = append(errs, fmt.Errorf("error al cerrar canal: %w", err))
		}
	}

	if p.conn != nil {
		if err := p.conn.Close(); err != nil {
			errs = append(errs, fmt.Errorf("error al cerrar conexión: %w", err))
		}
	}

	if len(errs) > 0 {
		return fmt.Errorf("errores al cerrar: %v", errs)
	}

	return nil
}

// PublishSongPlayed función pública para mantener compatibilidad
func PublishSongPlayed(userID, songID uint) error {
	return GetPublisher().PublishSongPlayed(userID, songID)
}
