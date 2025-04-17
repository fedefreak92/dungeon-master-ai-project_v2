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
      
      // Precarica le texture più importanti
      await this.preloadEssentialTextures();
      
      return true;
    } catch (err) {
      console.error('Errore nell\'inizializzazione del sistema di asset:', err);
      return false;
    }
  }
  
  /**
   * Precarica le texture essenziali per il gioco
   */
  static async preloadEssentialTextures() {
    try {
      console.log('Precaricamento texture essenziali...');
      
      // Carica in parallelo le texture per mappe ed entità
      const [mapTextures, entityTextures] = await Promise.all([
        this.loadMapTextures(),
        this.loadEntityTextures()
      ]);
      
      // Crea spritesheet virtuali dalle texture singole se necessario
      if (!SpriteSheetManager.isSpriteSheetLoaded('tiles')) {
        SpriteSheetManager.createSpriteSheet('tiles', mapTextures);
      }
      
      if (!SpriteSheetManager.isSpriteSheetLoaded('entities')) {
        SpriteSheetManager.createSpriteSheet('entities', entityTextures);
      }
      
      console.log('Precaricamento texture essenziali completato');
      return true;
    } catch (err) {
      console.error('Errore nel precaricamento delle texture essenziali:', err);
      return false;
    }
  }

  /**
   * Carica una texture dall'URL specificato
   * @param {string} url - URL della texture da caricare
   * @returns {Promise<PIXI.Texture>} - Texture caricata
   */
  static async loadTexture(url) {
    return new Promise((resolve) => {
      try {
        // Prima verifica se l'immagine è già in cache globale di PIXI
        if (PIXI.utils.TextureCache[url] && PIXI.utils.TextureCache[url].valid) {
          resolve(PIXI.utils.TextureCache[url]);
          return;
        }
        
        // Configurazione per il caricamento sicuro di texture
        PIXI.settings.STRICT_TEXTURE_CACHE = true;
        
        // Se la texture è già in fase di caricamento, non avviare un nuovo loader
        if (PIXI.Loader.shared.resources[url]) {
          resolve(PIXI.Loader.shared.resources[url].texture || PIXI.Texture.WHITE);
          return;
        }
        
        // Controlla se il loader è in esecuzione
        if (PIXI.Loader.shared.loading) {
          // Attendi che il loader corrente finisca prima di aggiungere nuove risorse
          PIXI.Loader.shared.onComplete.once(() => {
            // Quando il loader finisce, riprova a caricare questa texture
            this.loadTexture(url).then(resolve);
          });
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
            console.warn(`Errore nel caricamento della texture: ${url}, uso fallback`);
            resolve(PIXI.Texture.WHITE);
          }
        });
        
        // Gestisci gli errori
        loader.onError.add(() => {
          console.warn(`Errore nel caricamento della texture: ${url}, uso fallback`);
          resolve(PIXI.Texture.WHITE);
        });
      } catch (err) {
        console.warn(`Errore nel caricamento della texture: ${url}`, err);
        resolve(PIXI.Texture.WHITE);
      }
    });
  }
  
  /**
   * Carica un set di texture per i tile della mappa
   * @returns {Promise<Object>} - Mappa delle texture caricate
   */
  static async loadMapTextures() {
    // Tenta di usare prima la spritesheet
    if (SpriteSheetManager.isSpriteSheetLoaded('tiles')) {
      const spritesheet = SpriteSheetManager.spriteSheets['tiles'];
      
      // Trasforma la spritesheet in un oggetto di texture
      const tileTypes = [
        'floor', 'wall', 'door', 'grass', 'water',
        'road', 'lava', 'bridge', 'stairs'
      ];
      
      const texturesFromSheet = {};
      tileTypes.forEach(type => {
        // Cerca sia con estensione che senza
        const texture = 
          spritesheet.textures[`${type}.png`] || 
          spritesheet.textures[type] || 
          PIXI.Texture.WHITE;
        
        texturesFromSheet[type] = texture;
      });
      
      return texturesFromSheet;
    }
    
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
      
      // Verifica prima la disponibilità del server
      const serverAvailable = await this.checkServerAvailability();
      console.log(`Server disponibile: ${serverAvailable}`);
      
      // Carica le texture in sequenza invece che in parallelo
      for (const type of tileTypes) {
        try {
          // Cache locale per evitare ricaricamenti
          if (textureCache.tiles[type] && textureCache.tiles[type] !== PIXI.Texture.WHITE) {
            textures[type] = textureCache.tiles[type];
            continue;
          }
          
          let texture;
          const url = `${API_URL}/assets/tiles/${type}.png`;
          
          if (serverAvailable) {
            texture = await this.loadTextureWithFallback(url, true, 1);
          } else {
            // Se il server non è disponibile, prova a caricare dalla directory locale
            const localUrl = `/assets/fallback/tiles/${type}.png`;
            texture = await this.loadTextureWithFallback(localUrl, false, 0);
          }
          
          // Memorizza la texture anche se è un fallback
          textures[type] = texture;
        } catch (err) {
          console.warn(`Errore nel caricamento della texture '${type}', uso fallback`);
          textures[type] = PIXI.Texture.WHITE;
        }
      }
      
      // Verifica quante texture sono state caricate con successo
      const successCount = Object.values(textures).filter(
        texture => texture && texture !== PIXI.Texture.WHITE
      ).length;
      
      console.log(`Caricate ${successCount}/${tileTypes.length} texture per la mappa`);
      
      // Memorizza in cache solo se almeno alcune texture sono state caricate con successo
      if (successCount > 0) {
        // Memorizza solo le texture valide
        for (const type of tileTypes) {
          if (textures[type] && textures[type] !== PIXI.Texture.WHITE) {
            textureCache.tiles[type] = textures[type];
          }
        }
      }
      
      return textures;
    } catch (err) {
      console.error('Errore critico nel caricamento delle texture della mappa:', err);
      // In caso di errore grave, restituisci un set minimo di texture di fallback
      return {
        floor: PIXI.Texture.WHITE,
        wall: PIXI.Texture.WHITE,
        door: PIXI.Texture.WHITE
      };
    }
  }
  
  /**
   * Carica un set di texture per le entità
   * @returns {Promise<Object>} - Mappa delle texture caricate
   */
  static async loadEntityTextures() {
    // Tenta di usare prima la spritesheet
    if (SpriteSheetManager.isSpriteSheetLoaded('entities')) {
      const spritesheet = SpriteSheetManager.spriteSheets['entities'];
      
      // Trasforma la spritesheet in un oggetto di texture
      const entityTypes = [
        'player', 'npc', 'enemy', 'vendor', 'guard'
      ];
      
      const texturesFromSheet = {};
      entityTypes.forEach(type => {
        // Cerca sia con estensione che senza
        const texture = 
          spritesheet.textures[`${type}.png`] || 
          spritesheet.textures[type] || 
          PIXI.Texture.WHITE;
        
        texturesFromSheet[type] = texture;
      });
      
      return texturesFromSheet;
    }
    
    // Se le texture sono già in cache, le restituiamo subito
    if (Object.keys(textureCache.entities).length > 0) {
      return textureCache.entities;
    }
    
    try {
      const entityTypes = [
        'player', 'npc', 'enemy', 'vendor', 'guard'
      ];
      
      const textures = {};
      
      // Verifica prima la disponibilità del server
      const serverAvailable = await this.checkServerAvailability();
      
      // Carica le texture in sequenza invece che in parallelo
      for (const type of entityTypes) {
        try {
          // Cache locale per evitare ricaricamenti
          if (textureCache.entities[type] && textureCache.entities[type] !== PIXI.Texture.WHITE) {
            textures[type] = textureCache.entities[type];
            continue;
          }
          
          let texture;
          const url = `${API_URL}/assets/entities/${type}.png`;
          
          if (serverAvailable) {
            texture = await this.loadTextureWithFallback(url, true, 1);
          } else {
            // Se il server non è disponibile, prova a caricare dalla directory locale
            const localUrl = `/assets/fallback/entities/${type}.png`;
            texture = await this.loadTextureWithFallback(localUrl, false, 0);
          }
          
          // Memorizza la texture anche se è un fallback
          textures[type] = texture;
        } catch (err) {
          console.warn(`Errore nel caricamento della texture '${type}', uso fallback`);
          textures[type] = PIXI.Texture.WHITE;
        }
      }
      
      // Verifica quante texture sono state caricate con successo
      const successCount = Object.values(textures).filter(
        texture => texture && texture !== PIXI.Texture.WHITE
      ).length;
      
      console.log(`Caricate ${successCount}/${entityTypes.length} texture per le entità`);
      
      // Memorizza in cache solo le texture valide
      for (const type of entityTypes) {
        if (textures[type] && textures[type] !== PIXI.Texture.WHITE) {
          textureCache.entities[type] = textures[type];
        }
      }
      
      return textures;
    } catch (err) {
      console.error('Errore nel caricamento delle texture delle entità:', err);
      // In caso di errore, restituisci un set minimo di texture di fallback
      return {
        player: PIXI.Texture.WHITE,
        npc: PIXI.Texture.WHITE
      };
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
      
      // Carica le texture in parallelo
      await Promise.all(
        objectTypes.map(async (type) => {
          const url = `${API_URL}/assets/objects/${type}.png`;
          try {
            textures[type] = await this.loadTexture(url);
          } catch (err) {
            console.warn(`Impossibile caricare la texture per l'oggetto ${type}, uso fallback`);
            // Usa una texture di fallback per gli oggetti mancanti
            textures[type] = PIXI.Texture.WHITE;
          }
        })
      );
      
      // Memorizza in cache
      textureCache.objects = textures;
      
      return textures;
    } catch (err) {
      console.error('Errore nel caricamento delle texture degli oggetti:', err);
      throw err;
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
      
      // Carica le texture in parallelo
      await Promise.all(
        uiElements.map(async (type) => {
          const url = `${API_URL}/assets/ui/${type}.png`;
          try {
            textures[type] = await this.loadTexture(url);
          } catch (err) {
            console.warn(`Impossibile caricare la texture per l'UI ${type}, uso fallback`);
            // Usa una texture di fallback per gli elementi UI mancanti
            textures[type] = PIXI.Texture.WHITE;
          }
        })
      );
      
      // Memorizza in cache
      textureCache.ui = textures;
      
      return textures;
    } catch (err) {
      console.error('Errore nel caricamento delle texture dell\'UI:', err);
      throw err;
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
      // Usa un'immagine piccola e comune per il test
      const url = `${API_URL}/status`;
      
      // Utilizza fetch con timeout per verificare la disponibilità del server
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000); // 2 secondi di timeout
      
      const response = await fetch(url, {
        method: 'GET',
        signal: controller.signal,
        cache: 'no-store' // Evita la cache
      });
      
      clearTimeout(timeoutId);
      
      return response.ok;
    } catch (err) {
      console.warn('Server non disponibile:', err.message);
      return false;
    }
  }

  /**
   * Controlla la disponibilità degli asset necessari
   * @param {string} type - Tipo di asset da controllare (maps, sessions, ecc.)
   * @returns {Promise<boolean>} - true se gli asset sono disponibili, false altrimenti
   */
  static async checkAssetsAvailability(type) {
    try {
      // Prima verifica se il server è disponibile
      const serverAvailable = await this.checkServerAvailability();
      if (!serverAvailable) {
        console.warn(`Server non disponibile, utilizzo asset di fallback per ${type}`);
        return false;
      }
      
      // Tenta di contattare l'endpoint specifico
      let endpointUrl = `${API_URL}`;
      if (type === 'maps') {
        endpointUrl = `${API_URL}/api/maps`;
      } else if (type === 'sessions') {
        endpointUrl = `${API_URL}/api/sessions`;
      } else if (type.startsWith('asset/')) {
        const assetPath = type.substring(6);
        endpointUrl = `${API_URL}/assets/${assetPath}`;
      }
      
      // Usa una richiesta GET con timeout invece di HEAD
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);
      
      const response = await fetch(endpointUrl, {
        method: 'GET',
        signal: controller.signal,
        headers: {
          'Accept': 'application/json'
        }
      });
      
      clearTimeout(timeoutId);
      return response.ok;
    } catch (err) {
      console.warn(`Asset non disponibile: ${type}`, err);
      return false;
    }
  }

  /**
   * Rileva la configurazione del server
   * @returns {Promise<Object>} - Informazioni sul server
   */
  static async detectServerConfiguration() {
    try {
      // Verifica se il server è disponibile
      const isAvailable = await this.checkServerAvailability();
      
      if (!isAvailable) {
        return {
          available: false,
          offline: true,
          assetPaths: {}
        };
      }
      
      // Tenta di recuperare le informazioni sugli asset
      try {
        const response = await fetch(`${API_URL}/api/assets/info`);
        if (response.ok) {
          const data = await response.json();
          return {
            available: true,
            offline: false,
            ...data
          };
        }
      } catch (err) {
        console.warn('Impossibile recuperare le informazioni sugli asset', err);
      }
      
      // Configurazione di default
      return {
        available: true,
        offline: false,
        assetPaths: {
          tiles: '/assets/tiles/',
          entities: '/assets/entities/',
          objects: '/assets/objects/',
          ui: '/assets/ui/'
        }
      };
    } catch (err) {
      console.error('Errore nel rilevamento della configurazione del server', err);
      return {
        available: false,
        offline: true,
        assetPaths: {}
      };
    }
  }

  /**
   * Carica una texture con supporto automatico al fallback
   * @param {string} url - URL della texture da caricare
   * @param {boolean} useLocalFallback - Se usare il fallback locale
   * @param {number} retries - Numero di tentativi da effettuare
   * @returns {Promise<PIXI.Texture>} - Texture caricata
   */
  static async loadTextureWithFallback(url, useLocalFallback = true, retries = 2) {
    try {
      // Verifica se la texture è già in cache
      if (PIXI.utils.TextureCache[url] && PIXI.utils.TextureCache[url].valid) {
        return PIXI.utils.TextureCache[url];
      }
      
      // Prova a caricare la texture dall'URL originale
      try {
        const texture = await this.loadTexture(url);
        if (texture && texture !== PIXI.Texture.WHITE) {
          return texture;
        }
      } catch (err) {
        // Ignora l'errore e passa al fallback
        console.warn(`Errore nel caricamento della texture: ${url}, uso fallback`);
      }
      
      // Se arriviamo qui, la texture originale non è stata caricata
      if (useLocalFallback) {
        // Estrai il nome del file dall'URL
        const parts = url.split('/');
        const filename = parts[parts.length - 1];
        const type = parts[parts.length - 2] || 'tiles';
        
        // Controlla e usa prima la texture colorata di placeholder
        const fallbackUrl = `/assets/fallback/${type}/${filename}`;
        try {
          const fallbackTexture = await this.loadTexture(fallbackUrl);
          if (fallbackTexture && fallbackTexture !== PIXI.Texture.WHITE) {
            return fallbackTexture;
          }
        } catch (err) {
          // Crea una texture generica colorata in base al tipo
          try {
            const genericTexture = this.createGenericTexture(type, filename);
            if (genericTexture) {
              return genericTexture;
            }
          } catch (genErr) {
            console.warn(`Impossibile creare texture generica per ${type}/${filename}`);
          }
        }
      }
      
      // Se ci sono ancora tentativi disponibili e l'URL è remoto, prova a ritardare e riprovare
      if (retries > 0) {
        await new Promise(resolve => setTimeout(resolve, 500)); // Attendi 500ms
        return this.loadTextureWithFallback(url, useLocalFallback, retries - 1);
      }
      
      // Se tutti i tentativi falliscono, usa una texture bianca
      console.warn(`Impossibile caricare la texture dopo tutti i tentativi: ${url}`);
      return PIXI.Texture.WHITE;
    } catch (err) {
      console.error(`Errore critico nel caricamento della texture: ${url}`, err);
      return PIXI.Texture.WHITE;
    }
  }

  /**
   * Crea una texture generica colorata in base al tipo
   * @param {string} type - Tipo di texture (tiles, entities, ecc.)
   * @param {string} name - Nome del file
   * @returns {PIXI.Texture} - Texture generica
   */
  static createGenericTexture(type, name) {
    // Dimensione della texture
    const size = 32;
    
    // Crea un canvas temporaneo
    const canvas = document.createElement('canvas');
    canvas.width = size;
    canvas.height = size;
    
    const ctx = canvas.getContext('2d');
    
    // Colore di base in base al tipo
    let color = '#AAAAAA'; // Grigio di default
    
    if (type === 'tiles') {
      // Colori diversi per diversi tipi di tile
      if (name.includes('floor')) {
        color = '#DDDDDD'; // Grigio chiaro
      } else if (name.includes('wall')) {
        color = '#555555'; // Grigio scuro
      } else if (name.includes('water')) {
        color = '#0088FF'; // Blu
      } else if (name.includes('grass')) {
        color = '#00AA00'; // Verde
      } else if (name.includes('lava')) {
        color = '#FF4400'; // Arancione/rosso
      }
    } else if (type === 'entities') {
      // Colori per le entità
      if (name.includes('player')) {
        color = '#FF0000'; // Rosso
      } else if (name.includes('npc')) {
        color = '#00FF00'; // Verde
      } else if (name.includes('enemy')) {
        color = '#770000'; // Rosso scuro
      }
    }
    
    // Riempi il canvas con il colore
    ctx.fillStyle = color;
    ctx.fillRect(0, 0, size, size);
    
    // Aggiungi un bordo
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 2;
    ctx.strokeRect(2, 2, size - 4, size - 4);
    
    // Crea una texture PIXI dal canvas
    return PIXI.Texture.from(canvas);
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
      
      // Carica le texture in sequenza per evitare conflitti nel loader
      const tileTextures = await this.loadMapTextures();
      const entityTextures = await this.loadEntityTextures();
      const objectTextures = await this.loadObjectTextures();
      const uiTextures = await this.loadUITextures();
      
      console.log('Precaricamento completato:', {
        tiles: Object.keys(tileTextures).length,
        entities: Object.keys(entityTextures).length,
        objects: Object.keys(objectTextures).length,
        ui: Object.keys(uiTextures).length
      });
      
      // Restituisci un set minimo di texture di fallback
      return {
        tiles: tileTextures,
        entities: entityTextures,
        objects: objectTextures,
        ui: uiTextures
      };
    } catch (err) {
      console.error('Errore nel precaricamento delle texture:', err);
      
      // Restituisci un set minimo di texture di fallback
      return {
        tiles: {
          floor: PIXI.Texture.WHITE,
          wall: PIXI.Texture.WHITE
        },
        entities: {
          player: PIXI.Texture.WHITE,
          npc: PIXI.Texture.WHITE
        },
        objects: {
          chest: PIXI.Texture.WHITE
        },
        ui: {
          button: PIXI.Texture.WHITE
        }
      };
    }
  }

  /**
   * Precarica le texture delle entità all'avvio dell'applicazione
   * @returns {Promise<boolean>} - true se completato con successo
   */
  static async preloadEntityTextures() {
    try {
      console.log("Precaricamento texture entità...");
      
      // Precarica le texture delle entità
      const entityTextures = await this.loadEntityTextures();
      
      // Verifica quante texture sono state caricate con successo
      const successCount = Object.values(entityTextures).filter(
        texture => texture && texture !== PIXI.Texture.WHITE
      ).length;
      
      console.log(`Precaricate ${successCount} texture di entità`);
      return successCount > 0;
    } catch (err) {
      console.error("Errore nel precaricamento delle texture delle entità:", err);
      return false;
    }
  }
} 