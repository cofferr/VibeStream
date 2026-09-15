// src/components/artist/ArtistAlbums.jsx
import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContexts';
import { musicAPI } from '@/services/musicService';
import { Plus, Music, Calendar, Clock, MoreVertical, Edit, Trash2, ArrowLeft } from 'lucide-react';
import CreateAlbumModal from './CreateAlbumModal';
import AlbumDetail from './AlbumDetail'; // Importamos el componente de detalle

const ArtistAlbums = ({ artistId }) => {
  const { authTokens } = useAuth();
  const [albums, setAlbums] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedAlbum, setSelectedAlbum] = useState(null); // Nuevo estado para álbum seleccionado

  // Cargar álbumes del artista
  useEffect(() => {
    loadAlbums();
  }, [artistId]);

  const loadAlbums = async () => {
    try {
      setLoading(true);
      const response = await musicAPI.getMyAlbums({ 
        authTokens: {
          accessToken: authTokens?.accessToken || authTokens?.access
        }
      });
      
      console.log('📀 Álbumes cargados:', response);
      setAlbums(response.data?.albums || response.albums || []);
      
    } catch (err) {
      console.error('❌ Error completo:', err);
      console.error('🔍 Stack:', err.stack);
      
      if (err.response) {
        console.error('📊 Response status:', err.response.status);
        console.error('📊 Response data:', err.response.data);
      }
      
      setError(err.message || 'Error al cargar los álbumes');
    } finally {
      setLoading(false);
    }
  };

  const handleAlbumCreated = (newAlbum) => {
    setAlbums(prev => [newAlbum, ...prev]);
    setIsCreateModalOpen(false);
  };

  // Función para manejar la selección de un álbum
  const handleAlbumSelect = (album) => {
    setSelectedAlbum(album);
  };

  // Función para volver a la lista de álbumes
  const handleBackToList = () => {
    setSelectedAlbum(null);
    loadAlbums(); // Recargar la lista por si hubo cambios
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'No especificada';
    return new Date(dateString).toLocaleDateString('es-ES');
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '0:00';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  // Si hay un álbum seleccionado, mostrar el detalle
  if (selectedAlbum) {
    return (
      <div className="space-y-6">
        {/* Botón para volver */}
        <div className="flex items-center space-x-4">
          <button
            onClick={handleBackToList}
            className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Volver a mis álbumes</span>
          </button>
        </div>

        {/* Detalle del álbum */}
        <AlbumDetail 
          album={selectedAlbum}
          onAlbumUpdated={handleBackToList}
        />
      </div>
    );
  }

  // Vista normal de la lista de álbumes
  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-8 bg-gray-700 rounded w-1/4 mb-6"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="bg-gray-800 rounded-lg p-4 h-64">
              <div className="w-full h-40 bg-gray-700 rounded mb-4"></div>
              <div className="h-4 bg-gray-700 rounded mb-2"></div>
              <div className="h-3 bg-gray-700 rounded w-2/3"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header con estadísticas y botón crear */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Mis Álbumes</h2>
          <p className="text-gray-400">
            {albums.length} {albums.length === 1 ? 'álbum' : 'álbumes'} en tu catálogo
          </p>
        </div>
        
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="flex items-center space-x-2 bg-purple-600 hover:bg-purple-700 px-4 py-3 rounded-lg transition-colors font-medium"
        >
          <Plus className="w-5 h-5" />
          <span>Nuevo Álbum</span>
        </button>
      </div>

      {/* Mensaje de error */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Lista de álbumes */}
      {albums.length === 0 ? (
        <div className="text-center py-12 bg-gray-800 rounded-lg">
          <Music className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-400 mb-2">No hay álbumes</h3>
          <p className="text-gray-500 mb-6">Comienza creando tu primer álbum para organizar tu música.</p>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="bg-purple-600 hover:bg-purple-700 px-6 py-3 rounded-lg transition-colors font-medium"
          >
            Crear Primer Álbum
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {albums.map((album) => (
            <AlbumCard 
              key={album.id} 
              album={album} 
              onAlbumUpdated={loadAlbums}
              onAlbumSelect={handleAlbumSelect}
              formatDate={formatDate}
              formatDuration={formatDuration}
            />
          ))}
        </div>
      )}

      {/* Modal para crear álbum */}
      <CreateAlbumModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onAlbumCreated={handleAlbumCreated}
      />
    </div>
  );
};

