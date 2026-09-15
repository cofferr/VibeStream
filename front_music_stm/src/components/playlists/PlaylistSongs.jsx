// src/components/playlists/PlaylistSongs.js
import React, { useState } from 'react';
import { Trash2, Music, Play, Pause } from 'lucide-react';

const PlaylistSongs = ({ 
  songs, 
  onRemoveSong, 
  onPlaySong, 
  currentTrack, 
  isPlaying 
}) => {
  const [removingId, setRemovingId] = useState(null);

  const handleRemoveSong = async (songId) => {
    setRemovingId(songId);
    const result = await onRemoveSong(songId);
    setRemovingId(null);
    
    if (!result.success) {
      alert(`Error al eliminar canción: ${result.error}`);
    }
  };

  // ✅ FORMATO DE DURACIÓN
  const formatDuration = (seconds) => {
    if (!seconds) return '--:--';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  // ✅ FORMATO DE FECHA
  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  if (songs.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
          <Music size={24} className="text-gray-400" />
        </div>
        <h3 className="text-lg font-medium text-white mb-2">
          No hay canciones en esta playlist
        </h3>
        <p className="text-sm text-gray-400 mb-6">
          Añade canciones desde la búsqueda para empezar a reproducir
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-white">
          Canciones ({songs.length})
        </h3>
      </div>

      {/* ✅ DISEÑO MEJORADO CON MÁS INFORMACIÓN */}
      <div className="bg-gray-750 rounded-lg overflow-hidden">
        {/* Header de la tabla */}
        <div className="grid grid-cols-12 gap-4 px-6 py-3 text-gray-400 font-medium border-b border-gray-700 text-sm">
          <div className="col-span-1"></div>
          <div className="col-span-4">Título</div>
          <div className="col-span-2">Artista</div>
          <div className="col-span-2">Álbum</div>
          <div className="col-span-1 text-center">Duración</div>
          <div className="col-span-2 text-center">Añadida</div>
          <div className="col-span-1"></div>
        </div>

        {/* Lista de canciones */}
        <div className="divide-y divide-gray-700">
          {songs.map((song, index) => {
            const isCurrentTrack = currentTrack?.id === song.id;
            const isPlayingCurrent = isPlaying && isCurrentTrack;

            return (
              <div
                key={song.id} // ✅ KEY ÚNICA
                className="grid grid-cols-12 gap-4 px-6 py-4 items-center hover:bg-gray-700 transition-colors group"
              >
                {/* Botón de reproducción */}
                <div className="col-span-1">
                  <button
                    onClick={() => onPlaySong(song)}
                    className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-600 transition-colors"
                  >
                    {isPlayingCurrent ? (
                      <Pause className="w-4 h-4 fill-current text-green-400" />
                    ) : (
                      <>
                        <span className={`${isCurrentTrack ? 'text-green-400' : 'text-gray-400'} group-hover:hidden text-sm`}>
                          {index + 1}
                        </span>
                        <Play className={`w-4 h-4 fill-current hidden group-hover:block ${isCurrentTrack ? 'text-green-400' : ''}`} />
                      </>
                    )}
                  </button>
                </div>

                {/* Información de la canción con cover */}
                <div className="col-span-4 flex items-center gap-3 min-w-0">
                  <img
                    src={song.album_cover || '/default-cover.png'}
                    alt={song.title}
                    className="w-10 h-10 rounded object-cover flex-shrink-0"
                    onError={(e) => {
                      e.target.src = '/default-cover.png';
                    }}
                  />
                  <div className="min-w-0 flex-1">
                    <h4 className={`font-medium truncate ${isCurrentTrack ? 'text-green-400' : 'text-white'}`}>
                      {song.title}
                    </h4>
                    <p className="text-sm text-gray-400 truncate">
                      {song.album_title || 'Sin álbum'}
                    </p>
                  </div>
                </div>

                {/* Artista */}
                <div className="col-span-2">
                  <p className="text-gray-300 text-sm truncate">
                    {song.artist_name || 'Artista desconocido'}
                  </p>
                </div>

                {/* Álbum */}
                <div className="col-span-2">
                  <p className="text-gray-300 text-sm truncate">
                    {song.album_title || 'Sin álbum'}
                  </p>
                </div>

                {/* Duración */}
                <div className="col-span-1 text-center">
                  <span className={`text-sm ${isCurrentTrack ? 'text-green-400' : 'text-gray-400'}`}>
                    {formatDuration(song.duration)}
                  </span>
                </div>

                {/* Fecha de adición */}
                <div className="col-span-2 text-center">
                  <span className="text-xs text-gray-500">
                    {formatDate(song.added_at)}
                  </span>
                </div>

                {/* Botón eliminar */}
                <div className="col-span-1 text-right">
                  <button
                    onClick={() => handleRemoveSong(song.id)}
                    disabled={removingId === song.id}
                    className="p-2 text-red-400 hover:bg-gray-600 rounded transition-colors disabled:opacity-50 opacity-0 group-hover:opacity-100"
                    title="Eliminar de la playlist"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default PlaylistSongs;