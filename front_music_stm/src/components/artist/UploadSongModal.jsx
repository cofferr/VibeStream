// src/components/artist/UploadSongModal.jsx
import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContexts';
import { musicAPI } from '@/services/musicService';
import { X, Upload, Music } from 'lucide-react';

const UploadSongModal = ({ isOpen, onClose, onSongUploaded, albumId }) => {
  const { authTokens } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    track_number: '',
    genre_id: '',
    artist_ids: ''
  });

  const [audioFile, setAudioFile] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    setAudioFile(file);
    // Si no se ha ingresado un título, usar el nombre del archivo sin extensión
    if (!formData.title && file) {
      const fileName = file.name.replace(/\.[^/.]+$/, "");
      setFormData(prev => ({ ...prev, title: fileName }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!audioFile) {
      setError('Por favor, selecciona un archivo de audio');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const submitFormData = new FormData();
      submitFormData.append('title', formData.title);
      submitFormData.append('album_id', albumId);
      submitFormData.append('audio_file', audioFile);
      
      if (formData.track_number) submitFormData.append('track_number', formData.track_number);
      if (formData.genre_id) submitFormData.append('genre_id', formData.genre_id);
      if (formData.artist_ids) submitFormData.append('artist_ids', formData.artist_ids);

      const response = await musicAPI.createSong(submitFormData, { 
        authTokens: {
          accessToken: authTokens?.accessToken || authTokens?.access
        }
      });
      
      console.log('✅ Canción subida:', response);
      onSongUploaded(response.data || response);
      onClose();
      
      // Reset form
      setFormData({ title: '', track_number: '', genre_id: '', artist_ids: '' });
      setAudioFile(null);
    } catch (err) {
      console.error('Error uploading song:', err);
      setError(err.message || 'Error al subir la canción');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">Subir Canción</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-700 rounded transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 mb-4">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Archivo de audio */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Archivo de Audio *
            </label>
            <div className="border-2 border-dashed border-gray-600 rounded-lg p-4 text-center hover:border-purple-500 transition-colors">
              <input
                type="file"
                accept="audio/*"
                onChange={handleFileChange}
                className="hidden"
                id="audio-file"
                required
              />
              <label htmlFor="audio-file" className="cursor-pointer">
                {audioFile ? (
                  <div className="text-green-400">
                    <Music className="w-8 h-8 mx-auto mb-2" />
                    <p className="font-medium">{audioFile.name}</p>
                    <p className="text-sm text-gray-400">
                      {(audioFile.size / (1024 * 1024)).toFixed(2)} MB
                    </p>
                  </div>
                ) : (
                  <div className="text-gray-400">
                    <Upload className="w-8 h-8 mx-auto mb-2" />
                    <p className="font-medium">Seleccionar archivo de audio</p>
                    <p className="text-sm">MP3, WAV, FLAC, etc.</p>
                  </div>
                )}
              </label>
            </div>
          </div>

          {/* Título */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Título *
            </label>
            <input
              type="text"
              name="title"
              value={formData.title}
              onChange={handleInputChange}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:border-purple-500 focus:outline-none"
              required
              placeholder="Nombre de la canción"
            />
          </div>

          {/* Número de pista */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Número de pista
            </label>
            <input
              type="number"
              name="track_number"
              value={formData.track_number}
              onChange={handleInputChange}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:border-purple-500 focus:outline-none"
              min="1"
              placeholder="1"
            />
          </div>

          {/* Género ID */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              ID de Género
            </label>
            <input
              type="number"
              name="genre_id"
              value={formData.genre_id}
              onChange={handleInputChange}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:border-purple-500 focus:outline-none"
              placeholder="1 (opcional)"
            />
          </div>

          {/* IDs de Artistas */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              IDs de Artistas (separados por comas)
            </label>
            <input
              type="text"
              name="artist_ids"
              value={formData.artist_ids}
              onChange={handleInputChange}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:border-purple-500 focus:outline-none"
              placeholder="1, 2, 3 (opcional)"
            />
            <p className="text-xs text-gray-400 mt-1">
              Si se deja vacío, se usará tu artista principal
            </p>
          </div>

          <button
            type="submit"
            disabled={loading || !audioFile}
            className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed px-4 py-3 rounded-lg transition-colors font-medium flex items-center justify-center space-x-2"
          >
            <Upload className="w-5 h-5" />
            <span>{loading ? 'Subiendo...' : 'Subir Canción'}</span>
          </button>
        </form>
      </div>
    </div>
  );
};

export default UploadSongModal;