# Modulo states.base

Questo modulo contiene le classi base su cui si costruiscono tutti gli stati del gioco. È stato suddiviso in più file per migliorare la manutenibilità e la scalabilità del codice.

## Struttura

- **base_state.py** - Contiene la classe `BaseState`, che è la classe base per tutti gli stati del gioco.
- **base_game_state.py** - Contiene la classe `BaseGameState`, che estende `BaseState` aggiungendo gestione dei comandi e interfaccia utente.
- **ui.py** - Contiene la classe `BaseUI` con funzionalità di visualizzazione e rendering dell'interfaccia utente.
- **interazioni.py** - Contiene la classe `BaseInterazioni` con metodi per gestire le interazioni con oggetti e NPC sulla mappa.
- **serializzazione.py** - Contiene la classe `BaseSerializzazione` con metodi per convertire gli stati in dizionari e viceversa.

## Utilizzo

Le classi `BaseState` e `BaseGameState` vengono ereditate dalle classi figlie negli altri moduli di stati:

```python
# Esempio di stato che eredita da BaseState
from states.base import BaseState

class MioStato(BaseState):
    def __init__(self):
        super().__init__()
        # Inizializzazione specifica
        
    def esegui(self, gioco=None):
        # Implementazione del metodo esegui
        pass
```

```python
# Esempio di stato che eredita da BaseGameState
from states.base import BaseGameState

class MioStatoGioco(BaseGameState):
    def __init__(self, gioco=None):
        super().__init__(gioco)
        # Inizializzazione specifica
        
    def _init_commands(self):
        # Definizione dei comandi disponibili
        self.commands["comando"] = self.comando_handler
        
    def comando_handler(self, args):
        # Gestione del comando
        pass
```

## Note di implementazione

- Le classi di base sono organizzate per separare le responsabilità: gestione dello stato, interfaccia utente, interazioni e serializzazione.
- Le classi utilizzano metodi statici ove possibile per facilitare l'uso e la manutenzione.
- La serializzazione gestisce automaticamente vari tipi di attributi per una facile persistenza degli stati. 