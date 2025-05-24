import * as PIXI from 'pixi.js';

/**
 * Renderer semplificato basato su griglia per mappe con un'immagine di sfondo
 */
export default class GridMapRenderer {
  constructor() {
    this.GRID_SIZE = 64;
    this.app = null;
    this.viewport = null;
    this.layers = {
      background: null,
      grid: null,
      entities: null
    };
    this.sprites = {
      background: null,
      entities: {}
    };
    this.isInitialized = false;
    this.currentMapData = null;
  }

  /**
   * Inizializza il renderer
   * @param {PIXI.Application} app - Applicazione PIXI
   * @param {PIXI.Container} viewport - Container del viewport
   * @returns {Promise<boolean>} - true se l'inizializzazione è riuscita
   */
  async initialize(app, viewport) {
    try {
      this.app = app;
      this.viewport = viewport;
      
      // Reset della posizione del viewport
      this.viewport.position.set(0, 0);
      
      // Crea i layer nell'ordine corretto
      this.layers.background = new PIXI.Container();
      this.layers.background.name = 'background-layer';
      
      this.layers.grid = new PIXI.Container();
      this.layers.grid.name = 'grid-layer';
      
      this.layers.entities = new PIXI.Container();
      this.layers.entities.name = 'entities-layer';
      
      // Reset dei pivot
      this.layers.background.pivot.set(0, 0);
      this.layers.grid.pivot.set(0, 0);
      this.layers.entities.pivot.set(0, 0);
      
      // Aggiungi i layer al viewport nell'ordine corretto
      this.viewport.addChild(this.layers.background);
      this.viewport.addChild(this.layers.grid);
      this.viewport.addChild(this.layers.entities);
      
      this.isInitialized = true;
      return true;
    } catch (error) {
      console.error('Errore nell\'inizializzazione del GridMapRenderer:', error);
      return false;
    }
  }
  
  /**
   * Adatta il viewport alle dimensioni del contenitore
   */
  resizeViewportToContainer() {
    if (!this.app || !this.viewport) return;
    
    const renderer = this.app.renderer;
    const width = renderer.width;
    const height = renderer.height;
    
    console.log(`Dimensioni container: ${width}x${height}`);
    
    // Reset della posizione del viewport
    this.viewport.position.set(0, 0);
    
    // Assicuriamoci che il renderer PIXI abbia le dimensioni corrette
    if (this.app.view) {
      this.app.view.style.width = '100%';
      this.app.view.style.height = '100%';
    }
    
    // Dopo un ridimensionamento, centra di nuovo la mappa
    if (this.currentMapData) {
      this.centerMapInView();
    }
  }
  
  /**
   * Carica e renderizza una mappa
   * @param {Object} mapData - Dati della mappa
   * @returns {Promise<boolean>} - true se il caricamento è riuscito
   */
  async loadMap(mapData) {
    if (!this.isInitialized || !mapData) {
      console.error('Renderer non inizializzato o dati mappa mancanti');
      return false;
    }
    
    try {
      // Salva i dati della mappa per riferimento futuro
      this.currentMapData = mapData;
      
      // Pulisci i layer prima di caricare la nuova mappa
      this.clearMap();
      
      console.log(`Caricamento mappa: ${mapData.nome}, dimensioni: ${mapData.larghezza}x${mapData.altezza}`);
      
      // Carica l'immagine di sfondo
      if (mapData.backgroundImage) {
        await this.loadBackground(mapData.backgroundImage, mapData.larghezza, mapData.altezza);
      } else {
        // Se non c'è un'immagine di sfondo, crea uno sfondo colorato di default
        this.createDefaultBackground(mapData.larghezza, mapData.altezza);
      }
      
      // Disegna la griglia
      this.drawGrid(mapData.larghezza, mapData.altezza);
      
      // Posiziona la mappa al centro del viewport
      this.centerMapInView();
      
      return true;
    } catch (error) {
      console.error('Errore nel caricamento della mappa:', error);
      return false;
    }
  }
  
