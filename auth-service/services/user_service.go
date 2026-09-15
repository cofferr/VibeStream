// Package services contiene la lógica de negocio para usuarios.
package services

import (
	"auth-service/models"
	"auth-service/repositories"
	"errors"
	"regexp"
	"time"

	"golang.org/x/crypto/bcrypt"
)

// RegisterRequest representa la solicitud para registrar un nuevo usuario.
type RegisterRequest struct {
	Username  string `json:"username" binding:"required,min=3,max=20"`
	Email     string `json:"email" binding:"required,email"`
	Password  string `json:"password" binding:"required,min=8"`
	Birthdate string `json:"birthdate" binding:"required"`
}

// UpdateRequest representa la solicitud para actualizar la información de un usuario.
type UpdateRequest struct {
	Name     string `json:"name"`
	Username string `json:"username"`
	Email    string `json:"email"`
	Password string `json:"password"`
	Birthdate string `json:"birthdate"`
	Role string `json:"role"` // Agregado campo Role
}

// UserResponse representa la respuesta con los datos básicos de un usuario.
type UserResponse struct {
	ID        uint   `json:"id"`
	Name      string `json:"name"`
	Username  string `json:"username"`
	Email     string `json:"email"`
	Role      string `json:"role"`
	Birthdate string `json:"birthdate,omitempty"`
}

// UserDetailResponse representa la respuesta con los datos completos de un usuario.
type UserDetailResponse struct {
	ID                 uint        `json:"id"`
	Name               string      `json:"name"`
	Username           string      `json:"username"`
	Email              string      `json:"email"`
	Role               string      `json:"role"`
	Birthdate          string      `json:"birthdate"`
	RegisterDate       string      `json:"register_date"`
	LastUsernameChange interface{} `json:"last_username_change"`
	LastEmailChange    interface{} `json:"last_email_change"`
	LastPasswordChange interface{} `json:"last_password_change"`
}

// UserServiceInterface define las operaciones disponibles para gestionar usuarios.
type UserServiceInterface interface {
	// RegisterUser registra un nuevo usuario en la base de datos.
	RegisterUser(req RegisterRequest) (*UserResponse, error)

	// UpdateUser actualiza la información de un usuario existente.
	UpdateUser(userID uint, req UpdateRequest) (*UserResponse, error)

	// GetUserDetails obtiene los detalles completos de un usuario.
	GetUserDetails(userID uint) (*UserDetailResponse, error)
}

// UserService implementa UserServiceInterface usando un repositorio de usuarios.
type UserService struct {
	userRepo repositories.UserRepositoryInterface
}

// NewUserService crea una nueva instancia de UserService.
func NewUserService(userRepo repositories.UserRepositoryInterface) UserServiceInterface {
	return &UserService{
		userRepo: userRepo,
	}
}

// RegisterUser registra un nuevo usuario, validando duplicados
// y almacenando la contraseña encriptada.
func (s *UserService) RegisterUser(req RegisterRequest) (*UserResponse, error) {
	birthdate, err := time.Parse("2006-01-02", req.Birthdate)
	if err != nil {
		return nil, errors.New("fecha inválida, formato esperado YYYY-MM-DD")
	}

	_, err = s.userRepo.FindByUsernameOrEmail(req.Username, req.Email)
	if err == nil {
		return nil, errors.New("usuario o email ya registrados")
	}

	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		return nil, errors.New("no se pudo encriptar la contraseña")
	}

	user := &models.User{
		Name:         "user",
		Role:         "user",
		Username:     req.Username,
		Email:        req.Email,
		Password:     string(hashedPassword),
		Birthdate:    birthdate,
		Registerdate: time.Now(),
	}

	if err := s.userRepo.Create(user); err != nil {
		return nil, err
	}

	return &UserResponse{
		ID:        user.ID,
		Username:  user.Username,
		Email:     user.Email,
		Role:      user.Role,
		Birthdate: user.Birthdate.Format("2006-01-02"),
	}, nil
}

