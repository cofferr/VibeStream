import { Play, Pause, MoreHorizontal, Lock, Globe } from "lucide-react";

const PlaylistCard = ({ playlist, onPlay, isPlaying = false }) => {
  const formatTrackCount = (count) => {
    return `${count} ${count === 1 ? 'canción' : 'canciones'}`;
  };

  return (
    <div className="card card-hover group cursor-pointer">
      {/* Cover image */}
      <div className="relative mb-4 overflow-hidden rounded-lg">
        <img
          src={playlist.cover}
          alt={playlist.name}
          className="w-full aspect-square object-cover transition-transform duration-300 group-hover:scale-105"
        />
        
        {/* Play button overlay */}
        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-40 transition-all duration-300 flex items-center justify-center">
          <button
            onClick={onPlay}
            className="p-3 bg-green-500 text-black rounded-full transform translate-y-2 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 transition-all duration-300 hover:scale-110"
          >
            {isPlaying ? (
              <Pause className="w-6 h-6 fill-current" />
            ) : (
              <Play className="w-6 h-6 fill-current ml-1" />
            )}
          </button>
        </div>
      </div>

      {/* Playlist info */}
      <div className="space-y-2">
        <h3 className="font-semibold text-white truncate group-hover:text-purple-300 transition-colors">
          {playlist.name}
        </h3>
        
        <p className="text-sm text-gray-400 truncate">
          Por {playlist.owner}
        </p>
        
        <div className="flex items-center justify-between pt-1">
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">
              {formatTrackCount(playlist.trackCount)}
            </span>
            
            {/* Privacy indicator */}
            <div className="flex items-center gap-1">
              {playlist.isPublic ? (
                <Globe className="w-3 h-3 text-gray-500" />
              ) : (
                <Lock className="w-3 h-3 text-gray-500" />
              )}
            </div>
          </div>

          <button className="p-1 rounded-full text-gray-400 hover:text-white transition-colors opacity-0 group-hover:opacity-100">
            <MoreHorizontal className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default PlaylistCard;