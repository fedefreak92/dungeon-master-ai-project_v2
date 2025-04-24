# Sistema di Rendering Mappe Ottimizzato

Questo documento descrive il sistema di rendering delle mappe ottimizzato per Pixi.js implementato nel gioco RPG.

## Componenti Principali

Il sistema di rendering delle mappe è composto dai seguenti componenti:

1. **TileAtlas**: Gestisce le texture dei tile in un unico atlante per minimizzare i cambi di texture.
2. **OptimizedMapRenderer**: Renderer per mappe di grandi dimensioni che implementa viewport culling e chunk.
3. **CachedMapRenderer**: Renderer che utilizza RenderTexture per cachare gli elementi statici della mappa.
4. **MapRendererFactory**: Factory che seleziona automaticamente il renderer più appropriato.

## Quando Usare Ciascun Renderer

- **MapRenderer standard**: Per mappe piccole (<50x50 tile) con pochi oggetti (<100).
- **OptimizedMapRenderer**: Per mappe grandi con molti oggetti, dove il culling è essenziale.
- **CachedMapRenderer**: Per mappe con molti elementi statici e pochi elementi dinamici.

## Come Utilizzare il Sistema

### Renderizzazione Automatica Ottimizzata

Il metodo più semplice è utilizzare `pixiManager.renderMapOptimized()` che seleziona automaticamente il renderer più appropriato:

```javascript
// In un componente React
useEffect(() => {
  if (pixiApp && mapData) {
    pixiManager.renderMapOptimized(pixiApp, mapData);
  }
}, [pixiApp, mapData]);
```

### Configurazione Manuale del Renderer

Se hai esigenze specifiche, puoi configurare manualmente il renderer:

```javascript
import MapRendererFactory from './pixi/utils/MapRendererFactory';

// In un componente React
useEffect(() => {
  if (pixiApp && mapData) {
    const options = {
      forceOptimized: true,  // Forza l'uso di OptimizedMapRenderer
      chunkSize: 8,          // Dimensione dei chunk (default: 16)
      useCaching: true       // Usa RenderTexture per elementi statici
    };
    
    async function initRenderer() {
      const renderer = await MapRendererFactory.createRenderer(
        pixiApp,
        pixiApp.stage,
        mapData,
        options
      );
      
      // Memorizza il renderer per utilizzi futuri
      setMapRenderer(renderer);
    }
    
    initRenderer();
  }
  
  // Cleanup
  return () => {
    if (mapRenderer) {
      mapRenderer.destroy();
    }
  };
}, [pixiApp, mapData]);
```

## Ottimizzazioni Implementate

### 1. Texture Atlas

Tutte le texture dei tile sono organizzate in un unico atlante per minimizzare i cambi di contesto grafico:

```javascript
// Uso dell'atlas
const tileAtlas = new TileAtlas();
await tileAtlas.initialize();
const texture = tileAtlas.getTexture(tileId);
```

### 2. Culling del Viewport

Solo i chunk visibili nel viewport vengono renderizzati:

```javascript
// Il culling viene gestito automaticamente
renderer.updateVisibleChunks();
```

### 3. Batching per Tipo

Gli oggetti dello stesso tipo vengono raggruppati insieme per ottimizzare il rendering:

```javascript
// Gli oggetti vengono raggruppati automaticamente per tipo
renderer.renderObjects();
```

### 4. Caching degli Elementi Statici

Gli elementi statici della mappa vengono renderizzati una sola volta in una RenderTexture:

```javascript
// Invalidazione manuale della cache quando necessario
cachedRenderer.invalidateCache();

// Aggiorna un tile e rigenera la cache
cachedRenderer.updateTile(x, y, newTileId);
```

## Considerazioni sulle Prestazioni

- **WebGL vs Canvas**: Il sistema è ottimizzato per WebGL, ma include fallback per Canvas.
- **Memoria vs CPU**: L'uso delle cache può aumentare il consumo di memoria, ma riduce il carico CPU.
- **Dispositivi Mobili**: Su dispositivi a basse prestazioni, il sistema abilita automaticamente più ottimizzazioni.

## Estensioni Future

- Supporto per mappe multi-layer con parallasse
- Implementazione di shader personalizzati per effetti visivi
- Integrazione con un editor di mappe visuale
- Supporto per mappe vettoriali per scalabilità infinita

## Riferimenti

- [Pixi.js Performance Tips](https://pixijs.com/8.x/guides/production/performance-tips)
- [Documentazione Pixi.js](https://pixijs.io/guides) 