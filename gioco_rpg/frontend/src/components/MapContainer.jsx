import React, { useEffect, useRef, useState, useCallback, useLayoutEffect } from 'react';
import { pixiManager } from '../pixi';
import { useGame } from '../contexts/GameContext';
import { useGameState } from '../hooks/useGameState';
import { useSocket } from '../contexts/SocketContext';
import mapApi from '../api/mapApi';
import '../styles/MapContainer.css';

/**
 * Componente React per il rendering della mappa di gioco
 * Utilizza pixiManager con il nuovo GridMapRenderer
 */
const MapContainer = ({ mapId }) => {
  const containerRef = useRef(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [debugInfo, setDebugInfo] = useState({ logs: [], errors: [] });
  
  // Ottieni sessionId dal GameContext
  const { state: gameContextState } = useGame(); 
  const { sessionId, entities } = gameContextState;
  
  // Ottieni lo stato del giocatore da useGameState (aggiornato via WebSocket)
  const { gameState } = useGameState();
  const playerFromGameState = gameState.player;
  
  // Utilizziamo il contesto Socket invece del servizio diretto
  const { socketReady, connectionState, on, off, emitWithAck } = useSocket();
  
  // Identifica la scena usando l'ID mappa
  const sceneId = `map_scene_${mapId}`;
  
  // Definizione della costante MAX_RETRIES
  const MAX_RETRIES = 3;
  
  // Aggiungiamo un ref per tenere traccia se il componente è montato
  const isComponentMounted = useRef(true);
  
  // Ref per tenere traccia se il giocatore è già stato aggiunto
  const playerAddedRef = useRef(false);
  
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

  // Funzione per aggiornare le dimensioni del canvas
  const updateCanvasSize = useCallback(() => {
    if (!containerRef.current) return;
    
    const parentElement = containerRef.current.parentElement;
    if (!parentElement) return;
    
    // Calcola le dimensioni disponibili
    const containerWidth = parentElement.clientWidth;
    const containerHeight = parentElement.clientHeight;
    
    logDebug(`Dimensioni container: ${containerWidth}x${containerHeight}`);
    
    // Aggiorna i canvas presenti
    const canvases = containerRef.current.querySelectorAll('canvas');
    canvases.forEach(canvas => {
      canvas.style.width = '100%';
      canvas.style.height = '100%';
      canvas.style.display = 'block';
      
      // Se pixiManager ha un'app attiva, ridimensiona il renderer
      const scene = pixiManager.activeScenes.get(sceneId);
      if (scene && scene.renderer) {
        scene.renderer.resize(containerWidth, containerHeight);
        logDebug(`Renderer ridimensionato a: ${containerWidth}x${containerHeight}`);
      }
    });
  }, [sceneId, logDebug]);
  
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
      
      // Validazione e riparazione dei dati della mappa
      const validatedMapData = validateMapData(mapData);
      
      logDebug(`Dati mappa caricati con successo: ${id}`);
      
      return validatedMapData;
    } catch (error) {
      logDebug(`Errore nel caricamento della mappa ${id}: ${error.message}`, true);
      throw error; // Rilancia l'errore per la gestione in initializeScene
    }
  }, [sessionId, logDebug]);
  
  // Funzione di validazione e riparazione mappa
  const validateMapData = useCallback((mapData) => {
    if (!mapData) {
      logDebug("Dati mappa non validi: null o undefined", true);
      return null;
    }
    
    // Clone i dati per evitare modifiche ai dati originali
    const validatedData = JSON.parse(JSON.stringify(mapData));
    
    // Assicurati che le dimensioni della mappa siano valide
    validatedData.larghezza = validatedData.larghezza || 10;
    validatedData.altezza = validatedData.altezza || 10;
    const maxX = validatedData.larghezza - 1;
    const maxY = validatedData.altezza - 1;
    
    logDebug(`Validazione mappa: dimensioni ${validatedData.larghezza}x${validatedData.altezza}`);
    
    // Verifica che backgroundImage sia presente
    if (!validatedData.backgroundImage) {
      logDebug("backgroundImage mancante, impostazione valore predefinito", true);
      validatedData.backgroundImage = `assets/maps/${validatedData.nome || 'default'}_background.png`;
    }
    
    // Validazione della griglia
    if (!validatedData.griglia || !Array.isArray(validatedData.griglia)) {
      logDebug("Griglia mappa mancante o non valida, inizializzazione vuota", true);
      // Crea una griglia vuota come fallback
      validatedData.griglia = Array(validatedData.altezza).fill().map(() => Array(validatedData.larghezza).fill(0));
    } else {
      // Assicurati che la griglia abbia le dimensioni corrette
      if (validatedData.griglia.length > validatedData.altezza) {
        logDebug(`Troncamento righe griglia: ${validatedData.griglia.length} -> ${validatedData.altezza}`);
        validatedData.griglia = validatedData.griglia.slice(0, validatedData.altezza);
      }
      
      // Controlla e ripara ogni riga
      for (let y = 0; y < validatedData.griglia.length; y++) {
        const row = validatedData.griglia[y];
        if (!row || !Array.isArray(row)) {
          logDebug(`Riga ${y} non valida, creazione riga vuota`, true);
          validatedData.griglia[y] = Array(validatedData.larghezza).fill(0);
        } else if (row.length > validatedData.larghezza) {
          logDebug(`Troncamento colonne in riga ${y}: ${row.length} -> ${validatedData.larghezza}`);
          validatedData.griglia[y] = row.slice(0, validatedData.larghezza);
        } else if (row.length < validatedData.larghezza) {
          logDebug(`Espansione colonne in riga ${y}: ${row.length} -> ${validatedData.larghezza}`);
          // Riempi con tile vuoti fino alla larghezza richiesta
          validatedData.griglia[y] = [...row, ...Array(validatedData.larghezza - row.length).fill(0)];
        }
        
        // Assicurati che la griglia contenga solo 0 e 1 (0 = percorribile, 1 = ostacolo)
        validatedData.griglia[y] = validatedData.griglia[y].map(cellValue => 
          cellValue === 0 ? 0 : 1
        );
      }
      
      // Aggiungi righe mancanti se necessario
      if (validatedData.griglia.length < validatedData.altezza) {
        logDebug(`Aggiunta righe mancanti: ${validatedData.griglia.length} -> ${validatedData.altezza}`);
        for (let y = validatedData.griglia.length; y < validatedData.altezza; y++) {
          validatedData.griglia.push(Array(validatedData.larghezza).fill(0));
        }
      }
    }
    
    // Validazione degli oggetti
    if (validatedData.oggetti) {
      const validatedObjects = {};
      let removedObjectsCount = 0;
      
      Object.entries(validatedData.oggetti).forEach(([posizione, oggetto]) => {
        // Estrai le coordinate dalla stringa "[x, y]"
        const match = posizione.match(/\[(\d+),\s*(\d+)\]/);
        if (!match) {
          logDebug(`Oggetto con formato posizione non valido: ${posizione}`, true);
          removedObjectsCount++;
          return;
        }
        
        const x = parseInt(match[1], 10);
        const y = parseInt(match[2], 10);
        
        // Verifica che le coordinate siano valide
        if (x < 0 || x > maxX || y < 0 || y > maxY) {
          logDebug(`Oggetto fuori dai limiti: (${x}, ${y}), limiti: (0-${maxX}, 0-${maxY})`, true);
          removedObjectsCount++;
          return;
        }
        
        // Conserva l'oggetto valido
        validatedObjects[posizione] = oggetto;
        
        // Assicurati che l'oggetto abbia un nome
        if (!oggetto.nome) {
          oggetto.nome = `Oggetto ${x},${y}`;
          logDebug(`Oggetto senza nome a ${posizione}, assegnato nome: ${oggetto.nome}`);
        }
        
        // Assicurati che l'oggetto abbia un tipo
        if (!oggetto.tipo) {
          oggetto.tipo = 'oggetto_generico';
          logDebug(`Oggetto senza tipo a ${posizione}, assegnato tipo: ${oggetto.tipo}`);
        }
      });
      
      if (removedObjectsCount > 0) {
        logDebug(`Rimossi ${removedObjectsCount} oggetti fuori dai limiti della mappa`);
      }
      
      validatedData.oggetti = validatedObjects;
    }
    
    // Validazione degli NPC
    if (validatedData.npg) {
      const validatedNpcs = {};
      let removedNpcsCount = 0;
      
      Object.entries(validatedData.npg).forEach(([posizione, npc]) => {
        // Estrai le coordinate dalla stringa "[x, y]"
        const match = posizione.match(/\[(\d+),\s*(\d+)\]/);
        if (!match) {
          logDebug(`NPC con formato posizione non valido: ${posizione}`, true);
          removedNpcsCount++;
          return;
        }
        
        const x = parseInt(match[1], 10);
        const y = parseInt(match[2], 10);
        
        // Verifica che le coordinate siano valide
        if (x < 0 || x > maxX || y < 0 || y > maxY) {
          logDebug(`NPC fuori dai limiti: (${x}, ${y}), limiti: (0-${maxX}, 0-${maxY})`, true);
          removedNpcsCount++;
          return;
        }
        
        // Conserva l'NPC valido
        validatedNpcs[posizione] = npc;
        
        // Assicurati che l'NPC abbia un nome
        if (!npc.nome) {
          npc.nome = `NPC ${x},${y}`;
          logDebug(`NPC senza nome a ${posizione}, assegnato nome: ${npc.nome}`);
        }
      });
      
      if (removedNpcsCount > 0) {
        logDebug(`Rimossi ${removedNpcsCount} NPC fuori dai limiti della mappa`);
      }
      
      validatedData.npg = validatedNpcs;
    }
    
    return validatedData;
  }, [logDebug]);
  
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
    
    // Assicuriamoci che il container abbia le dimensioni corrette prima dell'inizializzazione
    const ensureContainerSize = () => {
      if (!containerRef.current) return false;
      
      const parentElement = containerRef.current.parentElement;
      if (!parentElement) return false;
      
      // Forza un'altezza minima se necessario
      if (parentElement.clientHeight <= 10) {
        parentElement.style.height = '500px';
        logDebug(`Altezza container forzata a 500px (era ${parentElement.clientHeight}px)`);
      }
      
      return parentElement.clientHeight > 10;
    };
    
    const initializeScene = async () => {
      try {
        logDebug(`Inizializzazione scena ${sceneId} per mappa ${mapId}`);

        if (!containerRef.current) {
          throw new Error('Il riferimento al container DOM non è più disponibile.');
        }

        // Assicuriamoci che il container abbia un'altezza valida
        if (!ensureContainerSize()) {
          throw new Error('Container con dimensioni invalide. Altezza insufficiente.');
        }

        // Calcola le dimensioni corrette
        const parentElement = containerRef.current.parentElement;
        const width = parentElement ? parentElement.clientWidth : window.innerWidth;
        const height = parentElement ? parentElement.clientHeight : window.innerHeight - 60;
        
        // Verifica che le dimensioni siano valide
        if (width <= 0 || height <= 0) {
          throw new Error(`Dimensioni non valide: ${width}x${height}. Utilizzo fallback.`);
        }

        logDebug(`Creazione scena PIXI nel container con dimensioni ${width}x${height}`);
        
        // Assicura che pixiManager non abbia già una scena con questo ID
        if (pixiManager.activeScenes.has(sceneId)) {
          logDebug(`Scena ${sceneId} già esistente, pulizia prima della ricreazione`);
          pixiManager.cleanupScene(sceneId);
        }
        
        const scene = pixiManager.createScene(containerRef.current, {
          sceneId: sceneId,
          width: Math.max(width, 100),
          height: Math.max(height, 100), // Usa almeno 100px come fallback
          backgroundColor: 0x1a1a1a,
          antialias: true, // Migliora la qualità del rendering
          resolution: window.devicePixelRatio || 1 // Supporto per display ad alta densità
        });

        if (!scene) {
          throw new Error('Impossibile creare la scena Pixi.js');
        }
        pixiApp = scene;
        
        // Assicurati che sceneId sia impostato correttamente sull'oggetto pixiApp
        pixiApp.name = sceneId;
        pixiApp._pixiManagerSceneId = sceneId;
        
        logDebug(`Scena PIXI (App) creata con successo per ${mapId}. ID: ${sceneId}`);

        // Assicuriamoci che il renderer sia posizionato correttamente
        if (pixiApp.view) {
          pixiApp.view.style.position = 'absolute';
          pixiApp.view.style.left = '0';
          pixiApp.view.style.top = '0';
          pixiApp.view.style.width = '100%';
          pixiApp.view.style.height = '100%';
          
          // Verifica le dimensioni reali del canvas
          logDebug(`Canvas creato con dimensioni ${pixiApp.view.width}x${pixiApp.view.height}`);
        }

        // Carica i dati della mappa
        const mapData = await fetchMapData(mapId);
        if (!mapData) {
          throw new Error(`Dati mappa non ricevuti per ${mapId}`);
        }
        logDebug('Dati mappa caricati.');

        // Renderizza la mappa usando il nuovo sistema GridMapRenderer
        logDebug(`Rendering mappa usando GridMapRenderer...`);
        const success = pixiManager.renderMap(pixiApp, mapData);

        if (!success) {
          throw new Error('Errore restituito da pixiManager.renderMap');
        }
        logDebug(`Mappa renderizzata con successo`);

        // Aggiungiamo il giocatore dopo che la mappa è stata renderizzata
        if (playerFromGameState) {
          const { x, y } = playerFromGameState;
          logDebug(`Aggiunta giocatore alla posizione (${x}, ${y})`);
          pixiManager.addPlayer(pixiApp, x, y);
          playerAddedRef.current = true;
        } else {
          const centerX = Math.floor((mapData.larghezza || 10) / 2);
          const centerY = Math.floor((mapData.altezza || 10) / 2);
          logDebug(`Aggiunta giocatore alla posizione di default (${centerX}, ${centerY})`);
          pixiManager.addPlayer(pixiApp, centerX, centerY);
        }

        // Aggiorna le dimensioni del canvas dopo il rendering completo
        updateCanvasSize();

        logDebug(`Inizializzazione scena ${sceneId} completata con successo`);
        setIsLoading(false);
        setError(null);

      } catch (err) {
        logDebug(`Errore nell'inizializzazione scena per ${sceneId}: ${err.message}`, true);
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
      }
    };
    
    // Ritarda l'inizializzazione per assicurarsi che il DOM sia completamente renderizzato
    setTimeout(initializeScene, 50);
    
    return () => {
      logDebug(`Cleanup per MapContainer (useLayoutEffect) - mapId: ${mapId}, sceneId: ${sceneId}`);
      // Marchiamo il componente come smontato per prevenire ulteriori aggiornamenti
      isComponentMounted.current = false;
      
      // Pianifica il cleanup del PixiManager dopo un piccolo ritardo
      setTimeout(() => {
        if (pixiManager.activeScenes.has(sceneId)) {
          logDebug(`Esecuzione cleanup scena ${sceneId}`);
          pixiManager.cleanupScene(sceneId);
        }
      }, 50); // Un piccolo ritardo per essere sicuri che React abbia finito
    };
  }, [mapId, socketReady, fetchMapData, logDebug, sceneId, playerFromGameState, sessionId, containerRef, updateCanvasSize]);
  
  // USEEFFECT SPECIFICO per aggiornare la posizione del giocatore quando cambia lo stato
  useEffect(() => {
    // Solo se il giocatore è già stato aggiunto e abbiamo dati validi
    if (playerAddedRef.current && playerFromGameState && playerFromGameState.x !== undefined && playerFromGameState.y !== undefined && !isLoading) {
      const { x, y } = playerFromGameState;
      logDebug(`[MOVEMENT UPDATE] Aggiornamento posizione giocatore da useGameState: (${x}, ${y})`);
      
      // Aggiorna la posizione sulla mappa PIXI
      pixiManager.updatePlayerPosition(sceneId, x, y);
    }
  }, [playerFromGameState?.x, playerFromGameState?.y, sceneId, isLoading, logDebug]);
  
  // Aggiornamenti quando cambiano le entità sulla mappa
  useEffect(() => {
    if (entities && !isLoading && socketReady) {
      logDebug(`Aggiornamento entità sulla mappa: ${entities.length} entità`);
      
      // Delega completamente la gestione dei retry al PixiManager
      // che ha ora un sistema interno più robusto
      pixiManager.updateEntities(sceneId, entities);
    }
  }, [entities, sceneId, isLoading, socketReady, logDebug]);
  
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
  
  // Aggiungiamo un listener per il ridimensionamento della finestra
  useEffect(() => {
    const handleResize = () => {
      updateCanvasSize();
    };
    
    window.addEventListener('resize', handleResize);
    
    // Assicurati che il canvas abbia le dimensioni corrette all'inizio
    updateCanvasSize();
    
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [updateCanvasSize]);
  
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
      style={{ minHeight: '500px' }} // Forza un'altezza minima
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