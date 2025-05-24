/**
 * TileAtlas.js
 * Gestisce l'atlante delle texture dei tile per l'OptimizedMapRenderer
 */
import * as PIXI from 'pixi.js';

export default class TileAtlas {
  constructor() {
    this.textures = {}; // Mappa delle texture per tipo di tile
    this.initialized = false;
    this.fallbackTexture = null;
    
    // Configurazione colori per le texture di fallback
    this.tileColors = {
      floor: 0x555555,  // pavimento - grigio
      1: 0x333333,      // muri - grigio scuro
      wall: 0x333333,   // muri - grigio scuro
      2: 0x8B4513,      // porte - marrone
      door: 0x8B4513,   // porte - marrone
      3: 0x00FF00,      // erba - verde
      grass: 0x00FF00,  // erba - verde
      4: 0x0000FF,      // acqua - blu
      water: 0x0000FF,  // acqua - blu
      5: 0xFFD700,      // oggetti - oro
      item: 0xFFD700,   // oggetti - oro
      npc: 0x0000FF,    // NPC - blu
      player: 0xFF0000, // giocatore - rosso
      default: 0x555555 // default - grigio
    };
  }
  
  /**
   * Inizializza l'atlante delle texture
   * @returns {Promise<boolean>} - true se l'inizializzazione è riuscita
   */
  async initialize() {
    if (this.initialized) return true;
    
    try {
      // Crea texture di fallback di base
      this.fallbackTexture = PIXI.Texture.WHITE;
      
      // Cerca di caricare lo spritesheet se esiste
      const success = await this.loadSpritesheet();
      
      // Se non abbiamo caricato correttamente lo spritesheet, crea texture di fallback
      if (!success || Object.keys(this.textures).length === 0) {
        console.log("Utilizzo texture di fallback per tutti i tile");
        this.createFallbackTextures();
      }
      
      // Verifica che tutte le texture essenziali siano disponibili
      this.ensureEssentialTextures();
      
      this.initialized = true;
      return true;
    } catch (error) {
      console.error("Errore nell'inizializzazione del TileAtlas:", error);
      
      // In caso di errore, usa texture di fallback
      this.createFallbackTextures();
      this.ensureEssentialTextures();
      this.initialized = true;
      return false;
    }
  }
  
  /**
   * Assicura che tutte le texture essenziali siano disponibili
   */
  ensureEssentialTextures() {
    const essentialTypes = ['floor', 'wall', 'door', 'grass', 'water', 'default', 0, 1, 2, 3, 4, 5];
    
    essentialTypes.forEach(type => {
      if (!this.textures[type]) {
        // Se manca una texture essenziale, crea una texture di fallback
        const color = this.tileColors[type] || this.tileColors.default;
        this.textures[type] = this.createColorTexture(color);
        console.log(`Creata texture di fallback per tipo '${type}'`);
      }
    });
  }
  
  /**
   * Carica lo spritesheet dei tile
   * @returns {Promise<boolean>} - true se il caricamento è riuscito
   */
  async loadSpritesheet() {
    return new Promise((resolve) => {
      try {
        // Percorso dello spritesheet (senza slash finale)
        const basePath = '/assets/fallback/spritesheets';
        const spritesheetPath = `tiles.json`;
        
        // Prova a caricare direttamente lo spritesheet JSON, senza controllo preventivo dell'immagine
        const loader = new PIXI.Loader();
        
        // Imposta il percorso base per le risorse
        loader.baseUrl = basePath;
        
        loader
          .add('tiles', spritesheetPath)
          .load((loader, resources) => {
            if (resources.tiles && resources.tiles.spritesheet && 
                resources.tiles.spritesheet.textures && 
                Object.keys(resources.tiles.spritesheet.textures).length > 0) {
              
              // Estrai le texture dallo spritesheet
              const spritesheet = resources.tiles.spritesheet;
              this.textures = { ...spritesheet.textures };
              
              // Configura le texture per i tipi di tile numerici
              this.textures[0] = this.textures['floor.png'] || this.fallbackTexture;
              this.textures[1] = this.textures['wall.png'] || this.fallbackTexture;
              this.textures[2] = this.textures['door.png'] || this.fallbackTexture;
              this.textures[3] = this.textures['grass.png'] || this.fallbackTexture;
              this.textures[4] = this.textures['water.png'] || this.fallbackTexture;
              this.textures[5] = this.textures['item.png'] || this.fallbackTexture;
              
              console.log("Spritesheet dei tile caricato con successo");
              resolve(true);
            } else {
              console.warn("Spritesheet dei tile non trovato o non valido, utilizzo texture di fallback");
              // Se non riusciamo a caricare lo spritesheet o le sue texture, passiamo alle texture di fallback
              this.createFallbackTextures();
              resolve(false);
            }
          })
          .onError.add(() => {
            console.warn("Errore nel caricamento dello spritesheet dei tile, utilizzo texture di fallback");
            this.createFallbackTextures();
            resolve(false);
          });
      } catch (error) {
        console.error("Errore critico nel caricamento dello spritesheet:", error);
        this.createFallbackTextures();
        resolve(false);
      }
    });
  }
  