  /**
   * Centra la mappa nella visualizzazione
   */
  centerMapInView() {
    if (!this.isInitialized || !this.currentMapData) return;
    
    const mapWidth = this.currentMapData.larghezza * this.GRID_SIZE;
    const mapHeight = this.currentMapData.altezza * this.GRID_SIZE;
    
    // Calcola la posizione centrale
    let screenWidth = this.app.renderer.width;
    let screenHeight = this.app.renderer.height;
    
    // Verifica dimensioni valide e usa fallback se necessario
    if (screenWidth <= 0) screenWidth = 800;
    if (screenHeight <= 0) screenHeight = 600;
    
    // Registra le dimensioni per debug
    console.log(`Dimensioni schermo: ${screenWidth}x${screenHeight}, dimensioni mappa: ${mapWidth}x${mapHeight}`);
    
    // NUOVO APPROCCIO: contenere completamente la mappa con un po' di padding
    // Usiamo min per assicurarci che la mappa sia interamente visibile
    const scaleX = (screenWidth - 40) / mapWidth;  // 20px di padding su ogni lato 
    const scaleY = (screenHeight - 40) / mapHeight; // 20px di padding sopra e sotto
    const scale = Math.min(scaleX, scaleY, 1.0); // Limitiamo a 1.0 per evitare pixelation
    
    console.log(`Ridimensionamento mappa con scala ${scale} (mappa contenuta)`);
    
    // Applica la scala ai layer
    this.layers.background.scale.set(scale, scale);
    this.layers.grid.scale.set(scale, scale);
    this.layers.entities.scale.set(scale, scale);
    
    // Calcola le dimensioni effettive dopo il ridimensionamento
    const scaledMapWidth = mapWidth * scale;
    const scaledMapHeight = mapHeight * scale;
    
    // Centra la mappa orizzontalmente e verticalmente
    const x = (screenWidth - scaledMapWidth) / 2;
    const y = (screenHeight - scaledMapHeight) / 2;
    
    // Posiziona tutti i layer nella stessa posizione
    this.layers.background.position.set(x, y);
    this.layers.grid.position.set(x, y);
    this.layers.entities.position.set(x, y);
    
    console.log(`Mappa posizionata: posizione (${x}, ${y}), dimensioni ${scaledMapWidth}x${scaledMapHeight}`);
  }
  
  /**
   * Carica l'immagine di sfondo della mappa
   * @param {string} backgroundUrl - URL dell'immagine di sfondo
   * @param {number} width - Larghezza della mappa in celle
   * @param {number} height - Altezza della mappa in celle
   * @returns {Promise<boolean>} - true se il caricamento è riuscito
   */
  async loadBackground(backgroundUrl, width, height) {
    return new Promise((resolve, reject) => {
      try {
        // Verifica se l'URL è assoluto o relativo
        let fullUrl = backgroundUrl;
        if (!backgroundUrl.startsWith('http') && !backgroundUrl.startsWith('/')) {
          fullUrl = `/${backgroundUrl}`;
        }
        
        console.log(`Caricamento immagine di sfondo: ${fullUrl}`);
        
        const texture = PIXI.Texture.from(fullUrl);
        const sprite = new PIXI.Sprite(texture);
        
        // Configura texture.onError se possibile
        if (texture.baseTexture) {
          texture.baseTexture.on('error', (err) => {
            console.error(`Errore nel caricamento della texture: ${fullUrl}`, err);
            this.createDefaultBackground(width, height);
            reject(err);
          });
        }
        
        // Quando la texture è caricata
        if (texture.valid) {
          // La texture è già caricata
          this.setupBackgroundSprite(sprite, width, height);
          resolve(true);
        } else {
          // Attendi il caricamento della texture
          texture.once('update', () => {
            this.setupBackgroundSprite(sprite, width, height);
            resolve(true);
          });
        }
      } catch (error) {
        console.error(`Errore nel caricamento dell'immagine di sfondo: ${backgroundUrl}`, error);
        this.createDefaultBackground(width, height);
        reject(error);
      }
    });
  }
  
  /**
   * Configura lo sprite di sfondo
   * @param {PIXI.Sprite} sprite - Sprite di sfondo
   * @param {number} width - Larghezza della mappa in celle
   * @param {number} height - Altezza della mappa in celle
   */
  setupBackgroundSprite(sprite, width, height) {
    // Dimensiona lo sprite per adattarlo alla griglia
    sprite.width = width * this.GRID_SIZE;
    sprite.height = height * this.GRID_SIZE;
    
    // Posizione di base (0,0) - sarà poi centrato da centerMapInView
    sprite.position.set(0, 0);
    
    // Memorizza e aggiungi lo sprite
    this.sprites.background = sprite;
    this.layers.background.addChild(sprite);
  }
  
