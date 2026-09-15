// src/services/musicService.js
import { musicRequest } from './api';

export const musicAPI = {
  // Obtener álbumes del artista autenticado
  getMyAlbums: async (authContext) => {
    return musicRequest('/albums/my-albums', {}, authContext);
  },

  // Obtener álbumes de un artista específico
  getArtistAlbums: async (artistId, authContext) => {
    return musicRequest(`/albums/artist/${artistId}`, {}, authContext);
  },

  // Obtener canciones de un álbum
  getAlbumSongs: async (albumId, authContext) => {
    return musicRequest(`/albums/${albumId}/songs`, {}, authContext);
  },

  // Obtener un álbum específico
  getAlbum: async (albumId, authContext) => {
    return musicRequest(`/albums/${albumId}`, {}, authContext);
  },

  // Crear un nuevo álbum
  createAlbum: async (formData, authContext) => {
    return musicRequest('/albums/', {
      method: 'POST',
      headers: {
        // NO establecer Content-Type - el navegador lo hará automáticamente para FormData
      },
      body: formData
    }, authContext);
  },

  // Actualizar álbum
  updateAlbum: async (albumId, formData, authContext) => {
    return musicRequest(`/albums/${albumId}`, {
      method: 'PUT',
      headers: {
        // NO establecer Content-Type para FormData
      },
      body: formData
    }, authContext);
  },

  // Eliminar álbum
  deleteAlbum: async (albumId, authContext) => {
    return musicRequest(`/albums/${albumId}`, {
      method: 'DELETE'
    }, authContext);
  },

  // create song, update song, delete song could be added similarly

  createSong: async (formData, authContext) => {
    return musicRequest('/songs/', {
      method: 'POST',
      body: formData
    }, authContext);
  },

  updateSong: async (songId, formData, authContext) => {
    return musicRequest(`/songs/${songId}`, {
      method: 'PUT',
      body: formData
    }, authContext);
  },

  deleteSong: async (songId, authContext) => {
    return musicRequest(`/songs/${songId}`, {
      method: 'DELETE'
    }, authContext);
  },

  getSong: async (songId, authContext) => {
    return musicRequest(`/songs/${songId}`, {}, authContext);
  }

  
};