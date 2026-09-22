package dto

type SongDTO struct {
	ID          uint        `json:"id"`
	Title       string      `json:"title"`
	Duration    int         `json:"duration"`
	AudioURL    string      `json:"audio_url"`
	TrackNumber int         `json:"track_number"`
	Album       AlbumDTO    `json:"album"`
	Artists     []ArtistDTO `json:"artists"`
}

type AlbumDTO struct {
	ID          uint   `json:"id"`
	Title       string `json:"title"`
	CoverURL    string `json:"cover_url"`
	ReleaseDate string `json:"release_date"`
}

type ArtistDTO struct {
	ID         uint   `json:"id"`
	Name       string `json:"name"`
	ProfilePic string `json:"profile_pic"`
}
