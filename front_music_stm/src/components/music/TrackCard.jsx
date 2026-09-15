import { useState } from "react";
import { Play, Pause, Heart, MoreHorizontal, Plus } from "lucide-react";

const TrackCard = ({ track, isLiked, onLike, onPlay, isPlaying = false }) => {
  const [showOptions, setShowOptions] = useState(false);

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="card card-hover group relative">
      {/* Cover image */}
      <div className="relative mb-4 overflow-hidden rounded-lg">
        <img
          src={track.cover}
          alt={track.title}
          className="w-full aspect-square object-cover transition-transform duration-300 group-hover:scale-105"
        />
        
        {/* Play button overlay */}
        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-40 transition-all duration-300 flex items-center justify-center">
          <button
            onClick={onPlay}
            className="p-3 bg-white text-black rounded-full transform translate-y-2 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 transition-all duration-300 hover:scale-110"
          >
            {isPlaying ? (
              <Pause className="w-6 h-6 fill-current" />
            ) : (
              <Play className="w-6 h-6 fill-current ml-1" />
            )}
          </button>
        </div>
      </div>

      {/* Track info */}
      <div className="space-y-2">
        <h3 className="font-semibold text-white truncate group-hover:text-purple-300 transition-colors">
          {track.title}
        </h3>
        
        <p className="text-sm text-gray-400 truncate">
          {track.artist}
        </p>
        
        {track.album && (
          <p className="text-xs text-gray-500 truncate">
            {track.album}
          </p>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between pt-2">
          <div className="flex items-center gap-2">
            <button
              onClick={onLike}
              className={`p-1 rounded-full transition-colors ${
                isLiked
                  ? 'text-red-500'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <Heart className={`w-4 h-4 ${isLiked ? 'fill-current' : ''}`} />
            </button>
            
            <button className="p-1 rounded-full text-gray-400 hover:text-white transition-colors">
              <Plus className="w-4 h-4" />
            </button>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">
              {formatDuration(track.duration)}
            </span>
            
            <div className="relative">
              <button
                onClick={() => setShowOptions(!showOptions)}
                className="p-1 rounded-full text-gray-400 hover:text-white transition-colors"
              >
                <MoreHorizontal className="w-4 h-4" />
              </button>

              {/* Dropdown menu */}
              {showOptions && (
                <div className="absolute right-0 top-full mt-1 bg-gray-700 rounded-lg shadow-xl z-10 min-w-[120px]">
                  <div className="py-1">
                    <button className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-600 hover:text-white">
                      Añadir a cola
                    </button>
                    <button className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-600 hover:text-white">
                      Ir al artista
                    </button>
                    <button className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-600 hover:text-white">
                      Ir al álbum
                    </button>
                    <button className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-600 hover:text-white">
                      Compartir
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Click outside to close dropdown */}
      {showOptions && (
        <div
          className="fixed inset-0 z-5"
          onClick={() => setShowOptions(false)}
        />
      )}
    </div>
  );
};

export default TrackCard;