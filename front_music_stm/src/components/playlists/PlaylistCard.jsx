// src/components/playlists/PlaylistCard.js
import React, { useState } from 'react';
import { MoreVertical, Trash2, Music } from 'lucide-react';

const PlaylistCard = ({
  playlist,
  isSelected,
  onSelect,
  onDelete,
  isDeleting
}) => {
  const [showMenu, setShowMenu] = useState(false);

  const handleClick = (e) => {
    // Evitar que el click del menú active la selección
    if (!e.target.closest('.menu-container')) {
      onSelect();
    }
  };

  return (
    <div
      className={`p-4 cursor-pointer transition-colors ${
        isSelected 
          ? 'bg-purple-600 border-r-4 border-r-purple-400' 
          : 'hover:bg-gray-700'
      } ${isDeleting ? 'opacity-50' : ''}`}
      onClick={handleClick}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-purple-600 rounded flex items-center justify-center">
              <Music size={20} className="text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-medium text-white truncate">
                {playlist.name}
              </h3>
              {playlist.description && (
                <p className="text-sm text-gray-300 truncate mt-1">
                  {playlist.description}
                </p>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-4 text-xs text-gray-400">
            <span>
              Creada: {new Date(playlist.created_at).toLocaleDateString()}
            </span>
            {playlist.updated_at !== playlist.created_at && (
              <span>
                Actualizada: {new Date(playlist.updated_at).toLocaleDateString()}
              </span>
            )}
          </div>
        </div>

        {/* Menú de opciones */}
        <div className="menu-container relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-1 hover:bg-gray-600 rounded transition-colors text-gray-400 hover:text-white"
          >
            <MoreVertical size={16} />
          </button>
          
          {showMenu && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setShowMenu(false)}
              />
              <div className="absolute right-0 top-6 bg-gray-700 border border-gray-600 rounded-lg shadow-lg z-20 min-w-32">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete();
                    setShowMenu(false);
                  }}
                  disabled={isDeleting}
                  className="flex items-center gap-2 w-full px-4 py-2 text-sm text-red-400 hover:bg-gray-600 disabled:opacity-50"
                >
                  <Trash2 size={16} />
                  {isDeleting ? 'Eliminando...' : 'Eliminar'}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default PlaylistCard;