/**
 * PixiManager.js
 * Singleton che gestisce tutte le risorse PIXI.js per l'intera applicazione
 * Versione riprogettata con architettura modulare
 */
import * as PIXI from 'pixi.js';
import PixiBase from './core/PixiBase';
import SceneManager from './core/SceneManager';
import EntityManager from './entities/EntityManager';
import GridMapRenderer from './utils/GridMapRenderer';
import SpriteSheetManager from './utils/SpriteSheetManager';
import AssetLoader from './utils/AssetLoader';
import FilterManager from './utils/FilterManager';

/**
 * Singleton che gestisce tutte le risorse PIXI.js per l'intera applicazione
 * Risolve i problemi di ciclo di vita tra React e PIXI.js
 */
class PixiManager {
  constructor() {
    // Istanza base PIXI
    this.pixiBase = new PixiBase();
    
    // Gestori specifici
    this.sceneManager = new SceneManager();
    this.entityManager = EntityManager;
    
    // Renderer mappe (ora utilizziamo GridMapRenderer)
    this.mapRenderers = new Map();
    
    // Tracciamento degli sprite delle entità e del giocatore
    this.entitySprites = new Map();
    this.playerSprites = new Map();
    
    // Memorizza le scene attive
    this.activeScenes = new Map();
    
    // Riferimenti diretti
    this.app = null;
    this.textures = {};
    this.renderMode = 'auto'; // 'auto', 'webgl', o 'canvas'
    
    // Binding dei metodi
    this.handleResize = this.handleResize.bind(this);
  }
  
  /**
   * Inizializza il manager PIXI, chiamare una sola volta all'avvio dell'app
   * @param {Object} options - Opzioni di configurazione per PIXI.Application
   * @returns {PIXI.Application} - L'istanza dell'applicazione PIXI
   */
  initialize(options = {}) {
    // Imposta il render mode
    this.pixiBase.renderMode = this.renderMode;
    
    // Inizializza l'applicazione PIXI
    this.app = this.pixiBase.initialize(options);
    
    // Precarica le texture comuni
    this.preloadCommonTextures();
    
    // Aggiungi un event listener per il ridimensionamento della finestra
    window.addEventListener('resize', this.handleResize);
    
    return this.app;
  }
  
  /**
   * Gestisce il ridimensionamento della finestra
   */
  handleResize() {
    // Ridimensiona tutti i renderer di mappa attivi
    for (const [sceneId, renderer] of this.mapRenderers) {
      if (renderer && typeof renderer.resize === 'function') {
        renderer.resize();
      }
    }
  }
  
  /**
   * Precarica le texture comuni usate in tutto il gioco
   * Usa AssetLoader e SpriteSheetManager per la gestione delle texture
   */
  async preloadCommonTextures() {
    try {
      console.log("PreloadCommonTextures: Inizio caricamento texture.");
      
      // Inizializza il sistema di asset
      await AssetLoader.initialize();
      
      // Carica le texture dall'AssetLoader
      const textures = await AssetLoader.preloadEssentialTextures();
      if (textures) {
        // Copia le texture
        this.textures = textures;
        
        console.log("Texture caricate con successo:", Object.keys(this.textures).length, "textures");
      } else {
        console.error("Errore nel caricamento delle texture di base");
      }
    } catch (error) {
      console.error("Errore durante preloadCommonTextures:", error);
    }
  }

  /**
   * Crea una nuova scena PIXI specifica per un componente React
   * @param {HTMLElement} container - L'elemento DOM container
   * @param {Object} options - Opzioni di configurazione (sceneId, width, height, backgroundColor)
   * @returns {PIXI.Application|null} - L'istanza dell'applicazione o null in caso di errore
   */
  createScene(container, options = {}) {
    const sceneId = options.sceneId || 'default';
    console.log(`createScene: Creating scene with ID ${sceneId}`);
    
    const scene = this.sceneManager.createScene(container, options);
    
    if (scene) {
      // Assegna esplicitamente lo sceneId all'applicazione per assicurare la coerenza
      scene.name = sceneId;
      scene._pixiManagerSceneId = sceneId; // Proprietà dedicata per evitare conflitti
      
      this.activeScenes.set(sceneId, scene);
      console.log(`createScene: Scene ${sceneId} created successfully and stored in activeScenes`);
      
      // Aggiungi gli eventi di resize al container
      if (scene.view && scene.view.parentElement) {
        const resizeObserver = new ResizeObserver(() => {
          this.handleResize();
        });
        resizeObserver.observe(scene.view.parentElement);
      }
    }
    
    return scene;
  }
  
