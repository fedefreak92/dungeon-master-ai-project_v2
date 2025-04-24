/**
 * Utility per il rendering condivise tra PIXI.js e Canvas 2D
 */

// Dimensione predefinita dei tile
export const TILE_SIZE = 64;

// Colori per i vari tipi di tile
export const TILE_COLORS = {
  1: 0x333333, // muri - grigio scuro
  2: 0x8B4513, // porte - marrone
  3: 0x00FF00, // erba - verde
  4: 0x0000FF, // acqua - blu
  5: 0xFFD700, // oggetti - oro
  default: 0x555555 // pavimento - grigio
};

// Colori in formato CSS per Canvas 2D
export const TILE_COLORS_CSS = {
  1: '#333333', // muri - grigio scuro
  2: '#8B4513', // porte - marrone
  3: '#00FF00', // erba - verde
  4: '#0000FF', // acqua - blu
  5: '#FFD700', // oggetti - oro
  default: '#555555' // pavimento - grigio
};

/**
 * Converte le coordinate del mouse in coordinate della griglia
 * @param {number} mouseX - Coordinata X del mouse
 * @param {number} mouseY - Coordinata Y del mouse
 * @param {number} tileSize - Dimensione di un tile
 * @param {number} offsetX - Offset X
 * @param {number} offsetY - Offset Y
 * @returns {Object} - Coordinate della griglia {x, y}
 */
export function mouseToGridCoords(mouseX, mouseY, tileSize = TILE_SIZE, offsetX = 0, offsetY = 0) {
  const gridX = Math.floor((mouseX - offsetX) / tileSize);
  const gridY = Math.floor((mouseY - offsetY) / tileSize);
  return { x: gridX, y: gridY };
}

/**
 * Ottimizza i dati della mappa per il rendering
 * @param {Object} rawMapData - Dati grezzi della mappa
 * @returns {Object} - Dati ottimizzati
 */
export function optimizeMapData(rawMapData) {
  if (!rawMapData) return null;
  
  // Copia di base per evitare modifiche all'originale
  const mapData = {
    width: rawMapData.larghezza || 0,
    height: rawMapData.altezza || 0,
    tiles: [],
    objects: [],
    npcs: []
  };
  
  // Normalizza i tile
  if (rawMapData.griglia && Array.isArray(rawMapData.griglia)) {
    mapData.tiles = rawMapData.griglia.map(row => {
      if (Array.isArray(row)) {
        return [...row];
      }
      return [];
    });
    
    // Assicura che width e height siano corretti
    if (mapData.tiles.length > 0) {
      mapData.height = mapData.tiles.length;
      mapData.width = mapData.tiles[0].length;
    }
  }
  
  // Normalizza gli oggetti
  if (rawMapData.oggetti) {
    for (const [posizione, oggetto] of Object.entries(rawMapData.oggetti)) {
      const match = posizione.match(/\((\d+),\s*(\d+)\)/);
      if (!match) continue;
      
      const x = parseInt(match[1], 10);
      const y = parseInt(match[2], 10);
      
      mapData.objects.push({
        x,
        y,
        name: oggetto.nome || 'Oggetto',
        type: oggetto.tipo || 'generic',
        data: oggetto
      });
    }
  }
  
  // Normalizza gli NPC
  if (rawMapData.npg) {
    for (const [posizione, npc] of Object.entries(rawMapData.npg)) {
      const match = posizione.match(/\((\d+),\s*(\d+)\)/);
      if (!match) continue;
      
      const x = parseInt(match[1], 10);
      const y = parseInt(match[2], 10);
      
      mapData.npcs.push({
        x,
        y,
        name: npc.nome || 'NPC',
        type: npc.tipo || 'generic',
        data: npc
      });
    }
  }
  
  return mapData;
}

/**
 * Disegna un tile colorato
 * @param {CanvasRenderingContext2D} ctx - Contesto 2D del canvas
 * @param {number} x - Coordinata X
 * @param {number} y - Coordinata Y
 * @param {string} color - Colore del tile
 * @param {number} size - Dimensione del tile
 */
export function drawColoredTile(ctx, x, y, color, size = TILE_SIZE) {
  ctx.fillStyle = color;
  ctx.fillRect(x * size, y * size, size, size);
}

/**
 * Disegna testo su un canvas
 * @param {CanvasRenderingContext2D} ctx - Contesto 2D del canvas
 * @param {string} text - Testo da disegnare
 * @param {number} x - Coordinata X
 * @param {number} y - Coordinata Y
 * @param {Object} options - Opzioni di stile
 */
export function drawText(ctx, text, x, y, options = {}) {
  const {
    fillColor = '#ffffff',
    strokeColor = '#000000',
    font = '12px Arial',
    strokeWidth = 2,
    align = 'left'
  } = options;
  
  ctx.font = font;
  ctx.textAlign = align;
  
  if (strokeColor && strokeWidth) {
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = strokeWidth;
    ctx.strokeText(text, x, y);
  }
  
  ctx.fillStyle = fillColor;
  ctx.fillText(text, x, y);
}

/**
 * Disegna un cerchio su un canvas
 * @param {CanvasRenderingContext2D} ctx - Contesto 2D del canvas
 * @param {number} x - Coordinata X del centro
 * @param {number} y - Coordinata Y del centro
 * @param {number} radius - Raggio del cerchio
 * @param {string} color - Colore di riempimento
 */
export function drawCircle(ctx, x, y, radius, color) {
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(x, y, radius, 0, Math.PI * 2);
  ctx.fill();
}

/**
 * Verifica se un punto è all'interno di un rettangolo
 * @param {number} px - Coordinata X del punto
 * @param {number} py - Coordinata Y del punto
 * @param {number} rx - Coordinata X del rettangolo
 * @param {number} ry - Coordinata Y del rettangolo
 * @param {number} rw - Larghezza del rettangolo
 * @param {number} rh - Altezza del rettangolo
 * @returns {boolean} - true se il punto è all'interno del rettangolo
 */
export function pointInRect(px, py, rx, ry, rw, rh) {
  return px >= rx && px <= rx + rw && py >= ry && py <= ry + rh;
} 