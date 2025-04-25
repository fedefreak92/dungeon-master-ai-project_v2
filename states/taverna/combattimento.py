from entities.nemico import Nemico

def scegli_nemico(stato, gioco):
    """Permette all'utente di scegliere un nemico con cui combattere tramite interfaccia grafica"""
    # Mostra le opzioni di scelta nemico
    opzioni = [
        "Nemico casuale",
        "Nemico casuale facile",
        "Nemico casuale medio",
        "Nemico casuale difficile",
        "Scegli un tipo specifico",
        "Torna al menu principale"
    ]
    
    # Effetto audio
    gioco.io.play_sound({
        "sound_id": "combat_menu",
        "volume": 0.6
    })
    
    # Mostra il dialogo con le opzioni
    gioco.io.mostra_dialogo("Combattimento", "Come vuoi scegliere il nemico?", opzioni)
    
    # Imposta il menu attivo
    stato.menu_attivo = "scelta_modalita_nemico"
    
    # Aggiorna l'handler per gestire la scelta della modalità nemico
    original_handler = getattr(stato, "_handle_dialog_choice", None)
    
    def enemy_choice_handler(event):
        if not hasattr(event, "data") or not event.data:
            return
            
        choice = event.data.get("choice")
        if not choice:
            return
            
        # Ripristina l'handler originale
        stato._handle_dialog_choice = original_handler
            
        if choice == "Nemico casuale":
            nemico = Nemico.crea_casuale()
            avvia_combattimento_con_nemico(nemico, stato, gioco)
            
        elif choice == "Nemico casuale facile":
            nemico = Nemico.crea_casuale("facile")
            avvia_combattimento_con_nemico(nemico, stato, gioco)
            
        elif choice == "Nemico casuale medio":
            nemico = Nemico.crea_casuale("medio")
            avvia_combattimento_con_nemico(nemico, stato, gioco)
            
        elif choice == "Nemico casuale difficile":
            nemico = Nemico.crea_casuale("difficile")
            avvia_combattimento_con_nemico(nemico, stato, gioco)
            
        elif choice == "Scegli un tipo specifico":
            mostra_tipi_mostri(stato, gioco)
            
        elif choice == "Torna al menu principale":
            stato.menu_handler.mostra_menu_principale(gioco)
            stato.menu_attivo = "menu_principale"
            
    # Sostituisci temporaneamente l'handler
    stato._handle_dialog_choice = enemy_choice_handler

def avvia_combattimento_con_nemico(nemico, stato, gioco):
    """Avvia il combattimento con un nemico"""
    from states.combattimento import CombattimentoState
    
    # Effetto audio
    gioco.io.play_sound({
        "sound_id": "battle_start",
        "volume": 0.7
    })
    
    # Transizione al combattimento
    stato._esegui_transizione(
        gioco, 
        CombattimentoState(nemico=nemico), 
        tipo_transizione="battle_transition", 
        durata=0.5
    )
    
    stato.menu_attivo = "menu_principale"
    
def mostra_tipi_mostri(stato, gioco):
    """Mostra i tipi di mostri disponibili"""
    from entities.nemico import Nemico
    
    # Ottieni i tipi di mostri disponibili
    tipi_mostri = Nemico.ottieni_tipi_mostri()
    
    if not tipi_mostri:
        gioco.io.mostra_dialogo("Errore", "Non ci sono tipi di mostri disponibili.", ["Torna al menu"])
        stato.menu_attivo = "errore_tipi_mostri"
        
        # Aggiorna l'handler per tornare al menu principale
        original_handler = getattr(stato, "_handle_dialog_choice", None)
        stato._handle_dialog_choice = lambda event: stato.menu_handler.mostra_menu_principale(gioco)
        return
    
    # Formatta i nomi dei tipi di mostri per la visualizzazione
    tipi_mostri_formattati = [tipo.replace('_', ' ').title() for tipo in tipi_mostri]
    
    # Aggiungi opzione per tornare indietro
    tipi_mostri_formattati.append("Torna indietro")
    
    # Memorizza i tipi di mostri originali
    stato.dati_contestuali["tipi_mostri"] = tipi_mostri
    
    # Mostra il dialogo con i tipi di mostri
    gioco.io.mostra_dialogo("Tipi di mostri", "Scegli un tipo di mostro:", tipi_mostri_formattati)
    
    # Imposta il menu attivo
    stato.menu_attivo = "scelta_tipo_mostro"
    
    # Aggiorna l'handler per gestire la scelta del tipo di mostro
    original_handler = getattr(stato, "_handle_dialog_choice", None)
    
    def monster_type_handler(event):
        if not hasattr(event, "data") or not event.data:
            return
            
        choice = event.data.get("choice")
        if not choice:
            return
            
        # Ripristina l'handler originale
        stato._handle_dialog_choice = original_handler
            
        if choice == "Torna indietro":
            scegli_nemico(stato, gioco)
            return
            
        # Trova il tipo di mostro originale
        tipo_mostro = None
        tipi_mostri = stato.dati_contestuali.get("tipi_mostri", [])
        tipi_mostri_formattati = [tipo.replace('_', ' ').title() for tipo in tipi_mostri]
        
        if choice in tipi_mostri_formattati:
            idx = tipi_mostri_formattati.index(choice)
            tipo_mostro = tipi_mostri[idx]
            
        if tipo_mostro:
            nemico = Nemico(nome="", tipo_mostro=tipo_mostro)
            avvia_combattimento_con_nemico(nemico, stato, gioco)
    
    # Sostituisci temporaneamente l'handler
    stato._handle_dialog_choice = monster_type_handler
    
