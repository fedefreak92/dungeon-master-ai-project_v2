/**
 * index.js
 * Punto di ingresso principale per il modulo Pixi
 * Esporta tutte le componenti necessarie per l'uso in altri moduli
 */

// Importa il PixiManager principale
import * as PIXI from 'pixi.js';
import GridMapRenderer from './utils/GridMapRenderer';
import { pixiManager } from './PixiManager';

// Esporta i componenti principali
export { 
  PIXI,
  GridMapRenderer,
  pixiManager
};

// Esporta per accesso diretto
export default pixiManager;

// Esporta i gestori individuali per uso avanzato
export { default as SceneManager } from './core/SceneManager';
export { default as EntityManager } from './entities/EntityManager';
export { default as MapManager } from './map/MapManager';
export { default as SpriteSheetManager } from './utils/SpriteSheetManager';
export { default as AssetLoader } from './utils/AssetLoader';
export { default as FilterManager } from './utils/FilterManager';

/**
 * Inizializza il sistema Pixi.js
 * Funzione di convenienza per inizializzare il pixiManager
 * 
 * @param {Object} options - Opzioni di configurazione
 * @returns {PIXI.Application} - L'istanza dell'applicazione PIXI
 */
export function initializePixi(options = {}) {
  const { pixiManager } = require('./PixiManager');
  return pixiManager.initialize(options);
}

/**
 * Pulisce tutte le risorse Pixi.js
 * Funzione di convenienza per la pulizia del pixiManager
 */
export function cleanupPixi() {
  const { pixiManager } = require('./PixiManager');
  return pixiManager.cleanup();
} 