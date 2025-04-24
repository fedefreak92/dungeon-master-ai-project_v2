import React, { useEffect, useState } from 'react';
import socketIOService from '../services/socketIOService';

/**
 * Componente che gestisce la connessione Socket.IO al server di gioco
 */
const GameConnection = ({ children, onConnectionChange }) => {
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  const maxRetries = 3;

  useEffect(() => {
    // Gestione eventi di connessione
    const handleConnectionEstablished = (data) => {
      setConnectionStatus('connected');
      setError(null);
      setRetryCount(0);
      if (onConnectionChange) onConnectionChange('connected');
    };

    const handleConnectionClosed = (data) => {
      setConnectionStatus('disconnected');
      if (onConnectionChange) onConnectionChange('disconnected');
    };

    const handleConnectionError = (data) => {
      setConnectionStatus('error');
      setError(data.error);
      if (onConnectionChange) onConnectionChange('error', data.error);
      
      // Tentativo di riconnessione automatica
      if (retryCount < maxRetries) {
        console.log(`Tentativo di riconnessione ${retryCount + 1}/${maxRetries}...`);
        const timer = setTimeout(() => {
          setRetryCount(prev => prev + 1);
          setConnectionStatus('connecting');
          tryConnect();
        }, 3000); // Attesa di 3 secondi prima di riprovare
        
        return () => clearTimeout(timer);
      }
    };

    // Funzione per tentare la connessione
    const tryConnect = () => {
      socketIOService.connect().catch(error => {
        setConnectionStatus('error');
        setError(error.message || 'Errore di connessione');
        if (onConnectionChange) onConnectionChange('error', error.message);
      });
    };

    // Registrazione dei callback
    socketIOService.on('connection_established', handleConnectionEstablished);
    socketIOService.on('connection_closed', handleConnectionClosed);
    socketIOService.on('connection_error', handleConnectionError);

    // Connessione al server
    setConnectionStatus('connecting');
    tryConnect();

    // Pulizia al dismount del componente
    return () => {
      socketIOService.off('connection_established', handleConnectionEstablished);
      socketIOService.off('connection_closed', handleConnectionClosed);
      socketIOService.off('connection_error', handleConnectionError);
      socketIOService.disconnect();
    };
  }, [onConnectionChange, retryCount]);

  // Renderizza i children con un indicatore di stato di connessione
  return (
    <div className="game-connection">
      {connectionStatus === 'error' && (
        <div className="connection-error">
          Errore di connessione: {error || 'Errore sconosciuto'}
          {retryCount < maxRetries && <p>Tentativo di riconnessione in corso ({retryCount + 1}/{maxRetries})...</p>}
          {retryCount >= maxRetries && <p>Numero massimo di tentativi raggiunto. Ricarica la pagina.</p>}
        </div>
      )}
      {connectionStatus === 'connecting' && (
        <div className="connection-pending">
          Connessione al server in corso...
        </div>
      )}
      {children}
    </div>
  );
};

export default GameConnection; 