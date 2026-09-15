package events

import (
	"context"
	"encoding/json"
	"history-service/config"
	"history-service/models"
	"history-service/services"
	"log"
	"time"

	amqp "github.com/rabbitmq/amqp091-go"
)

func StartConsumer(ctx context.Context, svc *services.HistoryService) error {
	cfg := config.GetConfig()

	// Reintentar conexión a RabbitMQ
	var conn *amqp.Connection
	var err error
	maxRetries := 10

	for i := 0; i < maxRetries; i++ {
		conn, err = amqp.Dial(cfg.RabbitURL)
		if err == nil {
			break
		}
		log.Printf("⚠️ Intento %d/%d: No se pudo conectar a RabbitMQ, reintentando en 3s...", i+1, maxRetries)
		time.Sleep(3 * time.Second)
	}

	if err != nil {
		return err
	}

	log.Println("✅ Conectado a RabbitMQ")

	ch, err := conn.Channel()
	if err != nil {
		return err
	}

	err = ch.ExchangeDeclare("song_events", "fanout", true, false, false, false, nil)
	if err != nil {
		return err
	}

	queue, err := ch.QueueDeclare("song_events_queue", true, false, false, false, nil)
	if err != nil {
		return err
	}

	err = ch.QueueBind(queue.Name, "", "song_events", false, nil)
	if err != nil {
		return err
	}

	msgs, err := ch.Consume(queue.Name, "", false, false, false, false, nil)
	if err != nil {
		return err
	}

	go func() {
		for d := range msgs {
			var evt models.SongPlayedEvent
			if err := json.Unmarshal(d.Body, &evt); err != nil {
				log.Printf("❌ Error decodificando evento: %v", err)
				d.Nack(false, false)
				continue
			}

			if err := svc.HandleSongPlayedEvent(ctx, evt); err != nil {
				log.Printf("❌ Error procesando evento: %v", err)
				d.Nack(false, true)
				continue
			}

			d.Ack(false)
			log.Printf("✅ Evento procesado: user=%d, song=%d", evt.UserID, evt.SongID)
		}
	}()

	<-ctx.Done()
	return conn.Close()
}