  /**
   * Crea texture colorate di fallback per ogni tipo di tile
   */
  createFallbackTextures() {
    console.log("Creazione texture di fallback per i tile");
    
    // Crea texture per ogni tipo di tile
    for (const [key, color] of Object.entries(this.tileColors)) {
      this.textures[key] = this.createColorTexture(color);
    }
  }
  
  /**
   * Crea una texture colorata
   * @param {number} color - Colore della texture in formato esadecimale
   * @returns {PIXI.Texture} - La texture creata
   */
  createColorTexture(color) {
    try {
      // Approccio semplificato: crea una texture base e assegna il colore
      const canvas = document.createElement('canvas');
      canvas.width = 64;
      canvas.height = 64;
      
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        console.warn("Impossibile ottenere il contesto 2D del canvas, utilizzo texture bianca");
        return PIXI.Texture.WHITE;
      }
      
      // Converti il colore esadecimale in RGB
      const r = (color >> 16) & 0xFF;
      const g = (color >> 8) & 0xFF;
      const b = color & 0xFF;
      
      // Riempi il canvas con il colore
      ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
      ctx.fillRect(0, 0, 64, 64);
      
      // Crea la texture dal canvas
      return PIXI.Texture.from(canvas);
    } catch (error) {
      console.error("Errore critico nella creazione della texture colorata:", error);
      return PIXI.Texture.WHITE;
    }
  }
  
  /**
   * Ottiene la texture per un tipo di tile
   * @param {string|number} tileType - Tipo di tile
   * @returns {PIXI.Texture} - La texture corrispondente o una texture di fallback
   */
  getTexture(tileType) {
    // Se la texture è disponibile, restituiscila
    if (this.textures[tileType]) {
      return this.textures[tileType];
    }
    
    // Se tileType è numerico, prova a interpretarlo
    if (typeof tileType === 'number' || !isNaN(parseInt(tileType))) {
      const tileId = parseInt(tileType);
      if (this.textures[tileId]) {
        return this.textures[tileId];
      }
      
      // Mappa i tipi numerici alle texture appropriate
      switch (tileId) {
        case 0: return this.textures.floor || this.fallbackTexture;
        case 1: return this.textures.wall || this.fallbackTexture;
        case 2: return this.textures.door || this.fallbackTexture;
        case 3: return this.textures.grass || this.fallbackTexture;
        case 4: return this.textures.water || this.fallbackTexture;
        case 5: return this.textures.item || this.fallbackTexture;
        default: return this.textures.default || this.fallbackTexture;
      }
    }
    
    // Usa una texture di fallback generica
    return this.textures.default || this.fallbackTexture;
  }
  
  /**
   * Ottiene tutte le texture disponibili
   * @returns {Object} - Mappa di tutte le texture
   */
  getAllTextures() {
    return this.textures;
  }
  
  /**
   * Distrugge e libera le risorse
   */
  dispose() {
    // Distruggi tutte le texture create (solo quelle che non fanno parte di uno spritesheet)
    for (const key in this.textures) {
      // Solo le texture create manualmente dovrebbero essere distrutte
      if (this.textures[key] !== this.fallbackTexture && this.textures[key].destroy) {
        this.textures[key].destroy(true);
      }
    }
    
    this.textures = {};
    this.initialized = false;
  }
}