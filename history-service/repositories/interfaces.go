package repositories

import "history-service/models"

// HistoryRepository maneja operaciones sobre historial de reproducciones
type HistoryRepository interface {
	AddEntry(userID, songID uint) error
	GetUserHistory(userID uint) ([]models.PlayHistoryEntry, error)
}
