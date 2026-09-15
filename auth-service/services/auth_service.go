// Package services contiene la lógica de negocio para autenticación y autorización.
package services

import (
	"auth-service/config"
	"auth-service/models"
	"auth-service/repositories"
	"errors"
	"time"

	"github.com/dgrijalva/jwt-go"
	"github.com/google/uuid"
	"golang.org/x/crypto/bcrypt"
)

// RefreshRequest representa la solicitud para renovar un token de acceso.
type RefreshRequest struct {
	RefreshToken string `json:"refresh_token" binding:"required"`
}

// RefreshResponse representa la respuesta al renovar un token de acceso.
type RefreshResponse struct {
	Message      string `json:"message"`
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	ExpiresIn    int    `json:"expires_in"`
}

// AuthServiceInterface define las operaciones de autenticación
// y manejo de tokens que el servicio debe implementar.
type AuthServiceInterface interface {
	// Login autentica a un usuario con credenciales y genera tokens.
	Login(req LoginRequest) (*LoginResponse, error)

	// RefreshToken genera un nuevo access token a partir de un refresh token válido.
	RefreshToken(req RefreshRequest) (*RefreshResponse, error)

	// Logout elimina los refresh tokens asociados a un usuario.
	Logout(userID uint) error
}

// AuthService implementa AuthServiceInterface, coordinando
// usuarios y refresh tokens a través de repositorios.
type AuthService struct {
	userRepo         repositories.UserRepositoryInterface
	refreshTokenRepo repositories.RefreshTokenRepositoryInterface
}

// NewAuthService crea una nueva instancia de AuthService.
func NewAuthService(userRepo repositories.UserRepositoryInterface, refreshTokenRepo repositories.RefreshTokenRepositoryInterface) AuthServiceInterface {
	return &AuthService{
		userRepo:         userRepo,
		refreshTokenRepo: refreshTokenRepo,
	}
}

// RefreshToken genera un nuevo access token utilizando un refresh token válido.
// Si el refresh token está cerca de expirar, también se rota por uno nuevo.
func (s *AuthService) RefreshToken(req RefreshRequest) (*RefreshResponse, error) {
	now := time.Now()

	stored, err := s.refreshTokenRepo.FindByToken(req.RefreshToken)
	if err != nil {
		return nil, errors.New("no se pudo renovar el token")
	}

	if now.After(stored.ExpiresAt) {
		return nil, errors.New("no se pudo renovar el token")
	}

	user, err := s.userRepo.FindByID(stored.UserID)
	if err != nil {
		return nil, errors.New("no se pudo renovar el token")
	}

	cfg := config.AppConfig

	claims := jwt.MapClaims{
		"user_id":  user.ID,
		"username": user.Username,
		"email":    user.Email,
		"role":     user.Role,
		"exp":      now.Add(cfg.AccessTokenTTL).Unix(),
	}

	accessToken := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	accessTokenString, err := accessToken.SignedString([]byte(cfg.JWTSecret))
	if err != nil {
		return nil, errors.New("no se pudo generar access token")
	}

	if stored.ExpiresAt.Sub(now) < cfg.RefreshTokenTTL/5 {
		stored.Token = uuid.New().String()
		stored.ExpiresAt = now.Add(cfg.RefreshTokenTTL)
		if err := s.refreshTokenRepo.Update(stored); err != nil {
			return nil, errors.New("error actualizando refresh token")
		}
	}

	return &RefreshResponse{
		Message:      "token renovado exitosamente",
		AccessToken:  accessTokenString,
		RefreshToken: stored.Token,
		ExpiresIn:    cfg.GetAccessTokenTTLSeconds(),
	}, nil
}

// Logout elimina todos los refresh tokens asociados al usuario.
func (s *AuthService) Logout(userID uint) error {
	return s.refreshTokenRepo.DeleteByUserID(userID)
}

// LoginRequest representa la solicitud de inicio de sesión
// con identificador (usuario o email) y contraseña.
type LoginRequest struct {
	Identifier string `json:"identifier" binding:"required"`
	Password   string `json:"password" binding:"required"`
}

// LoginResponse representa la respuesta de un inicio de sesión exitoso.
type LoginResponse struct {
	Message      string      `json:"message"`
	AccessToken  string      `json:"access_token"`
	RefreshToken string      `json:"refresh_token"`
	ExpiresIn    int         `json:"expires_in"`
	User         UserSummary `json:"user"`
}

// UserSummary contiene la información básica de un usuario autenticado.
type UserSummary struct {
	ID       uint   `json:"id"`
	Username string `json:"username"`
	Email    string `json:"email"`
	Role     string `json:"role"`
}

// Login autentica al usuario con sus credenciales, genera un access token
// y un refresh token nuevo, eliminando cualquier token previo del usuario.
func (s *AuthService) Login(req LoginRequest) (*LoginResponse, error) {
	user, err := s.userRepo.FindByUsernameOrEmail(req.Identifier, req.Identifier)
	if err != nil {
		return nil, errors.New("usuario no encontrado")
	}

	if err := bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(req.Password)); err != nil {
		return nil, errors.New("contraseña incorrecta")
	}

	cfg := config.AppConfig

	claims := jwt.MapClaims{
		"user_id":  user.ID,
		"username": user.Username,
		"email":    user.Email,
		"role":     user.Role,
		"exp":      time.Now().Add(cfg.AccessTokenTTL).Unix(),
	}

	accessToken := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	accessTokenString, err := accessToken.SignedString([]byte(cfg.JWTSecret))
	if err != nil {
		return nil, errors.New("no se pudo generar access token")
	}

	refreshToken := uuid.New().String()
	expiry := time.Now().Add(cfg.RefreshTokenTTL)

	s.refreshTokenRepo.DeleteByUserID(user.ID)

	newRT := &models.RefreshToken{
		UserID:    user.ID,
		Token:     refreshToken,
		ExpiresAt: expiry,
	}

	if err := s.refreshTokenRepo.Create(newRT); err != nil {
		return nil, errors.New("no se pudo guardar refresh token")
	}

	return &LoginResponse{
		Message:      "login exitoso",
		AccessToken:  accessTokenString,
		RefreshToken: refreshToken,
		ExpiresIn:    cfg.GetAccessTokenTTLSeconds(),
		User: UserSummary{
			ID:       user.ID,
			Username: user.Username,
			Email:    user.Email,
			Role:     user.Role,
		},
	}, nil
}
