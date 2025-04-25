import React, { useEffect, useState } from 'react';
import { GameProvider, useGame } from './contexts/GameContext';
import StartScreen from './components/StartScreen';
import MapSelectState from './game/states/MapSelectState';
import GameMapScreen from './game/screens/GameMapScreen';
import { sessionApi, saveApi, classesApi, playerApi } from './api/gameApi';
import { GameStateProvider } from './hooks/useGameState';
import MapDebugTool from './components/game/MapDebugTool';
import { SocketProvider, useSocket } from './contexts/SocketContext';
import './App.css';

// Componente interno che utilizza il contesto di gioco
function GameContent() {
  const { state, dispatch } = useGame();
  const { 
    sessionId, 
    gameState, 
    loading, 
    error 
  } = state;
  
  // Accesso al contesto del socket
  const { connectSocket, socketReady, connectionState, on, off } = useSocket();
  
  // Stato per il debug tool
  const [showDebugTool, setShowDebugTool] = useState(false);
  // Stato per indicare che la mappa è pronta e può essere visualizzata
  const [mappaPronta, setMappaPronta] = useState(false);
  
  // Attiva il debug tool con combinazione di tasti (Ctrl + Alt + D)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.ctrlKey && e.altKey && e.key === 'd') {
        setShowDebugTool(prev => !prev);
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, []);
  
  // Carica le classi disponibili all'avvio
  useEffect(() => {
    async function fetchClasses() {
      try {
        dispatch({ type: 'SET_LOADING', payload: true });
        
        const classes = await classesApi.getAvailableClasses();
        
        dispatch({ 
          type: 'SET_CLASSES', 
          payload: classes 
        });
      } catch (err) {
        console.error('Errore nel caricamento delle classi:', err);
        
        dispatch({ 
          type: 'SET_ERROR', 
          payload: 'Impossibile caricare le classi: ' + (err.message || 'Errore sconosciuto') 
        });
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    }
    
    fetchClasses();
  }, [dispatch]);
  
  // Inizializza la connessione socket quando cambia la sessione
  useEffect(() => {
    // Riferimento per controllare se la connessione è già stata tentata
    const shouldConnect = sessionId && !socketReady && !connectionState.connecting;
    
    if (!shouldConnect) {
      return; // Non tentare di connettersi se non necessario
    }
    
    // Crea una funzione per tentare la connessione
    const connectToSocket = async () => {
      console.log('Tentativo di connessione al socket con sessionId:', sessionId);
      
      try {
        // Tenta di connettersi con l'ID sessione
        await connectSocket(sessionId);
        console.log('Socket connesso con successo');
      } catch (err) {
        console.error('Errore nella connessione socket:', err);
        dispatch({ 
          type: 'SET_ERROR', 
          payload: 'Errore di connessione al server: ' + (err.message || 'Errore sconosciuto') 
        });
      }
    };
    
    // Esegui la connessione solo se necessario
    connectToSocket();
    
  }, [sessionId, connectSocket, dispatch, socketReady, connectionState.connecting]);
  
  // Registra il listener per l'evento map_change_complete
  useEffect(() => {
    if (!socketReady) {
      // Non registrare il listener se il socket non è pronto
      console.log('Socket non pronto, non registro listener map_change_complete');
      return;
    }
    
    console.log('Registrazione listener map_change_complete sul socket (socket pronto)');
    
    // Handler per l'evento map_change_complete
    function handleMapChangeComplete(data) {
      console.log('Evento map_change_complete ricevuto:', data);
      
      // Aggiorna stato globale con la nuova mappa e posizione
      if (data.mapId) {
        dispatch({ type: 'SET_MAP', payload: data.mapId });
      }
      
      // Segnala che la mappa è pronta
      setMappaPronta(true);
      
      // Cambia lo stato del gioco a 'map'
      dispatch({ type: 'SET_GAME_STATE', payload: 'map' });
    };
    
    // Registra il listener sull'evento map_change_complete
    on('map_change_complete', handleMapChangeComplete);
    
    // Cleanup
    return () => {
      console.log('Rimozione listener map_change_complete');
      off('map_change_complete', handleMapChangeComplete);
    };
  }, [socketReady, dispatch, on, off]);
  
  // Carica le informazioni sul giocatore quando cambia la sessione
  useEffect(() => {
    async function fetchPlayerInfo() {
      if (!sessionId) return;
      
      try {
        console.log('Caricamento informazioni giocatore per sessione:', sessionId);
        const playerData = await playerApi.getPlayerInfo(sessionId);
        console.log('Dati giocatore ricevuti:', playerData);
        
        dispatch({ 
          type: 'SET_PLAYER', 
          payload: playerData 
        });
      } catch (err) {
        console.error('Errore nel caricamento delle informazioni del giocatore:', err);
        dispatch({ 
          type: 'SET_ERROR', 
          payload: 'Impossibile caricare i dati del giocatore: ' + (err.message || 'Errore sconosciuto')
        });
      }
    }
    
    if (sessionId) {
      fetchPlayerInfo();
    }
  }, [sessionId, dispatch]);

  // Monitoraggio dello stato del gioco
  useEffect(() => {
    console.log('Stato corrente del gioco:', gameState);
    console.log('Session ID:', sessionId);
    console.log('Socket pronto:', socketReady);
    console.log('Stato connessione:', connectionState);
  }, [gameState, sessionId, socketReady, connectionState]);
  
  // Gestisce l'avvio di una nuova partita
  const handleStartNewGame = async (playerName, playerClass) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'CLEAR_ERROR' });
      
      console.log(`Avvio nuova partita: nome=${playerName}, classe=${playerClass}`);
      const response = await sessionApi.startNewGame(playerName, playerClass);
      console.log('Risposta server per nuova partita:', response);
      
      // Prima imposta l'ID sessione
      dispatch({ type: 'SET_SESSION', payload: response.session_id });
      
      // Attendi che lo stato sia aggiornato prima di cambiare lo stato del gioco
      setTimeout(() => {
        dispatch({ type: 'SET_GAME_STATE', payload: 'map-select' });
        dispatch({ type: 'SET_LOADING', payload: false });
      }, 100);
    } catch (err) {
      console.error('Errore nell\'avvio di una nuova partita:', err);
      
      dispatch({ 
        type: 'SET_ERROR', 
        payload: 'Impossibile avviare la partita: ' + (err.message || 'Errore sconosciuto') 
      });
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };
  
  // Gestisce il caricamento di una partita salvata
  const handleLoadGame = async (saveFileName) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'CLEAR_ERROR' });
      
      console.log(`Caricamento partita salvata: ${saveFileName}`);
      const response = await sessionApi.loadSavedGame(saveFileName);
      console.log('Risposta server per caricamento partita:', response);
      
      // Prima imposta l'ID sessione
      dispatch({ type: 'SET_SESSION', payload: response.session_id });
      
      // Attendi che lo stato sia aggiornato prima di cambiare lo stato del gioco
      setTimeout(() => {
        dispatch({ type: 'SET_GAME_STATE', payload: 'map' });
        dispatch({ type: 'SET_LOADING', payload: false });
      }, 100);
    } catch (err) {
      console.error('Errore nel caricamento della partita:', err);
      
      dispatch({ 
        type: 'SET_ERROR', 
        payload: 'Impossibile caricare la partita: ' + (err.message || 'Errore sconosciuto') 
      });
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };
  
  // Gestisce il salvataggio della partita
  const handleSaveGame = async (saveName) => {
    if (!sessionId) {
      dispatch({ 
        type: 'SET_ERROR', 
        payload: 'Nessuna sessione attiva da salvare' 
      });
      return;
    }
    
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'CLEAR_ERROR' });
      
      await saveApi.saveGame(sessionId, saveName);
      
      // Mostra messaggio di successo
      dispatch({ 
        type: 'SET_SAVE_SUCCESS', 
        payload: `Partita salvata con successo` 
      });
    } catch (err) {
      console.error('Errore nel salvataggio della partita:', err);
      
      dispatch({ 
        type: 'SET_ERROR', 
        payload: 'Impossibile salvare la partita: ' + (err.message || 'Errore sconosciuto') 
      });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };
  
  // Gestisce problemi e fallback
  const handleBackToMainMenu = () => {
    dispatch({ type: 'SET_GAME_STATE', payload: 'start-screen' });
    dispatch({ type: 'CLEAR_ERROR' });
    setMappaPronta(false);
  };
  
  // Rendering condizionale in base allo stato del gioco
  return (
    <>
      {/* Rendering dello stato di gioco */}
      {gameState === 'init' || gameState === 'start-screen' ? (
        <StartScreen 
          onStartNewGame={handleStartNewGame} 
          onLoadGame={handleLoadGame}
        />
      ) : gameState === 'map-select' ? (
        <div className="map-select-wrapper">
          <MapSelectState socketReady={socketReady} />
          {loading && <div className="global-loading-overlay">Comunicazione con il server in corso...</div>}
          {error && (
            <div className="global-error-overlay">
              <div className="error-content">
                <h3>Errore</h3>
                <p>{error}</p>
                <button onClick={handleBackToMainMenu}>Torna al menu principale</button>
              </div>
            </div>
          )}
        </div>
      ) : gameState === 'map' ? (
        <>
          {(socketReady && mappaPronta) ? (
            <GameMapScreen
              onSaveGame={handleSaveGame}
              onBackToMainMenu={handleBackToMainMenu}
              socketReady={socketReady}
            />
          ) : (
            <div className="loading-map-container">
              <div className="loading-spinner"></div>
              <p>Caricamento mappa in corso...</p>
              {connectionState.error && (
                <div className="connection-error">
                  <p>Errore di connessione: {connectionState.error}</p>
                  <button onClick={handleBackToMainMenu}>Torna al menu principale</button>
                </div>
              )}
            </div>
          )}
        </>
      ) : (
        <div className="unknown-state">
          <h2>Stato non riconosciuto: {gameState}</h2>
          <button onClick={handleBackToMainMenu}>Torna al menu principale</button>
        </div>
      )}
      
      {/* Strumento di debug (attivabile con Ctrl+Alt+D) */}
      {showDebugTool && sessionId && (
        <MapDebugTool 
          sessionId={sessionId} 
          onClose={() => setShowDebugTool(false)} 
        />
      )}
      
      {/* Pulsante di debug visibile solo in modalità sviluppo */}
      {process.env.NODE_ENV === 'development' && !showDebugTool && (
        <button 
          className="debug-tool-button" 
          onClick={() => setShowDebugTool(true)}
          title="Apri il debug tool (Ctrl+Alt+D)"
        >
          🧰
        </button>
      )}
    </>
  );
}

/**
 * Componente principale dell'applicazione
 */
function App() {
  return (
    <SocketProvider>
      <GameStateProvider>
        <GameProvider>
          <div className="app-container">
            <GameContent />
          </div>
        </GameProvider>
      </GameStateProvider>
    </SocketProvider>
  );
}

export default App; 
