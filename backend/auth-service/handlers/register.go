package handlers

import (
	"auth-service/services"
	"auth-service/utils"
	"errors"
	"net/http"

	"github.com/gin-gonic/gin"
)

// Register maneja el registro de un nuevo usuario
func Register(userService services.UserServiceInterface) gin.HandlerFunc {
	return func(c *gin.Context) {
		var input services.RegisterRequest

		if err := c.ShouldBindJSON(&input); err != nil {
			utils.RespondError(c, http.StatusBadRequest, err, "datos de solicitud inválidos")
			return
		}

		user, err := userService.RegisterUser(input)
		if err != nil {
			statusCode := http.StatusInternalServerError
			publicMsg := "no se pudo registrar el usuario"

			switch {
			case errors.Is(err, services.ErrInvalidBirthdate):
				statusCode = http.StatusBadRequest
				publicMsg = err.Error()
			case errors.Is(err, services.ErrUserAlreadyExists):
				statusCode = http.StatusConflict
				publicMsg = err.Error()
			}

			utils.RespondError(c, statusCode, err, publicMsg)
			return
		}

		c.JSON(http.StatusCreated, gin.H{
			"message": "usuario creado exitosamente",
			"user":    user,
		})
	}
}
