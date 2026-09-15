// src/components/playlists/PlaylistList.js
import React, { useState } from 'react';
import PlaylistCard from './PlaylistCard';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { Search } from 'lucide-react';

const PlaylistList = ({
  playlists,
  onSelectPlaylist,
  selectedPlaylist,
  onDeletePlaylist,
  loading,
  pagination,
  onPageChange
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [deletingId, setDeletingId] = useState(null);

  // Filtrar playlists por búsqueda
  const filteredPlaylists = playlists.filter(playlist =>
    playlist.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (playlist.description && playlist.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const handleDelete = async (playlistId) => {
    setDeletingId(playlistId);
    const result = await onDeletePlaylist(playlistId);
    setDeletingId(null);
    
    if (!result.success) {
      alert(`Error al eliminar: ${result.error}`);
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700">
      {/* Header con búsqueda */}
      <div className="p-4 border-b border-gray-700">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            placeholder="Buscar playlists..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-white placeholder-gray-400"
          />
        </div>
      </div>

      {/* Lista de Playlists */}
      <div className="max-h-96 lg:max-h-[calc(100vh-300px)] overflow-y-auto">
        {loading && playlists.length === 0 ? (
          <div className="flex justify-center p-8">
            <LoadingSpinner />
          </div>
        ) : filteredPlaylists.length === 0 ? (
          <div className="text-center p-8 text-gray-400">
            {searchTerm ? 'No se encontraron playlists' : 'No tienes playlists aún'}
          </div>
        ) : (
          <div className="divide-y divide-gray-700">
            {filteredPlaylists.map((playlist) => (
              <PlaylistCard
                key={playlist.id}
                playlist={playlist}
                isSelected={selectedPlaylist?.id === playlist.id}
                onSelect={() => onSelectPlaylist(playlist)}
                onDelete={() => handleDelete(playlist.id)}
                isDeleting={deletingId === playlist.id}
              />
            ))}
          </div>
        )}
      </div>

      {/* Paginación */}
      {pagination.total_pages > 1 && (
        <div className="p-4 border-t border-gray-700">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-400">
              Mostrando {filteredPlaylists.length} de {pagination.total_items}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => onPageChange(pagination.current_page - 1)}
                disabled={pagination.current_page === 1}
                className="px-3 py-1 text-sm bg-gray-700 border border-gray-600 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600"
              >
                Anterior
              </button>
              <button
                onClick={() => onPageChange(pagination.current_page + 1)}
                disabled={pagination.current_page === pagination.total_pages}
                className="px-3 py-1 text-sm bg-gray-700 border border-gray-600 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600"
              >
                Siguiente
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PlaylistList;