  /**
   * Renderizza una mappa in una scena specifica usando il nuovo GridMapRenderer
   * @param {PIXI.Application} app - Oggetto scena creato con createScene
   * @param {Object} mapData - Dati della mappa da renderizzare
   * @returns {boolean} - true se il rendering è riuscito
   */
  renderMap(app, mapData) {
    if (!app || !mapData) {
      console.error("App o dati mappa mancanti");
      return false;
    }
    
    try {
      // Recupera l'ID della scena in modo più affidabile
      const sceneId = app._pixiManagerSceneId || app.name || 'default';
      console.log(`renderMap: Inizio rendering mappa per scena ${sceneId}`);
      
      // DEBUG: Stampa tutte le chiavi attuali nella mappa
      console.log(`renderMap: Current mapRenderers keys:`, Array.from(this.mapRenderers.keys()));
      
      // Assicuriamoci che ci sia un viewport
      let viewport = app.stage.getChildByName('map-viewport');
      if (!viewport) {
        viewport = new PIXI.Container();
        viewport.name = 'map-viewport';
        app.stage.addChild(viewport);
      }
      
      // Inizializza il renderer della griglia se non esiste già
      let renderer;
      if (!this.mapRenderers.has(sceneId)) {
        console.log(`renderMap: Creazione nuovo GridMapRenderer per scena ${sceneId}`);
        const gridRenderer = new GridMapRenderer();
        gridRenderer.initialize(app, viewport);
        
        // Assicuriamoci che venga memorizzato correttamente
        this.mapRenderers.delete(sceneId); // Rimuovi eventuali entry precedenti
        this.mapRenderers.set(sceneId, gridRenderer);
        renderer = gridRenderer;
        
        // DEBUG: Verifica immediata che il renderer sia stato memorizzato
        console.log(`renderMap: Verifica che il renderer sia stato memorizzato: ${this.mapRenderers.has(sceneId)}`);
      } else {
        console.log(`renderMap: Utilizzo GridMapRenderer esistente per scena ${sceneId}`);
        renderer = this.mapRenderers.get(sceneId);
      }
      
      // Verifica che il renderer sia stato creato correttamente
      if (!renderer) {
        console.error(`renderMap: Impossibile inizializzare renderer per scena ${sceneId}`);
        return false;
      }
      
      // Log esplicito della presenza del renderer nella mappa
      console.log(`renderMap: Renderer creato e inserito correttamente in mapRenderers per scena ${sceneId}`);
      console.log(`renderMap: mapRenderers contiene ${this.mapRenderers.size} renderer`);
      console.log(`renderMap: Chiavi attuali:`, Array.from(this.mapRenderers.keys()));
      
      // Carica la mappa con il renderer
      renderer.loadMap(mapData);
      
      // Carica le entità (oggetti e NPG) dalla mappa
      this.loadEntitiesFromMap(sceneId, mapData);
      
      // Assicurati che la mappa sia correttamente dimensionata e centrata
      renderer.resize();
      
      console.log(`renderMap: Completato rendering mappa per scena ${sceneId}`);
      return true;
    } catch (error) {
      console.error("Errore nel rendering della mappa:", error);
      return false;
    }
  }
  
