import { useState, useEffect, useContext, createContext } from 'react';
import { io } from 'socket.io-client';

// Crea un contesto per lo stato di gioco
const GameStateContext = createContext();

/**
 * Funzione di utilità per garantire che i dati JSON siano sicuri per React
 * Converte qualsiasi oggetto non renderizzabile in una forma renderizzabile
 */
const sanitizeGameData = (data) => {
  if (data === null || data === undefined) return data;
  
  if (Array.isArray(data)) {
    return data.map(item => sanitizeGameData(item));
  }
  
  if (typeof data === 'object' && data !== null) {
    // Se è un oggetto Date, convertilo in stringa
    if (data instanceof Date) {
      return data.toISOString();
    }
    
    const result = {};
    
    Object.keys(data).forEach(key => {
      const value = data[key];
      
      // Gestisci ricorsivamente gli oggetti annidati
      if (typeof value === 'object' && value !== null) {
        // Per campi specifici che sappiamo essere oggetti ma sono attesi come stringhe nei componenti React
        // Ad esempio classi, razze, abilità, ecc.
        if (
          ['class', 'classe', 'razza', 'abilita', 'item', 'spell', 'slot'].includes(key) && 
          'nome' in value
        ) {
          // Preserva l'oggetto ma assicura che abbia una rappresentazione stringata
          const sanitizedObj = sanitizeGameData(value);
          sanitizedObj.toString = function() { return this.nome; };
          result[key] = sanitizedObj;
        } else {
          result[key] = sanitizeGameData(value);
        }
      } else {
        result[key] = value;
      }
    });
    
    return result;
  }
  
  // I tipi primitivi sono già sicuri (stringhe, numeri, booleani)
  return data;
};

/**
 * Provider per lo stato di gioco
 * Gestisce la connessione WebSocket e lo stato globale del gioco
 */
export const GameStateProvider = ({ children }) => {
  const [socket, setSocket] = useState(null);
  const [gameState, setGameState] = useState({
    player: null,
    currentMap: null,
    entities: [],
    inventory: [],
    quests: [],
    gameStatus: 'disconnected', // disconnected, connecting, connected, error
    error: null
  });
  
  // Inizializza la connessione WebSocket
  useEffect(() => {
    // URL del server WebSocket - usa esplicitamente localhost:5000
    const socketURL = 'http://localhost:5000';
    
    // Crea una nuova connessione
    const newSocket = io(socketURL, {
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      transports: ['websocket', 'polling'] // Preferisci WebSocket ma fallback a polling
    });
    
    // Gestori di eventi per la connessione
    newSocket.on('connect', () => {
      console.log('Connessione WebSocket stabilita');
      setGameState(prevState => ({
        ...prevState,
        gameStatus: 'connected',
        error: null
      }));
    });
    
    newSocket.on('disconnect', () => {
      console.log('Disconnesso dal server WebSocket');
      setGameState(prevState => ({
        ...prevState,
        gameStatus: 'disconnected'
      }));
    });
    
    newSocket.on('connect_error', (error) => {
      console.error('Errore di connessione WebSocket:', error);
      setGameState(prevState => ({
        ...prevState,
        gameStatus: 'error',
        error: 'Impossibile connettersi al server di gioco'
      }));
    });
    
    // Gestore per gli aggiornamenti di stato dal server
    newSocket.on('game_state_update', (newState) => {
      try {
        // Sanitizza i dati ricevuti per evitare errori di rendering
        const sanitizedState = sanitizeGameData(newState);
        
        setGameState(prevState => ({
          ...prevState,
          ...sanitizedState
        }));
      } catch (err) {
        console.error('Errore durante l\'elaborazione degli aggiornamenti di stato:', err);
      }
    });
    
    // Aggiornamenti specifici della mappa
    newSocket.on('map_update', (mapData) => {
      try {
        // Sanitizza i dati della mappa
        const sanitizedMapData = sanitizeGameData(mapData);
        
        setGameState(prevState => ({
          ...prevState,
          currentMap: sanitizedMapData
        }));
      } catch (err) {
        console.error('Errore durante l\'elaborazione degli aggiornamenti della mappa:', err);
      }
    });
    
    // Aggiornamenti specifici delle entità
    newSocket.on('entities_update', (entities) => {
      try {
        // Sanitizza i dati delle entità
        const sanitizedEntities = sanitizeGameData(entities);
        
        setGameState(prevState => ({
          ...prevState,
          entities: sanitizedEntities
        }));
      } catch (err) {
        console.error('Errore durante l\'elaborazione degli aggiornamenti delle entità:', err);
      }
    });
    
    // Salva il riferimento al socket
    setSocket(newSocket);
    
    // Aggiorna lo stato di connessione
    setGameState(prevState => ({
      ...prevState,
      gameStatus: 'connecting'
    }));
    
    // Cleanup alla disconnessione
    return () => {
      if (newSocket) {
        console.log('Cleanup nel GameStateProvider');
        
        // In React.StrictMode, il componente potrebbe essere smontato e rimontato immediatamente
        // Verifichiamo lo stato del socket prima di disconnetterlo
        if (newSocket.connected) {
          console.log('Chiusura connessione WebSocket (socket connesso)');
          newSocket.disconnect();
        } else if (newSocket.io && newSocket.io.readyState === 'opening') {
          console.log('Socket ancora in apertura, non disconnetto');
          // Non disconnettere un socket in fase di apertura
        } else {
          console.log('Chiusura socket in altro stato');
          // Rimuovi comunque gli handler se necessario
          newSocket.off();
        }
      }
    };
  }, []);
  
  /**
   * Invia un'azione al server
   * @param {string} action - Nome dell'azione
   * @param {object} data - Dati associati all'azione
   */
  const sendAction = (action, data = {}) => {
    if (socket && socket.connected) {
      socket.emit('player_action', { action, data });
    } else {
      console.error('Impossibile inviare azione: socket non connesso');
    }
  };
  
  /**
   * Carica una mappa specifica
   * @param {string} mapId - ID della mappa da caricare
   */
  const loadMap = (mapId) => {
    if (socket && socket.connected) {
      socket.emit('load_map', { mapId });
    } else {
      console.error('Impossibile caricare mappa: socket non connesso');
    }
  };
  
  /**
   * Carica il profilo del giocatore
   * @param {string} playerId - ID del giocatore
   */
  const loadPlayer = (playerId) => {
    if (socket && socket.connected) {
      socket.emit('load_player', { playerId });
    } else {
      console.error('Impossibile caricare profilo: socket non connesso');
    }
  };
  
  // Valore del contesto
  const value = {
    gameState,
    sendAction,
    loadMap,
    loadPlayer,
    isConnected: gameState.gameStatus === 'connected'
  };
  
  return (
    <GameStateContext.Provider value={value}>
      {children}
    </GameStateContext.Provider>
  );
};

/**
 * Hook personalizzato per utilizzare il contesto dello stato di gioco
 */
export const useGameState = () => {
  const context = useContext(GameStateContext);
  if (!context) {
    throw new Error('useGameState deve essere utilizzato all\'interno di un GameStateProvider');
  }
  return context;
}; 