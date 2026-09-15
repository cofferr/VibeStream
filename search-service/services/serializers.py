# services/serializers.py

def serialize_song(song_obj):
    """
    Serializa un objeto Song completo con sus relaciones
    """
    try:
        if not song_obj:
            return None
            
        print(f"🎵 Serializando canción: {getattr(song_obj, 'title', 'Sin título')}")
        
        serialized = {
            "id": song_obj.id,
            "title": getattr(song_obj, 'title', ''),
            "duration": getattr(song_obj, 'duration', None),
            "audio_url": getattr(song_obj, 'audio_url', ''),
            "track_number": getattr(song_obj, 'track_number', None),
            "genre_id": getattr(song_obj, 'genre_id', None),
            "created_at": getattr(song_obj, 'created_at', None),
            "updated_at": getattr(song_obj, 'updated_at', None),
            "album": None,
            "artists": []
        }
        
        # Verificar si el álbum está cargado sin activar lazy loading
        if song_obj.album is not None:
            serialized["album"] = serialize_album(song_obj.album)
        else:
            print(f"   ⚠️ Canción sin álbum cargado: {song_obj.title}")
        
        # Verificar si los artistas están cargados sin activar lazy loading
        if hasattr(song_obj, 'artists') and song_obj.artists is not None:
            for artist in song_obj.artists:
                artist_data = serialize_artist(artist)
                if artist_data:
                    serialized["artists"].append(artist_data)
        
        return serialized
        
    except Exception as e:
        print(f"❌ Error serializando canción: {e}")
        import traceback
        traceback.print_exc()
        return None

def serialize_album(album_obj):
    """
    Serializa un objeto Album completo con sus relaciones
    """
    try:
        if not album_obj:
            return None
            
        serialized = {
            "id": album_obj.id,
            "title": getattr(album_obj, 'title', ''),
            "release_date": getattr(album_obj, 'release_date', None),
            "cover_url": getattr(album_obj, 'cover_url', None),
            "created_at": getattr(album_obj, 'created_at', None),
            "updated_at": getattr(album_obj, 'updated_at', None),
            "artist": None
        }
        
        # Verificar si el artista está cargado sin activar lazy loading
        if album_obj.artist is not None:
            serialized["artist"] = serialize_artist(album_obj.artist)
        
        return serialized
        
    except Exception as e:
        print(f"❌ Error serializando álbum: {e}")
        import traceback
        traceback.print_exc()
        return None

def serialize_artist(artist_obj):
    """
    Serializa un objeto Artist completo con sus relaciones
    """
    try:
        if not artist_obj:
            return None
            
        # Verificar si el user está cargado sin activar lazy loading
        user_data = None
        if artist_obj.user is not None:
            user_data = {
                "id": artist_obj.user.id,
                "name": getattr(artist_obj.user, 'name', None),
                "username": getattr(artist_obj.user, 'username', None)
            }
        
        serialized = {
            "id": artist_obj.id,
            "name": getattr(artist_obj, 'artist_name', 'Artista'),
            "bio": getattr(artist_obj, 'bio', None),
            "profile_pic": getattr(artist_obj, 'profile_pic', None),
            "social_links": getattr(artist_obj, 'social_links', None),
            "created_at": getattr(artist_obj, 'created_at', None),
            "updated_at": getattr(artist_obj, 'updated_at', None),
            "user": user_data
        }
        
        return serialized
        
    except Exception as e:
        print(f"❌ Error serializando artista: {e}")
        import traceback
        traceback.print_exc()
        return None