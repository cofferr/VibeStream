// src/contexts/AuthContext.jsx
import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { authAPI } from '@/services/auth.js';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe ser usado dentro de un AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [authTokens, setAuthTokens] = useState(null);
  const [loading, setLoading] = useState(true);
  const [profileLoading, setProfileLoading] = useState(false);
  
  // Usar useRef para funciones que no cambian
  const isMounted = useRef(true);

  // Función para guardar tokens en localStorage
  const saveTokens = useCallback((tokens, user) => {
    if (!isMounted.current) return;
    
    localStorage.setItem('authTokens', JSON.stringify(tokens));
    localStorage.setItem('userData', JSON.stringify(user));
    setAuthTokens(tokens);
    setCurrentUser(user);
  }, []);

  // Función para limpiar tokens
  const clearTokens = useCallback(() => {
    if (!isMounted.current) return;
    
    localStorage.removeItem('authTokens');
    localStorage.removeItem('userData');
    setAuthTokens(null);
    setCurrentUser(null);
  }, []);

  // Función para actualizar el usuario en el contexto
  const updateUser = useCallback((userData) => {
    if (!isMounted.current) return;
    
    setCurrentUser(prev => {
      const updatedUser = { ...prev, ...userData };
      // Actualizar también en localStorage
      const storedUser = JSON.parse(localStorage.getItem('userData') || '{}');
      localStorage.setItem('userData', JSON.stringify({ ...storedUser, ...userData }));
      return updatedUser;
    });
  }, []);

  // Cargar detalles completos del perfil
  const loadUserProfile = useCallback(async () => {
    if (!authTokens?.accessToken) return null;
    
    try {
      setProfileLoading(true);
      const response = await authAPI.getProfile({ authTokens });
      
      if (isMounted.current) {
        updateUser(response.user);
      }
      
      return response.user;
    } catch (error) {
      console.error('Error loading user profile:', error);
      // Si hay error de autenticación, hacer logout
      if (error.message.includes('401') || error.message.includes('token')) {
        clearTokens();
      }
      throw error;
    } finally {
      if (isMounted.current) {
        setProfileLoading(false);
      }
    }
  }, [authTokens?.accessToken]); // Solo dependemos del accessToken

  // Actualizar perfil del usuario
  const updateUserProfile = useCallback(async (userData) => {
    if (!authTokens?.accessToken) {
      throw new Error('No authentication token available');
    }

    try {
      setProfileLoading(true);
      const response = await authAPI.updateProfile(userData, { authTokens });
      
      // Actualizar contexto con nuevos datos
      if (isMounted.current) {
        updateUser(response.user);
      }
      
      return response.user;
    } catch (error) {
      console.error('Error updating user profile:', error);
      throw error;
    } finally {
      if (isMounted.current) {
        setProfileLoading(false);
      }
    }
  }, [authTokens?.accessToken, updateUser]);

  // Cambiar contraseña
  const updatePassword = useCallback(async (passwordData) => {
    if (!authTokens?.accessToken) {
      throw new Error('No authentication token available');
    }

    try {
      setProfileLoading(true);
      const response = await authAPI.updateProfile(passwordData, { authTokens });
      return response;
    } catch (error) {
      console.error('Error updating password:', error);
      throw error;
    } finally {
      if (isMounted.current) {
        setProfileLoading(false);
      }
    }
  }, [authTokens?.accessToken]);

  // Verificar si el usuario es artista
  const isArtist = useCallback(() => {
    return currentUser?.role === 'artist';
  }, [currentUser?.role]); // Solo dependemos del rol

  // Verificar si el usuario es admin
  const isAdmin = useCallback(() => {
    return currentUser?.role === 'admin';
  }, [currentUser?.role]); // Solo dependemos del rol

  // Refrescar tokens (si es necesario)
  const refreshTokens = useCallback(async () => {
    if (!authTokens?.refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await authAPI.refresh(authTokens.refreshToken, { authTokens });
      const newTokens = {
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
        expiresIn: response.expires_in
      };
      
      if (isMounted.current) {
        saveTokens(newTokens, currentUser);
      }
      
      return newTokens;
    } catch (error) {
      console.error('Error refreshing tokens:', error);
      if (isMounted.current) {
        clearTokens();
      }
      throw error;
    }
  }, [authTokens?.refreshToken, currentUser, saveTokens, clearTokens]);

  // Verificar autenticación al cargar la app - SOLO UNA VEZ
  useEffect(() => {
    isMounted.current = true;
    
    const initAuth = async () => {
      try {
        const storedTokens = JSON.parse(localStorage.getItem('authTokens'));
        const storedUser = JSON.parse(localStorage.getItem('userData'));
        
        if (storedTokens && storedUser) {
          setAuthTokens(storedTokens);
          setCurrentUser(storedUser);
          
          // Solo cargar perfil si tenemos tokens válidos
          if (storedTokens.accessToken) {
            await loadUserProfile();
          }
        }
      } catch (error) {
        console.error('Error initializing auth:', error);
        if (isMounted.current) {
          clearTokens();
        }
      } finally {
        if (isMounted.current) {
          setLoading(false);
        }
      }
    };

    initAuth();

    return () => {
      isMounted.current = false;
    };
  }, []); // Empty dependency array - solo se ejecuta una vez

  const register = async (userData) => {
    try {
      const response = await authAPI.register(userData);
      return response;
    } catch (error) {
      console.error('Register error:', error);
      throw error;
    }
  };

  const login = async (credentials) => {
    try {
      const response = await authAPI.login(credentials);
      
      const tokens = {
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
        expiresIn: response.expires_in
      };
      
      if (isMounted.current) {
        saveTokens(tokens, response.user);
      }
      
      return response;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      if (authTokens) {
        await authAPI.logout({ authTokens });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      if (isMounted.current) {
        clearTokens();
      }
    }
  };

  const value = {
    // Estado
    currentUser,
    authTokens,
    loading,
    profileLoading,
    
    // Acciones básicas
    login,
    logout,
    register,
    
    // Nuevas funciones para gestión de perfil
    updateUser,
    loadUserProfile,
    updateUserProfile,
    updatePassword,
    
    // Funciones de verificación
    isArtist,
    isAdmin,
    
    // Gestión de tokens
    refreshTokens
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};