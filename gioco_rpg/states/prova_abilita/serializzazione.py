"""
Funzionalità di serializzazione per lo stato di prova abilità.
"""
from states.base.enhanced_base_state import EnhancedBaseState

def to_dict(state):
    """
    Converte lo stato in un dizionario per la serializzazione.
    
    Args:
        state: Istanza dello stato ProvaAbilitaState
        
    Returns:
        dict: Rappresentazione dello stato in formato dizionario
    """
    # Ottieni il dizionario base usando il metodo della classe base
    # Evita l'uso di super() che può causare problemi quando chiamato indirettamente
    data = EnhancedBaseState.to_dict(state)
    
    # Aggiungi attributi specifici
    data.update({
        "fase": state.fase,
        "ultimo_input": state.ultimo_input,
        "abilita_scelta": state.abilita_scelta,
        "menu_attivo": state.menu_attivo,
        "ui_aggiornata": state.ui_aggiornata
    })
    
    # Gestione di contesto e dati_contestuali
    # Filtra solo i dati serializzabili
    contesto_serializzabile = {}
    for k, v in state.contesto.items():
        if isinstance(v, (str, int, float, bool, list, dict, tuple, type(None))):
            contesto_serializzabile[k] = v
        elif hasattr(v, 'to_dict') and callable(getattr(v, 'to_dict')):
            contesto_serializzabile[k] = v.to_dict()
    
    dati_contestuali_serializzabili = {}
    for k, v in state.dati_contestuali.items():
        if isinstance(v, (str, int, float, bool, list, dict, tuple, type(None))):
            dati_contestuali_serializzabili[k] = v
        elif hasattr(v, 'to_dict') and callable(getattr(v, 'to_dict')):
            dati_contestuali_serializzabili[k] = v.to_dict()
            
    data["contesto"] = contesto_serializzabile
    data["dati_contestuali"] = dati_contestuali_serializzabili
    
    return data

def from_dict(cls, data, game=None):
    """
    Crea un'istanza di ProvaAbilitaState da un dizionario.
    
    Args:
        cls: Classe ProvaAbilitaState
        data (dict): Dizionario con i dati dello stato
        game: Istanza del gioco (opzionale)
        
    Returns:
        ProvaAbilitaState: Nuova istanza dello stato
    """
    contesto = data.get("contesto", {})
    state = cls(contesto)
    
    # Ripristina attributi
    state.fase = data.get("fase", "scegli_abilita")
    state.ultimo_input = data.get("ultimo_input")
    state.abilita_scelta = data.get("abilita_scelta")
    state.dati_contestuali = data.get("dati_contestuali", {})
    state.menu_attivo = data.get("menu_attivo")
    state.ui_aggiornata = data.get("ui_aggiornata", False)
    
    # Se è fornito un contesto di gioco, salvalo
    if game:
        state.set_game_context(game)
    
    return state 