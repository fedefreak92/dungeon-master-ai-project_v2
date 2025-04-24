/**
 * TileAtlas.js
 * Sistema di gestione per texture atlas di tile mappe
 * Ottimizzazione per il batching di rendering in Pixi.js
 */
import * as PIXI from 'pixi.js';

// Dimensione standard di un tile
const TILE_SIZE = 64;

/**
 * Classe per gestire un atlas di texture per le mappe
 */
export default class TileAtlas {
  constructor() {
    this.atlasTexture = null;       // BaseTexture dell'atlas
    this.tileTextures = {};         // Mappa delle texture dei tile
    this.isInitialized = false;     // Flag di inizializzazione
    this.tilesPerRow = 4;           // Numero di tile per riga nell'atlas
    this.tilesTotal = 16;           // Numero totale di tile nell'atlas
  }

  /**
   * Inizializza l'atlas di texture
   * @param {Object} options - Opzioni di configurazione
   * @returns {Promise<boolean>} - true se l'inizializzazione è riuscita
   */
  async initialize(options = {}) {
    if (this.isInitialized) return true;

    try {
      // Configurazione predefinita
      const config = {
        tileSize: options.tileSize || TILE_SIZE,
        tilesPerRow: options.tilesPerRow || 4,
        tilesTotal: options.tilesTotal || 16,
        baseColor: options.baseColor || 0x555555
      };
      
      this.tilesPerRow = config.tilesPerRow;
      this.tilesTotal = config.tilesTotal;
      this.tileSize = config.tileSize;
      
      // Calcola dimensioni dell'atlas
      const atlasWidth = config.tileSize * config.tilesPerRow;
      const atlasHeight = config.tileSize * Math.ceil(config.tilesTotal / config.tilesPerRow);
      
      // Crea l'atlas come una texture unica
      await this.createAtlasTexture(atlasWidth, atlasHeight, config.baseColor);
      
      // Crea le singole texture per ogni tile
      this.createTileTextures();
      
      this.isInitialized = true;
      console.log(`TileAtlas inizializzato: ${config.tilesTotal} tile (${atlasWidth}x${atlasHeight}px)`);
      
      return true;
    } catch (error) {
      console.error("Errore nell'inizializzazione dell'atlas:", error);
      return false;
    }
  }
  
  /**
   * Crea la texture base dell'atlas
   * @param {number} width - Larghezza in pixel
   * @param {number} height - Altezza in pixel
   * @param {number} baseColor - Colore di base
   */
  async createAtlasTexture(width, height, baseColor) {
    // Crea un canvas per disegnare l'atlas
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');
    
    // Riempie con il colore di base
    ctx.fillStyle = `#${baseColor.toString(16).padStart(6, '0')}`;
    ctx.fillRect(0, 0, width, height);
    
    // Definizione dei colori per diversi tipi di tile
    const tileColors = [
      '#555555', // pavimento - grigio (0)
      '#333333', // muri - grigio scuro (1)
      '#8B4513', // porte - marrone (2)
      '#00FF00', // erba - verde (3)
      '#0000FF', // acqua - blu (4)
      '#FFD700', // oggetti - oro (5)
      '#FF00FF', // casella speciale - magenta (6)
      '#00FFFF', // ghiaccio - ciano (7)
      '#FF0000', // lava - rosso (8)
      '#663399', // portale - viola (9)
      '#A0522D', // ponte - marrone chiaro (10)
      '#FFFF00', // sabbia - giallo (11)
      '#708090', // pietra - grigio blu (12)
      '#2F4F4F', // roccia - grigio scuro verde (13)
      '#CD853F', // legno - marrone chiaro (14)
      '#696969'  // metallo - grigio medio (15)
    ];
    
    // Disegna i tile nell'atlas
    for (let i = 0; i < this.tilesTotal; i++) {
      const row = Math.floor(i / this.tilesPerRow);
      const col = i % this.tilesPerRow;
      
      const x = col * this.tileSize;
      const y = row * this.tileSize;
      
      // Colore del tile
      ctx.fillStyle = tileColors[i] || tileColors[0];
      ctx.fillRect(x, y, this.tileSize, this.tileSize);
      
      // Bordo del tile per debugging
      ctx.strokeStyle = '#FFFFFF';
      ctx.lineWidth = 1;
      ctx.strokeRect(x, y, this.tileSize, this.tileSize);
      
      // Numero del tile per debugging
      ctx.fillStyle = '#FFFFFF';
      ctx.font = `${Math.floor(this.tileSize/3)}px Arial`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(i.toString(), x + this.tileSize/2, y + this.tileSize/2);
    }
    
    // Crea una texture dal canvas
    this.atlasTexture = PIXI.BaseTexture.from(canvas);
    
    return this.atlasTexture;
  }
  
  /**
   * Crea le singole texture per ogni tile a partire dall'atlas
   */
  createTileTextures() {
    // Verifica che l'atlas sia stato creato
    if (!this.atlasTexture) {
      console.error("Atlas texture non inizializzata");
      return;
    }
    
    // Crea una texture per ogni tile
    for (let i = 0; i < this.tilesTotal; i++) {
      const row = Math.floor(i / this.tilesPerRow);
      const col = i % this.tilesPerRow;
      
      const x = col * this.tileSize;
      const y = row * this.tileSize;
      
      // Crea un frame per questa texture
      const rect = new PIXI.Rectangle(x, y, this.tileSize, this.tileSize);
      
      // Crea la texture dal frame
      const texture = new PIXI.Texture(this.atlasTexture, rect);
      
      // Memorizza la texture
      this.tileTextures[i] = texture;
      
      // Aggiunge anche mappature per nomi comuni
      if (i === 0) this.tileTextures['floor'] = texture;
      if (i === 1) this.tileTextures['wall'] = texture;
      if (i === 2) this.tileTextures['door'] = texture;
      if (i === 3) this.tileTextures['grass'] = texture;
      if (i === 4) this.tileTextures['water'] = texture;
      if (i === 5) this.tileTextures['item'] = texture;
    }
  }
  
  /**
   * Ottiene una texture per un tipo di tile
   * @param {number|string} tileType - Tipo di tile (indice o nome)
   * @returns {PIXI.Texture} - La texture richiesta o una texture di fallback
   */
  getTexture(tileType) {
    // Se è una stringa, cerca la texture per nome
    if (typeof tileType === 'string') {
      return this.tileTextures[tileType] || this.tileTextures[0] || PIXI.Texture.WHITE;
    }
    
    // Se è un numero, cerca la texture per indice
    return this.tileTextures[tileType] || this.tileTextures[0] || PIXI.Texture.WHITE;
  }
  
  /**
   * Pulisce le risorse allocate dall'atlas
   */
  dispose() {
    try {
      // Distrugge le texture dei singoli tile
      Object.values(this.tileTextures).forEach(texture => {
        if (texture && texture !== PIXI.Texture.WHITE && texture.destroy) {
          texture.destroy(false); // Non distruggere la base texture
        }
      });
      
      // Reset dell'array delle texture
      this.tileTextures = {};
      
      // Distrugge la texture dell'atlas
      if (this.atlasTexture && this.atlasTexture.destroy) {
        this.atlasTexture.destroy(true);
        this.atlasTexture = null;
      }
      
      this.isInitialized = false;
      console.log("TileAtlas distrutto con successo");
    } catch (error) {
      console.error("Errore nella pulizia del TileAtlas:", error);
    }
  }
} 