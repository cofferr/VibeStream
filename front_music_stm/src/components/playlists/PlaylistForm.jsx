// src/components/playlists/PlaylistForm.js
import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';

const PlaylistForm = ({ onClose, onSubmit, mode = 'create', initialData = null }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: ''
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (initialData) {
      setFormData({
        name: initialData.name || '',
        description: initialData.description || ''
      });
    }
  }, [initialData]);

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'El nombre es obligatorio';
    } else if (formData.name.length > 100) {
      newErrors.name = 'El nombre no puede tener más de 100 caracteres';
    }
    
    if (formData.description && formData.description.length > 500) {
      newErrors.description = 'La descripción no puede tener más de 500 caracteres';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setLoading(true);
    const result = await onSubmit(formData);
    setLoading(false);
    
    if (result.success) {
      onClose();
    } else {
      setErrors({ submit: result.error });
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Limpiar error del campo cuando el usuario empiece a escribir
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-gray-800 rounded-lg max-w-md w-full border border-gray-700">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <h2 className="text-xl font-semibold text-white">
            {mode === 'create' ? 'Crear Nueva Playlist' : 'Editar Playlist'}
          </h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-700 rounded transition-colors text-gray-400 hover:text-white"
          >
            <X size={20} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6">
          {errors.submit && (
            <div className="mb-4 p-3 bg-red-900 border border-red-700 rounded-lg text-red-200 text-sm">
              {errors.submit}
            </div>
          )}

          <div className="space-y-4">
            {/* Nombre */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-300 mb-1">
                Nombre de la playlist *
              </label>
              <input
                type="text"
                id="name"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                className={`w-full px-3 py-2 bg-gray-700 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-white placeholder-gray-400 ${
                  errors.name ? 'border-red-500' : 'border-gray-600'
                }`}
                placeholder="Mi playlist favorita"
                maxLength={100}
              />
              {errors.name && (
                <p className="mt-1 text-sm text-red-400">{errors.name}</p>
              )}
              <div className="mt-1 text-xs text-gray-400 text-right">
                {formData.name.length}/100
              </div>
            </div>

            {/* Descripción */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-300 mb-1">
                Descripción
              </label>
              <textarea
                id="description"
                value={formData.description}
                onChange={(e) => handleChange('description', e.target.value)}
                rows={3}
                className={`w-full px-3 py-2 bg-gray-700 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-white placeholder-gray-400 ${
                  errors.description ? 'border-red-500' : 'border-gray-600'
                }`}
                placeholder="Describe tu playlist..."
                maxLength={500}
              />
              {errors.description && (
                <p className="mt-1 text-sm text-red-400">{errors.description}</p>
              )}
              <div className="mt-1 text-xs text-gray-400 text-right">
                {formData.description.length}/500
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-700 border border-gray-600 text-white rounded-lg hover:bg-gray-600 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Guardando...' : (mode === 'create' ? 'Crear Playlist' : 'Actualizar')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PlaylistForm;