from fastapi import UploadFile, HTTPException

# Formatos de audio soportados
SUPPORTED_AUDIO_FORMATS = {
    "audio/mpeg": [".mp3"],
    "audio/wav": [".wav"],
    "audio/x-wav": [".wav"],
    "audio/flac": [".flac"],
    "audio/x-flac": [".flac"],
    "audio/mp4": [".m4a", ".mp4"],
    "audio/x-m4a": [".m4a"],
    "audio/ogg": [".ogg"],
    "application/ogg": [".ogg"],
}


def validate_audio_file(audio_file: UploadFile) -> None:
    """Valida que el archivo sea un formato de audio soportado"""
    if (
        not audio_file.content_type
        or audio_file.content_type not in SUPPORTED_AUDIO_FORMATS
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Formato de audio no soportado. "
            f"Formatos permitidos: {', '.join(SUPPORTED_AUDIO_FORMATS.keys())}",
        )

    if not audio_file.filename:
        raise HTTPException(
            status_code=400, detail="El archivo debe tener un nombre válido"
        )

    # Verificar extensión del archivo
    filename_lower = audio_file.filename.lower()
    valid_extensions = []
    for exts in SUPPORTED_AUDIO_FORMATS.values():
        valid_extensions.extend(exts)

    if not any(filename_lower.endswith(ext) for ext in valid_extensions):
        raise HTTPException(
            status_code=400,
            detail=f"Extensión de archivo no válida. "
            f"Extensiones permitidas: {', '.join(valid_extensions)}",
        )
