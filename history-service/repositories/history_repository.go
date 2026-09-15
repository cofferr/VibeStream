package repositories

import (
	"database/sql"
	"history-service/models"
	"log"
	"time"
)

type historyRepo struct {
	db *sql.DB
}

func NewHistoryRepository(db *sql.DB) HistoryRepository {
	return &historyRepo{db: db}
}

func (r *historyRepo) AddEntry(userID, songID uint) error {
	_, err := r.db.Exec(
		`INSERT INTO music_streaming.play_history (user_id, song_id, played_at) VALUES ($1, $2, $3)`,
		userID, songID, time.Now(),
	)
	return err
}

// GetUserHistory devuelve solo las últimas 15 canciones reproducidas por el usuario
func (r *historyRepo) GetUserHistory(userID uint) ([]models.PlayHistoryEntry, error) {
	query := `
		SELECT 
			s.id as song_id,
			s.title as song_title,
			a.id as album_id,
			a.cover_url as album_cover,
			ar.artist_name
		FROM music_streaming.play_history ph
		JOIN music_streaming.songs s ON s.id = ph.song_id
		JOIN music_streaming.albums a ON a.id = s.album_id
		JOIN music_streaming.artists ar ON ar.id = a.artist_id
		WHERE ph.user_id = $1
		ORDER BY ph.played_at DESC
		LIMIT 15
	`
	rows, err := r.db.Query(query, userID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var entries []models.PlayHistoryEntry
	for rows.Next() {
		var e models.PlayHistoryEntry
		if err := rows.Scan(&e.SongID, &e.SongTitle, &e.AlbumID, &e.AlbumCover, &e.ArtistName); err != nil {
			log.Println("❌ Error scanning play history:", err)
			continue
		}
		entries = append(entries, e)
	}
	return entries, nil
}
