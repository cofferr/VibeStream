package middleware

import (
	"github.com/gin-gonic/gin"

	"vibestream/shared/authclaims"
)

// AuthMiddleware valida el token JWT de acceso usando la secret key que
// recibe por parámetro. Delega en el middleware compartido
// (vibestream/shared).
func AuthMiddleware(secret string) gin.HandlerFunc {
	return authclaims.AuthMiddleware(secret)
}
