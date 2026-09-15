package stream

import "io"

// AudioSource define el contrato para cualquier origen de audio
type AudioSource interface {
	GetReader() (io.ReadSeekCloser, error) // obtiene un lector del archivo (con Seek y Close)
	GetSize() int64                        // devuelve tamaño total del recurso
}
