// Package models contiene los modelos de datos del microservicio
package models

import "time"

// RefreshToken representa la tabla 'jwt.refresh_tokens' en la base de datos
type RefreshToken struct {
	ID        uint      `gorm:"primaryKey"`
	UserID    uint      `gorm:"not null"`
	Token     string    `gorm:"not null"`
	ExpiresAt time.Time `gorm:"not null"`
	CreatedAt time.Time `gorm:"autoCreateTime"`
	User      User      `gorm:"foreignKey:UserID;constraint:OnDelete:CASCADE"`
}

// TableName especifica el nombre de la tabla con su esquema
func (RefreshToken) TableName() string {
	return "jwt.refresh_tokens"
}
