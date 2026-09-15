package models

import "time"

// User representa la tabla 'music_streaming.users' en la base de datos
type User struct {
	ID                 uint      `gorm:"primaryKey;autoIncrement"`
	Name               string    `gorm:"not null"`
	Username           string    `gorm:"uniqueIndex;not null"`
	Email              string    `gorm:"uniqueIndex;not null"`
	Password           string    `gorm:"not null"`
	Role               string    `gorm:"not null"`
	Birthdate          time.Time `gorm:"not null"`
	Registerdate       time.Time `gorm:"autoCreateTime"`
	LastUsernameChange *time.Time
	LastEmailChange    *time.Time
	LastPasswordChange *time.Time
}

// TableName especifica el nombre de la tabla con su esquema.
func (User) TableName() string {
	return "music_streaming.users"
}
