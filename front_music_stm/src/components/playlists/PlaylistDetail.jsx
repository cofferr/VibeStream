// src/components/playlists/PlaylistDetail.js
import React, { useState, useEffect } from 'react';
import { playlistServices } from '@/services/playlistService';
import PlaylistSongs from './PlaylistSongs';
import PlaylistInfo from './PlaylistInfo';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorMessage from '@/components/ui/ErrorMessage';
import { usePlayer } from '@/contexts/PlayerContext';
import { Play } from 'lucide-react'; // ✅ Añadir Play icon

const PlaylistDetail = ({ playlist, onUpdatePlaylist, authTokens }) => {
  const [songs, setSongs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('songs');
  const { playTrack, currentTrack, isPlaying, setQueue } = usePlayer();

  // Cargar canciones de la playlist
  const loadSongs = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await playlistServices.getPlaylistSongs(playlist.id, authTokens);
      console.log('Loaded playlist songs:', response);
      
      // ✅ YA NO NECESITAMOS MAPEAR - los datos vienen en el formato correcto
      setSongs(response.songs || []);
    } catch (err) {
      setError(err.message);
      console.error('Error loading playlist songs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (playlist) {
      loadSongs();
    }
  }, [playlist]);

  // ✅ FUNCIÓN PARA REPRODUCIR CANCIÓN DESDE PLAYLIST
  const handlePlaySong = (song) => {
    const track = {
      id: song.id,
      title: song.title,
      artist: song.artist_name || 'Artista desconocido',
      cover: song.album_cover || '/default-cover.png', // ✅ Ya viene la URL completa
      duration: song.duration,
      audio_url: song.audio_url, // ✅ Ya viene la URL completa
    };
    playTrack(track);
  };

  // ✅ FUNCIÓN PARA REPRODUCIR TODA LA PLAYLIST
  const handlePlayPlaylist = () => {
    if (songs.length === 0) return;
    
    const tracks = songs.map(song => ({
      id: song.id,
      title: song.title,
      artist: song.artist_name || 'Artista desconocido',
      cover: song.album_cover || '/default-cover.png',
      duration: song.duration,
      audio_url: song.audio_url,
    }));
    
    setQueue(tracks);
    playTrack(tracks[0]);
  };

  // Eliminar canción de la playlist
  const handleRemoveSong = async (songId) => {
    try {
      await playlistServices.removeSongFromPlaylist(playlist.id, songId, authTokens);
      // Actualizar lista localmente
      setSongs(prev => prev.filter(song => song.id !== songId));
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  if (!playlist) return null;

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700">
      {/* Header con tabs */}
      <div className="border-b border-gray-700">
        <nav className="flex -mb-px">
          <button
            onClick={() => setActiveTab('songs')}
            className={`flex-1 py-4 px-6 text-center font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'songs'
                ? 'border-purple-500 text-purple-400'
                : 'border-transparent text-gray-400 hover:text-gray-300'
            }`}
          >
            Canciones ({songs.length})
          </button>
          <button
            onClick={() => setActiveTab('info')}
            className={`flex-1 py-4 px-6 text-center font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'info'
                ? 'border-purple-500 text-purple-400'
                : 'border-transparent text-gray-400 hover:text-gray-300'
            }`}
          >
            Información
          </button>
        </nav>
      </div>

      {/* Contenido de tabs */}
      <div className="p-6">
        {activeTab === 'songs' && (
          <>
            {/* ✅ BOTÓN PARA REPRODUCIR TODA LA PLAYLIST */}
            {songs.length > 0 && (
              <div className="mb-4">
                <button
                  onClick={handlePlayPlaylist}
                  className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors font-medium"
                >
                  <Play className="w-5 h-5" />
                  Reproducir Playlist Completa
                </button>
              </div>
            )}

            {error && (
              <ErrorMessage 
                message={error}
                onRetry={loadSongs}
              />
            )}
            
            {loading ? (
              <LoadingSpinner />
            ) : (
              <PlaylistSongs
                songs={songs}
                onRemoveSong={handleRemoveSong}
                onPlaySong={handlePlaySong}
                currentTrack={currentTrack}
                isPlaying={isPlaying}
              />
            )}
          </>
        )}

        {activeTab === 'info' && (
          <PlaylistInfo
            playlist={playlist}
            onUpdatePlaylist={onUpdatePlaylist}
            songsCount={songs.length}
          />
        )}
      </div>
    </div>
  );
};

export default PlaylistDetail;