// src/services/auth.js - VERSIÓN CORREGIDA
import { authPublicRequest, authRequest } from './api';

export const authAPI = {
  // Endpoints PÚBLICOS - no requieren token
  login: async (credentials) => {
    return authPublicRequest('/login', {
      method: 'POST',
      body: credentials
    });
  },

  register: async (userData) => {
    return authPublicRequest('/register', {
      method: 'POST', 
      body: userData
    });
  },

  // Endpoints PROTEGIDOS - requieren token
  refresh: async (refreshToken, authContext) => {
    return authRequest('/refresh', {
      method: 'POST',
      body: { refresh_token: refreshToken }
    }, authContext);
  },

  logout: async (authContext) => {
    return authRequest('/logout', {
      method: 'POST'
    }, authContext);
  },

  // Si tienes otros métodos protegidos:
  getProfile: async (authContext) => {
    return authRequest('/user/me', {}, authContext);
  },

  updateProfile: async (userData, authContext) => {
    return authRequest('/update', {
      method: 'PUT',
      body: userData
    }, authContext);
  }
};