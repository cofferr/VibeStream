package models

import "time"

type Album struct {
	ID          uint `gorm:"primaryKey"`
	ArtistID    uint `gorm:"not null;index"`
	Title       string
	ReleaseDate time.Time
	CoverURL    string
	CreatedAt   time.Time
	UpdatedAt   time.Time

	Artist Artist
	Songs  []Song
}
