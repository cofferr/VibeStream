import { publicRequest, streamingRequest } from './api';

class StreamingService {
  constructor() {
    this.baseURL = import.meta.env.VITE_STREAMING_URL || '/api/streaming';
  }

  // Obtener información de la canción (pública)
  async getSongInfo(songId) {
    try {
      const response = await publicRequest(`/song/${songId}/info`, {}, 'streaming');
      return response;
    } catch (error) {
      console.error('Error obteniendo información de la canción:', error);
      throw error;
    }
  }

  // Obtener URL de streaming CON token
  getStreamUrl(songId, token) {
    return `${this.baseURL}/stream?id=${songId}&token=${token}`;
  }

  // Método alternativo usando fetch con headers de autenticación
  async getAudioBlob(songId, authContext) {
    try {
      const response = await streamingRequest('/stream', {
        method: 'GET',
        params: { id: songId }
      }, authContext, 'streaming');

      // Para el elemento audio necesitamos una URL, no un blob en este caso
      return response;
    } catch (error) {
      console.error('Error obteniendo audio blob:', error);
      throw error;
    }
  }

  // Verificar salud del servicio
  async healthCheck() {
    try {
      const response = await publicRequest('/health', {}, 'streaming');
      return response;
    } catch (error) {
      console.error('Servicio de streaming no disponible:', error);
      throw error;
    }
  }
}

export const streamingService = new StreamingService();