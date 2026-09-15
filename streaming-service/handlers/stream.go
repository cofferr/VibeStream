package handlers

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"strconv"
	"streaming-service/aws"
	"streaming-service/events"
	"streaming-service/models"
	"streaming-service/services"
	"streaming-service/utils"
	"time"

	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/gin-gonic/gin"
)

// StreamSongHandler transmite la canción usando Range
func StreamSongHandler(songService services.SongService) gin.HandlerFunc {
	return func(c *gin.Context) {
		// Manejar preflight CORS
		if c.Request.Method == "OPTIONS" {
			c.Header("Access-Control-Allow-Methods", "GET, OPTIONS")
			c.Header("Access-Control-Allow-Headers", "Range, Authorization, Content-Type")
			c.Header("Access-Control-Max-Age", "86400")
			c.Status(http.StatusOK)
			return
		}

		// ✅ EL MIDDLEWARE DE AUTENTICACIÓN YA SE ENCARGA DE VALIDAR EL TOKEN
		// El token debe venir en el header: Authorization: Bearer <token>
		// El middleware ya validó el token y estableció user_id en el contexto

		// Verificar que el usuario está autenticado (middleware ya lo hizo)
		userIDAny, exists := c.Get("user_id")
		if !exists {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "usuario no autenticado"})
			return
		}

		userID, ok := userIDAny.(uint)
		if !ok || userID == 0 {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "user_id inválido"})
			return
		}

		fmt.Printf("✅ Usuario autenticado para streaming: userID=%d\n", userID)

		// ✅ CONTINUAR CON LA LÓGICA ORIGINAL DE STREAMING
		idStr := c.Query("id")
		if idStr == "" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "id de canción requerido"})
			return
		}

		id, err := strconv.Atoi(idStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "id inválido"})
			return
		}

		// Obtener la S3 key de la canción
		s3Key, err := songService.GetSongURL(uint(id))
		if err != nil {
			c.JSON(http.StatusNotFound, gin.H{"error": "canción no encontrada: " + err.Error()})
			return
		}

		// Obtener metadata del objeto S3 para conocer el tamaño
		headOutput, err := aws.S3.HeadObject(context.TODO(), &s3.HeadObjectInput{
			Bucket: &aws.Bucket,
			Key:    &s3Key,
		})
		if err != nil {
			c.JSON(http.StatusNotFound, gin.H{"error": "archivo de audio no encontrado en S3: " + err.Error()})
			return
		}

		size := headOutput.ContentLength
		rangeHeader := c.GetHeader("Range")

		c.Header("Accept-Ranges", "bytes")
		c.Header("Content-Type", "audio/mpeg")
		c.Header("Cache-Control", "no-cache")

		if rangeHeader == "" {
			c.Header("Content-Length", fmt.Sprintf("%d", *size))
			c.Status(http.StatusOK)

			publishSongPlayedEvent(c, uint(id))

			// Obtener todo el archivo de S3
			getOutput, err := aws.S3.GetObject(context.TODO(), &s3.GetObjectInput{
				Bucket: &aws.Bucket,
				Key:    &s3Key,
			})
			if err != nil {
				c.JSON(http.StatusInternalServerError, gin.H{"error": "error al obtener archivo de S3: " + err.Error()})
				return
			}
			defer getOutput.Body.Close()

			_, err = io.Copy(c.Writer, getOutput.Body)
			if err != nil {
				fmt.Printf("❌ Error enviando archivo completo: %v\n", err)
			}
			return
		}

		start, end := utils.ParseRange(rangeHeader, *size)
		if start > end || start >= *size {
			c.JSON(http.StatusRequestedRangeNotSatisfiable, gin.H{"error": "rango inválido"})
			return
		}

		length := end - start + 1
		c.Header("Content-Length", fmt.Sprintf("%d", length))
		c.Header("Content-Range", fmt.Sprintf("bytes %d-%d/%d", start, end, *size))
		c.Status(http.StatusPartialContent)

		// Solicitar rango específico de S3
		rangeRequest := fmt.Sprintf("bytes=%d-%d", start, end)
		getOutput, err := aws.S3.GetObject(context.TODO(), &s3.GetObjectInput{
			Bucket: &aws.Bucket,
			Key:    &s3Key,
			Range:  &rangeRequest,
		})
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "error al obtener rango de S3: " + err.Error()})
			return
		}
		defer getOutput.Body.Close()

		buf := make([]byte, 32*1024)
		var sent int64 = 0
		eventSent := false

		for sent < length {
			toRead := int64(len(buf))
			if length-sent < toRead {
				toRead = length - sent
			}

			n, err := getOutput.Body.Read(buf[:toRead])
			if n > 0 {
				_, writeErr := c.Writer.Write(buf[:n])
				if writeErr != nil {
					fmt.Printf("❌ Error escribiendo chunk: %v\n", writeErr)
					break
				}
				sent += int64(n)

				if !eventSent && float64(sent+start)/float64(*size) >= 0.3 {
					publishSongPlayedEvent(c, uint(id))
					eventSent = true
				}
			}

			if err != nil {
				if err != io.EOF {
					fmt.Printf("❌ Error leyendo desde S3: %v\n", err)
				}
				break
			}
		}
	}
}

