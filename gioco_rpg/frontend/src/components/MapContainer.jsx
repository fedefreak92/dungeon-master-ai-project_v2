import React, { useEffect, useRef, useState, useCallback, useLayoutEffect } from 'react';
import pixiManager from '../pixi/utils/pixiManager';
import { useGame } from '../contexts/GameContext';
import { useSocket } from '../contexts/SocketContext';
import mapApi from '../api/mapApi';
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
  
  // Ottieni sessionId e gameState da useGame
  const { state: gameContextState } = useGame(); 
  const { sessionId, player_position, entities } = gameContextState; // Estrai sessionId da qui
  
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
      // Usa sessionId dal context useGame
      if (!sessionId) { 
        throw new Error('Sessione di gioco non disponibile');
      }
      
      logDebug(`Caricamento dati mappa dal server: sessionId=${sessionId}, mapId=${id}`);
      
      // Usa la chiamata API REST mapApi.getMapData invece di emitWithAck
      const mapData = await mapApi.getMapData(sessionId, id); 
      
      // Valida e ripara i dati della mappa (opzionale ma consigliato)
      const validatedMapData = mapApi.validateAndFixMapData(mapData);
      if (!validatedMapData) {
        throw new Error('Dati mappa non validi dopo la validazione');
      }
      
      logDebug(`Dati mappa caricati con successo: ${id}`);
      
      // Verifica che i dati contengano le proprietà necessarie (già fatto in validateAndFix)
      // if (!validatedMapData.griglia || !validatedMapData.larghezza || !validatedMapData.altezza) {
      //   logDebug(`Dati mappa non validi: ${JSON.stringify(validatedMapData || {})}`, true);
      //   throw new Error('Dati mappa non validi o incompleti');
      // }
      
      return validatedMapData;
    } catch (error) {
      logDebug(`Errore nel caricamento della mappa ${id}: ${error.message}`, true);
      throw error; // Rilancia l'errore per la gestione in initializeScene
    }
    // Aggiorna dipendenza: usa sessionId da useGame
  }, [sessionId, logDebug]);
  
  // Inizializzazione della scena Pixi.js con useLayoutEffect
  useLayoutEffect(() => {
    if (!mapId || !socketReady || !containerRef.current) {
      if (!mapId) logDebug('ID mappa mancante, in attesa...', true);
      if (!socketReady) logDebug('Socket non pronto, in attesa...', true);
      if (!containerRef.current) logDebug('Ref del container non ancora disponibile (useLayoutEffect)', true);
      return;
    }
    
    logDebug(`Layout pronto per mappa ${mapId}. Inizializzazione scena (useLayoutEffect)...`);
    setIsLoading(true);
    setError(null);
    
    let pixiApp = null;
    let retryCount = 0;
    
    const initializeScene = async () => {
      let scene = null;
      try {
        logDebug(`Inizializzazione scena ${sceneId} per mappa ${mapId}`);

        if (!containerRef.current) {
          throw new Error('Il riferimento al container DOM non è più disponibile.');
        }

        logDebug(`Creazione scena PIXI nel container:`, containerRef.current);
        scene = pixiManager.createScene(containerRef.current, {
          sceneId: sceneId,
          width: containerRef.current.clientWidth || 800,
          height: containerRef.current.clientHeight || 600
        });

        if (!scene) {
          logDebug(`pixiManager.createScene ha restituito null. Container passato:`, containerRef.current, true);
          throw new Error('Impossibile creare la scena Pixi.js (pixiManager.createScene ha restituito null)');
        }
        pixiApp = scene;
        logDebug(`Scena PIXI (App) creata con successo per ${mapId}. ID: ${sceneId}`);

        const mapData = await fetchMapData(mapId);

        if (!mapData) {
          throw new Error(`Dati mappa non ricevuti per ${mapId}`);
        }
        logDebug('Dati mappa caricati.');

        logDebug(`Rendering mappa nella scena...`);
        const success = pixiManager.renderMap(pixiApp, mapData);

        if (!success) {
          throw new Error('Errore restituito da pixiManager.renderMap');
        }
        logDebug(`Mappa renderizzata con successo`);

        if (player_position) {
          const { x, y } = player_position;
          logDebug(`Aggiunta giocatore alla posizione (${x}, ${y})`);
          pixiManager.addPlayer(pixiApp, x, y);
        } else {
          const centerX = Math.floor((mapData.larghezza || 10) / 2);
          const centerY = Math.floor((mapData.altezza || 10) / 2);
          logDebug(`Aggiunta giocatore alla posizione di default (${centerX}, ${centerY})`);
          pixiManager.addPlayer(pixiApp, centerX, centerY);
        }

        logDebug(`Inizializzazione scena ${sceneId} completata con successo`);
        setIsLoading(false);
        setError(null);

      } catch (err) {
        logDebug(`Errore DENTRO initializeScene per ${sceneId}: ${err.message}`, true);
        console.error(err.stack);

        if (retryCount < MAX_RETRIES) {
          retryCount++;
          logDebug(`Tentativo ${retryCount}/${MAX_RETRIES} di inizializzazione scena ${sceneId} tra 1 secondo...`);
          if (isComponentMounted.current) {
              setTimeout(initializeScene, 1000);
          } else {
               logDebug(`Componente smontato, annullo retry per ${sceneId}.`);
          }
          return;
        }

        const finalErrorMessage = `Inizializzazione scena ${sceneId} fallita dopo ${MAX_RETRIES + 1} tentativi: ${err.message}`;
        logDebug(finalErrorMessage, true);
        setError(finalErrorMessage);
        setIsLoading(false);

        return;
      }
    };
    
    initializeScene();
    
    return () => {
      logDebug(`Cleanup per MapContainer (useLayoutEffect) - mapId: ${mapId}, sceneId: ${sceneId}`);
      // Scheduliamo la pulizia completa di Pixi per eseguirla dopo il ciclo di commit di React,
      // dando a React il tempo di rimuovere il container dal DOM prima che Pixi distrugga il canvas.
      setTimeout(() => {
          logDebug(`Esecuzione cleanup Pixi posticipata per ${sceneId}`);
          pixiManager.cleanupScene(sceneId); // Pixi gestisce la sua distruzione completa
      }, 0);
      logDebug(`Cleanup React per ${sceneId} completato, cleanup Pixi schedulato.`);
    };
  }, [mapId, socketReady, fetchMapData, logDebug, sceneId, player_position, sessionId, containerRef]);
  
  // Aggiornamenti quando cambiano le coordinate del giocatore
  useEffect(() => {
    if (player_position && !isLoading && socketReady) {
      const { x, y } = player_position;
      pixiManager.updatePlayerPosition(sceneId, x, y);
    }
  }, [player_position, sceneId, isLoading, socketReady]);
  
  // Aggiornamenti quando cambiano le entità sulla mappa
  useEffect(() => {
    if (entities && !isLoading && socketReady) {
      pixiManager.updateEntities(sceneId, entities);
    }
  }, [entities, sceneId, isLoading, socketReady]);
  
  // Aggiungiamo un listener per l'evento map_change_complete
  useEffect(() => {
    if (!socketReady) {
      logDebug('Socket non pronto, listener map_change_complete non registrato', true);
      return;
    }
    
    const handleMapChangeComplete = (data) => {
      if (isComponentMounted.current) {
        logDebug(`Cambio mappa completato: ${JSON.stringify(data)}`);
      }
    };
    
    logDebug('Registrazione listener map_change_complete');
    on('map_change_complete', handleMapChangeComplete);
    
    return () => {
      logDebug('Pulizia listener map_change_complete');
      off('map_change_complete', handleMapChangeComplete);
    };
  }, [socketReady, logDebug, on, off]);
  
  // Aggiungiamo un useEffect per il cleanup del ref quando il componente viene smontato
  useEffect(() => {
    isComponentMounted.current = true;
    
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