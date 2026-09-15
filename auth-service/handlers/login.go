package handlers

import (
	"auth-service/config"
	"auth-service/services"
	"auth-service/utils"
	"errors"
	"net/http"

	"github.com/gin-gonic/gin"
)

// Login maneja el inicio de sesión de un usuario
func Login(authService services.AuthServiceInterface) gin.HandlerFunc {
	return func(c *gin.Context) {
		var input services.LoginRequest

		if err := c.ShouldBindJSON(&input); err != nil {
			utils.RespondError(c, http.StatusBadRequest, err, "datos de solicitud inválidos")
			return
		}

		response, err := authService.Login(input)
		if err != nil {
			statusCode := http.StatusInternalServerError
			publicMsg := "no se pudo iniciar sesión"

			switch {
			case errors.Is(err, services.ErrUserNotFound), errors.Is(err, services.ErrInvalidPassword):
				statusCode = http.StatusUnauthorized
				publicMsg = "credenciales inválidas"
			}

			utils.RespondError(c, statusCode, err, publicMsg)
			return
		}

		cfg := config.AppConfig

		c.SetSameSite(http.SameSiteStrictMode)
		c.SetCookie(
			"refresh_token",
			response.RefreshToken,
			cfg.GetRefreshTokenTTLSeconds(),
			"/",
			"",
			false,
			true,
		)

		c.JSON(http.StatusOK, gin.H{
			"message":      response.Message,
			"access_token": response.AccessToken,
			"expires_in":   response.ExpiresIn,
			"user":         response.User,
		})
	}
}