  /**
   * Crea uno sfondo di default quando l'immagine non è disponibile
   * @param {number} width - Larghezza della mappa in celle
   * @param {number} height - Altezza della mappa in celle
   */
  createDefaultBackground(width, height) {
    console.log('Creazione sfondo di default');
    const graphics = new PIXI.Graphics();
    graphics.beginFill(0x333333);
    graphics.drawRect(0, 0, width * this.GRID_SIZE, height * this.GRID_SIZE);
    graphics.endFill();
    
    this.sprites.background = graphics;
    this.layers.background.addChild(graphics);
  }
  
  /**
   * Disegna la griglia sulla mappa
   * @param {number} width - Larghezza della mappa in celle
   * @param {number} height - Altezza della mappa in celle
   */
  drawGrid(width, height) {
    console.log(`Disegno griglia ${width}x${height}`);
    const graphics = new PIXI.Graphics();
    graphics.lineStyle(1, 0x444444, 0.5);
    
    // Linee verticali
    for (let x = 0; x <= width; x++) {
      graphics.moveTo(x * this.GRID_SIZE, 0);
      graphics.lineTo(x * this.GRID_SIZE, height * this.GRID_SIZE);
    }
    
    // Linee orizzontali
    for (let y = 0; y <= height; y++) {
      graphics.moveTo(0, y * this.GRID_SIZE);
      graphics.lineTo(width * this.GRID_SIZE, y * this.GRID_SIZE);
    }
    
    this.layers.grid.addChild(graphics);
  }
  
  /**
   * Aggiorna i limiti del viewport in base alle dimensioni della mappa
   */
  updateViewportBounds() {
    if (!this.viewport || !this.currentMapData) return;
    
    const width = this.currentMapData.larghezza;
    const height = this.currentMapData.altezza;
    const mapWidthPixels = width * this.GRID_SIZE;
    const mapHeightPixels = height * this.GRID_SIZE;
    
    console.log(`Aggiornati limiti viewport: ${mapWidthPixels}x${mapHeightPixels} pixel`);
  }
  
  /**
   * Aggiungi un'entità alla mappa (giocatore, NPC, oggetto)
   * @param {string} entityId - ID univoco dell'entità
   * @param {string} type - Tipo di entità (player, npc, object)
   * @param {Object} data - Dati dell'entità
   * @returns {PIXI.DisplayObject} - Sprite creato
   */
  addEntity(entityId, type, data) {
    if (!this.isInitialized) return null;
    
    // Estrai coordinate e URL sprite
    const { x, y, spriteUrl, nome } = data;
    
    try {
      let sprite;
      
      // Carica la texture se è stato fornito un URL
      if (spriteUrl) {
        // Verifica se l'URL è assoluto o relativo
        let fullUrl = spriteUrl;
        if (!spriteUrl.startsWith('http') && !spriteUrl.startsWith('/')) {
          fullUrl = `/${spriteUrl}`;
        }
        
        console.log(`Caricamento sprite per ${entityId}: ${fullUrl}`);
        
        const texture = PIXI.Texture.from(fullUrl);
        sprite = new PIXI.Sprite(texture);
      } else {
        // Crea un placeholder se non è stata fornita una texture
        return this.addEntityPlaceholder(entityId, type, x, y, nome);
      }
      
      // Posiziona lo sprite
      sprite.x = x * this.GRID_SIZE;
      sprite.y = y * this.GRID_SIZE;
      sprite.width = this.GRID_SIZE;
      sprite.height = this.GRID_SIZE;
      
      // Aggiungi metadati all'entità
      sprite.entityId = entityId;
      sprite.entityType = type;
      sprite.entityData = data;
      
      // Aggiungi interattività se non è il giocatore
      if (type !== 'player') {
        sprite.interactive = true;
        sprite.buttonMode = true;
      }
      
      // Memorizza e aggiungi lo sprite
      this.sprites.entities[entityId] = sprite;
      this.layers.entities.addChild(sprite);
      
      // Aggiungi un'etichetta con il nome, se disponibile
      if (nome) {
        this.addEntityLabel(entityId, nome, x, y);
      }
      
      return sprite;
    } catch (error) {
      console.error(`Errore nell'aggiunta dell'entità ${entityId}:`, error);
      // Fallback con un grafico colorato
      return this.addEntityPlaceholder(entityId, type, x, y, data.nome);
    }
  }
  