// Componente individual para cada álbum - MODIFICADO
const AlbumCard = ({ album, onAlbumUpdated, onAlbumSelect, formatDate, formatDuration }) => {
  const [showMenu, setShowMenu] = useState(false);
  const { authTokens } = useAuth();

  const handleViewAlbum = () => {
    onAlbumSelect(album);
  };

  const handleEditAlbum = () => {
    // Abrir modal de edición
    console.log('Editar álbum:', album.id);
    setShowMenu(false);
  };

  const handleDeleteAlbum = async () => {
    if (!window.confirm(`¿Estás seguro de eliminar el álbum "${album.title}"? Esta acción no se puede deshacer.`)) {
      return;
    }

    try {
      await musicAPI.deleteAlbum(album.id, { authTokens });
      console.log('Álbum eliminado:', album.id);
      onAlbumUpdated();
    } catch (error) {
      console.error('Error eliminando álbum:', error);
      alert('Error al eliminar el álbum');
    }
    setShowMenu(false);
  };

  return (
    <div className="bg-gray-800 rounded-lg p-4 hover:bg-gray-750 transition-colors group">
      {/* Portada del álbum */}
      <div className="relative mb-4">
        {album.cover_url ? (
          <img
            src={album.cover_url}
            alt={album.title}
            className="w-full aspect-square object-cover rounded-lg"
            onError={(e) => {
              console.log('❌ Error cargando imagen:', album.cover_url);
              console.log('🔍 URL intentada:', album.cover_url);
              e.target.style.display = 'none';
            }}
            onLoad={() => console.log('✅ Imagen cargada correctamente')}
          />
        ) : (
          <div className="w-full aspect-square bg-gradient-to-br from-purple-600 to-blue-600 rounded-lg flex items-center justify-center">
            <Music className="w-12 h-12 text-white" />
          </div>
        )}
        
        {/* Overlay con acciones */}
        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-40 transition-opacity rounded-lg flex items-center justify-center opacity-0 group-hover:opacity-100">
          <button
            onClick={handleViewAlbum}
            className="bg-white text-black px-4 py-2 rounded-full font-medium hover:bg-gray-100 transition-colors"
          >
            Ver Álbum
          </button>
        </div>

        {/* Menú de opciones */}
        <div className="absolute top-2 right-2">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-1 bg-black bg-opacity-50 rounded-full text-white hover:bg-opacity-70 transition-colors"
          >
            <MoreVertical className="w-4 h-4" />
          </button>

          {showMenu && (
            <div className="absolute right-0 top-8 bg-gray-700 rounded-lg py-1 shadow-lg z-10 min-w-32">
              <button
                onClick={handleEditAlbum}
                className="flex items-center space-x-2 w-full px-3 py-2 text-sm hover:bg-gray-600 transition-colors"
              >
                <Edit className="w-4 h-4" />
                <span>Editar</span>
              </button>
              <button
                onClick={handleDeleteAlbum}
                className="flex items-center space-x-2 w-full px-3 py-2 text-sm hover:bg-red-500 hover:bg-opacity-20 text-red-400 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
                <span>Eliminar</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Información del álbum */}
      <div className="space-y-2">
        <h3 className="font-semibold text-lg truncate" title={album.title}>
          {album.title}
        </h3>
        
        <div className="flex items-center space-x-4 text-sm text-gray-400">
          <div className="flex items-center space-x-1">
            <Calendar className="w-4 h-4" />
            <span>{formatDate(album.release_date)}</span>
          </div>
          
          <div className="flex items-center space-x-1">
            <Music className="w-4 h-4" />
            <span>{album.song_count || 0} canciones</span>
          </div>
        </div>

        {album.total_duration && (
          <div className="flex items-center space-x-1 text-sm text-gray-400">
            <Clock className="w-4 h-4" />
            <span>{formatDuration(album.total_duration)}</span>
          </div>
        )}

        {/* Estadísticas rápidas */}
        <div className="flex justify-between text-xs text-gray-500 pt-2 border-t border-gray-700">
          <span>Reproducciones: {album.play_count || 0}</span>
          <span>Likes: {album.like_count || 0}</span>
        </div>
      </div>
    </div>
  );
};

export default ArtistAlbums;