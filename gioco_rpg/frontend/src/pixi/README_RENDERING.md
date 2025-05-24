# Sistema di Rendering per RPG a Griglia

Questo documento descrive il sistema di rendering implementato per il gioco RPG, basato su una griglia con immagine di sfondo.

## Panoramica

Il sistema di rendering è stato progettato per essere semplice ed efficiente, perfetto per un gioco RPG a turni basato su griglia. Invece di utilizzare singole texture per ogni tile, il sistema utilizza:

1. **Un'immagine di sfondo per l'intera mappa** - che rappresenta visivamente l'ambiente
2. **Una griglia logica semplificata** - dove 0 = percorribile, 1 = ostacolo
3. **Token 2D** - per rappresentare il giocatore, NPC e oggetti interattivi

## Componenti Principali

Il sistema è composto dai seguenti componenti:

### 1. GridMapRenderer

La classe principale che gestisce il rendering della mappa, implementata in `gioco_rpg/frontend/src/pixi/utils/GridMapRenderer.js`. Responsabilità:

- Caricamento dell'immagine di sfondo
- Disegno della griglia
- Gestione delle entità (giocatore, NPC, oggetti)
- Aggiornamento delle posizioni
- Gestione della camera

### 2. PixiManager

Il singleton che orchestra il sistema di rendering, implementato in `gioco_rpg/frontend/src/pixi/PixiManager.js`. Responsabilità:

- Creazione e gestione delle scene
- Inizializzazione di GridMapRenderer
- Caricamento delle mappe
- Aggiunta/gestione delle entità
- Gestione delle risorse

### 3. MapContainer

Il componente React che interfaccia il sistema di rendering con l'applicazione, implementato in `gioco_rpg/frontend/src/components/MapContainer.jsx`. Responsabilità:

- Caricamento dei dati della mappa dal server
- Inizializzazione della scena Pixi.js
- Gestione degli aggiornamenti delle entità
- Gestione degli eventi di input

## Struttura Dati delle Mappe

Le mappe sono definite in formato JSON con la seguente struttura:

```json
{
  "nome": "taverna",
  "larghezza": 15,
  "altezza": 10,
  "tipo": "interno",
  "descrizione": "Una taverna accogliente con un camino e molti avventori.",
  "backgroundImage": "assets/maps/taverna_background.png",
  "griglia": [
    [0, 0, 0, 0, 0],
    [1, 1, 1, 1, 1]
  ],
  "oggetti": {
    "[3, 2]": {
      "nome": "Baule",
      "tipo": "oggetto_interattivo",
      "sprite": "chest"
    }
  },
  "npg": {
    "[8, 4]": {
      "nome": "Oste",
      "sprite": "npc_merchant"
    }
  },
  "porte": {
    "[12, 5]": ["villaggio", [1, 5]]
  },
  "pos_iniziale_giocatore": [7, 5]
}
```

### Elementi della Mappa

- **`nome`**: Identificatore unico della mappa
- **`larghezza`**, **`altezza`**: Dimensioni della mappa in celle
- **`tipo`**: Categoria della mappa (interno, esterno, dungeon, ecc.)
- **`descrizione`**: Descrizione testuale della mappa
- **`backgroundImage`**: Percorso dell'immagine di sfondo
- **`griglia`**: Matrice 2D che definisce gli ostacoli (0 = percorribile, 1 = ostacolo)
- **`oggetti`**: Dizionario di oggetti interattivi con posizione come chiave
- **`npg`**: Dizionario di NPC con posizione come chiave
- **`porte`**: Collegamenti ad altre mappe
- **`pos_iniziale_giocatore`**: Posizione iniziale del giocatore sulla mappa

## Flusso di Rendering

1. **Caricamento della mappa**:
   - Il componente `MapContainer` richiede i dati della mappa al server
   - I dati JSON vengono validati e normalizzati
   - `PixiManager` inizializza una nuova scena Pixi.js

2. **Inizializzazione del renderer**:
   - `PixiManager` crea un'istanza di `GridMapRenderer`
   - Il renderer inizializza i layer (sfondo, griglia, entità)

3. **Rendering degli elementi**:
   - L'immagine di sfondo viene caricata e posizionata
   - La griglia viene disegnata per aiutare la visualizzazione
   - Gli oggetti e gli NPC vengono posizionati nelle loro celle
   - Il giocatore viene posizionato nella sua cella iniziale

4. **Aggiornamenti di gioco**:
   - Quando il giocatore si muove, `updatePlayerPosition` aggiorna la posizione
   - Quando le entità cambiano, `updateEntities` aggiorna gli NPC e gli oggetti
   - La camera viene centrata sul giocatore

## Gestione delle Risorse

Le risorse grafiche sono organizzate nelle seguenti cartelle:

- **`assets/maps/`**: Contiene le immagini di sfondo delle mappe
- **`assets/entities/`**: Contiene gli sprite del giocatore e degli NPC
- **`assets/objects/`**: Contiene gli sprite degli oggetti interattivi

## Ottimizzazioni

Il sistema è ottimizzato per:

1. **Minimo uso di memoria** - Solo un'immagine di sfondo per mappa invece di tante texture
2. **Rendering efficiente** - Meno sprite da gestire e aggiornare
3. **Velocità di sviluppo** - Più facile creare nuove mappe con una singola immagine

## Estensibilità

Il sistema può essere esteso in diversi modi:

1. **Animazioni** - Aggiungendo supporto per sprite animati per il giocatore e gli NPC
2. **Effetti** - Implementando un sistema di particelle o filtri per effetti visivi
3. **Illuminazione** - Aggiungendo un layer per l'illuminazione dinamica
4. **Audio spaziale** - Integrando effetti sonori basati sulla posizione

## Note per gli Sviluppatori

- Quando crei una nuova mappa, assicurati di fornire un'immagine di sfondo di alta qualità
- La griglia dovrebbe contenere solo valori 0 (percorribile) e 1 (ostacolo)
- Le posizioni di oggetti e NPC sono nel formato "[x, y]" con coordinate basate sulla griglia
- Ogni oggetto e NPC dovrebbe avere un nome e un tipo appropriato 