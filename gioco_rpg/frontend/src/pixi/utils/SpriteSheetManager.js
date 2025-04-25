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
      
      // Verifica se ci sono sprite sheet disponibili tramite il nuovo endpoint API
      if (serverAvailable) {
        try {
          const response = await fetch(`${API_URL}/api/diagnostics/assets`);
          if (response.ok) {
            const data = await response.json();
            
            // Se abbiamo informazioni sugli sprite sheet, li carichiamo
            if (data.sprite_sheets && data.sprite_sheets.sheets > 0) {
              console.log(`Trovati ${data.sprite_sheets.sheets} sprite sheet sul server`);
              
              // Carica tutti gli sprite sheet disponibili
              await this.loadAllSpriteSheets();
              return true;
            }
          }
        } catch (err) {
          console.warn('Errore nella richiesta delle informazioni sugli sprite sheet:', err);
        }
      }
      
      // Configurazione delle spritesheet fallback
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
      
      console.log(`Trovati ${data.spritesheets.length} sprite sheet:`, data.spritesheets);
      
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
   * Genera sprite sheet sul server
   * @returns {Promise<boolean>} - true se la generazione è avvenuta con successo
   */
  static async generateSpriteSheets() {
    try {
      console.log('Richiesta generazione sprite sheet sul server...');
      
      // Verifica la disponibilità del server
      const serverAvailable = await AssetLoader.checkServerAvailability();
      if (!serverAvailable) {
        console.warn('Server non disponibile, impossibile generare sprite sheet');
        return false;
      }
      
      // Richiedi la generazione degli sprite sheet
      const response = await fetch(`${API_URL}/api/diagnostics/generate-sprite-sheets`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          async: true // Esegui la generazione in modo asincrono sul server
        })
      });
      
      if (!response.ok) {
        throw new Error(`Errore nella richiesta di generazione sprite sheet: ${response.status}`);
      }
      
      const result = await response.json();
      console.log('Risposta generazione sprite sheet:', result);
      
      // Se la generazione è stata avviata con successo, attendiamo un po' e poi ricarichiamo gli sprite sheet
      if (result.status === 'started' || result.status === 'completed') {
        if (result.status === 'started') {
          // Se è asincrono, attendiamo qualche secondo per dare tempo al server di generare i primi sprite sheet
          console.log('Generazione avviata in background, attesa 3 secondi...');
          await new Promise(resolve => setTimeout(resolve, 3000));
        }
        
        // Ricarichiamo gli sprite sheet
        await this.loadAllSpriteSheets();
        return true;
      }
      
      return false;
    } catch (err) {
      console.error('Errore nella generazione degli sprite sheet:', err);
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