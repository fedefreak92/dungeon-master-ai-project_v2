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
  const { connectSocket, socketReady, connectionState, on, off, emit } = useSocket();
  
  // Stato per il debug tool
  const [showDebugTool, setShowDebugTool] = useState(false);
  // Stato per indicare che la mappa è pronta e può essere visualizzata
  const [mappaPronta, setMappaPronta] = useState(false);
  
  // Stato per tracciare quando dobbiamo emettere game_loaded
  const [pendingGameLoaded, setPendingGameLoaded] = useState(null);
  
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
      console.log('Socket non pronto, non registro listener map_change_complete');
      return;
    }
    
    console.log('Registrazione listener map_change_complete sul socket (socket pronto)');
    
    // Handler per l'evento map_change_complete
    function handleMapChangeComplete(data) {
      console.log('>>> handleMapChangeComplete ESEGUITA! Dati ricevuti:', data);
      
      // Aggiorna stato globale con la nuova mappa e posizione
      if (data && data.mapId) {
        console.log(`handleMapChangeComplete: Aggiorno mappa a ${data.mapId}`);
        dispatch({ type: 'SET_MAP', payload: data.mapId });
      } else {
        console.warn('handleMapChangeComplete: Dati mappa mancanti nell\'evento', data);
      }
      
      // Segnala che la mappa è pronta
      console.log('handleMapChangeComplete: Imposto mappaPronta a true');
      setMappaPronta(true);
      
      // Cambia lo stato del gioco a 'map'
      console.log('handleMapChangeComplete: Imposto gameState a map');
      dispatch({ type: 'SET_GAME_STATE', payload: 'map' });

      // Resetta lo stato di caricamento globale usando dispatch
      console.log('handleMapChangeComplete: Resetto lo stato di loading globale');
      dispatch({ type: 'SET_LOADING', payload: false });
      
      // Se l'evento proviene da un salvataggio caricato, conferma che il caricamento è avvenuto
      if (data.fromSave) {
        console.log('handleMapChangeComplete: Caricamento da salvataggio completato');
        dispatch({ type: 'SET_LOAD_CONFIRMED', payload: true });
      }
    }
    
    // Registra direttamente il listener sull'evento
    on('map_change_complete', handleMapChangeComplete);
    
    // Rimuovi il listener quando il componente viene smontato
    return () => {
      console.log('Rimozione listener map_change_complete');
      off('map_change_complete', handleMapChangeComplete);
    };
  }, [socketReady, dispatch, on, off]);
  
  // Carica le informazioni sul giocatore quando cambia la sessione o lo stato del gioco
  useEffect(() => {
    let isMounted = true;
    let isLoading = false;
    
    async function fetchPlayerInfo() {
      if (!sessionId || isLoading) return;
      
      try {
        isLoading = true;
        console.log('Caricamento informazioni giocatore per sessione:', sessionId);
        const playerData = await playerApi.getPlayerInfo(sessionId);
        
        // Se il componente è stato smontato nel frattempo, interrompi
        if (!isMounted) return;
        
        console.log('Dati giocatore RICEVUTI dal server:', playerData);
        console.log('HP ORIGINALE RICEVUTO DAL SERVER:', playerData.hp, '/', playerData.hp_max);
        
        // Correggi i dati HP se sono zero o non definiti
        if (playerData) {
          // Otteniamo la classe del giocatore per determinare valori appropriati
          const classeGiocatore = typeof playerData.classe === 'object' ? 
            playerData.classe.id : 
            (typeof playerData.classe === 'string' ? playerData.classe : 'guerriero').toLowerCase();
          
          // Valori di HP base per classe come fallback, allineati con il backend
          const hpBaseFallback = {
            'guerriero': 12,
            'mago': 6, 
            'ladro': 8,
            'chierico': 10
          }[classeGiocatore] || 10; // 10 è un valore ragionevole come ultimo fallback
          
          // Utilizziamo hp_max dal backend o un valore appropriato per la classe
          const maxHP = playerData.hp_max || playerData.maxHP || hpBaseFallback;
          console.log('HP MAX CALCOLATO:', maxHP, 'per classe:', classeGiocatore);
          
          // Se l'HP è zero ma maxHP è valido, imposta HP a maxHP
          if ((playerData.hp === 0 || playerData.hp === undefined || playerData.hp === null) && maxHP > 0) {
            console.log(`Correzione HP: impostato da ${playerData.hp} a ${maxHP}`);
            playerData.hp = maxHP;
            playerData.currentHP = maxHP;
          }
          
          console.log('HP FINALE PRIMA DEL DISPATCH:', playerData.hp, '/', playerData.hp_max || maxHP);
        }
        
        dispatch({ 
          type: 'SET_PLAYER', 
          payload: playerData 
        });
      } catch (err) {
        if (!isMounted) return;
        
        console.error('Errore nel caricamento delle informazioni del giocatore:', err);
        dispatch({ 
          type: 'SET_ERROR', 
          payload: 'Impossibile caricare i dati del giocatore: ' + (err.message || 'Errore sconosciuto')
        });
      } finally {
        isLoading = false;
      }
    }
    
    // Carica le informazioni del giocatore sia al cambio di sessione che quando lo stato cambia a "map"
    if (sessionId && (gameState === 'map' || !gameState)) {
      console.log(`Caricamento dati giocatore per gameState=${gameState}`);
      fetchPlayerInfo();
    }
    
    // Cleanup per evitare aggiornamenti di stato dopo lo smontaggio
    return () => {
      isMounted = false;
    };
  }, [sessionId, dispatch, gameState]); // Aggiunto gameState alle dipendenze per ricaricare quando cambia lo stato
  
  // Aggiungi una funzione per pulire localStorage
  const clearLocalStorageData = () => {
    console.log('Pulizia localStorage...');
    localStorage.clear();
    sessionStorage.clear();
    console.log('localStorage e sessionStorage puliti!');
    alert('Cache del browser pulita. Ricarica la pagina per vedere le modifiche.');
  };
  
  // Monitoraggio dello stato del gioco
  useEffect(() => {
    console.log('Stato corrente del gioco:', gameState);
    console.log('Session ID:', sessionId);
    console.log('Socket pronto:', socketReady);
    console.log('Stato connessione:', connectionState);
    if (state.player) {
      console.log('STATO PLAYER HP:', state.player.hp, '/', state.player.hp_max);
    }
  }, [gameState, sessionId, socketReady, connectionState, state.player]);
  
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
      dispatch({ type: 'RESET_LOAD_STATE' });
      
      console.log(`Caricamento partita salvata: ${saveFileName}`);
      dispatch({ type: 'SET_LOADED_SAVE', payload: saveFileName });
      
      const response = await sessionApi.loadSavedGame(saveFileName);
      console.log('Risposta server per caricamento partita:', response);
      
      // Prima imposta l'ID sessione
      dispatch({ type: 'SET_SESSION', payload: response.session_id });
      
      // Se abbiamo info sul giocatore, aggiorniamo anche quelle
      if (response.player_info && Object.keys(response.player_info).length > 0) {
        dispatch({ type: 'SET_PLAYER_INFO', payload: response.player_info });
      }
      
      // Segnala che il caricamento è completato a livello di operazioni API
      dispatch({ type: 'SET_LOADING_COMPLETE' });
      
      // Attendi che lo stato sia aggiornato prima di cambiare lo stato del gioco
      setTimeout(() => {
        dispatch({ type: 'SET_GAME_STATE', payload: 'map' });
        dispatch({ type: 'SET_LOADING', payload: false });
        
        // Prepara l'evento game_loaded da emettere quando il socket sarà pronto
        if (socketReady && emit) {
          console.log('Socket già pronto, emissione immediata evento game_loaded');
          emit('game_loaded', {
            sessionId: response.session_id,
            saveName: saveFileName
          });
        } else {
          console.log('Socket non ancora pronto, evento game_loaded sarà emesso quando il socket sarà pronto');
          setPendingGameLoaded({ sessionId: response.session_id, saveName: saveFileName });
        }
      }, 300);
    } catch (err) {
      console.error('Errore nel caricamento della partita:', err);
      
      dispatch({ 
        type: 'SET_ERROR', 
        payload: 'Impossibile caricare la partita: ' + (err.message || 'Errore sconosciuto') 
      });
      dispatch({ type: 'RESET_LOAD_STATE' });
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
  
  // Aggiungiamo pulsante di debug per pulire localStorage
  const debugButton = (
    <div 
      className="debug-clear-storage" 
      style={{ 
        position: 'fixed', 
        bottom: '10px', 
        right: '10px', 
        zIndex: 9999,
        padding: '8px',
        background: 'red',
        color: 'white',
        cursor: 'pointer',
        borderRadius: '5px'
      }}
      onClick={clearLocalStorageData}
    >
      Pulisci Cache
    </div>
  );
  
  // Emette game_loaded quando il socket diventa pronto
  useEffect(() => {
    if (socketReady && emit && pendingGameLoaded) {
      console.log('Socket ora pronto, emissione evento game_loaded per notificare il server del caricamento completato');
      emit('game_loaded', {
        sessionId: pendingGameLoaded.sessionId,
        saveName: pendingGameLoaded.saveName
      });
      
      // Reset dello stato pending
      setPendingGameLoaded(null);
    }
  }, [socketReady, emit, pendingGameLoaded]);
  
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
      
      {/* Aggiungiamo pulsante di debug per pulire localStorage */}
      {debugButton}
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
