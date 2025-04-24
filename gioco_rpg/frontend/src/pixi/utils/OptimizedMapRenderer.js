/**
 * OptimizedMapRenderer.js
 * Renderer ottimizzato per mappe di grandi dimensioni con viewport culling e batching
 */
import * as PIXI from 'pixi.js';
import TileAtlas from './spritesheets/TileAtlas';

// Costanti
const TILE_SIZE = 64;
const CHUNK_SIZE = 16; // Dimensione dei chunk in tile (16x16)

/**
 * Renderer ottimizzato per mappe di grandi dimensioni
 */
export default class OptimizedMapRenderer {
  constructor() {
    this.tileAtlas = new TileAtlas();
    this.app = null;
    this.viewport = null;
    this.mapData = null;
    this.chunks = new Map(); // Map di chunk renderizzati
    this.renderedTiles = new Map(); // Cache di tutti i tile renderizzati
    this.isInitialized = false;
    this.lastViewportBounds = null; // Per evitare re-render inutili
    this.scaleFactor = 1; // Fattore di scala per zoom
    this.chunkContainers = new Map(); // Container per ogni chunk
    this.layerContainers = {}; // Container per i vari layer (terreno, oggetti, entità)
  }

  /**
   * Inizializza il renderer
   * @param {PIXI.Application} app - Applicazione PIXI.js
   * @param {PIXI.Container} viewport - Container del viewport
   * @returns {Promise<boolean>} - true se l'inizializzazione è riuscita
   */
  async initialize(app, viewport) {
    if (this.isInitialized) return true;

    try {
      this.app = app;
      this.viewport = viewport;

      // Inizializza l'atlas delle texture
      await this.tileAtlas.initialize();

      // Crea container per i vari layer
      this.layerContainers = {
        background: new PIXI.Container(),
        terrain: new PIXI.Container(),
        objects: new PIXI.Container(),
        entities: new PIXI.Container(),
        foreground: new PIXI.Container(),
        effects: new PIXI.Container()
      };

      // Configura zIndex e aggiunge i layer al viewport
      Object.entries(this.layerContainers).forEach(([key, container], index) => {
        container.name = `layer-${key}`;
        container.zIndex = index * 10;
        container.sortableChildren = true;
        this.viewport.addChild(container);
      });

      if (this.viewport.sortableChildren !== undefined) {
        this.viewport.sortableChildren = true;
      }

      // Aggiungi handler per aggiornare il culling quando il viewport cambia
      this.setupViewportListeners();

      this.isInitialized = true;
      return true;
    } catch (error) {
      console.error("Errore nell'inizializzazione del renderer:", error);
      return false;
    }
  }

  /**
   * Configura i listener per il viewport
   */
  setupViewportListeners() {
    // Per viewport plugin (pixi-viewport)
    if (this.viewport.plugins && this.viewport.on) {
      this.viewport.on('moved', this.updateVisibleChunks.bind(this));
      this.viewport.on('zoomed', this.handleZoom.bind(this));
    } else {
      // Fallback per viewport semplice
      this.app.ticker.add(this.checkViewportChanges.bind(this));
    }
  }

  /**
   * Carica una mappa e prepara il rendering
   * @param {Object} mapData - Dati della mappa da renderizzare
   * @returns {boolean} - true se la mappa è stata caricata
   */
  loadMap(mapData) {
    try {
      if (!mapData) {
        console.error("Dati mappa non validi");
        return false;
      }

      // Pulisci la mappa precedente
      this.clearMap();

      this.mapData = mapData;
      this.mapWidth = mapData.larghezza || (mapData.griglia ? mapData.griglia[0].length : 0);
      this.mapHeight = mapData.altezza || (mapData.griglia ? mapData.griglia.length : 0);

      console.log(`Caricamento mappa: ${this.mapWidth}x${this.mapHeight} tiles`);

      // Inizializza i chunk
      this.initializeChunks();

      // Renderizza i chunk visibili
      this.updateVisibleChunks();

      // Aggiungi griglia se necessario
      if (mapData.showGrid) {
        this.drawGrid();
      }

      return true;
    } catch (error) {
      console.error("Errore nel caricamento della mappa:", error);
      return false;
    }
  }

