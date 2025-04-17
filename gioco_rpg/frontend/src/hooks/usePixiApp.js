import { useRef, useEffect } from 'react';
import * as PIXI from 'pixi.js';
import { Viewport } from 'pixi-viewport';

/**
 * Hook personalizzato per gestire un'applicazione Pixi.js
 * @param {React.RefObject} containerRef - Riferimento al container DOM
 * @param {Object} options - Opzioni per l'applicazione Pixi
 * @returns {Object} - Riferimenti all'app e al viewport
 */
export default function usePixiApp(containerRef, options = {}) {
  const appRef = useRef(null);
  const viewportRef = useRef(null);
  
  useEffect(() => {
    if (!containerRef.current) return;
    
    // Creazione dell'applicazione Pixi
    const app = new PIXI.Application({
      width: containerRef.current.clientWidth,
      height: containerRef.current.clientHeight,
      backgroundColor: options.backgroundColor || 0x1a1a1a,
      resolution: window.devicePixelRatio || 1,
      antialias: true,
      autoDensity: true
    });
    
    // Aggiunta del canvas al DOM
    containerRef.current.innerHTML = '';
    containerRef.current.appendChild(app.view);
    appRef.current = app;
    
    // Fix per PIXI.js 6.5.9: proteggi l'interaction manager da errori frequenti
    if (app.renderer && app.renderer.plugins && app.renderer.plugins.interaction) {
      const interactionManager = app.renderer.plugins.interaction;
      
      // Patch completa e globale per tutto l'interaction manager
      // Questa funzione wrapperà ogni metodo dell'interaction manager con gestione degli errori
      const safeInteractionWrapper = (originalMethod, methodName) => {
        return function(...args) {
          try {
            // Controlli generici per tutti i metodi
            if (!this || this._destroyed) return false;
            
            // Controlli specifici per emit
            if (methodName.includes('emit') || methodName.includes('fire') || methodName.includes('dispatch')) {
              if (!this.emit || typeof this.emit !== 'function') {
                return false;
              }
            }
            
            // Controlli specifici per processPointerOverOut
            if (methodName === 'processPointerOverOut') {
              const [interactionEvent, displayObject, hit] = args;
              if (!interactionEvent || !displayObject) return false;
              if (!interactionEvent.data) return false;
              if (!interactionEvent.data.global) return false;
              
              // Verifica che global abbia le proprietà necessarie
              const global = interactionEvent.data.global;
              if (global.x === undefined || global.y === undefined) return false;
              
              // Verifica che il this.activeInteractionData abbia un array accessible
              if (!this.activeInteractionData) return false;
              
              // Controlla che esista un ID per questo evento
              const pointerId = interactionEvent.data.pointerId || 1;
              if (!this.activeInteractionData[pointerId]) return false;
            }
            
            // Controlli specifici per processPointerMove
            if (methodName === 'processPointerMove') {
              const [interactionEvent] = args;
              if (!interactionEvent || !interactionEvent.data) return false;
              
              // Verifica la struttura dell'emitter
              if (this.onPointerMove && 
                  (!this.onPointerMove.emit || typeof this.onPointerMove.emit !== 'function')) {
                // Ricostruisci l'emitter se possibile
                if (typeof PIXI.utils.EventEmitter === 'function') {
                  this.onPointerMove = new PIXI.utils.EventEmitter();
                } else {
                  return false;
                }
              }
            }
            
            // Controlli specifici per processInteractive
            if (methodName === 'processInteractive') {
              const [interactionEvent, displayObject, func] = args;
              if (!interactionEvent || !displayObject || !func) return false;
              if (typeof func !== 'function') return false;
            }
            
            // Esegui il metodo originale con protezione
            return originalMethod.apply(this, args);
          } catch (err) {
            console.warn(`Errore in ${methodName} evitato:`, err.message);
            return false;
          }
        };
      };
      
      // Applica il wrapper di sicurezza a tutti i metodi principali dell'interaction manager
      const methodsToPatch = [
        'processPointerDown', 'processPointerUp', 'processPointerMove', 
        'processPointerOverOut', 'processInteractive'
      ];
      
      methodsToPatch.forEach(methodName => {
        if (interactionManager[methodName] && typeof interactionManager[methodName] === 'function') {
          const originalMethod = interactionManager[methodName];
          interactionManager[methodName] = safeInteractionWrapper(originalMethod, methodName);
        }
      });
      
      // Aggiungi una protezione per il metodo mapPositionToPoint che può causare errori
      if (interactionManager.mapPositionToPoint) {
        const originalMapPositionToPoint = interactionManager.mapPositionToPoint;
        interactionManager.mapPositionToPoint = function(point, x, y) {
          try {
            if (!point || typeof point !== 'object') return;
            return originalMapPositionToPoint.call(this, point, x, y);
          } catch (err) {
            console.warn('Errore in mapPositionToPoint evitato:', err.message);
            // Imposta valori predefiniti sicuri
            if (point) {
              point.x = x || 0;
              point.y = y || 0;
            }
          }
        };
      }
      
      // Protegge anche da eventi di rimozione che possono causare problemi
      if (interactionManager.removeEvents) {
        const originalRemoveEvents = interactionManager.removeEvents;
        interactionManager.removeEvents = function() {
          try {
            return originalRemoveEvents.call(this);
          } catch (err) {
            console.warn('Errore in removeEvents evitato:', err.message);
          }
        };
      }
    }
    
    // Creazione del viewport se richiesto
    if (options.useViewport) {
      const viewport = new Viewport({
        screenWidth: app.view.width,
        screenHeight: app.view.height,
        worldWidth: options.worldWidth || 1000,
        worldHeight: options.worldHeight || 1000,
        interaction: app.renderer.plugins.interaction
      });
      
      // Configurazione delle funzionalità del viewport
      viewport
        .drag()
        .pinch()
        .wheel()
        .decelerate()
        .clampZoom({
          minScale: options.minZoom || 0.5,
          maxScale: options.maxZoom || 2
        });
      
      // Aggiunta del viewport allo stage
      app.stage.addChild(viewport);
      viewportRef.current = viewport;
    }
    
    // Gestore per il ridimensionamento della finestra
    const handleResize = () => {
      if (containerRef.current) {
        app.renderer.resize(
          containerRef.current.clientWidth,
          containerRef.current.clientHeight
        );
        
        if (viewportRef.current) {
          viewportRef.current.resize(
            containerRef.current.clientWidth,
            containerRef.current.clientHeight
          );
        }
      }
    };
    
    window.addEventListener('resize', handleResize);
    
    // Pulizia al dismount del componente
    return () => {
      window.removeEventListener('resize', handleResize);
      
      if (app) {
        app.destroy(true, {
          children: true,
          texture: true,
          baseTexture: true
        });
      }
    };
  }, [containerRef, options]);
  
  return { 
    app: appRef.current, 
    viewport: viewportRef.current 
  };
} 