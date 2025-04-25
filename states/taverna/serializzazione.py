"""
Funzioni di serializzazione e deserializzazione per lo stato Taverna.
Questo modulo implementa funzioni che permettono di convertire lo stato Taverna
in un formato serializzabile e viceversa.
"""

def to_dict(stato):
    """
    Converte lo stato Taverna in un dizionario per la serializzazione.
    
    Args:
        stato: L'istanza dello stato Taverna
        
    Returns:
        dict: Rappresentazione serializzabile dello stato
    """
    # Crea un dizionario base
    data = {
        "nome_stato": getattr(stato, "nome_stato", "taverna"),
        "fase": getattr(stato, "fase", "menu_principale"),
        "prima_visita": getattr(stato, "prima_visita", False),
        "ultima_scelta": getattr(stato, "ultima_scelta", None),
        "ultimo_input": getattr(stato, "ultimo_input", None),
        "menu_attivo": getattr(stato, "menu_attivo", "menu_principale"),
    }
    
    # Serializza gli NPG
    npg_dict = {}
    try:
        for nome, npg in stato.npg_presenti.items():
            if hasattr(npg, 'to_dict') and callable(getattr(npg, 'to_dict')):
                npg_dict[nome] = npg.to_dict()
            else:
                npg_dict[nome] = {"nome": nome}
    except (AttributeError, TypeError):
        # In caso di errore, salviamo solo i nomi degli NPG
        npg_dict = {}
    
    # Aggiungi i nomi degli NPG (utile per la deserializzazione)
    data["npg_nomi"] = list(npg_dict.keys())
    
    # Aggiungi info sugli NPG attivi
    data["nome_npg_attivo"] = getattr(stato, "nome_npg_attivo", None)
    data["stato_conversazione"] = getattr(stato, "stato_conversazione", "inizio")
    
    return data

def from_dict(cls, data, game=None):
    """
    Crea un'istanza di stato Taverna da un dizionario.
    
    Args:
        cls: La classe TavernaState
        data (dict): Dizionario con i dati serializzati
        game: L'istanza del gioco (opzionale)
        
    Returns:
        TavernaState: Una nuova istanza dello stato Taverna
    """
    # Crea una nuova istanza
    state = cls(game)
    
    # Imposta gli attributi base
    state.nome_stato = data.get("nome_stato", "taverna")
    state.fase = data.get("fase", "menu_principale")
    state.prima_visita = data.get("prima_visita", False)
    state.ultima_scelta = data.get("ultima_scelta")
    state.ultimo_input = data.get("ultimo_input")
    state.menu_attivo = data.get("menu_attivo", "menu_principale")
    state.nome_npg_attivo = data.get("nome_npg_attivo")
    state.stato_conversazione = data.get("stato_conversazione", "inizio")
    
    # Ricrea gli NPG
    npg_nomi = data.get("npg_nomi", ["Durnan", "Elminster", "Mirt"])
    state.npg_presenti = {}
    
    try:
        from entities.npg import NPG
        for nome in npg_nomi:
            state.npg_presenti[nome] = NPG(nome)
    except ImportError:
        # Gestisce l'errore se NPG non può essere importato
        state.npg_presenti = {nome: object() for nome in npg_nomi}
    
    # Inizializza gli oggetti interattivi
    try:
        from .oggetti_interattivi import inizializza_oggetti_taverna
        state.oggetti_interattivi = inizializza_oggetti_taverna()
    except ImportError:
        # Gestisce l'errore se non può inizializzare gli oggetti
        state.oggetti_interattivi = {}
    
    return state 