  /**
   * Inizializza i chunk della mappa
   */
  initializeChunks() {
    // Calcola il numero di chunk necessari
    this.chunksX = Math.ceil(this.mapWidth / CHUNK_SIZE);
    this.chunksY = Math.ceil(this.mapHeight / CHUNK_SIZE);

    console.log(`Mappa divisa in ${this.chunksX}x${this.chunksY} chunk`);

    // Prepara la struttura per i chunk
    this.chunks = new Map();
    this.chunkContainers = new Map();

    // Inizializza tutti i chunk (ma non renderizzarli ancora)
    for (let cy = 0; cy < this.chunksY; cy++) {
      for (let cx = 0; cx < this.chunksX; cx++) {
        const chunkId = `${cx},${cy}`;
        
        // Crea la struttura dati del chunk
        this.chunks.set(chunkId, {
          id: chunkId,
          x: cx,
          y: cy,
          isRendered: false,
          bounds: {
            x: cx * CHUNK_SIZE * TILE_SIZE,
            y: cy * CHUNK_SIZE * TILE_SIZE,
            width: CHUNK_SIZE * TILE_SIZE,
            height: CHUNK_SIZE * TILE_SIZE
          },
          tileIds: [] // Sarà popolato durante il rendering
        });
      }
    }
  }

  /**
   * Renderizza un singolo chunk della mappa
   * @param {string} chunkId - ID del chunk
   */
  renderChunk(chunkId) {
    const chunk = this.chunks.get(chunkId);
    if (!chunk || chunk.isRendered) return;

    // Crea un container per questo chunk
    const container = new PIXI.Container();
    container.name = `chunk-${chunkId}`;
    container.position.set(chunk.bounds.x, chunk.bounds.y);
    
    // Attiva il flag cull per ottimizzare il rendering
    container.cullable = true;

    // Prendi i limiti di questo chunk in coordinate tile
    const startX = chunk.x * CHUNK_SIZE;
    const startY = chunk.y * CHUNK_SIZE;
    const endX = Math.min(startX + CHUNK_SIZE, this.mapWidth);
    const endY = Math.min(startY + CHUNK_SIZE, this.mapHeight);

    // Aggiungi tile del terreno (strato base)
    if (this.mapData.griglia && Array.isArray(this.mapData.griglia)) {
      for (let y = startY; y < endY; y++) {
        const row = this.mapData.griglia[y];
        if (!row || !Array.isArray(row)) continue;

        for (let x = startX; x < endX; x++) {
          if (x >= row.length) continue;

          const tileId = row[x];
          if (!tileId) continue; // Salta i tile vuoti

          // Ottieni la texture corretta dal tile atlas
          const texture = this.tileAtlas.getTexture(tileId);

          // Crea lo sprite
          const sprite = new PIXI.Sprite(texture);
          sprite.x = (x - startX) * TILE_SIZE;
          sprite.y = (y - startY) * TILE_SIZE;
          sprite.width = TILE_SIZE;
          sprite.height = TILE_SIZE;

          // Aggiungi metadati
          sprite.tileId = tileId;
          sprite.tileX = x;
          sprite.tileY = y;
          
          // Attiva il flag cull anche per lo sprite
          sprite.cullable = true;

          // Aggiungi lo sprite al container del chunk
          container.addChild(sprite);

          // Aggiungi alla cache
          this.renderedTiles.set(`${x},${y}`, sprite);
        }
      }
    }

    // Memorizza il container del chunk
    this.chunkContainers.set(chunkId, container);
    
    // Aggiungi il chunk al layer terreno
    this.layerContainers.terrain.addChild(container);

    // Segna il chunk come renderizzato
    chunk.isRendered = true;
  }

  /**
   * Renderizza gli oggetti della mappa (porte, chest, etc.)
   */
  renderObjects() {
    if (!this.mapData.oggetti) return;

    // Pulisci il container degli oggetti
    while (this.layerContainers.objects.children.length > 0) {
      const child = this.layerContainers.objects.children[0];
      this.layerContainers.objects.removeChild(child);
      child.destroy({ children: true });
    }

    // Crea una mappa per raggruppare gli oggetti per tipo (per ottimizzare il batch rendering)
    const objectsByType = new Map();

    // Organizza gli oggetti per tipo
    for (const [posizione, oggetto] of Object.entries(this.mapData.oggetti)) {
      // Estrai le coordinate dalla stringa (x, y)
      const match = posizione.match(/\((\d+),\s*(\d+)\)/);
      if (!match) continue;

      const x = parseInt(match[1], 10);
      const y = parseInt(match[2], 10);

      // Aggiungi l'oggetto al gruppo del suo tipo
      if (!objectsByType.has(oggetto.tipo)) {
        objectsByType.set(oggetto.tipo, []);
      }
      objectsByType.get(oggetto.tipo).push({ x, y, data: oggetto });
    }

    // Per ogni tipo di oggetto, crea un batch
    for (const [tipo, oggetti] of objectsByType.entries()) {
      const batchContainer = new PIXI.Container();
      batchContainer.name = `batch-${tipo}`;
      
      // Texture specifica per questo tipo
      const texture = this.tileAtlas.getTexture('item');

      // Aggiungi tutti gli oggetti di questo tipo al batch
      for (const obj of oggetti) {
        const sprite = new PIXI.Sprite(texture);
        sprite.x = obj.x * TILE_SIZE;
        sprite.y = obj.y * TILE_SIZE;
        sprite.width = TILE_SIZE;
        sprite.height = TILE_SIZE;
        
        // Aggiungi metadati
        sprite.objectData = obj.data;
        sprite.interactive = true;
        sprite.buttonMode = true;
        
        // Attiva culling
        sprite.cullable = true;
        
        // Aggiungi al container del batch
        batchContainer.addChild(sprite);

        // Aggiungi etichetta (testo)
        const label = new PIXI.Text(obj.data.nome || tipo, {
          fontFamily: 'Arial',
          fontSize: 10,
          fill: 0xFFFFFF,
          stroke: 0x000000,
          strokeThickness: 2
        });
        label.position.set(obj.x * TILE_SIZE + 2, obj.y * TILE_SIZE + 2);
        label.cullable = true;
        batchContainer.addChild(label);
      }

      // Aggiungi il batch al layer degli oggetti
      this.layerContainers.objects.addChild(batchContainer);
    }
  }

