import * as PIXI from 'pixi.js';
// Tutti i moduli necessari sono disponibili direttamente da PIXI
// import { utils, settings, Rectangle, Point } from '@pixi/core';

// Costanti per il rendering
const TILE_SIZE = 64;
const GRID_COLOR = 0x444444;
const GRID_ALPHA = 0.3;

/**
 * Utility per il rendering della mappa con Pixi.js
 */
export default class MapRenderer {
  /**
   * Renderizza una griglia sulla mappa
   * @param {PIXI.Container} container - Container Pixi dove disegnare
   * @param {number} width - Larghezza della mappa in tile
   * @param {number} height - Altezza della mappa in tile
   */
  static drawGrid(container, width, height) {
    const graphics = new PIXI.Graphics();
    graphics.lineStyle(1, GRID_COLOR, GRID_ALPHA);
    
    // Disegna le linee verticali
    for (let x = 0; x <= width; x++) {
      graphics.moveTo(x * TILE_SIZE, 0);
      graphics.lineTo(x * TILE_SIZE, height * TILE_SIZE);
    }
    
    // Disegna le linee orizzontali
    for (let y = 0; y <= height; y++) {
      graphics.moveTo(0, y * TILE_SIZE);
      graphics.lineTo(width * TILE_SIZE, y * TILE_SIZE);
    }
    
    container.addChild(graphics);
    return graphics;
  }
  
