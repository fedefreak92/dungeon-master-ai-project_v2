"""
Gestori degli eventi UI per lo stato mappa.
Contiene le funzioni per gestire i click, i keypresses e le azioni dei menu.
"""

from states.mappa import movimento, interazioni, ui

def handle_dialog_choice(mappa_state, event):
    """
    Handler per le scelte dai dialoghi
    
    Args:
        mappa_state: Istanza di MappaState
        event: Evento di scelta da dialogo
    """
    if not hasattr(event, "data") or not event.data:
        return
    
    choice = event.data.get("choice")
    if not choice:
        return
        
    game_ctx = mappa_state.gioco
    if not game_ctx:
        return
        
    if mappa_state.menu_attivo == "principale":
        if choice == "Muoviti":
            ui.mostra_opzioni_movimento(mappa_state, game_ctx)
            mappa_state.menu_attivo = "movimento"
        elif choice == "Interagisci con l'ambiente":
            ui.mostra_opzioni_interazione(mappa_state, game_ctx)
            mappa_state.menu_attivo = "interazione"
        elif choice == "Mostra elementi nelle vicinanze":
            ui.mostra_elementi_vicini(mappa_state, game_ctx)
            mappa_state.menu_attivo = None  # Ritorna al menu principale dopo
        elif choice == "Mostra/nascondi leggenda":
            ui.toggle_leggenda(mappa_state, game_ctx)
            mappa_state.menu_attivo = None  # Ritorna al menu principale dopo
        elif choice == "Torna indietro":
            if game_ctx.stato_corrente() == mappa_state:
                game_ctx.pop_stato()
    elif mappa_state.menu_attivo == "movimento":
        # Gestione direzioni per il movimento
        if choice in ["Nord", "Sud", "Est", "Ovest"]:
            movimento.sposta_giocatore(mappa_state, game_ctx, choice.lower())
            mappa_state.menu_attivo = None  # Ritorna al menu principale dopo
        elif choice == "Indietro":
            mappa_state.menu_attivo = "principale"
            ui.mostra_menu_principale(mappa_state, game_ctx)
    elif mappa_state.menu_attivo == "interazione":
        # Gestione opzioni di interazione
        if choice == "Interagisci con un oggetto":
            interazioni.interagisci_con_oggetto(mappa_state, game_ctx)
            mappa_state.menu_attivo = None  # Ritorna al menu principale dopo
        elif choice == "Parla con un personaggio":
            interazioni.interagisci_con_npg(mappa_state, game_ctx)
            mappa_state.menu_attivo = None  # Ritorna al menu principale dopo
        elif choice == "Esamina l'area":
            interazioni.esamina_area(mappa_state, game_ctx)
            mappa_state.menu_attivo = None  # Ritorna al menu principale dopo
        elif choice == "Indietro":
            mappa_state.menu_attivo = "principale"
            ui.mostra_menu_principale(mappa_state, game_ctx)

def handle_keypress(mappa_state, event):
    """
    Handler per i tasti premuti
    
    Args:
        mappa_state: Istanza di MappaState
        event: Evento di pressione tasto
    """
    if not hasattr(event, "data") or not event.data:
        return
        
    key = event.data.get("key")
    if not key:
        return
        
    game_ctx = mappa_state.gioco
    if not game_ctx:
        return
        
    # Mappatura tasti freccia a direzioni
    if key == "ArrowUp":
        movimento.sposta_giocatore(mappa_state, game_ctx, "nord")
    elif key == "ArrowDown":
        movimento.sposta_giocatore(mappa_state, game_ctx, "sud")
    elif key == "ArrowRight":
        movimento.sposta_giocatore(mappa_state, game_ctx, "est")
    elif key == "ArrowLeft":
        movimento.sposta_giocatore(mappa_state, game_ctx, "ovest")
    elif key == "Escape":
        # Chiudi menu o dialoghi aperti
        # In caso non ce ne siano, torna indietro
        if game_ctx.stato_corrente() == mappa_state:
            game_ctx.pop_stato()

def handle_click_event(mappa_state, event):
    """
    Handler per gli eventi di click sulla mappa
    
    Args:
        mappa_state: Istanza di MappaState
        event: Evento di click
    """
    if not hasattr(event, "data") or not event.data:
        return
    
    target = event.data.get("target")
    if not target:
        return
        
    game_ctx = mappa_state.gioco
    if not game_ctx:
        return
        
    # Gestione click su elementi della mappa
    if target.startswith("oggetto_"):
        obj_id = target.replace("oggetto_", "")
        interazioni.interagisci_con_oggetto(mappa_state, game_ctx)
    elif target.startswith("npg_"):
        npg_id = target.replace("npg_", "")
        interazioni.interagisci_con_npg(mappa_state, game_ctx)
    elif target.startswith("cella_"):
        # Formato atteso: cella_x_y
        coord = target.replace("cella_", "").split("_")
        if len(coord) == 2 and coord[0].isdigit() and coord[1].isdigit():
            x, y = int(coord[0]), int(coord[1])
            movimento.gestisci_click_cella(mappa_state, game_ctx, x, y)

def handle_menu_action(mappa_state, event):
    """
    Handler per azioni menu contestuale
    
    Args:
        mappa_state: Istanza di MappaState
        event: Evento menu
    """
    if not hasattr(event, "data") or not event.data:
        return
    
    action = event.data.get("action")
    target_id = event.data.get("target_id")
    if not action:
        return
        
    game_ctx = mappa_state.gioco
    if not game_ctx:
        return
        
    # Gestione azioni menu contestuale per oggetti
    if action == "Esamina" and target_id and target_id.startswith("oggetto_"):
        obj_id = target_id.replace("oggetto_", "")
        interazioni.gestisci_interazione_oggetto(mappa_state, game_ctx, obj_id, "esamina")
    elif action == "Raccogli" and target_id and target_id.startswith("oggetto_"):
        obj_id = target_id.replace("oggetto_", "")
        interazioni.gestisci_interazione_oggetto(mappa_state, game_ctx, obj_id, "raccogli") 
    elif action == "Usa" and target_id and target_id.startswith("oggetto_"):
        obj_id = target_id.replace("oggetto_", "")
        interazioni.gestisci_interazione_oggetto(mappa_state, game_ctx, obj_id, "usa")
    
    # Gestione azioni menu contestuale per NPC
    elif action == "Parla" and target_id and target_id.startswith("npg_"):
        npg_id = target_id.replace("npg_", "")
        interazioni.gestisci_interazione_npg(mappa_state, game_ctx, npg_id, "parla")
    elif action == "Commercia" and target_id and target_id.startswith("npg_"):
        npg_id = target_id.replace("npg_", "")
        interazioni.gestisci_interazione_npg(mappa_state, game_ctx, npg_id, "commercia") 