  /**
   * Renderizza gli NPC sulla mappa
   */
  renderNPCs() {
    if (!this.mapData.npg) return;

    // Pulisci il container delle entità
    while (this.layerContainers.entities.children.length > 0) {
      const child = this.layerContainers.entities.children[0];
      this.layerContainers.entities.removeChild(child);
      child.destroy({ children: true });
    }

    // Container per tutti gli NPC
    const npcsContainer = new PIXI.Container();
    npcsContainer.name = 'npcs-container';

    // Texture per gli NPC
    const npcTexture = this.tileAtlas.getTexture('npc');

    // Aggiungi tutti gli NPC
    for (const [posizione, npc] of Object.entries(this.mapData.npg)) {
      // Estrai le coordinate dalla stringa (x, y)
      const match = posizione.match(/\((\d+),\s*(\d+)\)/);
      if (!match) continue;

      const x = parseInt(match[1], 10);
      const y = parseInt(match[2], 10);

      // Crea lo sprite dell'NPC
      const sprite = new PIXI.Sprite(npcTexture);
      sprite.x = x * TILE_SIZE;
      sprite.y = y * TILE_SIZE;
      sprite.width = TILE_SIZE;
      sprite.height = TILE_SIZE;
      
      // Aggiungi metadati
      sprite.npcData = npc;
      sprite.interactive = true;
      sprite.buttonMode = true;
      
      // Attiva culling
      sprite.cullable = true;
      
      // Aggiungi al container degli NPC
      npcsContainer.addChild(sprite);

      // Aggiungi etichetta (testo)
      const label = new PIXI.Text(npc.nome || 'NPC', {
        fontFamily: 'Arial',
        fontSize: 10,
        fill: 0xFFFFFF,
        stroke: 0x000000,
        strokeThickness: 2
      });
      label.position.set(x * TILE_SIZE + 2, y * TILE_SIZE - 12);
      label.cullable = true;
      npcsContainer.addChild(label);
    }

    // Aggiungi il container al layer delle entità
    this.layerContainers.entities.addChild(npcsContainer);
  }

  /**
   * Disegna una griglia sulla mappa
   */
  drawGrid() {
    const gridGraphics = new PIXI.Graphics();
    gridGraphics.lineStyle(1, 0x444444, 0.3);
    
    // Disegna linee verticali
    for (let x = 0; x <= this.mapWidth; x++) {
      gridGraphics.moveTo(x * TILE_SIZE, 0);
      gridGraphics.lineTo(x * TILE_SIZE, this.mapHeight * TILE_SIZE);
    }
    
    // Disegna linee orizzontali
    for (let y = 0; y <= this.mapHeight; y++) {
      gridGraphics.moveTo(0, y * TILE_SIZE);
      gridGraphics.lineTo(this.mapWidth * TILE_SIZE, y * TILE_SIZE);
    }
    
    this.layerContainers.foreground.addChild(gridGraphics);
  }

