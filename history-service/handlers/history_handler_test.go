package handlers

import (
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"history-service/models"
	"history-service/services"

	"github.com/gin-gonic/gin"
)

// fakeHistoryRepo es un doble en memoria de repositories.HistoryRepository,
// evitando levantar Postgres solo para probar el handler.
type fakeHistoryRepo struct {
	entries []models.PlayHistoryEntry
	err     error
}

func (f *fakeHistoryRepo) AddEntry(userID, songID uint) error { return nil }
func (f *fakeHistoryRepo) GetUserHistory(userID uint) ([]models.PlayHistoryEntry, error) {
	if f.err != nil {
		return nil, f.err
	}
	return f.entries, nil
}

func init() {
	gin.SetMode(gin.TestMode)
}

func TestGetHistoryHandler_NoUserID(t *testing.T) {
	handler := NewHistoryHandler(services.NewHistoryService(&fakeHistoryRepo{}))

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/history", nil)
	// deliberadamente no seteamos "user_id", como si el middleware de auth
	// no hubiera corrido (o el token no traía el claim)

	handler.GetHistoryHandler(c)

	if w.Code != http.StatusUnauthorized {
		t.Errorf("status = %d, esperaba %d", w.Code, http.StatusUnauthorized)
	}
}

func TestGetHistoryHandler_Success(t *testing.T) {
	repo := &fakeHistoryRepo{entries: []models.PlayHistoryEntry{
		{SongID: 1, SongTitle: "Una Canción", ArtistName: "Un Artista"},
	}}
	handler := NewHistoryHandler(services.NewHistoryService(repo))

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/history", nil)
	// el middleware compartido (shared-go/authclaims) siempre normaliza el
	// claim JWT a uint antes de guardarlo en el contexto
	c.Set("user_id", uint(42))

	handler.GetHistoryHandler(c)

	if w.Code != http.StatusOK {
		t.Fatalf("status = %d, esperaba %d, body=%s", w.Code, http.StatusOK, w.Body.String())
	}

	var got []models.PlayHistoryEntry
	if err := json.Unmarshal(w.Body.Bytes(), &got); err != nil {
		t.Fatalf("respuesta no es JSON válido: %v", err)
	}
	if len(got) != 1 || got[0].SongTitle != "Una Canción" {
		t.Errorf("body = %+v, esperaba una entrada con SongTitle=\"Una Canción\"", got)
	}
}

func TestGetHistoryHandler_RepositoryErrorIsSanitized(t *testing.T) {
	// Fase 1: los errores internos (fallo de BD) no deben filtrarse al
	// cliente como texto crudo, solo un mensaje genérico saneado.
	repo := &fakeHistoryRepo{err: errors.New("pq: connection refused a host interno secreto.db:5432")}
	handler := NewHistoryHandler(services.NewHistoryService(repo))

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/history", nil)
	c.Set("user_id", uint(42))

	handler.GetHistoryHandler(c)

	if w.Code != http.StatusInternalServerError {
		t.Fatalf("status = %d, esperaba %d", w.Code, http.StatusInternalServerError)
	}
	body := w.Body.String()
	if body == "" {
		t.Fatal("esperaba un body de error, vino vacío")
	}
	if strings.Contains(body, "connection refused") || strings.Contains(body, "secreto.db") {
		t.Errorf("el body no debería filtrar el detalle interno del error, body=%s", body)
	}
}
