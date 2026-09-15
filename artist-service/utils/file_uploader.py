import os
from fastapi import UploadFile, HTTPException
from config import settings
from typing import Union, Any


class FileUploader:
    """Sube archivos a AWS S3 de forma estructurada."""

    @staticmethod
    async def upload_profile_picture(
        file: UploadFile,
        artist_id: Union[int, Any],
    ) -> str:
        # === Validaciones ===
        if file.content_type not in settings.allowed_image_types:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de archivo no permitido: {file.content_type}",
            )

        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        if file_size > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail="Archivo demasiado grande (máx. 15 MB)",
            )

        # === Estructura de la clave S3 ===
        # s3://<bucket>/<artist_id>/utils/profile_picture.jpg
        artist_id_str = str(artist_id)
        _, ext = os.path.splitext(file.filename or "file.jpg")
        if not ext:
            ext = ".jpg"
        filename = f"profile_picture{ext}"
        key = f"{artist_id_str}/utils/{filename}"

        s3_client = settings.get_s3_client()
        try:
            file_bytes = await file.read()
            s3_client.put_object(
                Bucket=settings.aws_s3_bucket,
                Key=key,
                Body=file_bytes,
                ContentType=file.content_type,
            )
            print(f"✅ Imagen subida a S3: s3://{settings.aws_s3_bucket}/{key}")
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error subiendo a S3: {str(e)}"
            )

        # === URL pública (lectura directa desde AWS) ===
        public_url = f"{settings.get_public_base_url()}/{key}"
        return public_url
