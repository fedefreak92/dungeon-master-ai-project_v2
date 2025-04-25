"""
Modulo per la serializzazione e deserializzazione dello stato di dialogo
"""
import core.events as Events

def to_dict(self):
    """
    Converte lo stato del dialogo in un dizionario per la serializzazione.
    
    Returns:
        dict: Rappresentazione dello stato in formato dizionario
    """
    # Ottieni il dizionario base
    data = super().to_dict()
    
    # Aggiungi attributi specifici
    data.update({
        "stato_corrente": self.stato_corrente,
        "stato_ritorno": self.stato_ritorno,
        "dati_contestuali": self.dati_contestuali,
        "fase": self.fase,
        "ui_aggiornata": self.ui_aggiornata
    })
    
    # Salva le informazioni sul NPG
    if self.npg:
        if hasattr(self.npg, 'to_dict'):
            data["npg"] = self.npg.to_dict()
        else:
            data["npg"] = {"nome": self.npg.nome}
    
    # Emetti evento di serializzazione
    self.emit_event(Events.STATE_PAUSED, 
                   state_type="dialogo",
                   state_data=data)
    
    return data

def from_dict(cls, data, game=None):
    """
    Crea un'istanza di DialogoState da un dizionario.
    
    Args:
        data (dict): Dizionario con i dati dello stato
        game: L'istanza del gioco (opzionale)
        
    Returns:
        DialogoState: Nuova istanza di DialogoState
    """
    # Per creare un dialogo serve un NPG
    from entities.npg import NPG
    
    # Recupera o crea l'NPG
    npg_data = data.get("npg", {})
    if isinstance(npg_data, dict):
        if hasattr(NPG, 'from_dict'):
            npg = NPG.from_dict(npg_data)
        else:
            npg = NPG(npg_data.get("nome", "NPC Sconosciuto"))
    else:
        npg = NPG("NPC Sconosciuto")
        
    # Crea lo stato con l'NPG
    state = cls(npg, stato_ritorno=data.get("stato_ritorno"), gioco=game)
    
    # Ripristina attributi
    state.dati_contestuali = data.get("dati_contestuali", {})
    state.stato_corrente = data.get("stato_corrente", "inizio")
    state.fase = data.get("fase", "conversazione")
    state.ui_aggiornata = data.get("ui_aggiornata", False)
    
    # Emetti evento di deserializzazione se il contesto di gioco è disponibile
    if game and hasattr(state, 'event_bus'):
        state.emit_event(Events.STATE_RESUMED, 
                        state_type="dialogo",
                        state_id=id(state))
    
    return state 