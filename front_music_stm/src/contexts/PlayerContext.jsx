import React, { createContext, useContext, useState, useRef, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContexts';

const PlayerContext = createContext();

export const usePlayer = () => {
  const context = useContext(PlayerContext);
  if (!context) {
    throw new Error('usePlayer debe usarse dentro de PlayerProvider');
  }
  return context;
};

export const PlayerProvider = ({ children }) => {
  const { authTokens } = useAuth();
  const [currentTrack, setCurrentTrack] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [volume, setVolume] = useState(70);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);
  const [error, setError] = useState(null);
  const [queue, setQueue] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  
  const audioRef = useRef(null);
  const currentBlobUrl = useRef(null);
  const isProcessing = useRef(false); // 🔥 NUEVO: Flag para evitar recursión

  // Limpiar blob URLs para evitar fugas de memoria
  const cleanupBlobUrl = useCallback(() => {
    if (currentBlobUrl.current) {
      URL.revokeObjectURL(currentBlobUrl.current);
      currentBlobUrl.current = null;
    }
  }, []);

  // Inicializar elemento de audio
  useEffect(() => {
    audioRef.current = new Audio();
    const audio = audioRef.current;

    // Configuración básica del audio
    audio.volume = volume / 100;
    audio.preload = 'none';

    // Event listeners
    const handleTimeUpdate = () => {
      setProgress(audio.currentTime);
    };

    const handleLoadedMetadata = () => {
      setDuration(audio.duration);
      setIsLoading(false);
    };

    const handleLoadStart = () => {
      setIsLoading(true);
      setError(null);
    };

    const handleCanPlay = () => {
      setIsLoading(false);
    };

    const handleEnded = () => {
      setIsPlaying(false);
      setProgress(0);
      if (queue.length > 0) {
        const nextIndex = (currentIndex + 1) % queue.length;
        setCurrentIndex(nextIndex);
        if (queue[nextIndex]) {
          playTrack(queue[nextIndex]);
        }
      } else {
        stop();
      }
    };

    const handleError = (e) => {
      console.error('Error en reproducción:', e);
      
      if (audio.src && audio.src !== '') {
        console.error('Audio error details:', {
          error: audio.error,
          src: audio.src,
          networkState: audio.networkState,
          readyState: audio.readyState
        });
        
        let errorMessage = 'Error al reproducir la canción';
        if (audio.error) {
          switch (audio.error.code) {
            case audio.error.MEDIA_ERR_ABORTED:
              errorMessage = 'Reproducción cancelada';
              break;
            case audio.error.MEDIA_ERR_NETWORK:
              errorMessage = 'Error de red al cargar el audio';
              break;
            case audio.error.MEDIA_ERR_DECODE:
              errorMessage = 'Error al decodificar el audio';
              break;
            case audio.error.MEDIA_ERR_SRC_NOT_SUPPORTED:
              errorMessage = 'Formato de audio no soportado';
              break;
            default:
              errorMessage = 'Error desconocido en reproducción';
          }
        }
        
        setError(errorMessage);
      }
      
      setIsLoading(false);
      setIsPlaying(false);
    };

    const handleWaiting = () => {
      setIsLoading(true);
    };

    const handlePlaying = () => {
      setIsLoading(false);
    };

    // Agregar event listeners
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('loadstart', handleLoadStart);
    audio.addEventListener('canplay', handleCanPlay);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('error', handleError);
    audio.addEventListener('waiting', handleWaiting);
    audio.addEventListener('playing', handlePlaying);

    return () => {
      // Remover event listeners
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('loadstart', handleLoadStart);
      audio.removeEventListener('canplay', handleCanPlay);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('error', handleError);
      audio.removeEventListener('waiting', handleWaiting);
      audio.removeEventListener('playing', handlePlaying);
      
      // Limpiar audio y blob URLs
      if (audioRef.current) {
        audioRef.current.pause();
      }
      cleanupBlobUrl();
    };
  }, [cleanupBlobUrl, queue, currentIndex]);

  // Actualizar volumen
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume / 100;
    }
  }, [volume]);

  // Stop function
  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setIsPlaying(false);
    setProgress(0);
    cleanupBlobUrl();
  }, [cleanupBlobUrl]);

  // Seek function
  const seekTo = useCallback((time) => {
    if (audioRef.current && duration > 0) {
      const newTime = Math.max(0, Math.min(time, duration));
      audioRef.current.currentTime = newTime;
      setProgress(newTime);
    }
  }, [duration]);

  // Clear error function
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // 🔥 CORREGIDO: Toggle play/pause sin recursión
  const togglePlay = useCallback(async () => {
    if (!audioRef.current || !currentTrack || isProcessing.current) return;

    try {
      if (isPlaying) {
        audioRef.current.pause();
        setIsPlaying(false);
      } else {
        // Si el audio ya está cargado, simplemente reproducir
        if (audioRef.current.readyState >= 2 && audioRef.current.src) {
          await audioRef.current.play();
          setIsPlaying(true);
        } else {
          // Si no está cargado, recargar la misma canción PERO sin crear recursión
          isProcessing.current = true;
          await playTrack(currentTrack);
          isProcessing.current = false;
        }
      }
    } catch (error) {
      console.error('Error al pausar/reanudar:', error);
      setError('Error al controlar reproducción');
      isProcessing.current = false;
    }
  }, [currentTrack, isPlaying]);

  // 🔥 CORREGIDO: Play track con mejor manejo de misma canción
  const playTrack = useCallback(async (track, trackList = []) => {
    // Evitar procesamiento simultáneo
    if (isProcessing.current) return;
    isProcessing.current = true;

    try {
      setError(null);
      
      // 🔥 VERIFICACIÓN MEJORADA: Misma canción
      const isSameTrack = currentTrack?.id === track.id;
      
      if (isSameTrack && audioRef.current && audioRef.current.src) {
        // Si es la misma canción Y ya está cargada, solo manejar play/pause
        if (audioRef.current.readyState >= 2) {
          if (!isPlaying) {
            await audioRef.current.play();
            setIsPlaying(true);
          }
          // Si ya está playing, no hacer nada (o podrías pausar dependiendo del caso)
          isProcessing.current = false;
          return;
        }
        // Si es la misma pero no está cargada, continuar para recargar
      }

      // Si se proporciona una lista, establecer la cola
      if (trackList.length > 0) {
        setQueue(trackList);
        const trackIndex = trackList.findIndex(t => t.id === track.id);
        setCurrentIndex(trackIndex >= 0 ? trackIndex : 0);
      }

      // Nueva canción o misma canción que necesita recarga
      setCurrentTrack(track);
      setIsLoading(true);

      // Detener reproducción actual y limpiar blob anterior
      if (audioRef.current) {
        audioRef.current.pause();
      }
      cleanupBlobUrl();

      // Verificar autenticación
      const token = authTokens?.accessToken || authTokens?.access;
      if (!token) {
        throw new Error('No hay token de autenticación disponible');
      }

      const streamingBaseUrl = import.meta.env.VITE_STREAMING_URL || '/api/streaming';
      const streamUrl = `${streamingBaseUrl}/stream?id=${track.id}`;
      
      console.log('🎵 Iniciando reproducción con fetch:', {
        track: track.title,
        url: streamUrl,
        isSameTrack: isSameTrack ? 'Misma canción, recargando' : 'Nueva canción'
      });

      // Realizar fetch con el token en el header
      const response = await fetch(streamUrl, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Range': 'bytes=0-'
        }
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Error ${response.status}: ${response.statusText}. ${errorText}`);
      }

      // Verificar que el contenido sea audio
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('audio')) {
        console.warn('⚠️ Content-Type inesperado:', contentType);
      }

      // Convertir la respuesta a blob
      const blob = await response.blob();
      
      if (blob.size === 0) {
        throw new Error('El archivo de audio está vacío o no se pudo cargar');
      }

      console.log('✅ Blob creado:', {
        size: blob.size,
        type: blob.type
      });

      const blobUrl = URL.createObjectURL(blob);
      currentBlobUrl.current = blobUrl;

      // Configurar el audio con el blob
      audioRef.current.src = blobUrl;
      audioRef.current.crossOrigin = 'anonymous';
      audioRef.current.preload = 'metadata';

      // Esperar a que el audio esté listo para reproducir
      await new Promise((resolve, reject) => {
        const onLoadedMetadata = () => {
          audioRef.current.removeEventListener('loadedmetadata', onLoadedMetadata);
          audioRef.current.removeEventListener('error', onError);
          resolve();
        };
        
        const onError = (e) => {
          audioRef.current.removeEventListener('loadedmetadata', onLoadedMetadata);
          audioRef.current.removeEventListener('error', onError);
          reject(e);
        };
        
        audioRef.current.addEventListener('loadedmetadata', onLoadedMetadata);
        audioRef.current.addEventListener('error', onError);
        
        // Timeout de seguridad
        setTimeout(() => {
          audioRef.current.removeEventListener('loadedmetadata', onLoadedMetadata);
          audioRef.current.removeEventListener('error', onError);
          reject(new Error('Timeout al cargar el audio'));
        }, 30000);
      });

      // Intentar reproducir
      try {
        await audioRef.current.play();
        setIsPlaying(true);
        setIsLoading(false);
        console.log('✅ Reproducción iniciada correctamente con blob');
      } catch (playError) {
        console.error('Error al reproducir:', playError);
        throw new Error(`No se pudo reproducir la canción: ${playError.message}`);
      }

    } catch (error) {
      console.error('Error en playTrack:', error);
      setError(error.message);
      setIsLoading(false);
      setIsPlaying(false);
      cleanupBlobUrl();
    } finally {
      isProcessing.current = false;
    }
  }, [authTokens, currentTrack, isPlaying, cleanupBlobUrl]);
  // 🔥 REMOVIDA la dependencia de togglePlay para romper el ciclo

  // Next track function
  const handleNext = useCallback(() => {
    if (queue.length > 0) {
      const nextIndex = (currentIndex + 1) % queue.length;
      setCurrentIndex(nextIndex);
      playTrack(queue[nextIndex]);
    } else {
      stop();
    }
  }, [queue, currentIndex, playTrack, stop]);

  // Previous track function
  const handlePrevious = useCallback(() => {
    if (queue.length > 0) {
      const prevIndex = currentIndex > 0 ? currentIndex - 1 : queue.length - 1;
      setCurrentIndex(prevIndex);
      playTrack(queue[prevIndex]);
    }
  }, [queue, currentIndex, playTrack]);

  // Set queue and play function
  const setQueueAndPlay = useCallback((tracks, startIndex = 0) => {
    setQueue(tracks);
    setCurrentIndex(startIndex);
    if (tracks.length > 0) {
      playTrack(tracks[startIndex], tracks);
    }
  }, [playTrack]);

  // Debug: información del estado actual
  useEffect(() => {
    if (currentTrack) {
      console.log('🎵 Player State:', {
        currentTrack: currentTrack.title,
        isPlaying,
        isLoading,
        progress,
        duration,
        hasQueue: queue.length > 0
      });
    }
  }, [currentTrack, isPlaying, isLoading, progress, duration, queue.length]);

  const value = {
    // Estado
    currentTrack,
    isPlaying,
    isLoading,
    volume,
    progress,
    duration,
    error,
    queue,
    currentIndex,
    
    // Acciones
    playTrack,
    togglePlay,
    nextTrack: handleNext,
    previousTrack: handlePrevious,
    stop,
    seekTo,
    setVolume,
    setQueue: setQueueAndPlay,
    clearError,
    
    // Información adicional
    hasCurrentTrack: !!currentTrack,
    hasQueue: queue.length > 0,
    queueLength: queue.length,
    isFirstTrack: currentIndex === 0,
    isLastTrack: currentIndex === queue.length - 1,
  };

  return (
    <PlayerContext.Provider value={value}>
      {children}
    </PlayerContext.Provider>
  );
};