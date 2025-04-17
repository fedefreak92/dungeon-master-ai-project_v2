"""
Gestione del movimento del giocatore sulla mappa.
Contiene le funzioni per spostare il giocatore e gestire i cambi di mappa.
"""

def sposta_giocatore(mappa_state, gioco, direzione):
    """
    Sposta il giocatore nella direzione specificata
    
    Args:
        mappa_state: Istanza di MappaState
        gioco: Oggetto Game
        direzione: Stringa con la direzione (nord, sud, est, ovest)
    """
    # Ottieni la mappa corrente
    mappa_corrente = gioco.gestore_mappe.ottieni_mappa_attuale()
    if not mappa_corrente:
        gioco.io.messaggio_errore("Errore: mappa non disponibile.")
        return
        
    # Ottieni la posizione attuale
    x, y = gioco.giocatore.x, gioco.giocatore.y
    
    # Memorizza la mappa di origine prima del movimento
    mappa_origine = gioco.giocatore.mappa_corrente
    
    # Esegui il movimento
    movimento_riuscito = gioco.muovi_giocatore(direzione)
    
    if movimento_riuscito:
        # Aggiorna la visualizzazione dopo il movimento
        mappa_state.ui_aggiornata = False
        mappa_state.aggiorna_renderer(gioco)
        
        # Controlla se il movimento ha causato un cambio mappa
        if mappa_origine != gioco.giocatore.mappa_corrente:
            gestisci_cambio_mappa(mappa_state, gioco, mappa_origine, gioco.giocatore.mappa_corrente)
    else:
        gioco.io.messaggio_errore(f"Non puoi muoverti in quella direzione.")

def gestisci_cambio_mappa(mappa_state, gioco, mappa_origine, mappa_destinazione):
    """
    Gestisce il cambio di stato in base al cambio di mappa
    
    Args:
        mappa_state: Istanza di MappaState
        gioco: Oggetto Game
        mappa_origine: Nome della mappa di origine
        mappa_destinazione: Nome della mappa di destinazione
    """
    # Se il cambio mappa implica il cambio di stato
    if (mappa_state.stato_origine is not None and 
        hasattr(mappa_state.stato_origine, '__class__') and
        mappa_state.stato_origine.__class__.__name__ == "TavernaState" and 
        mappa_destinazione == "mercato"):
        
        # Chiedi se continuare a esplorare la nuova mappa tramite dialogo UI
        gioco.io.mostra_dialogo("Cambio Mappa", 
                                "Vuoi continuare a esplorare la mappa?", 
                                ["Sì", "No"])
        
        # La gestione della risposta avverrà in _handle_dialog_choice
        mappa_state.attesa_risposta_mappa = {
            "origine": mappa_origine,
            "destinazione": mappa_destinazione,
            "tipo": "taverna_to_mercato"
        }
            
    elif (mappa_state.stato_origine is not None and 
          hasattr(mappa_state.stato_origine, '__class__') and 
          mappa_state.stato_origine.__class__.__name__ == "MercatoState" and 
          mappa_destinazione == "taverna"):
          
        # Chiedi se continuare a esplorare la nuova mappa tramite dialogo UI
        gioco.io.mostra_dialogo("Cambio Mappa", 
                               "Vuoi continuare a esplorare la mappa?", 
                               ["Sì", "No"])
        
        # La gestione della risposta avverrà in _handle_dialog_choice
        mappa_state.attesa_risposta_mappa = {
            "origine": mappa_origine,
            "destinazione": mappa_destinazione,
            "tipo": "mercato_to_taverna"
        }

def gestisci_click_cella(mappa_state, gioco, x, y):
    """
    Gestisce il click su una cella della mappa
    
    Args:
        mappa_state: Istanza di MappaState
        gioco: Oggetto Game
        x: Coordinata X
        y: Coordinata Y
    """
    # Calcola la differenza rispetto alla posizione del giocatore
    dx = x - gioco.giocatore.x
    dy = y - gioco.giocatore.y
    
    # Se è una cella adiacente, prova a muovere il giocatore
    if abs(dx) + abs(dy) == 1:  # Distanza Manhattan = 1
        if dx == 1 and dy == 0:
            sposta_giocatore(mappa_state, gioco, "est")
        elif dx == -1 and dy == 0:
            sposta_giocatore(mappa_state, gioco, "ovest")
        elif dx == 0 and dy == 1:
            sposta_giocatore(mappa_state, gioco, "sud")
        elif dx == 0 and dy == -1:
            sposta_giocatore(mappa_state, gioco, "nord")
    else:
        gioco.io.mostra_messaggio("Non puoi muoverti direttamente in quella posizione.") 