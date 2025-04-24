/**
 * CachedMapRenderer.js
 * Renderer di mappe che utilizza RenderTexture per il caching degli elementi statici
 */
import * as PIXI from 'pixi.js';
import MapRenderer from './MapRenderer';

// Dimensione standard dei tile
const TILE_SIZE = 64;

/**
 * Renderer che utilizza il caching degli elementi statici per ottimizzare le prestazioni
 */
export default class CachedMapRenderer {
  constructor() {
    this.staticCache = null;       // RenderTexture per elementi statici
    this.staticSprite = null;      // Sprite che mostra la cache statica
    this.dynamicContainer = null;  // Container per elementi dinamici
    this.viewport = null;          // Viewport corrente
    this.mapData = null;           // Dati mappa correnti
    this.textures = {};            // Texture usate
    this.isDirty = true;           // Flag per rigenerazione cache
    this.app = null;               // Riferimento all'app Pixi.js
    this.isInitialized = false;    // Flag di inizializzazione
    this.staticLayerNames = ['terrain', 'background']; // Layer da cachare
  }

  /**
   * Inizializza il renderer
   * @param {PIXI.Application} app - Applicazione PIXI
   * @param {PIXI.Container} viewport - Container del viewport
   * @param {Object} textures - Texture disponibili
   * @returns {boolean} - true se l'inizializzazione è riuscita
   */
  initialize(app, viewport, textures = {}) {
    if (this.isInitialized) return true;

    try {
      this.app = app;
      this.viewport = viewport;
      this.textures = textures;

      // Crea i container principali
      this.dynamicContainer = new PIXI.Container();
      this.dynamicContainer.name = 'dynamic-elements';
      this.viewport.addChild(this.dynamicContainer);

      this.isInitialized = true;
      return true;
    } catch (error) {
      console.error("Errore nell'inizializzazione del CachedMapRenderer:", error);
      return false;
    }
  }

  /**
   * Renderizza una mappa con caching degli elementi statici
   * @param {Object} mapData - Dati della mappa
   * @returns {boolean} - true se il rendering è riuscito
   */
  renderMap(mapData) {
    if (!this.isInitialized || !mapData) {
      console.error("Renderer non inizializzato o dati mappa mancanti");
      return false;
    }

    try {
      this.mapData = mapData;

      // Determina la dimensione della mappa
      const width = mapData.larghezza || (mapData.griglia ? mapData.griglia[0].length : 0);
      const height = mapData.altezza || (mapData.griglia ? mapData.griglia.length : 0);

      // Se la cache è vuota o la mappa è cambiata, rigenera la cache
      if (this.isDirty || !this.staticCache || 
          this.staticCache.width !== width * TILE_SIZE ||
          this.staticCache.height !== height * TILE_SIZE) {
        this.regenerateStaticCache(width, height);
      }

      // Renderizza gli elementi dinamici
      this.renderDynamicElements();

      return true;
    } catch (error) {
      console.error("Errore nel rendering della mappa:", error);
      return false;
    }
  }

