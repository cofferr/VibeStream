import { NavLink, useNavigate, useLocation } from "react-router-dom";
import {
  Home,
  Search,
  Library,
  ListMusic,
  Settings,
  Music,
  User,
  PlusCircle,
  Menu,
  X,
  LogOut, 
  Mic
} from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/contexts/AuthContexts";

const LeftNav = ({ isOpen, onToggle }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { logout, currentUser } = useAuth();
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  const navItems = [
    { to: "/dashboard/home", icon: Home, label: "Inicio" },
    { to: "/dashboard/search", icon: Search, label: "Buscar" },
    { to: "/dashboard/library", icon: Library, label: "Biblioteca" },
    { to: "/dashboard/playlists", icon: ListMusic, label: "Playlists" },
  ];

  if (currentUser?.role === 'artist') {
    navItems.splice(1, 0, { 
      to: "/dashboard/artist/studio", 
      icon: Mic, 
      label: "Mi estudio" 
    });
  }

  const secondaryItems = [
    { to: "/dashboard/profile", icon: User, label: "Perfil" },
    { to: "/dashboard/settings", icon: Settings, label: "Configuración" },
  ];

  // Verificar si una ruta está activa (incluye subrutas)
  const isActiveRoute = (path) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate("/login");
    } catch (error) {
      console.error("Logout error:", error);
      // Fallback: limpiar localStorage y redirigir
      localStorage.removeItem('authTokens');
      localStorage.removeItem('userData');
      navigate("/login");
    }
  };

  // Nueva función para manejar el clic en cerrar sesión
  const handleLogoutClick = () => {
    // Si el nav está cerrado, lo abrimos primero
    if (!isOpen) {
      onToggle();
      // Esperamos a que la animación del nav termine antes de mostrar el modal
      setTimeout(() => {
        setShowLogoutConfirm(true);
      }, 300);
    } else {
      // Si ya está abierto, mostramos el modal directamente
      setShowLogoutConfirm(true);
    }
  };

  const LogoutConfirmModal = () => (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 max-w-sm mx-4 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-2">
          ¿Cerrar sesión?
        </h3>
        <p className="text-gray-300 text-sm mb-6">
          ¿Estás seguro de que quieres salir de tu cuenta?
        </p>
        <div className="flex gap-3 justify-end">
          <button
            onClick={() => setShowLogoutConfirm(false)}
            className="px-4 py-2 text-gray-300 hover:text-white transition-colors text-sm"
          >
            Cancelar
          </button>
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors text-sm font-medium"
          >
            Sí, cerrar sesión
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <>
      <nav className="h-full bg-gray-900 border-r border-gray-800 flex flex-col relative z-40">
        {/* Header con logo y toggle */}
        <div className="p-4 border-b border-gray-800 flex-shrink-0">
          <div className="flex items-center justify-between">
            {isOpen && (
              <div className="flex items-center gap-2 min-w-0">
                <Music className="w-8 h-8 text-purple-500 flex-shrink-0" />
                <span className="font-bold text-xl text-white truncate">VibeStream</span>
              </div>
            )}
            {!isOpen && (
              <div className="flex justify-center w-full">
                <Music className="w-8 h-8 text-purple-500 flex-shrink-0" />
              </div>
            )}
            <button
              onClick={onToggle}
              className="p-2 rounded-lg hover:bg-gray-800 transition-colors flex-shrink-0 ml-2"
            >
              {isOpen ? (
                <X className="w-5 h-5 text-gray-400" />
              ) : (
                <Menu className="w-5 h-5 text-gray-400" />
              )}
            </button>
          </div>
        </div>

        {/* Navigation principal */}
        <div className="flex-1 p-4 overflow-y-auto">
          <div className="space-y-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-3 rounded-lg transition-all duration-200 group ${
                    isActive || isActiveRoute(item.to)
                      ? "bg-gradient-to-r from-purple-600 to-purple-700 text-white shadow-lg shadow-purple-500/25"
                      : "text-gray-300 hover:bg-gray-800 hover:text-white"
                  }`
                }
              >
                <item.icon className={`w-5 h-5 flex-shrink-0 ${
                  isActiveRoute(item.to) ? "text-white" : "text-gray-400 group-hover:text-white"
                }`} />
                {isOpen && <span className="font-medium truncate">{item.label}</span>}
                
                {/* Tooltip cuando está colapsado */}
                {!isOpen && (
                  <div className="absolute left-full ml-2 px-2 py-1 bg-gray-900 text-white text-sm rounded-md opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-50 border border-gray-700">
                    {item.label}
                  </div>
                )}
              </NavLink>
            ))}
          </div>
        </div>

        {/* Footer con perfil, configuración y logout */}
        <div className="p-4 border-t border-gray-800 space-y-1 flex-shrink-0 bg-gray-900">
          {secondaryItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-3 rounded-lg transition-all duration-200 group ${
                  isActive || isActiveRoute(item.to)
                    ? "bg-gradient-to-r from-purple-600 to-purple-700 text-white shadow-lg shadow-purple-500/25"
                    : "text-gray-300 hover:bg-gray-800 hover:text-white"
                }`
              }
            >
              <item.icon className={`w-5 h-5 flex-shrink-0 ${
                isActiveRoute(item.to) ? "text-white" : "text-gray-400 group-hover:text-white"
              }`} />
              {isOpen && <span className="font-medium truncate">{item.label}</span>}
              
              {/* Tooltip cuando está colapsado */}
              {!isOpen && (
                <div className="absolute left-full ml-2 px-2 py-1 bg-gray-900 text-white text-sm rounded-md opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-50 border border-gray-700">
                  {item.label}
                </div>
              )}
            </NavLink>
          ))}

          {/* Información del usuario */}
          {isOpen && currentUser && (
            <div className="px-3 py-3 text-xs text-gray-400 border-t border-gray-700 mt-4 pt-4">
              <div className="truncate font-medium text-gray-300">{currentUser.username}</div>
              <div className="truncate text-gray-500">{currentUser.email}</div>
            </div>
          )}

          {/* Avatar del usuario cuando está colapsado */}
          {!isOpen && currentUser && (
            <div className="flex justify-center py-3 border-t border-gray-700 mt-4">
              <div 
                className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-600 to-pink-500 flex items-center justify-center text-white text-xs font-bold cursor-default group relative"
                title={`${currentUser.username}\n${currentUser.email}`}
              >
                {currentUser.username.charAt(0).toUpperCase()}
                <div className="absolute left-full ml-2 px-2 py-1 bg-gray-900 text-white text-sm rounded-md opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-50 border border-gray-700 text-left">
                  <div className="font-medium">{currentUser.username}</div>
                  <div className="text-gray-400 text-xs">{currentUser.email}</div>
                </div>
              </div>
            </div>
          )}

          {/* Logout - SIEMPRE VISIBLE - Ahora usa handleLogoutClick */}
          <button
            onClick={handleLogoutClick}
            className="flex items-center gap-3 px-3 py-3 text-red-400 hover:text-red-300 hover:bg-red-900/20 rounded-lg transition-all duration-200 w-full group mt-2"
            title={!isOpen ? "Cerrar Sesión" : ""}
          >
            <LogOut className="w-5 h-5 flex-shrink-0" />
            {isOpen && <span className="font-medium">Cerrar Sesión</span>}
            
            {/* Tooltip cuando está colapsado */}
            {!isOpen && (
              <div className="absolute left-full ml-2 px-2 py-1 bg-gray-900 text-white text-sm rounded-md opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-50 border border-gray-700">
                Cerrar Sesión
              </div>
            )}
          </button>
        </div>
      </nav>

      {/* Modal de confirmación de logout */}
      {showLogoutConfirm && <LogoutConfirmModal />}
    </>
  );
};

export default LeftNav; 