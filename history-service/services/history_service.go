package services

import (
	"context"
	"history-service/models"
	"history-service/repositories"
)

// HistoryService encapsula la lógica de historial
type HistoryService struct {
	historyRepo repositories.HistoryRepository
}

// NewHistoryService crea una instancia de HistoryService
func NewHistoryService(hr repositories.HistoryRepository) *HistoryService {
	return &HistoryService{historyRepo: hr}
}

// AddToHistory agrega una canción al historial de un usuario
func (s *HistoryService) AddToHistory(userID, songID uint) error {
	return s.historyRepo.AddEntry(userID, songID)
}

// GetUserHistory obtiene las últimas canciones reproducidas por el usuario
func (s *HistoryService) GetUserHistory(userID uint) ([]models.PlayHistoryEntry, error) {
	return s.historyRepo.GetUserHistory(userID)
}

// HandleSongPlayedEvent procesa un evento de canción reproducida
// Solo añade al historial
func (s *HistoryService) HandleSongPlayedEvent(ctx context.Context, event models.SongPlayedEvent) error {
	return s.AddToHistory(event.UserID, event.SongID)
}
