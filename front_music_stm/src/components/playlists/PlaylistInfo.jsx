// src/components/playlists/PlaylistInfo.js
import React, { useState } from 'react';
import { Edit2, Calendar, Music } from 'lucide-react';
import PlaylistForm from './PlaylistForm';

const PlaylistInfo = ({ playlist, onUpdatePlaylist, songsCount }) => {
  const [showEditForm, setShowEditForm] = useState(false);

  const handleUpdate = async (playlistData) => {
    const result = await onUpdatePlaylist(playlist.id, playlistData);
    if (result.success) {
      setShowEditForm(false);
    }
    return result;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-white">{playlist.name}</h2>
          {playlist.description && (
            <p className="mt-2 text-gray-300">{playlist.description}</p>
          )}
        </div>
        <button
          onClick={() => setShowEditForm(true)}
          className="flex items-center gap-2 px-3 py-2 text-sm text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
        >
          <Edit2 size={16} />
          Editar
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 p-4 bg-gray-700 rounded-lg">
        <div className="text-center">
          <div className="flex items-center justify-center gap-2 text-gray-300 mb-1">
            <Music size={16} />
            <span className="text-sm">Canciones</span>
          </div>
          <div className="text-2xl font-bold text-white">{songsCount}</div>
        </div>
        <div className="text-center">
          <div className="flex items-center justify-center gap-2 text-gray-300 mb-1">
            <Calendar size={16} />
            <span className="text-sm">Creada</span>
          </div>
          <div className="text-sm text-white">
            {new Date(playlist.created_at).toLocaleDateString()}
          </div>
        </div>
      </div>

      {/* Información adicional */}
      <div className="space-y-3 text-sm">
        <div className="flex justify-between py-2 border-b border-gray-700">
          <span className="text-gray-400">ID:</span>
          <span className="font-mono text-gray-300">{playlist.id}</span>
        </div>
        <div className="flex justify-between py-2 border-b border-gray-700">
          <span className="text-gray-400">Última actualización:</span>
          <span className="text-gray-300">
            {new Date(playlist.updated_at).toLocaleDateString()}
          </span>
        </div>
      </div>

      {/* Modal de edición */}
      {showEditForm && (
        <PlaylistForm
          onClose={() => setShowEditForm(false)}
          onSubmit={handleUpdate}
          mode="edit"
          initialData={playlist}
        />
      )}
    </div>
  );
};

export default PlaylistInfo;