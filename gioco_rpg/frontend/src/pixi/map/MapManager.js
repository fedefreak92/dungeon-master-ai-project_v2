/**
 * MapManager.js
 * Gestisce il caricamento, la validazione e il rendering delle mappe di gioco
 */
import * as PIXI from 'pixi.js';

export default class MapManager {
  constructor() {
    this.currentMap = null;
    this.mapContainer = null;
    this.useOptimizedRenderer = true; // Per default usa il renderer ottimizzato quando possibile
  }
  
  /**
   * Imposta le texture da utilizzare per il rendering della mappa
   * @param {Object} textures - Le texture disponibili
   */
  setTextures(textures) {
    // Funzionalità rimossa
    console.log("setTextures: metodo in attesa di implementazione con nuovo sistema di rendering");
  }
  
  /**
   * Carica una mappa e la renderizza nella scena specificata
   * @param {PIXI.Application} scene - La scena in cui renderizzare la mappa
   * @param {Object} mapData - I dati della mappa da renderizzare
   * @param {Object} options - Opzioni aggiuntive per il rendering
   * @returns {Promise<boolean>} - true se il caricamento e rendering sono riusciti
   */
  async loadMap(scene, mapData, options = {}) {
    try {
      // Validazione di base della mappa
      if (!this.validateMapData(mapData)) {
        console.error("Dati mappa non validi o incompleti");
        return false;
      }
      
      this.currentMap = mapData;
      
      // Verifica i container della scena
      if (!scene.mapContainer) {
        console.warn("Container mappa non trovato nella scena, il setup potrebbe essere incompleto");
        return false;
      }
      
      this.mapContainer = scene.mapContainer;
      
      console.log("Utilizzo nuovo sistema di rendering per la mappa");
      // Utilizza il renderer standard come fallback temporaneo
      return this.renderMapStandard(scene, mapData);
    } catch (error) {
      console.error("Errore nel caricamento della mappa:", error);
      return false;
    }
  }
  
  /**
   * Renderizza una mappa in una scena usando il renderer standard
   * @param {PIXI.Application} scene - La scena in cui renderizzare
   * @param {Object} mapData - I dati della mappa
   * @returns {boolean} - true se il rendering è riuscito
   */
  renderMapStandard(scene, mapData) {
    try {
      // Riferimenti ai container della scena
      const { tileContainer, objectsContainer, npcsContainer } = scene;
      
      // Pulisci i container esistenti
      if (tileContainer) tileContainer.removeChildren();
      if (objectsContainer) objectsContainer.removeChildren();
      if (npcsContainer) npcsContainer.removeChildren();
      
      console.log("renderMapStandard: metodo in attesa di implementazione con nuovo sistema di rendering");
      
      // Ritorno true per il momento per consentire il resto dell'inizializzazione
      return true;
    } catch (error) {
      console.error("Errore nel rendering standard della mappa:", error);
      return false;
    }
  }
  
  /**
   * Renderizza una mappa in una scena specifica utilizzando il renderer ottimale
   * @param {PIXI.Application} scene - Oggetto scena creato con createScene
   * @param {Object} mapData - Dati della mappa da renderizzare
   * @param {Object} options - Opzioni aggiuntive per il rendering
   * @returns {Promise<boolean>} - true se il rendering è riuscito
   */
  async renderMapOptimized(scene, mapData, options = {}) {
    if (!scene || !mapData) {
      console.error("Scene o mapData non validi");
      return false;
    }
    
    try {
      console.log("renderMapOptimized: metodo in attesa di implementazione con nuovo sistema di rendering");
      
      // Fallback al metodo di rendering standard
      return this.renderMapStandard(scene, mapData);
    } catch (error) {
      console.error("Errore nel rendering ottimizzato della mappa:", error);
      return false;
    }
  }
  
  /**
   * Valida i dati della mappa e ne verifica la struttura
   * @param {Object} mapData - Dati della mappa da validare
   * @returns {boolean} - true se i dati sono validi
   */
  validateMapData(mapData) {
    if (!mapData) {
      console.error("Dati mappa mancanti");
      return false;
    }
    
    // Verifica le proprietà essenziali
    if (!mapData.larghezza || !mapData.altezza || !mapData.griglia) {
      console.error("Proprietà essenziali mancanti nei dati mappa:", {
        larghezza: !!mapData.larghezza,
        altezza: !!mapData.altezza,
        griglia: !!mapData.griglia
      });
      return false;
    }
    
    // Verifica la griglia
    if (!Array.isArray(mapData.griglia)) {
      console.error("Griglia non valida, non è un array");
      return false;
    }
    
    // Verifica le dimensioni dichiarate rispetto alla griglia effettiva
    const grigliaNonVuota = mapData.griglia.length > 0;
    if (!grigliaNonVuota) {
      console.error("Griglia vuota nei dati mappa");
      return false;
    }
    
    // Verifica che le dimensioni siano numeri positivi
    if (
      typeof mapData.larghezza !== 'number' || 
      typeof mapData.altezza !== 'number' ||
      mapData.larghezza <= 0 ||
      mapData.altezza <= 0
    ) {
      console.error("Dimensioni mappa non valide:", {
        larghezza: mapData.larghezza,
        altezza: mapData.altezza
      });
      return false;
    }
    
    // Controllo aggiuntivo: se la griglia ha dimensioni coerenti
    const grigliaTroppoCorta = mapData.griglia.length < mapData.altezza;
    const righeNonCoerenti = mapData.griglia.some(row => 
      !Array.isArray(row) || row.length < mapData.larghezza
    );
    
    if (grigliaTroppoCorta || righeNonCoerenti) {
      console.warn("Dimensioni griglia non coerenti con le dimensioni dichiarate");
      console.warn("Questo potrebbe causare problemi di rendering");
      // Non blocchiamo il rendering, ma registriamo l'avviso
    }
    
    // Tutti i controlli passati
    return true;
  }
  
  /**
   * Aggiorna la mappa con nuovi dati (parziale o completo)
   * @param {PIXI.Application} scene - La scena in cui aggiornare
   * @param {Object} mapData - I nuovi dati della mappa o le modifiche
   * @param {Object} options - Opzioni per l'aggiornamento
   * @returns {boolean} - true se l'aggiornamento è riuscito
   */
  updateMap(scene, mapData, options = {}) {
    // Se ci sono nuovi dati completi, sostituisce la mappa corrente
    if (mapData && mapData.griglia) {
      this.currentMap = mapData;
      return this.loadMap(scene, mapData, options);
    }
    
    console.log("updateMap: metodo in attesa di implementazione con nuovo sistema di rendering");
    return false;
  }
  
  /**
   * Pulisce la mappa corrente e libera le risorse
   * @param {PIXI.Application} scene - La scena da cui rimuovere la mappa
   */
  unloadMap(scene) {
    if (!scene) return;
    
    // Pulisci i container
    if (scene.tileContainer) scene.tileContainer.removeChildren();
    if (scene.objectsContainer) scene.objectsContainer.removeChildren();
    if (scene.npcsContainer) scene.npcsContainer.removeChildren();
    
    // Rimuovi il renderer della mappa se presente
    if (scene.mapRenderer) {
      if (typeof scene.mapRenderer.destroy === 'function') {
        scene.mapRenderer.destroy();
      }
      scene.mapRenderer = null;
    }
    
    this.currentMap = null;
    this.mapContainer = null;
  }
} 