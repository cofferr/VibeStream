// Package authclaims contiene el middleware de validación JWT compartido
// por los servicios Go de VibeStream. Consolida la lógica que estaba
// duplicada (y divergida) en auth-service, history-service y
// streaming-service: parsear el header Authorization, validar la firma
// HMAC, extraer claims y normalizar el tipo de user_id.
package authclaims

import (
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
)

// AuthMiddleware valida el token JWT de acceso usando la secret key que
// recibe por parámetro. Permite solicitudes OPTIONS sin autenticación
// (CORS preflight) y normaliza claims["user_id"] a uint en el contexto,
// sea cual sea el tipo numérico con el que llegó decodificado del JSON.
func AuthMiddleware(secret string) gin.HandlerFunc {
	return func(c *gin.Context) {
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

		claims, ok := token.Claims.(jwt.MapClaims)
		if !ok {
			c.Next()
			return
		}

		c.Set("user", claims)

		if uid, exists := claims["user_id"]; exists {
			userID, ok := normalizeUserID(uid)
			if !ok {
				c.JSON(http.StatusUnauthorized, gin.H{"error": "tipo de user_id no soportado"})
				c.Abort()
				return
			}
			c.Set("user_id", userID)
		}

		if role, exists := claims["role"]; exists {
			c.Set("role", role)
		}

		c.Next()
	}
}

// normalizeUserID convierte los tipos numéricos con los que un claim
// puede llegar decodificado de JSON (float64 típicamente, a veces
// int/int64 si el token se construyó en el mismo proceso) a uint.
func normalizeUserID(v any) (uint, bool) {
	switch n := v.(type) {
	case float64:
		return uint(n), true
	case int:
		return uint(n), true
	case int64:
		return uint(n), true
	case uint:
		return n, true
	default:
		return 0, false
	}
}
