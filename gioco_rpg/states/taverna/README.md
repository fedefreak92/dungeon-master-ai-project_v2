# Modulo Taverna

Questo modulo gestisce lo stato della taverna "Il Portale Spalancato" del gioco. La taverna è un hub centrale dove il giocatore può interagire con NPC, accedere a diverse zone, gestire il proprio inventario e combattere.

## Struttura

Il modulo è organizzato in modo modulare secondo il principio di responsabilità singola:

- `taverna_state.py` - Classe principale che gestisce lo stato della taverna
- `ui_handlers.py` - Gestione dell'interfaccia utente e visualizzazione
- `menu_handlers.py` - Gestione dei menu e delle scelte dell'utente
- `dialogo.py` - Gestione dei dialoghi con gli NPC
- `oggetti_interattivi.py` - Gestione degli oggetti interattivi nella taverna
- `movimento.py` - Gestione del movimento nella mappa e interazione con l'ambiente
- `combattimento.py` - Gestione del combattimento con nemici e NPC

## Funzionalità principali

### Gestione stato
- Inizializzazione dello stato della taverna
- Persistenza e serializzazione
- Transizioni ad altri stati di gioco

### Interfaccia utente
- Visualizzazione del benvenuto
- Aggiornamento del renderer
- Gestione delle notifiche e audio

### Menu
- Menu principale con opzioni di interazione
- Salvataggio della partita
- Conferma di uscita dal gioco

### Dialogo
- Selezione degli NPC disponibili
- Avvio delle conversazioni
- Gestione delle risposte

### Oggetti interattivi
- Interazione con oggetti nella taverna (bancone, camino, bauli, ecc.)
- Collezione di oggetti speciali
- Attivazione di meccanismi (leve, porte, ecc.)

### Movimento
- Visualizzazione della mappa
- Movimento del giocatore nella taverna
- Input tramite tastiera

### Combattimento
- Selezione del tipo di nemico
- Selezione di NPC come avversari
- Avvio del combattimento

## Uso

Per utilizzare questo modulo, importare la classe principale:

```python
from states.taverna import TavernaState

# Creazione dello stato taverna
taverna = TavernaState(gioco)

# Passaggio allo stato taverna
gioco.cambia_stato(taverna)
```

## Note implementative

La classe TavernaState utilizza un sistema di fasi (`self.fase`) per tenere traccia dell'attività corrente del giocatore.
I gestori di eventi (`_handle_*`) consentono la navigazione tra le varie fasi in modo non bloccante.
Gli NPC e gli oggetti interattivi vengono inizializzati all'avvio e possono essere modificati durante il gioco. 