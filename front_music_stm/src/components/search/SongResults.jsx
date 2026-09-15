// src/components/search/SongResults.jsx - SOLUCIÓN 1
import { Play, Heart, MoreVertical, Clock, Pause } from 'lucide-react';
import Pagination from './Pagination';
import AddToPlaylist from '@/components/playlists/AddToPlaylist';

const SongResults = ({ 
  songs, 
  currentPage, 
  total, 
  onPlaySong, 
  onPageChange, 
  formatDuration, 
  currentTrack,
  isPlaying
}) => {
  if (songs.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-400">No se encontraron canciones</p>
      </div>
    );
  }

  return (  
    <div>
      <div className="mb-4">
        <p className="text-gray-400">
          {total} {total === 1 ? 'canción encontrada' : 'canciones encontradas'}
        </p>
      </div>

      {/* ✅ QUITAR overflow-hidden y usar overflow-visible */}
      <div className="bg-gray-800 rounded-lg">
        {/* Header de la tabla */}
        <div className="grid grid-cols-12 gap-4 px-6 py-3 text-gray-400 font-medium border-b border-gray-700">
          <div className="col-span-1">#</div>
          <div className="col-span-5">Título</div>
          <div className="col-span-3">Álbum</div>
          <div className="col-span-2 text-center">
            <Clock className="w-4 h-4 inline mr-1" />
            Duración
          </div>
          <div className="col-span-1"></div>
        </div>

        {/* ✅ QUITAR overflow-hidden aquí también */}
        <div className="divide-y divide-gray-700">
          {songs.map((song, index) => (
            <SongRow
              key={song.id}
              song={song}
              index={index}
              onPlay={() => onPlaySong(song)}
              formatDuration={formatDuration}
              isCurrentTrack={currentTrack?.id === song.id}
              isPlaying={isPlaying && currentTrack?.id === song.id} 
            />
          ))}
        </div>
      </div>

      {/* Paginación */}
      <Pagination
        currentPage={currentPage}
        totalItems={total}
        itemsPerPage={10}
        onPageChange={onPageChange}
      />
    </div>
  );
};

const SongRow = ({ song, index, onPlay, formatDuration, isCurrentTrack, isPlaying }) => {
  const handleAddToPlaylistSuccess = () => {
    console.log('Canción añadida exitosamente');
  };

  const handleAddToPlaylistError = (error) => {
    console.error('Error al añadir canción:', error);
  };

  return (
    <div className="grid grid-cols-12 gap-4 px-6 py-4 items-center hover:bg-gray-750 transition-colors group relative"> {/* ✅ Añadir relative */}
      {/* Número y botón play */}
      <div className="col-span-1">
        <button
          onClick={onPlay}
          className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-600 transition-colors"
        >
          {isPlaying ? (
            <Pause className="w-4 h-4 fill-current text-green-400" />
          ) : (
            <>
              <span className={`${isCurrentTrack ? 'text-green-400' : 'text-gray-400'} group-hover:hidden text-sm`}>
                {index + 1}
              </span>
              <Play className={`w-4 h-4 fill-current hidden group-hover:block ${isCurrentTrack ? 'text-green-400' : ''}`} />
            </>
          )}
        </button>
      </div>

      {/* Información de la canción */}
      <div className="col-span-5 flex items-center space-x-3">
        <img
          src={song.album?.cover_url || '/default-album.png'
          }
          alt={song.title}
          className="w-10 h-10 rounded object-cover"
          onError={(e) => {
            e.target.src = '/default-cover.png';
          }}
        />
        <div className="min-w-0">
          <div className={`font-medium truncate ${isCurrentTrack ? 'text-green-400' : 'text-white'}`}>
            {song.title}
          </div>
          <div className="text-sm text-gray-400 truncate">
            {song.artists?.map(artist => artist.name).join(', ') || 'Artista'}
          </div>
        </div>
      </div>

      {/* Álbum */}
      <div className={`col-span-3 text-sm ${isCurrentTrack ? 'text-green-400' : 'text-gray-400'}`}>
        {song.album?.title || 'Sin álbum'}
      </div>

      {/* Duración */}
      <div className={`col-span-2 text-center ${isCurrentTrack ? 'text-green-400' : 'text-gray-400'}`}>
        {formatDuration(song.duration)}
      </div>

      {/* Acciones */}
      <div className="col-span-1 text-right relative z-20"> {/* ✅ Añadir relative y z-20 */}
        <div className="flex items-center justify-end space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button className="p-1 rounded-full hover:bg-gray-600 transition-colors">
            <Heart className="w-4 h-4 text-gray-400 hover:text-red-400" />
          </button>
          
          {/* ✅ COMPONENTE AÑADIR A PLAYLIST */}
          <AddToPlaylist 
            song={song}
            onSuccess={handleAddToPlaylistSuccess}
            onError={handleAddToPlaylistError}
          />
        </div>
      </div>
    </div>
  );
};

export default SongResults;