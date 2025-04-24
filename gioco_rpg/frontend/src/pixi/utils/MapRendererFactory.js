/**
 * MapRendererFactory.js
 * Factory per creare il renderer di mappa appropriato in base alle esigenze
 */
import MapRenderer from './MapRenderer';
import OptimizedMapRenderer from './OptimizedMapRenderer';

// Soglie per selezionare automaticamente il renderer ottimizzato
const OPTIMIZED_THRESHOLD_TILES = 50 * 50; // 50x50 tiles
const OPTIMIZED_THRESHOLD_OBJECTS = 100;   // 100 oggetti

/**
 * Factory per creare renderer di mappe
 */
export default class MapRendererFactory {
  /**
   * Crea il renderer di mappa più appropriato per i dati forniti
   * @param {PIXI.Application} app - Applicazione PIXI
   * @param {PIXI.Container} viewport - Container del viewport
   * @param {Object} mapData - Dati della mappa
   * @param {Object} options - Opzioni aggiuntive
   * @returns {Object} - Istanza del renderer creato
   */
  static async createRenderer(app, viewport, mapData, options = {}) {
    // Determina quale renderer utilizzare
    const useOptimized = this.shouldUseOptimizedRenderer(mapData, options);
    
    let renderer;
    
    if (useOptimized) {
      console.log('Utilizzando OptimizedMapRenderer per mappa di grandi dimensioni o complessa');
      renderer = new OptimizedMapRenderer();
    } else {
      console.log('Utilizzando MapRenderer standard');
      renderer = { 
        renderMap: (scene, mapData) => MapRenderer.renderMapLayers(scene, mapData, options.textures || {})
      };
    }
    
    // Se è il renderer ottimizzato, inizializzalo
    if (renderer instanceof OptimizedMapRenderer) {
      await renderer.initialize(app, viewport);
      
      // Carica la mappa
      if (mapData) {
        renderer.loadMap(mapData);
        
        // Renderizza oggetti e NPC
        renderer.renderObjects();
        renderer.renderNPCs();
      }
    }
    
    return renderer;
  }
  
  /**
   * Determina se usare il renderer ottimizzato in base ai dati della mappa
   * @param {Object} mapData - Dati della mappa
   * @param {Object} options - Opzioni aggiuntive
   * @returns {boolean} - true se usare il renderer ottimizzato
   */
  static shouldUseOptimizedRenderer(mapData, options = {}) {
    // Se è specificato esplicitamente nelle opzioni, rispetta la scelta
    if (options.forceOptimized !== undefined) {
      return options.forceOptimized;
    }
    
    // Se non ci sono dati mappa, usa il renderer standard
    if (!mapData) return false;
    
    try {
      // Calcola le dimensioni della mappa
      const width = mapData.larghezza || (mapData.griglia ? mapData.griglia[0].length : 0);
      const height = mapData.altezza || (mapData.griglia ? mapData.griglia.length : 0);
      const totalTiles = width * height;
      
      // Conta gli oggetti
      const objectCount = mapData.oggetti ? Object.keys(mapData.oggetti).length : 0;
      const npcCount = mapData.npg ? Object.keys(mapData.npg).length : 0;
      const totalObjects = objectCount + npcCount;
      
      // Verifica se supera le soglie
      const exceedsTileThreshold = totalTiles > OPTIMIZED_THRESHOLD_TILES;
      const exceedsObjectThreshold = totalObjects > OPTIMIZED_THRESHOLD_OBJECTS;
      
      // Verifica anche prestazioni del dispositivo
      const isLowPerformanceDevice = this.isLowPerformanceDevice();
      
      // Usa il renderer ottimizzato se:
      // - La mappa è grande o ha molti oggetti
      // - Il dispositivo ha prestazioni limitate e la mappa non è piccolissima
      return exceedsTileThreshold || 
             exceedsObjectThreshold || 
             (isLowPerformanceDevice && totalTiles > 20 * 20);
    } catch (error) {
      console.warn("Errore nella determinazione del renderer, uso standard:", error);
      return false;
    }
  }
  
  /**
   * Rileva se il dispositivo ha prestazioni limitate
   * @returns {boolean} - true se il dispositivo ha prestazioni limitate
   */
  static isLowPerformanceDevice() {
    try {
      // Controlla il numero di core logici
      const cpuCores = navigator.hardwareConcurrency || 4;
      
      // Controlla se è un dispositivo mobile
      const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
      
      // Controlla se WebGL è supportato e quale versione
      const canvas = document.createElement('canvas');
      // Verifica il supporto a WebGL (1 o 2)
      const supportsWebGL2 = !!canvas.getContext('webgl2');
      
      // Considera un dispositivo a basse prestazioni se:
      // - Ha meno di 4 core CPU, o
      // - È un dispositivo mobile, o
      // - Non supporta WebGL2
      return cpuCores < 4 || isMobile || !supportsWebGL2;
    } catch (error) {
      console.warn("Errore nel rilevamento delle prestazioni del dispositivo:", error);
      return false;
    }
  }
  
  /**
   * Converte un renderer standard in uno ottimizzato
   * @param {PIXI.Application} app - Applicazione PIXI
   * @param {PIXI.Container} viewport - Container del viewport
   * @param {Object} mapData - Dati della mappa
   * @returns {Promise<OptimizedMapRenderer>} - Il nuovo renderer ottimizzato
   */
  static async upgradeToOptimized(app, viewport, mapData) {
    try {
      console.log('Aggiornamento a renderer ottimizzato...');
      
      // Crea una nuova istanza del renderer ottimizzato
      const optimizedRenderer = new OptimizedMapRenderer();
      
      // Inizializza il renderer
      await optimizedRenderer.initialize(app, viewport);
      
      // Carica la mappa
      if (mapData) {
        optimizedRenderer.loadMap(mapData);
        
        // Renderizza oggetti e NPC
        optimizedRenderer.renderObjects();
        optimizedRenderer.renderNPCs();
      }
      
      return optimizedRenderer;
    } catch (error) {
      console.error("Errore nell'aggiornamento al renderer ottimizzato:", error);
      throw error;
    }
  }
} 