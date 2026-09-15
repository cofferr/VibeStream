// src/components/artist/AlbumDetail.jsx
import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContexts';
import { usePlayer } from '@/contexts/PlayerContext';
import { musicAPI } from '@/services/musicService';
import { 
  Music, 
  Plus, 
  Edit, 
  Trash2, 
  Play, 
  Pause, 
  Clock, 
  MoreVertical, 
  Heart,
  Share,
  Download,
  Eye
} from 'lucide-react';
import UploadSongModal from './UploadSongModal';

const AlbumDetail = ({ album, onAlbumUpdated }) => {
  const { authTokens } = useAuth();
  const { 
    playTrack, 
    currentTrack, 
    isPlaying, 
    setQueue 
  } = usePlayer();
  
  const [songs, setSongs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  // Cargar canciones del álbum cuando cambie el álbum
  useEffect(() => {
    if (album) {
      loadSongs();
    }
  }, [album]);

  const loadSongs = async () => {
    try {
      setLoading(true);
      const songsResponse = await musicAPI.getAlbumSongs(album.id, { 
        authTokens: {
          accessToken: authTokens?.accessToken || authTokens?.access
        }
      });

      console.log('🎵 Canciones cargadas:', songsResponse);
      const songsData = songsResponse.data?.songs || songsResponse.songs || [];
      setSongs(songsData);
    } catch (err) {
      console.error('Error loading songs:', err);
      setError('Error al cargar las canciones del álbum');
    } finally {
      setLoading(false);
    }
  };

  const handleSongUploaded = (newSong) => {
    setSongs(prev => [...prev, newSong]);
    setIsUploadModalOpen(false);
    loadSongs(); // Recargar para obtener datos actualizados
  };

  const handleDeleteSong = async (songId) => {
    if (!window.confirm('¿Estás seguro de eliminar esta canción?')) {
      return;
    }

    try {
      await musicAPI.deleteSong(songId, { 
        authTokens: {
          accessToken: authTokens?.accessToken || authTokens?.access
        }
      });
      setSongs(prev => prev.filter(song => song.id !== songId));
    } catch (error) {
      console.error('Error eliminando canción:', error);
      alert('Error al eliminar la canción');
    }
  };

  // Función para preparar el track para el reproductor
  const prepareTrack = useCallback((song) => ({
    id: song.id,
    title: song.title,
    artist: album.artist_name || 'Artista',
    cover: album.cover_url || '/default-cover.png',
    duration: song.duration,
    play_count: song.play_count,
    like_count: song.like_count
  }), []);

  // Reproducir una canción individual
  const handlePlaySong = useCallback((song) => {
    const track = prepareTrack(song);
    playTrack(track);
  }, [prepareTrack, playTrack]);

  // Reproducir todo el álbum
  const handlePlayAlbum = useCallback(() => {
    if (songs.length === 0) return;
    
    const tracks = songs.map(song => prepareTrack(song));
    setQueue(tracks);
    playTrack(tracks[0]);
  }, [songs, prepareTrack, setQueue, playTrack]);

  const formatDuration = (seconds) => {
    if (!seconds) return '0:00';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'No especificada';
    return new Date(dateString).toLocaleDateString('es-ES');
  };

  const formatNumber = (num) => {
    if (!num) return '0';
    return num.toLocaleString();
  };

  // Calcular estadísticas del álbum
  const albumStats = {
    totalDuration: songs.reduce((total, song) => total + (song.duration || 0), 0),
    totalPlays: songs.reduce((total, song) => total + (song.play_count || 0), 0),
    totalLikes: songs.reduce((total, song) => total + (song.like_count || 0), 0),
  };

  // Estados de carga y error
  if (!album) {
    return (
      <div className="text-center py-12">
        <Music className="w-16 h-16 text-gray-600 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-gray-400 mb-2">Álbum no encontrado</h3>
      </div>
    );
  }

  if (loading) {
    return <AlbumDetailSkeleton />;
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
        <p className="text-red-400">{error}</p>
        <button 
          onClick={loadSongs}
          className="mt-2 bg-red-500 hover:bg-red-600 px-4 py-2 rounded text-white text-sm"
        >
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Portada y información del álbum */}
      <AlbumHeader 
        album={album}
        songsCount={songs.length}
        albumStats={albumStats}
        formatDate={formatDate}
        formatDuration={formatDuration}
        formatNumber={formatNumber}
        onPlayAlbum={handlePlayAlbum}
        onUploadClick={() => setIsUploadModalOpen(true)}
      />

      {/* Lista de canciones */}
      <div className="bg-gray-800 rounded-lg">
        <SongsListHeader />
        
        {songs.length === 0 ? (
          <EmptyState onUploadClick={() => setIsUploadModalOpen(true)} />
        ) : (
          <div className="divide-y divide-gray-700">
            {songs.map((song, index) => (
              <SongRow
                key={song.id}
                song={song}
                index={index}
                isPlaying={currentTrack?.id === song.id && isPlaying}
                onPlay={() => handlePlaySong(song)}
                onPlayAlbum={handlePlayAlbum}
                onDelete={() => handleDeleteSong(song.id)}
                formatDuration={formatDuration}
                formatNumber={formatNumber}
              />
            ))}
          </div>
        )}
      </div>

      {/* Modal para subir canción */}
      <UploadSongModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onSongUploaded={handleSongUploaded}
        albumId={album.id}
      />
    </div>
  );
};

