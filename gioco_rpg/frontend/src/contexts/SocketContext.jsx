import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import socketService from '../api/socketService';

// Crea il contesto per il socket
const SocketContext = createContext(null);

/**
 * Provider per il contesto del socket
 * Gestisce la connessione al socket e lo stato di pronto
 */
export const SocketProvider = ({ children }) => {
  // Gestisci lo stato di connessione e prontezza del socket
  const [socketReady, setSocketReady] = useState(false);
  const [connectionState, setConnectionState] = useState({
    connected: null,
    connecting: false,
    error: null
  });
  
  // Riferimento per evitare aggiornamenti multipli
  const connectionCheckRunning = useRef(false);
  const connectionUpdateTimeout = useRef(null);
  
  // Aggiorna lo stato di connessione quando cambia
  useEffect(() => {
    const updateConnectionState = () => {
      // Evita aggiornamenti multipli simultanei
      if (connectionCheckRunning.current) return;
      
      connectionCheckRunning.current = true;
      
      const isConnected = socketService.isConnected();
      const isReady = socketService.isReady();
      
      // Aggiorna lo stato solo se c'è un cambiamento effettivo
      setConnectionState(prevState => {
        if (prevState.connected !== isConnected || prevState.connecting !== false) {
          return {
            connected: isConnected,
            connecting: false,
            error: null
          };
        }
        return prevState;
      });
      
      setSocketReady(isReady);
      
      if (isConnected && !isReady) {
        // Se il socket è connesso ma non pronto, impostiamolo come pronto
        console.log('SocketContext: socket connesso ma non pronto, imposto a pronto');
        socketService.socketReady = true;
        setSocketReady(true);
      }
      
      connectionCheckRunning.current = false;
    };
    
    // Esegui subito il primo check
    updateConnectionState();
    
    // Imposta un intervallo ragionevole per i check successivi
    const interval = setInterval(() => {
      // Pianifica l'aggiornamento con un piccolo ritardo per evitare loop
      if (connectionUpdateTimeout.current) {
        clearTimeout(connectionUpdateTimeout.current);
      }
      
      connectionUpdateTimeout.current = setTimeout(updateConnectionState, 200);
    }, 3000); // Intervallo più lungo (3 secondi)
    
    // Gestori per gli eventi di connessione
    const handleConnect = () => {
      console.log('SocketContext: connessione stabilita');
      setConnectionState({
        connected: true,
        connecting: false,
        error: null
      });
      setSocketReady(true);
    };
    
    const handleDisconnect = (reason) => {
      console.log(`SocketContext: disconnesso (${reason})`);
      setConnectionState({
        connected: false,
        connecting: false,
        error: reason === 'io server disconnect' ? 'Disconnesso dal server' : null
      });
      
      if (reason === 'io server disconnect' || reason === 'io client disconnect') {
        setSocketReady(false);
      }
    };
    
    const handleConnectError = (error) => {
      console.error('SocketContext: errore di connessione', error);
      setConnectionState({
        connected: false,
        connecting: false,
        error: error.message
      });
      setSocketReady(false);
    };
    
    // Registra i listener sul socket
    if (socketService.socket) {
      socketService.on('connect', handleConnect);
      socketService.on('disconnect', handleDisconnect);
      socketService.on('connect_error', handleConnectError);
    }
    
    // Cleanup
    return () => {
      // Rimuovi solo i listener e gli intervalli
      clearInterval(interval);
      if (connectionUpdateTimeout.current) {
        clearTimeout(connectionUpdateTimeout.current);
      }
      
      if (socketService.socket) {
        socketService.off('connect', handleConnect);
        socketService.off('disconnect', handleDisconnect);
        socketService.off('connect_error', handleConnectError);
      }
    };
  }, []);
  
  /**
   * Inizializza la connessione socket
   * @param {string} sessionId - ID della sessione di gioco
   * @returns {Promise} Promise che si risolve quando la connessione è stabilita
   */
  const connectSocket = async (sessionId) => {
    try {
      // Previeni riconnessioni mentre è in corso una connessione
      if (connectionState.connecting) {
        console.log('SocketContext: connessione già in corso, ignoro la richiesta');
        return false;
      }
      
      setConnectionState(prev => ({
        ...prev,
        connecting: true,
        error: null
      }));
      
      await socketService.connect(sessionId);
      
      return true;
    } catch (error) {
      setConnectionState({
        connected: false,
        connecting: false,
        error: error.message
      });
      
      return false;
    }
  };
  
  /**
   * Chiudi la connessione socket
   */
  const disconnectSocket = () => {
    socketService.disconnect();
    setSocketReady(false);
    setConnectionState({
      connected: false,
      connecting: false,
      error: null
    });
  };
  
  // Valore del contesto
  const contextValue = {
    socketReady,
    connectionState,
    connectSocket,
    disconnectSocket,
    // Funzioni wrapper per le operazioni sul socket
    emit: socketService.emit.bind(socketService),
    emitWithAck: socketService.emitWithAck.bind(socketService),
    on: socketService.on.bind(socketService),
    off: socketService.off.bind(socketService)
  };
  
  return (
    <SocketContext.Provider value={contextValue}>
      {children}
    </SocketContext.Provider>
  );
};

/**
 * Hook per utilizzare il contesto del socket
 * @returns {Object} Il valore del contesto del socket
 */
export const useSocket = () => {
  const context = useContext(SocketContext);
  
  if (!context) {
    throw new Error('useSocket deve essere utilizzato all\'interno di un SocketProvider');
  }
  
  return context;
};

export default SocketContext; 