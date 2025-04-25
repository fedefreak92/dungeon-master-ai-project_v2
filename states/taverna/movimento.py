import core.events as Events

def visualizza_mappa(stato, gioco=None):
    """
    Visualizza la mappa della taverna con effetti di transizione.
    Versione aggiornata per utilizzare EventBus.
    """
    # Ottieni il contesto di gioco se non fornito
    game_ctx = gioco if gioco else getattr(stato, 'gioco', None)
    if not game_ctx:
        return False
        
    # Usa EventBus se disponibile, altrimenti usa il metodo legacy
    if hasattr(stato, 'event_bus'):
        # Emetti evento per aprire la mappa
        stato.emit_event(Events.MAP_LOAD, origin_state="taverna")
        
        # Aggiorna lo stato
        stato.fase = "menu_principale"
        stato.menu_attivo = "mappa_aperta"
        stato.elementi_attivi = ["mappa"]
        stato.ui_aggiornata = False
        
        # Riproduci effetto audio
        game_ctx.io.play_sound({
            "sound_id": "map_open",
            "volume": 0.6
        })
        
        return True
    else:
        # Codice legacy per retrocompatibilità
        from states.mappa import MappaState
        
        # Effetto audio per l'apertura della mappa
        game_ctx.io.play_sound({
            "sound_id": "map_open",
            "volume": 0.6
        })
        
        # Opzioni di transizione
        parametri_transizione = {}
        
        # Se c'è già un'istanza del map state, la usiamo
        map_state = next((s for s in game_ctx.stato_stack if isinstance(s, MappaState)), None)
        if map_state:
            # Esegui la transizione verso lo stato mappa
            stato._esegui_transizione(
                gioco=game_ctx,
                stato_destinazione=map_state,
                parametri=parametri_transizione,
                tipo_transizione="fade",
                durata=0.3
            )
        else:
            # Crea un nuovo stato mappa e esegui la transizione
            nuovo_map_state = MappaState(stato_origine=stato)
            stato._esegui_transizione(
                gioco=game_ctx,
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
        
        return True

def gestisci_movimento(stato, gioco=None):
    """
    Permette al giocatore di muoversi sulla mappa utilizzando l'interfaccia grafica.
    Versione aggiornata per utilizzare EventBus.
    """
    # Ottieni il contesto di gioco se non fornito
    game_ctx = gioco if gioco else getattr(stato, 'gioco', None)
    if not game_ctx:
        return False
        
    # Usa EventBus se disponibile, altrimenti usa il metodo legacy
    if hasattr(stato, 'event_bus'):
        # Emetti evento per attivare modalità movimento
        stato.emit_event(Events.UI_UPDATE, 
                        action="movement_mode", 
                        state="taverna")
        
        # Riproduci effetto audio
        game_ctx.io.play_sound({
            "sound_id": "movement_mode",
            "volume": 0.5
        })
        
        # Mostra istruzioni movimento
        game_ctx.io.mostra_ui_elemento({
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
        
        # Registra handler per movimento tramite EventBus
        stato.event_bus.on("KEYDOWN", lambda event_data: _handle_keypress_event(stato, event_data))
        
        # Imposta la fase
        stato.fase = "muovi_mappa"
        
        # Aggiorna stato UI
        stato.menu_attivo = "movimento"
        stato.ui_aggiornata = False
        
        return True
    else:
        # Codice legacy per retrocompatibilità
        from states.mappa import MappaState
        
        # Effetto audio per attivazione modalità movimento
        game_ctx.io.play_sound({
            "sound_id": "movement_mode",
            "volume": 0.5
        })
        
        # Mostra istruzioni movimento
        game_ctx.io.mostra_ui_elemento({
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
        map_state = next((s for s in game_ctx.stato_stack if isinstance(s, MappaState)), None)
        if map_state:
            # Attiva la modalità movimento nella mappa
            map_state.attiva_movimento(game_ctx)
            
            # Mostra indicatore posizione giocatore
            giocatore_x, giocatore_y = game_ctx.giocatore.x, game_ctx.giocatore.y
            game_ctx.io.mostra_ui_elemento({
                "type": "sprite",
                "id": "player_marker",
                "image": "player_avatar",
                "x": giocatore_x * 32 + 16,  # Posizione centrata sulla cella
                "y": giocatore_y * 32 + 16,
                "scale": 1.0,
                "z_index": 5
            })
            
            # Abilita handler per tasti di movimento
            game_ctx.io.registra_handler_input("keydown", lambda event: handle_keypress(event, stato))
        else:
            # Se non c'è un'istanza di mappa, crea una nuova
            map_state = MappaState(stato_origine=stato)
            
            # Effetto di transizione
            game_ctx.io.mostra_transizione("fade", 0.3)
            
            # Passa al nuovo stato
            game_ctx.push_stato(map_state)
            
            # Attiva la modalità movimento nella mappa
            map_state.attiva_movimento(game_ctx)
        
        # Imposta la fase
        stato.fase = "muovi_mappa"
        
        # Aggiorna stato UI
        stato.menu_attivo = "movimento"
        stato.ui_aggiornata = False
        
        return True

def _handle_keypress_event(stato, event_data):
    """
    Versione aggiornata di handle_keypress che utilizza EventBus.
    Gestisce gli eventi di pressione tasti per il movimento.
    """
    if not event_data or not isinstance(event_data, dict):
        return
        
    key = event_data.get("key", "").lower()
    
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
        # Emetti evento per tornare al menu principale
        stato.emit_event(Events.MENU_CHANGED, menu_id="menu_principale")
        return
        
    # Emetti evento di movimento
    stato.emit_event(Events.PLAYER_MOVE, direction=direzione)

# Manteniamo il vecchio handle_keypress per retrocompatibilità
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
        
    # Usa EventBus se disponibile
    if hasattr(stato, 'event_bus'):
        stato.emit_event(Events.PLAYER_MOVE, direction=direzione)
    else:
        # Codice legacy per retrocompatibilità
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

def interagisci_ambiente(stato, gioco=None):
    """
    Permette al giocatore di interagire con l'ambiente circostante.
    Versione aggiornata per utilizzare EventBus.
    """
    # Ottieni il contesto di gioco se non fornito
    game_ctx = gioco if gioco else getattr(stato, 'gioco', None)
    if not game_ctx:
        return False
        
    # Usa EventBus se disponibile
    if hasattr(stato, 'event_bus'):
        # Emetti evento per attivare modalità interazione
        stato.emit_event(Events.PLAYER_INTERACT, 
                        interaction_type="environment",
                        state="taverna")
        
        # Riproduce effetto audio
        game_ctx.io.play_sound({
            "sound_id": "interaction_mode",
            "volume": 0.5
        })
        
        return True
    else:
        # Codice legacy per retrocompatibilità
        from states.mappa import MappaState
        
        # Effetto audio per attivazione modalità interazione
        game_ctx.io.play_sound({
            "sound_id": "interaction_mode",
            "volume": 0.5
        })
        
        # Ottieni gli oggetti interattivi vicini
        oggetti_vicini = game_ctx.giocatore.ottieni_oggetti_vicini(game_ctx.gestore_mappe)
        
        if not oggetti_vicini:
            # Mostra messaggio se non ci sono oggetti vicini
            game_ctx.io.mostra_dialogo(
                "Interazione ambiente", 
                "Non ci sono oggetti con cui interagire nelle vicinanze.",
                ["Torna al menu"]
            )
            stato.menu_attivo = "no_oggetti_vicini"
            
            # Aggiorna l'handler per tornare al menu principale
            original_handler = getattr(stato, "_handle_dialog_choice", None)
            stato._handle_dialog_choice = lambda event: stato.menu_handler.mostra_menu_principale(game_ctx)
            return False
        
        # Se c'è già un'istanza del map state, la usiamo
        map_state = next((s for s in game_ctx.stato_stack if isinstance(s, MappaState)), None)
        if map_state:
            # Attiva la modalità interazione nella mappa
            map_state.attiva_interazione(game_ctx)
        else:
            # Se non c'è un'istanza di mappa, crea una nuova
            map_state = MappaState(stato_origine=stato)
            
            # Effetto di transizione
            game_ctx.io.mostra_transizione("fade", 0.3)
            
            # Passa al nuovo stato
            game_ctx.push_stato(map_state)
            
            # Attiva la modalità interazione nella mappa
            map_state.attiva_interazione(game_ctx)
        
        # Mostra la mappa
        visualizza_mappa(stato, game_ctx)
        
        # Mostra istruzioni
        game_ctx.io.mostra_ui_elemento({
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
            game_ctx.io.mostra_ui_elemento({
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
        
        # Registra handler ESC per tornare al menu
        game_ctx.io.registra_handler_input("keydown", lambda event: handle_esc_keypress(event, stato))
        
        # Registra handler click per processare interazioni
        game_ctx.io.registra_handler_input("click", lambda event: handle_click_event(event, stato))
        
        return True

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