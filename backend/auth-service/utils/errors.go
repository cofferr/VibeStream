// Package utils contiene helpers compartidos del microservicio.
package utils

import (
	"log"

	"github.com/gin-gonic/gin"
)

// RespondError loguea el error real server-side y devuelve al cliente
// únicamente el mensaje público saneado, evitando filtrar detalles
// internos (mensajes de driver de BD, stacktraces, etc.) en la respuesta.
func RespondError(c *gin.Context, status int, logErr error, publicMsg string) {
	if logErr != nil {
		log.Printf("❌ %s: %v", publicMsg, logErr)
	}
	c.JSON(status, gin.H{"error": publicMsg})
}
