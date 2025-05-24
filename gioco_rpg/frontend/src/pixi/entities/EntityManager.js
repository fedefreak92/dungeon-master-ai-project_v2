/**
 * EntityManager.js
 * Gestisce le entità di gioco come giocatore, NPC e altri oggetti interattivi
 */
import * as PIXI from 'pixi.js';
// Importazione con handling di errore per GlowFilter
let GlowFilter;
try {
  // Tenta di importare GlowFilter
  GlowFilter = require('pixi-filters').GlowFilter;
} catch (err) {
  console.warn('Impossibile importare GlowFilter da pixi-filters:', err);
  // Fallback a un filtro di base se GlowFilter non è disponibile
  GlowFilter = null;
}

class EntityManager {
  constructor() {
    if (EntityManager.instance) {
      return EntityManager.instance;
    }
    this.playerSprites = new Map(); // Memorizza gli sprite dei giocatori per ogni scena
    this.entitySprites = new Map(); // Memorizza gli sprite delle entità per ogni scena
    this.TILE_SIZE = 64; // Dimensione standard di un tile
    EntityManager.instance = this;
  }
  
  /**
   * Aggiunge lo sprite del giocatore alla scena
   * @param {PIXI.Application} scene - Oggetto scena creato con createScene
   * @param {number} x - Coordinata X in tile
   * @param {number} y - Coordinata Y in tile
   * @param {PIXI.Texture} texture - Texture da utilizzare per il giocatore
   * @returns {PIXI.Sprite} - Lo sprite del giocatore
   */
  addPlayer(scene, x, y, texture) {
    if (!scene) {
      console.error("[EntityManager] addPlayer: Scene parameter is null or undefined");
      return null;
    }
    
    const sceneId = scene.id || 'default_scene';
    
    // Verifica se esiste già uno sprite del giocatore e rimuovilo
    if (this.playerSprites.has(sceneId)) {
      const oldPlayer = this.playerSprites.get(sceneId);
      if (oldPlayer.main && oldPlayer.main.parent) {
        oldPlayer.main.parent.removeChild(oldPlayer.main);
      }
      if (oldPlayer.glow && oldPlayer.glow.parent) {
        oldPlayer.glow.parent.removeChild(oldPlayer.glow);
      }
      if (oldPlayer.stopAnimation) {
        oldPlayer.stopAnimation();
      }
    }
    
    // Crea un container per il giocatore
    const playerContainer = new PIXI.Container();
    
    // Crea lo sprite del giocatore
    const playerSprite = new PIXI.Sprite(texture || PIXI.Texture.WHITE);
    playerSprite.anchor.set(0.5);
    playerSprite.width = this.TILE_SIZE;
    playerSprite.height = this.TILE_SIZE;
    
    // Posiziona il giocatore
    playerSprite.x = (x + 0.5) * this.TILE_SIZE;
    playerSprite.y = (y + 0.5) * this.TILE_SIZE;
    
    // Verifica che lo stage esista prima di usarlo
    if (!scene.stage) {
      console.error("[EntityManager] addPlayer: scene.stage non esiste!");
      return null;
    }
    
    // Aggiungi il container alla scena
    scene.stage.addChild(playerContainer);
    playerContainer.addChild(playerSprite); // Aggiungiamo lo sprite subito, prima di provare i filtri
    
    // Memorizzazione sicura dello sprite e callback di cleanup
    let stopAnimationCallback = () => {};
    
    // Verifica se usare filtri o no (DEFAULT: NO FILTRI - più stabile)
    // Imposta a true solo se sei sicuro di voler usare i filtri
    const USE_GLOW_FILTERS = false;
    
    if (!USE_GLOW_FILTERS) {
      console.log('[EntityManager] addPlayer: Disabilitazione sistematica dei filtri per maggiore stabilità');
      this._addPlayerWithoutFilters(playerSprite, playerContainer, sceneId);
      return playerSprite;
    }
    
    // SOLO SE USE_GLOW_FILTERS = true, tenta di applicare i filtri
    // Controllo preventivo per problemi noti di ShaderSystem
    let useFilters = false;
    
    try {
      // Verifica se WebGL è disponibile e funzionante
      const isWebGLAvailable = this._isWebGLAvailable(scene);
      
      // Verifica aggiuntiva per problemi noti di shader
      if (isWebGLAvailable && scene.renderer && scene.renderer.shader) {
        // Verifica più rigorosa dello shader system per prevenire l'errore "Cannot read properties of undefined (reading 'add')"
        useFilters = typeof scene.renderer.shader.bind === 'function' && 
                    typeof scene.renderer.shader.system !== 'undefined' &&
                    scene.renderer.shader.system !== null;
        
        // Se ci sono troppi contesti WebGL attivi, non usare filtri
        const gl = scene.renderer.gl;
        if (gl && gl.getError && gl.getError() !== 0) {
          console.warn('[EntityManager] addPlayer: Errori rilevati nel contesto WebGL, disabilitazione filtri');
          useFilters = false;
        }
      }
      
      // Se il renderer è stato creato troppo recentemente, evita i filtri
      // (i problemi spesso si verificano nei primi frame dopo la creazione)
      if (!scene._frameCount || scene._frameCount < 5) {
        console.warn('[EntityManager] addPlayer: Renderer troppo nuovo, disabilitazione filtri per sicurezza');
        useFilters = false;
      }
    } catch (error) {
      console.warn('[EntityManager] addPlayer: Errore durante il controllo preventivo WebGL:', error);
      useFilters = false;
    }
    
    // Se GlowFilter non è disponibile o ci sono problemi potenziali, usa il metodo senza filtri
    if (!useFilters || !GlowFilter) {
      console.log('[EntityManager] addPlayer: Utilizzo metodo senza filtri per prevenire errori');
      this._addPlayerWithoutFilters(playerSprite, playerContainer, sceneId);
    } else {
      try {
        // Ulteriore verifica per assicurarsi che il renderer possa supportare shader complessi
        const contextValid = this._isWebGLContextValid(scene.renderer);
        if (!contextValid) {
          throw new Error("WebGL context not valid or lost");
        }
        
        // Prova ad applicare il GlowFilter in modo sicuro con parametri minimi per stabilità
        const glowFilter = new GlowFilter({
          distance: 5,            // Ridotto drasticamente per stabilità
          outerStrength: 1,       // Valore minimo
          innerStrength: 0.3,     // Ridotto per stabilità
          color: 0x00FF00,
          quality: 0.2,           // Qualità bassa per prestazioni migliori
          knockout: false         // Disabilitato knockout per migliorare stabilità
        });
        
        // Applicazione sicura del filtro
        try {
          playerSprite.filters = [glowFilter];
          console.log(`[EntityManager] addPlayer: GlowFilter applicato con successo`);
        } catch (filterApplyError) {
          console.warn(`[EntityManager] addPlayer: Errore durante l'applicazione del filtro`, filterApplyError);
          playerSprite.filters = []; // Rimuovi qualsiasi filtro che potrebbe essere stato applicato parzialmente
          this._addPlayerWithoutFilters(playerSprite, playerContainer, sceneId);
        }
      } catch (filterError) {
        console.warn('[EntityManager] addPlayer: Errore durante applicazione GlowFilter:', filterError);
        this._addPlayerWithoutFilters(playerSprite, playerContainer, sceneId);
      }
    }
    
    // Memorizza lo sprite del giocatore
    if (!this.playerSprites.has(sceneId)) {
      this.playerSprites.set(sceneId, {
        main: playerSprite,
        glow: null,
        stopAnimation: stopAnimationCallback
      });
    }
    
    return playerSprite;
  }
  