  /**
   * Disegna il pavimento predefinito per le celle vuote
   * @param {PIXI.Container} container - Container Pixi dove disegnare
   * @param {number} width - Larghezza della mappa in tile
   * @param {number} height - Altezza della mappa in tile
   * @param {PIXI.Texture} texture - Texture da usare per il pavimento
   */
  static drawDefaultFloor(container, width, height, texture) {
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const sprite = new PIXI.Sprite(texture);
        sprite.x = x * TILE_SIZE;
        sprite.y = y * TILE_SIZE;
        sprite.width = TILE_SIZE;
        sprite.height = TILE_SIZE;
        container.addChild(sprite);
      }
    }
  }
  
  /**
   * Renderizza uno strato della mappa
   * @param {PIXI.Container} container - Container Pixi dove disegnare
   * @param {Array} layer - Array con i dati dello strato
   * @param {number} width - Larghezza della mappa in tile
   * @param {number} height - Altezza della mappa in tile
   * @param {Object} textures - Mappa delle texture disponibili
   */
  static drawLayer(container, layer, width, height, textures) {
    const layerContainer = new PIXI.Container();
    
    // Iterazione sui dati dello strato
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        // Ottieni il tile alla posizione corrente
        const tileIndex = y * width + x;
        const tileType = layer[tileIndex];
        
        // Salta i tile vuoti (0 o null)
        if (!tileType) continue;
        
        // Cerca la texture corrispondente
        let texture = textures[tileType];
        
        // Se la texture non è disponibile, usa una texture predefinita
        if (!texture) {
          console.warn(`Texture mancante per il tile tipo ${tileType}`);
          texture = textures.floor || PIXI.Texture.WHITE;
        }
        
        // Crea lo sprite e posizionalo
        const sprite = new PIXI.Sprite(texture);
        sprite.x = x * TILE_SIZE;
        sprite.y = y * TILE_SIZE;
        sprite.width = TILE_SIZE;
        sprite.height = TILE_SIZE;
        
        layerContainer.addChild(sprite);
      }
    }
    
    container.addChild(layerContainer);
    return layerContainer;
  }
  
  /**
   * Renderizza tutti gli strati della mappa
   * @param {PIXI.Container} viewport - Container Pixi dove disegnare
   * @param {Object} mapData - Dati della mappa
   * @param {Object} textures - Mappa delle texture disponibili
   */
  static renderMapLayers(viewport, mapData, textures) {
    // Validazione input rigorosa
    if (!viewport) {
      console.error('Viewport non definito in renderMapLayers');
      return false;
    }

    if (!mapData) {
      console.error('Dati mappa non definiti in renderMapLayers');
      return false;
    }

    if (!textures) {
      console.error('Texture non definite in renderMapLayers');
      return false;
    }
    
    // Verifica che il viewport sia valido e ancora collegato allo stage
    if (!viewport.parent) {
      console.error('Viewport non collegato allo stage, impossibile renderizzare');
      return false;
    }
    
    // Verifica che il viewport abbia children
    if (!viewport.children || !Array.isArray(viewport.children)) {
      console.error('Viewport non ha figli o children non è un array');
      return false;
    }
    
    // Assicuriamoci che il viewport abbia i metodi base necessari 
    if (typeof viewport.addChild !== 'function') {
      console.error('Viewport non è un container PIXI valido, manca il metodo addChild');
      return false;
    }
    
    // Se getChildByName non è disponibile, aggiungiamo un'implementazione
    if (typeof viewport.getChildByName !== 'function') {
      console.log('Aggiunta implementazione di getChildByName al viewport');
      viewport.getChildByName = function(name) {
        if (!this.children) return null;
        return this.children.find(child => child && child.name === name);
      };
    }

    // Assicuriamoci che il metodo addChildAt sia disponibile, altrimenti utilizziamo addChild
    const safeAddChildAt = (parent, child, index) => {
      try {
        if (typeof parent.addChildAt === 'function') {
          parent.addChildAt(child, index);
        } else if (typeof parent.addChild === 'function') {
          parent.addChild(child);
        } else {
          throw new Error('Nessun metodo disponibile per aggiungere un figlio');
        }
      } catch (err) {
        console.error('Errore durante l\'aggiunta del child:', err);
        // Fallback a un addChild semplice
        try {
          parent.addChild(child);
        } catch (finalErr) {
          console.error('Fallimento critico nell\'aggiunta del child:', finalErr);
          return false;
        }
      }
      return true;
    };
    
    // Log del formato della mappa per debug
    console.log(`Inizio renderizzazione mappa: ${mapData.larghezza}x${mapData.altezza} tiles`);
    
    try {
      // Ottieni la dimensione dei tile
      const tileSize = this.TILE_SIZE || 32;
      
      // Definisci colori per diversi tipi di tile - sistema migliorato
      const tileColors = {
        1: 0x333333,  // muri - grigio scuro
        2: 0x8B4513,  // porte - marrone
        3: 0x00FF00,  // erba - verde
        4: 0x0000FF,  // acqua - blu
        5: 0xFFD700,  // oggetti - oro
        default: 0x555555  // pavimento - grigio
      };
      
      // Verifica se esiste già un map-layers container utilizzando getChildByName o una ricerca manuale
      let mapContainer = null;
      
      try {
        // Prima tenta con getChildByName
        mapContainer = viewport.getChildByName('map-layers');
      } catch (nameError) {
        console.warn('Errore usando getChildByName, tentativo ricerca manuale:', nameError);
        // Fallback: ricerca manuale del container per nome
        if (viewport.children) {
          mapContainer = viewport.children.find(child => child && child.name === 'map-layers');
        }
      }
      
      // Se esiste già, rimuovi tutti i figli ma riutilizza il container
      if (mapContainer) {
        console.log('Container map-layers già esistente, riutilizzo con pulizia figli');
        try {
          // Verifica che mapContainer abbia children
          if (!mapContainer.children || !Array.isArray(mapContainer.children)) {
            console.warn('Container esistente senza figli o children non è un array, creazione nuovo container');
            mapContainer = null;
          } else {
            // Rimuovi i figli esistenti
            while (mapContainer.children && mapContainer.children.length > 0) {
              try {
                const child = mapContainer.children[0];
                if (!child) {
                  console.warn("Figlio nullo trovato, salto alla prossima iterazione");
                  mapContainer.children.splice(0, 1);
                  continue;
                }
                mapContainer.removeChild(child);
                if (child && typeof child.destroy === 'function') {
                  child.destroy({ children: true });
                }
              } catch (childError) {
                console.warn('Errore nella rimozione del figlio:', childError);
                // Se c'è un errore, rimuoviamo manualmente l'elemento dall'array
                if (mapContainer.children.length > 0) {
                  mapContainer.children.splice(0, 1);
                } else {
                  break;
                }
              }
            }
          }
        } catch (cleanupError) {
          console.warn('Errore nella pulizia del container esistente:', cleanupError);
          // Creiamo un nuovo container se la pulizia fallisce
          mapContainer = null;
        }
      }
      
      // Se mapContainer è null (non esisteva o è stato invalidato), creane uno nuovo
      if (!mapContainer) {
        // Crea un nuovo container principale per tutti i layer della mappa
        try {
          mapContainer = new PIXI.Container();
          mapContainer.name = 'map-layers';
          
          // Assicurati che sortableChildren sia supportato prima di impostarlo
          try {
            mapContainer.sortableChildren = true;
          } catch (sortError) {
            console.warn('sortableChildren non supportato, z-index non funzionerà', sortError);
          }
          
          // Aggiungi il container al viewport con gestione errori
          const added = safeAddChildAt(viewport, mapContainer, 0);
          if (!added) {
            console.error('Errore nell\'aggiungere il container della mappa al viewport');
            throw new Error('Impossibile aggiungere il container al viewport');
          }
        } catch (containerError) {
          console.error('Errore nella creazione del container:', containerError);
          return false;
        }
      }
      
      // Renderizza una griglia di base come fallback visivo
      try {
        const gridGraphics = new PIXI.Graphics();
        gridGraphics.lineStyle(1, 0x333333, 0.5);
        
        // Disegna linee verticali
        for (let x = 0; x <= mapData.larghezza; x++) {
          gridGraphics.moveTo(x * tileSize, 0);
          gridGraphics.lineTo(x * tileSize, mapData.altezza * tileSize);
        }
        
        // Disegna linee orizzontali
        for (let y = 0; y <= mapData.altezza; y++) {
          gridGraphics.moveTo(0, y * tileSize);
          gridGraphics.lineTo(mapData.larghezza * tileSize, y * tileSize);
        }
        
        mapContainer.addChild(gridGraphics);
      } catch (gridError) {
        console.warn('Errore nel disegno della griglia di base:', gridError);
        // Continua comunque, la griglia è solo visiva
      }
      
      // Controlla il formato della mappa e usa il metodo appropriato
      let renderingSuccess = false;
      
      if (mapData.griglia && Array.isArray(mapData.griglia)) {
        try {
          console.log('Rendering mappa con formato griglia (array di array)');
          
          // Crea un container per i tile
          const tilesContainer = new PIXI.Container();
          tilesContainer.name = 'tiles-layer';
          mapContainer.addChild(tilesContainer);
          
          // Per ogni riga nella griglia
          for (let y = 0; y < mapData.griglia.length; y++) {
            const row = mapData.griglia[y];
            
            // Per ogni colonna nella riga
            if (row && Array.isArray(row)) {
              for (let x = 0; x < row.length; x++) {
                try {
                  const tileId = row[x];
                  
                  // Inizializza un elemento da aggiungere
                  let tileElement = null;
                  
                  // Determina il colore in base al tipo di tile
                  const tileColor = tileColors[tileId] || tileColors.default;
                  
                  // Usa sempre Graphics per il rendering dei tile
                  tileElement = new PIXI.Graphics();
                  tileElement.beginFill(tileColor);
                  tileElement.drawRect(0, 0, tileSize, tileSize);
                  tileElement.endFill();
                  
                  // Aggiungi metadati al tile per funzionalità future
                  tileElement.tileId = tileId;
                  tileElement.tileX = x;
                  tileElement.tileY = y;
                  
                  // Posiziona il tile
                  tileElement.position.set(x * tileSize, y * tileSize);
                  
                  // Aggiungi al container
                  tilesContainer.addChild(tileElement);
                } catch (tileError) {
                  console.warn(`Errore nel rendering del tile (${x}, ${y}):`, tileError);
                  // Continua con il prossimo tile
                }
              }
            }
          }
          
          renderingSuccess = true;
        } catch (gridRenderError) {
          console.error('Errore nel rendering del formato griglia:', gridRenderError);
        }
        
        // Gestisci gli oggetti
        try {
          if (mapData.oggetti) {
            console.log('Rendering oggetti mappa:', mapData.oggetti);
            
            // Crea un container per gli oggetti
            const objectsContainer = new PIXI.Container();
            objectsContainer.name = 'objects-layer';
            objectsContainer.zIndex = 10; // Sopra i tile
            mapContainer.addChild(objectsContainer);
            
            // Itera su tutti gli oggetti
            for (const [posizione, oggetto] of Object.entries(mapData.oggetti)) {
              try {
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
                
                objectGraphic.drawRect(0, 0, tileSize, tileSize);
                objectGraphic.endFill();
                objectGraphic.position.set(x * tileSize, y * tileSize);
                objectsContainer.addChild(objectGraphic);
                
                // Aggiungi etichetta dell'oggetto
                const label = new PIXI.Text(oggetto.nome, {
                  fontFamily: 'Arial',
                  fontSize: 10,
                  fill: 0xFFFFFF,
                  stroke: 0x000000,
                  strokeThickness: 2
                });
                label.position.set(x * tileSize + 2, y * tileSize + 2);
                objectsContainer.addChild(label);
              } catch (objErr) {
                console.warn(`Errore nel rendering dell'oggetto in posizione ${posizione}:`, objErr);
                // Continua con l'oggetto successivo
              }
            }
          }
        } catch (objectsError) {
          console.warn('Errore nel rendering degli oggetti:', objectsError);
          // Continua comunque, gli oggetti non sono essenziali
        }
        
        // Gestisci gli NPC
        try {
          if (mapData.npg) {
            console.log('Rendering NPC mappa:', mapData.npg);
            
            // Crea un container per gli NPC
            const npcsContainer = new PIXI.Container();
            npcsContainer.name = 'npcs-layer';
            npcsContainer.zIndex = 20; // Sopra gli oggetti
            mapContainer.addChild(npcsContainer);
            
            // Itera su tutti gli NPC
            for (const [posizione, npc] of Object.entries(mapData.npg)) {
              try {
                // Estrai le coordinate dalla stringa (x, y)
                const match = posizione.match(/\((\d+),\s*(\d+)\)/);
                if (!match) continue;
                
                const x = parseInt(match[1], 10);
                const y = parseInt(match[2], 10);
                
                // Crea un grafico per l'NPC
                const npcGraphic = new PIXI.Graphics();
                npcGraphic.beginFill(0x0000FF);
                npcGraphic.drawCircle(tileSize / 2, tileSize / 2, tileSize / 3);
                npcGraphic.endFill();
                npcGraphic.position.set(x * tileSize, y * tileSize);
                npcsContainer.addChild(npcGraphic);
                
                // Aggiungi etichetta dell'NPC
                const label = new PIXI.Text(npc.nome || 'NPC', {
                  fontFamily: 'Arial',
                  fontSize: 10,
                  fill: 0xFFFFFF,
                  stroke: 0x000000,
                  strokeThickness: 2
                });
                label.position.set(x * tileSize + 2, y * tileSize - 12);
                npcsContainer.addChild(label);
              } catch (npcErr) {
                console.warn(`Errore nel rendering dell'NPC in posizione ${posizione}:`, npcErr);
                // Continua con l'NPC successivo
              }
            }
          }
        } catch (npcsError) {
          console.warn('Errore nel rendering degli NPC:', npcsError);
          // Continua comunque, gli NPC non sono essenziali
        }
      } else {
        // Implementazione alternativa per altri formati di mappa...
        console.warn('Formato mappa non supportato:', mapData);
      }
      
      // Forza un aggiornamento in base allo z-index se sortableChildren è supportato
      try {
        if (mapContainer.sortableChildren) {
          mapContainer.sortChildren();
        }
      } catch (sortError) {
        console.warn('Errore nell\'ordinamento dei layer:', sortError);
        // Non blocchiamo il rendering per un errore di ordinamento
      }
      
      // Forza un rendering finale se possibile
      try {
        if (viewport.parent && viewport.parent.parent) {
          const app = viewport.parent.parent;
          if (app && app.renderer && typeof app.renderer.render === 'function') {
            app.renderer.render(app.stage);
          }
        }
      } catch (renderError) {
        console.warn('Errore nel forzare il rendering finale:', renderError);
        // Non blocchiamo il completamento per un errore di rendering finale
      }
      
      return renderingSuccess || true; // Ritorna true se il rendering base è riuscito
    } catch (globalError) {
      console.error('Errore critico nel rendering della mappa:', globalError);
      return false;
    }
  }
  
  /**
   * Crea uno sprite per un'entità
   * @param {string} type - Tipo di entità
   * @param {Object} entityData - Dati dell'entità
   * @param {Object} textures - Texture disponibili
   * @returns {PIXI.Sprite} - Sprite dell'entità
   */
  static createEntitySprite(type, entityData, textures) {
    try {
      // Usa la texture del tipo specifico o una generica di fallback
      const texture = textures[type] || textures.npc || PIXI.Texture.WHITE;
      
      // Crea lo sprite
      const sprite = new PIXI.Sprite(texture);
      
      // Imposta le proprietà dello sprite
      const tileSize = this.TILE_SIZE || 32;
      sprite.x = entityData.x * tileSize;
      sprite.y = entityData.y * tileSize;
      sprite.width = tileSize;
      sprite.height = tileSize;
      
      // Configura l'interattività
      sprite.interactive = true;
      sprite.buttonMode = true;
      
      // Aggiungi i dati dell'entità come metadati
      sprite.entityData = entityData;
      
      return sprite;
    } catch (error) {
      console.warn(`Errore nella creazione dello sprite per l'entità di tipo ${type}:`, error);
      
      // Crea uno sprite di fallback
      const fallbackSprite = new PIXI.Sprite(PIXI.Texture.WHITE);
      fallbackSprite.tint = 0xFF0000; // Colore rosso per evidenziare l'errore
      fallbackSprite.alpha = 0.5;
      
      // Imposta le proprietà minime dello sprite
      const tileSize = this.TILE_SIZE || 32;
      fallbackSprite.x = (entityData.x || 0) * tileSize;
      fallbackSprite.y = (entityData.y || 0) * tileSize;
      fallbackSprite.width = tileSize;
      fallbackSprite.height = tileSize;
      
      // Configura comunque l'interattività di base
      fallbackSprite.interactive = true;
      fallbackSprite.buttonMode = true;
      
      // Aggiungi i dati dell'entità come metadati
      fallbackSprite.entityData = entityData;
      
      return fallbackSprite;
    }
  }
  
  /**
   * Crea un'etichetta con il nome dell'entità
   * @param {string} text - Testo da mostrare
   * @param {number} x - Posizione X
   * @param {number} y - Posizione Y
   * @returns {PIXI.Text} - Oggetto Text creato
   */
  static createEntityLabel(text, x, y) {
    const style = new PIXI.TextStyle({
      fontFamily: 'Arial',
      fontSize: 12,
      fill: '#ffffff',
      stroke: '#000000',
      strokeThickness: 3,
      align: 'center'
    });
    
    const label = new PIXI.Text(text, style);
    label.anchor.set(0.5, 1); // Allinea il testo al centro-basso
    label.x = x;
    label.y = y;
    
    return label;
  }
  
  /**
   * Evidenzia un tile sulla mappa
   * @param {PIXI.Container} container - Container Pixi dove disegnare
   * @param {number} x - Coordinata X del tile
   * @param {number} y - Coordinata Y del tile
   * @param {number} color - Colore dell'evidenziazione
   * @param {number} alpha - Trasparenza dell'evidenziazione
   * @returns {PIXI.Graphics} - Oggetto grafico creato
   */
  static highlightTile(container, x, y, color = 0xffff00, alpha = 0.3) {
    const highlightGraphics = new PIXI.Graphics();
    highlightGraphics.beginFill(color, alpha);
    highlightGraphics.drawRect(
      x * TILE_SIZE,
      y * TILE_SIZE,
      TILE_SIZE,
      TILE_SIZE
    );
    highlightGraphics.endFill();
    
    container.addChild(highlightGraphics);
    return highlightGraphics;
  }
  
  /**
   * Centra la telecamera su una posizione specifica
   * @param {PIXI.Viewport} viewport - Viewport Pixi
   * @param {number} x - Coordinata X in tile
   * @param {number} y - Coordinata Y in tile
   */
  static centerCamera(viewport, x, y) {
    if (!viewport) return;
    
    // Converti le coordinate da tile a pixel
    const pixelX = x * TILE_SIZE + TILE_SIZE / 2;
    const pixelY = y * TILE_SIZE + TILE_SIZE / 2;
    
    // Centra il viewport su quelle coordinate
    viewport.moveCenter(pixelX, pixelY);
    
    // Opzionalmente, applica una breve animazione per rendere lo spostamento più fluido
    if (viewport.plugins && viewport.plugins.animate) {
      viewport.plugins.animate.to({
        position: { x: pixelX, y: pixelY },
        time: 300, // Durata in ms
        ease: 'easeInOutSine' // Funzione di easing
      });
    }
  }
  
  /**
   * Costante per la dimensione dei tile
   * @type {number}
   */
  static get TILE_SIZE() {
    return TILE_SIZE;
  }
} 