// src/components/artist/CreateAlbumModal.jsx
import { useState, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContexts';
import { musicAPI } from '@/services/musicService';
import { X, Upload, Calendar, Image } from 'lucide-react';

const CreateAlbumModal = ({ isOpen, onClose, onAlbumCreated }) => {
  const { authTokens } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    release_date: '',
    cover_image: null
  });
  const [coverPreview, setCoverPreview] = useState(null);
  const fileInputRef = useRef(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validar tipo de archivo
      if (!file.type.startsWith('image/')) {
        setError('Por favor selecciona un archivo de imagen válido');
        return;
      }

      // Validar tamaño (15MB máximo)
      if (file.size > 15 * 1024 * 1024) {
        setError('La imagen debe ser menor a 15MB');
        return;
      }

      setFormData(prev => ({
        ...prev,
        cover_image: file
      }));

      // Crear preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setCoverPreview(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleRemoveImage = () => {
    setFormData(prev => ({
      ...prev,
      cover_image: null
    }));
    setCoverPreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Crear FormData para enviar archivos
      const submitData = new FormData();
      submitData.append('title', formData.title.trim());
      
      if (formData.release_date) {
        submitData.append('release_date', formData.release_date);
      }
      
      if (formData.cover_image) {
        submitData.append('cover_image', formData.cover_image);
      }

      console.log('🎵 Enviando datos del álbum:', {
        title: formData.title,
        release_date: formData.release_date,
        hasCover: !!formData.cover_image
      });

      const response = await musicAPI.createAlbum(submitData, { authTokens });
      console.log('✅ Álbum creado:', response);

      // Reset form
      setFormData({
        title: '',
        release_date: '',
        cover_image: null
      });
      setCoverPreview(null);

      // Notificar al componente padre
      onAlbumCreated(response.data);

    } catch (err) {
      console.error('❌ Error creando álbum:', err);
      setError(err.message || 'Error al crear el álbum');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-xl p-6 w-full max-w-md">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold">Crear Nuevo Álbum</h3>
          <button
            onClick={handleClose}
            disabled={loading}
            className="text-gray-400 hover:text-white transition-colors disabled:opacity-50"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Preview de portada */}
          {coverPreview && (
            <div className="text-center">
              <div className="relative inline-block">
                <img
                  src={coverPreview}
                  alt="Preview"
                  className="w-32 h-32 object-cover rounded-lg mx-auto"
                />
                <button
                  type="button"
                  onClick={handleRemoveImage}
                  className="absolute -top-2 -right-2 bg-red-500 hover:bg-red-600 rounded-full p-1"
                >
                  <X className="w-4 h-4 text-white" />
                </button>
              </div>
              <p className="text-sm text-gray-400 mt-2">Vista previa</p>
            </div>
          )}

          {/* Título del álbum */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Título del álbum *
            </label>
            <input
              type="text"
              name="title"
              value={formData.title}
              onChange={handleInputChange}
              required
              disabled={loading}
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-colors disabled:opacity-50"
              placeholder="Ej: Mi Primer Álbum, Sencillos, etc."
            />
          </div>

          {/* Fecha de lanzamiento */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2 flex items-center space-x-2">
              <Calendar className="w-4 h-4" />
              <span>Fecha de lanzamiento (opcional)</span>
            </label>
            <input
              type="date"
              name="release_date"
              value={formData.release_date}
              onChange={handleInputChange}
              disabled={loading}
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-colors disabled:opacity-50"
            />
          </div>

          {/* Portada del álbum */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2 flex items-center space-x-2">
              <Image className="w-4 h-4" />
              <span>Portada del álbum (opcional)</span>
            </label>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              disabled={loading}
              className="w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-500 file:text-white hover:file:bg-purple-600 disabled:opacity-50"
            />
            <p className="text-xs text-gray-400 mt-1">
              PNG, JPG, JPEG hasta 15MB
            </p>
          </div>

          {/* Mensaje de error */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
              <div className="flex items-center space-x-2">
                <X className="w-4 h-4 text-red-400 flex-shrink-0" />
                <p className="text-red-400 text-sm">{error}</p>
              </div>
            </div>
          )}

          {/* Información de ayuda */}
          <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-4">
            <h4 className="font-medium text-purple-300 mb-2">Consejos</h4>
            <ul className="text-xs text-purple-300 space-y-1">
              <li>• El título debe ser único para tus álbumes</li>
              <li>• La fecha de lanzamiento ayuda a organizar tu música</li>
              <li>• Una buena portada mejora la presentación</li>
              <li>• Puedes agregar canciones después de crear el álbum</li>
            </ul>
          </div>

          {/* Botones */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              disabled={loading}
              className="flex-1 bg-gray-600 text-white py-3 px-4 rounded-lg hover:bg-gray-700 transition-colors font-medium disabled:opacity-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading || !formData.title.trim()}
              className="flex-1 bg-purple-600 text-white py-3 px-4 rounded-lg hover:bg-purple-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="flex items-center justify-center space-x-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Creando...</span>
                </div>
              ) : (
                'Crear Álbum'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateAlbumModal;