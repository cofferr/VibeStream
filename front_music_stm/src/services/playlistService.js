import { playlistRequest } from "./api";

export const playlistServices = {
  // Obtener todas las playlists del usuario
  getUserPlaylists: (authContext, page = 1, pageSize = 20) => 
    playlistRequest('/playlists', { 
      method: 'GET',
      params: { page, page_size: pageSize }
    }, authContext),

  // Obtener una playlist específica
  getPlaylist: (playlistId, authContext) =>
    playlistRequest(`/playlists/${playlistId}`, { method: 'GET' }, authContext),

  // Crear nueva playlist
  createPlaylist: (name, description, authContext) =>
    playlistRequest('/playlists', {
      method: 'POST',
      body: { name, description }
    }, authContext),

  // Actualizar playlist
  updatePlaylist: (playlistId, name, description, authContext) =>
    playlistRequest(`/playlists/${playlistId}`, {
      method: 'PUT',
      body: { name, description }
    }, authContext),

  // Eliminar playlist
  deletePlaylist: (playlistId, authContext) =>
    playlistRequest(`/playlists/${playlistId}`, { method: 'DELETE' }, authContext),

  // Obtener canciones de una playlist
  getPlaylistSongs: (playlistId, authContext) =>
    playlistRequest(`/playlists/${playlistId}/songs`, { method: 'GET' }, authContext),

  // Añadir canción a playlist
  addSongToPlaylist: (playlistId, songId, authContext) =>
    playlistRequest(`/playlists/${playlistId}/songs`, {
      method: 'POST',
      body: { song_id: songId }
    }, authContext),

  // Eliminar canción de playlist
  removeSongFromPlaylist: (playlistId, songId, authContext) =>
    playlistRequest(`/playlists/${playlistId}/songs/${songId}`, { 
      method: 'DELETE' 
    }, authContext),
};