  /**
   * Aggiorna i chunk visibili basandosi sul viewport
   */
  updateVisibleChunks() {
    if (!this.viewport || !this.mapData) return;

    try {
      // Calcola i limiti del viewport
      const viewportBounds = this.getViewportBounds();
      
      // Se i limiti non sono cambiati, non aggiornare
      if (this.lastViewportBounds && 
          this.lastViewportBounds.x === viewportBounds.x &&
          this.lastViewportBounds.y === viewportBounds.y &&
          this.lastViewportBounds.width === viewportBounds.width &&
          this.lastViewportBounds.height === viewportBounds.height) {
        return;
      }
      
      // Aggiorna i limiti correnti
      this.lastViewportBounds = viewportBounds;

      // Converti i limiti del viewport in coordinate chunk
      const startChunkX = Math.max(0, Math.floor(viewportBounds.x / (CHUNK_SIZE * TILE_SIZE)));
      const startChunkY = Math.max(0, Math.floor(viewportBounds.y / (CHUNK_SIZE * TILE_SIZE)));
      const endChunkX = Math.min(this.chunksX - 1, Math.ceil((viewportBounds.x + viewportBounds.width) / (CHUNK_SIZE * TILE_SIZE)));
      const endChunkY = Math.min(this.chunksY - 1, Math.ceil((viewportBounds.y + viewportBounds.height) / (CHUNK_SIZE * TILE_SIZE)));

      // Aggiungi margine per evitare pop-in
      const bufferChunks = 1;
      const minChunkX = Math.max(0, startChunkX - bufferChunks);
      const minChunkY = Math.max(0, startChunkY - bufferChunks);
      const maxChunkX = Math.min(this.chunksX - 1, endChunkX + bufferChunks);
      const maxChunkY = Math.min(this.chunksY - 1, endChunkY + bufferChunks);

      // Renderizza i chunk visibili
      for (let cy = minChunkY; cy <= maxChunkY; cy++) {
        for (let cx = minChunkX; cx <= maxChunkX; cx++) {
          const chunkId = `${cx},${cy}`;
          const chunk = this.chunks.get(chunkId);
          
          if (chunk && !chunk.isRendered) {
            this.renderChunk(chunkId);
          }
        }
      }
    } catch (error) {
      console.error("Errore nell'aggiornamento dei chunk visibili:", error);
    }
  }

  /**
   * Verifica se ci sono state modifiche al viewport
   */
  checkViewportChanges() {
    const viewportBounds = this.getViewportBounds();
    
    // Se i limiti sono cambiati, aggiorna i chunk visibili
    if (!this.lastViewportBounds || 
        this.lastViewportBounds.x !== viewportBounds.x ||
        this.lastViewportBounds.y !== viewportBounds.y ||
        this.lastViewportBounds.width !== viewportBounds.width ||
        this.lastViewportBounds.height !== viewportBounds.height) {
      this.updateVisibleChunks();
    }
  }

  /**
   * Gestisce gli eventi di zoom
   * @param {Object} event - Evento di zoom
   */
  handleZoom(event) {
    const newScale = event.target.scale.x;
    
    // Se lo zoom è cambiato significativamente
    if (Math.abs(this.scaleFactor - newScale) > 0.1) {
      this.scaleFactor = newScale;
      this.updateVisibleChunks();
    }
  }

  /**
   * Ottiene i limiti attuali del viewport
   * @returns {Object} - Limiti del viewport { x, y, width, height }
   */
  getViewportBounds() {
    try {
      // Per pixi-viewport plugin
      if (this.viewport.worldScreenWidth && this.viewport.worldScreenHeight) {
        return {
          x: this.viewport.left,
          y: this.viewport.top,
          width: this.viewport.worldScreenWidth,
          height: this.viewport.worldScreenHeight
        };
      }
      
      // Fallback per viewport semplice
      return {
        x: -this.viewport.x,
        y: -this.viewport.y,
        width: this.app.renderer.width / this.viewport.scale.x,
        height: this.app.renderer.height / this.viewport.scale.y
      };
    } catch (error) {
      console.error("Errore nel calcolo dei limiti del viewport:", error);
      
      // Fallback con dimensioni del renderer
      return {
        x: 0,
        y: 0,
        width: this.app.renderer.width,
        height: this.app.renderer.height
      };
    }
  }

  /**
   * Pulisce la mappa corrente
   */
  clearMap() {
    // Pulisci tutti i layer
    Object.values(this.layerContainers).forEach(container => {
      while (container.children.length > 0) {
        const child = container.children[0];
        container.removeChild(child);
        if (child.destroy) {
          child.destroy({ children: true });
        }
      }
    });

    // Reset delle strutture dati
    this.chunks = new Map();
    this.chunkContainers = new Map();
    this.renderedTiles = new Map();
    this.lastViewportBounds = null;
  }

  /**
   * Distrugge il renderer e libera le risorse
   */
  destroy() {
    try {
      // Pulisci la mappa
      this.clearMap();

      // Rimuovi listener
      if (this.viewport.plugins && this.viewport.off) {
        this.viewport.off('moved', this.updateVisibleChunks.bind(this));
        this.viewport.off('zoomed', this.handleZoom.bind(this));
      } else {
        this.app.ticker.remove(this.checkViewportChanges.bind(this));
      }

      // Distruggi l'atlas
      this.tileAtlas.dispose();

      // Reset delle variabili
      this.app = null;
      this.viewport = null;
      this.mapData = null;
      this.isInitialized = false;

      return true;
    } catch (error) {
      console.error("Errore nella distruzione del renderer:", error);
      return false;
    }
  }
} 