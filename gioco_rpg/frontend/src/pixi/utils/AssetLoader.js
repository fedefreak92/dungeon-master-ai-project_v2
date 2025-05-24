import * as PIXI from 'pixi.js';
// Importo direttamente i moduli specifici da pixi.js invece che da @pixi/core
// import { utils, settings, Rectangle, Point } from '@pixi/core';
import SpriteSheetManager from './SpriteSheetManager';

const API_URL = 'http://localhost:5000';

// Cache per le texture già caricate
const textureCache = {
  tiles: {},
  entities: {},
  objects: {},
  ui: {}
};

/**
 * Utility per caricare le texture degli asset
 */
export default class AssetLoader {
  /**
   * Inizializza il sistema di asset
   */
  static async initialize() {
    try {
      console.log('Inizializzazione del sistema di asset...');
      
      // Inizializza il gestore delle spritesheet
      await SpriteSheetManager.initialize();
      
      return true;
    } catch (err) {
      console.error('Errore nell\'inizializzazione del sistema di asset:', err);
      return false;
    }
  }
  
  /**
   * Precarica le texture essenziali per il gioco
   * @returns {Object} Un oggetto con tutte le texture caricate
   */
  static async preloadEssentialTextures() {
    try {
      console.log('Precaricamento texture essenziali...');
      
      // Verifica se esistono già spritesheet per le categorie principali
      const tilesSpriteSheetLoaded = SpriteSheetManager.isSpriteSheetLoaded('tiles');
      const entitiesSpriteSheetLoaded = SpriteSheetManager.isSpriteSheetLoaded('entities');
      const objectsSpriteSheetLoaded = SpriteSheetManager.isSpriteSheetLoaded('objects');
      const uiSpriteSheetLoaded = SpriteSheetManager.isSpriteSheetLoaded('ui');
      
      const loadPromises = [];
      if (!tilesSpriteSheetLoaded) {
        loadPromises.push(this.loadMapTextures());
      } else {
        console.log('[AssetLoader] Tiles spritesheet già caricata, uso cache.');
        loadPromises.push(Promise.resolve(textureCache.tiles));
      }

      if (!entitiesSpriteSheetLoaded) {
        loadPromises.push(this.loadEntityTextures());
      } else {
        console.log('[AssetLoader] Entities spritesheet già caricata, uso cache.');
        loadPromises.push(Promise.resolve(textureCache.entities));
      }

      if (!objectsSpriteSheetLoaded) {
        loadPromises.push(this.loadObjectTextures());
      } else {
        console.log('[AssetLoader] Objects spritesheet già caricata, uso cache.');
        loadPromises.push(Promise.resolve(textureCache.objects));
      }

      if (!uiSpriteSheetLoaded) {
        loadPromises.push(this.loadUITextures());
      } else {
        console.log('[AssetLoader] UI spritesheet già caricata, uso cache.');
        loadPromises.push(Promise.resolve(textureCache.ui));
      }
        
      const [mapTextures, entityTextures, objectTextures, uiTextures] = await Promise.all(loadPromises);
        
      console.log('[AssetLoader] Texture caricate individualmente (prima della spritesheet):');
      console.log('  - Map Textures:', Object.keys(mapTextures));
      console.log('  - Entity Textures:', Object.keys(entityTextures));
      console.log('  - Object Textures:', Object.keys(objectTextures));
      console.log('  - UI Textures:', Object.keys(uiTextures));
        
      // Crea spritesheet virtuali se necessario
      if (!tilesSpriteSheetLoaded && Object.keys(mapTextures).length > 0) {
        SpriteSheetManager.createSpriteSheet('tiles', mapTextures);
      }
      
      if (!entitiesSpriteSheetLoaded && Object.keys(entityTextures).length > 0) {
        SpriteSheetManager.createSpriteSheet('entities', entityTextures);
      }

      if (!objectsSpriteSheetLoaded && Object.keys(objectTextures).length > 0) {
        SpriteSheetManager.createSpriteSheet('objects', objectTextures);
      }

      if (!uiSpriteSheetLoaded && Object.keys(uiTextures).length > 0) {
        SpriteSheetManager.createSpriteSheet('ui', uiTextures);
      }
      
      // Raccoglie tutte le texture disponibili dalle spritesheet
      const textures = this.collectTexturesFromSpriteSheets();
      
      console.log('[AssetLoader] Texture raccolte da collectTexturesFromSpriteSheets:', Object.keys(textures));
      console.log('Precaricamento texture essenziali completato');
      return textures;
    } catch (err) {
      console.error('Errore nel precaricamento delle texture essenziali:', err);
      return {};
    }
  }

