// Package middleware contiene los middlewares del microservicio
package middleware

import (
	"github.com/gin-gonic/gin"

	"vibestream/shared/authclaims"
)

// AuthMiddleware verifica la validez del token JWT en las solicitudes
// entrantes. Delega en el middleware compartido (vibestream/shared),
// pasando la secret key de este servicio.
func AuthMiddleware(secret string) gin.HandlerFunc {
	return authclaims.AuthMiddleware(secret)
}
