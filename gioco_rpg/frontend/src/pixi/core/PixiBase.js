/**
 * PixiBase.js
 * Modulo base che gestisce l'inizializzazione e le funzionalità comuni di PIXI.js
 */
import * as PIXI from 'pixi.js';

export default class PixiBase {
  constructor() {
    this.app = null;
    this.isInitialized = false;
    this.renderMode = 'auto'; // 'auto', 'webgl', o 'canvas'
  }
  
  /**
   * Inizializza il sistema PIXI, chiamare una sola volta all'avvio dell'app
   * @param {Object} options - Opzioni di configurazione per PIXI.Application
   * @returns {PIXI.Application} - L'istanza dell'applicazione PIXI
   */
  initialize(options = {}) {
    if (this.isInitialized) return this.app;
    
    // Determina il renderer migliore da utilizzare
    const preferredRenderer = this.renderMode === 'auto' 
      ? (PIXI.utils.isWebGLSupported() ? 'webgl' : 'canvas')
      : this.renderMode;
    
    try {
      // Configura l'applicazione PIXI con le opzioni fornite e quelle predefinite
      const defaultOptions = {
        width: 800,
        height: 600,
        backgroundColor: 0x1a1a1a,
        resolution: window.devicePixelRatio || 1,
        antialias: true,
        forceCanvas: preferredRenderer === 'canvas',
        autoDensity: true
      };
      
      this.app = new PIXI.Application({
        ...defaultOptions,
        ...options
      });
      
      console.log(`PIXI inizializzato con renderer: ${this.app.renderer.type === PIXI.RENDERER_TYPE.WEBGL ? 'WebGL' : 'Canvas'}`);
      
      PIXI.utils.skipHello(); // Disabilita il messaggio di saluto di PIXI
      
      this.isInitialized = true;
      return this.app;
    } catch (error) {
      console.error("Errore nell'inizializzazione di PIXI:", error);
      
      // Fallback a Canvas se WebGL fallisce
      if (preferredRenderer === 'webgl') {
        console.warn("Fallback a renderer Canvas dopo fallimento WebGL");
        this.renderMode = 'canvas';
        return this.initialize(options);
      }
      
      throw error;
    }
  }

  /**
   * Verifica se il contesto WebGL è valido
   * @param {PIXI.Renderer} renderer - Renderer da verificare
   * @returns {boolean} - true se il contesto è valido, false altrimenti
   */
  isWebGLContextValid(renderer) {
    if (!renderer || !renderer.gl) {
      return false;
    }
    
    try {
      // Tenta un'operazione semplice per verificare se il contesto è valido
      renderer.gl.getParameter(renderer.gl.VERSION);
      return true;
    } catch (e) {
      return false;
    }
  }
  
  /**
   * Pulisce tutte le risorse PIXI e prepara la distruzione
   */
  cleanup() {
    if (!this.app) return;
    
    try {
      // Pulisci il renderer
      if (this.app.renderer) {
        try {
          // Esegui un flush se è disponibile il contesto WebGL
          if (this.app.renderer.gl && typeof this.app.renderer.gl.flush === 'function') {
            this.app.renderer.gl.flush();
          }
          
          // Fai un reset del renderer se possibile
          if (typeof this.app.renderer.reset === 'function') {
            this.app.renderer.reset();
          }
        } catch (rendererError) {
          console.warn('Errore durante cleanup renderer:', rendererError);
        }
      }
      
      // Destroy sicuro con true per rimuovere anche le texture
      this.app.destroy(true, { children: true, texture: true, baseTexture: true });
      console.log('App PIXI principale distrutta con successo.');
    } catch (err) {
      console.error('Errore durante distruzione dell\'app PIXI principale:', err);
    } finally {
      this.app = null;
      this.isInitialized = false;
    }
  }
} 