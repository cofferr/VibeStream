// src/pages/PlaylistsPage.js
import React, { useState, useEffect} from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContexts';
import { playlistServices } from '@/services/playlistService';
import PlaylistList from '@/components/playlists/PlaylistList';
import PlaylistForm from '@/components/playlists/PlaylistForm';
import PlaylistDetail from '@/components/playlists/PlaylistDetail';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorMessage from '@/components/ui/ErrorMessage';
import { Plus, Search } from 'lucide-react';

const PlaylistsPage = () => {
  const { authTokens } = useAuth();
  const navigate = useNavigate();
  const [playlists, setPlaylists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedPlaylist, setSelectedPlaylist] = useState(null);
  const [pagination, setPagination] = useState({
    current_page: 1,
    page_size: 20,
    total_items: 0,
    total_pages: 0
  });

  // Cargar playlists del usuario
  const loadPlaylists = async (page = 1) => {
    try {
      setLoading(true);
      setError(null);
      const response = await playlistServices.getUserPlaylists(
        authTokens, 
        page, 
        pagination.page_size
      );
      
      setPlaylists(response.playlists || []);
      setPagination(response.pagination || pagination);
    } catch (err) {
      setError(err.message);
      console.error('Error loading playlists:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPlaylists();
  }, []);

  // Crear nueva playlist
  const handleCreatePlaylist = async (playlistData) => {
    try {
      const newPlaylist = await playlistServices.createPlaylist(
        playlistData.name,
        playlistData.description,
        authTokens
      );
      
      setPlaylists(prev => [newPlaylist, ...prev]);
      setShowCreateForm(false);
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  // Actualizar playlist
  const handleUpdatePlaylist = async (playlistId, playlistData) => {
    try {
      const updatedPlaylist = await playlistServices.updatePlaylist(
        playlistId,
        playlistData.name,
        playlistData.description,
        authTokens
      );
      
      setPlaylists(prev => 
        prev.map(playlist => 
          playlist.id === playlistId ? updatedPlaylist : playlist
        )
      );
      
      if (selectedPlaylist && selectedPlaylist.id === playlistId) {
        setSelectedPlaylist(updatedPlaylist);
      }
      
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  // Eliminar playlist
  const handleDeletePlaylist = async (playlistId) => {
    try {
      await playlistServices.deletePlaylist(playlistId, authTokens);
      setPlaylists(prev => prev.filter(playlist => playlist.id !== playlistId));
      
      if (selectedPlaylist && selectedPlaylist.id === playlistId) {
        setSelectedPlaylist(null);
      }
      
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  if (loading && playlists.length === 0) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <LoadingSpinner size="large" text="Cargando playlists..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-white">Mis Playlists</h1>
              <p className="mt-2 text-sm text-gray-400">
                Gestiona tus listas de reproducción personalizadas
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => navigate('/dashboard/search')}
                className="flex items-center gap-2 bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
              >
                <Search size={20} />
                Buscar Canciones
              </button>
              <button
                onClick={() => setShowCreateForm(true)}
                className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors"
              >
                <Plus size={20} />
                Nueva Playlist
              </button>
            </div>
          </div>
        </div>

        {error && (
          <ErrorMessage 
            message={error}
            onRetry={() => loadPlaylists()}
          />
        )}

        {/* Contenido Principal */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Lista de Playlists */}
          <div className="lg:col-span-1">
            <PlaylistList
              playlists={playlists}
              onSelectPlaylist={setSelectedPlaylist}
              selectedPlaylist={selectedPlaylist}
              onDeletePlaylist={handleDeletePlaylist}
              loading={loading}
              pagination={pagination}
              onPageChange={loadPlaylists}
            />
          </div>

          {/* Detalle de Playlist o Vista Vacía */}
          <div className="lg:col-span-2">
            {selectedPlaylist ? (
              <PlaylistDetail
                playlist={selectedPlaylist}
                onUpdatePlaylist={handleUpdatePlaylist}
                authTokens={authTokens}
              />
            ) : (
              <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 text-center">
                <div className="max-w-md mx-auto">
                  <div className="w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Plus size={24} className="text-gray-400" />
                  </div>
                  <h3 className="text-lg font-medium text-white mb-2">
                    Selecciona una playlist
                  </h3>
                  <p className="text-sm text-gray-400 mb-6">
                    Elige una playlist de la lista para ver sus detalles y gestionar sus canciones
                  </p>
                  <button
                    onClick={() => setShowCreateForm(true)}
                    className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors"
                  >
                    Crear tu primera playlist
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Modal de Crear Playlist */}
        {showCreateForm && (
          <PlaylistForm
            onClose={() => setShowCreateForm(false)}
            onSubmit={handleCreatePlaylist}
            mode="create"
          />
        )}
      </div>
    </div>
  );
};

export default PlaylistsPage;