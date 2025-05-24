import * as PIXI from 'pixi.js';

const API_URL = 'http://localhost:5000';

/**
 * Gestore delle sprite sheet per ottimizzare il caricamento delle texture
 */
export default class SpriteSheetManager {
  // Cache delle spritesheet caricate
  static spriteSheets = {};
  // Dimensione predefinita dei tile
  static TILE_SIZE = 64;
  
  /**
   * Inizializza il sistema di sprite sheet
   */
  static async initialize() {
    try {
      console.log('Inizializzazione SpriteSheetManager...');
      
      // Carica tutti gli sprite sheet disponibili
      await this.loadAllSpriteSheets();
      return true;
    } catch (err) {
      console.error('Errore nell\'inizializzazione del SpriteSheetManager:', err);
      return false;
    }
  }
  
  /**
   * Carica tutti gli sprite sheet disponibili sul server
   */
  static async loadAllSpriteSheets() {
    try {
      // Ottieni la lista degli sprite sheet disponibili
      const response = await fetch(`${API_URL}/assets/spritesheets/`);
      if (!response.ok) {
        throw new Error(`Errore nella richiesta degli sprite sheet: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (!data.spritesheets || !Array.isArray(data.spritesheets) || data.spritesheets.length === 0) {
        console.warn('Nessuno sprite sheet trovato sul server');
        return [];
      }
      
      console.log(`Trovati ${data.spritesheets.length} sprite sheet`);
      
      // Carica tutti gli sprite sheet in parallelo
      const loadPromises = data.spritesheets.map(sheet => {
        // Estrai l'ID dallo sprite sheet
        const sheetId = sheet.id || sheet.name || sheet;
        // Se l'URL non è specificato, lo costruiamo basandoci sull'ID
        const url = sheet.url || `${API_URL}/assets/spritesheets/${sheetId}.json`;
        
        // Carica lo sprite sheet
        return this.loadSpriteSheet(sheetId, url)
          .catch(err => {
            console.warn(`Errore nel caricamento dello sprite sheet ${sheetId}:`, err);
            return null;
          });
      });
      
      // Attendi il caricamento di tutti gli sprite sheet
      const results = await Promise.all(loadPromises);
      
      // Filtra solo i risultati validi
      const loadedSheets = results.filter(Boolean);
      console.log(`Caricati ${loadedSheets.length}/${data.spritesheets.length} sprite sheet`);
      
      return loadedSheets;
    } catch (err) {
      console.error('Errore nel caricamento di tutti gli sprite sheet:', err);
      return [];
    }
  }
  
  /**
   * Carica una spritesheet dalla configurazione specificata
   * @param {string} name - Nome della spritesheet
   * @param {string} url - URL del file JSON della spritesheet
   * @returns {Promise<PIXI.Spritesheet>} - La spritesheet caricata
   */
  static async loadSpriteSheet(name, url) {
    try {
      // Se la spritesheet è già caricata, la restituiamo
      if (this.spriteSheets[name]) {
        return this.spriteSheets[name];
      }
      
      return new Promise((resolve, reject) => {
        // Configura un loader temporaneo per caricare la spritesheet
        const loader = new PIXI.Loader();
        
        // Tenta di caricare la spritesheet
        loader.add(name, url)
          .load((loader, resources) => {
            if (resources[name] && resources[name].spritesheet) {
              // Memorizza la spritesheet in cache
              this.spriteSheets[name] = resources[name].spritesheet;
              console.log(`Spritesheet '${name}' caricata con successo:`, 
                Object.keys(resources[name].spritesheet.textures).length, 'textures');
              resolve(resources[name].spritesheet);
            } else {
              reject(new Error(`Impossibile caricare la spritesheet: ${name}`));
            }
          });
        
        // Gestione degli errori
        loader.onError.add((error) => {
          reject(error);
        });
      });
    } catch (err) {
      console.error(`Errore nel caricamento della spritesheet ${name}:`, err);
      throw err;
    }
  }
  
  /**
   * Ottiene una texture dalla spritesheet
   * @param {string} sheetName - Nome della spritesheet
   * @param {string} textureName - Nome della texture
   * @returns {PIXI.Texture} - La texture richiesta, o una texture di fallback
   */
  static getTexture(sheetName, textureName) {
    try {
      // Verifica se la spritesheet esiste e contiene la texture
      const sheet = this.spriteSheets[sheetName];
      if (sheet && sheet.textures[textureName]) {
        return sheet.textures[textureName];
      }
      
      // Se non è specificato un nome di spritesheet, cerca in tutte le spritesheet
      if (!sheetName && textureName) {
        for (const sheetName in this.spriteSheets) {
          const sheet = this.spriteSheets[sheetName];
          if (sheet && sheet.textures[textureName]) {
            return sheet.textures[textureName];
          }
        }
      }
      
      // Se la texture non è disponibile, usa fallback
      console.warn(`Texture '${textureName}' non trovata${sheetName ? ` nella spritesheet '${sheetName}'` : ''}, uso fallback`);
      return PIXI.Texture.WHITE;
    } catch (err) {
      console.error(`Errore nel recupero della texture ${textureName}${sheetName ? ` dalla spritesheet ${sheetName}` : ''}:`, err);
      return PIXI.Texture.WHITE;
    }
  }
  
  /**
   * Ottiene tutte le texture da tutte le spritesheet disponibili
   * @returns {Object} - Un oggetto con tutte le texture
   */
  static getAllTextures() {
    const allTextures = {};
    
    // Combina le texture da tutte le spritesheet
    Object.values(this.spriteSheets).forEach(sheet => {
      if (sheet && sheet.textures) {
        Object.assign(allTextures, sheet.textures);
      }
    });
    
    return allTextures;
  }
  
  /**
   * Verifica se una spritesheet è stata caricata
   * @param {string} name - Nome della spritesheet
   * @returns {boolean} - true se la spritesheet è caricata
   */
  static isSpriteSheetLoaded(name) {
    return !!this.spriteSheets[name];
  }
  
  /**
   * Crea una nuova spritesheet a partire da texture individuali
   * @param {string} name - Nome della spritesheet
   * @param {Object} textures - Mappa di texture da includere
   * @returns {PIXI.Spritesheet} - La spritesheet creata
   */
  static createSpriteSheet(name, textures) {
    try {
      if (!textures || Object.keys(textures).length === 0) {
        console.warn(`Impossibile creare la spritesheet ${name}: nessuna texture fornita`);
        return null;
      }
      
      if (this.isSpriteSheetLoaded(name)) {
        console.warn(`Spritesheet "${name}" già esistente. Non verrà sovrascritta.`);
        return this.spriteSheets[name];
      }

      console.log(`[SpriteSheetManager] Creazione spritesheet "${name}" con ${Object.keys(textures).length} texture.`);
      // console.log(`[SpriteSheetManager] Texture fornite per "${name}":`, textures); // Log pesante

      const frames = {};
      let currentX = 0;
      
      // Aggiungi ogni texture alla definizione della spritesheet
      Object.keys(textures).forEach(key => {
        const texture = textures[key];
        
        // Salta le texture non valide
        if (!texture || texture === PIXI.Texture.WHITE) {
          return;
        }
        
        let frameName = key;
        if (frameName.includes('/')) {
          frameName = frameName.split('/').pop();
        }

        // Log per vedere come viene nominata la texture nella spritesheet
        console.log(`[SpriteSheetManager] Processing for spritesheet "${name}": Original key: "${key}", Effective frameName: "${frameName}"`); 

        frames[frameName] = {
          frame: { x: currentX, y: 0, w: texture.width, h: texture.height },
          rotated: false,
          trimmed: false,
          spriteSourceSize: {
            x: 0,
            y: 0,
            w: texture.width,
            h: texture.height
          },
          sourceSize: {
            w: texture.width,
            h: texture.height
          }
        };
        
        currentX += texture.width;
      });
      
      // Crea un oggetto di definizione della spritesheet
      const data = {
        meta: {
          image: `${name}.png`, // Nome file virtuale
          format: 'RGBA8888',
          size: { w: currentX, h: this.TILE_SIZE },
          scale: '1'
        },
        frames: frames,
        animations: {}
      };
      
      // Crea e memorizza la spritesheet
      const spriteSheetInstance = new PIXI.Spritesheet(
        PIXI.BaseTexture.EMPTY,
        data
      );
      
      // Assegna le texture direttamente
      spriteSheetInstance.textures = textures;
      
      // Registra la spritesheet
      this.spriteSheets[name] = spriteSheetInstance;
      console.log(`[SpriteSheetManager] Spritesheet "${name}" creata e registrata con successo con ${Object.keys(spriteSheetInstance.textures || {}).length} texture finali.`);
      
      return spriteSheetInstance;
    } catch (err) {
      console.error(`Errore nella creazione della spritesheet ${name}:`, err);
      return null;
    }
  }
  
  /**
   * Carica una texture singola
   * @param {string} url - URL della texture
   * @returns {Promise<PIXI.Texture>} - Texture caricata
   */
  static loadTexture(url) {
    return new Promise((resolve, reject) => {
      // Controlla se la texture è già in cache
      if (PIXI.utils.TextureCache[url]) {
        resolve(PIXI.utils.TextureCache[url]);
        return;
      }
      
      const loader = new PIXI.Loader();
      loader.add(url, url)
        .load((loader, resources) => {
          if (resources[url] && resources[url].texture) {
            resolve(resources[url].texture);
          } else {
            reject(new Error(`Impossibile caricare la texture: ${url}`));
          }
        });
      
      loader.onError.add((err) => {
        reject(err);
      });
    });
  }
  
  /**
   * Aggiunge texture a una spritesheet esistente
   * @param {string} sheetName - Nome della spritesheet
   * @param {Object} newTextures - Nuove texture da aggiungere
   * @returns {boolean} - true se l'operazione è riuscita
   */
  static addTexturesToSpriteSheet(sheetName, newTextures) {
    try {
      // Verifica che la spritesheet esista
      if (!this.spriteSheets[sheetName]) {
        console.warn(`Impossibile aggiungere texture: la spritesheet ${sheetName} non esiste`);
        return false;
      }
      
      // Aggiungi le nuove texture
      let count = 0;
      Object.entries(newTextures).forEach(([key, texture]) => {
        if (!this.spriteSheets[sheetName].textures[key]) {
          this.spriteSheets[sheetName].textures[key] = texture;
          count++;
        }
      });
      
      console.log(`Aggiunte ${count} texture alla spritesheet ${sheetName}`);
      return true;
    } catch (err) {
      console.error(`Errore nell'aggiunta di texture alla spritesheet ${sheetName}:`, err);
      return false;
    }
  }
  
  /**
   * Pulisce le risorse delle spritesheet
   */
  static dispose() {
    try {
      Object.keys(this.spriteSheets).forEach(name => {
        const sheet = this.spriteSheets[name];
        if (sheet) {
          // Rimuovi tutte le texture della spritesheet
          Object.keys(sheet.textures || {}).forEach(key => {
            const texture = sheet.textures[key];
            if (texture && texture.destroy) {
              texture.destroy(true);
            }
          });
        }
      });
      
      // Reset della cache
      this.spriteSheets = {};
      
      console.log('Risorse delle spritesheet liberate con successo');
    } catch (err) {
      console.error('Errore nella pulizia delle risorse delle spritesheet:', err);
    }
  }
} 