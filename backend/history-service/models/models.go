package models

import "time"

// SongPlayedEvent representa el evento que se consume de RabbitMQ
type SongPlayedEvent struct {
	UserID uint `json:"user_id"`
	SongID uint `json:"song_id"`
}

// PlayHistoryEntry representa un registro en el historial de reproducción
type PlayHistoryEntry struct {
	SongID     uint      `json:"song_id"`
	SongTitle  string    `json:"song_title"`
	AlbumID    uint      `json:"album_id"`
	AlbumCover string    `json:"album_cover"`
	ArtistName string    `json:"artist_name"`
	PlayedAt   time.Time `json:"played_at"`
}

// SongStats representa estadísticas de la canción
type SongStats struct {
	SongID uint `json:"song_id"`
	Plays  uint `json:"plays"`
}
