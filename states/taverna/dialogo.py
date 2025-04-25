def gestisci_dialogo_npg(stato, gioco):
    """Mostra il menu di dialogo con NPG usando l'interfaccia grafica"""
    
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
        "sound_id": "dialog_open",
        "volume": 0.5
    })
    
    # Mostra il dialogo con gli NPG disponibili
    gioco.io.mostra_dialogo("Con chi vuoi parlare?", "", npg_nomi)
    
    # Imposta il menu attivo
    stato.menu_attivo = "selezione_npg"
    
    # Aggiorna l'handler per gestire la scelta NPG per dialogo
    stato._handle_dialog_choice = lambda event: handle_dialog_npc_choice(event, stato)
    
def handle_dialog_npc_choice(event, stato):
    """Gestisce la selezione di un NPC per il dialogo"""
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
        # Effetto audio
        gioco.io.play_sound({
            "sound_id": "dialog_start",
            "volume": 0.6
        })
        
        # Avvia il dialogo con l'NPC
        from states.dialogo import DialogoState
        stato._esegui_transizione(
            gioco, 
            DialogoState(npg_selezionato), 
            tipo_transizione="fade", 
            durata=0.3
        )
        
        stato.menu_attivo = "menu_principale"
    else:
        # Se non troviamo l'NPC, mostra un errore
        gioco.io.mostra_notifica({
            "text": "NPC non trovato!",
            "type": "error",
            "duration": 2.0
        })
        
        # Torna al menu principale
        stato.menu_handler.mostra_menu_principale(gioco) 