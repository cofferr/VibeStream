# MusicStreaming — Database Schemas

**Proyecto:** MusicStreaming (Supabase / kngarcia's Org)  
**Esquemas:** `jwt`, `music_stm`, `music_streaming`  
**Total de columnas:** 274

---

## Esquema `jwt`

### `refresh_tokens`
| Columna | Tipo |
|---------|------|
| id | integer |
| user_id | integer |
| token | character varying |
| expires_at | timestamp without time zone |
| created_at | timestamp without time zone |

---

## Esquema `music_stm`
> Versión inicial/simplificada del sistema (nombres en español)

### `albumes`
| Columna | Tipo |
|---------|------|
| id_albumes | integer |
| titulo | character varying (45) |
| fecha_lanzamiento | date |
| portada_url | text |
| creado_en | timestamp without time zone |

### `albumes_artistas`
| Columna | Tipo |
|---------|------|
| id_albumes_artistas | integer |
| album_id | integer |
| artista_id | integer |
| rol | character varying (50) |

### `albumes_canciones`
| Columna | Tipo |
|---------|------|
| id_albumes_canciones | integer |
| album_id | integer |
| cancion_id | integer |
| orden | integer |
| nota | character varying (255) |
| creado_en | timestamp without time zone |

### `artistas`
| Columna | Tipo |
|---------|------|
| id_artistas | integer |
| id_usuario | integer |
| nombre_artistico | character varying (45) |
| biografia | text |

### `artistas_canciones`
| Columna | Tipo |
|---------|------|
| id_artistas_canciones | integer |
| artista_id | integer |
| canciones_id | integer |
| rol | character varying (50) |

### `canciones`
| Columna | Tipo |
|---------|------|
| id_canciones | integer |
| titulo | character varying |
| duracion | integer |
| url_audio | text |
| fecha_publicacion | date |

### `canciones_generos`
| Columna | Tipo |
|---------|------|
| canciones_id | integer |
| genero_id | integer |

### `estadisticas_reproducciones`
| Columna | Tipo |
|---------|------|
| id_estadisticas_reproducciones | integer |
| usuario_id | integer |
| cancion_id | integer |
| reproducciones | integer |
| ultima_reproduccion | timestamp without time zone |
| tiempo_total | integer |

### `feedbacks`
| Columna | Tipo |
|---------|------|
| id_feedbacks | integer |
| usuario_id | integer |
| entity_type | character varying |
| entity_id | integer |
| feedback_type | character varying |
| creado_en | timestamp without time zone |

### `generos`
| Columna | Tipo |
|---------|------|
| id_generos | integer |
| nombre | character varying (50) |

### `historial_reproducciones`
| Columna | Tipo |
|---------|------|
| id_historial_reproducciones | integer |
| usuario_id | integer |
| cancion_id | integer |
| fecha_reproduccion | timestamp without time zone |
| duracion_reproducida | integer |
| completada | boolean |

### `playlists`
| Columna | Tipo |
|---------|------|
| id_playlists | integer |
| usuario_id | integer |
| nombre | character varying (50) |
| descripcion | text |
| fecha_creacion | timestamp without time zone |
| fecha_actualizacion | timestamp without time zone |
| es_publica | boolean |
| es_colaborativa | boolean |

### `playlists_canciones`
| Columna | Tipo |
|---------|------|
| id_playlists_canciones | integer |
| playlist_id | integer |
| cancion_id | integer |
| agregado_por | integer |
| posicion | integer |
| fecha_agregado | timestamp without time zone |

### `playlists_colaboradores`
| Columna | Tipo |
|---------|------|
| playlist_id | integer |
| usuario_id | integer |
| agregado_en | timestamp without time zone |

### `playlists_seguidores`
| Columna | Tipo |
|---------|------|
| playlist_id | integer |
| usuario_id | integer |
| fecha_seguimiento | timestamp without time zone |

### `usuarios`
| Columna | Tipo |
|---------|------|
| id_usuarios | integer |
| nombre_usuario | character varying |
| email | character varying |
| password_hash | text |
| rol | text |
| fecha_nacimiento | date |
| fecha_registro | timestamp without time zone |
| last_email_change | timestamp with time zone |
| last_password_change | timestamp with time zone |
| username | character varying |
| last_username_change | timestamp with time zone |

---

## Esquema `music_streaming`
> Versión avanzada del sistema — incluye estadísticas, IA de mood, soft deletes, y características enriquecidas

### `album_stats`
| Columna | Tipo |
|---------|------|
| id | integer |
| album_id | integer |
| year | integer |
| month | integer |
| play_count | integer |
| total_play_count | integer |
| updated_at | timestamp without time zone |

### `albums`
| Columna | Tipo |
|---------|------|
| id | integer |
| artist_id | integer |
| title | character varying |
| release_date | date |
| cover_url | text |
| created_at | date |
| updated_at | date |
| album_type | character varying (20) |
| total_tracks | integer |
| total_plays | integer |
| total_likes | integer |
| deleted_at | timestamp without time zone |

### `artist_stats`
| Columna | Tipo |
|---------|------|
| id | integer |
| artist_id | integer |
| year | integer |
| month | integer |
| play_count | integer |
| total_play_count | integer |
| updated_at | timestamp without time zone |

### `artist_subscriptions`
| Columna | Tipo |
|---------|------|
| user_id | integer |
| artist_id | integer |
| created_at | date |

### `artists`
| Columna | Tipo |
|---------|------|
| id | integer |
| user_id | integer |
| bio | text |
| profile_pic | character varying |
| social_links | json |
| created_at | date |
| updated_at | date |
| artist_name | text |
| banner_pic | text |
| total_followers | integer |
| total_plays | integer |
| monthly_listeners | integer |
| is_verified | boolean |
| verified_at | timestamp without time zone |
| deleted_at | timestamp without time zone |

### `daily_song_stats`
| Columna | Tipo |
|---------|------|
| id | bigint |
| song_id | integer |
| date | date |
| total_plays | integer |
| total_skips | integer |
| total_likes | integer |
| unique_listeners | integer |
| total_duration_played | bigint |
| avg_completion_rate | double precision |
| created_at | timestamp without time zone |

### `genres`
| Columna | Tipo |
|---------|------|
| id | integer |
| name | character varying |
| description | text |

### `mood_session_context`
| Columna | Tipo |
|---------|------|
| id | integer |
| user_id | integer |
| current_dominant_mood | character varying (50) |
| recent_track_ids | json |
| session_start | timestamp without time zone |
| last_updated | timestamp without time zone |
| playback_context_type | character varying (50) |
| context_id | integer |
| is_active | boolean |

### `now_playing`
| Columna | Tipo |
|---------|------|
| id | integer |
| user_id | integer |
| song_id | integer |
| position | integer |
| is_playing | boolean |
| volume | integer |
| repeat_mode | character varying |
| shuffle_enabled | boolean |
| queue_context | character varying |
| queue_context_id | integer |
| started_at | timestamp without time zone |
| updated_at | timestamp without time zone |

### `playlists`
| Columna | Tipo |
|---------|------|
| id | integer |
| user_id | integer |
| name | character varying |
| description | text |
| created_at | date |
| updated_at | date |
| cover_image | text |
| is_public | boolean |
| is_collaborative | boolean |
| total_songs | integer |
| total_duration | integer |
| follower_count | integer |
| play_count | integer |
| deleted_at | timestamp without time zone |

### `search_history`
| Columna | Tipo |
|---------|------|
| id | bigint |
| user_id | integer |
| query | text |
| result_count | integer |
| searched_at | timestamp without time zone |

### `song_artists`
| Columna | Tipo |
|---------|------|
| song_id | integer |
| artist_id | integer |

### `song_stats`
| Columna | Tipo |
|---------|------|
| id | integer |
| song_id | integer |
| year | integer |
| month | integer |
| play_count | integer |
| total_play_count | integer |
| updated_at | timestamp without time zone |

### `songs`
| Columna | Tipo |
|---------|------|
| id | integer |
| album_id | integer |
| genre_id | integer |
| title | character varying |
| duration | integer |
| audio_url | text |
| track_number | integer |
| created_at | date |
| updated_at | date |
| disc_number | integer |
| bitrate | integer |
| sample_rate | integer |
| file_size | bigint |
| file_format | character varying |
| lyrics | text |
| has_lyrics | boolean |
| play_count | integer |
| like_count | integer |
| skip_count | integer |
| is_explicit | boolean |
| is_available | boolean |
| deleted_at | timestamp without time zone |

### `track_mood_features`
| Columna | Tipo |
|---------|------|
| id | integer |
| song_id | integer |
| primary_mood | character varying (50) |
| secondary_mood | character varying (50) |
| tempo | double precision |
| energy | double precision |
| valence | double precision |
| danceability | double precision |
| acousticness | double precision |
| instrumentalness | double precision |
| mood_tags | json |
| mood_confidence | double precision |
| created_at | timestamp without time zone |
| updated_at | timestamp without time zone |

### `user_follows`
| Columna | Tipo |
|---------|------|
| follower_id | integer |
| following_id | integer |
| followed_at | timestamp without time zone |

### `user_likes`
| Columna | Tipo |
|---------|------|
| id | integer |
| user_id | integer |
| entity_type | character varying |
| entity_id | integer |
| liked_at | timestamp without time zone |

### `user_mood_settings`
| Columna | Tipo |
|---------|------|
| id | integer |
| user_id | integer |
| mood_ai_enabled | boolean |
| transition_smoothness | character varying |
| last_toggle_at | timestamp without time zone |
| created_at | timestamp without time zone |
| updated_at | timestamp without time zone |

### `users`
| Columna | Tipo |
|---------|------|
| id | integer |
| name | character varying |
| username | character varying |
| email | character varying |
| password | character varying |
| role | character varying |
| birthdate | date |
| registerdate | date |
| last_username_change | timestamp without time zone |
| last_email_change | timestamp without time zone |
| last_password_change | timestamp without time zone |
| profile_picture | text |
| bio | text |
| last_login | timestamp without time zone |
| deleted_at | timestamp without time zone |