  /**
   * Raccoglie le texture disponibili dalle spritesheet
   * @returns {Object} Un oggetto con tutte le texture raccolte
   */
  static collectTexturesFromSpriteSheets() {
    const textures = {};
    
    console.log('[AssetLoader] Avvio collectTexturesFromSpriteSheets...');
    // Spritesheet principali da controllare
    const sheets = ['tiles', 'entities', 'objects', 'ui'];
    
    // Per ogni spritesheet
    for (const sheetName of sheets) {
      if (SpriteSheetManager.isSpriteSheetLoaded(sheetName)) {
        const sheet = SpriteSheetManager.spriteSheets[sheetName];
        if (sheet && sheet.textures) {
          console.log(`[AssetLoader] Raccolgo texture da spritesheet: ${sheetName}, numero texture: ${Object.keys(sheet.textures).length}`);
          // Copia tutte le texture dalla spritesheet nel dizionario textures
          Object.assign(textures, sheet.textures);
        }
      }
    }
    
    console.log('[AssetLoader] collectTexturesFromSpriteSheets completato. Texture totali raccolte:', Object.keys(textures).length);
    return textures;
  }

  /**
   * Carica una texture dall'URL specificato
   * @param {string} url - URL della texture da caricare
   * @returns {Promise<PIXI.Texture>} - Texture caricata
   */
  static async loadTexture(url) {
    return new Promise((resolve, reject) => {
      try {
        // Prima verifica se l'immagine è già in cache globale di PIXI
        if (PIXI.utils.TextureCache[url] && PIXI.utils.TextureCache[url].valid) {
          resolve(PIXI.utils.TextureCache[url]);
          return;
        }
        
        // Usa uno shared loader per evitare duplicati
        const loader = PIXI.Loader.shared;
        
        // Aggiungi la risorsa al loader solo se non è già presente
        if (!loader.resources[url]) {
          loader.add(url, url);
        }
        
        // Gestisci il completamento del caricamento
        loader.load((loader, resources) => {
          if (resources[url] && resources[url].texture) {
            resolve(resources[url].texture);
          } else {
            reject(new Error(`Errore nel caricamento della texture: ${url}`));
          }
        });
        
        // Gestisci gli errori
        loader.onError.add((error) => {
          reject(error);
        });
      } catch (err) {
        reject(err);
      }
    });
  }
  
  /**
   * Carica un set di texture per i tile della mappa
   * @returns {Promise<Object>} - Mappa delle texture caricate
   */
  static async loadMapTextures() {
    // Se le texture sono già in cache, le restituiamo subito
    if (Object.keys(textureCache.tiles).length > 0) {
      return textureCache.tiles;
    }
    
    try {
      // Elenco di tipi di tile da caricare
      const tileTypes = [
        'floor', 'wall', 'door', 'grass', 'water',
        'road', 'lava', 'bridge', 'stairs'
      ];
      
      const textures = {};
      
      // Carica le texture dei tile dal server
      for (const type of tileTypes) {
        try {
          const url = `${API_URL}/assets/file/tiles/${type}.png`;
          const texture = await this.loadTexture(url);
          textures[type] = texture;
          textureCache.tiles[type] = texture;
        } catch (err) {
          console.warn(`Errore nel caricamento della texture del tile "${type}": ${err.message}`);
        }
      }
      
      console.log(`Caricate ${Object.keys(textures).length}/${tileTypes.length} texture per i tile`);
      return textures;
    } catch (err) {
      console.error('Errore nel caricamento delle texture della mappa:', err);
      return {};
    }
  }
  
