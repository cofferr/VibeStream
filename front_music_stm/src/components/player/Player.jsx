import { useState, useEffect } from "react";
import { usePlayer } from "@/contexts/PlayerContext";
import { 
  Play, 
  Pause, 
  SkipBack, 
  SkipForward, 
  Volume2, 
  VolumeX, 
  Shuffle, 
  Repeat, 
  Heart, 
  MoreHorizontal,
  Loader2,
  AlertCircle
} from "lucide-react";

const Player = () => {
  const {
    currentTrack,
    isPlaying,
    isLoading,
    volume,
    progress,
    duration,
    error,
    togglePlay,
    nextTrack,
    previousTrack,
    seekTo,
    setVolume,
    clearError,
    hasQueue,
    isFirstTrack,
    isLastTrack
  } = usePlayer();

  const [isMuted, setIsMuted] = useState(false);
  const [isLiked, setIsLiked] = useState(false);
  const [shuffle, setShuffle] = useState(false);
  const [repeat, setRepeat] = useState(false);
  const [showError, setShowError] = useState(false);

  useEffect(() => {
    if (error) {
      setShowError(true);
      const timer = setTimeout(() => {
        setShowError(false);
        clearError();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

  const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return "0:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleProgressChange = (e) => {
    if (!duration) return;
    
    const rect = e.currentTarget.getBoundingClientRect();
    const percent = (e.clientX - rect.left) / rect.width;
    const newPosition = percent * duration;
    seekTo(newPosition);
  };

  const handleVolumeChange = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const percent = (e.clientX - rect.left) / rect.width;
    const newVolume = Math.floor(percent * 100);
    setVolume(newVolume);
    if (newVolume > 0 && isMuted) {
      setIsMuted(false);
    }
  };

  const toggleMute = () => {
    if (isMuted) {
      setVolume(volume > 0 ? volume : 50);
      setIsMuted(false);
    } else {
      setVolume(0);
      setIsMuted(true);
    }
  };

  const handleErrorClose = () => {
    setShowError(false);
    clearError();
  };

  if (!currentTrack) {
    return (
      <div className="bg-gray-800 border-t border-gray-700 px-4 py-3 h-20 flex items-center justify-center">
        <div className="text-center text-gray-400 text-sm">
          Selecciona una canción para reproducir
        </div>
      </div>
    );
  }

  const progressPercent = duration ? (progress / duration) * 100 : 0;
  const displayVolume = isMuted ? 0 : volume;

  return (
    <div className="bg-gray-800 border-t border-gray-700 px-4 py-3 h-20 relative">
      {/* Banner de error */}
      {showError && (
        <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-full bg-red-500 text-white px-4 py-2 rounded-lg flex items-center gap-2 text-sm mb-2">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
          <button 
            onClick={handleErrorClose}
            className="ml-2 hover:bg-red-600 rounded p-1"
          >
            ×
          </button>
        </div>
      )}

      <div className="flex items-center justify-between h-full max-w-screen-xl mx-auto">
        {/* Información de la canción */}
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <img 
            src={currentTrack.cover || '/default-cover.png'} 
            alt={currentTrack.title} 
            className="w-12 h-12 rounded-lg object-cover flex-shrink-0"
            onError={(e) => {
              e.target.src = '/default-cover.png';
            }}
          />
          <div className="min-w-0 flex-1">
            <h4 className="font-medium text-white truncate text-sm">
              {currentTrack.title}
            </h4>
            <p className="text-xs text-gray-400 truncate">
              {currentTrack.artist || 'Artista desconocido'}
            </p>
            {isLoading && (
              <div className="flex items-center gap-1 mt-1">
                <Loader2 className="w-3 h-3 text-purple-400 animate-spin" />
                <span className="text-xs text-purple-400">Cargando...</span>
              </div>
            )}
          </div>
          <button 
            onClick={() => setIsLiked(!isLiked)}
            className={`p-1 rounded-full transition-colors flex-shrink-0 ${
              isLiked ? 'text-red-500' : 'text-gray-400 hover:text-white'
            }`}
          >
            <Heart className={`w-4 h-4 ${isLiked ? 'fill-current' : ''}`} />
          </button>
        </div>

        {/* Controles principales */}
        <div className="flex flex-col items-center gap-1 flex-1 max-w-md">
          {/* Botones de control */}
          <div className="flex items-center gap-3">
            <button 
              onClick={() => setShuffle(!shuffle)}
              className={`p-1 rounded-full transition-colors ${
                shuffle ? 'text-purple-500' : 'text-gray-400 hover:text-white'
              }`}
            >
              <Shuffle className="w-4 h-4" />
            </button>
            <button 
              onClick={previousTrack}
              disabled={!hasQueue || isFirstTrack}
              className="p-1 text-gray-400 hover:text-white transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <SkipBack className="w-4 h-4" />
            </button>
            <button 
              onClick={togglePlay}
              disabled={isLoading}
              className="p-2 bg-white text-gray-900 rounded-full hover:bg-gray-100 transition-colors mx-1 disabled:opacity-50"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : isPlaying ? (
                <Pause className="w-4 h-4" />
              ) : (
                <Play className="w-4 h-4 ml-0.5" />
              )}
            </button>
            <button 
              onClick={nextTrack}
              disabled={!hasQueue || isLastTrack}
              className="p-1 text-gray-400 hover:text-white transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <SkipForward className="w-4 h-4" />
            </button>
            <button 
              onClick={() => setRepeat(!repeat)}
              className={`p-1 rounded-full transition-colors ${
                repeat ? 'text-purple-500' : 'text-gray-400 hover:text-white'
              }`}
            >
              <Repeat className="w-4 h-4" />
            </button>
          </div>

          {/* Barra de progreso */}
          <div className="flex items-center gap-2 w-full">
            <span className="text-xs text-gray-400 min-w-[35px] text-right">
              {formatTime(progress)}
            </span>
            <div 
              className="flex-1 h-1 bg-gray-600 rounded-full cursor-pointer group"
              onClick={handleProgressChange}
            >
              <div 
                className="h-full bg-purple-500 rounded-full relative group-hover:bg-purple-400 transition-colors"
                style={{ width: `${progressPercent}%` }}
              >
                <div className="absolute right-0 top-1/2 transform -translate-y-1/2 w-3 h-3 bg-white rounded-full opacity-0 group-hover:opacity-100 shadow-lg" />
              </div>
            </div>
            <span className="text-xs text-gray-400 min-w-[35px]">
              {formatTime(duration)}
            </span>
          </div>
        </div>

        {/* Controles de volumen */}
        <div className="flex items-center gap-3 flex-1 justify-end">
          <button className="p-1 text-gray-400 hover:text-white transition-colors">
            <MoreHorizontal className="w-4 h-4" />
          </button>
          <div className="flex items-center gap-2">
            <button 
              onClick={toggleMute}
              className="p-1 text-gray-400 hover:text-white transition-colors"
            >
              {isMuted || volume === 0 ? (
                <VolumeX className="w-4 h-4" />
              ) : (
                <Volume2 className="w-4 h-4" />
              )}
            </button>
            <div 
              className="w-20 h-1 bg-gray-600 rounded-full cursor-pointer group"
              onClick={handleVolumeChange}
            >
              <div 
                className="h-full bg-gray-400 rounded-full relative group-hover:bg-white transition-colors"
                style={{ width: `${displayVolume}%` }}
              >
                <div className="absolute right-0 top-1/2 transform -translate-y-1/2 w-3 h-3 bg-white rounded-full opacity-0 group-hover:opacity-100 shadow-lg" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Player;