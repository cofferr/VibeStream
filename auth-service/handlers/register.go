package handlers

import (
	"auth-service/services"
	"net/http"

	"github.com/gin-gonic/gin"
)

// Register maneja el registro de un nuevo usuario
func Register(userService services.UserServiceInterface) gin.HandlerFunc {
	return func(c *gin.Context) {
		var input services.RegisterRequest

		if err := c.ShouldBindJSON(&input); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		user, err := userService.RegisterUser(input)
		if err != nil {
			statusCode := http.StatusInternalServerError

			switch err.Error() {
			case "fecha inválida, formato esperado YYYY-MM-DD":
				statusCode = http.StatusBadRequest
			case "usuario o email ya registrados":
				statusCode = http.StatusConflict
			case "no se pudo encriptar la contraseña":
				statusCode = http.StatusInternalServerError
			}

			c.JSON(statusCode, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusCreated, gin.H{
			"message": "usuario creado exitosamente",
			"user":    user,
		})
	}
}
