import * as PIXI from 'pixi.js';
// Tutti i moduli necessari sono disponibili direttamente da PIXI
// import { utils, settings, Rectangle, Point } from '@pixi/core';

// Costanti per il rendering
const TILE_SIZE = 64;
const GRID_COLOR = 0x444444;
const GRID_ALPHA = 0.3;

/**
 * Utility per il rendering della mappa con Pixi.js
 */
export default class MapRenderer {
  /**
   * Renderizza una griglia sulla mappa
   * @param {PIXI.Container} container - Container Pixi dove disegnare
   * @param {number} width - Larghezza della mappa in tile
   * @param {number} height - Altezza della mappa in tile
   */
  static drawGrid(container, width, height) {
    const graphics = new PIXI.Graphics();
    graphics.lineStyle(1, GRID_COLOR, GRID_ALPHA);
    
    // Disegna le linee verticali
    for (let x = 0; x <= width; x++) {
      graphics.moveTo(x * TILE_SIZE, 0);
      graphics.lineTo(x * TILE_SIZE, height * TILE_SIZE);
    }
    
    // Disegna le linee orizzontali
    for (let y = 0; y <= height; y++) {
      graphics.moveTo(0, y * TILE_SIZE);
      graphics.lineTo(width * TILE_SIZE, y * TILE_SIZE);
    }
    
    container.addChild(graphics);
    return graphics;
  }
  