// Componente para el encabezado del álbum
const AlbumHeader = ({ 
  album, 
  songsCount, 
  albumStats, 
  formatDate, 
  formatDuration, 
  formatNumber, 
  onPlayAlbum,
  onUploadClick 
}) => (
  <div className="flex items-start space-x-6">
    {album.cover_url ? (
      <img
        src={album.cover_url}
        alt={album.title}
        className="w-48 h-48 object-cover rounded-lg shadow-lg"
        onError={(e) => {
          console.log('❌ Error cargando imagen del álbum:', album.cover_url);
          e.target.style.display = 'none';
        }}
      />
    ) : (
      <div className="w-48 h-48 bg-gradient-to-br from-purple-600 to-blue-600 rounded-lg flex items-center justify-center shadow-lg">
        <Music className="w-16 h-16 text-white" />
      </div>
    )}
    
    <div className="flex-1 space-y-4">
      <div>
        <h2 className="text-2xl font-bold">{album.title}</h2>
        <p className="text-gray-400">Álbum • {album.artist_name || 'Artista'}</p>
        <p className="text-gray-400">
          Lanzado el {formatDate(album.release_date)}
        </p>
      </div>
      
      {/* Estadísticas del álbum */}
      <div className="flex items-center space-x-6 text-sm">
        <div className="text-center">
          <div className="text-2xl font-bold text-purple-400">{songsCount}</div>
          <div className="text-gray-400">Canciones</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-400">
            {formatDuration(albumStats.totalDuration)}
          </div>
          <div className="text-gray-400">Duración total</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-400">
            {formatNumber(albumStats.totalPlays)}
          </div>
          <div className="text-gray-400">Reproducciones</div>
        </div>
      </div>
      
      <div className="flex items-center space-x-4">
        <button
          onClick={onPlayAlbum}
          disabled={songsCount === 0}
          className="flex items-center space-x-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed px-4 py-3 rounded-lg transition-colors font-medium"
        >
          <Play className="w-5 h-5" />
          <span>Reproducir Álbum</span>
        </button>
        
        <button
          onClick={onUploadClick}
          className="flex items-center space-x-2 bg-purple-600 hover:bg-purple-700 px-4 py-3 rounded-lg transition-colors font-medium"
        >
          <Plus className="w-5 h-5" />
          <span>Subir Canción</span>
        </button>
        
        <button className="flex items-center space-x-2 bg-gray-700 hover:bg-gray-600 px-4 py-3 rounded-lg transition-colors font-medium">
          <Share className="w-5 h-5" />
          <span>Compartir</span>
        </button>
      </div>
    </div>
  </div>
);

// Componente para el encabezado de la lista de canciones
const SongsListHeader = () => (
  <div className="grid grid-cols-12 gap-4 px-6 py-3 text-gray-400 font-medium border-b border-gray-700">
    <div className="col-span-1 text-center">#</div>
    <div className="col-span-5">Título</div>
    <div className="col-span-2 text-center">
      <Eye className="w-4 h-4 inline mr-1" />
      Plays
    </div>
    <div className="col-span-2 text-center">
      <Clock className="w-4 h-4 inline mr-1" />
      Duración
    </div>
    <div className="col-span-2 text-right">Acciones</div>
  </div>
);

// Componente para estado vacío
const EmptyState = ({ onUploadClick }) => (
  <div className="text-center py-12">
    <Music className="w-16 h-16 text-gray-600 mx-auto mb-4" />
    <h3 className="text-xl font-semibold text-gray-400 mb-2">No hay canciones</h3>
    <p className="text-gray-500 mb-6">Sube tu primera canción a este álbum.</p>
    <button
      onClick={onUploadClick}
      className="bg-purple-600 hover:bg-purple-700 px-6 py-3 rounded-lg transition-colors font-medium"
    >
      Subir Canción
    </button>
  </div>
);

