import { useState, useEffect } from 'react';
import socketService from '../api/socketService';

/**
 * Hook personalizzato per gestire la connessione WebSocket tramite socketService
 * @param {string} sessionId - ID della sessione di gioco
 * @param {Object} options - Opzioni aggiuntive per il socket
 * @returns {Object} - Stato della connessione e metodi per interagire con il socket
 */
export default function useSocket(sessionId, options = {}) {
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    // Non connettere se non c'è un sessionId
    if (!sessionId) {
      setConnected(false);
      setError(null);
      return;
    }
    
    // Funzione per gestire la connessione
    async function setupConnection() {
      try {
        await socketService.connect(sessionId, options);
        setConnected(true);
        setError(null);
      } catch (err) {
        console.error('Errore nella connessione WebSocket:', err);
        setConnected(false);
        setError(`Errore di connessione: ${err.message}`);
      }
    }
    
    // Inizializza la connessione
    setupConnection();
    
    // Configura listener per cambiamenti di stato
    const handleConnect = () => {
      setConnected(true);
      setError(null);
    };
    
    const handleDisconnect = () => {
      setConnected(false);
    };
    
    const handleError = (err) => {
      setError(`Errore WebSocket: ${err.message || 'Errore sconosciuto'}`);
    };
    
    socketService.on('connect', handleConnect);
    socketService.on('disconnect', handleDisconnect);
    socketService.on('error', handleError);
    
    // Pulizia al dismount
    return () => {
      socketService.off('connect', handleConnect);
      socketService.off('disconnect', handleDisconnect);
      socketService.off('error', handleError);
      
      // Se cambia il sessionId, disconnetti
      if (sessionId !== socketService.sessionId) {
        socketService.disconnect();
      }
    };
  }, [sessionId, options]);
  
  return {
    socket: socketService.socket,
    connected,
    error,
    emit: socketService.emit.bind(socketService),
    on: socketService.on.bind(socketService),
    off: socketService.off.bind(socketService),
    requestEntities: socketService.requestEntities.bind(socketService),
    movePlayer: socketService.movePlayer.bind(socketService),
    interactWithEntity: socketService.interactWithEntity.bind(socketService)
  };
} 