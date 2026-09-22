#!/bin/sh
# Se ejecuta automáticamente dentro del contenedor de LocalStack una vez
# que el servicio S3 está listo (LocalStack monta este directorio en
# /etc/localstack/init/ready.d/, ver docker-compose.yml). awslocal ya
# viene incluido en la imagen, no hace falta instalarlo en el host.
set -e

BUCKET="${AWS_S3_BUCKET:-vibestream-media}"

echo "[localstack-init] Creando bucket s3://${BUCKET}..."
awslocal s3 mb "s3://${BUCKET}" || true
awslocal s3api put-bucket-cors --bucket "${BUCKET}" --cors-configuration '{
  "CORSRules": [
    {
      "AllowedOrigins": ["*"],
      "AllowedMethods": ["GET", "HEAD"],
      "AllowedHeaders": ["*"]
    }
  ]
}'
echo "[localstack-init] Bucket listo."