  /**
   * Metodo di fallback per aggiungere un giocatore senza effetti di filtro
   * @param {PIXI.Sprite} playerSprite - Lo sprite del giocatore
   * @param {PIXI.Container} container - Il container dello sprite
   * @param {string} sceneId - L'ID della scena
   * @private
   */
  _addPlayerWithoutFilters(playerSprite, container, sceneId) {
    try {
      // Aggiungi lo sprite al container se non è già presente
      if (playerSprite.parent !== container) {
        container.addChild(playerSprite);
      }
      
      // Assicurati che non ci siano filtri attivi
      if (playerSprite.filters && playerSprite.filters.length > 0) {
        // Rimuovi i filtri in modo sicuro
        try {
          // Prima disattiva i filtri esistenti
          const oldFilters = playerSprite.filters;
          if (Array.isArray(oldFilters)) {
            for (let filter of oldFilters) {
              if (filter && typeof filter.destroy === 'function') {
                try {
                  filter.enabled = false;
                } catch (e) {
                  // Ignora errori durante la disattivazione
                }
              }
            }
          }
        } catch (e) {
          // Ignora errori durante la pulizia dei filtri
        }
        
        // Poi rimuovi completamente i filtri
        playerSprite.filters = [];
      }
      
      console.log('[EntityManager] _addPlayerWithoutFilters: Player aggiunto senza effetti di filtro');
      
      // Aggiorna la mappa dei playerSprites
      if (this.playerSprites.has(sceneId)) {
        const playerData = this.playerSprites.get(sceneId);
        playerData.main = playerSprite;
        playerData.glow = null;
      } else {
        this.playerSprites.set(sceneId, {
          main: playerSprite,
          glow: null,
          stopAnimation: () => {}
        });
      }
    } catch (error) {
      console.error('[EntityManager] _addPlayerWithoutFilters: Errore durante l\'aggiunta del player:', error);
    }
  }
  