  /**
   * Rigenera la cache degli elementi statici
   * @param {number} width - Larghezza della mappa in tile
   * @param {number} height - Altezza della mappa in tile
   */
  regenerateStaticCache(width, height) {
    // Pulisci le risorse esistenti
    if (this.staticCache) {
      this.staticCache.destroy(true);
      this.staticCache = null;
    }
    
    if (this.staticSprite) {
      if (this.viewport.children.includes(this.staticSprite)) {
        this.viewport.removeChild(this.staticSprite);
      }
      this.staticSprite.destroy();
      this.staticSprite = null;
    }

    // Crea un container temporaneo per renderizzare gli elementi statici
    const tempContainer = new PIXI.Container();

    // Rendering sicuro con try-catch
    try {
      // Disegna la griglia di fondo
      const gridGraphics = new PIXI.Graphics();
      gridGraphics.lineStyle(1, 0x444444, 0.3);
      
      // Disegna linee verticali
      for (let x = 0; x <= width; x++) {
        gridGraphics.moveTo(x * TILE_SIZE, 0);
        gridGraphics.lineTo(x * TILE_SIZE, height * TILE_SIZE);
      }
      
      // Disegna linee orizzontali
      for (let y = 0; y <= height; y++) {
        gridGraphics.moveTo(0, y * TILE_SIZE);
        gridGraphics.lineTo(width * TILE_SIZE, y * TILE_SIZE);
      }
      
      tempContainer.addChild(gridGraphics);

      // Rendering dei tile di terreno
      if (this.mapData.griglia && Array.isArray(this.mapData.griglia)) {
        // Mappa dei colori per i tipi di tile
        const tileColors = {
          1: 0x333333,  // muri - grigio scuro
          2: 0x8B4513,  // porte - marrone
          3: 0x00FF00,  // erba - verde
          4: 0x0000FF,  // acqua - blu
          5: 0xFFD700,  // oggetti - oro
          default: 0x555555  // pavimento - grigio
        };

        // Per ogni riga nella griglia
        for (let y = 0; y < this.mapData.griglia.length; y++) {
          const row = this.mapData.griglia[y];
          if (!row || !Array.isArray(row)) continue;

          // Per ogni colonna nella riga
          for (let x = 0; x < row.length; x++) {
            const tileId = row[x];
            if (!tileId) continue; // Salta i tile vuoti

            // Determina la texture o colore per questo tile
            let tileElement;
            if (this.textures[tileId] || this.textures.floor) {
              // Usa texture se disponibile
              const texture = this.textures[tileId] || this.textures.floor;
              tileElement = new PIXI.Sprite(texture);
            } else {
              // Altrimenti usa un grafico colorato
              const tileColor = tileColors[tileId] || tileColors.default;
              tileElement = new PIXI.Graphics();
              tileElement.beginFill(tileColor);
              tileElement.drawRect(0, 0, TILE_SIZE, TILE_SIZE);
              tileElement.endFill();
            }

            // Posiziona il tile
            tileElement.x = x * TILE_SIZE;
            tileElement.y = y * TILE_SIZE;
            tileElement.width = TILE_SIZE;
            tileElement.height = TILE_SIZE;

            // Aggiungi al container temporaneo
            tempContainer.addChild(tileElement);
          }
        }
      }

      // Crea la RenderTexture con le dimensioni della mappa
      this.staticCache = PIXI.RenderTexture.create({
        width: width * TILE_SIZE,
        height: height * TILE_SIZE
      });

      // Renderizza il container temporaneo nella texture
      this.app.renderer.render(tempContainer, {
        renderTexture: this.staticCache,
        clear: true
      });

      // Crea uno sprite che usa la texture cacheata
      this.staticSprite = new PIXI.Sprite(this.staticCache);
      this.staticSprite.name = 'static-map-cache';
      
      // Aggiungi lo sprite al viewport come primo elemento (sotto gli altri)
      this.viewport.addChildAt(this.staticSprite, 0);

      // Reset del flag dirty
      this.isDirty = false;

      console.log(`Cache statica generata: ${width}x${height} tiles`);
    } catch (error) {
      console.error("Errore nella generazione della cache statica:", error);
    } finally {
      // Pulisci il container temporaneo
      tempContainer.destroy({ children: true });
    }
  }

