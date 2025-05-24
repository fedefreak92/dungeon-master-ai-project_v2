/**
 * FilterManager.js
 * Gestore sicuro per applicare filtri Pixi.js con gestione appropriata degli errori
 * e verifica del contesto WebGL
 */
import * as PIXI from 'pixi.js';

export default class FilterManager {
  /**
   * Verifica se WebGL è disponibile e utilizzabile
   * @param {PIXI.Application} app - Istanza dell'applicazione Pixi.js
   * @returns {boolean} true se WebGL è disponibile e funzionante
   */
  static isWebGLAvailable(app) {
    if (!app || !app.renderer) return false;
    
    // Verifica se il renderer è di tipo WebGL
    return app.renderer.type === PIXI.RENDERER_TYPE.WEBGL;
  }
  
  /**
   * Verifica se il contesto WebGL è valido
   * @param {PIXI.Application} app - Istanza dell'applicazione Pixi.js
   * @returns {boolean} true se il contesto WebGL è valido
   */
  static isWebGLContextValid(app) {
    try {
      if (!this.isWebGLAvailable(app)) return false;
      
      // Verifica se il contesto esiste e non è perso
      const gl = app.renderer.gl;
      return gl && gl.getError() === gl.NO_ERROR;
    } catch (error) {
      console.error("Errore nella verifica del contesto WebGL:", error);
      return false;
    }
  }
  
  /**
   * Applica in modo sicuro un filtro Pixi a un oggetto DisplayObject
   * @param {PIXI.DisplayObject} target - Oggetto a cui applicare il filtro
   * @param {PIXI.Filter|PIXI.Filter[]} filter - Filtro o array di filtri da applicare
   * @param {PIXI.Application} app - Istanza dell'applicazione Pixi.js
   * @returns {boolean} true se il filtro è stato applicato con successo
   */
  static applyFilter(target, filter, app) {
    if (!target) {
      console.error("Target non valido per l'applicazione del filtro");
      return false;
    }
    
    // Verifica se WebGL è disponibile
    if (!this.isWebGLAvailable(app)) {
      console.warn("WebGL non disponibile, utilizzo fallback senza filtri");
      return false;
    }
    
    // Verifica se il contesto WebGL è valido
    if (!this.isWebGLContextValid(app)) {
      console.warn("Contesto WebGL non valido, filtro non applicato");
      return false;
    }
    
    try {
      // Applica il filtro
      target.filters = Array.isArray(filter) ? filter : [filter];
      return true;
    } catch (error) {
      console.error("Errore nell'applicazione del filtro:", error);
      
      // Rimuovi tutti i filtri in caso di errore
      target.filters = null;
      return false;
    }
  }
  
  /**
   * Crea un filtro GlowFilter in modo sicuro
   * @param {number} distance - Distanza dell'effetto glow
   * @param {number} outerStrength - Forza dell'effetto esterno
   * @param {number} innerStrength - Forza dell'effetto interno
   * @param {number} color - Colore dell'effetto glow
   * @param {number} quality - Qualità dell'effetto
   * @param {PIXI.Application} app - Istanza dell'applicazione Pixi.js
   * @returns {PIXI.Filter|null} Il filtro se creato con successo, null altrimenti
   */
  static createGlowFilter(distance, outerStrength, innerStrength, color, quality, app) {
    // Verifica se WebGL è disponibile
    if (!this.isWebGLAvailable(app)) {
      console.warn("WebGL non disponibile, impossibile creare GlowFilter");
      return null;
    }
    
    try {
      // Importazione dinamica del filtro solo se WebGL è disponibile
      // Questa riga presuppone che @pixi/filter-glow sia installato
      const GlowFilter = PIXI.filters?.GlowFilter || PIXI.filters?.OutlineFilter;
      
      if (!GlowFilter) {
        console.warn("GlowFilter non disponibile nella versione corrente di Pixi.js");
        return null;
      }
      
      // Crea il filtro
      return new GlowFilter(distance, outerStrength, innerStrength, color, quality);
    } catch (error) {
      console.error("Errore nella creazione del GlowFilter:", error);
      return null;
    }
  }
  
