package utils

import (
	"fmt"
	"streaming-service/config"
	"strings"
)

// ExtractS3KeyFromURL extrae la key de S3 desde una URL completa. Reconoce
// tanto el formato real de AWS como el de LocalStack (ver
// content-service/infrastructure/storage/s3_client.py:build_s3_public_url,
// que genera ambos formatos según corresponda — la URL la escribe
// content-service, streaming-service solo la lee).
// Formato AWS:        https://bucket.s3.region.amazonaws.com/key
// Formato LocalStack: http://localstack:4566/bucket/key
func ExtractS3KeyFromURL(url string) (string, error) {
	cfg := config.GetConfig()

	if cfg.AWSEndpointURL != "" {
		prefix := fmt.Sprintf("%s/%s/", cfg.AWSEndpointURL, cfg.AWSS3Bucket)
		if strings.HasPrefix(url, prefix) {
			return strings.TrimPrefix(url, prefix), nil
		}
	}

	prefix := fmt.Sprintf("https://%s.s3.%s.amazonaws.com/", cfg.AWSS3Bucket, cfg.AWSRegion)
	if strings.HasPrefix(url, prefix) {
		return strings.TrimPrefix(url, prefix), nil
	}

	return "", fmt.Errorf("URL inválida o no es de S3: %s", url)
}
