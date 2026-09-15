package handlers

import (
	"auth-service/config"
	"auth-service/services"
	"net/http"

	"github.com/gin-gonic/gin"
)

// Login maneja el inicio de sesión de un usuario
func Login(authService services.AuthServiceInterface) gin.HandlerFunc {
	return func(c *gin.Context) {
		var input services.LoginRequest

		if err := c.ShouldBindJSON(&input); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		response, err := authService.Login(input)
		if err != nil {
			statusCode := http.StatusInternalServerError

			switch err.Error() {
			case "usuario no encontrado", "contraseña incorrecta":
				statusCode = http.StatusUnauthorized
			case "no se pudo generar access token", "no se pudo guardar refresh token", "error limpiando tokens anteriores":
				statusCode = http.StatusInternalServerError
			}

			c.JSON(statusCode, gin.H{"error": err.Error()})
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
