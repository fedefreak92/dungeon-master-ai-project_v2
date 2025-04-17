# Modulo Mappa

Questo modulo contiene l'implementazione dello stato mappa del gioco RPG.

## Struttura del Modulo

Il modulo è diviso in diversi file per migliorare la manutenibilità e seguire una struttura più modulare:

- **mappa_state.py** - Classe principale che coordina tutte le funzionalità
- **ui.py** - Gestione dell'interfaccia utente e della visualizzazione
- **movimento.py** - Logica per il movimento del giocatore sulla mappa
- **interazioni.py** - Gestione delle interazioni con oggetti, NPC e ambiente
- **ui_handlers.py** - Gestori per gli eventi UI (click, keypress, menu)
- **serializzazione.py** - Funzioni per il salvataggio e caricamento dello stato

## Funzionalità Principali

### Movimento

La classe gestisce il movimento del giocatore nelle quattro direzioni cardinali, sia tramite comandi che con le frecce direzionali. Supporta anche il clic sulle celle adiacenti per muoversi.

### Interazioni

Permette di interagire con:
- Oggetti sulla mappa (esaminare, raccogliere, usare)
- NPC (parlare, commerciare)
- Ambiente circostante (esaminare l'area)

### UI

Fornisce menu interattivi per le diverse azioni e visualizza una leggenda per interpretare gli elementi della mappa.

### Cambio Mappa

Gestisce il passaggio tra diverse mappe, con logica specifica in caso di cambio tra stati specifici (es. taverna -> mercato).

## Struttura Dati

Lo stato mappa memorizza:
- Stato di origine (per tornare indietro)
- Stato dell'UI (leggenda, menu attivo)
- Direzioni di movimento
- Comandi disponibili

## Utilizzo

```python
# Creare un'istanza dello stato mappa
mappa_state = MappaState()

# Eseguire lo stato
gioco.push_stato(mappa_state)
```

## Estensioni Future

- Aggiungere ricerca percorsi avanzata
- Implementare modalità di esplorazione automatica
- Supportare mappe con altitudini diverse 