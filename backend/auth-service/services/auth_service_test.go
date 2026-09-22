package services

import (
	"errors"
	"testing"
	"time"

	"auth-service/config"
	"auth-service/models"

	"golang.org/x/crypto/bcrypt"
)

// fakeUserRepo es un doble de prueba en memoria de UserRepositoryInterface,
// evitando levantar una base de datos real solo para probar la lógica de
// AuthService.Login (que es lo que de verdad queremos cubrir: los errores
// centinela tipados de la Fase 1, no el driver de GORM).
type fakeUserRepo struct {
	byIdentifier map[string]*models.User
}

func (f *fakeUserRepo) Create(user *models.User) error { return nil }
func (f *fakeUserRepo) FindByID(id uint) (*models.User, error) {
	for _, u := range f.byIdentifier {
		if u.ID == id {
			return u, nil
		}
	}
	return nil, errors.New("no encontrado")
}
func (f *fakeUserRepo) FindByUsernameOrEmail(username, email string) (*models.User, error) {
	if u, ok := f.byIdentifier[username]; ok {
		return u, nil
	}
	return nil, errors.New("no encontrado")
}
func (f *fakeUserRepo) ExistsByUsername(username string) (bool, error) { return false, nil }
func (f *fakeUserRepo) ExistsByEmail(email string) (bool, error)       { return false, nil }
func (f *fakeUserRepo) Update(user *models.User) error                 { return nil }

// fakeRefreshTokenRepo es un doble de prueba en memoria de
// RefreshTokenRepositoryInterface.
type fakeRefreshTokenRepo struct {
	created    []*models.RefreshToken
	failCreate bool
}

func (f *fakeRefreshTokenRepo) FindByToken(token string) (*models.RefreshToken, error) {
	return nil, errors.New("no implementado en este test")
}
func (f *fakeRefreshTokenRepo) Create(rt *models.RefreshToken) error {
	if f.failCreate {
		return errors.New("fallo simulado de BD")
	}
	f.created = append(f.created, rt)
	return nil
}
func (f *fakeRefreshTokenRepo) Update(rt *models.RefreshToken) error { return nil }
func (f *fakeRefreshTokenRepo) DeleteByUserID(userID uint) error     { return nil }

func testConfig() {
	config.AppConfig = &config.Config{
		JWTSecret:       "test-secret",
		AccessTokenTTL:  15 * time.Minute,
		RefreshTokenTTL: 168 * time.Hour,
	}
}

func hashPassword(t *testing.T, plain string) string {
	t.Helper()
	hashed, err := bcrypt.GenerateFromPassword([]byte(plain), bcrypt.MinCost)
	if err != nil {
		t.Fatalf("no se pudo hashear la contraseña de prueba: %v", err)
	}
	return string(hashed)
}

func TestLogin_Success(t *testing.T) {
	testConfig()

	userRepo := &fakeUserRepo{byIdentifier: map[string]*models.User{
		"juan": {
			ID:       1,
			Username: "juan",
			Email:    "juan@example.com",
			Password: hashPassword(t, "correcta123"),
			Role:     "user",
		},
	}}
	rtRepo := &fakeRefreshTokenRepo{}

	svc := NewAuthService(userRepo, rtRepo)

	resp, err := svc.Login(LoginRequest{Identifier: "juan", Password: "correcta123"})
	if err != nil {
		t.Fatalf("esperaba login exitoso, obtuve error: %v", err)
	}
	if resp.AccessToken == "" {
		t.Error("esperaba un access_token no vacío")
	}
	if resp.User.Username != "juan" {
		t.Errorf("username = %q, esperaba %q", resp.User.Username, "juan")
	}
	if len(rtRepo.created) != 1 {
		t.Errorf("esperaba que se guardara 1 refresh token, se guardaron %d", len(rtRepo.created))
	}
}

func TestLogin_UserNotFound(t *testing.T) {
	testConfig()

	userRepo := &fakeUserRepo{byIdentifier: map[string]*models.User{}}
	svc := NewAuthService(userRepo, &fakeRefreshTokenRepo{})

	_, err := svc.Login(LoginRequest{Identifier: "no-existe", Password: "cualquiera"})

	if !errors.Is(err, ErrUserNotFound) {
		t.Errorf("error = %v, esperaba ErrUserNotFound (errors.Is)", err)
	}
}

func TestLogin_InvalidPassword(t *testing.T) {
	testConfig()

	userRepo := &fakeUserRepo{byIdentifier: map[string]*models.User{
		"juan": {
			ID:       1,
			Username: "juan",
			Password: hashPassword(t, "correcta123"),
		},
	}}
	svc := NewAuthService(userRepo, &fakeRefreshTokenRepo{})

	_, err := svc.Login(LoginRequest{Identifier: "juan", Password: "incorrecta"})

	if !errors.Is(err, ErrInvalidPassword) {
		t.Errorf("error = %v, esperaba ErrInvalidPassword (errors.Is)", err)
	}
}

func TestLogin_RefreshTokenSaveFails(t *testing.T) {
	testConfig()

	userRepo := &fakeUserRepo{byIdentifier: map[string]*models.User{
		"juan": {
			ID:       1,
			Username: "juan",
			Password: hashPassword(t, "correcta123"),
		},
	}}
	rtRepo := &fakeRefreshTokenRepo{failCreate: true}
	svc := NewAuthService(userRepo, rtRepo)

	_, err := svc.Login(LoginRequest{Identifier: "juan", Password: "correcta123"})

	// Cubre que un fallo real de infraestructura (guardar el refresh
	// token) se mapea al error centinela correcto y no, por ejemplo, a
	// ErrInvalidPassword o a un error genérico sin tipar.
	if !errors.Is(err, ErrRefreshTokenSave) {
		t.Errorf("error = %v, esperaba ErrRefreshTokenSave (errors.Is)", err)
	}
}