// Componente para el skeleton loading
const AlbumDetailSkeleton = () => (
  <div className="animate-pulse space-y-6">
    <div className="flex space-x-6">
      <div className="w-48 h-48 bg-gray-700 rounded-lg"></div>
      <div className="flex-1 space-y-4">
        <div className="h-10 bg-gray-700 rounded w-1/3"></div>
        <div className="h-6 bg-gray-700 rounded w-1/4"></div>
        <div className="flex space-x-4">
          <div className="h-12 bg-gray-700 rounded w-40"></div>
          <div className="h-12 bg-gray-700 rounded w-40"></div>
        </div>
      </div>
    </div>
    <div className="space-y-3">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="h-16 bg-gray-700 rounded"></div>
      ))}
    </div>
  </div>
);

// Componente individual para cada canción
const SongRow = ({ 
  song, 
  index, 
  isPlaying, 
  onPlay, 
  onDelete, 
  formatDuration, 
  formatNumber 
}) => {
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef(null);

  // Cerrar menú al hacer click fuera
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <div className="grid grid-cols-12 gap-4 px-6 py-4 items-center hover:bg-gray-750 transition-colors group relative">
      {/* Número de pista y botón play */}
      <div className="col-span-1 text-center">
        <button
          onClick={onPlay}
          className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-600 transition-colors"
        >
          {isPlaying ? (
            <Pause className="w-4 h-4 fill-current text-purple-400" />
          ) : (
            <>
              <span className="group-hover:hidden text-gray-400 text-sm">
                {index + 1}
              </span>
              <Play className="w-4 h-4 fill-current hidden group-hover:block" />
            </>
          )}
        </button>
      </div>
      
      {/* Información de la canción */}
      <div className="col-span-5">
        <div className="font-medium">{song.title}</div>
        <div className="text-sm text-gray-400">
          {song.artists?.map(artist => artist.artist_name).join(', ') || 'Artista'}
        </div>
      </div>
      
      {/* Estadísticas */}
      <div className="col-span-2 text-center text-gray-400 text-sm">
        <div className="flex items-center justify-center space-x-1">
          <Eye className="w-3 h-3" />
          <span>{formatNumber(song.play_count || 0)}</span>
        </div>
      </div>
      
      {/* Duración */}
      <div className="col-span-2 text-center text-gray-400">
        {formatDuration(song.duration)}
      </div>
      
      {/* Acciones */}
      <div className="col-span-2 text-right">
        <div className="flex items-center justify-end space-x-2">
          {/* Botón de like */}
          <button className="p-1 rounded-full hover:bg-gray-600 transition-colors opacity-0 group-hover:opacity-100">
            <Heart className="w-4 h-4 text-gray-400 hover:text-red-400" />
          </button>
          
          {/* Menú de opciones */}
          <div className="relative inline-block" ref={menuRef}>
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="p-1 rounded-full hover:bg-gray-600 transition-colors opacity-0 group-hover:opacity-100"
            >
              <MoreVertical className="w-4 h-4" />
            </button>

            {/* Menú desplegable */}
            {showMenu && (
              <div className="absolute right-0 top-full mt-1 bg-gray-700 rounded-lg py-1 shadow-lg z-50 min-w-32 border border-gray-600">
                <button
                  onClick={() => {
                    console.log('Editar canción:', song.id);
                    setShowMenu(false);
                  }}
                  className="flex items-center space-x-2 w-full px-3 py-2 text-sm hover:bg-gray-600 transition-colors text-left"
                >
                  <Edit className="w-4 h-4" />
                  <span>Editar</span>
                </button>
                <button
                  onClick={() => {
                    console.log('Descargar canción:', song.id);
                    setShowMenu(false);
                  }}
                  className="flex items-center space-x-2 w-full px-3 py-2 text-sm hover:bg-gray-600 transition-colors text-left"
                >
                  <Download className="w-4 h-4" />
                  <span>Descargar</span>
                </button>
                <button
                  onClick={() => {
                    onDelete(song.id);
                    setShowMenu(false);
                  }}
                  className="flex items-center space-x-2 w-full px-3 py-2 text-sm hover:bg-red-500 hover:bg-opacity-20 text-red-400 transition-colors text-left"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>Eliminar</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlbumDetail;