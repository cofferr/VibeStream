package models

type Genre struct {
	ID          uint   `gorm:"primaryKey"`
	Name        string `gorm:"uniqueIndex"`
	Description string

	Songs []Song
}
