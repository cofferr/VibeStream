import { searchRequest } from './api';

class SearchService {
  constructor() {
    this.baseEndpoint = '/search';
  }

  async search(query, options = {}, authContext) {
    const { 
      songPage = 1, 
      albumPage = 1, 
      artistPage = 1, 
      limit = 10 
    } = options;

    try {
      const response = await searchRequest(this.baseEndpoint, {
        method: 'GET',
        params: {
          q: query,
          song_page: songPage,
          album_page: albumPage,
          artist_page: artistPage,
          limit: limit,
        },
      }, authContext);

      return response;
    } catch (error) {
      console.error('Error en búsqueda:', error);
      throw error;
    }
  }

  // Búsqueda rápida para sugerencias (opcional)
  async quickSearch(query, authContext) {
    try {
      const response = await searchRequest(this.baseEndpoint, {
        method: 'GET',
        params: {
          q: query,
          limit: 5, // Menos resultados para sugerencias
        },
      }, authContext);

      return response;
    } catch (error) {
      console.error('Error en búsqueda rápida:', error);
      throw error;
    }
  }
}

export const searchService = new SearchService();