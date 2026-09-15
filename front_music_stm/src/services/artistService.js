// src/services/artist.js
import { artistRequest } from "./api";

// src/services/artist.js
export const artistAPI = {
    // Registrar artista con FORM-DATA
    registerArtist: async (formData, authContext) => {
        return await artistRequest('/artists/register', {
            method: 'POST',
            headers:{},
            body: formData,
        }, authContext);
    },

    // Obtener perfil de artista del usuario actual
    getMyArtist: async (authContext) => {
        return await artistRequest('/artists/me', {
            method: 'GET',
        }, authContext);
    },

    // Actualizar artista
    updateArtist: async (formData, authContext) => {
        return await artistRequest('/artists/me', {
            method: 'PUT',
            headers: {
                // No establecer Content-Type para FormData
            },
            body: formData,
        }, authContext);
    },

    // Eliminar artista
    deleteArtist: async (authContext) => {
        return await artistRequest('/artists/me', {
            method: 'DELETE',
        }, authContext);
    },

    // Verificar si el usuario es artista - CORREGIDO
    checkIfArtist: async (authContext) => {
        try {
            const response = await artistRequest('/artists/me', {
                method: 'GET',
            }, authContext);
            
            console.log('🔍 Respuesta completa de /me:', response);
            console.log('🔍 response.data:', response.data);
            console.log('🔍 response.data.isArtist:', response.data?.isArtist);
            
            // La respuesta tiene: { success: true, data: { isArtist: boolean }, message: string }
            return { 
                isArtist: response.data?.isArtist || false, // ← EXTRACT isArtist FROM RESPONSE
                data: response 
            };
        } catch (error) {
            console.error('🔍 Error en checkIfArtist:', error);
            if (error.message.includes('404') || error.message.includes('no encontrado')) {
                return { isArtist: false, data: null };
            }
            throw error;
        }
    }
};