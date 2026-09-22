# infrastructure/storage/s3_client.py
from botocore.exceptions import ClientError

from config import settings


def get_s3_client():
    return settings.get_s3_client()


def upload_bytes_to_s3(
    bucket: str, key: str, data: bytes, content_type: str | None = None
):
    """Sube bytes a S3 y no devuelve URL."""
    s3 = get_s3_client()
    extra_args = {"ContentType": content_type} if content_type else {}
    s3.put_object(Bucket=bucket, Key=key, Body=data, **extra_args)


def delete_from_s3(bucket: str, key: str) -> bool:
    """
    Elimina un objeto de S3.
    Retorna True si se eliminó correctamente, False si hubo error.
    """
    try:
        s3 = get_s3_client()
        s3.delete_object(Bucket=bucket, Key=key)
        print(f"[✓] Archivo eliminado de S3: {key}")
        return True
    except ClientError as e:
        print(f"[!] Error eliminando archivo de S3: {e}")
        return False


def extract_s3_key_from_url(url: str, bucket: str, region: str) -> str | None:
    """
    Extrae el key de S3 desde una URL pública. Reconoce tanto el formato
    real de AWS como el de LocalStack (settings.aws_endpoint_url) — ver
    build_s3_public_url, que genera ambos formatos según corresponda.
    Ejemplo AWS: https://bucket.s3.region.amazonaws.com/artist/album/file.mp3
    Ejemplo LocalStack: http://localstack:4566/bucket/artist/album/file.mp3
    """
    try:
        prefixes = [f"https://{bucket}.s3.{region}.amazonaws.com/"]
        if settings.aws_endpoint_url:
            prefixes.append(f"{settings.aws_endpoint_url}/{bucket}/")

        for prefix in prefixes:
            if url.startswith(prefix):
                return url[len(prefix):]

        return None
    except Exception as e:
        print(f"[!] Error extrayendo key de URL: {e}")
        return None


def build_s3_public_url(bucket: str, region: str, key: str) -> str:
    """Crea una URL pública del objeto. Si hay un endpoint local
    configurado (LocalStack), apunta ahí en vez del dominio real de AWS
    — el "addressing style" de LocalStack es path-style, no
    virtual-hosted (ver Settings.get_s3_client)."""
    if settings.aws_endpoint_url:
        return f"{settings.aws_endpoint_url}/{bucket}/{key}"
    return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
