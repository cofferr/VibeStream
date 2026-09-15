  // src/components/search/ArtistAlbumsView.jsx
  import { useState, useEffect } from 'react';
  import { useAuth } from '@/contexts/AuthContexts';
  import { musicAPI } from '@/services/musicService';
  import { ArrowLeft, Music, Play, Clock, Calendar } from 'lucide-react';

  const ArtistAlbumsView = ({ artist, onBack, onAlbumSelect }) => {
    const { authTokens } = useAuth();
    const [albums, setAlbums] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
      if (artist) {
        loadArtistAlbums();
      }
    }, [artist]);

    // En ArtistAlbumsView.jsx - en la función loadArtistAlbums
    const loadArtistAlbums = async () => {
      try {
        setLoading(true);
        const response = await musicAPI.getArtistAlbums(artist.id, { 
          authTokens: {
            accessToken: authTokens?.accessToken || authTokens?.access
          }
        });
        
        console.log('📀 Álbumes del artista:', response);
        let albumsData = response.data?.albums || response.albums || [];
        
        // Asegurarnos de que cada álbum tenga la información del artista con estructura consistente
        albumsData = albumsData.map(album => ({
          ...album,
          artist: {
            name: artist.name,
          }
        }));
        
        setAlbums(albumsData);
        
      } catch (err) {
        console.error('Error cargando álbumes del artista:', err);
        setError('Error al cargar los álbumes del artista');
      } finally {
        setLoading(false);
      }
    };

    const formatDate = (dateString) => {
      if (!dateString) return 'No especificada';
      return new Date(dateString).toLocaleDateString('es-ES');
    };

    if (loading) {
      return (
        <div className="animate-pulse space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="flex items-center space-x-4 p-4 bg-gray-800 rounded-lg">
              <div className="w-16 h-16 bg-gray-700 rounded"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-700 rounded w-1/3"></div>
                <div className="h-3 bg-gray-700 rounded w-1/4"></div>
              </div>
            </div>
          ))}
        </div>
      );
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
            <span>Volver a búsqueda</span>
          </button>
        </div>

        {/* Información del artista */}
        <div className="flex items-center space-x-4 p-6 bg-gray-800 rounded-lg">
          {artist.profile_pic ? (
            <img
              src={artist.profile_pic}
              alt={artist.name}
              className="w-20 h-20 rounded-full object-cover"
            />
          ) : (
            <div className="w-20 h-20 bg-gradient-to-br from-purple-600 to-blue-600 rounded-full flex items-center justify-center">
              <Music className="w-8 h-8 text-white" />
            </div>
          )}
          <div>
            <h2 className="text-2xl font-bold">{artist.name}</h2>
            <p className="text-gray-400">{albums.length} álbumes</p>
          </div>
        </div>

        {/* Lista de álbumes */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {albums.length === 0 ? (
          <div className="text-center py-12 bg-gray-800 rounded-lg">
            <Music className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-400 mb-2">No hay álbumes</h3>
            <p className="text-gray-500">Este artista no tiene álbumes publicados.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {albums.map((album) => (
              <AlbumCard 
                key={album.id} 
                album={album} 
                onSelect={onAlbumSelect}
                formatDate={formatDate}
              />
            ))}
          </div>
        )}
      </div>
    );
  };

  // Componente individual de álbum
  const AlbumCard = ({ album, onSelect, formatDate }) => {
    return (
      <div 
        className="bg-gray-800 rounded-lg p-4 hover:bg-gray-750 transition-colors cursor-pointer group"
        onClick={() => onSelect(album)}
      >
        <div className="relative mb-4">
          {album.cover_url ? (
            <img
              src={album.cover_url}
              alt={album.title}
              className="w-full aspect-square object-cover rounded-lg"
            />
          ) : (
            <div className="w-full aspect-square bg-gradient-to-br from-purple-600 to-blue-600 rounded-lg flex items-center justify-center">
              <Music className="w-12 h-12 text-white" />
            </div>
          )}
          
          {/* Overlay con botón play */}
          <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-40 transition-opacity rounded-lg flex items-center justify-center opacity-0 group-hover:opacity-100">
            <div className="bg-green-500 p-3 rounded-full transform scale-0 group-hover:scale-100 transition-transform">
              <Play className="w-6 h-6 text-white fill-current" />
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <h3 className="font-semibold text-lg truncate" title={album.title}>
            {album.title}
          </h3>
          
          <div className="flex items-center space-x-1 text-sm text-gray-400">
            <Calendar className="w-4 h-4" />
            <span>{formatDate(album.release_date)}</span>
          </div>

          {album.song_count && (
            <div className="flex items-center space-x-1 text-sm text-gray-400">
              <Music className="w-4 h-4" />
              <span>{album.song_count} canciones</span>
            </div>
          )}
        </div>
      </div>
    );
  };

  export default ArtistAlbumsView;