def combatti_con_npg(stato, gioco):
    """Mostra il menu di combattimento con NPG usando l'interfaccia grafica"""
    
    # Ottieni la lista di NPG da mostrare
    npg_lista = []
    npg_nomi = []
    
    if gioco.giocatore.mappa_corrente:
        npg_vicini = gioco.giocatore.ottieni_npg_vicini(gioco.gestore_mappe)
        if npg_vicini:
            npg_lista = list(npg_vicini.values())
        npg_nomi = [npg.nome for npg in npg_lista]
    
    # Se non ci sono NPG vicini, usa gli NPG della taverna
    if not npg_lista:
        npg_lista = list(stato.npg_presenti.values())
        npg_nomi = list(stato.npg_presenti.keys())
    
    # Aggiungi opzione per tornare indietro
    npg_nomi.append("Torna indietro")
    
    # Memorizza la lista di NPG per gestire la scelta
    stato.dati_contestuali["npg_lista"] = npg_lista
    
    # Effetto audio
    gioco.io.play_sound({
        "sound_id": "combat_menu",
        "volume": 0.6
    })
    
    # Mostra il dialogo con gli NPG disponibili
    gioco.io.mostra_dialogo("Con chi vuoi combattere?", "Scegli un avversario:", npg_nomi)
    
    # Imposta il menu attivo
    stato.menu_attivo = "selezione_npg_combattimento"
    
    # Aggiorna l'handler per gestire la scelta NPG per combattimento
    stato._handle_dialog_choice = lambda event: handle_combat_npc_choice(event, stato)
    
def handle_combat_npc_choice(event, stato):
    """
    Gestisce la selezione di un NPC per il combattimento
    """
    gioco = stato.gioco
    if not hasattr(event, "data") or not event.data:
        return
        
    choice = event.data.get("choice")
    if not choice:
        return
        
    # Se l'utente ha scelto di tornare indietro
    if choice == "Torna indietro":
        stato.menu_handler.mostra_menu_principale(gioco)
        return
        
    # Trova l'NPC selezionato
    npg_lista = stato.dati_contestuali.get("npg_lista", [])
    npg_selezionato = None
    
    for npg in npg_lista:
        if npg.nome == choice:
            npg_selezionato = npg
            break
    
    if not npg_selezionato:
        # Se non troviamo l'NPC nei dati contestuali, lo cerchiamo nei presenti
        if choice in stato.npg_presenti:
            npg_selezionato = stato.npg_presenti[choice]
    
    if npg_selezionato:
        # Chiedi conferma prima di attaccare
        gioco.io.mostra_dialogo(
            "Conferma combattimento", 
            f"Sei sicuro di voler attaccare {npg_selezionato.nome}?", 
            ["Sì, attacca", "No, torna indietro"]
        )
        
        # Memorizza l'NPC selezionato
        stato.dati_contestuali["npg_selezionato"] = npg_selezionato
        
        # Imposta il menu attivo
        stato.menu_attivo = "conferma_combattimento_npg"
        
        # Aggiorna l'handler per gestire la conferma
        original_handler = getattr(stato, "_handle_dialog_choice", None)
        
        def combat_confirmation_handler(event):
            if not hasattr(event, "data") or not event.data:
                return
                
            choice = event.data.get("choice")
            if not choice:
                return
                
            # Ripristina l'handler originale
            stato._handle_dialog_choice = original_handler
                
            if choice == "Sì, attacca":
                # Avvia il combattimento con l'NPC
                from states.combattimento import CombattimentoState
                npg = stato.dati_contestuali.get("npg_selezionato")
                
                if npg:
                    # Effetto audio
                    gioco.io.play_sound({
                        "sound_id": "battle_start",
                        "volume": 0.7
                    })
                    
                    # Transizione al combattimento
                    stato._esegui_transizione(
                        gioco, 
                        CombattimentoState(npg_ostile=npg), 
                        tipo_transizione="battle_transition", 
                        durata=0.5
                    )
                    
                    stato.menu_attivo = "menu_principale"
            else:
                # Torna al menu principale
                stato.menu_handler.mostra_menu_principale(gioco)
        
        # Imposta il nuovo handler
        stato._handle_dialog_choice = combat_confirmation_handler
    else:
        # Se non troviamo l'NPC, mostra un errore
        gioco.io.mostra_notifica({
            "text": "NPC non trovato!",
            "type": "error",
            "duration": 2.0
        })
        
        # Torna al menu principale
        stato.menu_handler.mostra_menu_principale(gioco) 