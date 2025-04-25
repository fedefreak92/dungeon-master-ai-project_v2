import React, { useEffect, useRef, useState, useCallback } from 'react';
import pixiManager from '../pixi/utils/pixiManager';
import { useGameState } from '../hooks/useGameState';
import { useSocket } from '../contexts/SocketContext';
import '../styles/MapContainer.css';

/**
 * Componente React per il rendering della mappa di gioco
 * Utilizza pixiManager per gestire le risorse PIXI
 */
const MapContainer = ({ mapId }) => {
  const containerRef = useRef(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [debugInfo, setDebugInfo] = useState({ logs: [], errors: [] });
  const { gameState, setGameState } = useGameState();
  
  // Utilizziamo il contesto Socket invece del servizio diretto
  const { socketReady, connectionState, on, off, emitWithAck } = useSocket();
  
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
      
      // Utilizziamo il emitWithAck dal contesto del socket
      const mapData = await emitWithAck('get_map_data', {
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
  }, [gameState?.sessionId, logDebug, emitWithAck]);
  
  // Inizializzazione della scena Pixi.js
  useEffect(() => {
    if (!mapId || !socketReady) {
      if (!mapId) logDebug('ID mappa mancante, in attesa...', true);
      if (!socketReady) logDebug('Socket non pronto, in attesa...', true);
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
  }, [mapId, socketReady, fetchMapData, logDebug, sceneId, gameState?.player_position, gameState?.sessionId]);
  
  // Aggiornamenti quando cambiano le coordinate del giocatore
  useEffect(() => {
    if (gameState?.player_position && !isLoading && socketReady) {
      const { x, y } = gameState.player_position;
      pixiManager.updatePlayerPosition(sceneId, x, y);
    }
  }, [gameState?.player_position, sceneId, isLoading, socketReady]);
  
  // Aggiornamenti quando cambiano le entità sulla mappa
  useEffect(() => {
    if (gameState?.entities && !isLoading && socketReady) {
      pixiManager.updateEntities(sceneId, gameState.entities);
    }
  }, [gameState?.entities, sceneId, isLoading, socketReady]);
  
  // Aggiungiamo un listener per l'evento map_change_complete
  useEffect(() => {
    if (!socketReady) {
      logDebug('Socket non pronto, listener map_change_complete non registrato', true);
      return;
    }
    
    const handleMapChangeComplete = (data) => {
      if (isComponentMounted.current) {
        logDebug(`Cambio mappa completato: ${JSON.stringify(data)}`);
        
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
    logDebug('Registrazione listener map_change_complete');
    on('map_change_complete', handleMapChangeComplete);
    
    // Cleanup
    return () => {
      logDebug('Pulizia listener map_change_complete');
      off('map_change_complete', handleMapChangeComplete);
    };
  }, [socketReady, logDebug, setGameState, on, off]);
  
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
            <p>Socket Ready: {socketReady ? 'Yes' : 'No'}</p>
            <p>Loading: {isLoading ? 'Yes' : 'No'}</p>
            {connectionState && (
              <p>Connection: {connectionState.connected ? 'Connected' : connectionState.connecting ? 'Connecting' : 'Disconnected'}</p>
            )}
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