  /**
   * Carica un set di texture per le entità
   * @returns {Promise<Object>} - Mappa delle texture caricate
   */
  static async loadEntityTextures() {
    // Se le texture sono già in cache, le restituiamo subito
    if (Object.keys(textureCache.entities).length > 0) {
      return textureCache.entities;
    }
    
    try {
      const entityTypes = [
        'player', 'npc', 'enemy', 'vendor', 'guard'
      ];
      
      const textures = {};
      
      // Carica le texture delle entità dal server
      for (const type of entityTypes) {
        try {
          const url = `${API_URL}/assets/file/entities/${type}.png`;
          const texture = await this.loadTexture(url);
          textures[type] = texture;
          textureCache.entities[type] = texture;
        } catch (err) {
          console.warn(`Errore nel caricamento della texture dell'entità "${type}": ${err.message}`);
        }
      }
      
      console.log(`Caricate ${Object.keys(textures).length}/${entityTypes.length} texture per le entità`);
      return textures;
    } catch (err) {
      console.error('Errore nel caricamento delle texture delle entità:', err);
      return {};
    }
  }
  
  /**
   * Carica un set di texture per gli oggetti
   * @returns {Promise<Object>} - Mappa delle texture caricate
   */
  static async loadObjectTextures() {
    if (Object.keys(textureCache.objects).length > 0) {
      return textureCache.objects;
    }
    
    try {
      const objectTypes = [
        'chest', 'furniture', 'door', 'potion', 'weapon'
      ];
      
      const textures = {};
      
      // Carica le texture degli oggetti dal server
      for (const type of objectTypes) {
        try {
          const url = `${API_URL}/assets/file/objects/${type}.png`;
          const texture = await this.loadTexture(url);
          textures[type] = texture;
          textureCache.objects[type] = texture;
        } catch (err) {
          console.warn(`Errore nel caricamento della texture dell'oggetto "${type}": ${err.message}`);
        }
      }
      
      console.log(`Caricate ${Object.keys(textures).length}/${objectTypes.length} texture per gli oggetti`);
      return textures;
    } catch (err) {
      console.error('Errore nel caricamento delle texture degli oggetti:', err);
      return {};
    }
  }
  
  /**
   * Carica un set di texture per l'interfaccia utente
   * @returns {Promise<Object>} - Mappa delle texture caricate
   */
  static async loadUITextures() {
    if (Object.keys(textureCache.ui).length > 0) {
      return textureCache.ui;
    }
    
    try {
      const uiElements = [
        'button', 'panel', 'frame', 'icon'
      ];
      
      const textures = {};
      
      // Carica le texture UI dal server
      for (const type of uiElements) {
        try {
          const url = `${API_URL}/assets/file/ui/${type}.png`;
          const texture = await this.loadTexture(url);
          textures[type] = texture;
          textureCache.ui[type] = texture;
        } catch (err) {
          console.warn(`Errore nel caricamento della texture UI "${type}": ${err.message}`);
        }
      }
      
      console.log(`Caricate ${Object.keys(textures).length}/${uiElements.length} texture per l'UI`);
      return textures;
    } catch (err) {
      console.error('Errore nel caricamento delle texture dell\'UI:', err);
      return {};
    }
  }
  
