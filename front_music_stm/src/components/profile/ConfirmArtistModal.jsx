// src/components/profile/ConfirmArtistModal.jsx
import { useState } from 'react';
import { X, AlertCircle, CheckCircle, User, Loader } from 'lucide-react';

const ConfirmArtistModal = ({ isOpen, onClose, onConfirm, loading, currentUser }) => {
  const [artistName, setArtistName] = useState(currentUser?.username || '');

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (artistName.trim()) {
      // ✅ SOLO CAMBIO AQUÍ - Usar FormData en lugar de objeto JSON
      const formData = new FormData();
      formData.append('artist_name', artistName.trim());
      
      onConfirm(formData);
    }
  };

  const handleClose = () => {
    if (!loading) {
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-xl p-6 w-full max-w-md">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold text-white">Convertirse en Artista</h3>
          <button
            onClick={handleClose}
            disabled={loading}
            className="text-gray-400 hover:text-white transition-colors disabled:opacity-50"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Nombre de Artista */}
          <div>
            <label htmlFor="artistName" className="block text-sm font-medium text-gray-300 mb-2">
              <User className="w-4 h-4 inline mr-2" />
              Nombre artístico
            </label>
            <input
              type="text"
              id="artistName"
              value={artistName}
              onChange={(e) => setArtistName(e.target.value)}
              disabled={loading}
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-colors disabled:opacity-50"
              placeholder="Tu nombre como artista"
              required
              minLength={2}
              maxLength={50}
            />
            <p className="text-gray-400 text-xs mt-1">
              Este será tu nombre público como artista. Puedes cambiarlo después.
            </p>
          </div>

          {/* Advertencia */}
          <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-yellow-400 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="text-yellow-300 font-medium text-sm mb-1">¿Estás seguro?</h4>
                <p className="text-yellow-300 text-xs">
                  Esta acción creará un perfil de artista vinculado a tu cuenta. 
                  Podrás subir música, gestionar álbumes y llegar a una audiencia global.
                </p>
              </div>
            </div>
          </div>

          {/* Beneficios */}
          <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-4">
            <h4 className="text-purple-300 font-medium text-sm mb-2">Ahora podrás:</h4>
            <ul className="text-purple-300 text-xs space-y-1">
              <li className="flex items-center gap-2">
                <CheckCircle className="w-3 h-3" />
                Subir tus canciones y álbumes
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-3 h-3" />
                Gestionar tu catálogo musical
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-3 h-3" />
                Llegar a una audiencia global
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-3 h-3" />
                Acceder a herramientas de artista
              </li>
            </ul>
          </div>

          {/* Botones */}
          <div className="flex justify-end gap-4 pt-4 border-t border-gray-700">
            <button
              type="button"
              onClick={handleClose}
              disabled={loading}
              className="px-6 py-3 bg-gray-600 text-white font-medium rounded-lg hover:bg-gray-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading || !artistName.trim()}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-yellow-500 to-orange-500 text-white font-medium rounded-lg hover:from-yellow-600 hover:to-orange-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader className="w-4 h-4 animate-spin" />
                  Registrando...
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4" />
                  Confirmar
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ConfirmArtistModal;