import { useState, useEffect } from "react";
import { Outlet, useLocation } from "react-router-dom";
import LeftNav from "./LeftNav";
import Player from "../player/Player";
import { PlayerProvider } from "@/contexts/PlayerContext";
import { Menu } from "lucide-react";

const AppShell = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const location = useLocation();

  // Cerrar sidebar en móvil al cambiar de ruta
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setSidebarOpen(false);
      }
    };

    window.addEventListener('resize', handleResize);
    handleResize(); // Ejecutar al montar

    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Cerrar sidebar en móvil al navegar
  useEffect(() => {
    if (window.innerWidth < 768) {
      setSidebarOpen(false);
    }
  }, [location.pathname]);

  return (
    <PlayerProvider>
      <div className="h-screen flex bg-gray-900 text-white overflow-hidden">
        {/* Overlay para móvil cuando sidebar está abierto */}
        {sidebarOpen && (
          <div 
            className="fixed inset-0 bg-black/50 z-30 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
        
        {/* Sidebar FIXED */}
        <div 
          className={`
            transition-all duration-300 flex-shrink-0 h-full fixed left-0 top-0 z-40
            ${sidebarOpen ? 'w-64 translate-x-0' : 'w-16 -translate-x-full md:translate-x-0'}
          `}
        >
          <LeftNav 
            isOpen={sidebarOpen} 
            onToggle={() => setSidebarOpen(!sidebarOpen)} 
          />
        </div>
        
        {/* Contenido principal con PADDING BOTTOM para el Player */}
        <div 
          className={`
            flex-1 flex flex-col min-h-full transition-all duration-300
            ${sidebarOpen ? 'md:ml-64' : 'md:ml-16'}
          `}
        >
          {/* Área de contenido con scroll y PADDING BOTTOM */}
          <main className="flex-1 overflow-y-auto pb-24 md:pb-20">
            <div className="min-h-full p-4 md:p-6">
              <Outlet />
            </div>
          </main>
        </div>
        
        {/* Player FIXED */}
        <div 
          className={`
            fixed bottom-0 transition-all duration-300 z-30 bg-gray-900 border-t border-gray-800
            ${sidebarOpen ? 'md:left-64' : 'md:left-16'} left-0 right-0
          `}
        >
          <Player />
        </div>

        {/* Botón flotante para abrir sidebar en móvil */}
        {!sidebarOpen && (
          <button
            onClick={() => setSidebarOpen(true)}
            className="fixed bottom-20 left-4 z-40 md:hidden w-12 h-12 bg-purple-600 hover:bg-purple-700 text-white rounded-full flex items-center justify-center shadow-lg transition-all duration-200"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}
      </div>
    </PlayerProvider>
  );
};

export default AppShell;