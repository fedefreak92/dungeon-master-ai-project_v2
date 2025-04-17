import React, { useRef, useEffect, useState, useCallback } from 'react';
import * as PIXI from 'pixi.js';
import { useGame } from '../../contexts/GameContext';
import usePixiApp from '../../hooks/usePixiApp';
import useSocket from '../../hooks/useSocket';
import useKeyboard from '../../hooks/useKeyboard';
import AssetLoader from '../../pixi/utils/AssetLoader';
import MapRenderer from '../../pixi/utils/MapRenderer';
import mapApi from '../../api/mapApi';
import '../../styles/MapRenderer.css';

// Versione degli asset per evitare problemi di cache
const ASSET_VERSION = Date.now();

/**
 * Componente per la schermata della mappa di gioco
 * Gestisce il rendering e l'interazione con la mappa
 */
const GameMapScreen = () => {
  const { state } = useGame();
  const { sessionId, currentMap } = state;
  
  // Riferimento al container per il canvas
  const containerRef = useRef(null);
  
  // Hook personalizzati
  const { app, viewport } = usePixiApp(containerRef, {
    useViewport: true,
    backgroundColor: 0x1a1a1a,
    worldWidth: 3000,
    worldHeight: 3000
  });
  
  const { socket, connected, emit } = useSocket(sessionId);
  const keyboard = useKeyboard();
  
  // Stato locale
  const [mapData, setMapData] = useState(null);
  const [entities, setEntities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTile, setSelectedTile] = useState(null);
  const [tileHighlight, setTileHighlight] = useState(null);
  
  // Riferimenti per gli oggetti pixi
  const entitiesLayerRef = useRef(null);
  const texturesRef = useRef({
    tiles: null,
    entities: null
  });
  const spritesRef = useRef({});
  
  // Dichiarazione anticipata per risolvere dipendenze circolari
  const handleEntityClickRef = useRef(null);
  
  // Prima dell'useEffect per il caricamento della mappa, aggiungo un nuovo useEffect per verificare la disponibilità del server
  useEffect(() => {
    async function checkAssets() {
      try {
        setLoading(true);
        console.log("Controllo disponibilità server e asset...");
        
        // Inizializza il sistema di gestione errori di PIXI
        PIXI.utils.skipHello();
        
        // Sovrascrivi il metodo di gestione errori di PIXI per prevenire crash
        const originalOnError = window.onerror;
        window.onerror = function(message, source, lineno, colno, error) {
          // Filtra gli errori specifici di PIXI che non devono bloccare l'esecuzione
          if (source && source.includes('pixi.js') && message.includes('Cannot read properties')) {
            console.warn('Errore nel caricamento di una texture: ', { message, source, lineno, colno });
            return true; // previene il crash dell'app
          }
          return originalOnError ? originalOnError(message, source, lineno, colno, error) : false;
        };
        
        // Verifica la disponibilità del server
        const serverAvailable = await AssetLoader.checkServerAvailability();
        
        if (!serverAvailable) {
          console.warn("Server non disponibile, modalità offline attiva");
          setError("Server non disponibile, utilizzo asset locali (modalità offline)");
        }
        
        // Anche se il server non è disponibile, procediamo con gli asset di fallback
        // Precarica le texture più comuni per migliorare l'esperienza utente
        console.log("Precaricamento texture di base...");
        await AssetLoader.loadMapTextures(); // Precarica textures dei tiles
        await AssetLoader.preloadEntityTextures(); // Precarica textures delle entità
        
        setLoading(false);
        console.log("Precaricamento completato");
      } catch (err) {
        console.error("Errore durante il controllo degli asset:", err);
        setError("Errore durante il caricamento degli asset: " + (err.message || "Errore sconosciuto"));
        setLoading(false);
      }
    }
    
    // Inizializza il gestore globale di promesse non gestite
    const unhandledRejectionHandler = (event) => {
      // Previeni la visualizzazione dell'errore nella console
      event.preventDefault();
      
      // Registra l'errore in modo controllato
      console.warn('Promise non gestita intercettata:', event.reason);
      
      // Se l'errore riguarda il caricamento delle texture, non propagarlo
      if (event.reason && 
          (event.reason.message?.includes('texture') || 
           event.reason.message?.includes('image') || 
           event.reason.message?.includes('resource'))) {
        console.log("Errore di caricamento texture gestito silenziosamente");
      }
    };
    
    window.addEventListener('unhandledrejection', unhandledRejectionHandler);
    
    checkAssets();
    
    // Pulizia al dismount
    return () => {
      window.removeEventListener('unhandledrejection', unhandledRejectionHandler);
    };
  }, []);
  
  // Carica i dati della mappa quando cambia la mappa corrente
  useEffect(() => {
    async function fetchMapData() {
      if (!sessionId || !currentMap) return;
      
      try {
        setLoading(true);
        setError(null);
        
        // Carica i dati della mappa
        const data = await mapApi.getMapData(sessionId, currentMap);
        setMapData(data);
        
        setLoading(false);
      } catch (err) {
        console.error('Errore nel caricamento dei dati della mappa:', err);
        setError('Impossibile caricare la mappa: ' + (err.message || 'Errore sconosciuto'));
        setLoading(false);
      }
    }
    
    fetchMapData();
  }, [sessionId, currentMap]);
  
  // Configura il listener per l'aggiornamento delle entità
  useEffect(() => {
    if (!socket || !connected) return;
    
    // Richiedi i dati iniziali delle entità
    emit('request_entities', { id_sessione: sessionId });
    
    // Configura il listener per gli aggiornamenti delle entità
    const handleEntitiesUpdate = (data) => {
      if (data && data.entities) {
        setEntities(data.entities);
      }
    };
    
    // Registra i listener
    socket.on('entities_update', handleEntitiesUpdate);
    
    // Pulizia
    return () => {
      socket.off('entities_update', handleEntitiesUpdate);
    };
  }, [socket, connected, sessionId, emit]);
  
  // Aggiungere questa funzione prima dell'useEffect di rendering della mappa
  const cleanupAndRetry = useCallback(async () => {
    console.log("Pulizia e tentativo di ripristino...");
    
    try {
      // Imposta lo stato di caricamento
      setLoading(true);
      setError(null);
      
      // Pulisci la cache delle texture
      await AssetLoader.clearCache(true);
      
      // Se c'è un viewport, rimuovi tutti i figli
      if (viewport) {
        while (viewport.children.length > 0) {
          viewport.removeChildAt(0);
        }
      }
      
      // Se c'è un'app PIXI, pulisci i contenuti
      if (app && app.stage) {
        while (app.stage.children.length > 0) {
          app.stage.removeChildAt(0);
        }
      }
      
      // Reset dei riferimenti
      entitiesLayerRef.current = null;
      spritesRef.current = {};
      texturesRef.current = {
        tiles: null,
        entities: null
      };
      
      // Ricaricare le texture
      console.log("Ricaricamento texture dopo pulizia...");
      await AssetLoader.loadMapTextures();
      await AssetLoader.loadEntityTextures();
      
      setLoading(false);
      return true;
    } catch (err) {
      console.error("Errore durante il tentativo di ripristino:", err);
      setError("Impossibile recuperare dopo errore: " + (err.message || "Errore sconosciuto"));
      setLoading(false);
      return false;
    }
  }, [viewport, app]);
  
  // Modifica l'hook che gestisce gli errori di caricamento delle texture
  useEffect(() => {
    const handleTextureError = (event) => {
      // Questo evento si attiva quando una texture non può essere caricata
      console.error("Errore nel caricamento di una texture:", event);
      
      // Se c'è già un errore in corso, non far nulla
      if (error || loading) return;
      
      // Tentativo di recupero automatico
      cleanupAndRetry().then(success => {
        if (!success) {
          setError("Errore nel caricamento delle texture. Prova a ricaricare la pagina.");
        }
      });
    };
    
    // Aggiungi listener globale per gli errori di caricamento texture
    window.addEventListener('error', handleTextureError, { capture: true });
    
    return () => {
      // Rimuovi il listener quando il componente viene smontato
      window.removeEventListener('error', handleTextureError, { capture: true });
    };
  }, [error, loading, cleanupAndRetry]);
  
  // Modifica l'useEffect di smontaggio del componente
  useEffect(() => {
    // Al momento dello smontaggio, pulisci le risorse
    return () => {
      console.log("Smontaggio componente GameMapScreen, pulizia risorse...");
      
      // Pulisci la cache delle texture quando il componente viene smontato
      AssetLoader.clearCache(true);
      
      // Pulisci i riferimenti
      entitiesLayerRef.current = null;
      spritesRef.current = {};
      texturesRef.current = {
        tiles: null,
        entities: null
      };
    };
  }, []);
  
  // Funzioni per il rendering della mappa
  const loadTextures = useCallback(async () => {
    try {
      // Carica le texture per i tile della mappa
      const tileTextures = await AssetLoader.loadMapTextures(`?v=${ASSET_VERSION}`);
      texturesRef.current.tiles = tileTextures;
      
      // Carica le texture per le entità
      const entityTextures = await AssetLoader.loadEntityTextures(`?v=${ASSET_VERSION}`);
      texturesRef.current.entities = entityTextures;
      
      return true;
    } catch (err) {
      console.error('Errore nel caricamento delle texture:', err);
      setError('Errore nel caricamento delle texture: ' + (err.message || 'Errore sconosciuto'));
      return false;
    }
  }, []);
  
  const setupLayers = useCallback(() => {
    if (!app || !viewport || !mapData) return false;
    
    // Pulisci il viewport se necessario
    while (viewport.children.length > 0) {
      viewport.removeChildAt(0);
    }
    
    // Crea il container per le entità
    const entitiesLayer = new PIXI.Container();
    entitiesLayer.name = 'entities';
    viewport.addChild(entitiesLayer);
    entitiesLayerRef.current = entitiesLayer;
    
    return true;
  }, [app, viewport, mapData]);
  
  const renderMapLayers = useCallback(() => {
    if (!app || !viewport || !mapData || !texturesRef.current.tiles) return false;
    
    try {
      // Usa MapRenderer per renderizzare gli strati della mappa
      MapRenderer.renderMapLayers(
        viewport,
        mapData,
        texturesRef.current.tiles
      );
      
      return true;
    } catch (err) {
      console.error('Errore nel rendering degli strati della mappa:', err);
      setError('Errore nel rendering della mappa: ' + (err.message || 'Errore sconosciuto'));
      return false;
    }
  }, [app, viewport, mapData]);
  
  // Funzione per aggiornare le entità sulla mappa
  const updateEntities = useCallback(() => {
    if (!entitiesLayerRef.current || !texturesRef.current || !texturesRef.current.entities) return;
    
    const entitiesLayer = entitiesLayerRef.current;
    
    // Rimuovi tutti gli sprite delle entità esistenti
    while (entitiesLayer.children.length > 0) {
      entitiesLayer.removeChildAt(0);
    }
    
    // Pulisci il riferimento agli sprite
    spritesRef.current = {};
    
    // Itera sulle entità e crea sprite per ciascuna
    entities.forEach(entity => {
      // Salta entità senza posizione
      if (entity.x === undefined || entity.y === undefined) return;
      
      try {
        // Determina il tipo di entità
        const entityType = entity.is_player ? 'player' : (entity.type || 'npc');
        
        // Crea lo sprite dell'entità
        const sprite = MapRenderer.createEntitySprite(
          entityType,
          entity,
          texturesRef.current.entities
        );
        
        // Configura l'interazione con lo sprite
        sprite.on('pointerdown', () => {
          if (handleEntityClickRef.current) {
            handleEntityClickRef.current(entity);
          }
        });
        
        // Memorizza lo sprite nel riferimento
        spritesRef.current[entity.id] = sprite;
        
        // Aggiungi lo sprite al layer delle entità
        entitiesLayer.addChild(sprite);
        
        // Aggiungi un'etichetta con il nome dell'entità
        if (entity.name) {
          const tileSize = MapRenderer.TILE_SIZE || 32;
          const label = MapRenderer.createEntityLabel(
            entity.name,
            (entity.x + 0.5) * tileSize,
            entity.y * tileSize
          );
          entitiesLayer.addChild(label);
        }
      } catch (error) {
        console.warn(`Errore nel rendering dell'entità ${entity.id}:`, error);
      }
    });
  }, [entities]);
  
  // Funzione per configurare l'interazione con il viewport
  const setupViewportInteraction = useCallback(() => {
    if (!viewport) return;
    
    try {
      // Configura le opzioni del viewport
      viewport.drag();
      viewport.pinch();
      viewport.wheel();
      viewport.decelerate();
      
      // Limita il viewport alla dimensione della mappa
      if (mapData) {
        const tileSize = MapRenderer.TILE_SIZE || 32;
        const worldWidth = mapData.width * tileSize;
        const worldHeight = mapData.height * tileSize;
        
        try {
          viewport.resize(
            containerRef.current?.clientWidth || window.innerWidth,
            containerRef.current?.clientHeight || window.innerHeight,
            worldWidth,
            worldHeight
          );
          
          // Verifica che il viewport e il suo parent siano validi prima di chiamare clampZoom
          if (viewport && viewport.parent && viewport.scale) {
            viewport.clampZoom({
              minScale: 0.1,
              maxScale: 5
            });
          }
        } catch (resizeError) {
          console.warn('Errore durante il resize del viewport:', resizeError);
          // Fallback con valori di default
          if (viewport && viewport.parent) {
            viewport.resize(
              window.innerWidth, 
              window.innerHeight,
              worldWidth, 
              worldHeight
            );
          }
        }
      }
      
      return true;
    } catch (err) {
      console.error('Errore nella configurazione del viewport:', err);
      return false;
    }
  }, [viewport, mapData]);
  
  // Funzione per centrare la vista sul giocatore
  const centerOnPlayer = useCallback(() => {
    if (!viewport || !entities || !mapData) return;
    
    // Trova l'entità del giocatore
    const player = entities.find(entity => entity.is_player);
    
    // Se troviamo il giocatore, centra la vista su di lui
    if (player && player.x !== undefined && player.y !== undefined) {
      const tileSize = MapRenderer.TILE_SIZE || 32;
      MapRenderer.centerCamera(
        viewport,
        player.x,
        player.y
      );
    }
  }, [viewport, entities, mapData]);
  
  // Imposta la mappa e carica le texture
  useEffect(() => {
    if (!app || !viewport || !mapData) return;
    
    let isMounted = true;
    console.log("Inizializzazione rendering mappa...");
    
    async function renderMap() {
      try {
        console.log("1. Caricamento texture...");
        
        // Carica le texture della mappa
        const texturesLoaded = await loadTextures();
        if (!isMounted) return;
        
        if (!texturesLoaded) {
          throw new Error("Impossibile caricare le texture necessarie");
        }
        
        console.log("2. Texture caricate con successo");
        console.log("3. Configurazione layer...");
        
        // Crea container per i layer
        const layersSetup = setupLayers();
        if (!isMounted) return;
        
        if (!layersSetup) {
          throw new Error("Impossibile configurare i layer della mappa");
        }
        
        console.log("4. Layer configurati con successo");
        console.log("5. Renderizzazione strati mappa...");
        
        // Disegna gli strati della mappa
        const layersRendered = renderMapLayers();
        if (!isMounted) return;
        
        if (!layersRendered) {
          throw new Error("Impossibile renderizzare gli strati della mappa");
        }
        
        console.log("6. Strati mappa renderizzati con successo");
        console.log("7. Configurazione viewport...");
        
        // Configura l'interazione con il viewport
        setupViewportInteraction();
        if (!isMounted) return;
        
        console.log("8. Aggiornamento entità...");
        
        // Aggiorna le entità
        updateEntities();
        if (!isMounted) return;
        
        console.log("9. Centraggio su giocatore...");
        
        // Centra la mappa sul giocatore
        centerOnPlayer();
        
        console.log("Mappa inizializzata con successo");
      } catch (err) {
        console.error('Errore nel rendering della mappa:', err);
        if (isMounted) {
          setError('Errore nel rendering della mappa: ' + (err.message || 'Errore sconosciuto'));
          setLoading(false);
        }
      }
    }
    
    renderMap().catch(err => {
      console.error("Errore non gestito nel rendering della mappa:", err);
      if (isMounted) {
        setError('Errore critico nel rendering della mappa. Ricarica la pagina.');
        setLoading(false);
      }
    });
    
    // Pulizia quando il componente viene smontato
    return () => {
      isMounted = false;
    };
  }, [app, viewport, mapData, loadTextures, setupLayers, renderMapLayers, updateEntities, setupViewportInteraction, centerOnPlayer]);
  
  // Aggiorna le entità quando cambiano
  useEffect(() => {
    if (entitiesLayerRef.current && texturesRef.current && texturesRef.current.entities) {
      updateEntities();
    }
  }, [entities, updateEntities]);
  
  // Gestione input da tastiera
  useEffect(() => {
    if (!socket || !connected || !sessionId) return;
    
    const handleMovement = () => {
      if (!mapData) return;
      
      let dx = 0;
      let dy = 0;
      
      // Determina la direzione in base ai tasti premuti
      if (keyboard.isKeyDown('ArrowUp') || keyboard.isKeyDown('KeyW')) {
        dy = -1;
      } else if (keyboard.isKeyDown('ArrowDown') || keyboard.isKeyDown('KeyS')) {
        dy = 1;
      }
      
      if (keyboard.isKeyDown('ArrowLeft') || keyboard.isKeyDown('KeyA')) {
        dx = -1;
      } else if (keyboard.isKeyDown('ArrowRight') || keyboard.isKeyDown('KeyD')) {
        dx = 1;
      }
      
      // Invia movimento al server se è stato premuto un tasto di movimento
      if (dx !== 0 || dy !== 0) {
        emit('player_move', { 
          id_sessione: sessionId, 
          dx, 
          dy 
        });
      }
    };
    
    // Configura un intervallo per il movimento
    const intervalId = setInterval(handleMovement, 150);
    
    return () => {
      clearInterval(intervalId);
    };
  }, [socket, connected, sessionId, mapData, keyboard, emit]);
  
  // Configura il gestore di click sulle entità
  handleEntityClickRef.current = useCallback((entity) => {
    console.log('Click sull\'entità:', entity);
    
    // Emetti evento al server se connesso
    if (socket && connected) {
      emit('entity_interaction', {
        id_sessione: sessionId,
        id_entita: entity.id
      });
    }
  }, [socket, connected, sessionId, emit]);
  
  // Rendering del componente
  return (
    <div className="game-map-screen">
      {loading && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <div className="loading-text">Caricamento mappa...</div>
        </div>
      )}
      
      {error && (
        <div className="error-message">
          {error}
          <button onClick={cleanupAndRetry} className="retry-button">
            Riprova
          </button>
        </div>
      )}
      
      <div 
        ref={containerRef} 
        className="map-container"
      ></div>
      
      {/* Mini mappa (opzionale) */}
      <div className="mini-map">
        {/* Contenuto della mini mappa */}
      </div>
      
      {/* Interfaccia utente aggiuntiva */}
      <div className="map-controls">
        <button onClick={centerOnPlayer}>
          Centra
        </button>
      </div>
    </div>
  );
};

export default GameMapScreen; 