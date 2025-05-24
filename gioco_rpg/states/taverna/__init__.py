"""
Pacchetto per lo stato Taverna.
Implementa le funzionalità della taverna nel gioco RPG,
tra cui interazioni, dialoghi e gestione del menu taverna.
Ora supporta l'architettura EventBus.
"""

# Esporta la classe principale
from .taverna_state import TavernaState

# Esporta i moduli di funzionalità
from . import movimento
from . import oggetti_interattivi
# from . import taverna_menu_handlers # COMMENTATO - Caricato dinamicamente da MappaState
# from . import taverna_ui_handlers   # COMMENTATO - Caricato dinamicamente da MappaState
from . import serializzazione
from . import dialogo
from . import combattimento

# Rendi disponibili le classi principali a livello di pacchetto
__all__ = ['TavernaState', 'serializzazione', 'movimento', 'oggetti_interattivi'] 