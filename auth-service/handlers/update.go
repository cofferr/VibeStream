package handlers

import (
	"auth-service/services"
	"net/http"

	"github.com/gin-gonic/gin"
)

// UpdateUser maneja la actualización de la información del usuario verificando la identidad mediante el user_id del JWT
func UpdateUser(userService services.UserServiceInterface) gin.HandlerFunc {
	return func(c *gin.Context) {
		// Obtener el user_id del JWT
		uid, exists := c.Get("user_id")
		if !exists {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "usuario no autenticado"})
			return
		}

		var input services.UpdateRequest
		if err := c.ShouldBindJSON(&input); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		var userID uint
		switch v := uid.(type) {
		case uint:
			userID = v
		case float64:
			userID = uint(v)
		case int:
			userID = uint(v)
		default:
			c.JSON(http.StatusInternalServerError, gin.H{"error": "error en la autenticación"})
			return
		}

		user, err := userService.UpdateUser(userID, input)
		if err != nil {
			statusCode := http.StatusInternalServerError

			switch err.Error() {
			case "usuario no encontrado":
				statusCode = http.StatusNotFound
			case "username ya está en uso", "email ya está en uso", "formato de email inválido", "la contraseña debe tener al menos 6 caracteres":
				statusCode = http.StatusBadRequest
			}

			c.JSON(statusCode, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"message": "usuario actualizado correctamente",
			"user":    user,
		})
	}
}
