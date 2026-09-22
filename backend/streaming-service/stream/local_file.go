package stream

import (
	"io"
	"os"
)

// LocalFileSource implementa AudioSource para archivos locales
type LocalFileSource struct {
	path string
	size int64
}

// NewLocalFileSource constructor para inicializar LocalFileSource correctamente
func NewLocalFileSource(path string) (*LocalFileSource, error) {
	info, err := os.Stat(path)
	if err != nil {
		return nil, err
	}

	return &LocalFileSource{
		path: path,
		size: info.Size(),
	}, nil
}

func (l *LocalFileSource) GetReader() (io.ReadSeekCloser, error) {
	return os.Open(l.path) // *os.File implementa io.ReadSeekCloser
}

func (l *LocalFileSource) GetSize() int64 {
	return l.size
}
