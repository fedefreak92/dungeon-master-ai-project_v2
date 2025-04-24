import { useRef, useEffect, useState } from 'react';
import * as PIXI from 'pixi.js';

// Disabilita alcune funzionalità problematiche di PIXI globalmente
// Questo aiuta a prevenire errori in alcuni browser
try {
  // Disattiva l'auto-detect del renderer per forzare un rendering predefinito
  PIXI.settings.PREFER_ENV = PIXI.ENV.WEBGL2;
  
  // Imposta l'opzione di scala per evitare problemi con le texture
  PIXI.settings.SCALE_MODE = PIXI.SCALE_MODES.NEAREST;
  
  // Imposta un limite inferiore di texture per evitare problemi di memoria
  PIXI.settings.SPRITE_MAX_TEXTURES = Math.min(PIXI.settings.SPRITE_MAX_TEXTURES, 16);
  
  // Disabilita i mipmaps che possono causare problemi su alcuni dispositivi
  PIXI.settings.MIPMAP_TEXTURES = PIXI.MIPMAP_MODES.OFF;
  
  // Utilizzare Typed Arrays per evitare problemi di overflow
  PIXI.settings.PREFER_WEBGL_2 = false;
} catch (settingsError) {
  console.warn('Impossibile configurare PIXI.settings:', settingsError);
}

/**
 * Hook personalizzato per gestire un'applicazione Pixi.js
 * @param {React.RefObject} containerRef - Riferimento al container DOM
 * @param {Object} options - Opzioni per l'applicazione Pixi
 * @returns {Object} - Riferimenti all'app e al viewport
 */
