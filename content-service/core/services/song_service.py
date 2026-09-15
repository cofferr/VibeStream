import tempfile
from pathlib import Path
from mutagen._file import File as MutagenFile
from infrastructure.db.models import Song, Artist
from core.repositories.song_repository import SongRepository
from events.producer import publish_song_created_event, publish_song_updated_event
from core.services.artist_lookup import ArtistLookupService
import re
from sqlalchemy.ext.asyncio import AsyncSession
from config import settings
from infrastructure.storage.s3_client import (
    upload_bytes_to_s3,
    build_s3_public_url,
    delete_from_s3,
    extract_s3_key_from_url,
    get_s3_client,
)


class SongService:
    def __init__(self, repo: SongRepository):
        self.repo = repo

    def _extract_audio_metadata(self, audio_data: bytes, filename: str) -> dict:
        """Extrae metadatos del archivo de audio usando mutagen"""
        try:
            with tempfile.NamedTemporaryFile(
                suffix=Path(filename).suffix, delete=False
            ) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name

            audio_file = MutagenFile(temp_file_path)
            Path(temp_file_path).unlink(missing_ok=True)

            if audio_file is None:
                raise ValueError("Formato de audio no soportado")

            metadata = {
                "duration": int(audio_file.info.length) if audio_file.info else 0,
                "bitrate": getattr(audio_file.info, "bitrate", None),
                "sample_rate": getattr(audio_file.info, "sample_rate", None),
                "channels": getattr(audio_file.info, "channels", None),
            }

            if audio_file.tags:
                metadata.update(
                    {
                        "artist": str(audio_file.tags.get("TPE1", [""])[0])
                        if "TPE1" in audio_file.tags
                        else None,
                        "album": str(audio_file.tags.get("TALB", [""])[0])
                        if "TALB" in audio_file.tags
                        else None,
                        "title": str(audio_file.tags.get("TIT2", [""])[0])
                        if "TIT2" in audio_file.tags
                        else None,
                        "track_number": str(audio_file.tags.get("TRCK", [""])[0]).split(
                            "/"
                        )[0]
                        if "TRCK" in audio_file.tags
                        else None,
                        "genre": str(audio_file.tags.get("TCON", [""])[0])
                        if "TCON" in audio_file.tags
                        else None,
                    }
                )

            print(
                f"[✓] Metadatos extraídos: duración={metadata['duration']}s, bitrate={metadata['bitrate']}"
            )
            return metadata

        except Exception as e:
            print(f"[!] Error extrayendo metadatos: {e}")
            return {"duration": 0}

    def _sanitize_filename(self, name: str) -> str:
        """Sanitiza un nombre para que sea válido como archivo"""
        return re.sub(r"[^a-zA-Z0-9_\- ]+", "", name).strip().replace(" ", "_")

    def _save_audio_file(
        self,
        artist_id: str,
        album_id: str,
        audio_data: bytes,
        title: str,
        original_filename: str,
    ) -> str:
        """Sube un archivo de audio a S3"""
        ext = Path(original_filename).suffix or ".mp3"
        safe_title = self._sanitize_filename(title) or "untitled"
        filename = f"{safe_title}{ext}"
        key = f"{artist_id}/{album_id}/{filename}"

        upload_bytes_to_s3(settings.aws_s3_bucket, key, audio_data, "audio/mpeg")

        audio_url = build_s3_public_url(
            settings.aws_s3_bucket, settings.aws_region, key
        )
        print(f"[✓] Archivo subido a S3: {audio_url}")
        return audio_url

    def _delete_audio_file(self, audio_url: str) -> bool:
        """Elimina el archivo de audio de S3"""
        key = extract_s3_key_from_url(
            audio_url, settings.aws_s3_bucket, settings.aws_region
        )
        if key:
            return delete_from_s3(settings.aws_s3_bucket, key)
        return False

    async def create_song(
        self,
        title: str,
        album_id: int,
        user_id: int,
        audio_file: bytes,
        audio_filename: str,
        db: AsyncSession,
        artist_ids: list[int] | None = None,
        track_number: int | None = None,
        genre_id: int | None = None,
        override_duration: int | None = None,
    ) -> Song:
        """Crea una nueva canción"""
        if not artist_ids:
            artist_id = await ArtistLookupService.get_artist_id_by_user(user_id, db=db)
            if not artist_id:
                raise ValueError(f"No existe artista para el user_id {user_id}")
            artist_ids = [artist_id]

        # Extraer metadatos del audio
        metadata = self._extract_audio_metadata(audio_file, audio_filename)
        duration = (
            override_duration if override_duration is not None else metadata["duration"]
        )

        # Subir archivo a S3
        audio_url = self._save_audio_file(
            str(artist_ids[0]), str(album_id), audio_file, title, audio_filename
        )

        # Fallbacks con metadatos
        if not title and metadata.get("title"):
            title = metadata["title"]
        if track_number is None and metadata.get("track_number"):
            try:
                track_number = int(metadata["track_number"])
            except (ValueError, TypeError):
                pass

        song = Song(
            title=title,
            album_id=album_id,
            duration=duration,
            audio_url=audio_url,
            track_number=track_number,
            genre_id=genre_id,
        )

        # Asociar artistas
        for artist_id in artist_ids:
            artist = await self.repo.session.get(Artist, artist_id)
            if not artist:
                raise ValueError(f"El artista con id {artist_id} no existe")
            song.artists.append(artist)

        song = await self.repo.create(song)

        await publish_song_created_event(
            {
                "id": song.id,
                "title": song.title,
                "album_id": song.album_id,
                "artist_ids": artist_ids,
                "duration": song.duration,
                "audio_url": song.audio_url,
                "track_number": song.track_number,
                "genre_id": song.genre_id,
            }
        )
        return song

    async def update_song(
        self,
        song: Song,
        title: str | None = None,
        track_number: int | None = None,
        genre_id: int | None = None,
        audio_file: bytes | None = None,
        audio_filename: str | None = None,
    ) -> Song:
        """Actualiza una canción existente"""

        # Si se actualiza el título, renombrar archivo en S3
        if title and title != song.title:
            if not song.audio_url:
                raise ValueError("La canción no tiene un archivo de audio asociado")

            old_key = extract_s3_key_from_url(
                song.audio_url, settings.aws_s3_bucket, settings.aws_region
            )

            if old_key:
                try:
                    s3 = get_s3_client()

                    # Descargar archivo actual de S3
                    response = s3.get_object(Bucket=settings.aws_s3_bucket, Key=old_key)
                    audio_data = response["Body"].read()

                    # Crear nuevo key con título sanitizado
                    ext = Path(old_key).suffix or ".mp3"
                    safe_title = self._sanitize_filename(title)
                    new_filename = f"{safe_title}{ext}"

                    # Mantener estructura: artist_id/album_id/filename
                    path_parts = old_key.split("/")
                    if len(path_parts) >= 3:
                        new_key = f"{path_parts[0]}/{path_parts[1]}/{new_filename}"
                    else:
                        artist_id = (
                            song.artists[0].id if song.artists else song.album.artist_id
                        )
                        new_key = f"{artist_id}/{song.album_id}/{new_filename}"

                    # Subir con nuevo nombre
                    upload_bytes_to_s3(
                        settings.aws_s3_bucket, new_key, audio_data, "audio/mpeg"
                    )

                    # Eliminar archivo antiguo
                    delete_from_s3(settings.aws_s3_bucket, old_key)

                    # Actualizar URL
                    song.audio_url = build_s3_public_url(
                        settings.aws_s3_bucket, settings.aws_region, new_key
                    )

                    print(f"[✓] Archivo renombrado en S3: {old_key} -> {new_key}")

                except Exception as e:
                    print(f"[!] Error renombrando archivo en S3: {e}")
                    raise

            song.title = title

        # Si se envía nuevo archivo de audio, reemplazar el existente
        if audio_file and audio_filename:
            # Eliminar archivo anterior de S3
            if song.audio_url:
                self._delete_audio_file(song.audio_url)

            # Subir nuevo archivo a S3
            artist_id = song.artists[0].id if song.artists else song.album.artist_id
            audio_url = self._save_audio_file(
                str(artist_id),
                str(song.album_id),
                audio_file,
                song.title,
                audio_filename,
            )
            song.audio_url = audio_url

            # Actualizar duración con el nuevo archivo
            metadata = self._extract_audio_metadata(audio_file, audio_filename)
            song.duration = metadata.get("duration", 0)

        if track_number is not None:
            song.track_number = track_number
        if genre_id is not None:
            song.genre_id = genre_id

        song = await self.repo.update(song)

        await publish_song_updated_event(
            {
                "id": song.id,
                "title": song.title,
                "album_id": song.album_id,
                "duration": song.duration,
                "audio_url": song.audio_url,
                "track_number": song.track_number,
                "genre_id": song.genre_id,
            }
        )
        return song

    async def delete_song(self, song: Song) -> None:
        """Elimina una canción y su archivo de S3"""
        # Eliminar archivo de audio de S3 si existe
        if song.audio_url:
            self._delete_audio_file(song.audio_url)

        # Eliminar canción de la base de datos
        await self.repo.delete(song)

    async def get_song(self, song_id: int) -> Song | None:
        """Obtiene una canción por ID"""
        return await self.repo.get_by_id(song_id)
