package handlers

import (
	"auth-service/services"
	"auth-service/utils"
	"errors"
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
			utils.RespondError(c, http.StatusBadRequest, err, "datos de solicitud inválidos")
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
			publicMsg := "no se pudo actualizar el usuario"

			switch {
			case errors.Is(err, services.ErrUserNotFound):
				statusCode = http.StatusNotFound
				publicMsg = err.Error()
			case errors.Is(err, services.ErrUsernameTaken),
				errors.Is(err, services.ErrEmailTaken),
				errors.Is(err, services.ErrInvalidEmailFormat),
				errors.Is(err, services.ErrPasswordTooShort),
				errors.Is(err, services.ErrInvalidBirthdateFmt),
				errors.Is(err, services.ErrInvalidRole):
				statusCode = http.StatusBadRequest
				publicMsg = err.Error()
			}

			utils.RespondError(c, statusCode, err, publicMsg)
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"message": "usuario actualizado correctamente",
			"user":    user,
		})
	}
}
