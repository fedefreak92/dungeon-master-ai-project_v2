"""
Modulo per la gestione degli eventi dell'interfaccia utente dello stato di dialogo
"""
import core.events as Events

def handle_dialog_choice(self, event):
    """
    Handler per le scelte dai dialoghi
    
    Args:
        event: Evento di scelta da dialogo
    """
    if not hasattr(event, "data") or not event.data:
        return
    
    choice = event.data.get("choice")
    if not choice:
        return
        
    game_ctx = self.gioco
    if not game_ctx:
        return
    
    # Fase normale di conversazione con opzioni
    if self.fase == "conversazione":
        # Trova l'indice della scelta selezionata
        dati_conversazione = self.npg.ottieni_conversazione(self.stato_corrente)
        if dati_conversazione and "opzioni" in dati_conversazione:
            opzioni = [testo for testo, _ in dati_conversazione["opzioni"]]
            if choice in opzioni:
                idx = opzioni.index(choice)
                # Ottieni la destinazione associata alla scelta
                destinazioni = self.dati_contestuali.get("opzioni_destinazioni", [])
                if idx < len(destinazioni):
                    destinazione = destinazioni[idx]
                    
                    # Emetti evento per la selezione del dialogo
                    self.emit_event(Events.MENU_SELECTION, 
                                   menu_id="dialog_options",
                                   selection=choice,
                                   destination=destinazione)
                    
                    # Effetto audio per la selezione
                    game_ctx.io.play_sound({
                        "sound_id": "dialog_select",
                        "volume": 0.6
                    })
                    
                    # Se la destinazione è None, termina il dialogo
                    if destinazione is None:
                        self.emit_event(Events.UI_DIALOG_CLOSE)
                    else:
                        # Altrimenti, passa allo stato successivo
                        self.stato_corrente = destinazione
                        self.dati_contestuali["mostrato_dialogo_corrente"] = False
                        
                        # Aggiorna l'interfaccia
                        self._mostra_dialogo_corrente(game_ctx)
    
    # Fase finale del dialogo o caso senza opzioni
    elif self.fase == "fine":
        if choice == "Continua" or choice == "Chiudi":
            self.emit_event(Events.UI_DIALOG_CLOSE)

def handle_click_event(self, event):
    """
    Handler per gestire gli eventi di click su elementi dell'interfaccia
    
    Args:
        event: Evento di click
    """
    if not hasattr(event, "data") or not event.data:
        return
    
    target = event.data.get("target")
    if not target:
        return
        
    game_ctx = self.gioco
    if not game_ctx:
        return
    
    # Gestione click su elementi specifici dell'interfaccia di dialogo
    if target == "ritratto_npg":
        # Emetti evento di click sul ritratto
        self.emit_event(Events.UI_DIALOG_OPEN, 
                       dialog_id="info_npg")
    elif target == "sfondo_dialogo":
        # Click sullo sfondo del dialogo potrebbe continuare il dialogo
        if self.fase == "fine":
            self.emit_event(Events.UI_DIALOG_CLOSE)
    elif target.startswith("opzione_dialogo_"):
        # Click su un'opzione di dialogo
        try:
            indice = int(target.replace("opzione_dialogo_", ""))
            self._gestisci_click_opzione(game_ctx, indice)
        except ValueError:
            pass

def handle_menu_action(self, event):
    """
    Handler per le azioni dal menu contestuale
    
    Args:
        event: Evento di menu
    """
    if not hasattr(event, "data") or not event.data:
        return
    
    action = event.data.get("action")
    if not action:
        return
        
    game_ctx = self.gioco
    if not game_ctx:
        return
    
    # Gestione azioni menu contestuale
    if action == "Info Personaggio":
        self.emit_event(Events.UI_DIALOG_OPEN, 
                       dialog_id="info_npg")
    elif action == "Mostra Inventario":
        self.emit_event(Events.UI_DIALOG_OPEN, 
                       dialog_id="inventario_npg")
    elif action == "Termina Dialogo":
        self.emit_event(Events.UI_DIALOG_CLOSE)

def gestisci_click_opzione(self, gioco, indice):
    """
    Gestisce il click su un'opzione di dialogo
    
    Args:
        gioco: Istanza del gioco
        indice: Indice dell'opzione selezionata
    """
    # Ottieni i dati della conversazione
    dati_conversazione = self.npg.ottieni_conversazione(self.stato_corrente)
    
    # Verifica che l'opzione sia valida
    if not dati_conversazione or not dati_conversazione.get("opzioni") or indice >= len(dati_conversazione["opzioni"]):
        return
    
    # Ottieni la destinazione
    opzione_testo, destinazione = dati_conversazione["opzioni"][indice]
    
    # Emetti evento di selezione opzione
    self.emit_event(Events.DIALOG_CHOICE, 
                   choice=opzione_testo, 
                   dialog_id=self.stato_corrente)
    
    # Effetto audio per la selezione
    gioco.io.play_sound({
        "sound_id": "dialog_select",
        "volume": 0.6
    })
    
    # Procedi con la destinazione
    if destinazione is None:
        self.emit_event(Events.UI_DIALOG_CLOSE)
    else:
        self.stato_corrente = destinazione
        self.dati_contestuali["mostrato_dialogo_corrente"] = False
        
        # Aggiorna l'interfaccia
        self._mostra_dialogo_corrente(gioco) 