// Estructura de respuesta para la información de la canción
type SongInfoResponse struct {
	ID          uint             `json:"id"`
	Title       string           `json:"title"`
	Duration    int              `json:"duration"`
	TrackNumber int              `json:"trackNumber"`
	AudioURL    string           `json:"audioUrl"`
	Album       AlbumResponse    `json:"album"`
	Genre       GenreResponse    `json:"genre"`
	Artists     []ArtistResponse `json:"artists"`
	CreatedAt   string           `json:"createdAt"`
}

type AlbumResponse struct {
	ID    uint   `json:"id"`
	Title string `json:"title"`
}

type GenreResponse struct {
	ID   uint   `json:"id"`
	Name string `json:"name"`
}

type ArtistResponse struct {
	ID   uint   `json:"id"`
	Name string `json:"name"`
}

// GetSongInfoHandler devuelve información básica de la canción
func GetSongInfoHandler(songService services.SongService) gin.HandlerFunc {
	return func(c *gin.Context) {
		songIDStr := c.Param("id")
		songID, err := strconv.Atoi(songIDStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "ID de canción inválido"})
			return
		}

		song, err := songService.GetSongInfo(uint(songID))
		if err != nil {
			c.JSON(http.StatusNotFound, gin.H{"error": "Canción no encontrada"})
			return
		}

		// Mapear a la estructura de respuesta
		response := mapSongToResponse(song)
		c.JSON(http.StatusOK, response)
	}
}

// Función helper para mapear el modelo Song a la respuesta
func mapSongToResponse(song *models.Song) SongInfoResponse {
	// Mapear artistas
	artists := make([]ArtistResponse, len(song.Artists))
	for i, artist := range song.Artists {
		artists[i] = ArtistResponse{
			ID: artist.ID,
		}
	}

	return SongInfoResponse{
		ID:          song.ID,
		Title:       song.Title,
		Duration:    song.Duration,
		TrackNumber: song.TrackNumber,
		AudioURL:    song.AudioURL,
		Album: AlbumResponse{
			ID:    song.Album.ID,
			Title: song.Album.Title,
		},
		Genre: GenreResponse{
			ID:   song.Genre.ID,
			Name: song.Genre.Name,
		},
		Artists:   artists,
		CreatedAt: song.CreatedAt.Format(time.RFC3339),
	}
}

// publishSongPlayedEvent publica el evento de canción reproducida
func publishSongPlayedEvent(c *gin.Context, songID uint) {
	userIDAny, exists := c.Get("user_id")
	if !exists {
		fmt.Println("⚠️ No se encontró user_id en el contexto, no se publicará el evento")
		return
	}

	userID, ok := userIDAny.(uint)
	if !ok || userID == 0 {
		fmt.Printf("⚠️ user_id inválido en contexto: %v\n", userIDAny)
		return
	}

	fmt.Printf("✅ Publicando evento: userID=%d, songID=%d\n", userID, songID)
	go events.PublishSongPlayed(userID, songID)
}