  /**
   * Pulisce tutte le cache delle texture
   * @param {boolean} forceDestroy - Se forzare la distruzione delle texture
   */
  static clearCache(forceDestroy = false) {
    console.log("Pulizia cache texture...");
    
    // Pulisci la cache locale
    Object.keys(textureCache).forEach(category => {
      Object.keys(textureCache[category]).forEach(key => {
        try {
          const texture = textureCache[category][key];
          
          if (texture && texture !== PIXI.Texture.WHITE) {
            // Rimuovi i listener per evitare memory leak
            if (texture.baseTexture) {
              texture.baseTexture.removeAllListeners();
            }
            
            // Rimuovi dalla cache PIXI
            if (texture.textureCacheIds) {
              texture.textureCacheIds.forEach(id => {
                PIXI.utils.TextureCache[id] = null;
                delete PIXI.utils.TextureCache[id];
              });
            }
            
            // Distruggi la texture se richiesto
            if (forceDestroy && texture.destroy) {
              texture.destroy(true);
            }
          }
        } catch (err) {
          console.warn(`Errore nella pulizia della texture ${category}/${key}`, err);
        }
      });
      
      // Reset della cache
      textureCache[category] = {};
    });
    
    // Reset del loader condiviso
    PIXI.Loader.shared.reset();
    
    // Pulisci anche le spritesheet
    SpriteSheetManager.dispose();
    
    // Pulisci la cache globale di Pixi
    try {
      PIXI.utils.clearTextureCache();
    } catch (err) {
      console.warn("Errore nella pulizia della cache globale PIXI", err);
    }
    
    console.log("Cache texture pulita con successo");
  }

  /**
   * Verifica se il server è disponibile
   * @returns {Promise<boolean>} - true se il server è disponibile
   */
  static async checkServerAvailability() {
    try {
      // Utilizza fetch con timeout per verificare la disponibilità del server
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000); // 2 secondi di timeout
      
      const response = await fetch(`${API_URL}/status`, {
        method: 'GET',
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      return response.ok;
    } catch (err) {
      return false;
    }
  }

  /**
   * Precarica tutte le texture necessarie per il gioco
   * @returns {Promise<Object>} - Oggetto con tutte le texture caricate
   */
  static async preloadAllTextures() {
    try {
      console.log('Precaricamento di tutte le texture...');
      
      // Inizializza il sistema di asset se non è già stato fatto
      await this.initialize();
      
      // Verifica se gli spritesheet sono già caricati
      const sheetsLoaded = this.areSpriteSheetLoaded(['tiles', 'entities', 'objects', 'ui']);
      
      // Se gli spritesheet sono già caricati, ritorna le texture raccolte
      if (sheetsLoaded) {
        return this.collectTexturesFromSpriteSheets();
      }
      
      // Carica le texture in sequenza per evitare conflitti nel loader
      const tileTextures = await this.loadMapTextures();
      const entityTextures = await this.loadEntityTextures();
      const objectTextures = await this.loadObjectTextures();
      const uiTextures = await this.loadUITextures();
      
      // Crea gli spritesheet con le texture caricate
      SpriteSheetManager.createSpriteSheet('tiles', tileTextures);
      SpriteSheetManager.createSpriteSheet('entities', entityTextures);
      SpriteSheetManager.createSpriteSheet('objects', objectTextures);
      SpriteSheetManager.createSpriteSheet('ui', uiTextures);
      
      console.log('Precaricamento completato:', {
        tiles: Object.keys(tileTextures).length,
        entities: Object.keys(entityTextures).length,
        objects: Object.keys(objectTextures).length,
        ui: Object.keys(uiTextures).length
      });
      
      // Restituisci la raccolta di texture da tutte le spritesheet
      return this.collectTexturesFromSpriteSheets();
    } catch (err) {
      console.error('Errore nel precaricamento delle texture:', err);
      return {};
    }
  }

  /**
   * Verifica se tutti gli spritesheet specificati sono caricati
   * @param {Array<string>} sheetNames - Nomi degli spritesheet da verificare
   * @returns {boolean} - true se tutti gli spritesheet specificati sono caricati
   */
  static areSpriteSheetLoaded(sheetNames) {
    if (!Array.isArray(sheetNames) || sheetNames.length === 0) {
      return false;
    }
    
    return sheetNames.every(name => SpriteSheetManager.isSpriteSheetLoaded(name));
  }
} 