  /**
   * Crea un placeholder per un'entità quando la texture non è disponibile
   * @param {string} entityId - ID univoco dell'entità
   * @param {string} type - Tipo di entità (player, npc, object)
   * @param {number} x - Coordinata X in celle
   * @param {number} y - Coordinata Y in celle
   * @param {string} [name] - Nome dell'entità
   * @returns {PIXI.Graphics} - Grafico creato
   */
  addEntityPlaceholder(entityId, type, x, y, name) {
    console.log(`Creazione placeholder per ${entityId} di tipo ${type}`);
    const graphics = new PIXI.Graphics();
    
    // Diversi colori per diversi tipi di entità
    let color;
    if (type === 'player') color = 0x00FF00;
    else if (type === 'npc') color = 0x0000FF;
    else color = 0xFF0000;
    
    graphics.beginFill(color, 0.7);
    
    if (type === 'npc') {
      // NPC: cerchio
      graphics.drawCircle(this.GRID_SIZE / 2, this.GRID_SIZE / 2, this.GRID_SIZE / 3);
    } else {
      // Altri: quadrato
      graphics.drawRect(0, 0, this.GRID_SIZE, this.GRID_SIZE);
    }
    
    graphics.endFill();
    graphics.x = x * this.GRID_SIZE;
    graphics.y = y * this.GRID_SIZE;
    
    // Aggiungi metadati
    graphics.entityId = entityId;
    graphics.entityType = type;
    
    // Memorizza e aggiungi lo sprite
    this.sprites.entities[entityId] = graphics;
    this.layers.entities.addChild(graphics);
    
    // Aggiungi un'etichetta con il nome, se disponibile
    if (name) {
      this.addEntityLabel(entityId, name, x, y);
    }
    
    return graphics;
  }
  
  /**
   * Aggiunge un'etichetta con il nome dell'entità
   * @param {string} entityId - ID dell'entità
   * @param {string} name - Nome da visualizzare
   * @param {number} x - Coordinata X in celle
   * @param {number} y - Coordinata Y in celle
   */
  addEntityLabel(entityId, name, x, y) {
    const labelStyle = new PIXI.TextStyle({
      fontFamily: 'Arial',
      fontSize: 12,
      fill: '#ffffff',
      stroke: '#000000',
      strokeThickness: 3,
      align: 'center'
    });
    
    const label = new PIXI.Text(name, labelStyle);
    label.anchor.set(0.5, 1); // Allinea il testo al centro-basso
    label.x = x * this.GRID_SIZE + this.GRID_SIZE / 2;
    label.y = y * this.GRID_SIZE;
    
    // Aggiungi un ID univoco per poterlo trovare in seguito
    label.name = `label-${entityId}`;
    
    this.layers.entities.addChild(label);
  }
  
  /**
   * Aggiorna la posizione di un'entità
   * @param {string} entityId - ID dell'entità
   * @param {number} x - Nuova coordinata X in celle
   * @param {number} y - Nuova coordinata Y in celle
   * @returns {boolean} - true se l'aggiornamento è riuscito
   */
  updateEntityPosition(entityId, x, y) {
    const sprite = this.sprites.entities[entityId];
    if (!sprite) {
      console.warn(`Entità ${entityId} non trovata`);
      return false;
    }
    
    // Aggiorna le coordinate
    sprite.x = x * this.GRID_SIZE;
    sprite.y = y * this.GRID_SIZE;
    
    // Aggiorna anche l'etichetta, se presente
    const label = this.findEntityLabel(entityId);
    if (label) {
      label.x = x * this.GRID_SIZE + this.GRID_SIZE / 2;
      label.y = y * this.GRID_SIZE;
    }
    
    return true;
  }
  
  /**
   * Trova l'etichetta di un'entità
   * @param {string} entityId - ID dell'entità
   * @returns {PIXI.Text|null} - Etichetta trovata o null
   */
  findEntityLabel(entityId) {
    return this.layers.entities.children.find(child => child.name === `label-${entityId}`);
  }
  
