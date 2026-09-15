package utils

import (
	"fmt"
	"streaming-service/config"
	"strings"
)

// ExtractS3KeyFromURL extrae la key de S3 desde una URL completa de AWS S3
// Formato esperado: https://bucket.s3.region.amazonaws.com/key
func ExtractS3KeyFromURL(url string) (string, error) {
	cfg := config.GetConfig()

	// Para AWS S3: https://bucket.s3.region.amazonaws.com/key
	prefix := fmt.Sprintf("https://%s.s3.%s.amazonaws.com/", cfg.AWSS3Bucket, cfg.AWSRegion)
	if strings.HasPrefix(url, prefix) {
		return strings.TrimPrefix(url, prefix), nil
	}

	// Si no coincide con el patrón AWS, retornar error
	return "", fmt.Errorf("URL inválida o no es de AWS S3: %s (esperado: %s...)", url, prefix)
}
