package handlers

import (
	"errors"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"streaming-service/models"

	"github.com/gin-gonic/gin"
)

// fakeSongService es un doble de prueba de services.SongService. Permite
// probar la lógica de validación/auth de los handlers (que es lo que de
// verdad queremos cubrir con estos tests, ver Fase 1 — sanear errores de
// S3/AWS antes de devolverlos al cliente) sin necesitar credenciales AWS
// reales ni una base de datos.
type fakeSongService struct {
	url     string
	urlErr  error
	info    *models.Song
	infoErr error
}

func (f *fakeSongService) GetSongURL(id uint) (string, error) {
	return f.url, f.urlErr
}
func (f *fakeSongService) GetSongInfo(id uint) (*models.Song, error) {
	return f.info, f.infoErr
}

func init() {
	gin.SetMode(gin.TestMode)
}

func newTestContext(method, target string) (*httptest.ResponseRecorder, *gin.Context) {
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(method, target, nil)
	return w, c
}

func TestStreamSongHandler_NoUserID(t *testing.T) {
	w, c := newTestContext(http.MethodGet, "/stream?id=1")

	StreamSongHandler(&fakeSongService{})(c)

	if w.Code != http.StatusUnauthorized {
		t.Errorf("status = %d, esperaba %d", w.Code, http.StatusUnauthorized)
	}
}

func TestStreamSongHandler_WrongUserIDType(t *testing.T) {
	// El middleware compartido siempre normaliza a uint, pero el handler
	// igual valida el tipo defensivamente — cubrimos que sigue rechazando
	// con 401 si algún día eso deja de ser cierto.
	w, c := newTestContext(http.MethodGet, "/stream?id=1")
	c.Set("user_id", "42") // string en vez de uint

	StreamSongHandler(&fakeSongService{})(c)

	if w.Code != http.StatusUnauthorized {
		t.Errorf("status = %d, esperaba %d", w.Code, http.StatusUnauthorized)
	}
}

func TestStreamSongHandler_MissingSongID(t *testing.T) {
	w, c := newTestContext(http.MethodGet, "/stream")
	c.Set("user_id", uint(1))

	StreamSongHandler(&fakeSongService{})(c)

	if w.Code != http.StatusBadRequest {
		t.Errorf("status = %d, esperaba %d", w.Code, http.StatusBadRequest)
	}
}

func TestStreamSongHandler_InvalidSongID(t *testing.T) {
	w, c := newTestContext(http.MethodGet, "/stream?id=no-es-un-numero")
	c.Set("user_id", uint(1))

	StreamSongHandler(&fakeSongService{})(c)

	if w.Code != http.StatusBadRequest {
		t.Errorf("status = %d, esperaba %d", w.Code, http.StatusBadRequest)
	}
}

func TestStreamSongHandler_SongNotFound_ErrorIsSanitized(t *testing.T) {
	w, c := newTestContext(http.MethodGet, "/stream?id=999")
	c.Set("user_id", uint(1))

	svc := &fakeSongService{urlErr: errors.New("dial tcp 10.0.5.12:5432: connection refused")}
	StreamSongHandler(svc)(c)

	if w.Code != http.StatusNotFound {
		t.Fatalf("status = %d, esperaba %d, body=%s", w.Code, http.StatusNotFound, w.Body.String())
	}
	body := w.Body.String()
	if body == "" {
		t.Fatal("esperaba un body de error")
	}
	if strings.Contains(body, "10.0.5.12") || strings.Contains(body, "connection refused") {
		t.Errorf("el body no debería filtrar el error interno de infraestructura, body=%s", body)
	}
}

func TestGetSongInfoHandler_InvalidID(t *testing.T) {
	w, c := newTestContext(http.MethodGet, "/song/abc/info")
	c.Params = gin.Params{{Key: "id", Value: "abc"}}

	GetSongInfoHandler(&fakeSongService{})(c)

	if w.Code != http.StatusBadRequest {
		t.Errorf("status = %d, esperaba %d", w.Code, http.StatusBadRequest)
	}
}

func TestGetSongInfoHandler_NotFound(t *testing.T) {
	w, c := newTestContext(http.MethodGet, "/song/1/info")
	c.Params = gin.Params{{Key: "id", Value: "1"}}

	svc := &fakeSongService{infoErr: errors.New("record not found")}
	GetSongInfoHandler(svc)(c)

	if w.Code != http.StatusNotFound {
		t.Errorf("status = %d, esperaba %d", w.Code, http.StatusNotFound)
	}
}

func TestGetSongInfoHandler_Success(t *testing.T) {
	w, c := newTestContext(http.MethodGet, "/song/1/info")
	c.Params = gin.Params{{Key: "id", Value: "1"}}

	svc := &fakeSongService{info: &models.Song{
		ID:    1,
		Title: "Una Canción",
		Album: models.Album{ID: 5, Title: "Un Álbum"},
	}}
	GetSongInfoHandler(svc)(c)

	if w.Code != http.StatusOK {
		t.Fatalf("status = %d, esperaba %d, body=%s", w.Code, http.StatusOK, w.Body.String())
	}
	if body := w.Body.String(); !strings.Contains(body, "Una Canción") || !strings.Contains(body, "Un Álbum") {
		t.Errorf("body no incluye los datos esperados: %s", body)
	}
}