export default function usePixiApp(containerRef, options = {}) {
  const appRef = useRef(null);
  const viewportRef = useRef(null);
  const destructionFlagRef = useRef(false); // Flag per indicare che la distruzione è in corso
  const [appReady, setAppReady] = useState(false);
  const [viewportReady, setViewportReady] = useState(false);
  
  // Funzione sicura per la pulizia globale dei riferimenti PIXI
  const cleanupPixiReferences = () => {
    // Svuota la cache delle texture globale se disponibile
    try {
      if (PIXI.utils && PIXI.utils.TextureCache) {
        Object.keys(PIXI.utils.TextureCache).forEach(key => {
          try {
            delete PIXI.utils.TextureCache[key];
          } catch (e) {}
        });
      }
      
      // Svuota la cache dei BaseTexture se disponibile
      if (PIXI.utils && PIXI.utils.BaseTextureCache) {
        Object.keys(PIXI.utils.BaseTextureCache).forEach(key => {
          try {
            delete PIXI.utils.BaseTextureCache[key];
          } catch (e) {}
        });
      }
    } catch (cacheError) {
      console.warn('Errore durante la pulizia delle cache PIXI:', cacheError);
    }
  };
  
  useEffect(() => {
    if (!containerRef.current) return;
    
    console.log("PIXI INIT: Inizializzazione diretta dell'app");
    
    // Impostazione preventiva per evitare errori WebGL
    let forceCanvas = false;
    
    try {
      // Verifica se WebGL è supportato
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      
      if (!gl) {
        console.warn("PIXI INIT: WebGL non disponibile, utilizzo canvas");
        forceCanvas = true;
      } else {
        // Test di base per verificare se WebGL funziona
        try {
          // Prova a creare un buffer e impostare i valori di base
          const testBuffer = gl.createBuffer();
          gl.bindBuffer(gl.ARRAY_BUFFER, testBuffer);
          gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([0, 0, 0, 0]), gl.STATIC_DRAW);
          
          // Pulizia del buffer
          gl.bindBuffer(gl.ARRAY_BUFFER, null);
          gl.deleteBuffer(testBuffer);
        } catch (webglTestError) {
          console.warn("PIXI INIT: WebGL disponibile ma errore di test, utilizzo canvas:", webglTestError);
          forceCanvas = true;
        }
      }
    } catch (glCheckError) {
      console.warn("PIXI INIT: Errore nel test WebGL, utilizzo canvas:", glCheckError);
      forceCanvas = true;
    }
    
    // Imposta appRef a null prima dell'inizializzazione per evitare riferimenti stale
    appRef.current = null;
    viewportRef.current = null;
    destructionFlagRef.current = false;
    
    // Creazione dell'applicazione Pixi con dimensioni fisse e interazioni disabilitate
    try {
      // Crea un renderer con le impostazioni più sicure possibili
      let app = null;
      
      // Controlla se dobbiamo forzare canvas
      if (forceCanvas) {
        try {
          app = new PIXI.Application({
            width: options.width || containerRef.current.clientWidth || 800,
            height: options.height || containerRef.current.clientHeight || 600,
            backgroundColor: options.backgroundColor || 0x1a1a1a,
            forceCanvas: true,
            antialias: false,
            resolution: 1,
            clearBeforeRender: true,
            autoStart: true
          });
          console.log("PIXI INIT: Applicazione creata con CanvasRenderer");
        } catch (canvasAppError) {
          console.error("PIXI INIT: Errore nella creazione dell'app con Canvas:", canvasAppError);
          throw canvasAppError;
        }
      } else {
        // Altrimenti prova con WebGL (predefinito)
        try {
          app = new PIXI.Application({
            width: options.width || containerRef.current.clientWidth || 800,
            height: options.height || containerRef.current.clientHeight || 600,
            backgroundColor: options.backgroundColor || 0x1a1a1a,
            resolution: window.devicePixelRatio || 1,
            antialias: true,
            autoDensity: true,
            clearBeforeRender: true,
            forceCanvas: false,
            // IMPORTANTE: Disattiva completamente le interazioni
            interactive: false
          });
          console.log("PIXI INIT: Applicazione creata con WebGLRenderer");
        } catch (webglAppError) {
          console.warn("PIXI INIT: Errore nella creazione dell'app con WebGL, tentativo con Canvas:", webglAppError);
          
          // Fallback a canvas se WebGL fallisce
          try {
            app = new PIXI.Application({
              width: options.width || containerRef.current.clientWidth || 800,
              height: options.height || containerRef.current.clientHeight || 600,
              backgroundColor: options.backgroundColor || 0x1a1a1a,
              forceCanvas: true,
              antialias: false,
              resolution: 1,
              clearBeforeRender: true,
              autoStart: true
            });
            console.log("PIXI INIT: Fallback a CanvasRenderer riuscito");
          } catch (fallbackError) {
            console.error("PIXI INIT: Errore nel fallback a Canvas:", fallbackError);
            throw fallbackError;
          }
        }
      }
      
      // Verifica che l'app sia stata creata correttamente
      if (!app) {
        throw new Error("PIXI INIT: Impossibile creare l'applicazione PIXI");
      }
      
      // PROTEZIONE CONTRO RENDER NULL: sovrascriviamo il metodo render con versione safe
      const originalRender = app.render;
      app.render = function() {
        try {
          // Controllo di distruzione
          if (destructionFlagRef.current) {
            console.log("PIXI RENDER: App in fase di distruzione, render saltato");
            return false;
          }
          
          // Verifica se il renderer e stage esistono prima di chiamare render
          if (this.renderer && this.stage && typeof originalRender === 'function') {
            return originalRender.apply(this, arguments);
          } else {
            return false;
          }
        } catch (e) {
          console.warn('PIXI RENDER: Errore durante il rendering:', e);
          return false;
        }
      };
      
      // Assicuriamoci che il renderer sia creato e valido
      if (!app.renderer) {
        throw new Error('PIXI INIT: Renderer non creato correttamente');
      }
      
      if (!app.stage) {
        throw new Error('PIXI INIT: Stage non creato correttamente');
      }
      
      // PROTEZIONE TICKER: ticker semplificato senza errori
      if (app.ticker) {
        const originalUpdate = app.ticker.update;
        app.ticker.update = function(currentTime) {
          try {
            // Controllo di distruzione
            if (destructionFlagRef.current) {
              console.log("PIXI TICKER: App in fase di distruzione, update saltato");
              return false;
            }
            
            // Verifica se l'app può renderizzare prima di aggiornare
            if (app.renderer && app.stage) {
              return originalUpdate.call(this, currentTime);
            } else {
              return false;
            }
          } catch (e) {
            console.warn('PIXI TICKER: Errore durante l\'aggiornamento:', e);
            return false;
          }
        };
      }
      
      // Aggiunta sicura del canvas al DOM
      try {
        console.log("PIXI INIT: Inserimento del canvas nel DOM");
        // Svuota il container
        containerRef.current.innerHTML = '';
        
        // Verifica che il canvas esista
        if (!app.view) {
          throw new Error("PIXI INIT: Canvas non trovato nell'app");
        }
        
        // Aggiungi il canvas al DOM
        containerRef.current.appendChild(app.view);
        
        // Imposta stili espliciti per il canvas
        app.view.style.position = 'absolute';
        app.view.style.display = 'block';
        app.view.style.width = '100%';
        app.view.style.height = '100%';
        app.view.style.zIndex = '1';
      } catch (domError) {
        console.error("PIXI INIT: Errore nell'inserimento del canvas nel DOM:", domError);
        throw domError;
      }
      
      // Imposta l'oggetto app nel riferimento
      appRef.current = app;
      
      console.log("PIXI INIT: App creata con dimensioni:", app.view.width, app.view.height);
      
      // Segnala che l'app è pronta
      setAppReady(true);
      
      // Creazione del viewport se richiesto
      if (options.useViewport) {
        try {
          // Importazione dinamica di pixi-viewport
          import('pixi-viewport').then(({ Viewport }) => {
            try {
              console.log("PIXI INIT: Creazione del viewport");
              
              // Crea il viewport con opzioni minime
              const viewport = new Viewport({
                screenWidth: app.view.width,
                screenHeight: app.view.height,
                worldWidth: options.worldWidth || 2000,
                worldHeight: options.worldHeight || 2000,
                noTicker: true
              });
              
              // Aggiungi getChildByName se non è disponibile
              if (typeof viewport.getChildByName !== 'function') {
                console.log("PIXI INIT: Aggiunta implementazione di getChildByName");
                viewport.getChildByName = function(name) {
                  if (!this.children) return null;
                  return this.children.find(child => child && child.name === name);
                };
              }
              
              // Inizializza le proprietà fondamentali
              viewport.name = 'viewport';
              
              // Sovrascrivi i metodi critici con versioni semplificate
              viewport.moveCenter = function(x, y) {
                try {
                  if (!this.scale) this.scale = { x: 1, y: 1 };
                  if (!this.position) this.position = { x: 0, y: 0 };
                  
                  this.position.x = (this.screenWidth / 2) - (x * this.scale.x);
                  this.position.y = (this.screenHeight / 2) - (y * this.scale.y);
                  
                  return this;
                } catch (error) {
                  console.warn('PIXI VIEWPORT: Errore in moveCenter:', error);
                  return this;
                }
              };
              
              viewport.resize = function(screenWidth, screenHeight, worldWidth, worldHeight) {
                try {
                  this.screenWidth = screenWidth || app.view.width;
                  this.screenHeight = screenHeight || app.view.height;
                  
                  if (worldWidth) this.worldWidth = worldWidth;
                  if (worldHeight) this.worldHeight = worldHeight;
                  
                  return this;
                } catch (error) {
                  console.warn('PIXI VIEWPORT: Errore in resize:', error);
                  return this;
                }
              };
              
              // Aggiungi al container
              app.stage.addChild(viewport);
              
              // Inizializza un container base per testare il viewport
              const worldContainer = new PIXI.Container();
              worldContainer.name = 'world-container';
              viewport.addChild(worldContainer);
              
              // Crea una griglia di base per visualizzare che il viewport funziona
              const gridContainer = new PIXI.Container();
              gridContainer.name = 'grid-layer';
              worldContainer.addChild(gridContainer);
              
              // Aggiungi una semplice griglia
              const cellSize = 64;
              const rows = 10;
              const cols = 15;
              
              // Crea una singola grafica per la griglia invece di molti elementi
              const grid = new PIXI.Graphics();
              grid.lineStyle(1, 0x333333, 0.5);
              
              // Linee verticali
              for (let x = 0; x <= cols; x++) {
                grid.moveTo(x * cellSize, 0);
                grid.lineTo(x * cellSize, rows * cellSize);
              }
              
              // Linee orizzontali
              for (let y = 0; y <= rows; y++) {
                grid.moveTo(0, y * cellSize);
                grid.lineTo(cols * cellSize, y * cellSize);
              }
              
              gridContainer.addChild(grid);
              
              // Salva il viewport
              viewportRef.current = viewport;
              
              // Rendering sicuro (una volta che tutto è pronto)
              try {
                app.render();
              } catch (renderError) {
                console.warn("PIXI INIT: Errore nel rendering iniziale:", renderError);
              }
              
              // Segnala che il viewport è pronto
              setViewportReady(true);
            } catch (viewportError) {
              console.error("PIXI INIT: Errore nella creazione del viewport:", viewportError);
              setViewportReady(false);
            }
          }).catch(importError => {
            console.error("PIXI INIT: Errore nell'importazione di pixi-viewport:", importError);
            setViewportReady(false);
          });
        } catch (viewportSetupError) {
          console.error("PIXI INIT: Errore nell'inizializzazione del viewport:", viewportSetupError);
          setViewportReady(false);
        }
      } else {
        // Se non abbiamo bisogno del viewport, impostiamo direttamente lo stato a pronto
        setViewportReady(true);
      }
    } catch (appInitError) {
      console.error('PIXI INIT: Errore critico nella creazione dell\'app:', appInitError);
      appRef.current = null;
      viewportRef.current = null;
      setAppReady(false);
      setViewportReady(false);
    }
    
    // Gestore per il ridimensionamento della finestra
    const handleResize = () => {
      if (!containerRef.current || !appRef.current || destructionFlagRef.current) return;
      
      const app = appRef.current;
      
      console.log("PIXI RESIZE: Adattamento dimensioni");
      
      try {
        const width = containerRef.current.clientWidth;
        const height = containerRef.current.clientHeight;
        
        if (app.renderer && typeof app.renderer.resize === 'function') {
          app.renderer.resize(width, height);
        }
        
        // Ridimensiona il viewport se disponibile
        if (viewportRef.current) {
          const viewport = viewportRef.current;
          if (typeof viewport.resize === 'function') {
            viewport.resize(width, height);
          }
        }
      } catch (resizeError) {
        console.warn('PIXI RESIZE: Errore nel ridimensionamento:', resizeError);
      }
    };
    
    window.addEventListener('resize', handleResize);
    
    // Pulizia al dismount del componente
    return () => {
      window.removeEventListener('resize', handleResize);
      
      // Imposta flag di distruzione per bloccare le operazioni in-flight
      destructionFlagRef.current = true;
      
      console.log("PIXI CLEANUP: Inizializzazione pulizia");
      
      const app = appRef.current;
      
      if (!app) {
        console.log("PIXI CLEANUP: Nessuna app da pulire");
        return;
      }
      
      // Funzione di pulizia sicura basata sui passaggi
      const cleanupSteps = async () => {
        try {
          // STEP 1: Segnala che stiamo per distruggere l'app
          // Imposta flag per bloccare operazioni concorrenti
          console.log("PIXI CLEANUP: Step 1 - Inizio pulizia app");
          
          // STEP 2: Ferma il ticker per prevenire ulteriori animazioni
          try {
            if (app.ticker) {
              app.ticker.stop();
              app.ticker.remove(null, null);
              console.log("PIXI CLEANUP: Step 2 - Ticker fermato");
            }
          } catch (tickerError) {
            console.warn("PIXI CLEANUP: Errore nel fermare il ticker:", tickerError);
          }
          
          // STEP 3: Pulizia del viewport
          try {
            if (viewportRef.current) {
              const viewport = viewportRef.current;
              
              // Rimuovi tutti i figli dal viewport
              if (viewport.children && viewport.children.length > 0) {
                while (viewport.children.length > 0) {
                  const child = viewport.children[0];
                  try {
                    viewport.removeChild(child);
                    if (child && typeof child.destroy === 'function') {
                      child.destroy({ children: true });
                    }
                  } catch (childError) {
                    console.warn("PIXI CLEANUP: Errore nella rimozione di un figlio del viewport:", childError);
                  }
                }
              }
              
              // Non rimuoviamo il viewport dallo stage per evitare errori
              console.log("PIXI CLEANUP: Step 3 - Viewport pulito");
            }
          } catch (viewportError) {
            console.warn("PIXI CLEANUP: Errore nella pulizia del viewport:", viewportError);
          }
          
          // STEP 4: Pulizia dello stage principale
          try {
            if (app.stage && app.stage.children) {
              while (app.stage.children.length > 0) {
                const child = app.stage.children[0];
                try {
                  app.stage.removeChild(child);
                  if (child && typeof child.destroy === 'function') {
                    child.destroy({ children: true });
                  }
                } catch (stageChildError) {
                  console.warn("PIXI CLEANUP: Errore nella rimozione di un figlio dello stage:", stageChildError);
                }
              }
              console.log("PIXI CLEANUP: Step 4 - Stage pulito");
            }
          } catch (stageError) {
            console.warn("PIXI CLEANUP: Errore nella pulizia dello stage:", stageError);
          }
          
          // STEP 5: Rimozione del canvas dal DOM
          try {
            if (app.view && app.view.parentNode) {
              app.view.parentNode.removeChild(app.view);
              console.log("PIXI CLEANUP: Step 5 - Canvas rimosso dal DOM");
            }
          } catch (viewError) {
            console.warn("PIXI CLEANUP: Errore nella rimozione del canvas:", viewError);
          }
          
          // STEP 6: Disabilita il renderer prima di distruggerlo
          try {
            if (app.renderer) {
              // Disabilita i metodi principali del renderer
              if (typeof app.renderer.render === 'function') {
                app.renderer.render = function() { return null; };
              }
              
              // Svuota risorse WebGL
              if (app.renderer.gl) {
                try {
                  app.renderer.gl.getExtension('WEBGL_lose_context');
                } catch (glError) {
                  console.warn("PIXI CLEANUP: Errore nella pulizia del contesto WebGL:", glError);
                }
                
                // Svuota i riferimenti al contesto WebGL
                app.renderer.gl = null;
              }
              
              console.log("PIXI CLEANUP: Step 6 - Renderer disabilitato");
            }
          } catch (rendererError) {
            console.warn("PIXI CLEANUP: Errore nella disabilitazione del renderer:", rendererError);
          }
          
          // STEP 7: Prevenzione di errori nel metodo destroy di Application
          try {
            // Crea copie di sicurezza di riferimenti importanti
            const stage = app.stage;
            const ticker = app.ticker;
            const renderer = app.renderer;
            
            // Imposta proprietà nulle per evitare che destroy() causi errori
            app.stage = null;
            app.ticker = null;
            app.renderer = null;
            
            // Distruggi i componenti individualmente
            if (stage && typeof stage.destroy === 'function') {
              try {
                stage.destroy({ children: true });
              } catch (stageDestroyError) {
                console.warn("PIXI CLEANUP: Errore nella distruzione dello stage:", stageDestroyError);
              }
            }
            
            if (ticker && typeof ticker.destroy === 'function') {
              try {
                ticker.destroy();
              } catch (tickerDestroyError) {
                console.warn("PIXI CLEANUP: Errore nella distruzione del ticker:", tickerDestroyError);
              }
            }
            
            if (renderer && typeof renderer.destroy === 'function') {
              try {
                renderer.destroy(true);
              } catch (rendererDestroyError) {
                console.warn("PIXI CLEANUP: Errore nella distruzione del renderer:", rendererDestroyError);
              }
            }
            
            console.log("PIXI CLEANUP: Step 7 - Componenti distrutti separatamente");
          } catch (componentsDestroyError) {
            console.warn("PIXI CLEANUP: Errore nella distruzione dei componenti:", componentsDestroyError);
          }
          
          // STEP 8: Pulizia dei riferimenti
          try {
            // Pulisci riferimenti globali
            cleanupPixiReferences();
            
            // Rilascia riferimenti React
            appRef.current = null;
            viewportRef.current = null;
            
            console.log("PIXI CLEANUP: Step 8 - Riferimenti puliti");
          } catch (referencesError) {
            console.warn("PIXI CLEANUP: Errore nella pulizia dei riferimenti:", referencesError);
          }
          
          console.log("PIXI CLEANUP: Pulizia completata con successo");
        } catch (globalCleanupError) {
          console.error("PIXI CLEANUP: Errore critico nella pulizia globale:", globalCleanupError);
        }
      };
      
      // Avvia la pulizia
      cleanupSteps();
    };
  }, [containerRef, options]);
  
  return { 
    app: appReady ? appRef.current : null, 
    viewport: viewportReady ? viewportRef.current : null,
    appReady,
    viewportReady
  };
} 