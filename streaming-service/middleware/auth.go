package middleware

import (
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
)

// AuthMiddleware valida el token JWT de acceso usando la secret key que recibe por parámetro
func AuthMiddleware(secret string) gin.HandlerFunc {
	return func(c *gin.Context) {
		// Permitir OPTIONS para CORS preflight
		if c.Request.Method == "OPTIONS" {
			c.Next()
			return
		}

		authHeader := c.GetHeader("Authorization")
		if !strings.HasPrefix(authHeader, "Bearer ") {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "token requerido"})
			c.Abort()
			return
		}

		tokenString := strings.TrimPrefix(authHeader, "Bearer ")

		// Parsear y validar token
		token, err := jwt.Parse(tokenString, func(token *jwt.Token) (any, error) {
			if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
				return nil, jwt.ErrSignatureInvalid
			}
			return []byte(secret), nil
		})

		if err != nil || !token.Valid {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "token inválido o expirado"})
			c.Abort()
			return
		}

		// Extraer claims y guardarlos en el contexto
		if claims, ok := token.Claims.(jwt.MapClaims); ok {
			c.Set("user", claims)
			
			// Manejar diferentes tipos de user_id
			if uid, exists := claims["user_id"]; exists {
				switch v := uid.(type) {
				case float64:
					c.Set("user_id", uint(v))
				case int:
					c.Set("user_id", uint(v))
				case int64:
					c.Set("user_id", uint(v))
				default:
					c.JSON(http.StatusUnauthorized, gin.H{"error": "tipo de user_id no soportado"})
					c.Abort()
					return
				}
			}
			
			if role, exists := claims["role"]; exists {
				c.Set("role", role)
			}
		}

		c.Next()
	}
}