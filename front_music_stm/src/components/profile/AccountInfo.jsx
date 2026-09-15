import { Calendar, Shield, Clock, UserCheck } from 'lucide-react';

const AccountInfo = ({ user }) => {
  const formatDate = (dateString) => {
    if (!dateString) return 'No disponible';
    return new Date(dateString).toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getRoleInfo = (role) => {
    const roles = {
      user: { label: 'Usuario', color: 'text-blue-400' },
      artist: { label: 'Artista', color: 'text-purple-400' },
      admin: { label: 'Administrador', color: 'text-red-400' }
    };
    return roles[role] || roles.user;
  };

  const roleInfo = getRoleInfo(user?.role);

  return (
    <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
      <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
        <UserCheck className="w-5 h-5" />
        Información de Cuenta
      </h3>

      <div className="space-y-4">
        {/* Rol */}
        <div className="flex items-center justify-between">
          <span className="text-gray-400 flex items-center gap-2">
            <Shield className="w-4 h-4" />
            Rol
          </span>
          <span className={`font-medium ${roleInfo.color}`}>
            {roleInfo.label}
          </span>
        </div>

        {/* Fecha de registro */}
        <div className="flex items-center justify-between">
          <span className="text-gray-400 flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            Miembro desde
          </span>
          <span className="text-white text-sm">
            {formatDate(user?.register_date)}
          </span>
        </div>

        {/* Últimos cambios */}
        {(user?.last_username_change || user?.last_email_change) && (
          <div className="pt-4 border-t border-gray-700">
            <h4 className="text-sm font-medium text-gray-300 mb-2">Últimos cambios</h4>
            <div className="space-y-2 text-xs">
              {user.last_username_change && (
                <div className="flex justify-between text-gray-400">
                  <span>Usuario:</span>
                  <span>{formatDate(user.last_username_change)}</span>
                </div>
              )}
              {user.last_email_change && (
                <div className="flex justify-between text-gray-400">
                  <span>Email:</span>
                  <span>{formatDate(user.last_email_change)}</span>
                </div>
              )}
              {user.last_password_change && (
                <div className="flex justify-between text-gray-400">
                  <span>Contraseña:</span>
                  <span>{formatDate(user.last_password_change)}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AccountInfo;