  /**
   * Configura i listener per gestire la perdita e il ripristino del contesto WebGL
   * @param {PIXI.Application} app - Istanza dell'applicazione Pixi.js
   * @param {Function} onContextLost - Callback da eseguire quando il contesto è perso
   * @param {Function} onContextRestored - Callback da eseguire quando il contesto è ripristinato
   */
  static setupContextListeners(app, onContextLost, onContextRestored) {
    if (!app || !app.renderer || !app.renderer.view) {
      console.error("Applicazione Pixi.js non valida");
      return;
    }
    
    const canvas = app.renderer.view;
    
    // Rimuovi eventuali listener precedenti
    canvas.removeEventListener('webglcontextlost', this._handleContextLost);
    canvas.removeEventListener('webglcontextrestored', this._handleContextRestored);
    
    // Funzione di gestione della perdita del contesto
    this._handleContextLost = (event) => {
      event.preventDefault(); // Impedisce il comportamento predefinito
      console.warn("Contesto WebGL perso");
      
      // Esegui il callback personalizzato
      if (typeof onContextLost === 'function') {
        onContextLost(event);
      }
      
      // Rimuovi tutti i filtri attivi nell'applicazione
      this._removeAllFilters(app.stage);
    };
    
    // Funzione di gestione del ripristino del contesto
    this._handleContextRestored = (event) => {
      console.log("Contesto WebGL ripristinato");
      
      // Esegui il callback personalizzato
      if (typeof onContextRestored === 'function') {
        onContextRestored(event);
      }
    };
    
    // Aggiungi i listener
    canvas.addEventListener('webglcontextlost', this._handleContextLost);
    canvas.addEventListener('webglcontextrestored', this._handleContextRestored);
  }
  
  /**
   * Rimuove tutti i filtri da un container e dai suoi figli ricorsivamente
   * @param {PIXI.Container} container - Container da cui rimuovere i filtri
   * @private
   */
  static _removeAllFilters(container) {
    if (!container) return;
    
    try {
      // Rimuovi i filtri dal container stesso
      if (container.filters) {
        // Prima disattiva i filtri impostando l'array vuoto
        container.filters = [];
        // Poi imposta a null per rimuovere completamente il riferimento
        container.filters = null;
      }
      
      // Rimuovi ricorsivamente i filtri da tutti i figli
      if (container.children && container.children.length > 0) {
        // Itera dall'ultimo al primo per evitare problemi se i figli vengono rimossi
        for (let i = container.children.length - 1; i >= 0; i--) {
          if (i < container.children.length) { // Verifica aggiuntiva per sicurezza
            const child = container.children[i];
            if (child) {
              this._removeAllFilters(child);
            }
          }
        }
      }
    } catch (error) {
      console.warn("Errore nella rimozione dei filtri:", error);
    }
  }
  
  /**
   * Metodo pubblico per rimuovere in modo sicuro tutti i filtri da un'app o container
   * Utile da chiamare prima di distruggere l'app PIXI per prevenire memory leak
   * @param {PIXI.Application|PIXI.Container} target - App PIXI o container da cui rimuovere i filtri
   * @returns {boolean} true se l'operazione è riuscita
   */
  static removeAllFilters(target) {
    try {
      if (!target) {
        console.warn("Target non valido per removeAllFilters");
        return false;
      }
      
      // Se target è un'app PIXI, utilizza il suo stage
      const container = target.stage || target;
      
      if (!container) {
        console.warn("Container non valido per removeAllFilters");
        return false;
      }
      
      // Rimuovi tutti i filtri in modo ricorsivo
      this._removeAllFilters(container);
      
      return true;
    } catch (error) {
      console.error("Errore critico in removeAllFilters:", error);
      return false;
    }
  }
  
  /**
   * Prepara un'app PIXI o un container per la distruzione, rimuovendo tutti i filtri
   * e liberando le risorse WebGL associate
   * @param {PIXI.Application|PIXI.Container} target - App PIXI o container da preparare
   * @returns {boolean} true se l'operazione è riuscita
   */
  static prepareForDestruction(target) {
    try {
      if (!target) {
        console.warn("Target non valido per prepareForDestruction");
        return false;
      }
      
      // Rimuovi tutti i filtri
      const filtersRemoved = this.removeAllFilters(target);
      
      // Se target è un'app PIXI, pulisci anche il renderer
      if (target.renderer && target.renderer.gl) {
        try {
          // Esegui un flush per completare tutte le operazioni WebGL pendenti
          target.renderer.gl.flush();
          
          // Se l'app ha un texture garbage collector, forza una pulizia
          if (target.renderer.textureGC) {
            target.renderer.textureGC.run();
          }
        } catch (rendererError) {
          console.warn("Errore durante la pulizia del renderer:", rendererError);
        }
      }
      
      return filtersRemoved;
    } catch (error) {
      console.error("Errore critico in prepareForDestruction:", error);
      return false;
    }
  }
} 