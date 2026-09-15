package stream

import "errors"

// AudioFactory crea la fuente correcta según tipo de origen
func AudioFactory(sourceType, path string) (AudioSource, error) {
	switch sourceType {
	case "local":
		return NewLocalFileSource(path)
	// futuro: "s3", "cdn"
	default:
		return nil, errors.New("source type no soportado")
	}
}
