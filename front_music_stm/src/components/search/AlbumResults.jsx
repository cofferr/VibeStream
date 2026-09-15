import { Play, MoreVertical, Music } from 'lucide-react';
import Pagination from './Pagination';

const AlbumResults = ({ albums, onAlbumSelect, currentPage, total, onPageChange }) => {
  if (albums.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-400">No se encontraron álbumes</p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-4">
        <p className="text-gray-400">
          {total} {total === 1 ? 'álbum encontrado' : 'álbumes encontrados'}
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
        {albums.map((album) => (
          <AlbumCard 
            key={album.id} 
            album={album} 
            onAlbumSelect={onAlbumSelect}
          />
        ))}
      </div>

      <Pagination
        currentPage={currentPage}
        totalItems={total}
        itemsPerPage={10}
        onPageChange={onPageChange}
      />
    </div>
  );
};

const AlbumCard = ({ album, onAlbumSelect }) => {
  const handleClick = () => {
    onAlbumSelect(album);
  };

  const handlePlayClick = (e) => {
    e.stopPropagation(); // Evita que se active el click del card
    // Aquí podrías agregar lógica para reproducir el álbum directamente
    console.log('Reproducir álbum:', album.title);
    // Por ejemplo: onPlayAlbum(album);
  };

  return (
    <div 
      className="bg-gray-800 rounded-lg p-4 hover:bg-gray-750 transition-colors group cursor-pointer"
      onClick={handleClick}
    >
      <div className="relative mb-4">
        {album.cover_url ? (
          <img
            src={album.cover_url}
            alt={album.title}
            className="w-full aspect-square object-cover rounded"
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
        ) : (
          <div className="w-full aspect-square bg-gradient-to-br from-purple-600 to-blue-600 rounded flex items-center justify-center">
            <Music className="w-12 h-12 text-white" />
          </div>
        )}
        
        <button 
          onClick={handlePlayClick}
          className="absolute bottom-2 right-2 w-10 h-10 bg-green-500 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shadow-lg hover:scale-105 transform transition-transform"
        >
          <Play className="w-5 h-5 text-black fill-current ml-0.5" />
        </button>
      </div>

      <div className="min-w-0">
        <h3 className="font-medium truncate mb-1">{album.title}</h3>
        <p className="text-sm text-gray-400 truncate">
          {album.artist?.name || 'Artista'}
        </p>
        <p className="text-xs text-gray-500 mt-1">
          {album.release_date ? new Date(album.release_date).getFullYear() : 'Año desconocido'}
        </p>
      </div>
    </div>
  );
};

export default AlbumResults;