package models

import "time"

type Song struct {
	ID          uint `gorm:"primaryKey"`
	AlbumID     uint `gorm:"not null;index"`
	GenreID     uint `gorm:"not null;index"`
	Title       string
	Duration    int // segundos
	AudioURL    string
	TrackNumber int
	CreatedAt   time.Time
	UpdatedAt   time.Time

	Album   Album
	Genre   Genre
	Artists []Artist `gorm:"many2many:song_artists"`
}
