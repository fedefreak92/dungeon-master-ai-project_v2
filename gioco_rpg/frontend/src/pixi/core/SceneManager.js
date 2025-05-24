/**
 * SceneManager.js
 * Gestisce la creazione, la configurazione e la pulizia delle scene PIXI
 */
import * as PIXI from 'pixi.js';

export default class SceneManager {
  constructor() {
    this.activeScenes = new Map();
  }
  
  /**
   * Crea una nuova scena PIXI specifica per un componente React, gestendo la sua istanza
   * @param {HTMLElement} container - L'elemento DOM container
   * @param {Object} options - Opzioni di configurazione (sceneId, width, height, backgroundColor)
   * @returns {PIXI.Application|null} - L'istanza dell'applicazione o null in caso di errore
   */
  createScene(container, options = {}) {
    const { sceneId, width, height, backgroundColor } = options;

    if (!container) {
      console.error(`[SceneManager] createScene(${sceneId}): Container non fornito.`);
      return null;
    }

    if (!sceneId) {
      console.error('[SceneManager] createScene: sceneId è obbligatorio nelle opzioni.');
      return null;
    }

    // Controlla se esiste già una scena attiva con lo stesso ID
    if (this.activeScenes.has(sceneId)) {
      console.warn(`[SceneManager] createScene(${sceneId}): Esiste già una scena attiva con questo ID. Pulizia precedente...`);
      this.cleanupScene(sceneId); // Pulisce la vecchia scena prima di crearne una nuova
    }

    try {
      console.log(`[SceneManager] createScene(${sceneId}): Creazione nuova istanza PIXI.Application`);
      console.log(`[SceneManager] createScene(${sceneId}): Dimensioni richieste: ${width}x${height}`);

      // Verifica se le dimensioni sono valide
      if (!width || width <= 0 || !height || height <= 0) {
        console.error(`[SceneManager] createScene(${sceneId}): Dimensioni non valide fornite (width: ${width}, height: ${height}). Impossibile creare la scena.`);
        // Potremmo provare a prendere le dimensioni dal container, ma è rischioso se non sono ancora definite
        const cWidth = container.clientWidth;
        const cHeight = container.clientHeight;
        if (!cWidth || cWidth <= 0 || !cHeight || cHeight <= 0) {
           console.error(`[SceneManager] createScene(${sceneId}): Anche le dimensioni del container (${cWidth}x${cHeight}) non sono valide. Fallimento.`);
           return null;
        }
         console.warn(`[SceneManager] createScene(${sceneId}): Utilizzo dimensioni del container (${cWidth}x${cHeight}) come fallback.`);
         options.width = cWidth;
         options.height = cHeight;
      }

      // Determina il renderer preferito
      const preferredRenderer = 'auto' === 'auto'
        ? (PIXI.utils.isWebGLSupported() ? PIXI.RENDERER_TYPE.WEBGL : PIXI.RENDERER_TYPE.CANVAS)
        : ('auto' === 'webgl' ? PIXI.RENDERER_TYPE.WEBGL : PIXI.RENDERER_TYPE.CANVAS);

      const app = new PIXI.Application({
        width: options.width, 
        height: options.height,
        backgroundColor: backgroundColor || 0x1a1a1a,
        resolution: window.devicePixelRatio || 1,
        autoDensity: true,
        antialias: true,
        forceCanvas: preferredRenderer === PIXI.RENDERER_TYPE.CANVAS,
        failIfMajorPerformanceCaveat: false, 
        powerPreference: 'high-performance',
      });

      console.log(`[SceneManager] createScene(${sceneId}): Istanza PIXI.Application creata con renderer: ${app.renderer.type === PIXI.RENDERER_TYPE.WEBGL ? 'WebGL' : 'Canvas'}`);

      // Più sicuro - Verifichiamo se il canvas è già nel container
      // Se il canvas è già presente nel container, lo rimuoverà solo se è un vecchio canvas Pixi
      const existingCanvas = container.querySelector('canvas');
      if (existingCanvas && existingCanvas !== app.view) {
        console.log(`[SceneManager] createScene(${sceneId}): Trovato canvas esistente nel container.`);
        try {
          container.removeChild(existingCanvas);
          console.log(`[SceneManager] createScene(${sceneId}): Canvas precedente rimosso con successo.`);
        } catch (err) {
          console.warn(`[SceneManager] createScene(${sceneId}): Errore durante rimozione canvas precedente:`, err);
          // Continuare con la creazione della scena comunque
        }
      }

      // Aggiungi il canvas al container SOLO se non è già presente
      if (!container.contains(app.view)) {
        container.appendChild(app.view);
        console.log(`[SceneManager] createScene(${sceneId}): Canvas PIXI aggiunto al container.`);
      } else {
        console.log(`[SceneManager] createScene(${sceneId}): Canvas PIXI già presente nel container.`);
      }

      // Aggiungi listener per perdita contesto (opzionale ma utile)
      app.renderer.view.addEventListener('webglcontextlost', (event) => {
        event.preventDefault(); // Importante per consentire il ripristino
        console.warn(`[SceneManager] createScene(${sceneId}): Contesto WebGL perso!`, event);
      }, false);

      app.renderer.view.addEventListener('webglcontextrestored', () => {
        console.log(`[SceneManager] createScene(${sceneId}): Contesto WebGL ripristinato.`);
        // Potremmo ricaricare texture e rigenerare la scena qui
      }, false);

      // Memorizza l'istanza dell'app nella mappa delle scene attive
      this.activeScenes.set(sceneId, app);
      
      // Imposta l'ID sull'istanza dell'app per riferimento futuro
      app.id = sceneId;
      // Potremmo anche impostare il nome se preferito, ma l'ID è più univoco
      // app.name = sceneId; 

      // Crea container principali per la scena
      this._setupSceneContainers(app);
      
      console.log(`[SceneManager] createScene(${sceneId}): Scena creata e registrata con successo.`);

      return app; // Restituisce l'istanza PIXI.Application creata

    } catch (err) {
      console.error(`[SceneManager] createScene(${sceneId}): Errore GRAVE durante creazione scena Pixi.js:`, err);
      // Assicurati che non rimanga una scena parziale registrata
      if (this.activeScenes.has(sceneId)) {
         const partialApp = this.activeScenes.get(sceneId);
         try {
           partialApp.destroy(true, {children: true, texture: true, baseTexture: true });
         } catch (destroyErr) {
           console.error(`[SceneManager] createScene(${sceneId}): Errore durante destroy dopo fallimento creazione:`, destroyErr);
         }
         this.activeScenes.delete(sceneId);
      }
      return null; // Restituisce null in caso di qualsiasi errore
    }
  }
  