  /**
   * Versione di fallback per aggiungere il giocatore senza filtri WebGL
   * @private
   */
  _addPlayerWithManualGlow(scene, x, y, playerSprite, playerContainer) {
    if (!scene || !playerSprite || !playerContainer) {
      console.error("Parametri mancanti per _addPlayerWithManualGlow");
      return null;
    }
    
    const sceneId = scene.id || 'default_scene';
    
    // Tenta di utilizzare un filtro di base più semplice
    try {
      if (PIXI.filters && PIXI.filters.ColorMatrixFilter) {
        const basicFilter = new PIXI.filters.ColorMatrixFilter();
        
        // Applica il filtro solo se disponibile
        if (basicFilter && scene.renderer && scene.renderer.gl) {
          playerContainer.filters = [basicFilter];
        }
      }
    } catch (error) {
      console.warn('[EntityManager] _addPlayerWithManualGlow: impossibile applicare filtro di base:', error);
    }
    
    // Assicurarsi che lo sprite sia stato aggiunto al container
    if (!playerSprite.parent) {
      playerContainer.addChild(playerSprite);
    }
    
    // Memorizza lo sprite del giocatore (versione semplificata)
    this.playerSprites.set(sceneId, {
      main: playerSprite,
      glow: null,
      stopAnimation: () => { /* Nessuna animazione da fermare in questa versione base */ }
    });
  }
  
  /**
   * Aggiorna la posizione del giocatore
   * @param {string} sceneId - Identificativo della scena
   * @param {number} x - Coordinata X in tile
   * @param {number} y - Coordinata Y in tile
   */
  updatePlayerPosition(sceneId, x, y) {
    if (!sceneId) {
      console.error("[EntityManager] updatePlayerPosition: sceneId is null or undefined");
      return;
    }
    
    if (!this.playerSprites.has(sceneId)) {
      console.warn(`[EntityManager] updatePlayerPosition: Nessuno sprite giocatore trovato per la scena ${sceneId}`);
      return;
    }
    
    const playerSprite = this.playerSprites.get(sceneId);
    if (!playerSprite || !playerSprite.main) {
      console.warn(`[EntityManager] updatePlayerPosition: Sprite giocatore non valido per la scena ${sceneId}`);
      return;
    }
    
    // Aggiorna le coordinate
    playerSprite.main.x = (x + 0.5) * this.TILE_SIZE;
    playerSprite.main.y = (y + 0.5) * this.TILE_SIZE;
    
    // Se c'è anche lo sprite glow, aggiornalo
    if (playerSprite.glow) {
      playerSprite.glow.x = playerSprite.main.x;
      playerSprite.glow.y = playerSprite.main.y;
    }
  }
  
