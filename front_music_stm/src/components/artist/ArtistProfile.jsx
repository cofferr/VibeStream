// src/components/artist/ArtistProfile.jsx
import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContexts';
import { artistAPI } from '@/services/artistService';
import ArtistProfileForm from './ArtistProfileForm';
import { Edit3, Trash2, User, Link2, FileText, AlertTriangle } from 'lucide-react';

const ArtistProfile = ({ artistData, onArtistUpdate, onReload }) => {
  const { authTokens, updateUser, updateUserProfile } = useAuth();
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(false);

  const handleUpdate = async (formData) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await artistAPI.updateArtist(formData, { authTokens });
      onArtistUpdate(response.data);
      setEditing(false);
      
      // Recargar datos completos
      onReload();
    } catch (err) {
      console.error('Error updating artist:', err);
      setError(err.message || 'Error al actualizar el perfil');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    try {
      setLoading(true);
      await artistAPI.deleteArtist({ authTokens });
      
      // Actualizar perfil del usuario (volver a ser user)
      await updateUserProfile({ role: 'user' });

      console.log('Perfil de artista eliminado, actualizando contexto del usuario...');

      // Actualizar contexto del usuario (volver a ser user)
      updateUser({ role: 'user' });
      
      // Redirigir a la página principal
      window.location.href = '/dashboard/profile';
    } catch (err) {
      console.error('Error deleting artist:', err);
      setError(err.message || 'Error al eliminar el perfil de artista');
      setDeleteConfirm(false);
    } finally {
      setLoading(false);
    }
  };

  if (editing) {
    return (
      <ArtistProfileForm
        artistData={artistData}
        onSave={handleUpdate}
        onCancel={() => setEditing(false)}
        loading={loading}
      />
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Panel de información */}
      <div className="lg:col-span-2 space-y-6">
        {/* Información básica */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Información del Artista</h2>
            <button
              onClick={() => setEditing(true)}
              className="flex items-center space-x-2 bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg transition-colors"
            >
              <Edit3 className="w-4 h-4" />
              <span>Editar</span>
            </button>
          </div>

          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <User className="w-5 h-5 text-gray-400" />
              <div>
                <p className="text-sm text-gray-400">Nombre artístico</p>
                <p className="font-medium">{artistData?.artist_name}</p>
              </div>
            </div>

            {artistData?.bio && (
              <div className="flex items-start space-x-3">
                <FileText className="w-5 h-5 text-gray-400 mt-0.5" />
                <div>
                  <p className="text-sm text-gray-400">Biografía</p>
                  <p className="font-medium whitespace-pre-line">{artistData.bio}</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Enlaces sociales */}
        {artistData?.social_links && Object.values(artistData.social_links).some(link => link) && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
              <Link2 className="w-5 h-5" />
              <span>Enlaces Sociales</span>
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(artistData.social_links).map(([platform, url]) => 
                url && (
                  <a
                    key={platform}
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center space-x-3 p-3 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors"
                  >
                    <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                      <span className="text-xs font-bold uppercase">
                        {platform.slice(0, 2)}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium capitalize">{platform}</p>
                      <p className="text-sm text-gray-400 truncate">{url}</p>
                    </div>
                  </a>
                )
              )}
            </div>
          </div>
        )}
      </div>

      {/* Panel lateral - Foto de perfil y acciones */}
      <div className="space-y-6">
        {/* Foto de perfil */}
        <div className="bg-gray-800 rounded-lg p-6 text-center">
          <div className="mb-4">
            {artistData?.profile_pic ? (
              <img
                src={artistData.profile_pic}
                alt={artistData.artist_name}
                className="w-32 h-32 rounded-full object-cover mx-auto"
                onError={(e) => {
                  console.error('Error cargando imagen:', {
                    url: e.target.src,
                    profilePic: artistData.profile_pic
                  });
                  e.target.style.display = 'none';
                }}
                onLoad={() => console.log('✅ Imagen cargada correctamente')}
              />
            ) : (
              <div className="w-32 h-32 bg-purple-500 rounded-full flex items-center justify-center mx-auto">
                <User className="w-12 h-12 text-white" />
              </div>
            )}
          </div>
          <p className="text-sm text-gray-400">Foto de perfil</p>
        </div>

        {/* Estadísticas rápidas */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="font-semibold mb-4">Resumen</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Álbumes</span>
              <span className="font-medium">0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Canciones</span>
              <span className="font-medium">0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Seguidores</span>
              <span className="font-medium">0</span>
            </div>
          </div>
        </div>

        {/* Eliminar perfil */}
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-6">
          <h3 className="font-semibold text-red-400 mb-2 flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4" />
            <span>Zona peligrosa</span>
          </h3>
          <p className="text-sm text-red-400 mb-4">
            Eliminar tu perfil de artista eliminará todos tus datos musicales.
          </p>
          
          {!deleteConfirm ? (
            <button
              onClick={() => setDeleteConfirm(true)}
              className="w-full flex items-center justify-center space-x-2 bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              <span>Eliminar Perfil</span>
            </button>
          ) : (
            <div className="space-y-2">
              <p className="text-sm text-red-400 font-medium">
                ¿Estás completamente seguro?
              </p>
              <div className="flex space-x-2">
                <button
                  onClick={handleDelete}
                  disabled={loading}
                  className="flex-1 bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
                >
                  {loading ? 'Eliminando...' : 'Sí, eliminar'}
                </button>
                <button
                  onClick={() => setDeleteConfirm(false)}
                  className="flex-1 bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded-lg transition-colors"
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Mensaje de error */}
      {error && (
        <div className="lg:col-span-3 bg-red-500/10 border border-red-500/20 rounded-lg p-4">
          <p className="text-red-400">{error}</p>
        </div>
      )}
    </div>
  );
};

export default ArtistProfile;