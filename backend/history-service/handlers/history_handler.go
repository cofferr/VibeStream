package handlers

import (
	"history-service/services"
	"net/http"

	"github.com/gin-gonic/gin"
)

type HistoryHandler struct {
	service *services.HistoryService
}

// NewHistoryHandler crea un handler para historial
func NewHistoryHandler(svc *services.HistoryService) *HistoryHandler {
	return &HistoryHandler{service: svc}
}

// GetHistoryHandler devuelve las últimas canciones reproducidas por el usuario
// Se obtiene el user_id desde el JWT en el contexto (middleware)
func (h *HistoryHandler) GetHistoryHandler(c *gin.Context) {
	uidVal, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "usuario no autenticado"})
		return
	}

	// Convertir user_id a uint
	var userID uint
	switch v := uidVal.(type) {
	case float64:
		userID = uint(v)
	case int:
		userID = uint(v)
	case uint:
		userID = v
	default:
		c.JSON(http.StatusInternalServerError, gin.H{"error": "user_id inválido"})
		return
	}

	history, err := h.service.GetUserHistory(userID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "error obteniendo historial"})
		return
	}

	c.JSON(http.StatusOK, history)
}
