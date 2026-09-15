// src/components/search/AlbumSongsView.jsx
import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContexts';
import { usePlayer } from '@/contexts/PlayerContext';
import { musicAPI } from '@/services/musicService';
import AddToPlaylist from '@/components/playlists/AddToPlaylist';
import { ArrowLeft, Music, Play, Pause, Clock, Eye, Heart } from 'lucide-react';

const AlbumSongsView = ({ album, onBack, onArtistSelect }) => {
  const { authTokens } = useAuth();
  const { playTrack, currentTrack, isPlaying, setQueue } = usePlayer();
  const [songs, setSongs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [albumArtist, setAlbumArtist] = useState(null);

  useEffect(() => {
    if (album) {
      loadAlbumSongs();
      determineAlbumArtist();
    }
  }, [album]);

  // Función para determinar correctamente el artista del álbum
  const determineAlbumArtist = () => {
    console.log('🎵 Estructura completa del álbum:', album);
    
    // Caso 1: Venimos de ArtistAlbumsView - album.artist es un objeto completo
    if (album.artist && typeof album.artist === 'object') {
      setAlbumArtist(album.artist);
    }
    // Caso 2: Venimos de búsqueda directa - album.artist puede ser un objeto con name
    else if (album.artist && album.artist.name) {
      setAlbumArtist(album.artist);
    }
    // Caso 3: El artista está en otra propiedad
    else if (album.artist_name) {
      setAlbumArtist({ name: album.artist_name, id: null });
    }
    // Caso 4: Fallback
    else {
      setAlbumArtist({ name: 'Artista', id: null });
    }
  };

  const loadAlbumSongs = async () => {
    try {
      setLoading(true);
      const response = await musicAPI.getAlbumSongs(album.id, { 
        authTokens: {
          accessToken: authTokens?.accessToken || authTokens?.access
        }
      });

      console.log('🎵 Canciones del álbum:', response);
      const songsData = response.data?.songs || response.songs || [];
      setSongs(songsData);
    } catch (err) {
      console.error('Error cargando canciones del álbum:', err);
      setError('Error al cargar las canciones del álbum');
    } finally {
      setLoading(false);
    }
  };

  // Función para obtener el nombre del artista de forma segura
  const getArtistName = () => {
    if (albumArtist && albumArtist.name) {
      return albumArtist.name;
    }
    return 'Artista';
  };

  // Función para obtener el artista de una canción
  const getSongArtist = (song) => {
    // Prioridad 1: Artistas de la canción (para colaboraciones)
    if (song.artists && song.artists.length > 0) {
      return song.artists.map(artist => artist.name).join(', ');
    }
    // Prioridad 2: Artista del álbum
    return getArtistName();
  };

  const handlePlaySong = (song) => {
    const track = {
      id: song.id,
      title: song.title,
      artist: getSongArtist(song),
      cover: album.cover_url || '/default-cover.png',
      duration: song.duration,
      audio_url: song.audio_url,
    };
    playTrack(track);
  };

  const handlePlayAlbum = () => {
    if (songs.length === 0) return;
    
    const tracks = songs.map(song => ({
      id: song.id,
      title: song.title,
      artist: getSongArtist(song),
      cover: album.cover_url || '/default-cover.png',
      duration: song.duration,
      audio_url: song.audio_url,
    }));
    
    setQueue(tracks);
    playTrack(tracks[0]);
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '0:00';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const formatNumber = (num) => {
    if (!num) return '0';
    return num.toLocaleString();
  };

  if (loading) {
    return <AlbumSongsSkeleton />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <button
          onClick={onBack}
          className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>Volver</span>
        </button>
      </div>

      {/* Información del álbum */}
      <div className="flex items-start space-x-6">
        {album.cover_url ? (
          <img
            src={album.cover_url}
            alt={album.title}
            className="w-48 h-48 object-cover rounded-lg"
          />
        ) : (
          <div className="w-48 h-48 bg-gradient-to-br from-purple-600 to-blue-600 rounded-lg flex items-center justify-center">
            <Music className="w-16 h-16 text-white" />
          </div>
        )}
        
        <div className="flex-1 space-y-4">
          <div>
            <h2 className="text-2xl font-bold">{album.title}</h2>
            {albumArtist && (
              <p 
                className="text-gray-400 hover:text-white cursor-pointer transition-colors"
                onClick={() => onArtistSelect(albumArtist)}
              >
                {getArtistName()}
              </p>
            )}
          </div>
          
          <div className="flex items-center space-x-6 text-sm">
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-400">{songs.length}</div>
              <div className="text-gray-400">Canciones</div>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <button
              onClick={handlePlayAlbum}
              disabled={songs.length === 0}
              className="flex items-center space-x-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed px-4 py-3 rounded-lg transition-colors font-medium"
            >
              <Play className="w-5 h-5" />
              <span>Reproducir Álbum</span>
            </button>
          </div>
        </div>
      </div>

      {/* Lista de canciones */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {songs.length === 0 ? (
        <div className="text-center py-12 bg-gray-800 rounded-lg">
          <Music className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-400 mb-2">No hay canciones</h3>
          <p className="text-gray-500">Este álbum no tiene canciones publicadas.</p>
        </div>
      ) : (
        <div className="bg-gray-800 rounded-lg">
          <SongsListHeader />
          <div className="divide-y divide-gray-700">
            {songs.map((song, index) => (
              <SongRow
                key={song.id}
                song={song}
                index={index}
                isPlaying={currentTrack?.id === song.id && isPlaying}
                onPlay={() => handlePlaySong(song)}
                formatDuration={formatDuration}
                formatNumber={formatNumber}
                artistName={getSongArtist(song)} // Pasamos el nombre del artista calculado
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Componentes auxiliares
const AlbumSongsSkeleton = () => (
  <div className="animate-pulse space-y-6">
    <div className="flex space-x-6">
      <div className="w-48 h-48 bg-gray-700 rounded-lg"></div>
      <div className="flex-1 space-y-4">
        <div className="h-10 bg-gray-700 rounded w-1/3"></div>
        <div className="h-6 bg-gray-700 rounded w-1/4"></div>
        <div className="flex space-x-4">
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

const SongRow = ({ song, index, isPlaying, onPlay, formatDuration, formatNumber, artistName }) => {
  const handleAddToPlaylistSuccess = () => {
    console.log('Canción añadida exitosamente a la playlist');
  };

  const handleAddToPlaylistError = (error) => {
    console.error('Error al añadir canción:', error);
  };

  return (
    <div className="grid grid-cols-12 gap-4 px-6 py-4 items-center hover:bg-gray-750 transition-colors group">
      <div className="col-span-1 text-center">
        <button
          onClick={onPlay}
          className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-600 transition-colors"
        >
          {isPlaying ? (
            <Pause className="w-4 h-4 fill-current text-green-400" />
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
      
      <div className="col-span-6">
        <div className="font-medium">{song.title}</div>
        <div className="text-sm text-gray-400">
          {artistName}
        </div>
      </div>
      
      <div className="col-span-2 text-center text-gray-400 text-sm">
        <div className="flex items-center justify-center space-x-1">
          <Eye className="w-3 h-3" />
          <span>{formatNumber(song.play_count || 0)}</span>
        </div>
      </div>
      
      <div className="col-span-2 text-center text-gray-400">
        {formatDuration(song.duration)}
      </div>

      {/* ✅ NUEVA COLUMNA PARA AÑADIR A PLAYLIST */}
      <div className="col-span-1 text-right">
        <div className="flex items-center justify-end space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button className="p-1 rounded-full hover:bg-gray-600 transition-colors">
            <Heart className="w-4 h-4 text-gray-400 hover:text-red-400" />
          </button>
          
          <AddToPlaylist 
            song={song}
            onSuccess={handleAddToPlaylistSuccess}
            onError={handleAddToPlaylistError}
          />
        </div>
      </div>
    </div>
  );
};

// También actualizar el SongsListHeader para la nueva columna
const SongsListHeader = () => (
  <div className="grid grid-cols-12 gap-4 px-6 py-3 text-gray-400 font-medium border-b border-gray-700">
    <div className="col-span-1 text-center">#</div>
    <div className="col-span-6">Título</div>
    <div className="col-span-2 text-center">
      <Eye className="w-4 h-4 inline mr-1" />
      Plays
    </div>
    <div className="col-span-2 text-center">
      <Clock className="w-4 h-4 inline mr-1" />
      Duración
    </div>
    <div className="col-span-1 text-center">Acciones</div> {/* Nueva columna */}
  </div>
);

export default AlbumSongsView;