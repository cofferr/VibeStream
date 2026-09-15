package models

import (
	"time"

	"gorm.io/datatypes"
)

type Artist struct {
	ID          uint `gorm:"primaryKey"`
	UserID      uint `gorm:"not null;uniqueIndex"`
	Bio         string
	ProfilePic  string
	SocialLinks datatypes.JSON
	CreatedAt   time.Time
	UpdatedAt   time.Time

	Albums []Album
	Songs  []Song `gorm:"many2many:song_artists"`
}
