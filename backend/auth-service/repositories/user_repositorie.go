// Package repositories contiene los repositorios para acceder a la base de datos.
package repositories

import (
	"auth-service/models"

	"gorm.io/gorm"
)

// UserRepositoryInterface define las operaciones disponibles
// para interactuar con los usuarios en la base de datos.
type UserRepositoryInterface interface {
	Create(user *models.User) error
	FindByID(id uint) (*models.User, error)
	FindByUsernameOrEmail(username, email string) (*models.User, error)
	ExistsByUsername(username string) (bool, error)
	ExistsByEmail(email string) (bool, error)
	Update(user *models.User) error
}

// UserRepository implementa UserRepositoryInterface
// usando GORM para interactuar con la base de datos.
type UserRepository struct {
	db *gorm.DB
}

// NewUserRepository crea una nueva instancia de UserRepository.
func NewUserRepository(db *gorm.DB) UserRepositoryInterface {
	return &UserRepository{db: db}
}

// Create inserta un nuevo usuario en la base de datos.
func (r *UserRepository) Create(user *models.User) error {
	return r.db.Create(user).Error
}

// FindByID busca un usuario por su ID en la base de datos.
func (r *UserRepository) FindByID(id uint) (*models.User, error) {
	var user models.User
	err := r.db.First(&user, id).Error
	if err != nil {
		return nil, err
	}
	return &user, nil
}

// FindByUsernameOrEmail busca un usuario por su nombre de usuario o email en la base de datos.
func (r *UserRepository) FindByUsernameOrEmail(username, email string) (*models.User, error) {
	var user models.User
	err := r.db.Where("username = ? OR email = ?", username, email).First(&user).Error
	if err != nil {
		return nil, err
	}
	return &user, nil
}

// ExistsByUsername verifica si existe un usuario con el nombre de usuario dado.
func (r *UserRepository) ExistsByUsername(username string) (bool, error) {
	var count int64
	err := r.db.Model(&models.User{}).Where("username = ?", username).Count(&count).Error
	return count > 0, err
}

// ExistsByEmail verifica si existe un usuario con el email dado.
func (r *UserRepository) ExistsByEmail(email string) (bool, error) {
	var count int64
	err := r.db.Model(&models.User{}).Where("email = ?", email).Count(&count).Error
	return count > 0, err
}

// Update actualiza la información de un usuario existente en la base de datos.
func (r *UserRepository) Update(user *models.User) error {
	return r.db.Save(user).Error
}
