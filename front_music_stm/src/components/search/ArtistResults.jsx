import { Users, MoreVertical, Play } from 'lucide-react';
import Pagination from './Pagination';

const ArtistResults = ({ artists, currentPage, total, onPageChange, onArtistSelect }) => {
  if (artists.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-400">No se encontraron artistas</p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-4">
        <p className="text-gray-400">
          {total} {total === 1 ? 'artista encontrado' : 'artistas encontrados'}
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
        {artists.map((artist) => (
          <ArtistCard 
            key={artist.id} 
            artist={artist} 
            onArtistSelect={onArtistSelect}
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

const ArtistCard = ({ artist, onArtistSelect }) => {
  const handleClick = () => {
    onArtistSelect(artist);
  };

  const handlePlayClick = (e) => {
    e.stopPropagation(); // Evita que se active el click del card
    // Aquí podrías agregar lógica para reproducir las canciones más populares del artista
    console.log('Reproducir artista:', artist.name);
    // Por ejemplo: onPlayArtist(artist);
  };

  return (
    <div 
      className="bg-gray-800 rounded-lg p-4 hover:bg-gray-750 transition-colors group text-center cursor-pointer"
      onClick={handleClick}
    >
      <div className="relative mb-4">
        {artist.profile_pic ? (
          <img
            src={artist.profile_pic}
            alt={artist.name}
            className="w-32 h-32 mx-auto rounded-full object-cover group-hover:scale-105 transition-transform"
          />
        ) : (
          <div className="w-32 h-32 mx-auto bg-gradient-to-br from-purple-600 to-blue-600 rounded-full flex items-center justify-center group-hover:scale-105 transition-transform">
            <Users className="w-12 h-12 text-white" />
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
        <h3 className="font-medium truncate">{artist.name}</h3>
        <p className="text-sm text-gray-400">Artista</p>
      </div>
    </div>
  );
};

export default ArtistResults;