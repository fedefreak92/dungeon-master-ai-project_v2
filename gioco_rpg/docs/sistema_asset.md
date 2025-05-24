# Sistema di gestione degli asset

Questo documento descrive il sistema standardizzato per la gestione degli asset nel gioco RPG.

## Panoramica

Il sistema di gestione degli asset è responsabile del caricamento, dell'organizzazione e dell'ottimizzazione delle risorse grafiche utilizzate nel gioco, come sprite, tile e interfaccia utente. È stato semplificato per utilizzare esclusivamente JSON per i metadati e WebGL per il rendering tramite Pixi.js.

## Componenti principali

### Backend

1. **AssetManager**: Singleton che gestisce il caricamento e l'organizzazione degli asset.
   - File: `gioco_rpg/util/asset_manager.py`
   - Funzionalità: Registra asset, carica manifest, scansiona directory.

2. **SpriteSheetManager**: Gestisce gli sprite sheet per ottimizzare le richieste HTTP.
   - File: `gioco_rpg/util/sprite_sheet_manager.py`
   - Funzionalità: Combina più sprite in un'unica texture, gestisce metadati degli sprite sheet in formato JSON.

3. **API REST**: Endpoint per l'accesso e la gestione degli asset.
   - File: `gioco_rpg/server/routes/assets_routes.py`
   - Funzionalità: Fornisce informazioni sugli asset, restituisce file degli asset, aggiorna gli asset.

4. **WebSocket**: Notifica ai client gli aggiornamenti degli asset in tempo reale.
   - File: `gioco_rpg/server/websocket/assets.py`
   - Funzionalità: Gestisce la sincronizzazione degli asset, notifica gli aggiornamenti.

### Frontend

1. **AssetLoader**: Classe per caricare le texture degli asset nel frontend.
   - File: `gioco_rpg/frontend/src/pixi/utils/AssetLoader.js`
   - Funzionalità: Carica texture, gestisce la cache delle texture, precarica texture essenziali.

2. **SpriteSheetManager**: Gestisce gli sprite sheet lato frontend.
   - File: `gioco_rpg/frontend/src/pixi/utils/SpriteSheetManager.js`
   - Funzionalità: Carica gli sprite sheet dal server, crea sprite sheet virtuali se necessario.

3. **TextureManager**: Gestisce le texture per il rendering della mappa.
   - File: `gioco_rpg/frontend/src/pixi/utils/TextureManager.js`
   - Funzionalità: Carica texture base, fornisce un'interfaccia per accedere alle texture.

## Flusso di lavoro standard

### Inizializzazione del sistema

1. Il backend inizializza l'`AssetManager` e carica il manifest degli asset.
2. Il backend scansiona le directory per registrare gli asset e crea gli sprite sheet.
3. Il frontend inizializza l'`AssetLoader` quando l'applicazione viene avviata.
4. Il frontend carica gli sprite sheet e le texture essenziali.

### Caricamento degli asset

1. Il frontend richiede i dati degli asset al backend tramite l'API REST o WebSocket.
2. Il backend invia le informazioni sugli asset, inclusi i metadati degli sprite sheet.
3. Il frontend carica gli sprite sheet e le texture da utilizzare nel rendering.

### Aggiornamento degli asset

1. Il backend rileva modifiche nelle directory degli asset.
2. Il backend aggiorna il manifest e comunica le modifiche ai client tramite WebSocket.
3. I client ricevono la notifica e aggiornano automaticamente i loro asset locali.

## Formati e standard

- **Metadati**: Esclusivamente in formato JSON.
- **Sprite sheet**: JSON standard compatibile con Pixi.js.
- **Rendering**: WebGL tramite Pixi.js.
- **Comunicazione**: API REST per operazioni sincrone, WebSocket per notifiche in tempo reale.

## Organizzazione delle directory

```
assets/
  ├── sprites/      # Sprite individuali
  ├── tiles/        # Tile per le mappe
  ├── ui/           # Elementi dell'interfaccia utente
  ├── spritesheets/ # Sprite sheet generati
  ├── animations/   # Dati delle animazioni
  └── tilesets/     # Set di tile per le mappe
```

## Esempi di utilizzo

### Backend: Registrazione di un asset

```python
asset_manager = get_asset_manager()
asset_manager.register_sprite(
    sprite_id="player",
    name="Player",
    file_path="sprites/player.png",
    dimensions=(32, 32)
)
```

### Backend: Creazione di uno sprite sheet

```python
sprite_sheet_manager = get_sprite_sheet_manager()
sprite_sheet_manager.generate_sprite_sheet_from_directory("assets/sprites", "player_sprites")
```

### Frontend: Caricamento di una texture

```javascript
const texture = await AssetLoader.loadTexture("/assets/file/sprites/player.png");
```

### Frontend: Utilizzo di una texture da uno sprite sheet

```javascript
const texture = SpriteSheetManager.getTexture("player_sprites", "idle");
const sprite = new PIXI.Sprite(texture);
```

## Configurazione

Il sistema di asset può essere configurato tramite le seguenti variabili:

- **Backend**: Le directory di base sono configurate negli oggetti singleton `AssetManager` e `SpriteSheetManager`.
- **Frontend**: L'URL di base dell'API è configurato nei moduli `AssetLoader.js` e `SpriteSheetManager.js`.

## Raccomandazioni

1. **Organizzazione**: Mantenere un'organizzazione coerente degli asset nelle rispettive directory.
2. **Nomina**: Utilizzare nomi descrittivi e coerenti per gli asset.
3. **Ottimizzazione**: Utilizzare gli sprite sheet per ridurre le richieste HTTP e migliorare le prestazioni.
4. **Versioning**: Aggiornare regolarmente il manifest degli asset per assicurarsi che i client abbiano le versioni più recenti.
5. **Precaricamento**: Precare gli asset essenziali all'avvio dell'applicazione per evitare ritardi durante il gioco. 