  /**
   * Carica le entità presenti nella mappa
   * @param {string} sceneId - ID della scena
   * @param {Object} mapData - Dati della mappa
   */
  loadEntitiesFromMap(sceneId, mapData) {
    const renderer = this.mapRenderers.get(sceneId);
    if (!renderer) return;
    
    // Carica gli NPC
    if (mapData.npg) {
      Object.entries(mapData.npg).forEach(([position, npc]) => {
        // Estrai coordinate dalla stringa [x, y]
        const match = position.match(/\[(\d+),\s*(\d+)\]/);
        if (!match) return;
        
        const x = parseInt(match[1], 10);
        const y = parseInt(match[2], 10);
        
        // Aggiungi l'NPC alla mappa
        renderer.addEntity(
          `npc-${npc.nome}`,
          'npc',
          {
            x,
            y,
            nome: npc.nome,
            spriteUrl: `assets/entities/${npc.sprite || 'npc_default'}.png`
          }
        );
    
        // Memorizza lo sprite per riferimento futuro
        this.entitySprites.set(`${sceneId}-npc-${npc.nome}`, {
          x,
          y,
          type: 'npc',
          data: npc
        });
      });
    }
    
    // Carica gli oggetti
    if (mapData.oggetti) {
      Object.entries(mapData.oggetti).forEach(([position, object]) => {
        // Estrai coordinate dalla stringa [x, y]
        const match = position.match(/\[(\d+),\s*(\d+)\]/);
        if (!match) return;
        
        const x = parseInt(match[1], 10);
        const y = parseInt(match[2], 10);
        
        // Aggiungi l'oggetto alla mappa
        renderer.addEntity(
          `object-${object.nome}`,
          'object',
          {
            x,
            y,
            nome: object.nome,
            spriteUrl: `assets/objects/${object.sprite || 'default_object'}.png`
          }
        );
        
        // Memorizza lo sprite per riferimento futuro
        this.entitySprites.set(`${sceneId}-object-${object.nome}`, {
          x,
          y,
          type: 'object',
          data: object
        });
      });
    }
  }
  
  /**
   * Aggiunge lo sprite del giocatore alla scena
   * @param {PIXI.Application} scene - Oggetto scena creato con createScene
   * @param {number} x - Coordinata X in tile
   * @param {number} y - Coordinata Y in tile
   * @returns {PIXI.Sprite} - Lo sprite del giocatore
   */
  addPlayer(scene, x, y) {
    const sceneId = scene.name || 'default';
    const renderer = this.mapRenderers.get(sceneId);
    
    if (!renderer) {
      console.error(`Renderer non trovato per la scena ${sceneId}`);
      return null;
    }
    
    // Crea lo sprite del giocatore
    const playerSprite = renderer.addEntity(
      'player',
      'player',
      {
        x,
        y,
        nome: 'Giocatore',
        spriteUrl: 'assets/entities/player.png'
      }
    );
    
    // Memorizza lo sprite del giocatore
    this.playerSprites.set(sceneId, {
      sprite: playerSprite,
      x,
      y
    });
    
    // Centra la visuale sul giocatore
    renderer.centerOnEntity('player');
    
    return playerSprite;
  }
  
  /**
   * Ottiene il renderer associato a una scena in modo affidabile
   * @param {string} sceneId - ID della scena
   * @returns {GridMapRenderer|null} - Il renderer della mappa o null se non trovato
   */
  getMapRenderer(sceneId) {
    if (!sceneId || !this.mapRenderers) {
      console.warn(`getMapRenderer: Parametri invalidi, sceneId=${sceneId}, mapRenderers esistente=${!!this.mapRenderers}`);
      return null;
    }
    
    // Controllo diretto
    if (this.mapRenderers.has(sceneId)) {
      return this.mapRenderers.get(sceneId);
    }
    
    // Tentativo di ricerca con strategie alternative
    console.warn(`getMapRenderer: Renderer non trovato direttamente per sceneId=${sceneId}, tento ricerca alternativa`);
    
    // 1. Verifica se c'è un renderer con un nome simile
    for (const [key, renderer] of this.mapRenderers.entries()) {
      // Corrispondenza parziale (es. se ci sono spazi o caratteri extra)
      if (key.includes(sceneId) || sceneId.includes(key)) {
        console.warn(`getMapRenderer: Trovata corrispondenza parziale ${key} per ${sceneId}`);
        return renderer;
      }
    }
    
    // 2. Se abbiamo una sola scena attiva, supponiamo sia quella cercata
    if (this.mapRenderers.size === 1) {
      const firstKey = Array.from(this.mapRenderers.keys())[0];
      const firstRenderer = this.mapRenderers.get(firstKey);
      console.warn(`getMapRenderer: Solo un renderer disponibile (${firstKey}), lo uso per ${sceneId}`);
      return firstRenderer;
    }
    
    console.error(`getMapRenderer: Renderer non trovato per ${sceneId}`);
    console.error(`getMapRenderer: Renderer disponibili:`, Array.from(this.mapRenderers.keys()));
    return null;
  }
  
