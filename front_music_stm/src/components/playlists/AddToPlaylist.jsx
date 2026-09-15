// src/components/playlists/AddToPlaylist.jsx
import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContexts';
import { playlistServices } from '@/services/playlistService';
import { Plus, Loader2, ListMusic } from 'lucide-react';

const AddToPlaylist = ({ song, onSuccess, onError }) => {
  const { authTokens } = useAuth();
  const [playlists, setPlaylists] = useState([]);
  const [loading, setLoading] = useState(false);
  const [adding, setAdding] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  const dropdownRef = useRef(null);
  const buttonRef = useRef(null);

  // Cargar playlists del usuario cuando se abre el dropdown
  useEffect(() => {
    if (isOpen && playlists.length === 0) {
      loadPlaylists();
    }
  }, [isOpen]);

  // Cerrar dropdown al hacer clic fuera
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target) && 
          buttonRef.current && !buttonRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [isOpen]);

  // Ajustar posición del dropdown si se sale de la pantalla
  useEffect(() => {
    if (isOpen && dropdownRef.current) {
      const dropdown = dropdownRef.current;
      const rect = dropdown.getBoundingClientRect();
      
      // Si el dropdown se sale por la parte inferior de la pantalla
      if (rect.bottom > window.innerHeight) {
        dropdown.style.bottom = '100%';
        dropdown.style.top = 'auto';
      } else {
        dropdown.style.bottom = 'auto';
        dropdown.style.top = '100%';
      }

      // Si se sale por la derecha
      if (rect.right > window.innerWidth) {
        dropdown.style.right = '0';
        dropdown.style.left = 'auto';
      }
    }
  }, [isOpen]);

  const loadPlaylists = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await playlistServices.getUserPlaylists(authTokens, 1, 20); // Reducido a 20
      setPlaylists(response.playlists || []);
    } catch (err) {
      setError('Error al cargar las playlists');
      console.error('Error loading playlists:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToPlaylist = async (playlistId) => {
    try {
      setAdding(true);
      setError(null);
      
      await playlistServices.addSongToPlaylist(playlistId, song.id, authTokens);
      
      setSuccess('Canción añadida a la playlist');
      if (onSuccess) onSuccess();
      
      // Cerrar el dropdown después de un tiempo
      setTimeout(() => {
        setIsOpen(false);
        setSuccess(null);
      }, 1500);
      
    } catch (err) {
      const errorMsg = err.message || 'Error al añadir la canción';
      setError(errorMsg);
      if (onError) onError(errorMsg);
    } finally {
      setAdding(false);
    }
  };

  const handleCreateNewPlaylist = () => {
    // TODO: Podríamos integrar el modal de creación de playlist aquí
    console.log("Abrir modal de creación de playlist");
    // Por ahora, simplemente cerramos y mostramos un mensaje
    setError('Función de crear playlist próximamente');
    setIsOpen(false);
  };

  const toggleDropdown = () => {
    setIsOpen(!isOpen);
    setError(null);
    setSuccess(null);
  };

  return (
    <div className="relative">
      <button
        ref={buttonRef}
        onClick={toggleDropdown}
        disabled={adding}
        className="p-1 rounded-full hover:bg-gray-600 transition-colors disabled:opacity-50"
        title="Añadir a playlist"
      >
        {adding ? (
          <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />
        ) : (
          <Plus className="w-4 h-4 text-gray-400" />
        )}
      </button>

      {isOpen && (
        <div
          ref={dropdownRef}
          className="absolute right-0 top-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-50 min-w-64 max-h-80 flex flex-col"
          style={{
            // Posicionamiento dinámico
            zIndex: 9999
          }}
        >
          {/* Header */}
          <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-700 sticky top-0 bg-gray-800 z-10">
            <ListMusic className="w-4 h-4 text-purple-400 flex-shrink-0" />
            <span className="text-sm font-medium text-white truncate">
              Añadir a playlist
            </span>
          </div>

          {/* Estados */}
          <div className="flex-1 overflow-hidden flex flex-col min-h-0">
            {loading && (
              <div className="flex justify-center p-4 flex-shrink-0">
                <Loader2 className="w-5 h-5 text-purple-400 animate-spin" />
              </div>
            )}

            {error && (
              <div className="p-2 mx-2 mt-2 bg-red-900 border border-red-700 rounded text-red-200 text-xs flex-shrink-0">
                {error}
              </div>
            )}

            {success && (
              <div className="p-2 mx-2 mt-2 bg-green-900 border border-green-700 rounded text-green-200 text-xs flex-shrink-0">
                {success}
              </div>
            )}

            {/* Lista de playlists con scroll */}
            <div className="flex-1 overflow-y-auto max-h-48">
              {!loading && playlists.length === 0 ? (
                <div className="text-center p-4 text-gray-400 text-sm">
                  No tienes playlists
                </div>
              ) : (
                <div className="p-1">
                  {playlists.map(playlist => (
                    <button
                      key={playlist.id}
                      onClick={() => handleAddToPlaylist(playlist.id)}
                      disabled={adding}
                      className="flex items-center justify-between w-full px-2 py-2 text-sm text-gray-300 hover:bg-gray-700 rounded transition-colors disabled:opacity-50"
                    >
                      <div className="flex items-center gap-2 min-w-0 flex-1">
                        <div className="w-6 h-6 bg-gradient-to-br from-purple-500 to-purple-600 rounded flex items-center justify-center flex-shrink-0">
                          <ListMusic className="w-3 h-3 text-white" />
                        </div>
                        <div className="text-left min-w-0 flex-1">
                          <div className="font-medium text-white truncate text-xs">
                            {playlist.name}
                          </div>
                          {playlist.description && (
                            <div className="text-xs text-gray-400 truncate">
                              {playlist.description}
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {adding && (
                        <Loader2 className="w-3 h-3 text-purple-400 animate-spin flex-shrink-0 ml-2" />
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Botón para crear nueva playlist */}
            {!loading && (
              <div className="p-2 border-t border-gray-700 flex-shrink-0">
                <button
                  onClick={handleCreateNewPlaylist}
                  className="flex items-center gap-2 w-full px-2 py-2 text-xs text-purple-400 hover:bg-gray-700 rounded transition-colors border border-gray-600 justify-center"
                >
                  <Plus className="w-3 h-3" />
                  <span>Crear nueva playlist</span>
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AddToPlaylist;