  /**
   * Configura i container principali per una scena
   * @param {PIXI.Application} app - L'app PIXI della scena
   * @private
   */
  _setupSceneContainers(app) {
    if (!app || !app.stage) return;
    
    // Crea container per la mappa
    app.mapContainer = new PIXI.Container();
    app.stage.addChild(app.mapContainer);
    
    // Crea contenitori dedicati per ogni tipo di elemento della mappa
    app.tileContainer = new PIXI.Container();
    app.objectsContainer = new PIXI.Container();
    app.npcsContainer = new PIXI.Container();
    app.entitiesContainer = new PIXI.Container();
    
    // Aggiungi i container al container principale della mappa
    app.mapContainer.addChild(app.tileContainer);
    app.mapContainer.addChild(app.objectsContainer);
    app.mapContainer.addChild(app.npcsContainer);
    app.mapContainer.addChild(app.entitiesContainer);
  }
  
  /**
   * Pulisce una specifica scena PIXI rimuovendo l'app e le sue risorse
   * @param {string} id - L'ID della scena da pulire (es. 'map_scene_taverna')
   */
  cleanupScene(id) {
    console.log(`[SceneManager] cleanupScene: Inizio pulizia per sceneId: ${id}`);
    if (this.activeScenes.has(id)) {
      const app = this.activeScenes.get(id);
      console.log(`[SceneManager] cleanupScene(${id}): Trovata app PIXI attiva.`);
      
      try {
        this._destroyPixiApp(app, id);
      } catch (error) {
        console.error(`[SceneManager] cleanupScene(${id}): Errore durante la pulizia:`, error);
      }
    } else {
      console.warn(`[SceneManager] cleanupScene(${id}): Nessuna scena attiva trovata con questo ID. Pulizia saltata.`);
    }
  }
  
