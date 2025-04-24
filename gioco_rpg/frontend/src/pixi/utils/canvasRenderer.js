/**
 * Renderer alternativo basato su Canvas 2D per massima compatibilità
 * Serve come fallback quando WebGL non è disponibile o ci sono problemi con PIXI.js
 */
export class CanvasRenderer {
  /**
   * Inizializza il renderer canvas
   * @param {HTMLCanvasElement} canvas - Elemento canvas da utilizzare
   * @param {number} width - Larghezza iniziale
   * @param {number} height - Altezza iniziale
   */
  constructor(canvas, width = 800, height = 600) {
    this.canvas = canvas || document.createElement('canvas');
    this.ctx = this.canvas.getContext('2d');
    this.width = width;
    this.height = height;
    this.tileSize = 64;
    this.debugMode = false;
    
    // Colori predefiniti per i vari tipi di tile
    this.tileColors = {
      1: '#333333', // muri - grigio scuro
      2: '#8B4513', // porte - marrone
      3: '#00FF00', // erba - verde
      4: '#0000FF', // acqua - blu
      5: '#FFD700', // oggetti - oro
      default: '#555555' // pavimento - grigio
    };
    
    // Cache delle immagini caricate
    this.imageCache = new Map();
    
    // Configura il canvas
    this.resize(width, height);
  }
  
  /**
   * Ridimensiona il canvas
   * @param {number} width - Nuova larghezza
   * @param {number} height - Nuova altezza
   */
  resize(width, height) {
    this.width = width;
    this.height = height;
    this.canvas.width = width;
    this.canvas.height = height;
    
    // Reimposta il contesto dopo il ridimensionamento
    this.ctx = this.canvas.getContext('2d');
    this.ctx.imageSmoothingEnabled = false; // Pixel art croccante
  }
  
  /**
   * Pulisce il canvas
   * @param {string} color - Colore di sfondo
   */
  clear(color = '#1a1a1a') {
    this.ctx.fillStyle = color;
    this.ctx.fillRect(0, 0, this.width, this.height);
  }
  
  /**
   * Renderizza una mappa completa
   * @param {Object} mapData - Dati della mappa
   */
  renderMap(mapData) {
    if (!mapData) return false;
    
    // Pulisci il canvas
    this.clear();
    
    const width = mapData.larghezza || (mapData.griglia ? mapData.griglia[0].length : 0);
    const height = mapData.altezza || (mapData.griglia ? mapData.griglia.length : 0);
    
    // Disegna la griglia di base
    this.drawGrid(width, height);
    
    // Renderizza i tile della mappa
    if (mapData.griglia && Array.isArray(mapData.griglia)) {
      this.renderTiles(mapData.griglia);
    }
    
    // Renderizza gli oggetti
    if (mapData.oggetti) {
      this.renderObjects(mapData.oggetti);
    }
    
    // Renderizza gli NPC
    if (mapData.npg) {
      this.renderNPCs(mapData.npg);
    }
    
    return true;
  }
  
  /**
   * Disegna una griglia sul canvas
   * @param {number} width - Larghezza in tile
   * @param {number} height - Altezza in tile
   */
  drawGrid(width, height) {
    const tileSize = this.tileSize;
    
    this.ctx.strokeStyle = '#444444';
    this.ctx.lineWidth = 0.5;
    this.ctx.globalAlpha = 0.3;
    
    // Disegna linee verticali
    for (let x = 0; x <= width; x++) {
      this.ctx.beginPath();
      this.ctx.moveTo(x * tileSize, 0);
      this.ctx.lineTo(x * tileSize, height * tileSize);
      this.ctx.stroke();
    }
    
    // Disegna linee orizzontali
    for (let y = 0; y <= height; y++) {
      this.ctx.beginPath();
      this.ctx.moveTo(0, y * tileSize);
      this.ctx.lineTo(width * tileSize, y * tileSize);
      this.ctx.stroke();
    }
    
    // Ripristina l'opacità
    this.ctx.globalAlpha = 1.0;
  }
  
  /**
   * Renderizza i tile della mappa
   * @param {Array} grid - Griglia dei tile
   */
  renderTiles(grid) {
    const tileSize = this.tileSize;
    
    // Per ogni riga nella griglia
    for (let y = 0; y < grid.length; y++) {
      const row = grid[y];
      
      // Per ogni colonna nella riga
      if (row && Array.isArray(row)) {
        for (let x = 0; x < row.length; x++) {
          const tileId = row[x];
          
          // Salta i tile vuoti
          if (!tileId) continue;
          
          // Ottieni il colore corrispondente al tipo di tile
          const color = this.tileColors[tileId] || this.tileColors.default;
          
          // Disegna il tile come rettangolo colorato
          this.ctx.fillStyle = color;
          this.ctx.fillRect(x * tileSize, y * tileSize, tileSize, tileSize);
          
          // In modalità debug, aggiungi un'etichetta con l'ID del tile
          if (this.debugMode) {
            this.ctx.fillStyle = 'white';
            this.ctx.font = '10px Arial';
            this.ctx.fillText(`${tileId}`, x * tileSize + 5, y * tileSize + 15);
          }
        }
      }
    }
  }
  
