package services

import (
	"streaming-service/models"
	"streaming-service/repositories"
	"streaming-service/utils"

	"gorm.io/gorm"
)

type SongService interface {
	GetSongURL(id uint) (string, error) // devuelve la S3 key
	GetSongInfo(id uint) (*models.Song, error)
}

type songService struct {
	repo repositories.SongRepository
}

func NewSongService(db *gorm.DB) SongService {
	repo := repositories.NewSongRepository(db)
	return &songService{repo: repo}
}

// GetSongURL obtiene la URL completa de la BD y extrae la S3 key
func (s *songService) GetSongURL(id uint) (string, error) {
	audioURL, err := s.repo.GetSongURLByID(id)
	if err != nil {
		return "", err
	}

	// Extraer la key de S3 desde la URL
	s3Key, err := utils.ExtractS3KeyFromURL(audioURL)
	if err != nil {
		return "", err
	}

	return s3Key, nil
}

func (s *songService) GetSongInfo(id uint) (*models.Song, error) {
	return s.repo.GetSongInfo(id)
}
