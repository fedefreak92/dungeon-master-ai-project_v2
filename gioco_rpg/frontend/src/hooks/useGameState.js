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
    error: null,
    gameState: 'start-screen', // start-screen, character-select, map-select, map, battle, etc.
    sessionId: null,
    playerInfo: null,
    loading: false,
    saveSuccess: null,
    loadedSaveName: null,  // Nome del salvataggio caricato
    loadingComplete: false,  // Flag che indica se il caricamento è completato
    loadConfirmed: false    // Flag che indica se il server ha confermato il caricamento
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

      // Autenticazione con il server
      let authToken = localStorage.getItem('authToken'); 
      
      if (!authToken) {
        console.error('[AUTH_FRONTEND] CRITICO: authToken (session_id) non trovato in localStorage. L\'autenticazione WebSocket potrebbe usare un token non valido o fallire. Assicurati che il session_id venga salvato in localStorage con la chiave "authToken" dopo la creazione della sessione HTTP.');
        // Se authToken non è trovato, impostalo a una stringa che indichi chiaramente l'errore
        // Questo eviterà di usare il vecchio placeholder "token-fittizio-per-sviluppo"
        // e renderà più evidente il problema nei log del server se il client tenta comunque di autenticarsi.
        authToken = 'ERRORE_SESSION_ID_NON_TROVATO_IN_LOCALSTORAGE'; 
      }

      const clientId = localStorage.getItem('clientId') || `client_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('clientId', clientId);

      console.log(`[AUTH_FRONTEND] Tento autenticazione con token: ${authToken} e client_id: ${clientId}`);
      newSocket.emit('authenticate', { 
        token: authToken,
        client_id: clientId 
      });
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
    
    // AGGIUNTA GESTORI AUTENTICAZIONE
    newSocket.on('authenticated', (authData) => {
      console.log('[AUTH_FRONTEND] Autenticazione riuscita:', authData);
      setGameState(prevState => ({
        ...prevState,
        sessionId: authData.session_id, // Memorizza il session_id ricevuto dal server
        error: null,
      }));
      // Qui potresti voler fare altre azioni, tipo caricare lo stato iniziale del gioco
      // se l'autenticazione implica l'inizio di una sessione.
    });

    newSocket.on('auth_error', (errorData) => {
      console.error('[AUTH_FRONTEND] Errore di autenticazione:', errorData);
      setGameState(prevState => ({
        ...prevState,
        gameStatus: 'error',
        error: errorData.message || 'Autenticazione fallita',
        sessionId: null,
      }));
      // Potresti voler disconnettere il socket o mostrare un messaggio all'utente
    });
    // FINE AGGIUNTA GESTORI AUTENTICAZIONE

    // Listener per aggiornamento posizione giocatore
    newSocket.on('player_position_updated', (data) => {
      console.log('[FRONTEND WS] Ricevuto evento player_position_updated:', data);
      
      setGameState(prevState => {
        console.log('[FRONTEND WS] Verifica aggiornamento posizione:');
        console.log('  - prevState.player:', prevState.player);
        console.log('  - data.player_id:', data.player_id);
        console.log('  - player corrente ID:', prevState.player ? prevState.player.id : 'N/A');
        
        // Aggiorna sempre la posizione se abbiamo i dati, indipendentemente dall'ID per debug
        if (data.x !== undefined && data.y !== undefined) {
          console.log('[FRONTEND WS] Aggiornamento posizione da:', 
                      prevState.player ? `(${prevState.player.x}, ${prevState.player.y})` : 'N/A',
                      'a:', `(${data.x}, ${data.y})`);
          
          const updatedPlayer = prevState.player ? {
            ...prevState.player,
            x: data.x,
            y: data.y,
            mappa_corrente: data.map_id || prevState.player.mappa_corrente,
          } : {
            // Se non abbiamo un player, creiamo un oggetto minimo
            id: data.player_id,
            x: data.x,
            y: data.y,
            mappa_corrente: data.map_id,
            nome: 'Giocatore'
          };
          
          return {
            ...prevState,
            player: updatedPlayer,
          };
        } else {
          console.warn('[FRONTEND WS] Dati posizione incompleti:', data);
        }
        
        return prevState;
      });
    });

    // Listener per movimento fallito
    newSocket.on('player_move_failed', (data) => {
      console.warn('[FRONTEND WS] Movimento fallito:', data.message);
      // Mostra una notifica all'utente o aggiorna lo stato con un messaggio di errore
      setGameState(prevState => ({
        ...prevState,
        error: `Movimento fallito: ${data.message}`,
        // Potresti anche voler aggiungere un flag temporaneo per mostrare l'errore nell'UI
        movementError: {
          message: data.message,
          timestamp: Date.now()
        }
      }));
      
      // Rimuovi l'errore di movimento dopo alcuni secondi
      setTimeout(() => {
        setGameState(prevState => ({
          ...prevState,
          error: prevState.error === `Movimento fallito: ${data.message}` ? null : prevState.error,
          movementError: null
        }));
      }, 3000);
    });

    // Listener per cambio mappa (se necessario)
    newSocket.on('map_changed', (data) => {
      console.log('[FRONTEND WS] Ricevuto evento map_changed:', data);
      setGameState(prevState => ({
        ...prevState,
        currentMap: data.new_map_id, // Aggiorna la mappa corrente
        player: {
          ...prevState.player,
          mappa_corrente: data.new_map_id,
          x: data.player_new_coords ? data.player_new_coords[0] : prevState.player.x, // Aggiorna le coordinate se fornite
          y: data.player_new_coords ? data.player_new_coords[1] : prevState.player.y,
        },
        player_position: data.player_new_coords ? { x: data.player_new_coords[0], y: data.player_new_coords[1] } : prevState.player_position,
        // Potrebbe essere necessario resettare/ricaricare le entità della mappa, ecc.
        entities: [], 
        // Aggiungi un messaggio per informare l'utente del cambio mappa
        mapChangeMessage: data.message || `Sei entrato in: ${data.new_map_id}`
      }));
      
      // Probabilmente qui dovresti triggerare un ricaricamento dei dati della nuova mappa
      // loadMap(data.new_map_id); // se hai una funzione loadMap
      
      // Rimuovi il messaggio di cambio mappa dopo alcuni secondi
      setTimeout(() => {
        setGameState(prevState => ({
          ...prevState,
          mapChangeMessage: null
        }));
      }, 3000);
    });

    // Listener migliorato per risultati di interazione
    newSocket.on('interaction_result', (data) => {
      console.log('[FRONTEND WS] Ricevuto evento interaction_result:', data);
      if (data.success) {
        // Potresti voler aggiornare lo stato con il risultato dell'interazione
        setGameState(prevState => ({
          ...prevState,
          lastInteractionResult: {
            success: data.success,
            message: data.message,
            timestamp: Date.now()
          }
        }));
      } else {
        // Gestisci errori di interazione
        setGameState(prevState => ({
          ...prevState,
          error: data.message || 'Errore durante l\'interazione',
          lastInteractionResult: {
            success: false,
            message: data.message,
            timestamp: Date.now()
          }
        }));
      }
      
      // Rimuovi il risultato dell'interazione dopo alcuni secondi
      setTimeout(() => {
        setGameState(prevState => ({
          ...prevState,
          lastInteractionResult: null
        }));
      }, 5000);
    });

    // Listener per aggiornamenti di dialogo
    newSocket.on('dialog_update', (data) => {
      console.log('[FRONTEND WS] Ricevuto evento dialog_update:', data);
      setGameState(prevState => ({
        ...prevState,
        dialogState: {
          active: true,
          message: data.message,
          success: data.success,
          timestamp: Date.now()
        }
      }));
    });

    // Listener per eventi di gioco generici
    newSocket.on('game_event_response', (data) => {
      console.log('[FRONTEND WS] Ricevuto evento game_event_response:', data);
      if (data.event === 'exit_to_menu') {
        // Gestisci l'uscita al menu
        setGameState(prevState => ({
          ...prevState,
          gameState: 'start-screen', // Torna alla schermata iniziale
          exitMessage: data.message
        }));
      }
      // Altri eventi possono essere gestiti qui
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
      console.log(`Invio azione ${action} al server con dati:`, data);
      
      // Gestione specificamente migliorata per l'azione save_game
      if (action === 'save_game') {
        console.log("Invio azione di salvataggio con nome:", data.name);
        socket.emit('player_action', { 
          action: 'save_game',
          data: data  // Invia data come oggetto intero
        });
      } else {
        // Per tutte le altre azioni, usa il formato standard
        socket.emit('player_action', { 
          action: action,
          params: data 
        });
      }
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

function reducer(state, action) {
  switch (action.type) {
    case 'SET_LOADED_SAVE':
      return {
        ...state,
        loadedSaveName: action.payload,
        loadingComplete: false,
        loadConfirmed: false
      };
    
    case 'SET_LOADING_COMPLETE':
      return {
        ...state,
        loadingComplete: true
      };
      
    case 'SET_LOAD_CONFIRMED':
      console.log('Reducer: SET_LOAD_CONFIRMED', action.payload);
      return {
        ...state,
        loadConfirmed: action.payload === false ? false : true
      };
      
    case 'RESET_LOAD_STATE':
      return {
        ...state,
        loadedSaveName: null,
        loadingComplete: false,
        loadConfirmed: false
      };
      
    default:
      return state;
  }
} 