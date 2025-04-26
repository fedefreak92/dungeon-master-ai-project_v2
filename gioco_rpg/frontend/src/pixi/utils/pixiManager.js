import * as PIXI from 'pixi.js';
import { GlowFilter } from 'pixi-filters';
import MapRendererFactory from './MapRendererFactory';

/**
 * Singleton che gestisce tutte le risorse PIXI.js per l'intera applicazione
 * Risolve i problemi di ciclo di vita tra React e PIXI.js
 */
class PixiManager {
  constructor() {
    this.app = null;
    this.viewports = {};
    this.resources = {};
    this.renderers = {};
    this.textures = {};
    this.isInitialized = false;
    this.activeScenes = new Map();
    this.renderMode = 'auto'; // 'auto', 'webgl', o 'canvas'
    this.playerSprites = new Map(); // Memorizza gli sprite dei giocatori per ogni scena
    this.entitySprites = new Map(); // Memorizza gli sprite delle entità per ogni scena
  }
  
  /**
   * Inizializza il manager PIXI, chiamare una sola volta all'avvio dell'app
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
      
      // Precarica le texture comuni
      this.preloadCommonTextures();
      
      // Registra il gestore di errori globale
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
   * Precarica le texture comuni usate in tutto il gioco
   */
  preloadCommonTextures() {
    // Implementazione texture di base per test
    console.log("PreloadCommonTextures: Inizio creazione texture.");
    if (!this.app || !this.app.renderer) {
      console.error("PreloadCommonTextures: Errore - App PIXI o renderer non inizializzati!");
      return;
    }
    if (typeof this.app.renderer.generateTexture !== 'function') {
      console.error("PreloadCommonTextures: Errore - generateTexture non è una funzione sul renderer!");
      return;
    }
    console.log("PreloadCommonTextures: Renderer App valido.");

    const createColoredTexture = (color, name) => {
      try {
        const graphics = new PIXI.Graphics();
        graphics.beginFill(color);
        graphics.drawRect(0, 0, 64, 64);
        graphics.endFill();
        
        // Assicurati che generateTexture esista e sia una funzione
        if (this.app.renderer.generateTexture) {
          const texture = this.app.renderer.generateTexture(graphics);
          this.textures[name] = texture;
          console.log(`PreloadCommonTextures: Texture '${name}' creata.`);
          return texture;
        } else {
          console.error(`PreloadCommonTextures: generateTexture non trovato per ${name}`);
          return null;
        }
      } catch (error) {
        console.error(`PreloadCommonTextures: Errore durante creazione texture '${name}':`, error);
        return null;
      }
    };
    
    // Crea texture base per i tipi di tile principali
    createColoredTexture(0x333333, 'wall');    // muri - grigio scuro
    createColoredTexture(0x8B4513, 'door');    // porte - marrone
    createColoredTexture(0x00FF00, 'grass');   // erba - verde
    createColoredTexture(0x0000FF, 'water');   // acqua - blu
    createColoredTexture(0xFFD700, 'item');    // oggetti - oro
    createColoredTexture(0x555555, 'floor');   // pavimento - grigio
    
    // Crea texture per il giocatore
    const playerGraphics = new PIXI.Graphics();
    playerGraphics.beginFill(0x00FF00);
    playerGraphics.lineStyle(2, 0xFFFFFF);
    playerGraphics.drawCircle(32, 32, 16);
    playerGraphics.endFill();
    this.textures.player = this.app.renderer.generateTexture(playerGraphics);
    
    // Crea texture per gli NPC
    const npcGraphics = new PIXI.Graphics();
    npcGraphics.beginFill(0x0000FF);
    npcGraphics.lineStyle(2, 0xFFFFFF);
    npcGraphics.drawCircle(32, 32, 16);
    npcGraphics.endFill();
    this.textures.npc = this.app.renderer.generateTexture(npcGraphics);
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
      console.error(`[PixiManager] createScene(${sceneId}): Container non fornito.`);
      return null;
    }

    if (!sceneId) {
      console.error('[PixiManager] createScene: sceneId è obbligatorio nelle opzioni.');
      return null;
    }

    // Controlla se esiste già una scena attiva con lo stesso ID
    if (this.activeScenes.has(sceneId)) {
      console.warn(`[PixiManager] createScene(${sceneId}): Esiste già una scena attiva con questo ID. Pulizia precedente...`);
      this.cleanupScene(sceneId); // Pulisce la vecchia scena prima di crearne una nuova
    }

