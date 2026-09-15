// src/pages/ArtistStudio.jsx
import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContexts';
import { artistAPI } from '@/services/artistService';
import ArtistProfile from '@/components/artist/ArtistProfile';
import ArtistAlbums from '@/components/artist/ArtistAlbums';
import { User, Music, BarChart3, Settings } from 'lucide-react';

const ArtistStudio = () => {
  const { authTokens, currentUser } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
  const [artistData, setArtistData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Cargar datos del artista
  useEffect(() => {
    loadArtistData();
  }, []);

  const loadArtistData = async () => {
    try {
      setLoading(true);
      const response = await artistAPI.getMyArtist({ authTokens });
      setArtistData(response.data.artist);
    } catch (err) {
      console.error('Error loading artist data:', err);
      setError('Error al cargar los datos del artista');
    } finally {
      setLoading(false);
    }
  };

  const handleArtistUpdate = (updatedArtist) => {
    setArtistData(updatedArtist);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-700 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <div className="lg:col-span-1 bg-gray-800 rounded-lg p-4 h-32"></div>
            <div className="lg:col-span-3 bg-gray-800 rounded-lg p-6 h-64"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 p-6">
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
          <p className="text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {artistData?.profile_pic ? (
                <img
                  src={artistData.profile_pic}
                  alt={artistData.artist_name}
                  className="w-16 h-16 rounded-full object-cover"
                />
              ) : (
                <div className="w-16 h-16 bg-purple-500 rounded-full flex items-center justify-center">
                  <User className="w-8 h-8 text-white" />
                </div>
              )}
              <div>
                <h1 className="text-2xl font-bold">{artistData?.artist_name}</h1>
                <p className="text-gray-400">Estudio de Artista</p>
              </div>
            </div>
            <div className="text-sm text-gray-400">
              Miembro desde {new Date(artistData?.created_at).toLocaleDateString()}
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {[
              { id: 'profile', label: 'Perfil', icon: User },
              { id: 'albums', label: 'Álbumes', icon: Music },
              { id: 'stats', label: 'Estadísticas', icon: BarChart3 },
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-purple-500 text-purple-400'
                      : 'border-transparent text-gray-400 hover:text-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'profile' && (
          <ArtistProfile 
            artistData={artistData} 
            onArtistUpdate={handleArtistUpdate}
            onReload={loadArtistData}
          />
        )}
        {activeTab === 'albums' && (
          <ArtistAlbums 
            artistId={artistData.id} 
          />
        )}
      </div>
    </div>
  );
};

export default ArtistStudio;