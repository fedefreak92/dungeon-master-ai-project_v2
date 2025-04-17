# Modulo Mercato

Questo modulo implementa lo stato del mercato all'interno del gioco RPG. È stato progettato con un'architettura modulare per migliorare la manutenibilità e la scalabilità del codice.

## Struttura del modulo

Il modulo è organizzato in diversi file, ciascuno con una responsabilità specifica:

- **mercato_state.py** - Classe principale che integra tutti gli altri componenti
- **oggetti_interattivi.py** - Definizione degli oggetti interattivi presenti nel mercato
- **menu_handlers.py** - Gestione dei menu e delle opzioni di interazione
- **ui_handlers.py** - Gestione degli eventi dell'interfaccia utente
- **movimento.py** - Gestione del movimento del giocatore all'interno del mercato
- **dialogo.py** - Gestione delle conversazioni con gli NPC del mercato

## Utilizzo

Per utilizzare lo stato del mercato nel gioco, importare la classe `MercatoState` dal modulo:

```python
from states.mercato import MercatoState

# Crea un'istanza dello stato mercato
mercato_state = MercatoState(gioco)

# Aggiungi lo stato allo stack degli stati del gioco
gioco.push_stato(mercato_state)
```

## Interazioni disponibili

Nel mercato il giocatore può:

- Comprare pozioni e oggetti
- Vendere oggetti dal proprio inventario
- Parlare con vari NPC (Araldo, Violetta, Gundren)
- Esplorare e interagire con oggetti (bancarella, baule, statua antica, ecc.)
- Visualizzare la mappa del mercato
- Navigare tra diverse aree del mercato

## Estensione

Per aggiungere nuovi elementi al mercato:

### Nuovi oggetti interattivi

Modificare `oggetti_interattivi.py` aggiungendo nuove funzioni per creare oggetti:

```python
def crea_nuovo_oggetto():
    """Crea un nuovo oggetto interattivo."""
    nuovo_oggetto = OggettoInterattivo("Nome", "Descrizione", "stato_iniziale", posizione="mercato")
    # Configurare l'oggetto...
    return nuovo_oggetto
```

Poi aggiungere l'oggetto alla funzione `crea_tutti_oggetti_interattivi()`.

### Nuovi NPC

Modificare la classe `MercatoState` in `mercato_state.py` per aggiungere nuovi NPC:

```python
self.npg_presenti["NuovoNPC"] = NPG("NuovoNPC")
```

E aggiungere i dialoghi corrispondenti in `dialogo.py` nel metodo `_inizializza_dialoghi()`.

### Nuovi menu

Aggiungere nuovi menu nel file `menu_handlers.py` creando nuovi metodi nella classe `MenuMercatoHandler`. 