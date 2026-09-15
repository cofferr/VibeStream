  import { useState, useEffect } from "react";
  import { Play, Heart, MoreHorizontal, TrendingUp, Music, Clock, Users } from "lucide-react";
  import TrackCard from "@/components/music/TrackCard";
  import PlaylistCard from "@/components/music/PlaylistCard";
  import { useAuth } from "@/contexts/AuthContexts";
  import { usePlayer } from "@/contexts/PlayerContext";
  import { musicAPI } from "@/services/musicService";

  const Dashboard = () => {
    const authContext = useAuth();
    const { currentUser, authTokens } = authContext;
    const { playTrack, currentTrack, isPlaying } = usePlayer();
    const [likedTracks, setLikedTracks] = useState(new Set());
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [dashboardData, setDashboardData] = useState({
      recentAlbums: [],
      popularSongs: [],
      trendingArtists: []
    });

    // Cargar datos para el dashboard de usuario
    useEffect(() => {
      const loadDashboardData = async () => {
        try {
          setLoading(true);
          setError(null);
          
          if (!authContext.authTokens?.accessToken) {
            throw new Error('No authentication token available');
          }

          // Intentar cargar datos públicos/recientes
          try {
            // Últimos álbumes publicados
            const recentAlbumsResponse = await musicAPI.getRecentAlbums(authContext);
            const recentAlbums = recentAlbumsResponse.data?.albums || recentAlbumsResponse.albums || [];
            
            // Canciones populares
            const popularSongsResponse = await musicAPI.getPopularSongs(authContext);
            const popularSongs = popularSongsResponse.data?.songs || popularSongsResponse.songs || [];

            setDashboardData({
              recentAlbums: recentAlbums,
              popularSongs: popularSongs,
              trendingArtists: []
            });

          } catch (apiError) {
            console.warn('Endpoints de dashboard no disponibles, usando datos de ejemplo');
            setDashboardData(getFallbackData());
          }

        } catch (err) {
          console.error('Error loading dashboard data:', err);
          setError('No se pudieron cargar los datos. Los endpoints pueden no estar disponibles aún.');
          setDashboardData(getFallbackData());
        } finally {
          setLoading(false);
        }
      };

      if (currentUser && authTokens) {
        loadDashboardData();
      }
    }, [currentUser, authTokens, authContext]);

    // Datos de ejemplo para cuando no hay conexión
    const getFallbackData = () => {
      return {
        recentAlbums: [
          {
            id: 1,
            title: "Summer Vibes 2024",
            artist_name: "DJ Stream",
            cover_url: "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400&h=400&fit=crop",
            release_date: "2024-01-15",
            song_count: 12
          },
          {
            id: 2,
            title: "Indie Collection",
            artist_name: "The Unknowns",
            cover_url: "https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=400&h=400&fit=crop",
            release_date: "2024-01-10",
            song_count: 8
          },
          {
            id: 3,
            title: "Urban Beats",
            artist_name: "City Sound",
            cover_url: "https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=400&h=400&fit=crop",
            release_date: "2024-01-05",
            song_count: 10
          }
        ],
        popularSongs: [
          {
            id: 1,
            title: "Electric Dreams",
            artist_name: "DJ Stream",
            album_title: "Summer Vibes 2024",
            cover_url: "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400&h=400&fit=crop",
            duration: 180,
            plays: 15000
          },
          {
            id: 2,
            title: "Midnight City",
            artist_name: "The Unknowns",
            album_title: "Indie Collection",
            cover_url: "https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=400&h=400&fit=crop",
            duration: 210,
            plays: 12000
          },
          {
            id: 3,
            title: "Neon Lights",
            artist_name: "City Sound",
            album_title: "Urban Beats",
            cover_url: "https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=400&h=400&fit=crop",
            duration: 195,
            plays: 9800
          }
        ],
        trendingArtists: []
      };
    };

    const handleLikeTrack = (trackId) => {
      const newLiked = new Set(likedTracks);
      if (newLiked.has(trackId)) {
        newLiked.delete(trackId);
      } else {
        newLiked.add(trackId);
      }
      setLikedTracks(newLiked);
    };

    const handlePlayTrack = (track) => {
      playTrack({
        id: track.id,
        title: track.title,
        artist: track.artist_name || track.artist,
        album: track.album_title || track.album,
        cover: track.cover_url || track.cover,
        duration: track.duration,
        audioUrl: track.audio_url || `/api/songs/${track.id}/stream`
      });
    };

    const handlePlayAlbum = async (album) => {
      try {
        const songsResponse = await musicAPI.getAlbumSongs(album.id, authContext);
        const songs = songsResponse.data?.songs || songsResponse.songs || [];
        
        if (songs.length > 0) {
          const firstSong = songs[0];
          handlePlayTrack(firstSong);
        } else {
          alert('Este álbum no tiene canciones disponibles');
        }
      } catch (err) {
        console.error('Error loading album songs:', err);
        alert('No se pudieron cargar las canciones del álbum');
      }
    };

    const handleRetry = () => {
      window.location.reload();
    };

    if (loading) {
      return (
        <div className="p-6 flex items-center justify-center min-h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="p-6 flex flex-col items-center justify-center min-h-96">
          <div className="text-yellow-400 text-lg mb-4 text-center">
            {error}
          </div>
          <p className="text-gray-400 mb-4 text-center">
            El backend aún no tiene todos los endpoints implementados.
          </p>
          <button 
            onClick={handleRetry}
            className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            Reintentar
          </button>
        </div>
      );
    }

    return (
      <div className="p-6 space-y-8 fade-in">
        {/* Header de Bienvenida */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">
              ¡Bienvenido, {currentUser?.username || 'Usuario'}!
            </h1>
            <p className="text-gray-400 mt-1">
              Descubre nueva música y artistas increíbles
            </p>
          </div>
          <button className="px-6 py-3 bg-purple-600 text-white rounded-full hover:bg-purple-700 transition-colors">
            Explorar Música
          </button>
        </div>

        {/* Sección de Álbumes Recientes */}
        <Section 
          title="Álbumes Recientes" 
          actionText="Ver todos"
          icon={<Music className="w-5 h-5" />}
        >
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
            {dashboardData.recentAlbums.map((album) => (
              <PlaylistCard
                key={album.id}
                playlist={{
                  id: album.id,
                  name: album.title,
                  owner: album.artist_name,
                  cover: album.cover_url,
                  trackCount: album.song_count || 0,
                  isPublic: true
                }}
                onPlay={() => handlePlayAlbum(album)}
              />
            ))}
          </div>
        </Section>

        {/* Sección de Canciones Populares */}
        <Section 
          title="Canciones Populares" 
          actionText="Ver todas"
          icon={<TrendingUp className="w-5 h-5" />}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {dashboardData.popularSongs.map((song, index) => (
              <TrackCard
                key={song.id}
                track={{
                  id: song.id,
                  title: song.title,
                  artist: song.artist_name,
                  album: song.album_title,
                  cover: song.cover_url,
                  duration: song.duration,
                  plays: song.plays
                }}
                isLiked={likedTracks.has(song.id)}
                isPlaying={currentTrack?.id === song.id && isPlaying}
                onLike={() => handleLikeTrack(song.id)}
                onPlay={() => handlePlayTrack(song)}
                showIndex={true}
                index={index + 1}
              />
            ))}
          </div>
        </Section>

        {/* Sección de Descubrimiento */}
        <Section 
          title="Descubre Más" 
          actionText="Explorar"
          icon={<Users className="w-5 h-5" />}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 rounded-lg p-6">
              <h3 className="text-white font-semibold text-lg mb-2">Artistas Emergentes</h3>
              <p className="text-gray-300 mb-4">Descubre nuevos talentos en la plataforma</p>
              <button className="px-4 py-2 bg-white/10 text-white rounded-full hover:bg-white/20 transition-colors text-sm">
                Ver Artistas
              </button>
            </div>
            
            <div className="bg-gradient-to-r from-blue-600/20 to-green-600/20 rounded-lg p-6">
              <h3 className="text-white font-semibold text-lg mb-2">Géneros Musicales</h3>
              <p className="text-gray-300 mb-4">Explora música por tus géneros favoritos</p>
              <button className="px-4 py-2 bg-white/10 text-white rounded-full hover:bg-white/20 transition-colors text-sm">
                Explorar Géneros
              </button>
            </div>
          </div>
        </Section>
      </div>
    );
  };

  // Componente de sección reutilizable
  const Section = ({ title, actionText, onActionClick, icon, children }) => (
    <section>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          {icon}
          <h2 className="text-2xl font-bold text-white">{title}</h2>
        </div>
        {actionText && (
          <button 
            onClick={onActionClick}
            className="text-gray-400 hover:text-white text-sm font-medium transition-colors"
          >
            {actionText}
          </button>
        )}
      </div>
      {children}
    </section>
  );

  export default Dashboard;