    try {
      console.log(`[PixiManager] createScene(${sceneId}): Creazione nuova istanza PIXI.Application in container:`, container);
      console.log(`[PixiManager] createScene(${sceneId}): Dimensioni richieste: ${width}x${height}`);

      // Verifica se le dimensioni sono valide
      if (!width || width <= 0 || !height || height <= 0) {
        console.error(`[PixiManager] createScene(${sceneId}): Dimensioni non valide fornite (width: ${width}, height: ${height}). Impossibile creare la scena.`);
        // Potremmo provare a prendere le dimensioni dal container, ma è rischioso se non sono ancora definite
        const cWidth = container.clientWidth;
        const cHeight = container.clientHeight;
        if (!cWidth || cWidth <= 0 || !cHeight || cHeight <= 0) {
           console.error(`[PixiManager] createScene(${sceneId}): Anche le dimensioni del container (${cWidth}x${cHeight}) non sono valide. Fallimento.`);
           return null;
        }
         console.warn(`[PixiManager] createScene(${sceneId}): Utilizzo dimensioni del container (${cWidth}x${cHeight}) come fallback.`);
         options.width = cWidth;
         options.height = cHeight;
        // Riassegna width e height locali per l'istanza
        // width = cWidth; // Non necessario se usiamo options.width sotto
        // height = cHeight;
      }


      // Determina il renderer preferito
      const preferredRenderer = this.renderMode === 'auto'
        ? (PIXI.utils.isWebGLSupported() ? PIXI.RENDERER_TYPE.WEBGL : PIXI.RENDERER_TYPE.CANVAS)
        : (this.renderMode === 'webgl' ? PIXI.RENDERER_TYPE.WEBGL : PIXI.RENDERER_TYPE.CANVAS);

      const app = new PIXI.Application({
        width: options.width, // Usa le dimensioni dalle opzioni (potenzialmente corrette sopra)
        height: options.height,
        backgroundColor: backgroundColor || 0x1a1a1a,
        resolution: window.devicePixelRatio || 1,
        autoDensity: true,
        antialias: true,
        forceCanvas: preferredRenderer === PIXI.RENDERER_TYPE.CANVAS,
        // Gestione perdita contesto WebGL
        failIfMajorPerformanceCaveat: false, // Tenta di usare WebGL anche se non ottimale
         powerPreference: 'high-performance',
      });

      console.log(`[PixiManager] createScene(${sceneId}): Istanza PIXI.Application creata con renderer: ${app.renderer.type === PIXI.RENDERER_TYPE.WEBGL ? 'WebGL' : 'Canvas'}`);

      // Aggiungi il canvas al container
      // Pulisci prima il container da eventuali canvas precedenti o overlay
      while (container.firstChild) {
          container.removeChild(container.firstChild);
      }
      container.appendChild(app.view); // app.view è il canvas
      console.log(`[PixiManager] createScene(${sceneId}): Canvas PIXI aggiunto al container.`);

      // Aggiungi listener per perdita contesto (opzionale ma utile)
      app.renderer.view.addEventListener('webglcontextlost', (event) => {
        console.warn(`[PixiManager] createScene(${sceneId}): Contesto WebGL perso!`, event);
        // Qui potresti provare a gestire il ripristino
      }, false);

      app.renderer.view.addEventListener('webglcontextrestored', () => {
        console.log(`[PixiManager] createScene(${sceneId}): Contesto WebGL ripristinato.`);
        // Qui potresti dover ricaricare le texture o ri-renderizzare
      }, false);


      // Memorizza l'istanza dell'app nella mappa delle scene attive
      this.activeScenes.set(sceneId, app);
      console.log(`[PixiManager] createScene(${sceneId}): Scena creata e registrata con successo.`);

      return app; // Restituisce l'istanza PIXI.Application creata

    } catch (err) {
      console.error(`[PixiManager] createScene(${sceneId}): Errore GRAVE durante creazione scena Pixi.js:`, err);
      // Assicurati che non rimanga una scena parziale registrata
      if (this.activeScenes.has(sceneId)) {
         const partialApp = this.activeScenes.get(sceneId);
         try {
           partialApp.destroy(true, {children: true, texture: true, baseTexture: true });
         } catch (destroyErr) {
           console.error(`[PixiManager] createScene(${sceneId}): Errore durante destroy dopo fallimento creazione:`, destroyErr);
         }
         this.activeScenes.delete(sceneId);
      }
      return null; // Restituisce null in caso di qualsiasi errore
    }
  }
  
  /**
   * Renderizza una mappa in una scena specifica utilizzando il renderer ottimale
   * @param {Object} scene - Oggetto scena creato con createScene
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
      // Usa il factory per creare il renderer ottimale
      const renderer = await MapRendererFactory.createRenderer(
        this.app, 
        scene.mapContainer, 
        mapData, 
        {
          textures: this.textures,
          ...options
        }
      );
      
      // Memorizza il renderer nella scena per riferimenti futuri
      scene.mapRenderer = renderer;
      
      return true;
    } catch (error) {
      console.error("Errore nel rendering ottimizzato della mappa:", error);
      
      // Fallback al metodo di rendering standard in caso di errore
      console.log("Fallback al renderer standard");
      return this.renderMap(scene, mapData);
    }
  }
  
  /**
   * Renderizza una mappa in una scena specifica
   * @param {Object} scene - Oggetto scena creato con createScene
   * @param {Object} mapData - Dati della mappa da renderizzare
   * @returns {boolean} - true se il rendering è riuscito
   */
  renderMap(scene, mapData) {
    if (!scene || !mapData) {
      console.error("Scene o mapData non validi");
      return false;
    }
    
    try {
      console.log("Inizio rendering mappa con dimensioni:", {
        larghezza: mapData.larghezza,
        altezza: mapData.altezza
      });
      
      // Validazione di sicurezza dei dati della mappa
      if (!this.validateMapData(mapData)) {
        throw new Error("Dati mappa non validi o incompleti");
      }
      
      // Crea un container per la mappa
      if (!scene.mapContainer) {
        scene.mapContainer = new PIXI.Container();
        scene.stage.addChild(scene.mapContainer);
      }
      
      // Pulisci il container per evitare rendering duplicati
      scene.mapContainer.removeChildren();
      
      // Memorizza i dati della mappa per riferimento futuro
      scene.mapData = mapData;
      
      // Crea contenitori dedicati per ogni tipo di elemento della mappa
      const tileContainer = new PIXI.Container();
      const objectsContainer = new PIXI.Container();
      const npcsContainer = new PIXI.Container();
      const entitiesContainer = new PIXI.Container();
      
      // Aggiungi i container al container principale della mappa
      scene.mapContainer.addChild(tileContainer);
      scene.mapContainer.addChild(objectsContainer);
      scene.mapContainer.addChild(npcsContainer);
      scene.mapContainer.addChild(entitiesContainer);
      
      // Memorizza i riferimenti ai container per utilizzo futuro
      scene.tileContainer = tileContainer;
      scene.objectsContainer = objectsContainer;
      scene.npcsContainer = npcsContainer;
      scene.entitiesContainer = entitiesContainer;
      
      // Disegna la griglia di base della mappa
      this.renderMapGrid(scene, mapData);
      
      // Disegna gli oggetti presenti sulla mappa
      this.renderMapObjects(scene, mapData);
      
      // Disegna gli NPC presenti sulla mappa
      this.renderMapNPCs(scene, mapData);
      
      // Imposta la scala e la posizione iniziale
      scene.mapContainer.scale.set(1);
      scene.mapContainer.position.set(0, 0);
      
      console.log("Rendering mappa completato con successo");
      return true;
    } catch (error) {
      console.error("Errore nel rendering della mappa:", error);
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
   * Disegna la griglia di base della mappa
   * @param {Object} scene - La scena in cui disegnare
   * @param {Object} mapData - I dati della mappa
   */
  renderMapGrid(scene, mapData) {
    try {
      const { tileContainer } = scene;
      const { larghezza, altezza, griglia } = mapData;
      
      console.log(`Rendering griglia: ${larghezza}x${altezza}`);
      
      // Usa la dimensione dei tile costante
      const TILE_SIZE = 64;
      
      // Crea un Graphics per disegnare la griglia di riferimento
      const gridGraphics = new PIXI.Graphics();
      gridGraphics.lineStyle(1, 0x444444, 0.3);
      
      // Disegna le linee orizzontali
      for (let y = 0; y <= altezza; y++) {
        gridGraphics.moveTo(0, y * TILE_SIZE);
        gridGraphics.lineTo(larghezza * TILE_SIZE, y * TILE_SIZE);
      }
      
      // Disegna le linee verticali
      for (let x = 0; x <= larghezza; x++) {
        gridGraphics.moveTo(x * TILE_SIZE, 0);
        gridGraphics.lineTo(x * TILE_SIZE, altezza * TILE_SIZE);
      }
      
      tileContainer.addChild(gridGraphics);
      
      // Disegna i tile della mappa
      for (let y = 0; y < altezza; y++) {
        for (let x = 0; x < larghezza; x++) {
          // Verifica che esistano dati per questa posizione
          if (!griglia[y] || typeof griglia[y][x] === 'undefined') {
            console.warn(`Cella mancante nella griglia a [${x},${y}]`);
            continue;
          }
          
          const tileType = griglia[y][x];
          
          // Salta le celle vuote (0)
          if (tileType === 0) continue;
          
          // Ottieni la texture per questo tipo di tile
          const texture = this.getTileTexture(tileType);
          
          if (texture) {
            // Crea e posiziona lo sprite
            const tileSprite = new PIXI.Sprite(texture);
            tileSprite.x = x * TILE_SIZE;
            tileSprite.y = y * TILE_SIZE;
            tileSprite.width = TILE_SIZE;
            tileSprite.height = TILE_SIZE;
            
            // Aggiungi lo sprite al container
            tileContainer.addChild(tileSprite);
          } else {
            console.warn(`Texture mancante per il tipo di tile ${tileType} a [${x},${y}]`);
            
            // Crea un placeholder grafico
            const placeholderGraphics = new PIXI.Graphics();
            placeholderGraphics.beginFill(this.getColorForTileType(tileType));
            placeholderGraphics.drawRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
            placeholderGraphics.endFill();
            
            // Aggiunge un testo per identificare il tipo
            const text = new PIXI.Text(`${tileType}`, { 
              fontSize: 10, 
              fill: 0xffffff,
              align: 'center'
            });
            text.x = x * TILE_SIZE + TILE_SIZE / 2 - text.width / 2;
            text.y = y * TILE_SIZE + TILE_SIZE / 2 - text.height / 2;
            
            // Aggiungi gli elementi al container
            tileContainer.addChild(placeholderGraphics);
            tileContainer.addChild(text);
          }
        }
      }
      
      console.log("Rendering griglia completato");
    } catch (error) {
      console.error("Errore nel rendering della griglia:", error);
    }
  }
  
  /**
   * Ottiene una texture per un tipo di tile specifico
   * @param {number} tileType - Il tipo di tile
   * @returns {PIXI.Texture|null} - La texture o null se non trovata
   */
  getTileTexture(tileType) {
    // Mappatura dei tipi di tile alle texture
    const tileTextureMap = {
      1: this.textures.wall,    // Muro
      2: this.textures.door,    // Porta
      3: this.textures.grass,   // Erba
      4: this.textures.water,   // Acqua
      5: this.textures.floor    // Pavimento
    };
    
    // Restituisci la texture corrispondente o null
    const texture = tileTextureMap[tileType];
    if (!texture) {
      // Logga solo se il tipo non è 0 (che ignoriamo comunque)
      if (tileType !== 0) { 
          console.warn(`getTileTexture: Texture non trovata per tipo ${tileType}, usando fallback.`);
      }
      return this.textures.floor || null; // Fallback a pavimento se esiste
    }
    return texture;
  }
  
  /**
   * Ottiene un colore per un tipo di tile (usato per i placeholder)
   * @param {number} tileType - Il tipo di tile
   * @returns {number} - Il colore in formato esadecimale
   */
  getColorForTileType(tileType) {
    // Mappatura dei tipi di tile ai colori
    const tileColorMap = {
      1: 0x333333,    // Muro - grigio scuro
      2: 0x8B4513,    // Porta - marrone
      3: 0x00AA00,    // Erba - verde
      4: 0x0000AA,    // Acqua - blu
      5: 0x555555     // Pavimento - grigio
    };
    
    // Restituisci il colore corrispondente o un colore di fallback
    return tileColorMap[tileType] || 0xFF00FF; // Magenta per tipi sconosciuti
  }
  
  /**
   * Disegna gli oggetti presenti sulla mappa
   * @param {Object} scene - La scena in cui disegnare
   * @param {Object} mapData - I dati della mappa
   */
  renderMapObjects(scene, mapData) {
    try {
      const { objectsContainer } = scene;
      const TILE_SIZE = 64;
      
      // Verifica che esistano oggetti da renderizzare
      if (!mapData.oggetti) {
        console.log("Nessun oggetto da renderizzare");
        return;
      }
      
      console.log(`Rendering oggetti: ${Object.keys(mapData.oggetti).length}`);
      
      // Itera su tutti gli oggetti
      for (const objectId in mapData.oggetti) {
        const object = mapData.oggetti[objectId];
        let x, y;

        // --- Gestione Coordinate Oggetti --- 
        if (typeof object.x === 'number' && typeof object.y === 'number') {
            x = object.x;
            y = object.y;
        } else if (typeof object.posizione === 'string') { 
            // Prova a parsare da stringa "(x, y)"
            const match = object.posizione.match(/\((\d+),\s*(\d+)\)/);
            if (match) {
                x = parseInt(match[1], 10);
                y = parseInt(match[2], 10);
            } else {
                console.warn(`Oggetto ${objectId} con stringa posizione non valida: ${object.posizione}`, object);
                continue;
            }
        } else {
             console.warn(`Oggetto ${objectId} con coordinate non valide o mancanti:`, object);
             continue;
        }
        // -----------------------------------

        // Verifica che l'oggetto abbia le coordinate necessarie (dopo parsing)
        // if (typeof object.x !== 'number' || typeof object.y !== 'number') { // Rimosso controllo ridondante
        //   console.warn(`Oggetto ${objectId} con coordinate non valide:`, object);
        //   continue;
        // }
        
        // Ottieni la texture per questo tipo di oggetto
        let objectSprite;
        const objectTexture = this.getObjectTexture(object.tipo || 'default');
        
        if (objectTexture) {
          // Crea lo sprite dell'oggetto
          objectSprite = new PIXI.Sprite(objectTexture);
        } else {
          // Crea un placeholder grafico per l'oggetto
          objectSprite = new PIXI.Graphics();
          objectSprite.beginFill(0xFFD700); // Oro per gli oggetti
          objectSprite.drawRect(0, 0, TILE_SIZE, TILE_SIZE);
          objectSprite.endFill();
          
          // Aggiungi un testo per identificare l'oggetto
          const text = new PIXI.Text(object.nome || objectId, { 
            fontSize: 10, 
            fill: 0x000000,
            align: 'center'
          });
          text.x = TILE_SIZE / 2 - text.width / 2;
          text.y = TILE_SIZE / 2 - text.height / 2;
          objectSprite.addChild(text);
        }
        
        // Posiziona lo sprite
        objectSprite.x = x * TILE_SIZE;
        objectSprite.y = y * TILE_SIZE;
        objectSprite.width = TILE_SIZE;
        objectSprite.height = TILE_SIZE;
        
        // Aggiunge metadati utili per l'interazione
        objectSprite.interactive = true;
        objectSprite.buttonMode = true;
        objectSprite.objectId = objectId;
        objectSprite.objectData = object;
        
        // Aggiungi lo sprite al container
        objectsContainer.addChild(objectSprite);
      }
      
      console.log("Rendering oggetti completato");
    } catch (error) {
      console.error("Errore nel rendering degli oggetti:", error);
    }
  }
  
  /**
   * Ottiene una texture per un tipo di oggetto specifico
   * @param {string} objectType - Il tipo di oggetto
   * @returns {PIXI.Texture|null} - La texture o null se non trovata
   */
  getObjectTexture(objectType) {
    // Mappatura dei tipi di oggetto alle texture
    const objectTextureMap = {
      'chest': this.textures.item,
      'furniture': this.textures.item,
      'default': this.textures.item
    };
    
    // Restituisci la texture corrispondente o null
    return objectTextureMap[objectType] || objectTextureMap.default || null;
  }
  
  /**
   * Disegna gli NPC presenti sulla mappa
   * @param {Object} scene - La scena in cui disegnare
   * @param {Object} mapData - I dati della mappa
   */
  renderMapNPCs(scene, mapData) {
    try {
      const { npcsContainer } = scene;
      const TILE_SIZE = 64;
      
      // Verifica che esistano NPC da renderizzare
      if (!mapData.npg) {
        console.log("Nessun NPC da renderizzare");
        return;
      }
      
      console.log(`Rendering NPC: ${Object.keys(mapData.npg).length}`);
      
      // Itera su tutti gli NPC
      for (const npcId in mapData.npg) {
        const npc = mapData.npg[npcId];
        let x, y;

        // --- Gestione Coordinate NPC --- 
        if (typeof npc.x === 'number' && typeof npc.y === 'number') {
            x = npc.x;
            y = npc.y;
        } else if (typeof npc.posizione === 'string') { 
            // Prova a parsare da stringa "(x, y)"
            const match = npc.posizione.match(/\((\d+),\s*(\d+)\)/);
            if (match) {
                x = parseInt(match[1], 10);
                y = parseInt(match[2], 10);
            } else {
                console.warn(`NPC ${npcId} con stringa posizione non valida: ${npc.posizione}`, npc);
                continue;
            }
        } else {
             console.warn(`NPC ${npcId} con coordinate non valide o mancanti:`, npc);
             continue;
        }
        // -------------------------------

        // Verifica che l'NPC abbia le coordinate necessarie (dopo parsing)
        // if (typeof npc.x !== 'number' || typeof npc.y !== 'number') { // Rimosso controllo ridondante
        //   console.warn(`NPC ${npcId} con coordinate non valide:`, npc);
        //   continue;
        // }
        
        // Ottieni la texture per questo tipo di NPC
        let npcSprite;
        const npcTexture = this.getNPCTexture(npc.tipo || 'default');
        
        if (npcTexture) {
          // Crea lo sprite dell'NPC
          npcSprite = new PIXI.Sprite(npcTexture);
        } else {
          // Crea un placeholder grafico per l'NPC
          npcSprite = new PIXI.Graphics();
          npcSprite.beginFill(0x0000FF); // Blu per gli NPC
          npcSprite.drawCircle(TILE_SIZE / 2, TILE_SIZE / 2, TILE_SIZE / 3);
          npcSprite.endFill();
          
          // Aggiungi un testo per identificare l'NPC
          const text = new PIXI.Text(npc.nome || npcId, { 
            fontSize: 10, 
            fill: 0xFFFFFF,
            align: 'center'
          });
          text.x = TILE_SIZE / 2 - text.width / 2;
          text.y = TILE_SIZE / 2 - text.height / 2;
          npcSprite.addChild(text);
        }
        
        // Posiziona lo sprite
        npcSprite.x = x * TILE_SIZE;
        npcSprite.y = y * TILE_SIZE;
        npcSprite.width = TILE_SIZE;
        npcSprite.height = TILE_SIZE;
        
        // Aggiunge metadati utili per l'interazione
        npcSprite.interactive = true;
        npcSprite.buttonMode = true;
        npcSprite.npcId = npcId;
        npcSprite.npcData = npc;
        
        // Aggiungi lo sprite al container
        npcsContainer.addChild(npcSprite);
      }
      
      console.log("Rendering NPC completato");
    } catch (error) {
      console.error("Errore nel rendering degli NPC:", error);
    }
  }
  
  /**
   * Ottiene una texture per un tipo di NPC specifico
   * @param {string} npcType - Il tipo di NPC
   * @returns {PIXI.Texture|null} - La texture o null se non trovata
   */
  getNPCTexture(npcType) {
    // Mappatura dei tipi di NPC alle texture
    const npcTextureMap = {
      'merchant': this.textures.npc,
      'villager': this.textures.npc,
      'guard': this.textures.npc,
      'default': this.textures.npc
    };
    
    // Restituisci la texture corrispondente o null
    return npcTextureMap[npcType] || npcTextureMap.default || null;
  }
  
  /**
   * Aggiunge lo sprite del giocatore alla scena
   * @param {Object} scene - Oggetto scena creato con createScene
   * @param {number} x - Coordinata X in tile
   * @param {number} y - Coordinata Y in tile
   * @returns {PIXI.Sprite} - Lo sprite del giocatore
   */
  addPlayer(scene, x, y) {
    if (!scene) return null;
    
    // Verifica se esiste già uno sprite del giocatore e rimuovilo
    if (this.playerSprites.has(scene.id)) {
      const oldPlayer = this.playerSprites.get(scene.id);
      if (oldPlayer.main && oldPlayer.main.parent) {
        oldPlayer.main.parent.removeChild(oldPlayer.main);
      }
      if (oldPlayer.glow && oldPlayer.glow.parent) {
        oldPlayer.glow.parent.removeChild(oldPlayer.glow);
      }
      if (oldPlayer.stopAnimation) {
        oldPlayer.stopAnimation();
      }
    }
    
    // Crea un container per il giocatore
    const playerContainer = new PIXI.Container();
    
    // Crea lo sprite del giocatore
    const playerSprite = new PIXI.Sprite(this.textures.player);
    playerSprite.anchor.set(0.5);
    playerSprite.width = 64;
    playerSprite.height = 64;
    
    // Posiziona il giocatore
    const TILE_SIZE = 64;
    playerSprite.x = (x + 0.5) * TILE_SIZE;
    playerSprite.y = (y + 0.5) * TILE_SIZE;
    
    // Aggiungi il container alla scena
    scene.stage.addChild(playerContainer);
    
    // Tenta di usare effetti avanzati solo se WebGL è disponibile
    if (isWebGLContextValid(scene.renderer)) {
      try {
        // Applica il filtro glow direttamente allo sprite
        playerSprite.filters = [new GlowFilter({
          distance: 15,
          outerStrength: 2,
          innerStrength: 1,
          color: 0x00FF00,
          quality: 0.5
        })];
        
        playerContainer.addChild(playerSprite);
        
        // Memorizza lo sprite del giocatore
        this.playerSprites.set(scene.id, {
          main: playerSprite,
          glow: null
        });
        
        console.log('GlowFilter applicato con successo');
      } catch (error) {
        console.error('Fallback al metodo alternativo dopo errore:', error);
        this.addPlayerWithManualGlow(scene, x, y, playerSprite, playerContainer);
      }
    } else {
      console.warn('Contesto WebGL non valido, utilizzo fallback Canvas');
      this.addPlayerWithManualGlow(scene, x, y, playerSprite, playerContainer);
    }
    
    return playerSprite;
  }
  
  /**
   * Versione di fallback per aggiungere il giocatore senza filtri WebGL
   * @private
   */
  addPlayerWithManualGlow(scene, x, y, playerSprite, playerContainer) {
    if (!scene || !playerSprite || !playerContainer) {
      console.error("Parametri mancanti per addPlayerWithManualGlow");
      return null;
    }
    
    // Variabili per il controllo dell'animazione
    let animationActive = true;
    
    // Utilizziamo un filtro di base invece di un filtro glow
    const basicFilter = new PIXI.filters.ColorMatrixFilter();
    
    // Applica il filtro
    if (playerContainer && basicFilter) {
      playerContainer.filters = [basicFilter];
    }
    
    // Crea animazione pulsante con protezione
    const animate = () => {
      if (!animationActive) return;
      if (!isWebGLContextValid(scene.renderer)) {
        console.warn('Contesto WebGL non valido durante animazione');
        // Riprova tra un po'
        setTimeout(() => {
          if (animationActive) requestAnimationFrame(animate);
        }, 1000);
        return;
      }
      
      try {
        // Continua l'animazione
        if (scene.isActive && animationActive) {
          requestAnimationFrame(animate);
        }
      } catch (err) {
        console.error('Errore durante animazione glow:', err);
        animationActive = false; // Ferma l'animazione in caso di errore
      }
    };
    
    // Avvia l'animazione
    animate();
    
    // Memorizza lo sprite del giocatore (sono due sprite insieme in questo caso)
    this.playerSprites.set(scene.id, {
      main: playerSprite,
      glow: null,
      animate: animate,
      stopAnimation: () => { animationActive = false; }
    });
  }
  
  /**
   * Aggiorna la posizione del giocatore con supporto per renderer ottimizzato
   * @param {string} sceneId - ID della scena
   * @param {number} x - Nuova coordinata X in tile
   * @param {number} y - Nuova coordinata Y in tile
   */
  updatePlayerPosition(sceneId, x, y) {
    const scene = this.activeScenes.get(sceneId);
    if (!scene) return;
    
    // Se la scena usa un renderer ottimizzato, delegagli l'aggiornamento
    if (scene.mapRenderer && typeof scene.mapRenderer.updatePlayerPosition === 'function') {
      scene.mapRenderer.updatePlayerPosition(x, y);
      return;
    }
    
    // Altrimenti usa l'implementazione standard
    const playerSprites = this.playerSprites.get(sceneId);
    if (!playerSprites) {
      // Se lo sprite del giocatore non esiste, crealo
      return this.addPlayer(scene, x, y);
    }
    
    const TILE_SIZE = 64;
    
    // Aggiorna la posizione
    const targetX = (x + 0.5) * TILE_SIZE;
    const targetY = (y + 0.5) * TILE_SIZE;
    
    // Applica un'animazione alla transizione
    const animateMove = () => {
      // Riferimenti agli sprite principale
      const playerSprite = playerSprites.main;
      const glowSprite = playerSprites.glow;
      
      // Calcola la direzione e la distanza
      const dx = targetX - playerSprite.x;
      const dy = targetY - playerSprite.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      
      // Se la distanza è sufficientemente piccola, imposta la posizione finale
      if (distance < 1) {
        playerSprite.x = targetX;
        playerSprite.y = targetY;
        if (glowSprite) {
          glowSprite.x = targetX;
          glowSprite.y = targetY;
        }
        return;
      }
      
      // Altrimenti, sposta gradualmente verso la destinazione
      const speed = Math.min(10, distance * 0.2); // Velocità proporzionale alla distanza
      playerSprite.x += dx * speed / distance;
      playerSprite.y += dy * speed / distance;
      if (glowSprite) {
        glowSprite.x = playerSprite.x;
        glowSprite.y = playerSprite.y;
      }
      
      // Continua l'animazione
      requestAnimationFrame(animateMove);
    };
    
    // Avvia l'animazione di movimento
    animateMove();
  }
  
  /**
   * Aggiorna le entità sulla mappa
   * @param {string} sceneId - ID della scena
   * @param {Array} entities - Array di entità da renderizzare
   */
  updateEntities(sceneId, entities) {
    const sceneData = this.activeScenes.get(sceneId);
    if (!sceneData || !entities) return;
    
    const scene = sceneData.app; // Ottieni l'applicazione PIXI dalla mappa delle scene
    if (!scene || !scene.stage) {
      console.error("Applicazione PIXI o stage non trovati per updateEntities");
      return;
    }
    
    // Accedi a entitiesContainer tramite la scena PIXI (dove è stato aggiunto da renderMap)
    const entitiesContainer = scene.entitiesContainer; 
    if (!entitiesContainer) {
        console.error("entitiesContainer non trovato sulla scena PIXI. Assicurati che renderMap sia stato eseguito.");
        // Potremmo creare il container qui come fallback?
        // scene.entitiesContainer = new PIXI.Container();
        // scene.stage.addChild(scene.entitiesContainer);
        // entitiesContainer = scene.entitiesContainer;
        return; // Per ora usciamo se non esiste
    }

    const TILE_SIZE = 64;
    
    // Rimuovi le entità esistenti
    while (entitiesContainer.children.length > 0) {
      const child = entitiesContainer.children[0];
      entitiesContainer.removeChild(child);
      if (child.destroy) {
        child.destroy();
      }
    }
    
    // Pulisci la mappa delle entità
    this.entitySprites.get(sceneId).clear();
    
    // Aggiungi le nuove entità
    entities.forEach(entity => {
      // Determina il tipo di texture in base al tipo di entità
      let texture;
      if (entity.type === 'npc') {
        texture = this.textures.npc;
      } else if (entity.type === 'item') {
        texture = this.textures.item;
      } else {
        texture = this.textures.default;
      }
      
      // Crea lo sprite per l'entità
      const sprite = new PIXI.Sprite(texture);
      sprite.x = entity.x * TILE_SIZE;
      sprite.y = entity.y * TILE_SIZE;
      sprite.width = TILE_SIZE;
      sprite.height = TILE_SIZE;
      
      // Aggiungi metadati all'entità
      sprite.entityData = entity;
      sprite.interactive = true;
      sprite.buttonMode = true;
      
      // Memorizza l'entità nella mappa delle entità
      const entityId = `entity-${entity.id || entity.type}-${entity.x}-${entity.y}`;
      this.entitySprites.get(sceneId).set(entityId, sprite);
      
      // Aggiungi l'etichetta dell'entità
      const label = new PIXI.Text(entity.name || entity.type, {
        fontFamily: 'Arial',
        fontSize: 10,
        fill: 0xFFFFFF,
        stroke: 0x000000,
        strokeThickness: 2
      });
      label.position.set(entity.x * TILE_SIZE + 2, entity.y * TILE_SIZE - 12);
      
      entitiesContainer.addChild(sprite);
      entitiesContainer.addChild(label);
    });
  }
  
  /**
   * Pulisce una specifica scena PIXI rimuovendo l'app e le sue risorse
   * @param {string} id - L'ID della scena da pulire (es. 'map_scene_taverna')
   */
  cleanupScene(id) {
    console.log(`[PixiManager] cleanupScene: Inizio pulizia per sceneId: ${id}`);
    if (this.activeScenes.has(id)) {
      const app = this.activeScenes.get(id);
      console.log(`[PixiManager] cleanupScene(${id}): Trovata app PIXI attiva.`);
      
      try {
        // Distruggi l'applicazione PIXI
        // Il secondo argomento { children: true, texture: true, baseTexture: true }
        // assicura una pulizia più profonda delle risorse GPU
        console.log(`[PixiManager] cleanupScene(${id}): Tentativo di distruzione app.destroy(true, {...})...`);
        app.destroy(true, { children: true, texture: true, baseTexture: true });
        console.log(`[PixiManager] cleanupScene(${id}): App PIXI distrutta con successo.`);

      } catch (error) {
        console.error(`[PixiManager] cleanupScene(${id}): Errore durante la distruzione dell'app PIXI:`, error);
      } finally {
        // Rimuovi la scena dalla mappa delle scene attive INDIPENDENTEMENTE dall'esito
        this.activeScenes.delete(id);
        console.log(`[PixiManager] cleanupScene(${id}): Scena rimossa dalla mappa activeScenes.`);
      }
    } else {
      console.warn(`[PixiManager] cleanupScene(${id}): Nessuna scena attiva trovata con questo ID. Pulizia saltata.`);
    }

    // Pulisci gli sprite associati a questa scena
    this.playerSprites.delete(id);
    console.log(`[PixiManager] cleanupScene(${id}): Sprite giocatore rimosso (se esisteva).`);
    this.entitySprites.delete(id);
    console.log(`[PixiManager] cleanupScene(${id}): Cache sprite entità rimossa (se esisteva).`);


    // Nota: Non puliamo le texture globali qui (this.textures)
    // perché potrebbero essere usate da altre scene.
    // La pulizia globale avviene solo con this.cleanup()
  }
  
  /**
   * Pulisce tutte le risorse PIXI e prepara la distruzione del manager
   */
  cleanup() {
    // Pulisci tutte le scene attive
    for (const id of this.activeScenes.keys()) {
      this.cleanupScene(id);
    }
    
    // Distruggi l'applicazione PIXI principale
    if (this.app) {
      try {
        // Rimuovi tutti i filtri prima della distruzione
        if (this.app.stage && this.app.stage.filters) {
          this.app.stage.filters = null;
        }
        
        // Destroy sicuro con true per rimuovere anche le texture
        this.app.destroy(true, { children: true, texture: true, baseTexture: true });
      } catch (err) {
        console.error('Errore durante cleanup dell\'app PIXI:', err);
      } finally {
        this.app = null;
      }
    }
    
    // Pulisci le texture
    for (const key in this.textures) {
      if (this.textures[key] && this.textures[key].destroy) {
        try {
          this.textures[key].destroy(true);
        } catch (err) {
          console.error(`Errore durante distruzione texture ${key}:`, err);
        }
      }
    }
    this.textures = {};
    
    // Pulisci le mappe
    this.playerSprites.clear();
    this.entitySprites.clear();
    
    this.isInitialized = false;
    console.log('PixiManager: pulizia globale completata');
  }
  
  /**
   * Ottiene una texture dal cache o ne crea una nuova
   * @param {string} name - Nome della texture
   * @param {Function} creator - Funzione per creare la texture se non esiste
   * @returns {PIXI.Texture} - La texture richiesta
   */
  getTexture(name, creator) {
    if (this.textures[name]) {
      return this.textures[name];
    }
    
    if (creator && typeof creator === 'function') {
      const texture = creator();
      this.textures[name] = texture;
      return texture;
    }
    
    return null;
  }
}

/**
 * Verifica se il contesto WebGL è valido
 * @param {PIXI.Renderer} renderer - Renderer da verificare
 * @returns {boolean} - true se il contesto è valido, false altrimenti
 */
function isWebGLContextValid(renderer) {
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

// Export dell'istanza singleton
const pixiManager = new PixiManager();
export default pixiManager; 