import * as PIXI from 'pixi.js';
import AssetLoader from './AssetLoader';

const API_URL = 'http://localhost:5000';

/**
 * Gestore delle sprite sheet per ottimizzare il caricamento delle texture
 */
export default class SpriteSheetManager {
  // Cache delle spritesheet caricate
  static spriteSheets = {};
  
  /**
   * Inizializza il sistema di sprite sheet
   */
  static async initialize() {
    try {
      console.log('Inizializzazione SpriteSheetManager...');
      
      // Verifica la disponibilità del server
      const serverAvailable = await AssetLoader.checkServerAvailability();
      
      // Configurazione delle spritesheet da caricare
      const spriteSheetConfigs = [
        { 
          name: 'tiles', 
          url: serverAvailable 
            ? `${API_URL}/assets/spritesheets/tiles.json` 
            : `/assets/fallback/spritesheets/tiles.json`
        },
        { 
          name: 'entities', 
          url: serverAvailable 
            ? `${API_URL}/assets/spritesheets/entities.json` 
            : `/assets/fallback/spritesheets/entities.json`
        }
      ];
      
      // Tenta di caricare le sprite sheet, con fallback a textures individuali
      for (const config of spriteSheetConfigs) {
        try {
          await this.loadSpriteSheet(config.name, config.url);
        } catch (err) {
          console.warn(`Impossibile caricare la spritesheet ${config.name}, uso textures individuali`);
        }
      }
      
      return true;
    } catch (err) {
      console.error('Errore nell\'inizializzazione del SpriteSheetManager:', err);
      return false;
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
        loader.onError.add((error, loader) => {
          reject(error);
        });
      });
    } catch (err) {
      console.error(`Errore nel caricamento della spritesheet ${name}:`, err);
      throw err;
    }
  }
  
  /**
   * Ottiene una texture dalla spritesheet, con fallback
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
      
      // Se la texture non è disponibile nella spritesheet, logga e usa fallback
      console.warn(`Texture '${textureName}' non trovata nella spritesheet '${sheetName}', uso fallback`);
      return PIXI.Texture.WHITE;
    } catch (err) {
      console.error(`Errore nel recupero della texture ${textureName} dalla spritesheet ${sheetName}:`, err);
      return PIXI.Texture.WHITE;
    }
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
      
      // Crea un oggetto di definizione della spritesheet
      const data = {
        meta: {
          image: `${name}.png`, // Nome file virtuale
          format: 'RGBA8888',
          size: { w: 0, h: 0 },
          scale: '1'
        },
        frames: {},
        animations: {}
      };
      
      // Aggiungi ogni texture alla definizione della spritesheet
      Object.keys(textures).forEach(key => {
        const texture = textures[key];
        
        // Salta le texture non valide
        if (!texture || texture === PIXI.Texture.WHITE) {
          return;
        }
        
        data.frames[key] = {
          frame: {
            x: 0,
            y: 0,
            w: texture.width,
            h: texture.height
          },
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
      });
      
      // Crea e memorizza la spritesheet
      const spritesheet = new PIXI.Spritesheet(
        PIXI.BaseTexture.EMPTY,
        data
      );
      
      // Assegna le texture direttamente
      spritesheet.textures = textures;
      
      // Memorizza in cache
      this.spriteSheets[name] = spritesheet;
      
      console.log(`Spritesheet virtuale '${name}' creata con ${Object.keys(textures).length} texture`);
      return spritesheet;
    } catch (err) {
      console.error(`Errore nella creazione della spritesheet ${name}:`, err);
      return null;
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