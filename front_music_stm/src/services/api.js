// src/services/api.js

import { Search } from "lucide-react";

// Definir las URLs base para diferentes servicios
// En Docker: usa el proxy de Nginx (/api/*)
// En desarrollo local: usa localhost directo
const API_BASES = {
  auth: import.meta.env.VITE_AUTH_URL || '/api/auth',
  streaming: import.meta.env.VITE_STREAMING_URL || '/api/streaming',
  music: import.meta.env.VITE_CONTENT_URL || '/api/content',
  artist: import.meta.env.VITE_ARTIST_URL || '/api/artist',
  search: import.meta.env.VITE_SEARCH_URL || '/api/search',
  playlist: import.meta.env.VITE_PLAYLIST_URL || '/api/playlist',
  history: import.meta.env.VITE_HISTORY_URL || '/api/history',
  subscription: import.meta.env.VITE_SUBSCRIPTION_URL || '/api/subscription',
};

// Función para requests PÚBLICOS (sin autenticación)
export const publicRequest = async (endpoint, options = {}, serviceType = 'auth') => {
  const baseURL = API_BASES[serviceType];
  
  if (!baseURL) {
    throw new Error(`Tipo de servicio no configurado: ${serviceType}`);
  }

  const url = `${baseURL}${endpoint}`;

  const config = {
    method: options.method || 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  // Manejar parámetros de consulta
  let finalUrl = url;
  if (options.params && config.method === 'GET') {
    const queryParams = new URLSearchParams(options.params).toString();
    finalUrl = `${url}?${queryParams}`;
  }

  // Manejar cuerpo para solicitudes que lo requieren
  if (options.body && ['POST', 'PUT', 'PATCH'].includes(config.method)) {
    config.body = JSON.stringify(options.body);
  }

  try {
    const response = await fetch(finalUrl, config);

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = `HTTP error! status: ${response.status}`;
      
      try {
        const errorData = JSON.parse(errorText);
        errorMessage = errorData.error || errorData.message || errorMessage;
      } catch {
        errorMessage = errorText || errorMessage;
      }

      throw new Error(errorMessage);
    }

    return await response.json();
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
};

// Función para requests AUTENTICADOS (con token)
// En api.js - MODIFICAR authenticatedRequest
export const authenticatedRequest = async (endpoint, options = {}, authContext, serviceType = 'music') => {
  const baseURL = API_BASES[serviceType];
  
  if (!baseURL) {
    throw new Error(`Tipo de servicio no configurado: ${serviceType}`);
  }

  // ✅ CORRECCIÓN: Manejar diferentes estructuras de authContext
  let token;
  if (authContext?.authTokens?.accessToken) {
    token = authContext.authTokens.accessToken;
  } else if (authContext?.accessToken) {
    token = authContext.accessToken;
  } else if (authContext?.authTokens) {
    token = authContext.authTokens.accessToken;
  }

  if (!token) {
    console.error('No authentication token available. authContext:', authContext);
    throw new Error('No authentication token available');
  }

  const url = `${baseURL}${endpoint}`;

  // ✅ DETECTAR SI ES FORMDATA
  const isFormData = options.body instanceof FormData;
  
  const config = {
    method: options.method || 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  };

  // ✅ NO establecer Content-Type para FormData
  if (!isFormData) {
    config.headers['Content-Type'] = 'application/json';
  }

  // Manejar parámetros de consulta
  let finalUrl = url;
  if (options.params && config.method === 'GET') {
    const queryParams = new URLSearchParams(options.params).toString();
    finalUrl = `${url}?${queryParams}`;
  }

  // ✅ Manejar cuerpo - NO stringificar si es FormData
  if (options.body && ['POST', 'PUT', 'PATCH'].includes(config.method)) {
    if (isFormData) {
      config.body = options.body; // FormData directamente
    } else {
      config.body = JSON.stringify(options.body); // JSON para otros casos
    }
  }

  try {
    const response = await fetch(finalUrl, config);

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = `HTTP error! status: ${response.status}`;
      
      try {
        const errorData = JSON.parse(errorText);
        errorMessage = errorData.error || errorData.message || errorMessage;
      } catch {
        errorMessage = errorText || errorMessage;
      }

      throw new Error(errorMessage);
    }

    return await response.json();
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
};

// Funciones específicas para cada servicio
export const authPublicRequest = (endpoint, options = {}) => 
  publicRequest(endpoint, options, 'auth');

export const authRequest = (endpoint, options = {}, authContext) => 
  authenticatedRequest(endpoint, options, authContext, 'auth');

export const musicRequest = (endpoint, options = {}, authContext) => 
  authenticatedRequest(endpoint, options, authContext, 'music');

export const artistRequest = (endpoint, options = {}, authContext) => 
  authenticatedRequest(endpoint, options, authContext, 'artist');

export const streamingRequest = (endpoint, options = {}, authContext) => 
  authenticatedRequest(endpoint, options, authContext, 'streaming');

export const searchRequest = (endpoint, options = {}, authContext) => 
  authenticatedRequest(endpoint, options, authContext, 'search');

export const playlistRequest = (endpoint, options = {}, authContext) =>
  authenticatedRequest(endpoint, options, authContext, 'playlist');