  /**
   * Rimuovi un'entità dalla mappa
   * @param {string} entityId - ID dell'entità
   * @returns {boolean} - true se la rimozione è riuscita
   */
  removeEntity(entityId) {
    const sprite = this.sprites.entities[entityId];
    if (!sprite) {
      console.warn(`Entità ${entityId} non trovata per la rimozione`);
      return false;
    }
    
    // Rimuovi lo sprite
    this.layers.entities.removeChild(sprite);
    sprite.destroy();
    delete this.sprites.entities[entityId];
    
    // Rimuovi anche l'etichetta, se presente
    const label = this.findEntityLabel(entityId);
    if (label) {
      this.layers.entities.removeChild(label);
      label.destroy();
    }
    
    return true;
  }
  
  /**
   * Pulisce la mappa rimuovendo tutti gli elementi
   */
  clearMap() {
    console.log('Pulizia della mappa');
    
    // Pulisci il layer di sfondo
    while (this.layers.background.children.length > 0) {
      const child = this.layers.background.children[0];
      this.layers.background.removeChild(child);
      child.destroy();
    }
    
    // Pulisci il layer della griglia
    while (this.layers.grid.children.length > 0) {
      const child = this.layers.grid.children[0];
      this.layers.grid.removeChild(child);
      child.destroy();
    }
    
    // Pulisci il layer delle entità
    while (this.layers.entities.children.length > 0) {
      const child = this.layers.entities.children[0];
      this.layers.entities.removeChild(child);
      child.destroy();
    }
    
    // Reset delle strutture dati
    this.sprites.background = null;
    this.sprites.entities = {};
  }
  
  /**
   * Centra la visualizzazione su una posizione specifica
   * @param {number} x - Coordinata X in celle
   * @param {number} y - Coordinata Y in celle
   */
  centerOn(x, y) {
    if (!this.viewport || !this.currentMapData) return;
    
    const mapWidth = this.currentMapData.larghezza * this.GRID_SIZE;
    const mapHeight = this.currentMapData.altezza * this.GRID_SIZE;
    
    // Calcola la posizione centrale
    const screenWidth = this.app.renderer.width;
    const screenHeight = this.app.renderer.height;
    
    const baseX = (screenWidth - mapWidth) / 2;
    const baseY = (screenHeight - mapHeight) / 2;
    
    // Centra la mappa, poi sposta il viewport in modo che l'entità sia al centro
    const entityCenterX = x * this.GRID_SIZE + this.GRID_SIZE / 2;
    const entityCenterY = y * this.GRID_SIZE + this.GRID_SIZE / 2;
    const targetX = screenWidth / 2 - entityCenterX;
    const targetY = screenHeight / 2 - entityCenterY;
    
    // Applica offset per centrare l'entità
    this.layers.background.position.set(baseX + targetX, baseY + targetY);
    this.layers.grid.position.set(baseX + targetX, baseY + targetY);
    this.layers.entities.position.set(baseX + targetX, baseY + targetY);
  }
  
  /**
   * Centra la visualizzazione su un'entità
   * @param {string} entityId - ID dell'entità
   */
  centerOnEntity(entityId) {
    const sprite = this.sprites.entities[entityId];
    if (!sprite) return;
    
    const x = sprite.x / this.GRID_SIZE;
    const y = sprite.y / this.GRID_SIZE;
    
    this.centerOn(x, y);
  }
  
  /**
   * Ottiene l'entità a una specifica posizione
   * @param {number} x - Coordinata X in celle
   * @param {number} y - Coordinata Y in celle
   * @returns {Object|null} - Entità trovata o null
   */
  getEntityAt(x, y) {
    // Converti le coordinate da celle a pixel
    const pixelX = x * this.GRID_SIZE;
    const pixelY = y * this.GRID_SIZE;
    
    // Cerca tra tutte le entità
    for (const entityId in this.sprites.entities) {
      const sprite = this.sprites.entities[entityId];
      
      if (sprite.x === pixelX && sprite.y === pixelY) {
        return {
          id: entityId,
          type: sprite.entityType,
          data: sprite.entityData
        };
      }
    }
    
    return null;
  }
  
