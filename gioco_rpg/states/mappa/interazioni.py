"""
Gestione delle interazioni con l'ambiente sulla mappa.
Contiene le funzioni per interagire con oggetti, NPC e aree del gioco.
"""

def interagisci_con_oggetto(mappa_state, gioco):
    """
    Interagisce con un oggetto adiacente
    
    Args:
        mappa_state: Istanza di MappaState
        gioco: Oggetto Game
    """
    if gioco.giocatore.interagisci_con_oggetto_adiacente(gioco.gestore_mappe, gioco):
        pass  # L'interazione è già gestita nel metodo
    else:
        gioco.io.mostra_messaggio("Non ci sono oggetti con cui interagire nelle vicinanze.")

def interagisci_con_npg(mappa_state, gioco):
    """
    Interagisce con un NPC adiacente
    
    Args:
        mappa_state: Istanza di MappaState
        gioco: Oggetto Game
    """
    if gioco.giocatore.interagisci_con_npg_adiacente(gioco.gestore_mappe, gioco):
        pass  # L'interazione è già gestita nel metodo
    else:
        gioco.io.mostra_messaggio("Non ci sono personaggi con cui parlare nelle vicinanze.")

def esamina_area(mappa_state, gioco):
    """
    Esamina l'area per trovare oggetti o personaggi
    
    Args:
        mappa_state: Istanza di MappaState
        gioco: Oggetto Game
    """
    gioco.io.mostra_messaggio("Esamini attentamente l'area circostante...")
    
    # Si potrebbe implementare una meccanica di scoperta di oggetti nascosti qui
    oggetti_vicini = gioco.giocatore.ottieni_oggetti_vicini(gioco.gestore_mappe, 2)
    npg_vicini = gioco.giocatore.ottieni_npg_vicini(gioco.gestore_mappe, 2)
    
    if oggetti_vicini or npg_vicini:
        gioco.io.mostra_messaggio("Noti alcune cose interessanti:")
        
        if oggetti_vicini:
            gioco.io.mostra_messaggio("\nOggetti:")
            for pos, obj in oggetti_vicini.items():
                x, y = pos
                gioco.io.mostra_messaggio(f"- {obj.nome} a ({x}, {y}) da te")
        
        if npg_vicini:
            gioco.io.mostra_messaggio("\nPersonaggi:")
            for pos, npg in npg_vicini.items():
                x, y = pos
                gioco.io.mostra_messaggio(f"- {npg.nome} a ({x}, {y}) da te")
    else:
        gioco.io.mostra_messaggio("Non noti nulla di particolare.")

def torna_indietro(mappa_state, gioco):
    """
    Torna allo stato precedente
    
    Args:
        mappa_state: Istanza di MappaState
        gioco: Oggetto Game
    """
    if gioco.stato_corrente() == mappa_state:
        gioco.pop_stato()
        
def gestisci_interazione_oggetto(mappa_state, gioco, oggetto_id, azione):
    """
    Gestisce interazioni specifiche con oggetti
    
    Args:
        mappa_state: Istanza di MappaState
        gioco: Oggetto Game
        oggetto_id: ID dell'oggetto
        azione: Tipo di azione (esamina, raccogli, usa)
    """
    if azione == "esamina":
        gioco.io.mostra_messaggio(f"Stai esaminando l'oggetto {oggetto_id}...")
    elif azione == "raccogli":
        gioco.io.mostra_messaggio(f"Hai raccolto l'oggetto {oggetto_id}!")
        # Implementa la logica per raccogliere l'oggetto
    elif azione == "usa":
        gioco.io.mostra_messaggio(f"Stai usando l'oggetto {oggetto_id}...")
        
def gestisci_interazione_npg(mappa_state, gioco, npg_id, azione):
    """
    Gestisce interazioni specifiche con NPC
    
    Args:
        mappa_state: Istanza di MappaState
        gioco: Oggetto Game
        npg_id: ID del personaggio
        azione: Tipo di azione (parla, commercia)
    """
    if azione == "parla":
        gioco.io.mostra_messaggio(f"Stai parlando con {npg_id}...")
    elif azione == "commercia":
        gioco.io.mostra_messaggio(f"Stai commerciando con {npg_id}...") 