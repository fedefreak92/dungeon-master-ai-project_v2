import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import pixiManager from '../pixi/utils/pixiManager';
import { useGameState } from '../hooks/useGameState';
import socketService from '../api/socketService';
import '../styles/MapContainer.css';

/**
 * Componente React per il rendering della mappa di gioco
 * Utilizza pixiManager per gestire le risorse PIXI
 */
const MapContainer = ({ mapId }) => {
  const containerRef = useRef(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnected, setIsConnected] = useState(socketService.isConnected());
  const [error, setError] = useState(null);
  const [debugInfo, setDebugInfo] = useState({ logs: [], errors: [] });
  const { gameState, setGameState } = useGameState();
  
  // Identifica la scena usando l'ID mappa
  const sceneId = `map_scene_${mapId}`;
  
  // Definizione della costante MAX_RETRIES
  const MAX_RETRIES = 3;
  
  // Aggiungiamo un ref per tenere traccia se il componente è montato
  const isComponentMounted = useRef(true);
  
  // Funzione di debug per tracciare i passaggi
  const logDebug = useCallback((message, isError = false) => {
    console.log(`[MapContainer] ${message}`);
    
    setDebugInfo(prev => {
      const newDebugInfo = { ...prev };
      
      if (isError) {
        newDebugInfo.errors = [...prev.errors, message].slice(-10);
      } else {
        newDebugInfo.logs = [...prev.logs, message].slice(-20);
      }
      
      return newDebugInfo;
    });
  }, []);
  
  // Caricamento dei dati della mappa dal server
  const fetchMapData = useCallback(async (id) => {
    if (!id) {
      throw new Error('ID mappa non valido');
    }
    
    try {
      // Ottieni l'ID sessione dallo stato globale del gioco
      const sessionId = gameState?.sessionId;
      
      if (!sessionId) {
        throw new Error('Sessione di gioco non disponibile');
      }
      
      logDebug(`Caricamento dati mappa dal server: sessionId=${sessionId}, mapId=${id}`);
      
      // Utilizziamo il nuovo metodo emitWithAck per evitare l'errore del socket
      const mapData = await socketService.emitWithAck('get_map_data', {
        id_sessione: sessionId,
        id_mappa: id
      });
      
      logDebug(`Dati mappa caricati con successo: ${id}`);
      
      // Verifica che i dati contengano le proprietà necessarie
      if (!mapData.griglia || !mapData.larghezza || !mapData.altezza) {
        logDebug(`Dati mappa non validi: ${JSON.stringify(mapData || {})}`, true);
        throw new Error('Dati mappa non validi o incompleti');
      }
      
      return mapData;
    } catch (error) {
      logDebug(`Errore nel caricamento della mappa ${id}: ${error.message}`, true);
      throw error;
    }
  }, [gameState?.sessionId, logDebug]);
  
  // Verifica lo stato della connessione socket
  useEffect(() => {
    const checkConnection = () => {
      const connected = socketService.isConnected();
      if (connected !== isConnected && isComponentMounted.current) {
        setIsConnected(connected);
        logDebug(`Stato connessione cambiato: ${connected ? 'connesso' : 'disconnesso'}`);
      }
    };
    
    // Verifica subito e poi ogni secondo
    checkConnection();
    const interval = setInterval(checkConnection, 1000);
    
    // Funzione per tentare una connessione
    const attemptConnection = async () => {
      // Evita di connettersi se il componente è stato smontato
      if (!isComponentMounted.current) return;
      
      // Non tentare la connessione se è già in corso o già connesso
      if (socketService.isConnected()) {
        logDebug('Socket già connesso, salto tentativo di connessione');
        return;
      }
      
      try {
        logDebug('Tentativo di connessione socket...');
        
        await socketService.connect(gameState.sessionId);
        
        if (isComponentMounted.current) {
          logDebug('Socket connesso con successo');
          setIsConnected(true);
        }
      } catch (err) {
        if (isComponentMounted.current) {
          logDebug(`Errore connessione socket: ${err.message}`, true);
        }
      }
    };
    
    // Tenta di connettere il socket se non è già connesso e abbiamo un ID sessione
    if (!socketService.isConnected() && gameState?.sessionId) {
      // Aggiungiamo un leggero ritardo prima di tentare la connessione
      setTimeout(() => attemptConnection(), 500);
    }
    
    // Definiamo gli handler per gli eventi socket
    const handleConnect = () => {
      if (isComponentMounted.current) {
        setIsConnected(true);
        logDebug('Socket connesso');
      }
    };
    
    const handleDisconnect = () => {
      if (isComponentMounted.current) {
        setIsConnected(false);
        logDebug('Socket disconnesso', true);
      }
    };
    
    const handleError = (err) => {
      if (isComponentMounted.current) {
        logDebug(`Errore socket: ${err?.message || 'Errore sconosciuto'}`, true);
      }
    };
    
    const handleGameStateUpdate = (state) => {
      if (isComponentMounted.current) {
        setGameState(prevState => ({
          ...prevState,
          ...state
        }));
        logDebug('Aggiornamento stato gioco ricevuto');
      }
    };
    
    // Registra i listener solo se il socket è disponibile
    if (socketService.socket) {
      logDebug('Registrazione listener socket');
      socketService.on('connect', handleConnect);
      socketService.on('disconnect', handleDisconnect);
      socketService.on('error', handleError);
      socketService.on('game_state_update', handleGameStateUpdate);
    } else {
      logDebug('Socket non disponibile, i listener verranno registrati automaticamente alla connessione');
    }
    
    // Cleanup
    return () => {
      isComponentMounted.current = false;
      clearInterval(interval);
      
      // Rimuovi i listener solo se il socket esiste
      if (socketService.socket) {
        socketService.off('connect', handleConnect);
        socketService.off('disconnect', handleDisconnect);
        socketService.off('error', handleError);
        socketService.off('game_state_update', handleGameStateUpdate);
      }
    };
  }, [isConnected, logDebug, setGameState, gameState?.sessionId]);
  
  // Effetto per l'inizializzazione della scena Pixi.js
  useEffect(() => {
    if (!mapId || !isConnected) {
      if (!mapId) logDebug('ID mappa mancante, in attesa...', true);
      if (!isConnected) logDebug('Socket non connesso, in attesa...', true);
      return;
    }
    
    logDebug(`Inizializzazione scena per mappa ${mapId}`);
    setIsLoading(true);
    setError(null);
    
    let pixiApp = null;
    let retryCount = 0;
    
    const initializeScene = async () => {
      try {
        logDebug(`Inizializzazione scena ${sceneId} per mappa ${mapId}`);
        
        // Caricamento dati mappa
        logDebug('Caricamento dati mappa');
        const mapData = await fetchMapData(mapId).catch(err => {
          throw new Error(`Errore caricamento mappa: ${err.message}`);
        });
        
        // Verifica che ci siano dati validi
        if (!mapData) {
          throw new Error(`Impossibile caricare i dati per la mappa ${mapId}`);
        }
        
        // Crea una nuova scena PIXI tramite il manager
        logDebug(`Creazione scena PIXI per ${mapId}`);
        const scene = pixiManager.createScene(sceneId, containerRef.current);
        
        if (!scene) {
          throw new Error('Impossibile creare la scena Pixi.js');
        }
        
        // Renderizza la mappa nella scena
        logDebug(`Rendering mappa nella scena`);
        const success = pixiManager.renderMap(scene, mapData);
        
        if (!success) {
          throw new Error('Errore nel rendering della mappa');
        }
        
        // Aggiungi il giocatore se le coordinate sono disponibili
        if (gameState?.player_position) {
          const { x, y } = gameState.player_position;
          logDebug(`Aggiunta giocatore alla posizione (${x}, ${y})`);
          pixiManager.addPlayer(scene, x, y);
        } else {
          // Posizione predefinita al centro della mappa
          const centerX = Math.floor((mapData.larghezza || 10) / 2);
          const centerY = Math.floor((mapData.altezza || 10) / 2);
          logDebug(`Aggiunta giocatore alla posizione di default (${centerX}, ${centerY})`);
          pixiManager.addPlayer(scene, centerX, centerY);
        }
        
        pixiApp = scene;
        logDebug(`Inizializzazione scena completata con successo`);
        setIsLoading(false);
        setError(null);
        
        return scene;
      } catch (err) {
        logDebug(`Errore nell'inizializzazione della scena: ${err.message}`, true);
        
        if (retryCount < MAX_RETRIES) {
          retryCount++;
          logDebug(`Tentativo ${retryCount}/${MAX_RETRIES} di inizializzazione scena...`);
          setTimeout(initializeScene, 1000);
          return;
        }
        
        setError(err.message);
        setIsLoading(false);
        return null;
      }
    };
    
    // Avvia l'inizializzazione
    initializeScene();
    
    // Cleanup sicuro
    return () => {
      // Rimuovo la variabile non utilizzata
      
      // Verifica se l'app è stata creata prima di distruggerla
      if (pixiApp) {
        try {
          logDebug(`Pulizia scena ${sceneId}`);
          // Rimuovi tutti i filtri prima della distruzione
          if (pixiApp.stage && pixiApp.stage.filters) {
            pixiApp.stage.filters = null;
          }
          
          // Destroy sicuro con true per rimuovere anche le texture
          pixiApp.destroy(true, { children: true, texture: true, baseTexture: true });
        } catch (err) {
          logDebug(`Errore durante pulizia Pixi.js: ${err.message}`, true);
        }
      }
      
      // Pulisci la scena tramite il manager
      pixiManager.cleanupScene(sceneId);
    };
  }, [mapId, isConnected, gameState?.currentMap, fetchMapData, logDebug, sceneId, gameState?.player_position, setGameState]);
  
  // Aggiornamenti quando cambiano le coordinate del giocatore
  useEffect(() => {
    if (gameState?.player_position && !isLoading && isConnected) {
      const { x, y } = gameState.player_position;
      pixiManager.updatePlayerPosition(sceneId, x, y);
    }
  }, [gameState?.player_position, sceneId, isLoading, isConnected]);
  
  // Aggiornamenti quando cambiano le entità sulla mappa
  useEffect(() => {
    if (gameState?.entities && !isLoading && isConnected) {
      pixiManager.updateEntities(sceneId, gameState.entities);
    }
  }, [gameState?.entities, sceneId, isLoading, isConnected]);
  
  // Aggiungiamo un listener per l'evento map_change_complete
  useEffect(() => {
    const handleMapChangeComplete = (data) => {
      if (isComponentMounted.current) {
        logDebug(`Cambio mappa completato: ${JSON.stringify(data)}`);
        
        // Verifica che il socket sia connesso, altrimenti tenta una riconnessione
        if (!socketService.isConnected()) {
          logDebug('Socket non connesso durante cambio mappa, tentativo di riconnessione...');
          
          // Attendi un attimo per dare tempo al server di completare il cambio mappa
          setTimeout(() => {
            socketService.reconnect()
              .then(() => {
                if (isComponentMounted.current) {
                  logDebug('Riconnessione dopo cambio mappa riuscita');
                  setIsConnected(true);
                }
              })
              .catch(err => {
                if (isComponentMounted.current) {
                  logDebug(`Errore riconnessione dopo cambio mappa: ${err.message}`, true);
                }
              });
          }, 1000);
        }
        
        // Aggiorna lo stato del gioco con le nuove informazioni sulla mappa
        if (data.mapId && setGameState) {
          setGameState(prevState => ({
            ...prevState,
            currentMap: data.mapId,
            player_position: data.position
          }));
          logDebug(`Stato gioco aggiornato con nuova mappa: ${data.mapId}`);
        }
      }
    };
    
    // Registra il listener per l'evento map_change_complete
    socketService.on('map_change_complete', handleMapChangeComplete);
    
    // Cleanup
    return () => {
      isComponentMounted.current = false;
      socketService.off('map_change_complete', handleMapChangeComplete);
    };
  }, [logDebug, setGameState]);
  
  // Modifichiamo la parte di gestione della disconnessione per utilizzare il sistema di riconnessione
  useEffect(() => {
    const handleDisconnect = (reason) => {
      if (isComponentMounted.current) {
        setIsConnected(false);
        logDebug(`Socket disconnesso: ${reason}`, true);
        
        // Tenta una riconnessione rapida se è stata una disconnessione non voluta
        if (reason !== 'io client disconnect') {
          // Attendi un momento prima di tentare la riconnessione
          setTimeout(() => {
            if (!socketService.isConnected() && gameState?.sessionId && isComponentMounted.current) {
              logDebug('Tentativo di riconnessione automatica...');
              
              socketService.reconnect()
                .then(() => {
                  if (isComponentMounted.current) {
                    logDebug('Riconnessione rapida riuscita');
                    setIsConnected(true);
                  }
                })
                .catch(err => {
                  if (isComponentMounted.current) {
                    logDebug(`Errore nella riconnessione rapida: ${err.message}`, true);
                    
                    // Fallback alla connessione normale
                    logDebug('Tentativo di connessione standard...');
                    socketService.connect(gameState.sessionId)
                      .then(() => {
                        if (isComponentMounted.current) {
                          logDebug('Connessione standard riuscita');
                          setIsConnected(true);
                        }
                      })
                      .catch(innerErr => {
                        if (isComponentMounted.current) {
                          logDebug(`Anche la connessione standard è fallita: ${innerErr.message}`, true);
                        }
                      });
                  }
                });
            }
          }, 1500);
        }
      }
    };
    
    // Registra il listener per la disconnessione
    socketService.on('disconnect', handleDisconnect);
    
    // Cleanup
    return () => {
      isComponentMounted.current = false;
      socketService.off('disconnect', handleDisconnect);
    };
  }, [logDebug, setIsConnected, gameState?.sessionId]);
  
  // Aggiungiamo un useEffect per il cleanup del ref quando il componente viene smontato
  useEffect(() => {
    // Al montaggio il componente è attivo
    isComponentMounted.current = true;
    
    // Al cleanup impostiamo il flag a false
    return () => {
      isComponentMounted.current = false;
    };
  }, []);
  
  return (
    <div 
      ref={containerRef} 
      className="map-container" 
      style={{ 
        width: '100%', 
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
        backgroundColor: '#1a1a1a'
      }}
    >
      {isLoading && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <span>Caricamento mappa...</span>
        </div>
      )}
      
      {error && (
        <div className="error-overlay">
          <h3>Errore durante il caricamento della mappa</h3>
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>Riprova</button>
        </div>
      )}
      
      {/* Debug Panel - visibile solo in modalità sviluppo */}
      {process.env.NODE_ENV === 'development' && (
        <div className="debug-panel">
          <h4>Debug Info</h4>
          <div>
            <p>Map ID: {mapId}</p>
            <p>Connected: {isConnected ? 'Yes' : 'No'}</p>
            <p>Loading: {isLoading ? 'Yes' : 'No'}</p>
            <div className="debug-logs">
              <h5>Logs:</h5>
              <ul>
                {debugInfo.logs.map((log, idx) => (
                  <li key={idx}>{log}</li>
                ))}
              </ul>
            </div>
            {debugInfo.errors.length > 0 && (
              <div className="debug-errors">
                <h5>Errors:</h5>
                <ul>
                  {debugInfo.errors.map((err, idx) => (
                    <li key={idx}>{err}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default MapContainer; 