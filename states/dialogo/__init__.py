from states.dialogo.dialogo_state import DialogoState
import core.events as Events

# Esponiamo la classe principale e gli eventi rilevanti per mantenere la retrocompatibilità
__all__ = [
    'DialogoState',
    # Aggiungi eventuali altre classi o funzioni utili
]

# Constants per facilitare l'uso di eventi specifici del dialogo
DIALOG_EVENTS = {
    'OPEN': Events.UI_DIALOG_OPEN,
    'CLOSE': Events.UI_DIALOG_CLOSE,
    'CHOICE': Events.DIALOG_CHOICE,
    'MENU_SELECTION': Events.MENU_SELECTION
} 