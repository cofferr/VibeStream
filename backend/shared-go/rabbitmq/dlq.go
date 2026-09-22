// Package rabbitmq centraliza la topología de dead-letter compartida por
// los consumers Go (Fase 4). Un mensaje que un consumer rechaza sin
// reintentar (Nack con requeue=false) se pierde silenciosamente si su
// cola no tiene una dead-letter-exchange configurada. Un único DLX
// (fanout) + una cola dlq, iguales a los que usa el lado Python
// (vibestream_common.rabbitmq), centralizan esos mensajes fallidos de
// toda la app en vez de perderlos.
package rabbitmq

import amqp "github.com/rabbitmq/amqp091-go"

const (
	DLXExchange = "dlx"
	DLQQueue    = "dlq"
)

// WorkQueueArgs son los argumentos que debe llevar cualquier cola de
// trabajo para enrutar sus mensajes rechazados al DLX compartido.
// Productor y consumer deben declarar la misma cola con argumentos
// idénticos, o RabbitMQ rechaza la segunda declaración.
func WorkQueueArgs() amqp.Table {
	return amqp.Table{"x-dead-letter-exchange": DLXExchange}
}

// DeclareDLQ declara el exchange dlx (fanout, durable) y la cola dlq
// enlazada a él. Idempotente: seguro de llamar desde cualquier servicio
// que declare colas de trabajo, sin coordinación entre ellos.
func DeclareDLQ(ch *amqp.Channel) error {
	if err := ch.ExchangeDeclare(DLXExchange, "fanout", true, false, false, false, nil); err != nil {
		return err
	}
	queue, err := ch.QueueDeclare(DLQQueue, true, false, false, false, nil)
	if err != nil {
		return err
	}
	return ch.QueueBind(queue.Name, "", DLXExchange, false, nil)
}
