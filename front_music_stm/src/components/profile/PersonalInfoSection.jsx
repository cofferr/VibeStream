import { useState, useEffect } from 'react';
import { Save, X, Edit3, User, Mail, Calendar } from 'lucide-react';

const PersonalInfoSection = ({ user, onUpdate }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    username: '',
    email: '',
    birthdate: ''
  });
  const [originalData, setOriginalData] = useState({});
  const [saving, setSaving] = useState(false);

  // Inicializar datos cuando el usuario cambia y no estamos editando
  useEffect(() => {
    if (user && !isEditing) {
      const userData = {
        name: user.name || '',
        username: user.username || '',
        email: user.email || '',
        birthdate: user.birthdate ? user.birthdate.split('T')[0] : ''
      };
      
      setFormData(userData);
      setOriginalData(userData);
    }
  }, [user, isEditing]); // Agregar isEditing como dependencia

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const hasChanges = () => {
    return Object.keys(formData).some(key => formData[key] !== originalData[key]);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    
    if (!hasChanges()) {
      setIsEditing(false);
      return;
    }

    setSaving(true);
    // Solo enviar campos que han cambiado
    const changedData = {};
    Object.keys(formData).forEach(key => {
      if (formData[key] !== originalData[key]) {
        changedData[key] = formData[key];
      }
    });

    try {
      await onUpdate(changedData);
      setOriginalData(formData);
      setIsEditing(false);
    } catch (error) {
      // El error se maneja en el componente padre (ProfilePage)
      console.error('Error saving profile:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setFormData(originalData);
    setIsEditing(false);
  };

  const handleEdit = () => {
    setIsEditing(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Información Personal</h2>
        {!isEditing && (
          <button
            onClick={handleEdit}
            className="flex items-center gap-2 px-4 py-2 text-purple-400 hover:text-purple-300 hover:bg-purple-500/10 rounded-lg transition-colors"
          >
            <Edit3 className="w-4 h-4" />
            Editar
          </button>
        )}
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Nombre */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-300 mb-2">
              <User className="w-4 h-4 inline mr-2" />
              Nombre completo
            </label>
            <input
              type="text"
              id="name"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              disabled={!isEditing || saving}
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              placeholder="Tu nombre completo"
            />
          </div>

          {/* Username */}
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-300 mb-2">
              <User className="w-4 h-4 inline mr-2" />
              Nombre de usuario
            </label>
            <input
              type="text"
              id="username"
              value={formData.username}
              onChange={(e) => handleChange('username', e.target.value)}
              disabled={!isEditing || saving}
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              placeholder="Tu nombre de usuario"
            />
          </div>

          {/* Email */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
              <Mail className="w-4 h-4 inline mr-2" />
              Correo electrónico
            </label>
            <input
              type="email"
              id="email"
              value={formData.email}
              onChange={(e) => handleChange('email', e.target.value)}
              disabled={!isEditing || saving}
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              placeholder="tu@email.com"
            />
          </div>

          {/* Fecha de nacimiento */}
          <div>
            <label htmlFor="birthdate" className="block text-sm font-medium text-gray-300 mb-2">
              <Calendar className="w-4 h-4 inline mr-2" />
              Fecha de nacimiento
            </label>
            <input
              type="date"
              id="birthdate"
              value={formData.birthdate}
              onChange={(e) => handleChange('birthdate', e.target.value)}
              disabled={!isEditing || saving}
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>
        </div>

        {/* Botones de acción */}
        {isEditing && (
          <div className="flex justify-end gap-4 pt-6 border-t border-gray-700">
            <button
              type="button"
              onClick={handleCancel}
              disabled={saving}
              className="flex items-center gap-2 px-6 py-3 bg-gray-600 text-white font-medium rounded-lg hover:bg-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <X className="w-4 h-4" />
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving || !hasChanges()}
              className="flex items-center gap-2 px-6 py-3 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Save className="w-4 h-4" />
              {saving ? 'Guardando...' : 'Guardar Cambios'}
            </button>
          </div>
        )}
      </form>
    </div>
  );
};

export default PersonalInfoSection;