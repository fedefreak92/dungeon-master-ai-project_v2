import React, { useEffect } from 'react';
import { GameProvider, useGame } from './contexts/GameContext';
import StartScreen from './components/StartScreen';
import MapSelectState from './game/states/MapSelectState';
import GameMapScreen from './game/screens/GameMapScreen';
import { sessionApi, saveApi, classesApi, playerApi } from './api/gameApi';
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
  }, [gameState, sessionId]);
  
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
  };
  
  // Rendering condizionale in base allo stato del gioco
  switch (gameState) {
    case 'init':
    case 'start-screen':
      return (
        <StartScreen 
          onStartNewGame={handleStartNewGame} 
          onLoadGame={handleLoadGame}
        />
      );
      
    case 'map-select':
      return (
        <div className="map-select-wrapper">
          <MapSelectState />
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
      );
      
    case 'map':
      return <GameMapScreen />;
      
    default:
      return (
        <div className="unknown-state">
          <h2>Stato sconosciuto: {gameState}</h2>
          <button onClick={() => dispatch({ type: 'SET_GAME_STATE', payload: 'start-screen' })}>
            Torna al menu principale
          </button>
        </div>
      );
  }
}

// Componente principale dell'applicazione
function App() {
  return (
    <GameProvider>
      <div className="app-container">
        <GameContent />
      </div>
    </GameProvider>
  );
}

export default App; 