  /**
   * Renderizza gli oggetti sulla mappa
   * @param {Object} objects - Oggetti della mappa
   */
  renderObjects(objects) {
    const tileSize = this.tileSize;
    
    this.ctx.font = '10px Arial';
    
    for (const [posizione, oggetto] of Object.entries(objects)) {
      // Estrai le coordinate dalla stringa (x, y)
      const match = posizione.match(/\((\d+),\s*(\d+)\)/);
      if (!match) continue;
      
      const x = parseInt(match[1], 10);
      const y = parseInt(match[2], 10);
      
      // Disegna il background dell'oggetto
      if (oggetto.tipo === 'porta') {
        this.ctx.fillStyle = '#8B4513'; // Marrone per le porte
      } else if (oggetto.tipo === 'oggetto_interattivo') {
        this.ctx.fillStyle = '#FFD700'; // Oro per oggetti interattivi
      } else {
        this.ctx.fillStyle = '#00FF00'; // Verde per altri oggetti
      }
      
      this.ctx.fillRect(x * tileSize, y * tileSize, tileSize, tileSize);
      
      // Etichetta dell'oggetto
      this.ctx.fillStyle = 'white';
      this.ctx.strokeStyle = 'black';
      this.ctx.lineWidth = 2;
      this.ctx.strokeText(oggetto.nome, x * tileSize + 2, y * tileSize + 12);
      this.ctx.fillText(oggetto.nome, x * tileSize + 2, y * tileSize + 12);
    }
  }
  
  /**
   * Renderizza gli NPC sulla mappa
   * @param {Object} npcs - NPC della mappa
   */
  renderNPCs(npcs) {
    const tileSize = this.tileSize;
    
    for (const [posizione, npc] of Object.entries(npcs)) {
      // Estrai le coordinate dalla stringa (x, y)
      const match = posizione.match(/\((\d+),\s*(\d+)\)/);
      if (!match) continue;
      
      const x = parseInt(match[1], 10);
      const y = parseInt(match[2], 10);
      
      // Disegna un cerchio per rappresentare l'NPC
      this.ctx.fillStyle = '#0000FF';
      this.ctx.beginPath();
      this.ctx.arc(
        x * tileSize + tileSize / 2,
        y * tileSize + tileSize / 2,
        tileSize / 3,
        0,
        Math.PI * 2
      );
      this.ctx.fill();
      
      // Etichetta dell'NPC
      this.ctx.fillStyle = 'white';
      this.ctx.strokeStyle = 'black';
      this.ctx.lineWidth = 2;
      this.ctx.font = '10px Arial';
      this.ctx.strokeText(npc.nome || 'NPC', x * tileSize + 2, y * tileSize - 5);
      this.ctx.fillText(npc.nome || 'NPC', x * tileSize + 2, y * tileSize - 5);
    }
  }
  
  /**
   * Disegna un singolo tile
   * @param {number} tileType - Tipo di tile
   * @param {number} x - Coordinata X in tile
   * @param {number} y - Coordinata Y in tile
   */
  renderTile(tileType, x, y) {
    const tileSize = this.tileSize;
    const color = this.tileColors[tileType] || this.tileColors.default;
    
    this.ctx.fillStyle = color;
    this.ctx.fillRect(x * tileSize, y * tileSize, tileSize, tileSize);
  }
  
  /**
   * Carica un'immagine
   * @param {string} src - URL dell'immagine
   * @returns {Promise<HTMLImageElement>} - Promessa che risolve all'immagine caricata
   */
  loadImage(src) {
    // Se l'immagine è già nella cache, restituiscila
    if (this.imageCache.has(src)) {
      return Promise.resolve(this.imageCache.get(src));
    }
    
    // Altrimenti carica l'immagine
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        this.imageCache.set(src, img);
        resolve(img);
      };
      img.onerror = (err) => {
        reject(new Error(`Impossibile caricare l'immagine: ${src}`));
      };
      img.src = src;
    });
  }
  
  /**
   * Disegna un'immagine sul canvas
   * @param {HTMLImageElement} image - Immagine da disegnare
   * @param {number} x - Coordinata X
   * @param {number} y - Coordinata Y
   * @param {number} width - Larghezza
   * @param {number} height - Altezza
   */
  drawImage(image, x, y, width = this.tileSize, height = this.tileSize) {
    if (!image) return;
    
    try {
      this.ctx.drawImage(image, x, y, width, height);
    } catch (err) {
      console.error('Errore nel disegno dell\'immagine:', err);
    }
  }
  
  /**
   * Disegna testo sul canvas
   * @param {string} text - Testo da disegnare
   * @param {number} x - Coordinata X
   * @param {number} y - Coordinata Y
   * @param {string} color - Colore del testo
   * @param {string} font - Font da usare
   */
  drawText(text, x, y, color = 'white', font = '12px Arial') {
    this.ctx.font = font;
    this.ctx.fillStyle = color;
    this.ctx.fillText(text, x, y);
  }
  
  /**
   * Evidenzia un tile specifico (per selezione)
   * @param {number} x - Coordinata X in tile
   * @param {number} y - Coordinata Y in tile
   * @param {string} color - Colore dell'evidenziazione
   */
  highlightTile(x, y, color = 'rgba(255, 255, 0, 0.3)') {
    const tileSize = this.tileSize;
    
    this.ctx.fillStyle = color;
    this.ctx.fillRect(x * tileSize, y * tileSize, tileSize, tileSize);
  }
  
  /**
   * Pulisce le risorse
   */
  destroy() {
    // Pulisci la cache delle immagini
    this.imageCache.clear();
    
    // Rimuovi i riferimenti
    this.canvas = null;
    this.ctx = null;
    
    console.log('CanvasRenderer: distruzione completata');
  }
}

/**
 * Metodo di utilità per creare un renderer canvas
 * @param {HTMLCanvasElement} canvas - Elemento canvas
 * @param {number} width - Larghezza
 * @param {number} height - Altezza
 * @returns {CanvasRenderer} - Istanza del renderer
 */
export const createCanvasRenderer = (canvas, width, height) => {
  return new CanvasRenderer(canvas, width, height);
}; 