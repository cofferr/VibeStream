// src/components/artist/ArtistProfileForm.jsx
import { useState } from 'react';
import { User, FileText, Link2, Image, X, Save } from 'lucide-react';

const ArtistProfileForm = ({ artistData, onSave, onCancel, loading }) => {
  const [formData, setFormData] = useState({
    artist_name: artistData?.artist_name || '',
    bio: artistData?.bio || '',
    social_links: {
      website: artistData?.social_links?.website || '',
      youtube: artistData?.social_links?.youtube || '',
      instagram: artistData?.social_links?.instagram || '',
      spotify: artistData?.social_links?.spotify || '',
      tiktok: artistData?.social_links?.tiktok || '',
      twitter: artistData?.social_links?.twitter || '',
    },
    profile_pic_file: null
  });

  const [profilePreview, setProfilePreview] = useState(artistData?.profile_pic || null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSocialLinkChange = (platform, value) => {
    setFormData(prev => ({
      ...prev,
      social_links: {
        ...prev.social_links,
        [platform]: value
      }
    }));
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setFormData(prev => ({
        ...prev,
        profile_pic_file: file
      }));

      // Crear preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setProfilePreview(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleRemoveImage = () => {
    setFormData(prev => ({
      ...prev,
      profile_pic_file: null
    }));
    setProfilePreview(null);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Crear FormData para enviar archivos
    const submitData = new FormData();
    submitData.append('artist_name', formData.artist_name);
    submitData.append('bio', formData.bio);
    
    // Filtrar enlaces sociales que no estén vacíos
    const nonEmptyLinks = Object.fromEntries(
      Object.entries(formData.social_links).filter(([_, value]) => value.trim() !== '')
    );
    submitData.append('social_links', JSON.stringify(nonEmptyLinks));
    
    if (formData.profile_pic_file) {
      submitData.append('profile_pic_file', formData.profile_pic_file);
    }

    onSave(submitData);
  };

  const socialPlatforms = [
    { key: 'website', label: 'Sitio Web', placeholder: 'https://tusitio.com' },
    { key: 'youtube', label: 'YouTube', placeholder: 'https://youtube.com/tucanal' },
    { key: 'instagram', label: 'Instagram', placeholder: 'https://instagram.com/tuusuario' },
    { key: 'spotify', label: 'Spotify', placeholder: 'https://open.spotify.com/artist/tuid' },
    { key: 'tiktok', label: 'TikTok', placeholder: 'https://tiktok.com/@tucusuario' },
    { key: 'twitter', label: 'Twitter', placeholder: 'https://twitter.com/tucusuario' },
  ];

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">Editar Perfil de Artista</h2>
          <div className="flex space-x-3">
            <button
              type="button"
              onClick={onCancel}
              disabled={loading}
              className="flex items-center space-x-2 bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
            >
              <X className="w-4 h-4" />
              <span>Cancelar</span>
            </button>
            <button
              type="submit"
              disabled={loading || !formData.artist_name.trim()}
              className="flex items-center space-x-2 bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              <span>{loading ? 'Guardando...' : 'Guardar Cambios'}</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Columna izquierda - Información básica */}
          <div className="lg:col-span-2 space-y-6">
            {/* Nombre artístico */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2 flex items-center space-x-2">
                <User className="w-4 h-4" />
                <span>Nombre artístico *</span>
              </label>
              <input
                type="text"
                name="artist_name"
                value={formData.artist_name}
                onChange={handleInputChange}
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Tu nombre como artista"
                required
              />
            </div>

            {/* Biografía */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2 flex items-center space-x-2">
                <FileText className="w-4 h-4" />
                <span>Biografía</span>
              </label>
              <textarea
                name="bio"
                value={formData.bio}
                onChange={handleInputChange}
                rows="5"
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Cuéntale a tus fans sobre tu música, inspiración, etc..."
              />
              <p className="text-sm text-gray-400 mt-1">
                {formData.bio.length}/500 caracteres
              </p>
            </div>

            {/* Enlaces sociales */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-4 flex items-center space-x-2">
                <Link2 className="w-4 h-4" />
                <span>Enlaces Sociales</span>
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {socialPlatforms.map((platform) => (
                  <div key={platform.key}>
                    <label className="block text-xs text-gray-400 mb-1">
                      {platform.label}
                    </label>
                    <input
                      type="url"
                      value={formData.social_links[platform.key]}
                      onChange={(e) => handleSocialLinkChange(platform.key, e.target.value)}
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-purple-500 focus:border-transparent text-sm"
                      placeholder={platform.placeholder}
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Columna derecha - Imagen de perfil */}
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-4 flex items-center space-x-2">
                <Image className="w-4 h-4" />
                <span>Foto de perfil</span>
              </label>
              
              <div className="text-center">
                {/* Preview de imagen */}
                <div className="mb-4">
                  {profilePreview ? (
                    <div className="relative inline-block">
                      <img
                        src={profilePreview}
                        alt="Preview"
                        className="w-32 h-32 rounded-full object-cover mx-auto"
                      />
                      <button
                        type="button"
                        onClick={handleRemoveImage}
                        className="absolute -top-2 -right-2 bg-red-500 hover:bg-red-600 rounded-full p-1"
                      >
                        <X className="w-4 h-4 text-white" />
                      </button>
                    </div>
                  ) : (
                    <div className="w-32 h-32 bg-gray-700 rounded-full flex items-center justify-center mx-auto">
                      <User className="w-8 h-8 text-gray-400" />
                    </div>
                  )}
                </div>

                {/* Input de archivo */}
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  className="w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-500 file:text-white hover:file:bg-purple-600"
                />
                <p className="text-xs text-gray-400 mt-2">
                  PNG, JPG, JPEG hasta 5MB
                </p>
              </div>
            </div>

            {/* Información de ayuda */}
            <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-4">
              <h4 className="font-medium text-purple-300 mb-2">Consejos</h4>
              <ul className="text-xs text-purple-300 space-y-1">
                <li>• Usa tu nombre artístico real</li>
                <li>• Añade una biografía interesante</li>
                <li>• Incluye tus redes sociales</li>
                <li>• Usa una foto de perfil de calidad</li>
              </ul>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
};

export default ArtistProfileForm;