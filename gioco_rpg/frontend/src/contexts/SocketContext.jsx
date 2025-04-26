import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
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
  
  // Stato per tracciare il socket effettivo e forzare aggiornamento
  const [socketInstance, setSocketInstance] = useState(socketService.socket);
  
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
      
      // Aggiorna l'istanza del socket se necessario
      if (socketInstance !== socketService.socket) {
        setSocketInstance(socketService.socket);
      }
      
      connectionCheckRunning.current = false;
    };
    
    // Esegui subito il primo check
    updateConnectionState();
    
    // Imposta un intervallo più breve per i check di connessione
    const interval = setInterval(() => {
      // Pianifica l'aggiornamento con un piccolo ritardo per evitare loop
      if (connectionUpdateTimeout.current) {
        clearTimeout(connectionUpdateTimeout.current);
      }
      
      connectionUpdateTimeout.current = setTimeout(updateConnectionState, 100);
    }, 1000); // Intervallo più breve (1 secondo) per rilevare rapidamente i problemi
    
    // Gestori per gli eventi di connessione con retry per errori
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
      // Non imposta subito error su disconnessione normale, permettendo un tentativo di riconnessione
      setConnectionState(prev => ({
        connected: false,
        connecting: reason !== 'io server disconnect' && reason !== 'io client disconnect',
        error: prev.error // Mantieni l'errore precedente se presente
      }));
      
      if (reason === 'io server disconnect' || reason === 'io client disconnect') {
        setSocketReady(false);
      }
    };
    
    const handleConnectError = (error) => {
      console.error('SocketContext: errore di connessione', error);
      // Tentativo di riconnessione automatica in caso di errore di connessione
      setConnectionState(prev => ({
        connected: false,
        connecting: true, // Imposta a true per mostrare che sta tentando di riconnettersi
        error: error.message
      }));
      
      // Non imposta socketReady a false per permettere un nuovo tentativo
      // Tentativo di riconnessione automatico dopo un breve ritardo
      setTimeout(() => {
        if (socketService.sessionId) {
          console.log('SocketContext: tentativo di riconnessione automatica...');
          socketService.connect(socketService.sessionId)
            .then(() => {
              console.log('SocketContext: riconnessione automatica riuscita');
              setSocketReady(true);
              setConnectionState({
                connected: true,
                connecting: false,
                error: null
              });
            })
            .catch(err => {
              console.error('SocketContext: riconnessione automatica fallita', err);
              setSocketReady(false);
              setConnectionState({
                connected: false,
                connecting: false,
                error: err.message
              });
            });
        }
      }, 2000); // Attendi 2 secondi prima di tentare la riconnessione
    };
    
    // Registra i listener sul socket
    if (socketService.socket) {
      socketService.on('connect', handleConnect);
      socketService.on('disconnect', handleDisconnect);
      socketService.on('connect_error', handleConnectError);
      
      // Aggiungi un gestore per l'errore di timeout che è specifico di Socket.IO
      socketService.on('error', (error) => {
        console.error('SocketContext: errore socket generico', error);
        if (error && error.message && error.message.includes('timeout')) {
          handleConnectError(error); // Tratta i timeout come errori di connessione
        }
      });
    }
    
    // Aggiorna l'istanza del socket all'inizio
    setSocketInstance(socketService.socket);

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
        socketService.off('error');
      }
    };
  }, [socketInstance]);
  
  /**
   * Inizializza la connessione socket
   * Memoizzata con useCallback per stabilità referenziale
   */
  const connectSocket = useCallback(async (sessionId) => {
    // Usa connectionState.current per leggere lo stato più recente senza causare ri-render
    const currentConnectionState = connectionState;
    
    try {
      // Previeni riconnessioni mentre è in corso una connessione
      if (currentConnectionState.connecting) {
        console.log('SocketContext: connessione già in corso, ignoro la richiesta');
        return false;
      }
      
      // Aggiorna lo stato per indicare che la connessione è in corso
      setConnectionState(prev => ({
        ...prev,
        connecting: true,
        error: null
      }));
      
      await socketService.connect(sessionId);
      // L'aggiornamento a connected: true avverrà tramite l'evento 'connect'
      
      // Aggiorna l'istanza del socket dopo la connessione
      setSocketInstance(socketService.socket);
      return true;
    } catch (error) {
      console.error("SocketContext: Errore durante connectSocket", error);
      setConnectionState({
        connected: false,
        connecting: false,
        error: error.message
      });
      setSocketInstance(socketService.socket); // Assicurati che l'istanza sia aggiornata anche in caso di errore
      return false;
    }
    // Aggiungi connectionState come dipendenza se leggi direttamente lo stato
  }, [connectionState.connecting]); // Dipende solo da connecting per evitare loop
  
  /**
   * Chiudi la connessione socket
   * Memoizzata con useCallback
   */
  const disconnectSocket = useCallback(() => {
    socketService.disconnect();
    setSocketReady(false);
    setConnectionState({
      connected: false,
      connecting: false,
      error: null
    });
    setSocketInstance(null); // Resetta l'istanza del socket
  }, []); // Nessuna dipendenza

  // Funzioni wrapper memoizzate per le operazioni sul socket
  const emit = useCallback((...args) => {
    if (socketService.socket) {
      return socketService.emit(...args);
    }
    console.warn("Socket non disponibile per emit");
  }, [socketInstance]); // Dipende dall'istanza del socket

  const emitWithAck = useCallback((...args) => {
    if (socketService.socket) {
      return socketService.emitWithAck(...args);
    }
    console.warn("Socket non disponibile per emitWithAck");
    return Promise.reject(new Error("Socket non disponibile"));
  }, [socketInstance]); // Dipende dall'istanza del socket

  const on = useCallback((...args) => {
    if (socketService.socket) {
      return socketService.on(...args);
    }
    console.warn("Socket non disponibile per on");
  }, [socketInstance]); // Dipende dall'istanza del socket

  const off = useCallback((...args) => {
    if (socketService.socket) {
      return socketService.off(...args);
    }
    console.warn("Socket non disponibile per off");
  }, [socketInstance]); // Dipende dall'istanza del socket

  // Valore del contesto memoizzato
  // Includi le funzioni memoizzate
  const contextValue = React.useMemo(() => ({
    socketReady,
    connectionState,
    connectSocket,
    disconnectSocket,
    emit,
    emitWithAck,
    on,
    off
  }), [socketReady, connectionState, connectSocket, disconnectSocket, emit, emitWithAck, on, off]);

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