  /**
   * Metodo helper per distruggere un'app Pixi
   * @param {PIXI.Application} app - L'app Pixi da distruggere
   * @param {string} id - L'ID della scena per i messaggi di log
   * @private
   */
  _destroyPixiApp(app, id) {
    try {
      // Verificare che l'app esista ancora
      if (!app) {
        console.warn(`[SceneManager] _destroyPixiApp(${id}): App non trovata.`);
        this.activeScenes.delete(id);
        return;
      }
      
      // Verifica e svuota esplicitamente stage e renderer prima della distruzione
      if (app.stage) {
        console.log(`[SceneManager] _destroyPixiApp(${id}): Rimozione dei figli dallo stage...`);
        
        // Rimuovi i figli dal basso verso l'alto per evitare problemi con l'indice
        while (app.stage.children.length > 0) {
          const child = app.stage.children[0];
          app.stage.removeChild(child);
          
          // Distruggi il figlio se ha un metodo destroy
          if (child && typeof child.destroy === 'function') {
            try {
              child.destroy({ children: true, texture: false, baseTexture: false });
            } catch (childError) {
              console.warn(`[SceneManager] _destroyPixiApp(${id}): Errore durante distruzione figlio:`, childError);
            }
          }
        }
      }
      
      // Assicurati che il renderer sia rilasciato correttamente
      if (app.renderer) {
        try {
          // Disconnetti tutti i textures dal renderer
          if (app.renderer.textureGC) {
            app.renderer.textureGC.unload(app.stage);
          }
          
          // Esegui un flush se è disponibile il contesto WebGL
          if (app.renderer.gl && typeof app.renderer.gl.flush === 'function') {
            app.renderer.gl.flush();
          }
          
          // Fai un reset del renderer se possibile
          if (typeof app.renderer.reset === 'function') {
            app.renderer.reset();
          }
        } catch (rendererError) {
          console.warn(`[SceneManager] _destroyPixiApp(${id}): Errore durante cleanup renderer:`, rendererError);
        }
      }
      
      // Distruggi l'applicazione PIXI con un approccio sicuro
      console.log(`[SceneManager] _destroyPixiApp(${id}): Tentativo di distruzione dell'app...`);
      try {
        // Cattura eventuali errori durante la distruzione
        const destroyOptions = { 
          children: true, 
          texture: true, 
          baseTexture: true 
        };
        
        app.destroy(true, destroyOptions);
        console.log(`[SceneManager] _destroyPixiApp(${id}): App PIXI distrutta con successo.`);
      } catch (destroyError) {
        console.error(`[SceneManager] _destroyPixiApp(${id}): Errore durante la distruzione dell'app PIXI:`, destroyError);
      }
    } catch (error) {
      console.error(`[SceneManager] _destroyPixiApp(${id}): Errore critico:`, error);
    } finally {
      // Rimuovi SEMPRE la scena dalla mappa delle scene attive
      this.activeScenes.delete(id);
      console.log(`[SceneManager] _destroyPixiApp(${id}): Scena rimossa dalla mappa activeScenes.`);
    }
  }
  
  /**
   * Ottiene una scena attiva
   * @param {string} sceneId - ID della scena
   * @returns {PIXI.Application|null} - L'app della scena o null se non trovata
   */
  getScene(sceneId) {
    return this.activeScenes.get(sceneId) || null;
  }
  
  /**
   * Pulisce tutte le scene attive
   */
  cleanupAllScenes() {
    const sceneIds = Array.from(this.activeScenes.keys());
    console.log(`[SceneManager] cleanupAllScenes: Pulizia di ${sceneIds.length} scene attive...`);
    
    // Pulizia di tutte le scene una per una
    for (const id of sceneIds) {
      try {
        this.cleanupScene(id);
      } catch (err) {
        console.error(`[SceneManager] cleanupAllScenes: Errore durante pulizia della scena ${id}:`, err);
      }
    }
    
    // Svuota la mappa dopo la pulizia delle scene
    this.activeScenes.clear();
  }
} 