  /**
   * Renderizza elementi dinamici (NPC, oggetti interattivi, ecc.)
   */
  renderDynamicElements() {
    // Pulisci il container degli elementi dinamici
    while (this.dynamicContainer.children.length > 0) {
      const child = this.dynamicContainer.children[0];
      this.dynamicContainer.removeChild(child);
      child.destroy({ children: true });
    }

    try {
      // Rendering degli oggetti
      if (this.mapData.oggetti) {
        const objectsContainer = new PIXI.Container();
        objectsContainer.name = 'objects-layer';

        for (const [posizione, oggetto] of Object.entries(this.mapData.oggetti)) {
          // Estrai le coordinate dalla stringa (x, y)
          const match = posizione.match(/\((\d+),\s*(\d+)\)/);
          if (!match) continue;

          const x = parseInt(match[1], 10);
          const y = parseInt(match[2], 10);

          // Crea un grafico per l'oggetto
          const objectGraphic = new PIXI.Graphics();
          
          if (oggetto.tipo === 'porta') {
            objectGraphic.beginFill(0x8B4513);
          } else if (oggetto.tipo === 'oggetto_interattivo') {
            objectGraphic.beginFill(0xFFD700);
          } else {
            objectGraphic.beginFill(0x00FF00);
          }
          
          objectGraphic.drawRect(0, 0, TILE_SIZE, TILE_SIZE);
          objectGraphic.endFill();
          objectGraphic.position.set(x * TILE_SIZE, y * TILE_SIZE);
          
          // Aggiungi metadati all'oggetto
          objectGraphic.objectData = oggetto;
          objectGraphic.interactive = true;
          objectGraphic.buttonMode = true;
          
          objectsContainer.addChild(objectGraphic);

          // Aggiungi etichetta dell'oggetto
          const label = new PIXI.Text(oggetto.nome, {
            fontFamily: 'Arial',
            fontSize: 10,
            fill: 0xFFFFFF,
            stroke: 0x000000,
            strokeThickness: 2
          });
          label.position.set(x * TILE_SIZE + 2, y * TILE_SIZE + 2);
          objectsContainer.addChild(label);
        }

        this.dynamicContainer.addChild(objectsContainer);
      }

      // Rendering degli NPC
      if (this.mapData.npg) {
        const npcsContainer = new PIXI.Container();
        npcsContainer.name = 'npcs-layer';

        for (const [posizione, npc] of Object.entries(this.mapData.npg)) {
          // Estrai le coordinate dalla stringa (x, y)
          const match = posizione.match(/\((\d+),\s*(\d+)\)/);
          if (!match) continue;

          const x = parseInt(match[1], 10);
          const y = parseInt(match[2], 10);

          // Crea un grafico per l'NPC
          const npcGraphic = new PIXI.Graphics();
          npcGraphic.beginFill(0x0000FF);
          npcGraphic.drawCircle(TILE_SIZE / 2, TILE_SIZE / 2, TILE_SIZE / 3);
          npcGraphic.endFill();
          npcGraphic.position.set(x * TILE_SIZE, y * TILE_SIZE);
          
          // Aggiungi metadati all'NPC
          npcGraphic.npcData = npc;
          npcGraphic.interactive = true;
          npcGraphic.buttonMode = true;
          
          npcsContainer.addChild(npcGraphic);

          // Aggiungi etichetta dell'NPC
          const label = new PIXI.Text(npc.nome || 'NPC', {
            fontFamily: 'Arial',
            fontSize: 10,
            fill: 0xFFFFFF,
            stroke: 0x000000,
            strokeThickness: 2
          });
          label.position.set(x * TILE_SIZE + 2, y * TILE_SIZE - 12);
          npcsContainer.addChild(label);
        }

        this.dynamicContainer.addChild(npcsContainer);
      }
    } catch (error) {
      console.error("Errore nel rendering degli elementi dinamici:", error);
    }
  }

  /**
   * Segnala che la cache deve essere rigenerata
   */
  invalidateCache() {
    this.isDirty = true;
  }
  
  /**
   * Aggiorna una posizione specifica della mappa
   * @param {number} x - Coordinata X in tile
   * @param {number} y - Coordinata Y in tile
   * @param {number} newTileId - Nuovo ID tile
   */
  updateTile(x, y, newTileId) {
    if (!this.mapData || !this.mapData.griglia) return;
    
    // Aggiorna il dato nella griglia
    if (y >= 0 && y < this.mapData.griglia.length) {
      const row = this.mapData.griglia[y];
      if (row && x >= 0 && x < row.length) {
        row[x] = newTileId;
        
        // Invalida la cache per forzare la rigenerazione
        this.invalidateCache();
      }
    }
  }
  
  /**
   * Aggiorna un oggetto sulla mappa
   * @param {string} position - Posizione dell'oggetto (x,y)
   * @param {Object} newObjectData - Nuovi dati dell'oggetto
   */
  updateObject(position, newObjectData) {
    if (!this.mapData || !this.mapData.oggetti) return;
    
    // Aggiorna l'oggetto
    if (this.mapData.oggetti[position]) {
      this.mapData.oggetti[position] = newObjectData;
      
      // Aggiorna solo gli elementi dinamici (non serve rigenerare la cache)
      this.renderDynamicElements();
    }
  }
  
  /**
   * Distrugge il renderer e libera le risorse
   */
  destroy() {
    try {
      // Pulisci il container degli elementi dinamici
      if (this.dynamicContainer) {
        this.dynamicContainer.destroy({ children: true });
        this.dynamicContainer = null;
      }
      
      // Distruggi la cache statica
      if (this.staticCache) {
        this.staticCache.destroy(true);
        this.staticCache = null;
      }
      
      // Distruggi lo sprite statico
      if (this.staticSprite) {
        this.staticSprite.destroy();
        this.staticSprite = null;
      }
      
      // Reset delle variabili
      this.viewport = null;
      this.mapData = null;
      this.app = null;
      this.isInitialized = false;
      
      return true;
    } catch (error) {
      console.error("Errore nella distruzione del renderer:", error);
      return false;
    }
  }
} 