  /**
   * Aggiorna la posizione del giocatore
   * @param {string} sceneId - ID della scena
   * @param {number} x - Nuova coordinata X in tile
   * @param {number} y - Nuova coordinata Y in tile
   */
  updatePlayerPosition(sceneId, x, y) {
    const renderer = this.getMapRenderer(sceneId);
    if (!renderer) {
      console.warn(`updatePlayerPosition: Renderer per scena ${sceneId} non trovato`);
      return;
    }
    
    // Aggiorna la posizione
    renderer.updateEntityPosition('player', x, y);
    
    // Aggiorna la posizione memorizzata
    if (this.playerSprites.has(sceneId)) {
      const playerData = this.playerSprites.get(sceneId);
      playerData.x = x;
      playerData.y = y;
    }
  }
  
  /**
   * Aggiorna le entità sulla mappa
   * @param {string} sceneId - ID della scena
   * @param {Array} entities - Array di entità da renderizzare
   * @param {number} retryCount - Contatore di tentativi per i retry, default 0
   * @returns {boolean} - true se l'aggiornamento è riuscito
   */
  updateEntities(sceneId, entities, retryCount = 0) {
    const MAX_RETRIES = 5;
    
    // DEBUG: Log dettagliati per debug
    console.log(`updateEntities: Tentativo di aggiornare entità per scena ${sceneId}`);
    console.log(`updateEntities: Chiavi disponibili in mapRenderers:`, Array.from(this.mapRenderers.keys()));
    
    // Prova a ottenere il renderer con il metodo affidabile
    const renderer = this.getMapRenderer(sceneId);
    
    // Controlla se il renderer esiste
    if (!renderer) {
      console.warn(`updateEntities: Renderer per scena ${sceneId} non trovato (tentativo ${retryCount + 1}/${MAX_RETRIES + 1})`);
      
      // Se abbiamo raggiunto il numero massimo di tentativi, rinuncia
      if (retryCount >= MAX_RETRIES) {
        console.error(`updateEntities: Impossibile aggiornare entità dopo ${MAX_RETRIES + 1} tentativi`);
        
        // DEBUG: Stampa tutte le chiavi disponibili per aiutare nel debug
        if (this.mapRenderers) {
          console.error(`updateEntities: mapRenderers contiene ${this.mapRenderers.size} renderer con chiavi:`, 
                        Array.from(this.mapRenderers.keys()));
        }
        
        return false;
      }
      
      // Altrimenti, riprova dopo un breve ritardo con delay esponenziale
      const delay = Math.min(300 * Math.pow(1.5, retryCount), 2000); // Max 2 secondi di delay
      console.log(`updateEntities: Riprovo tra ${delay}ms...`);
      
      setTimeout(() => {
        this.updateEntities(sceneId, entities, retryCount + 1);
      }, delay);
      
      return false;
    }
    
    console.log(`updateEntities: Renderer trovato per scena ${sceneId}`);
    
    if (!entities || !Array.isArray(entities)) {
      console.warn('updateEntities: Nessuna entità da aggiornare');
      return true; // Non è un errore, solo niente da fare
    }
    
    console.log(`updateEntities: Aggiornamento di ${entities.length} entità sulla mappa ${sceneId}`);
    
    try {
      // Rimuovi entità non più presenti
      const currentEntityIds = new Set();
      
      entities.forEach(entity => {
        const entityId = `${entity.type}-${entity.id || entity.nome}`; // Assicurati un ID univoco
        currentEntityIds.add(entityId);
        
        // Determina lo sprite corretto per gli oggetti
        let spriteName = entity.sprite;
        if (entity.type === 'object' && (spriteName === 'furniture' || spriteName === 'chest')) {
          spriteName = entity.nome; // Usa il nome dell'oggetto come nome del file
        }
        
        // Aggiorna o aggiungi l'entità
        if (renderer.sprites && renderer.sprites.entities && renderer.sprites.entities[entityId]) {
          // Aggiorna la posizione se necessario
          renderer.updateEntityPosition(entityId, entity.x, entity.y);
        } else {
          // Aggiungi una nuova entità
          renderer.addEntity(
            entityId,
            entity.type,
            {
              x: entity.x,
              y: entity.y,
              nome: entity.nome || entity.name,
              // Usa spriteName determinato sopra per gli oggetti
              spriteUrl: `assets/${entity.type === 'npc' ? 'entities' : 'objects'}/${spriteName || (entity.type === 'npc' ? 'npc_default' : 'default_object')}.png`
            }
          );
        }
      });
      
      // Rimuovi entità non più presenti, escludendo il giocatore
      if (renderer.sprites && renderer.sprites.entities) {
        let performRemoval = true;
        // Se l'array di entità ricevuto è vuoto, non eseguire la rimozione.
        // Questo previene la cancellazione delle entità caricate da loadEntitiesFromMap
        // a causa di una chiamata iniziale a updateEntities con una lista vuota.
        if (Array.isArray(entities) && entities.length === 0) {
            console.log("[PixiManager.updateEntities] Ricevuto array di entità vuoto. Si salta la fase di rimozione per preservare le entità caricate inizialmente.");
            performRemoval = false;
        }

        if (performRemoval) {
            for (const entityId in renderer.sprites.entities) {
              if (entityId !== 'player' && !currentEntityIds.has(entityId)) {
                renderer.removeEntity(entityId);
              }
            }
        }
      }
      
      console.log(`updateEntities: Aggiornamento completato per ${sceneId}`);
      return true;
    } catch (error) {
      console.error(`updateEntities: Errore durante l'aggiornamento delle entità:`, error);
      return false;
    }
  }
  
