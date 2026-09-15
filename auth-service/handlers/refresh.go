package handlers

import (
	"auth-service/config"
	"auth-service/services"
	"net/http"

	"github.com/gin-gonic/gin"
)

// Refresh maneja la renovación del access token usando el refresh token almacenado en una cookie HttpOnly
func Refresh(authService services.AuthServiceInterface) gin.HandlerFunc {
	return func(c *gin.Context) {
		// Obtener refresh token desde la cookie HttpOnly
		refreshToken, err := c.Cookie("refresh_token")
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "refresh token requerido"})
			return
		}

		input := services.RefreshRequest{
			RefreshToken: refreshToken,
		}

		response, err := authService.RefreshToken(input)
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": err.Error()})
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
		})
	}
}