  /**
   * Aggiorna le entità sulla mappa
   * @param {string} sceneId - ID della scena
   * @param {Array} entities - Array di entità da renderizzare
   * @param {PIXI.Application} scene - Scena in cui aggiornare le entità
   * @param {Object} textures - Mappa delle texture disponibili
   */
  updateEntities(sceneId, entities, scene, textures) {
    if (!sceneId || !entities || !scene) {
      console.warn(`[EntityManager] updateEntities: Parametri mancanti - sceneId: ${sceneId}, entities: ${!!entities}, scene: ${!!scene}`);
      return;
    }
    
    // Verifica che la scena abbia uno stage
    if (!scene.stage) {
      console.error(`[EntityManager] updateEntities: Stage non trovato per scena ${sceneId}`);
      return;
    }
    
    // Verifica se entitiesContainer è stato creato
    let entitiesContainer = scene.entitiesContainer;
    if (!entitiesContainer) {
      console.warn(`[EntityManager] updateEntities: Container entità non trovato, creazione...`);
      
      // Fallback: crea il container se non esiste
      entitiesContainer = new PIXI.Container();
      scene.stage.addChild(entitiesContainer);
      scene.entitiesContainer = entitiesContainer;
    }
    
    // Inizializza la mappa degli sprite delle entità per questa scena se non esiste
    if (!this.entitySprites.has(sceneId)) {
      this.entitySprites.set(sceneId, new Map());
    }
    
    // Rimuovi le entità esistenti
    while (entitiesContainer.children.length > 0) {
      const child = entitiesContainer.children[0];
      entitiesContainer.removeChild(child);
      if (child.destroy) {
        child.destroy({ children: true, texture: false, baseTexture: false });
      }
    }
    
    // Pulisci la mappa delle entità
    this.entitySprites.get(sceneId).clear();
    
    // Se non ci sono entità da aggiungere, esci
    if (!Array.isArray(entities) || entities.length === 0) {
      console.log(`[EntityManager] updateEntities: Nessuna entità da renderizzare per ${sceneId}`);
      return;
    }
    
    // Aggiungi le nuove entità
    entities.forEach(entity => {
      // Verifica che l'entità abbia coordinate valide
      if (typeof entity.x !== 'number' || typeof entity.y !== 'number') {
        console.warn(`[EntityManager] updateEntities: Entità ${entity.id || entity.nome} con coordinate non valide:`, entity);
        return;
      }
      
      console.log(`[EntityManager] Richiesta texture per: id=${entity.id}, nome=${entity.nome}, tipo=${entity.type}, textureName=${entity.textureName}`);
      
      // Determina il tipo di texture in base al tipo di entità e al textureName fornito
      let textureToUse = textures[entity.textureName]; // Prova prima il nome specifico

      if (!textureToUse || textureToUse === PIXI.Texture.WHITE) {
        // console.log(`[EntityManager] Texture specifica '${entity.textureName}' non trovata per ${entity.type} ${entity.id || entity.nome}. Tento fallback.`);
        if (entity.type === 'npc') {
          console.log(`[EntityManager] Tento fallback per NPC: textures['npc'] o textures['npc_default']`);
          textureToUse = textures['npc'] || textures['npc_default']; // Fallback per NPC
        } else if (entity.type === 'item' || entity.type === 'object' || entity.type === 'furniture' || entity.type === 'chest' || entity.type === 'weapon' || entity.type === 'potion') {
          // Fallback per vari tipi di oggetti/item
          console.log(`[EntityManager] Tento fallback per ${entity.type}: textures['${entity.type}'] o textures['item'] o textures['item_default'] o textures['object_default']`);
          textureToUse = textures[entity.type] || textures['item'] || textures['item_default'] || textures['object_default'];
        } else if (entity.type === 'player') { // Anche se il player di solito è gestito da addPlayer
            console.log(`[EntityManager] Tento fallback per Player (in updateEntities): textures['player'] o textures['character']`);
            textureToUse = textures['player'] || textures['character'];
        }
        
        // if (!textureToUse && entity.textureName) {
        //    console.log(`[EntityManager] Fallback per '${entity.textureName}' (tipo: ${entity.type}) non riuscito.`);
        // }
      }
      
      if (!textureToUse || textureToUse === PIXI.Texture.WHITE) {
        console.warn(`[EntityManager] updateEntities: Texture finale non trovata per entità ${entity.id || entity.nome} (tipo: ${entity.type}, textureName: ${entity.textureName}). Uso PIXI.Texture.WHITE.`);
        textureToUse = PIXI.Texture.WHITE; // Fallback definitivo
      }
      
      // Crea lo sprite per l'entità
      const sprite = new PIXI.Sprite(textureToUse);
      sprite.x = entity.x * this.TILE_SIZE;
      sprite.y = entity.y * this.TILE_SIZE;
      sprite.width = this.TILE_SIZE;
      sprite.height = this.TILE_SIZE;
      
      // Aggiungi metadati all'entità
      sprite.entityData = entity;
      sprite.interactive = true;
      sprite.buttonMode = true;
      
      // Memorizza l'entità nella mappa delle entità
      const entityId = `entity-${entity.id || entity.type}-${entity.x}-${entity.y}`;
      this.entitySprites.get(sceneId).set(entityId, sprite);
      
      // Aggiungi l'etichetta dell'entità
      const label = new PIXI.Text(entity.name || entity.type, {
        fontFamily: 'Arial',
        fontSize: 10,
        fill: 0xFFFFFF,
        stroke: 0x000000,
        strokeThickness: 2
      });
      label.position.set(entity.x * this.TILE_SIZE + 2, entity.y * this.TILE_SIZE - 12);
      
      entitiesContainer.addChild(sprite);
      entitiesContainer.addChild(label);
    });
    
    console.log(`[EntityManager] updateEntities: Aggiunte ${entities.length} entità alla scena ${sceneId}`);
  }
  
