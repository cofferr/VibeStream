// Package handlers contiene los handlers del microservicio
package handlers

import (
	"auth-service/services"
	"auth-service/utils"
	"errors"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
)

// GetPublicUser devuelve los campos públicos de un usuario por id, sin
// requerir autenticación. Lo consumen playlist-service y
// subscription-service, que hoy leen la tabla users directamente
// (Fase 3: propiedad de datos por servicio).
func GetPublicUser(userService services.UserServiceInterface) gin.HandlerFunc {
	return func(c *gin.Context) {
		idParam := c.Param("id")
		id, err := strconv.ParseUint(idParam, 10, 64)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "id inválido"})
			return
		}

		user, err := userService.GetPublicUser(uint(id))
		if err != nil {
			statusCode := http.StatusInternalServerError
			publicMsg := "no se pudo obtener el usuario"
			if errors.Is(err, services.ErrUserNotFound) {
				statusCode = http.StatusNotFound
				publicMsg = err.Error()
			}

			utils.RespondError(c, statusCode, err, publicMsg)
			return
		}

		c.JSON(http.StatusOK, gin.H{"user": user})
	}
}
