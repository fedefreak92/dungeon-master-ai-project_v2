def visualizza_mappa(stato, gioco):
    """Visualizza la mappa della taverna con effetti di transizione"""
    from states.mappa import MappaState
    
    # Effetto audio per l'apertura della mappa
    gioco.io.play_sound({
        "sound_id": "map_open",
        "volume": 0.6
    })
    
    # Opzioni di transizione
    parametri_transizione = {}
    
    # Se c'è già un'istanza del map state, la usiamo
    map_state = next((s for s in gioco.stato_stack if isinstance(s, MappaState)), None)
    if map_state:
        # Esegui la transizione verso lo stato mappa
        stato._esegui_transizione(
            gioco=gioco,
            stato_destinazione=map_state,
            parametri=parametri_transizione,
            tipo_transizione="fade",
            durata=0.3
        )
    else:
        # Crea un nuovo stato mappa e esegui la transizione
        nuovo_map_state = MappaState(stato_origine=stato)
        stato._esegui_transizione(
            gioco=gioco,
            stato_destinazione=nuovo_map_state,
            parametri=parametri_transizione,
            tipo_transizione="fade",
            durata=0.3
        )
    
    # Torna al menu principale
    stato.fase = "menu_principale"
    
    # Aggiorna lo stato dell'UI
    stato.menu_attivo = "mappa_aperta"
    stato.elementi_attivi = ["mappa"]
    stato.ui_aggiornata = False

def gestisci_movimento(stato, gioco):
    """Permette al giocatore di muoversi sulla mappa utilizzando l'interfaccia grafica"""
    from states.mappa import MappaState
    
    # Effetto audio per attivazione modalità movimento
    gioco.io.play_sound({
        "sound_id": "movement_mode",
        "volume": 0.5
    })
    
    # Mostra istruzioni movimento
    gioco.io.mostra_ui_elemento({
        "type": "text",
        "id": "istruzioni_movimento",
        "text": "Usa i tasti freccia o WASD per muoverti. ESC per tornare al menu.",
        "x": 400,
        "y": 50,
        "font_size": 16,
        "color": "#FFFFFF",
        "background": "#000000AA",
        "padding": 10,
        "z_index": 10
    })
    
    # Se c'è già un'istanza del map state, la usiamo
    map_state = next((s for s in gioco.stato_stack if isinstance(s, MappaState)), None)
    if map_state:
        # Attiva la modalità movimento nella mappa
        map_state.attiva_movimento(gioco)
        
        # Mostra indicatore posizione giocatore
        giocatore_x, giocatore_y = gioco.giocatore.x, gioco.giocatore.y
        gioco.io.mostra_ui_elemento({
            "type": "sprite",
            "id": "player_marker",
            "image": "player_avatar",
            "x": giocatore_x * 32 + 16,  # Posizione centrata sulla cella
            "y": giocatore_y * 32 + 16,
            "scale": 1.0,
            "z_index": 5
        })
        
        # Abilita handler per tasti di movimento
        gioco.io.registra_handler_input("keydown", lambda event: handle_keypress(event, stato))
    else:
        # Se non c'è un'istanza di mappa, crea una nuova
        map_state = MappaState(stato_origine=stato)
        
        # Effetto di transizione
        gioco.io.mostra_transizione("fade", 0.3)
        
        # Passa al nuovo stato
        gioco.push_stato(map_state)
        
        # Attiva la modalità movimento nella mappa
        map_state.attiva_movimento(gioco)
    
    # Imposta la fase
    stato.fase = "muovi_mappa"
    
    # Aggiorna stato UI
    stato.menu_attivo = "movimento"
    stato.ui_aggiornata = False
    
