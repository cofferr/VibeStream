import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContexts';
import ProfileHeader from '@/components/profile/ProfileHeader';
import ProfileTabs from '@/components/profile/ProfileTabs';
import PersonalInfoSection from '@/components/profile/PersonalInfoSection';
import SecuritySection from '@/components/profile/SecuritySection';
import AccountInfo from '../components/profile/AccountInfo';
import { Loader, AlertCircle } from 'lucide-react';
import BecomeArtistCard from '@/components/profile/BecomeArtistCard';

const ProfilePage = () => {
  const { 
    currentUser, 
    updateUserProfile, 
    updatePassword,
    loadUserProfile 
  } = useAuth();
  
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [activeTab, setActiveTab] = useState('personal');
  const [initialLoad, setInitialLoad] = useState(true);

  // Cargar detalles del perfil solo una vez al montar
  useEffect(() => {
    const loadProfileData = async () => {
      if (currentUser && initialLoad) {
        try {
          await loadUserProfile();
        } catch (err) {
          console.error('Error loading profile:', err);
        } finally {
          setInitialLoad(false);
        }
      }
    };

    loadProfileData();
  }, [currentUser, initialLoad, loadUserProfile]);

  const clearMessages = useCallback(() => {
    setError(null);
    setSuccess(null);
  }, []);

  const handleUpdateProfile = useCallback(async (formData) => {
    try {
      clearMessages();
      await updateUserProfile(formData);
      setSuccess('Perfil actualizado correctamente');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message || 'Error al actualizar el perfil');
      throw err;
    }
  }, [updateUserProfile, clearMessages]);

  const handleUpdatePassword = useCallback(async (passwordData) => {
    try {
      clearMessages();
      await updatePassword(passwordData);
      setSuccess('Contraseña actualizada correctamente');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message || 'Error al actualizar la contraseña');
      throw err;
    }
  }, [updatePassword, clearMessages]);

  if (!currentUser) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader className="w-8 h-8 animate-spin text-purple-500 mx-auto mb-4" />
          <p className="text-gray-400">Cargando perfil...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Alertas globales */}
        {error && (
          <div className="mb-6 p-4 rounded-lg bg-red-500/10 border border-red-500/20">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-red-400" />
              <p className="text-red-400">{error}</p>
            </div>
          </div>
        )}

        {success && (
          <div className="mb-6 p-4 rounded-lg bg-green-500/10 border border-green-500/20">
            <div className="flex items-center gap-2">
              <p className="text-green-400">{success}</p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Columna izquierda - Información unificada */}
          <div className="lg:col-span-1 space-y-6">
            <ProfileHeader user={currentUser} />
            <AccountInfo user={currentUser} />
            <BecomeArtistCard />
          </div>

          {/* Columna derecha - Contenido editable */}
          <div className="lg:col-span-2">
            <div className="bg-gray-800 rounded-xl shadow-lg overflow-hidden">
              <ProfileTabs 
                activeTab={activeTab} 
                onTabChange={setActiveTab} 
              />
              
              <div className="p-6">
                {activeTab === 'personal' && (
                  <PersonalInfoSection 
                    user={currentUser}
                    onUpdate={handleUpdateProfile}
                  />
                )}
                
                {activeTab === 'security' && (
                  <SecuritySection 
                    onUpdatePassword={handleUpdatePassword}
                  />
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;