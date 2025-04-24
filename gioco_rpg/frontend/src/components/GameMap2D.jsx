import React, { useEffect, useRef, useState } from 'react';
import * as PIXI from 'pixi.js';
import { Viewport } from 'pixi-viewport';
import axios from 'axios';
import io from 'socket.io-client';
import diagnosticService from '../services/DiagnosticService';
import '../styles/GameMap2D.css';

const API_URL = 'http://localhost:5000';

// Costanti per la configurazione della mappa
const TILE_SIZE = 64;
const GRID_COLOR = 0x444444;
const GRID_ALPHA = 0.3;
const DEFAULT_ZOOM = 1;

/**
 * Componente per la visualizzazione e interazione con la mappa di gioco 2D
 */
const GameMap2D = ({ sessionId }) => {
  // Riferimenti e stato
  const pixiContainerRef = useRef(null);
  const appRef = useRef(null);
  const viewportRef = useRef(null);
  const socketRef = useRef(null);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [mapData, setMapData] = useState(null);
  const [entitiesData, setEntitiesData] = useState([]);
  const [highlightedTile, setHighlightedTile] = useState(null);
  const [selectedEntity, setSelectedEntity] = useState(null);
  
  // Memorizza il riferimento alle texture caricate
  const texturesRef = useRef({
    tiles: {},
    entities: {}
  });
  
  // Memorizza il riferimento agli sprites creati
  const spritesRef = useRef({
    tiles: {},
    entities: {},
    highlights: {},
    markers: {}
  });
  
  // Inizializza Pixi.js
  useEffect(() => {
    if (!pixiContainerRef.current) return;
    
    // Crea l'app Pixi
    const app = new PIXI.Application({
      width: pixiContainerRef.current.clientWidth,
      height: pixiContainerRef.current.clientHeight,
      backgroundColor: 0x1a1a1a,
      resolution: window.devicePixelRatio || 1,
      antialias: true,
      autoDensity: true
    });
    
    // Aggiungi il canvas all'elemento container
    pixiContainerRef.current.innerHTML = '';
    pixiContainerRef.current.appendChild(app.view);
    appRef.current = app;
    
    // Crea il viewport per il panning/zooming
    const viewport = new Viewport({
      screenWidth: app.view.width,
      screenHeight: app.view.height,
      worldWidth: 1000,
      worldHeight: 1000,
      // Usa events per PixiJS v7 in modo compatibile
      events: app.renderer.events
    });
    
    // Configura il viewport
    viewport
      .drag()
      .pinch()
      .wheel()
      .decelerate()
      .clampZoom({
        minScale: 0.5,
        maxScale: 2
      });
    
    // Aggiungi il viewport allo stage
    app.stage.addChild(viewport);
    viewportRef.current = viewport;
    
    // Invia dati viewport al servizio diagnostica
    const viewportInfo = {
      width: app.view.width,
      height: app.view.height,
      scale: viewport.scale.x,
      center_x: viewport.center.x,
      center_y: viewport.center.y
    };
    diagnosticService.updateViewport(viewportInfo);
    
    // Aggiungi listener per aggiornamenti viewport
    viewport.on('zoomed', () => {
      if (viewport && diagnosticService) {
        diagnosticService.updateViewport({
          scale: viewport.scale.x
        });
      }
    });
    
    viewport.on('moved', () => {
      if (viewport && diagnosticService) {
        diagnosticService.updateViewport({
          center_x: viewport.center.x,
          center_y: viewport.center.y
        });
      }
    });
    
    // Gestisci il ridimensionamento della finestra
    const handleResize = () => {
      if (pixiContainerRef.current) {
        app.renderer.resize(
          pixiContainerRef.current.clientWidth,
          pixiContainerRef.current.clientHeight
        );
        
        viewport.resize(
          pixiContainerRef.current.clientWidth,
          pixiContainerRef.current.clientHeight
        );
        
        // Aggiorna dimensioni viewport nel servizio diagnostica
        diagnosticService.updateViewport({
          width: app.view.width,
          height: app.view.height
        });
      }
    };
    
    window.addEventListener('resize', handleResize);
    
    // Pulizia al dismount
    return () => {
      window.removeEventListener('resize', handleResize);
      
      // Disconnetti il socket
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
      
      // Distruggi l'app Pixi
      app.destroy(true, {
        children: true,
        texture: true,
        baseTexture: true
      });
    };
  }, []);
  
  // Connetti al server via WebSocket quando sessionId cambia
  useEffect(() => {
    if (!sessionId) return;
    
    // Connetti al server
    const socket = io(API_URL);
    socketRef.current = socket;
    
    // Evento di connessione
    socket.on('connect', () => {
      console.log('WebSocket connesso');
      
      // Entra nella sessione di gioco
      socket.emit('join_game', { id_sessione: sessionId });
      
      // Richiedi i dati della mappa
      socket.emit('request_map_data', { id_sessione: sessionId });
    });
    
    // Evento di disconnessione
    socket.on('disconnect', () => {
      console.log('WebSocket disconnesso');
    });
    
    // Errore di connessione
    socket.on('connect_error', (error) => {
      console.error('Errore di connessione WebSocket:', error);
      setError('Impossibile connettersi al server: ' + error.message);
    });
    
    // Gestisci dati mappa
    socket.on('map_data', (data) => {
      console.log('Dati mappa ricevuti:', data);
      setMapData(data);
      setLoading(false);
      
      // Renderizza la mappa
      renderMap(data);
    });
    
    // Gestisci aggiornamenti delle entità
    socket.on('entities_update', (data) => {
      console.log('Aggiornamento entità:', data);
      setEntitiesData(data.entities);
      
      // Aggiorna le entità sulla mappa
      updateEntities(data.entities);
    });
    
    return () => {
      if (socket) {
        socket.disconnect();
      }
    };
  }, [sessionId]);
  
  // Carica le texture necessarie
  const loadTextures = async () => {
    try {
      // Carica le texture per i tile
      const tileTextures = {
        floor: PIXI.Texture.from(`${API_URL}/assets/file/tiles/floor.png`),
        wall: PIXI.Texture.from(`${API_URL}/assets/file/tiles/wall.png`),
        door: PIXI.Texture.from(`${API_URL}/assets/file/tiles/door.png`),
        grass: PIXI.Texture.from(`${API_URL}/assets/file/tiles/grass.png`),
        water: PIXI.Texture.from(`${API_URL}/assets/file/tiles/water.png`)
      };
      
      // Carica le texture per le entità
      const entityTextures = {
        player: PIXI.Texture.from(`${API_URL}/assets/file/entities/player.png`),
        npc: PIXI.Texture.from(`${API_URL}/assets/file/entities/npc.png`),
        enemy: PIXI.Texture.from(`${API_URL}/assets/file/entities/enemy.png`),
        chest: PIXI.Texture.from(`${API_URL}/assets/file/objects/chest.png`),
        furniture: PIXI.Texture.from(`${API_URL}/assets/file/objects/furniture.png`)
      };
      
      // Memorizza le texture
      texturesRef.current = {
        tiles: tileTextures,
        entities: entityTextures
      };
      
      // Registra texture nel servizio diagnostica
      for (const key in tileTextures) {
        diagnosticService.registerTexture(tileTextures[key]);
      }
      
      for (const key in entityTextures) {
        diagnosticService.registerTexture(entityTextures[key]);
      }
      
      return true;
    } catch (error) {
      console.error('Errore nel caricamento delle texture:', error);
      setError('Impossibile caricare le risorse grafiche: ' + error.message);
      
      // Invia diagnostica errore
      diagnosticService.logRenderingError(`Errore caricamento texture: ${error.message}`);
      
      return false;
    }
  };
  
  // Renderizza la mappa
  const renderMap = async (mapData) => {
    if (!appRef.current || !viewportRef.current) return;
    
    // Pulisci il viewport prima di renderizzare
    const viewport = viewportRef.current;
    while (viewport.children.length > 0) {
      viewport.removeChild(viewport.children[0]);
    }
    
    // Carica le texture se non già caricate
    const texturesLoaded = await loadTextures();
    if (!texturesLoaded) return;
    
    // Crea contenitori per i diversi layer
    const tileLayer = new PIXI.Container();
    const entityLayer = new PIXI.Container();
    const highlightLayer = new PIXI.Container();
    const gridLayer = new PIXI.Container();
    
    // Aggiungi i layer al viewport nell'ordine corretto
    viewport.addChild(tileLayer);
    viewport.addChild(gridLayer);
    viewport.addChild(entityLayer);
    viewport.addChild(highlightLayer);
    
    // Memorizza i container per aggiornamenti futuri
    spritesRef.current.layers = {
      tile: tileLayer,
      entity: entityLayer,
      highlight: highlightLayer,
      grid: gridLayer
    };
    
    // Estrai informazioni sulla mappa
    const { width, height, layers, name } = mapData;
    
    // Aggiorna le dimensioni del mondo
    viewport.worldWidth = width * TILE_SIZE;
    viewport.worldHeight = height * TILE_SIZE;
    
    // Disegna la griglia
    drawGrid(gridLayer, width, height);
    
    // Disegna i tile
    if (layers && layers.length > 0) {
      layers.forEach(layer => {
        drawLayer(tileLayer, layer, width, height);
      });
    } else {
      // Fallback se non ci sono layer definiti
      drawDefaultFloor(tileLayer, width, height);
    }
    
    // Posiziona la camera al centro della mappa
    centerCamera(width, height);
    
    // Quando la mappa è caricata, richiedi le entità
    requestEntities();
  };
  
  // Disegna la griglia
  const drawGrid = (container, width, height) => {
    const graphics = new PIXI.Graphics();
    graphics.lineStyle(1, GRID_COLOR, GRID_ALPHA);
    
    // Linee orizzontali
    for (let y = 0; y <= height; y++) {
      graphics.moveTo(0, y * TILE_SIZE);
      graphics.lineTo(width * TILE_SIZE, y * TILE_SIZE);
    }
    
    // Linee verticali
    for (let x = 0; x <= width; x++) {
      graphics.moveTo(x * TILE_SIZE, 0);
      graphics.lineTo(x * TILE_SIZE, height * TILE_SIZE);
    }
    
    container.addChild(graphics);
  };
  
  // Disegna un layer
  const drawLayer = (container, layer, width, height) => {
    const { name, data } = layer;
    
    // Mappa degli ID tile alle texture
    const tileMap = {
      0: null, // Tile vuoto
      1: texturesRef.current.tiles.floor, // Pavimento
      2: texturesRef.current.tiles.wall,  // Muro
      3: texturesRef.current.tiles.door,  // Porta
      4: texturesRef.current.tiles.grass, // Erba
      5: texturesRef.current.tiles.water  // Acqua
    };
    
    // Per ogni tile nel layer
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const tileIndex = y * width + x;
        const tileId = data[tileIndex];
        
        // Salta i tile vuoti
        if (tileId === 0) continue;
        
        // Ottieni la texture per il tile
        const texture = tileMap[tileId] || texturesRef.current.tiles.floor;
        
        // Crea lo sprite
        if (texture) {
          const sprite = new PIXI.Sprite(texture);
          sprite.x = x * TILE_SIZE;
          sprite.y = y * TILE_SIZE;
          sprite.width = TILE_SIZE;
          sprite.height = TILE_SIZE;
          
          // Memorizza il tile
          const tileKey = `${x},${y},${name}`;
          spritesRef.current.tiles[tileKey] = sprite;
          
          // Aggiungi lo sprite al container
          container.addChild(sprite);
        }
      }
    }
  };
  
  // Disegna un pavimento di default
  const drawDefaultFloor = (container, width, height) => {
    const floorTexture = texturesRef.current.tiles.floor;
    
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const sprite = new PIXI.Sprite(floorTexture);
        sprite.x = x * TILE_SIZE;
        sprite.y = y * TILE_SIZE;
        sprite.width = TILE_SIZE;
        sprite.height = TILE_SIZE;
        
        // Memorizza il tile
        const tileKey = `${x},${y},default`;
        spritesRef.current.tiles[tileKey] = sprite;
        
        // Aggiungi lo sprite al container
        container.addChild(sprite);
      }
    }
  };
  
  // Centra la camera sulla mappa
  const centerCamera = (width, height) => {
    if (!viewportRef.current) return;
    
    const viewport = viewportRef.current;
    viewport.moveCenter(width * TILE_SIZE / 2, height * TILE_SIZE / 2);
    viewport.setZoom(DEFAULT_ZOOM, true);
  };
  
  // Richiedi le entità presenti sulla mappa
  const requestEntities = () => {
    if (!sessionId || !socketRef.current) return;
    
    // Richiedi le entità attraverso il WebSocket
    socketRef.current.emit('request_entities', {
      id_sessione: sessionId
    });
  };
  
  // Aggiorna le entità sulla mappa
  const updateEntities = (entities) => {
    if (!appRef.current || !spritesRef.current.layers) return;
    
    const entityLayer = spritesRef.current.layers.entity;
    
    // Rimuovi tutte le entità esistenti
    while (entityLayer.children.length > 0) {
      entityLayer.removeChild(entityLayer.children[0]);
    }
    
    // Pulisci il riferimento agli sprite delle entità
    spritesRef.current.entities = {};
    
    // Renderizza le nuove entità
    entities.forEach(entity => {
      const { id, tipo, nome, x, y, spriteId } = entity;
      
      // Determina quale texture usare
      let texture;
      if (tipo === 'player') {
        texture = texturesRef.current.entities.player;
      } else if (tipo === 'npc') {
        texture = texturesRef.current.entities.npc;
      } else if (tipo === 'enemy') {
        texture = texturesRef.current.entities.enemy;
      } else if (tipo === 'chest') {
        texture = texturesRef.current.entities.chest;
      } else {
        texture = texturesRef.current.entities.furniture;
      }
      
      // Crea lo sprite
      if (texture) {
        const sprite = new PIXI.Sprite(texture);
        sprite.x = x * TILE_SIZE;
        sprite.y = y * TILE_SIZE;
        sprite.width = TILE_SIZE;
        sprite.height = TILE_SIZE;
        
        // Aggiungi interattività
        sprite.interactive = true;
        sprite.cursor = 'pointer';
        
        // Gestisci click sull'entità
        sprite.on('pointerdown', () => {
          handleEntityClick(entity);
        });
        
        // Memorizza lo sprite
        spritesRef.current.entities[id] = sprite;
        
        // Aggiungi lo sprite al container
        entityLayer.addChild(sprite);
        
        // Aggiungi etichetta con il nome
        addEntityLabel(entityLayer, nome, x, y);
      }
    });
  };
  
  // Aggiunge un'etichetta con il nome dell'entità
  const addEntityLabel = (container, name, x, y) => {
    const text = new PIXI.Text(name, {
      fontFamily: 'Arial',
      fontSize: 12,
      fill: 0xffffff,
      align: 'center',
      stroke: 0x000000,
      strokeThickness: 4
    });
    
    text.anchor.set(0.5, 0);
    text.x = x * TILE_SIZE + TILE_SIZE / 2;
    text.y = y * TILE_SIZE - 15;
    
    container.addChild(text);
  };
  
  // Gestisce il click su un'entità
  const handleEntityClick = (entity) => {
    console.log('Entità selezionata:', entity);
    setSelectedEntity(entity);
    
    // Emetti evento al server
    if (socketRef.current) {
      socketRef.current.emit('entity_interaction', {
        id_sessione: sessionId,
        entity_id: entity.id
      });
    }
  };
  
  // Gestisce il click su un tile
  const handleTileClick = (x, y) => {
    console.log('Tile selezionato:', x, y);
    setHighlightedTile({ x, y });
    
    // Evidenzia il tile selezionato
    highlightTile(x, y);
    
    // Emetti evento al server
    if (socketRef.current) {
      socketRef.current.emit('move_to', {
        id_sessione: sessionId,
        x: x,
        y: y
      });
    }
  };
  
  // Evidenzia un tile
  const highlightTile = (x, y) => {
    if (!spritesRef.current.layers) return;
    
    const highlightLayer = spritesRef.current.layers.highlight;
    
    // Rimuovi eventuali evidenziazioni precedenti
    while (highlightLayer.children.length > 0) {
      highlightLayer.removeChild(highlightLayer.children[0]);
    }
    
    // Crea un nuovo rettangolo di evidenziazione
    const highlight = new PIXI.Graphics();
    highlight.lineStyle(2, 0xffb938, 0.8);
    highlight.beginFill(0xffb938, 0.2);
    highlight.drawRect(0, 0, TILE_SIZE, TILE_SIZE);
    highlight.endFill();
    highlight.x = x * TILE_SIZE;
    highlight.y = y * TILE_SIZE;
    
    // Aggiungi al layer di evidenziazione
    highlightLayer.addChild(highlight);
  };
  
  // Funzione per eseguire test di rendering
  const runRenderTest = async () => {
    if (!appRef.current || !viewportRef.current) return;
    
    try {
      // Richiedi dati di test
      const testData = await diagnosticService.requestRenderTest();
      
      if (testData.error) {
        console.error('Errore test rendering:', testData.error);
        return;
      }
      
      // Render la mappa di test
      if (testData.map) {
        console.log('Rendering mappa di test');
        renderMap(testData.map);
      }
      
      // Render entità di test
      if (testData.entities && testData.entities.entities) {
        console.log('Rendering entità di test');
        updateEntities(testData.entities.entities);
      }
    } catch (error) {
      console.error('Errore nel test di rendering:', error);
    }
  };
  
  // Aggiungi pulsante di diagnostica sotto la mappa
  const DiagnosticPanel = () => {
    const [isVisible, setIsVisible] = useState(false);
    const [report, setReport] = useState(null);
    
    const runDiagnostics = async () => {
      const results = await diagnosticService.runDiagnostics();
      setReport(results);
    };
    
    if (!isVisible) {
      return (
        <button 
          className="diagnostic-button"
          onClick={() => setIsVisible(true)}
          style={{
            position: 'absolute',
            bottom: '10px',
            right: '10px',
            zIndex: 1000
          }}
        >
          Diagnostica
        </button>
      );
    }
    
    return (
      <div 
        className="diagnostic-panel"
        style={{
          position: 'absolute',
          bottom: '10px',
          right: '10px',
          backgroundColor: 'rgba(0,0,0,0.8)',
          color: 'white',
          padding: '10px',
          borderRadius: '5px',
          zIndex: 1000,
          maxWidth: '300px',
          maxHeight: '300px',
          overflow: 'auto'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
          <h4 style={{ margin: 0 }}>Diagnostica</h4>
          <button onClick={() => setIsVisible(false)}>X</button>
        </div>
        
        <div className="diagnostic-actions">
          <button onClick={runDiagnostics}>Esegui Diagnostica</button>
          <button onClick={runRenderTest}>Test Rendering</button>
        </div>
        
        {report && (
          <div className="diagnostic-report">
            <h5>Connessione Socket</h5>
            <p>Stato: {report.socket.connected ? 'Connesso' : 'Disconnesso'}</p>
            <p>Latenza: {report.socket.latency || 'N/A'} ms</p>
            <p>Pacchetti inviati: {report.socket.sent}</p>
            <p>Pacchetti ricevuti: {report.socket.received}</p>
            
            <h5>Rendering</h5>
            <p>Viewport: {report.viewport.width}x{report.viewport.height}</p>
            <p>Scala: {report.viewport.scale}</p>
            <p>Texture: {report.textures.loaded}/{report.textures.count} caricate</p>
          </div>
        )}
      </div>
    );
  };
  
  return (
    <div className="game-map-container">
      <div
        ref={pixiContainerRef}
        className="pixi-container"
        style={{ width: '100%', height: '100%' }}
      />
      
      {loading && (
        <div className="loading-overlay">
          <p>Caricamento mappa...</p>
        </div>
      )}
      
      {error && (
        <div className="error-overlay">
          <p>Errore: {error}</p>
        </div>
      )}
      
      {/* Pannello diagnostica in sviluppo */}
      {process.env.NODE_ENV !== 'production' && <DiagnosticPanel />}
    </div>
  );
};

export default GameMap2D; 