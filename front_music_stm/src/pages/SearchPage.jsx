// src/pages/SearchPage.jsx (actualizado)
import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContexts';
import { usePlayer } from '@/contexts/PlayerContext';
import { searchService } from '@/services/searchService';
import SongResults from '@/components/search/SongResults';
import AlbumResults from '@/components/search/AlbumResults';
import ArtistResults from '@/components/search/ArtistResults';
import ArtistAlbumsView from '@/components/search/ArtistAlbumsView';
import AlbumSongsView from '@/components/search/AlbumSongsView';
import { 
  Search, 
  Music, 
  Disc, 
  Users, 
  Loader2 
} from 'lucide-react';

const SearchPage = () => {
  const { authTokens } = useAuth();
  const { playTrack, currentTrack, isPlaying } = usePlayer();
  const [query, setQuery] = useState('');
  const [activeTab, setActiveTab] = useState('songs');
  const [view, setView] = useState('search'); // 'search', 'artistAlbums', 'albumSongs'
  const [selectedArtist, setSelectedArtist] = useState(null);
  const [selectedAlbum, setSelectedAlbum] = useState(null);
  const [results, setResults] = useState({
    songs: { page: 1, results: [], total: 0 },
    albums: { page: 1, results: [], total: 0 },
    artists: { page: 1, results: [], total: 0 },
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);
  
  const searchTimeoutRef = useRef(null);

  // Búsqueda con debounce
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (query.trim().length >= 2) {
      setLoading(true);
      searchTimeoutRef.current = setTimeout(() => {
        performSearch(query);
      }, 500);
    } else if (query.trim().length === 0 && hasSearched) {
      setResults({
        songs: { page: 1, results: [], total: 0 },
        albums: { page: 1, results: [], total: 0 },
        artists: { page: 1, results: [], total: 0 },
      });
      setHasSearched(false);
      setView('search');

    }

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [query]);

  const performSearch = async (searchQuery, pageOverrides = {}) => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    setError(null);
    setHasSearched(true);
    setView('search');

    try {
      const response = await searchService.search(searchQuery, {
        songPage: pageOverrides.songs || results.songs.page,
        albumPage: pageOverrides.albums || results.albums.page,
        artistPage: pageOverrides.artists || results.artists.page,
        limit: 10,
      }, { authTokens });

      setResults(prev => ({
        songs: response.songs || prev.songs,
        albums: response.albums || prev.albums,
        artists: response.artists || prev.artists,
      }));

      // Degub respuesta
      console.log('🔍 Resultados de búsqueda:', response);
      console.log('🔍 Query de búsqueda:', searchQuery);
      console.log('🔍 Páginas de búsqueda:', {  
        songPage: pageOverrides.songs || results.songs.page,
        albumPage: pageOverrides.albums || results.albums.page,
        artistPage: pageOverrides.artists || results.artists.page,
      });

    } catch (err) {
      console.error('Error en búsqueda:', err);
      setError('Error al realizar la búsqueda. Intenta nuevamente.');
    } finally {
      setLoading(false);
    }
  };

  // Handlers para navegación
  const handleArtistSelect = (artist) => {
    setSelectedArtist(artist);
    setView('artistAlbums');
  };

  const handleAlbumSelect = (album) => {
    setSelectedAlbum(album);
    setView('albumSongs');
  };

  const handleBackToSearch = () => {
    setView('search');
    setSelectedArtist(null);
    setSelectedAlbum(null);
  };

  const handleBackFromAlbum = () => {
    if (selectedArtist) {
      setView('artistAlbums');
      setSelectedAlbum(null);
    } else {
      setView('search');
      setSelectedAlbum(null);
    }
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    if (results[tab]?.results?.length === 0 && query.trim() && hasSearched) {
      performSearch(query, { [tab]: 1 });
    }
  };

  const handlePlaySong = (song) => {
    const track = {
      id: song.id,
      title: song.title,
      artist: song.artists?.map(artist => artist.name).join(', ') || 'Artista',
      cover: song.album?.cover_url || '/default-cover.png',
      duration: song.duration,
      audio_url: song.audio_url,
    };
    playTrack(track);
  };

  const handlePageChange = (type, newPage) => {
    setResults(prev => ({
      ...prev,
      [type]: {
        ...prev[type],
        page: newPage
      }
    }));
    
    performSearch(query, { [type]: newPage });
  };

  // Renderizado condicional por vista
  const renderContent = () => {
    switch (view) {
      case 'artistAlbums':
        return (
          <ArtistAlbumsView
            artist={selectedArtist}
            onBack={handleBackToSearch}
            onAlbumSelect={handleAlbumSelect}
          />
        );

      case 'albumSongs':
        return (
          <AlbumSongsView
            album={selectedAlbum}
            onBack={handleBackFromAlbum}
            onArtistSelect={handleArtistSelect}
          />
        );

      case 'search':
      default:
        return renderSearchContent();
    }
  };

  const renderSearchContent = () => {
    if (!hasSearched) {
      return <EmptyState />;
    }

    if (loading) {
      return <LoadingState />;
    }

    const totalResults = results.songs.total + results.albums.total + results.artists.total;
    
    if (totalResults === 0) {
      return <NoResultsState query={query} />;
    }

    return (
      <div className="space-y-6">
        {/* Tabs de navegación */}
        <div className="border-b border-gray-700">
          <nav className="flex space-x-8">
            {[
              { key: 'songs', label: 'Canciones', icon: Music, count: results.songs.total },
              { key: 'albums', label: 'Álbumes', icon: Disc, count: results.albums.total },
              { key: 'artists', label: 'Artistas', icon: Users, count: results.artists.total },
            ].map(({ key, label, icon: Icon, count }) => (
              <button
                key={key}
                onClick={() => handleTabChange(key)}
                className={`py-3 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 transition-colors ${
                  activeTab === key
                    ? 'border-purple-500 text-purple-500'
                    : 'border-transparent text-gray-400 hover:text-gray-300'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{label}</span>
                {count > 0 && (
                  <span className="bg-gray-700 text-gray-300 px-2 py-1 rounded-full text-xs">
                    {count}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>

        {/* Contenido de los tabs */}
        <div>
          {activeTab === 'songs' && (
            <SongResults 
              songs={results.songs.results}
              currentPage={results.songs.page}
              total={results.songs.total}
              onPlaySong={handlePlaySong}
              onPageChange={(page) => handlePageChange('songs', page)}
              formatDuration={(duration) => {
                const minutes = Math.floor(duration / 60);
                const seconds = duration % 60;
                return `${minutes}:${seconds.toString().padStart(2, '0')}`;
              }}
              currentTrack={currentTrack}
              isPlaying={isPlaying}
            />
          )}

          {activeTab === 'albums' && (
            <AlbumResults 
              albums={results.albums.results}
              currentPage={results.albums.page}
              total={results.albums.total}
              onPageChange={(page) => handlePageChange('albums', page)}
              onAlbumSelect={handleAlbumSelect}
            />
          )}

          {activeTab === 'artists' && (
            <ArtistResults 
              artists={results.artists.results}
              currentPage={results.artists.page}
              total={results.artists.total}
              onPageChange={(page) => handlePageChange('artists', page)}
              onArtistSelect={handleArtistSelect}
            />
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header de búsqueda (siempre visible) */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Buscar</h1>
        <div className="relative max-w-2xl">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Busca canciones, álbumes, artistas..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full pl-12 pr-4 py-4 bg-gray-800 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:bg-gray-750 transition-all"
          />
          {loading && (
            <Loader2 className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5 animate-spin" />
          )}
        </div>
      </div>

      {/* Estado de error */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 mb-6">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Contenido principal */}
      {renderContent()}
    </div>
  );
};

// Componente para estado vacío (sin búsqueda)
const EmptyState = () => (
  <div className="text-center py-20">
    <Search className="w-24 h-24 text-gray-600 mx-auto mb-6" />
    <h3 className="text-2xl font-semibold text-gray-400 mb-4">Encuentra tu música favorita</h3>
    <p className="text-gray-500 max-w-md mx-auto">
      Busca canciones, álbumes, artistas y más. Escribe algo en la barra de búsqueda para comenzar.
    </p>
  </div>
);

// Componente para estado de carga
const LoadingState = () => (
  <div className="text-center py-20">
    <Loader2 className="w-12 h-12 text-purple-500 animate-spin mx-auto mb-4" />
    <p className="text-gray-400">Buscando...</p>
  </div>
);

// Componente para sin resultados
const NoResultsState = ({ query }) => (
  <div className="text-center py-20">
    <Search className="w-24 h-24 text-gray-600 mx-auto mb-6" />
    <h3 className="text-2xl font-semibold text-gray-400 mb-2">
      No hay resultados para "{query}"
    </h3>
    <p className="text-gray-500">
      Intenta con otras palabras o verifica la ortografía.
    </p>
  </div>
);

export default SearchPage;