def handle_keypress(event, stato):
    """Gestisce gli input da tastiera per il movimento del giocatore"""
    gioco = stato.gioco
    if not hasattr(event, "data") or not event.data:
        return
        
    key = event.data.get("key", "").lower()
    
    # Mappatura dei tasti alle direzioni
    key_mappings = {
        "arrowup": "nord",
        "w": "nord",
        "arrowdown": "sud",
        "s": "sud",
        "arrowright": "est",
        "d": "est",
        "arrowleft": "ovest",
        "a": "ovest",
        "escape": "esci"
    }
    
    if key not in key_mappings:
        return
        
    direzione = key_mappings[key]
    
    if direzione == "esci":
        # Torna al menu principale
        stato.menu_handler.mostra_menu_principale(gioco)
        return
        
    # Esegui il movimento
    movimento_riuscito = gioco.muovi_giocatore(direzione)
    
    if movimento_riuscito:
        # Effetto sonoro di movimento
        gioco.io.play_sound({
            "sound_id": "footstep",
            "volume": 0.3
        })
        
        # Aggiorna la posizione dell'indicatore
        giocatore_x, giocatore_y = gioco.giocatore.x, gioco.giocatore.y
        gioco.io.aggiorna_ui_elemento({
            "id": "player_marker",
            "x": giocatore_x * 32 + 16,
            "y": giocatore_y * 32 + 16
        })
        
        # Forza aggiornamento del renderer
        stato.ui_aggiornata = False
    else:
        # Effetto audio di collisione
        gioco.io.play_sound({
            "sound_id": "bump",
            "volume": 0.4
        })
        
        # Mostra messaggio di errore
        gioco.io.mostra_notifica({
            "text": "Non puoi muoverti in quella direzione!",
            "type": "warning",
            "duration": 1.0
        })

def interagisci_ambiente(stato, gioco):
    """Permette al giocatore di interagire con l'ambiente circostante tramite interfaccia grafica"""
    from states.mappa import MappaState
    
    # Effetto audio per attivazione modalità interazione
    gioco.io.play_sound({
        "sound_id": "interaction_mode",
        "volume": 0.5
    })
    
    # Ottieni gli oggetti interattivi vicini
    oggetti_vicini = gioco.giocatore.ottieni_oggetti_vicini(gioco.gestore_mappe)
    
    if not oggetti_vicini:
        # Mostra messaggio se non ci sono oggetti vicini
        gioco.io.mostra_dialogo(
            "Interazione ambiente", 
            "Non ci sono oggetti con cui interagire nelle vicinanze.",
            ["Torna al menu"]
        )
        stato.menu_attivo = "no_oggetti_vicini"
        
        # Aggiorna l'handler per tornare al menu principale
        original_handler = getattr(stato, "_handle_dialog_choice", None)
        stato._handle_dialog_choice = lambda event: stato.menu_handler.mostra_menu_principale(gioco)
        return
    
    # Se c'è già un'istanza del map state, la usiamo
    map_state = next((s for s in gioco.stato_stack if isinstance(s, MappaState)), None)
    if map_state:
        # Attiva la modalità interazione nella mappa
        map_state.attiva_interazione(gioco)
    else:
        # Se non c'è un'istanza di mappa, crea una nuova
        map_state = MappaState(stato_origine=stato)
        
        # Effetto di transizione
        gioco.io.mostra_transizione("fade", 0.3)
        
        # Passa al nuovo stato
        gioco.push_stato(map_state)
        
        # Attiva la modalità interazione nella mappa
        map_state.attiva_interazione(gioco)
    
    # Mostra la mappa
    visualizza_mappa(stato, gioco)
    
    # Mostra istruzioni
    gioco.io.mostra_ui_elemento({
        "type": "text",
        "id": "istruzioni_interazione",
        "text": "Clicca su un oggetto per interagire. ESC per tornare al menu.",
        "x": 400,
        "y": 50,
        "font_size": 16,
        "color": "#FFFFFF",
        "background": "#000000AA",
        "padding": 10,
        "z_index": 10
    })
    
    # Mostra indicatori per oggetti interattivi
    for pos, oggetto in oggetti_vicini.items():
        x, y = pos
        # Crea un indicatore visivo per ogni oggetto
        gioco.io.mostra_ui_elemento({
            "type": "sprite",
            "id": f"oggetto_marker_{x}_{y}",
            "image": "interactive_marker",
            "x": x * 32 + 16,
            "y": y * 32 + 16,
            "scale": 1.0,
            "z_index": 5,
            "interactive": True,
            "on_click": {
                "action": "interact",
                "target_id": oggetto.id if hasattr(oggetto, "id") else f"oggetto_{x}_{y}"
            }
        })
        
        # Aggiungi testo descrittivo sopra l'oggetto
        gioco.io.mostra_ui_elemento({
            "type": "text",
            "id": f"oggetto_label_{x}_{y}",
            "text": oggetto.nome,
            "x": x * 32 + 16,
            "y": y * 32 - 10,
            "font_size": 12,
            "color": "#FFFFFF",
            "background": "#00000088",
            "padding": 5,
            "z_index": 6
        })
    
    # Registra handler per gli eventi di click
    gioco.io.registra_handler_input("click", lambda event: handle_click_event(event, stato))
    
    # Registra handler per tasto ESC
    gioco.io.registra_handler_input("keydown", lambda event: handle_esc_keypress(event, stato))
    
    # Imposta la fase
    stato.fase = "interagisci_ambiente"
    
    # Aggiorna stato UI
    stato.menu_attivo = "interazione"
    stato.ui_aggiornata = False

