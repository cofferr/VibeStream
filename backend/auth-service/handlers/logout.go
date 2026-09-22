package handlers

import (
	"auth-service/services"
	"net/http"

	"github.com/gin-gonic/gin"
)

// Logout maneja el cierre de sesión de un usuario eliminando su refresh token
func Logout(authService services.AuthServiceInterface) gin.HandlerFunc {
	return func(c *gin.Context) {
		// Obtener user_id del contexto
		userIDAny, exists := c.Get("user_id")
		if !exists {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "usuario no autenticado"})
			return
		}

		// Convertir a uint (manejo robusto de diferentes tipos)
		var userID uint
		switch v := userIDAny.(type) {
		case uint:
			userID = v
		case float64:
			userID = uint(v)
		case int:
			userID = uint(v)
		default:
			c.JSON(http.StatusInternalServerError, gin.H{"error": "error procesando ID de usuario"})
			return
		}

		err := authService.Logout(userID)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "error cerrando sesión"})
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"message": "logged_out",
		})
	}
}
