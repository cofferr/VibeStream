import { useState } from 'react';
import { Save, X, Lock, Eye, EyeOff } from 'lucide-react';

const SecuritySection = ({ onUpdatePassword }) => {
  const [passwordData, setPasswordData] = useState({
    newPassword: '',
    confirmPassword: ''
  });
  const [showPasswords, setShowPasswords] = useState({
    new: false,
    confirm: false
  });
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleChange = (field, value) => {
    setPasswordData(prev => ({ ...prev, [field]: value }));
  };

  const togglePasswordVisibility = (field) => {
    setShowPasswords(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };

  const hasData = passwordData.newPassword || passwordData.confirmPassword;
  const passwordsMatch = passwordData.newPassword === passwordData.confirmPassword;
  const isValid = hasData && passwordsMatch && passwordData.newPassword.length >= 6;

  const handleSave = async (e) => {
    e.preventDefault();
    
    if (!isValid) return;

    setSaving(true);
    try {
      await onUpdatePassword({
        password: passwordData.newPassword
      });

      // Limpiar formulario
      setPasswordData({
        newPassword: '',
        confirmPassword: ''
      });
      setShowPasswords({
        new: false,
        confirm: false
      });
      setIsEditing(false);
    } catch (error) {
      console.error('Error updating password:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setPasswordData({
      newPassword: '',
      confirmPassword: ''
    });
    setShowPasswords({
      new: false,
      confirm: false
    });
    setIsEditing(false);
  };

  const handleEdit = () => {
    setIsEditing(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Seguridad</h2>
        {!isEditing && (
          <button
            onClick={handleEdit}
            className="flex items-center gap-2 px-4 py-2 text-purple-400 hover:text-purple-300 hover:bg-purple-500/10 rounded-lg transition-colors"
          >
            <Lock className="w-4 h-4" />
            Cambiar Contraseña
          </button>
        )}
      </div>

      {!isEditing ? (
        <div className="text-gray-400">
          <p>Puedes cambiar tu contraseña aquí para mantener tu cuenta segura.</p>
        </div>
      ) : (
        <form onSubmit={handleSave} className="space-y-6">
          <div className="grid grid-cols-1 gap-6">
            {/* Nueva contraseña */}
            <div>
              <label htmlFor="newPassword" className="block text-sm font-medium text-gray-300 mb-2">
                Nueva contraseña
              </label>
              <div className="relative">
                <input
                  type={showPasswords.new ? 'text' : 'password'}
                  id="newPassword"
                  value={passwordData.newPassword}
                  onChange={(e) => handleChange('newPassword', e.target.value)}
                  disabled={saving}
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-colors pr-12 disabled:opacity-50 disabled:cursor-not-allowed"
                  placeholder="Mínimo 6 caracteres"
                />
                <button
                  type="button"
                  onClick={() => togglePasswordVisibility('new')}
                  disabled={saving}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors disabled:opacity-50"
                >
                  {showPasswords.new ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {passwordData.newPassword && passwordData.newPassword.length < 6 && (
                <p className="text-red-400 text-xs mt-1">La contraseña debe tener al menos 6 caracteres</p>
              )}
            </div>

            {/* Confirmar contraseña */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-300 mb-2">
                Confirmar contraseña
              </label>
              <div className="relative">
                <input
                  type={showPasswords.confirm ? 'text' : 'password'}
                  id="confirmPassword"
                  value={passwordData.confirmPassword}
                  onChange={(e) => handleChange('confirmPassword', e.target.value)}
                  disabled={saving}
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-colors pr-12 disabled:opacity-50 disabled:cursor-not-allowed"
                  placeholder="Repite la contraseña"
                />
                <button
                  type="button"
                  onClick={() => togglePasswordVisibility('confirm')}
                  disabled={saving}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors disabled:opacity-50"
                >
                  {showPasswords.confirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {passwordData.confirmPassword && !passwordsMatch && (
                <p className="text-red-400 text-xs mt-1">Las contraseñas no coinciden</p>
              )}
            </div>
          </div>

          {/* Botones de acción */}
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
              disabled={saving || !isValid}
              className="flex items-center gap-2 px-6 py-3 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Save className="w-4 h-4" />
              {saving ? 'Actualizando...' : 'Cambiar Contraseña'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

export default SecuritySection;