def handle_click_event(event, stato):
    """Gestisce gli eventi di click per l'interazione con gli oggetti"""
    gioco = stato.gioco
    if not hasattr(event, "data") or not event.data:
        return
        
    action = event.data.get("action")
    target_id = event.data.get("target_id")
    
    if action != "interact" or not target_id:
        return
        
    # Trova l'oggetto cliccato dalle coordinate
    oggetti_vicini = gioco.giocatore.ottieni_oggetti_vicini(gioco.gestore_mappe)
    oggetto_selezionato = None
    
    for pos, oggetto in oggetti_vicini.items():
        obj_id = oggetto.id if hasattr(oggetto, "id") else f"oggetto_{pos[0]}_{pos[1]}"
        if obj_id == target_id:
            oggetto_selezionato = oggetto
            break
    
    if oggetto_selezionato:
        # Effetto audio
        gioco.io.play_sound({
            "sound_id": "item_interact",
            "volume": 0.6
        })
        
        # Mostra la descrizione dell'oggetto
        gioco.io.mostra_dialogo(
            f"Oggetto: {oggetto_selezionato.nome}",
            oggetto_selezionato.descrizione,
            ["Interagisci", "Torna alla mappa"]
        )
        
        # Memorizza l'oggetto selezionato
        stato.dati_contestuali["oggetto_selezionato"] = oggetto_selezionato
        
        # Aggiorna l'handler per gestire l'interazione con l'oggetto
        original_handler = getattr(stato, "_handle_dialog_choice", None)
        
        def object_interaction_handler(event):
            if not hasattr(event, "data") or not event.data:
                return
                
            choice = event.data.get("choice")
            if not choice:
                return
                
            # Ripristina l'handler originale
            stato._handle_dialog_choice = original_handler
            
            if choice == "Interagisci":
                # Interagisci con l'oggetto
                oggetto = stato.dati_contestuali.get("oggetto_selezionato")
                if oggetto:
                    # Effetto audio
                    gioco.io.play_sound({
                        "sound_id": "item_use",
                        "volume": 0.7
                    })
                    
                    # Esegui l'interazione
                    risultato = oggetto.interagisci(gioco.giocatore)
                    
                    # Mostra il risultato dell'interazione
                    gioco.io.mostra_notifica({
                        "text": risultato if risultato else f"Hai interagito con {oggetto.nome}",
                        "type": "success" if risultato else "info",
                        "duration": 2.0
                    })
                    
                    # Torna alla modalità interazione
                    interagisci_ambiente(stato, gioco)
            else:
                # Torna alla modalità interazione
                interagisci_ambiente(stato, gioco)
        
        # Imposta il nuovo handler
        stato._handle_dialog_choice = object_interaction_handler

def handle_esc_keypress(event, stato):
    """Gestisce la pressione del tasto ESC durante l'interazione con l'ambiente"""
    gioco = stato.gioco
    if not hasattr(event, "data") or not event.data:
        return
        
    key = event.data.get("key", "").lower()
    
    if key == "escape":
        # Cancella registrazioni degli handler
        gioco.io.cancella_handler_input("click", lambda event: handle_click_event(event, stato))
        gioco.io.cancella_handler_input("keydown", lambda event: handle_esc_keypress(event, stato))
        
        # Torna al menu principale
        stato.menu_handler.mostra_menu_principale(gioco) 