// UpdateUser actualiza los datos de un usuario, validando duplicados y formato.
func (s *UserService) UpdateUser(userID uint, req UpdateRequest) (*UserResponse, error) {
    user, err := s.userRepo.FindByID(userID)
    if err != nil {
        return nil, errors.New("usuario no encontrado")
    }

    now := time.Now() // Obtener la hora actual una sola vez
    var updatedFields []string

    if req.Name != "" && req.Name != user.Name {
        user.Name = req.Name
    }

    if req.Username != "" && req.Username != user.Username {
        exists, err := s.userRepo.ExistsByUsername(req.Username)
        if err != nil {
            return nil, errors.New("error al verificar username")
        }
        if exists {
            return nil, errors.New("username ya está en uso")
        }
        user.Username = req.Username
        user.LastUsernameChange = &now // ✅ Actualizar timestamp
        updatedFields = append(updatedFields, "username")
    }

    if req.Email != "" && req.Email != user.Email {
        matched, _ := regexp.MatchString(`^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$`, req.Email)
        if !matched {
            return nil, errors.New("formato de email inválido")
        }

        exists, err := s.userRepo.ExistsByEmail(req.Email)
        if err != nil {
            return nil, errors.New("error al verificar email")
        }
        if exists {
            return nil, errors.New("email ya está en uso")
        }
        user.Email = req.Email
        user.LastEmailChange = &now // ✅ Actualizar timestamp
        updatedFields = append(updatedFields, "email")
    }

    if req.Password != "" {
		if len(req.Password) < 6 {
			return nil, errors.New("la contraseña debe tener al menos 6 caracteres")
		}

		// Verificar si la nueva contraseña es diferente a la actual
		err := bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(req.Password))
		if err != nil { // Si hay error, significa que son diferentes
			hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
			if err != nil {
				return nil, errors.New("no se pudo encriptar la contraseña")
			}
			user.Password = string(hashedPassword)
			user.LastPasswordChange = &now
			updatedFields = append(updatedFields, "password")
		} else {
			// La contraseña es la misma, podrías devolver un mensaje informativo
			// return nil, errors.New("la nueva contraseña no puede ser igual a la actual")
		}
	}

    if req.Birthdate != "" {
        birthdate, err := time.Parse("2006-01-02", req.Birthdate)
        if err != nil {
            return nil, errors.New("fecha de nacimiento inválida, formato esperado YYYY-MM-DD")
        }
        // Solo actualizar si es diferente
        if !birthdate.Equal(user.Birthdate) {
            user.Birthdate = birthdate
            updatedFields = append(updatedFields, "birthdate")
        }
    }

	if req.Role != "" && req.Role != user.Role {
		// validar que el rol sea uno permitido
		validRoles := map[string]bool{
			"user":   true,
			"artist": true,
			"admin":  true,
		}
		if !validRoles[req.Role] {
			return nil, errors.New("rol inválido")
		}
		user.Role = req.Role
		updatedFields = append(updatedFields, "role")
	}

    // Solo actualizar en la base de datos si hay cambios reales
    if len(updatedFields) > 0 {
        if err := s.userRepo.Update(user); err != nil {
            return nil, errors.New("no se pudo actualizar el usuario")
        }
    }

    return &UserResponse{
        ID:        user.ID,
        Name:      user.Name,
        Username:  user.Username,
        Email:     user.Email,
        Role:      user.Role,
        Birthdate: user.Birthdate.Format("2006-01-02"),
    }, nil
}

// GetUserDetails devuelve los detalles completos de un usuario.
func (s *UserService) GetUserDetails(userID uint) (*UserDetailResponse, error) {
	user, err := s.userRepo.FindByID(userID)
	if err != nil {
		return nil, errors.New("usuario no encontrado")
	}

	return &UserDetailResponse{
		ID:                 user.ID,
		Name:               user.Name,
		Username:           user.Username,
		Email:              user.Email,
		Role:               user.Role,
		Birthdate:          user.Birthdate.Format("2006-01-02"),
		RegisterDate:       user.Registerdate.Format("2006-01-02 15:04:05"),
		LastUsernameChange: formatTimePointer(user.LastUsernameChange),
		LastEmailChange:    formatTimePointer(user.LastEmailChange),
		LastPasswordChange: formatTimePointer(user.LastPasswordChange),
	}, nil
}

// formatTimePointer convierte un *time.Time en string formateado o nil.
func formatTimePointer(t *time.Time) interface{} {
	if t == nil {
		return nil
	}
	return t.Format("2006-01-02 15:04:05")
}
