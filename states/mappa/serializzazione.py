"""
Funzioni di serializzazione e deserializzazione per lo stato mappa.
Contiene le funzioni per convertire lo stato in formato JSON e viceversa.
"""

def to_dict(mappa_state):
    """
    Converte lo stato in un dizionario per la serializzazione.
    
    Args:
        mappa_state: Istanza di MappaState
        
    Returns:
        dict: Rappresentazione dello stato in formato dizionario
    """
    # Ottieni il dizionario base
    data = mappa_state.get_base_dict()
    
    # Aggiungi attributi specifici
    data.update({
        "mostra_leggenda": mappa_state.mostra_leggenda,
        "menu_attivo": mappa_state.menu_attivo,
        "ui_aggiornata": mappa_state.ui_aggiornata,
        "ultima_scelta": mappa_state.ultima_scelta
    })
    
    # Salva lo stato di origine se presente
    if mappa_state.stato_origine and hasattr(mappa_state.stato_origine, "__class__"):
        data["stato_origine_tipo"] = mappa_state.stato_origine.__class__.__name__
    
    return data

def from_dict(cls, data, game=None):
    """
    Crea un'istanza di MappaState da un dizionario.
    
    Args:
        cls: Classe MappaState
        data (dict): Dizionario con i dati dello stato
        game: Istanza del gioco (opzionale)
        
    Returns:
        MappaState: Nuova istanza dello stato
    """
    state = cls()
    
    # Ripristina attributi
    state.mostra_leggenda = data.get("mostra_leggenda", True)
    state.menu_attivo = data.get("menu_attivo", None)
    state.ui_aggiornata = data.get("ui_aggiornata", False)
    state.ultima_scelta = data.get("ultima_scelta", None)
    
    # Inizializza con il contesto di gioco se fornito
    if game:
        state.set_game_context(game)
    
    # Nota: stato_origine verrà gestito dopo il caricamento completo
    # dello stack degli stati, in quanto potrebbe richiedere riferimenti circolari
    
    return state 