  /**
   * Evidenzia una cella della griglia
   * @param {number} x - Coordinata X in celle
   * @param {number} y - Coordinata Y in celle
   * @param {number} color - Colore dell'evidenziazione (esadecimale)
   * @param {number} alpha - Trasparenza dell'evidenziazione (0-1)
   */
  highlightCell(x, y, color = 0xFFFF00, alpha = 0.3) {
    // Rimuovi evidenziazione precedente
    this.clearHighlights();
    
    // Crea un nuovo rettangolo di evidenziazione
    const highlight = new PIXI.Graphics();
    highlight.beginFill(color, alpha);
    highlight.drawRect(0, 0, this.GRID_SIZE, this.GRID_SIZE);
    highlight.endFill();
    highlight.x = x * this.GRID_SIZE;
    highlight.y = y * this.GRID_SIZE;
    
    // Aggiungi un nome per identificarlo
    highlight.name = 'cell-highlight';
    
    // Aggiungi al layer della griglia
    this.layers.grid.addChild(highlight);
  }
  
  /**
   * Rimuove tutte le evidenziazioni
   */
  clearHighlights() {
    // Trova e rimuovi tutti gli elementi con nome 'cell-highlight'
    const highlights = this.layers.grid.children.filter(child => child.name === 'cell-highlight');
    
    for (const highlight of highlights) {
      this.layers.grid.removeChild(highlight);
      highlight.destroy();
    }
  }
  
  /**
   * Verifica se una cella è percorribile (non contiene ostacoli)
   * @param {number} x - Coordinata X in celle
   * @param {number} y - Coordinata Y in celle
   * @returns {boolean} - true se la cella è percorribile
   */
  isCellWalkable(x, y) {
    if (!this.currentMapData || !this.currentMapData.griglia) return false;
    
    // Verifica che le coordinate siano all'interno della mappa
    if (x < 0 || y < 0 || y >= this.currentMapData.griglia.length || 
        !this.currentMapData.griglia[y] || x >= this.currentMapData.griglia[y].length) {
      return false;
    }
    
    // Nella griglia: 0 = percorribile, 1 = ostacolo
    return this.currentMapData.griglia[y][x] === 0;
  }
  
  /**
   * Aggiorna il renderer quando le dimensioni del contenitore cambiano
   * Questo dovrebbe essere chiamato quando la finestra viene ridimensionata
   */
  resize() {
    if (!this.app || !this.isInitialized) return;
    
    // Aggiorna le dimensioni del renderer PIXI se necessario
    const canvas = this.app.view;
    if (canvas && canvas.parentElement) {
      // Ottieni le dimensioni del contenitore
      let parentWidth = canvas.parentElement.clientWidth;
      let parentHeight = canvas.parentElement.clientHeight;
      
      // Assicurati che le dimensioni siano valide
      if (parentWidth <= 0) parentWidth = 800; // Valore fallback
      if (parentHeight <= 0) parentHeight = 600; // Valore fallback
      
      console.log(`Ridimensionamento renderer a ${parentWidth}x${parentHeight}`);
      
      // Verifica se le dimensioni sono effettivamente cambiate
      if (this.app.renderer.width !== parentWidth || this.app.renderer.height !== parentHeight) {
        // Resize del renderer a piena dimensione
        this.app.renderer.resize(parentWidth, parentHeight);
        
        // Assicurati che il canvas abbia le dimensioni corrette
        canvas.style.width = '100%';
        canvas.style.height = '100%';
        
        // Registra le dimensioni effettive
        console.log(`Dimensioni canvas dopo resize: ${canvas.width}x${canvas.height}`);
        
        // Ricentralizza la mappa
        this.centerMapInView();
      }
    }
  }
  
  /**
   * Distrugge il renderer e libera le risorse
   */
  destroy() {
    if (!this.isInitialized) return;
    
    this.clearMap();
    
    // Rimuovi i layer dal viewport
    if (this.viewport) {
      this.viewport.removeChild(this.layers.background);
      this.viewport.removeChild(this.layers.grid);
      this.viewport.removeChild(this.layers.entities);
    }
    
    // Reset delle variabili
    this.layers = null;
    this.sprites = null;
    this.currentMapData = null;
    this.app = null;
    this.viewport = null;
    this.isInitialized = false;
  }
} 