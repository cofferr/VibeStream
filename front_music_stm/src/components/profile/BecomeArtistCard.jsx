// src/components/profile/BecomeArtistCard.jsx
import { useState, useEffect } from 'react';
import { Music, Star, CheckCircle, AlertCircle, Mic } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContexts';
import { artistAPI } from '@/services/artistService';
import ConfirmArtistModal from './ConfirmArtistModal';
import { useNavigate } from 'react-router-dom';

const BecomeArtistCard = () => {
  const { currentUser, updateUser, updateUserProfile, authTokens } = useAuth(); // ✅ Obtén authTokens aquí
  const navigate = useNavigate();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [artistStatus, setArtistStatus] = useState({
    isArtist: false,
    checking: true
  });

  // Verificar si el usuario ya es artista
  useEffect(() => {
    const checkArtistStatus = async () => {
      try {

        console.log('🔍 Iniciando verificación de artista...');
        console.log('🔍 authTokens disponibles:', authTokens?.accessToken ? 'SÍ' : 'NO');
        // ✅ Usa authTokens directamente desde el hook principal
        if (authTokens?.accessToken) {
          const result = await artistAPI.checkIfArtist({ authTokens });
          console.log('🔍 Resultado COMPLETO de checkIfArtist:', result);
          console.log('🔍 isArtist value:', result.isArtist);
          console.log('🔍 Tipo de isArtist:', typeof result.isArtist);
          setArtistStatus({
            isArtist: result.isArtist,
            checking: false
          });
        } else {
          setArtistStatus({
            isArtist: false,
            checking: false
          });
        }
      } catch (err) {
        console.error('Error checking artist status:', err);
        setArtistStatus({
          isArtist: false,
          checking: false
        });
      }
    };

    checkArtistStatus();
  }, [currentUser, authTokens]); // ✅ Agrega authTokens como dependencia

  const handleArtistRequest = () => {
    setError(null);
    setIsModalOpen(true);
  };

  const handleConfirm = async (formData) => {
  setLoading(true);
  setError(null);

  try {
    console.log('🔍 FormData recibido del modal:');
    
    // Debug: mostrar contenido del FormData
    for (let [key, value] of formData.entries()) {
      console.log(`🔍 ${key}:`, value);
    }

    // ✅ 1. Registrar artista en el artist-service
    const response = await artistAPI.registerArtist(formData, { authTokens });
    
    console.log('✅ Artista registrado exitosamente:', response);

    // ✅ 2. Actualizar el rol del usuario en el auth-service
    try {
      console.log('🔄 Actualizando rol del usuario a "artist"...');
      await updateUserProfile({ role: 'artist' });
      console.log('✅ Rol actualizado correctamente en el backend');
    } catch (updateError) {
      console.error('❌ Error actualizando rol:', updateError);
      // Aún así actualizamos el contexto local para mejor UX
      updateUser({ role: 'artist' });
      throw new Error('Artista registrado, pero hubo un error actualizando el rol. Recarga la página.');
    }

    // ✅ 3. Actualizar contexto local (por si acaso)
    updateUser({ 
      role: 'artist',
      ...response.data 
    });

    setIsModalOpen(false);
    
  } catch (err) {
    console.error('❌ Error registrando artista:', err);
    setError(err.message || 'Error al registrarse como artista');
  } finally {
    setLoading(false);
  }
};

  const handleGoToStudio = () => {
    navigate('/dashboard/artist/studio');
  };

  // Si está verificando, mostrar skeleton
  if (artistStatus.checking) {
    return (
      <div className="bg-gray-800 rounded-xl p-6 shadow-lg animate-pulse">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-gray-700 rounded-full"></div>
          <div className="space-y-2">
            <div className="h-4 bg-gray-700 rounded w-24"></div>
            <div className="h-3 bg-gray-700 rounded w-16"></div>
          </div>
        </div>
        <div className="space-y-2">
          <div className="h-3 bg-gray-700 rounded"></div>
          <div className="h-3 bg-gray-700 rounded w-5/6"></div>
        </div>
      </div>
    );
  }

  // Si ya es artista
  if (artistStatus.isArtist || currentUser?.role === 'artist') {
    return (
      <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/20 rounded-xl p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-purple-500 rounded-full flex items-center justify-center">
            <CheckCircle className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">¡Eres Artista!</h3>
            <p className="text-purple-300 text-sm">Cuenta verificada</p>
          </div>
        </div>
        
        <p className="text-gray-300 text-sm mb-4">
          Tienes acceso completo a las herramientas de artista para gestionar tu música.
        </p>
        
        <button 
          onClick={handleGoToStudio}
          className="w-full bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 transition-colors font-medium"
        >
          Ir a Mi Estudio
        </button>
      </div>
    );
  }

  // Si no es artista, mostrar opción para convertirse
  return (
    <>
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-gradient-to-br from-yellow-500 to-orange-500 rounded-full flex items-center justify-center">
            <Star className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Conviértete en Artista</h3>
            <p className="text-gray-400 text-sm">Comparte tu música</p>
          </div>
        </div>
        
        <ul className="space-y-3 mb-6">
          <li className="flex items-center gap-2 text-sm text-gray-300">
            <Music className="w-4 h-4 text-green-400" />
            Sube tus canciones y álbumes
          </li>
          <li className="flex items-center gap-2 text-sm text-gray-300">
            <Mic className="w-4 h-4 text-green-400" />
            Gestiona tu catálogo musical
          </li>
          <li className="flex items-center gap-2 text-sm text-gray-300">
            <Music className="w-4 h-4 text-green-400" />
            Llega a una audiencia global
          </li>
        </ul>

        {/* Mostrar error si existe */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 mb-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
              <p className="text-red-400 text-xs">{error}</p>
            </div>
          </div>
        )}

        <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-3 mb-4">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
            <p className="text-yellow-300 text-xs">
              Esta acción creará un perfil de artista vinculado a tu cuenta. Podrás subir música y gestionar tus lanzamientos.
            </p>
          </div>
        </div>

        <button 
          onClick={handleArtistRequest}
          disabled={loading}
          className="w-full bg-gradient-to-r from-yellow-500 to-orange-500 text-white py-3 px-4 rounded-lg hover:from-yellow-600 hover:to-orange-600 transition-all font-medium shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Procesando...' : 'Solicitar Ser Artista'}
        </button>
      </div>

      <ConfirmArtistModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onConfirm={handleConfirm}
        loading={loading}
        currentUser={currentUser}
      />
    </>
  );
};

export default BecomeArtistCard;