  /**
   * Pulisce gli sprite delle entità per una specifica scena
   * @param {string} sceneId - ID della scena
   */
  cleanupEntities(sceneId) {
    // Pulisci la mappa degli sprite delle entità
    if (this.entitySprites.has(sceneId)) {
      this.entitySprites.delete(sceneId);
    }
    
    // Pulisci la mappa degli sprite del giocatore
    if (this.playerSprites.has(sceneId)) {
      const playerSprite = this.playerSprites.get(sceneId);
      if (playerSprite && playerSprite.stopAnimation) {
        playerSprite.stopAnimation();
      }
      this.playerSprites.delete(sceneId);
    }
  }
  
  /**
   * Verifica se WebGL è disponibile e funzionante nell'applicazione PIXI
   * @param {PIXI.Application} app - Applicazione PIXI
   * @returns {boolean} - true se WebGL è disponibile e funzionante
   * @private
   */
  _isWebGLAvailable(app) {
    if (!app) return false;
    
    // Verifica che il renderer sia inizializzato
    if (!app.renderer) return false;
    
    // Verifica che sia un renderer WebGL
    const isWebGL = app.renderer.type === PIXI.RENDERER_TYPE.WEBGL || 
                    app.renderer.type === PIXI.RENDERER_TYPE.WEBGL2;
    
    if (!isWebGL) return false;
    
    // Verifica che il contesto GL esista
    if (!app.renderer.gl) return false;
    
    // Verifica più approfondita del sistema shader
    let hasValidShaderSystem = false;
    try {
      hasValidShaderSystem = app.renderer.shader !== undefined && 
                            app.renderer.shader !== null &&
                            typeof app.renderer.shader.bind === 'function';
                            
      // Verifica anche il sistema specifico che causa l'errore
      if (hasValidShaderSystem) {
        // In alcune versioni di PIXI, lo shader.system non è immediatamente disponibile
        // o potrebbe essere accessibile tramite un'altra proprietà
        const shaderSystem = app.renderer.shader.system || app.renderer.shader;
        
        // Verifica esplicita che il metodo 'add' sia disponibile
        hasValidShaderSystem = hasValidShaderSystem && 
                              typeof shaderSystem.add === 'function';
      }
    } catch (error) {
      console.warn('[EntityManager] _isWebGLAvailable: Errore durante verifica shader system:', error);
      return false;
    }
    
    // Verifica aggiuntiva per il sistema di filtri
    let hasValidFilterSystem = false;
    try {
      hasValidFilterSystem = app.renderer.filter !== undefined &&
                            app.renderer.filter !== null;
    } catch (error) {
      console.warn('[EntityManager] _isWebGLAvailable: Errore durante verifica filter system:', error);
      // Non fallire solo per questo
    }
    
    // Verifica che non ci siano errori nel contesto WebGL
    let contextIsValid = true;
    try {
      if (app.renderer.gl && app.renderer.gl.getError) {
        const glError = app.renderer.gl.getError();
        if (glError !== 0) {
          console.warn('[EntityManager] _isWebGLAvailable: Errore WebGL:', glError);
          contextIsValid = false;
        }
      }
    } catch (error) {
      console.warn('[EntityManager] _isWebGLAvailable: Errore durante verifica errori WebGL:', error);
      contextIsValid = false;
    }
    
    return hasValidShaderSystem && contextIsValid;
  }
  
  /**
   * Verifica che il contesto WebGL sia ancora valido
   * @param {PIXI.Renderer} renderer - Il renderer PIXI
   * @returns {boolean} - true se il contesto è valido
   * @private
   */
  _isWebGLContextValid(renderer) {
    if (!renderer || !renderer.gl) return false;
    
    try {
      // Tenta un'operazione sul contesto
      const gl = renderer.gl;
      const status = gl.getError();
      
      // Se otteniamo CONTEXT_LOST_WEBGL, il contesto non è valido
      return status !== gl.CONTEXT_LOST_WEBGL;
    } catch (e) {
      return false;
    }
  }
  
  /**
   * Pulisce tutte le risorse delle entità
   */
  cleanup() {
    // Interrompi tutte le animazioni attive
    for (const playerSprite of this.playerSprites.values()) {
      if (playerSprite && playerSprite.stopAnimation) {
        try {
          playerSprite.stopAnimation();
        } catch (err) {
          console.warn('[EntityManager] cleanup: Errore durante l\'interruzione dell\'animazione:', err);
        }
      }
    }
    
    // Svuota le mappe
    this.playerSprites.clear();
    this.entitySprites.clear();
    console.log('[EntityManager] cleanup: Mappe degli sprite svuotate.');
  }
}

const entityManagerInstance = new EntityManager();
export default entityManagerInstance; 