  /**
   * Pulisce una specifica scena PIXI rimuovendo l'app e le sue risorse
   * @param {string} id - L'ID della scena da pulire (es. 'map_scene_taverna')
   */
  cleanupScene(id) {
    console.log(`Pulizia scena: ${id}`);
    
    // Pulisci il renderer della mappa
    if (this.mapRenderers.has(id)) {
      const renderer = this.mapRenderers.get(id);
      renderer.destroy();
      this.mapRenderers.delete(id);
    }
    
    // Rimuovi riferimenti agli sprite delle entità
    for (const key of [...this.entitySprites.keys()]) {
      if (key.startsWith(`${id}-`)) {
        this.entitySprites.delete(key);
      }
    }
    
    // Rimuovi riferimento allo sprite del giocatore
    this.playerSprites.delete(id);
    
    // Rimuovi la scena dal gestore
    this.sceneManager.cleanupScene(id);
    
    // Rimuovi la scena attiva
    this.activeScenes.delete(id);
  }
  
  /**
   * Ottiene una texture dal cache
   * @param {string} name - Nome della texture
   * @returns {PIXI.Texture} - La texture richiesta o una texture di fallback
   */
  getTexture(name) {
    // Prima cerca nella cache locale
    if (this.textures[name]) {
      return this.textures[name];
    }
    
    // Poi cerca nelle spritesheet
    const sheetNames = ['entities', 'tiles', 'ui'];
    for (const sheet of sheetNames) {
      if (SpriteSheetManager.isSpriteSheetLoaded(sheet)) {
        const texture = SpriteSheetManager.getTexture(sheet, name);
        if (texture && texture !== PIXI.Texture.WHITE) {
          return texture;
        }
      }
    }
    
    console.warn(`getTexture: Texture '${name}' non trovata, uso fallback`);
    return PIXI.Texture.WHITE;
  }
  
  /**
   * Pulisce tutte le risorse PIXI e prepara la distruzione del manager
   */
  cleanup() {
    console.log('[PixiManager] cleanup: Inizio pulizia globale di tutte le risorse PIXI.');
    
    // Rimuovi l'event listener per il ridimensionamento
    window.removeEventListener('resize', this.handleResize);
    
    // Pulisci tutti i renderer delle mappe
    for (const [sceneId, renderer] of this.mapRenderers) {
      renderer.destroy();
    }
    this.mapRenderers.clear();
    
    // Pulisci le tracce degli sprite
    this.entitySprites.clear();
    this.playerSprites.clear();
    
    // Pulisci tutte le scene
    this.sceneManager.cleanupAllScenes();
    this.activeScenes.clear();
    
    // Pulisci le texture tramite AssetLoader
    AssetLoader.clearCache(true);
    
    // Pulisci l'app PIXI
    if (this.app) {
      try {
        // Usa FilterManager per preparare la distruzione
        FilterManager.prepareForDestruction(this.app);
        this.pixiBase.cleanup();
        this.app = null;
      } catch (err) {
        console.error('[PixiManager] cleanup: Errore durante la pulizia dell\'app PIXI:', err);
      }
    }
    
    this.textures = {};
    console.log('[PixiManager] cleanup: Pulizia globale completata');
  }
}

// Export dell'istanza singleton
const pixiManager = new PixiManager();
export { pixiManager };
export default pixiManager; 