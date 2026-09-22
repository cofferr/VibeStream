// Package repositories contiene los repositorios para acceder a la base de datos.
package repositories

import (
	"auth-service/models"

	"gorm.io/gorm"
)

// RefreshTokenRepositoryInterface define las operaciones disponibles
// para interactuar con los refresh tokens en la base de datos.
type RefreshTokenRepositoryInterface interface {
	FindByToken(token string) (*models.RefreshToken, error)
	Create(refreshToken *models.RefreshToken) error
	Update(refreshToken *models.RefreshToken) error
	DeleteByUserID(userID uint) error
}

// RefreshTokenRepository implementa RefreshTokenRepositoryInterface
// usando GORM para interactuar con la base de datos.
type RefreshTokenRepository struct {
	db *gorm.DB
}

// NewRefreshTokenRepository crea una nueva instancia de RefreshTokenRepository.
func NewRefreshTokenRepository(db *gorm.DB) RefreshTokenRepositoryInterface {
	return &RefreshTokenRepository{db: db}
}

// FindByToken busca un refresh token por su valor en la base de datos.
func (r *RefreshTokenRepository) FindByToken(token string) (*models.RefreshToken, error) {
	var refreshToken models.RefreshToken
	err := r.db.Where("token = ?", token).First(&refreshToken).Error
	if err != nil {
		return nil, err
	}
	return &refreshToken, nil
}

// Update actualiza un refresh token existente en la base de datos.
func (r *RefreshTokenRepository) Update(refreshToken *models.RefreshToken) error {
	return r.db.Save(refreshToken).Error
}

// DeleteByUserID elimina todos los refresh tokens asociados al ID de un usuario.
func (r *RefreshTokenRepository) DeleteByUserID(userID uint) error {
	return r.db.Where("user_id = ?", userID).Delete(&models.RefreshToken{}).Error
}

// Create inserta un nuevo refresh token en la base de datos.
func (r *RefreshTokenRepository) Create(refreshToken *models.RefreshToken) error {
	return r.db.Create(refreshToken).Error
}