  /**
   * Disegna il pavimento predefinito per le celle vuote
   * @param {PIXI.Container} container - Container Pixi dove disegnare
   * @param {number} width - Larghezza della mappa in tile
   * @param {number} height - Altezza della mappa in tile
   * @param {PIXI.Texture} texture - Texture da usare per il pavimento
   */
  static drawDefaultFloor(container, width, height, texture) {
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const sprite = new PIXI.Sprite(texture);
        sprite.x = x * TILE_SIZE;
        sprite.y = y * TILE_SIZE;
        sprite.width = TILE_SIZE;
        sprite.height = TILE_SIZE;
        container.addChild(sprite);
      }
    }
  }
  
  /**
   * Renderizza uno strato della mappa
   * @param {PIXI.Container} container - Container Pixi dove disegnare
   * @param {Array} layer - Array con i dati dello strato
   * @param {number} width - Larghezza della mappa in tile
   * @param {number} height - Altezza della mappa in tile
   * @param {Object} textures - Mappa delle texture disponibili
   */
  static drawLayer(container, layer, width, height, textures) {
    const layerContainer = new PIXI.Container();
    
    // Iterazione sui dati dello strato
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        // Ottieni il tile alla posizione corrente
        const tileIndex = y * width + x;
        const tileType = layer[tileIndex];
        
        // Salta i tile vuoti (0 o null)
        if (!tileType) continue;
        
        // Cerca la texture corrispondente
        let texture = textures[tileType];
        
        // Se la texture non è disponibile, usa una texture predefinita
        if (!texture) {
          console.warn(`Texture mancante per il tile tipo ${tileType}`);
          texture = textures.floor || PIXI.Texture.WHITE;
        }
        
        // Crea lo sprite e posizionalo
        const sprite = new PIXI.Sprite(texture);
        sprite.x = x * TILE_SIZE;
        sprite.y = y * TILE_SIZE;
        sprite.width = TILE_SIZE;
        sprite.height = TILE_SIZE;
        
        layerContainer.addChild(sprite);
      }
    }
    
    container.addChild(layerContainer);
    return layerContainer;
  }
  
  /**
   * Renderizza tutti gli strati della mappa
   * @param {PIXI.Container} container - Container Pixi dove disegnare
   * @param {Object} mapData - Dati della mappa
   * @param {Object} textures - Mappa delle texture disponibili
   */
  static renderMapLayers(container, mapData, textures) {
    const { width, height, layers } = mapData;
    
    // Layer container per organizzare i layer
    const layersContainer = new PIXI.Container();
    container.addChild(layersContainer);
    
    // Disegna il pavimento predefinito se disponibile
    if (textures.floor) {
      this.drawDefaultFloor(layersContainer, width, height, textures.floor);
    }
    
    // Disegna gli strati della mappa
    if (layers && Array.isArray(layers)) {
      layers.forEach((layer, index) => {
        if (!layer.data || !Array.isArray(layer.data)) return;
        
        const layerContainer = this.drawLayer(
          layersContainer,
          layer.data,
          width,
          height,
          textures
        );
        
        // Aggiungi metadati al layer
        layerContainer.name = layer.name || `layer_${index}`;
        layerContainer.visible = layer.visible !== false;
        layerContainer.alpha = layer.opacity !== undefined ? layer.opacity : 1;
        
        // Proprietà specifiche per i layer
        if (layer.properties) {
          Object.keys(layer.properties).forEach(key => {
            layerContainer[key] = layer.properties[key];
          });
        }
      });
    }
    
    // Disegna la griglia (opzionale)
    this.drawGrid(layersContainer, width, height);
    
    return layersContainer;
  }
  
  /**
   * Crea uno sprite per un'entità
   * @param {string} type - Tipo di entità
   * @param {Object} entityData - Dati dell'entità
   * @param {Object} textures - Texture disponibili
   * @returns {PIXI.Sprite} - Sprite dell'entità
   */
  static createEntitySprite(type, entityData, textures) {
    try {
      // Usa la texture del tipo specifico o una generica di fallback
      const texture = textures[type] || textures.npc || PIXI.Texture.WHITE;
      
      // Crea lo sprite
      const sprite = new PIXI.Sprite(texture);
      
      // Imposta le proprietà dello sprite
      const tileSize = this.TILE_SIZE || 32;
      sprite.x = entityData.x * tileSize;
      sprite.y = entityData.y * tileSize;
      sprite.width = tileSize;
      sprite.height = tileSize;
      
      // Configura l'interattività
      sprite.interactive = true;
      sprite.buttonMode = true;
      
      // Aggiungi i dati dell'entità come metadati
      sprite.entityData = entityData;
      
      return sprite;
    } catch (error) {
      console.warn(`Errore nella creazione dello sprite per l'entità di tipo ${type}:`, error);
      
      // Crea uno sprite di fallback
      const fallbackSprite = new PIXI.Sprite(PIXI.Texture.WHITE);
      fallbackSprite.tint = 0xFF0000; // Colore rosso per evidenziare l'errore
      fallbackSprite.alpha = 0.5;
      
      // Imposta le proprietà minime dello sprite
      const tileSize = this.TILE_SIZE || 32;
      fallbackSprite.x = (entityData.x || 0) * tileSize;
      fallbackSprite.y = (entityData.y || 0) * tileSize;
      fallbackSprite.width = tileSize;
      fallbackSprite.height = tileSize;
      
      // Configura comunque l'interattività di base
      fallbackSprite.interactive = true;
      fallbackSprite.buttonMode = true;
      
      // Aggiungi i dati dell'entità come metadati
      fallbackSprite.entityData = entityData;
      
      return fallbackSprite;
    }
  }
  
  /**
   * Crea un'etichetta con il nome dell'entità
   * @param {string} text - Testo da mostrare
   * @param {number} x - Posizione X
   * @param {number} y - Posizione Y
   * @returns {PIXI.Text} - Oggetto Text creato
   */
  static createEntityLabel(text, x, y) {
    const style = new PIXI.TextStyle({
      fontFamily: 'Arial',
      fontSize: 12,
      fill: '#ffffff',
      stroke: '#000000',
      strokeThickness: 3,
      align: 'center'
    });
    
    const label = new PIXI.Text(text, style);
    label.anchor.set(0.5, 1); // Allinea il testo al centro-basso
    label.x = x;
    label.y = y;
    
    return label;
  }
  
  /**
   * Evidenzia un tile sulla mappa
   * @param {PIXI.Container} container - Container Pixi dove disegnare
   * @param {number} x - Coordinata X del tile
   * @param {number} y - Coordinata Y del tile
   * @param {number} color - Colore dell'evidenziazione
   * @param {number} alpha - Trasparenza dell'evidenziazione
   * @returns {PIXI.Graphics} - Oggetto grafico creato
   */
  static highlightTile(container, x, y, color = 0xffff00, alpha = 0.3) {
    const highlightGraphics = new PIXI.Graphics();
    highlightGraphics.beginFill(color, alpha);
    highlightGraphics.drawRect(
      x * TILE_SIZE,
      y * TILE_SIZE,
      TILE_SIZE,
      TILE_SIZE
    );
    highlightGraphics.endFill();
    
    container.addChild(highlightGraphics);
    return highlightGraphics;
  }
  
  /**
   * Centra la telecamera su una posizione specifica
   * @param {PIXI.Viewport} viewport - Viewport Pixi
   * @param {number} x - Coordinata X in tile
   * @param {number} y - Coordinata Y in tile
   */
  static centerCamera(viewport, x, y) {
    if (!viewport) return;
    
    // Converti le coordinate da tile a pixel
    const pixelX = x * TILE_SIZE + TILE_SIZE / 2;
    const pixelY = y * TILE_SIZE + TILE_SIZE / 2;
    
    // Centra il viewport su quelle coordinate
    viewport.moveCenter(pixelX, pixelY);
    
    // Opzionalmente, applica una breve animazione per rendere lo spostamento più fluido
    if (viewport.plugins && viewport.plugins.animate) {
      viewport.plugins.animate.to({
        position: { x: pixelX, y: pixelY },
        time: 300, // Durata in ms
        ease: 'easeInOutSine' // Funzione di easing
      });
    }
  }
  
  /**
   * Costante per la dimensione dei tile
   * @type {number}
   */
  static get TILE_SIZE() {
    return TILE_SIZE;
  }
} 