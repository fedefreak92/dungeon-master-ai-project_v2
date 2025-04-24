class MenuInventarioHandler:
    """
    Classe che gestisce le interazioni con i menu dell'inventario.
    Gestisce le scelte di dialogo e le transizioni tra i vari menu.
    """
    
    def __init__(self, inventario_state):
        """
        Inizializza il gestore menu.
        
        Args:
            inventario_state: L'istanza dello stato inventario
        """
        self.inventario_state = inventario_state
        
    def handle_dialog_choice(self, event):
        """
        Gestisce le scelte dai dialoghi.
        
        Args:
            event: Evento di scelta da dialogo
            
        Returns:
            bool: True se l'evento è stato gestito, False altrimenti
        """
        if not hasattr(event, "data") or not event.data:
            return False
        
        choice = event.data.get("choice")
        if not choice:
            return False
            
        game_ctx = self.inventario_state.gioco
        if not game_ctx:
            return False
        
        # Menu principale - Selezione azione
        if self.inventario_state.fase == "menu_principale":
            return self._handle_menu_principale(choice, game_ctx)
        
        # Selezione oggetto da usare
        elif self.inventario_state.fase == "usa_oggetto":
            return self._handle_usa_oggetto(choice, game_ctx)
        
        # Selezione oggetto da equipaggiare
        elif self.inventario_state.fase == "equipaggia_oggetto":
            return self._handle_equipaggia_oggetto(choice, game_ctx)
        
        # Selezione equipaggiamento da rimuovere
        elif self.inventario_state.fase == "rimuovi_equipaggiamento":
            return self._handle_rimuovi_equipaggiamento(choice, game_ctx)
        
        # Selezione oggetto da esaminare
        elif self.inventario_state.fase == "esamina_oggetto":
            return self._handle_esamina_oggetto(choice, game_ctx)
        
        # Conferma dopo aver esaminato un oggetto
        elif self.inventario_state.fase == "visualizza_dettagli":
            self.inventario_state.fase = "menu_principale"
            self.inventario_state.ui_aggiornata = False
            return True
        
        # Mostrare avviso quando non ci sono oggetti equipaggiabili o da rimuovere
        elif self.inventario_state.fase in ["avviso_equipaggiamento", "avviso_rimozione"]:
            if choice == "Torna al Menu":
                self.inventario_state.fase = "menu_principale"
                self.inventario_state.ui_aggiornata = False
                return True
        
        # Inventario vuoto
        elif choice == "Torna Indietro":
            self.torna_indietro(game_ctx)
            return True
            
        return False
        
    def _handle_menu_principale(self, choice, game_ctx):
        """
        Gestisce le scelte del menu principale.
        
        Args:
            choice: La scelta effettuata
            game_ctx: Il contesto di gioco
            
        Returns:
            bool: True se la scelta è stata gestita, False altrimenti
        """
        if choice == "Usa oggetto":
            self.inventario_state.fase = "usa_oggetto"
            self.inventario_state.ui_aggiornata = False
            # Emetti evento di cambio menu
            if hasattr(self.inventario_state, 'emit_event'):
                self.inventario_state.emit_event("MENU_CHANGED", menu="usa_oggetto")
            return True
        elif choice == "Equipaggia oggetto":
            self.inventario_state.fase = "equipaggia_oggetto"
            self.inventario_state.ui_aggiornata = False
            # Emetti evento di cambio menu
            if hasattr(self.inventario_state, 'emit_event'):
                self.inventario_state.emit_event("MENU_CHANGED", menu="equipaggia_oggetto")
            return True
        elif choice == "Rimuovi equipaggiamento":
            self.inventario_state.fase = "rimuovi_equipaggiamento"
            self.inventario_state.ui_aggiornata = False
            # Emetti evento di cambio menu
            if hasattr(self.inventario_state, 'emit_event'):
                self.inventario_state.emit_event("MENU_CHANGED", menu="rimuovi_equipaggiamento")
            return True
        elif choice == "Esamina oggetto":
            self.inventario_state.fase = "esamina_oggetto"
            self.inventario_state.ui_aggiornata = False
            # Emetti evento di cambio menu
            if hasattr(self.inventario_state, 'emit_event'):
                self.inventario_state.emit_event("MENU_CHANGED", menu="esamina_oggetto")
            return True
        elif choice == "Torna indietro":
            self.torna_indietro(game_ctx)
            return True
            
        return False
        
    def _handle_usa_oggetto(self, choice, game_ctx):
        """
        Gestisce le scelte del menu uso oggetti.
        
        Args:
            choice: La scelta effettuata
            game_ctx: Il contesto di gioco
            
        Returns:
            bool: True se la scelta è stata gestita, False altrimenti
        """
        if choice == "Annulla":
            self.inventario_state.fase = "menu_principale"
            self.inventario_state.ui_aggiornata = False
            # Emetti evento di cambio menu
            if hasattr(self.inventario_state, 'emit_event'):
                self.inventario_state.emit_event("MENU_CHANGED", menu="menu_principale")
            return True
        else:
            for i, item in enumerate(game_ctx.giocatore.inventario):
                nome_item = item.nome if hasattr(item, 'nome') else str(item)
                if nome_item == choice:
                    # Emetti evento di uso oggetto
                    if hasattr(self.inventario_state, 'emit_event'):
                        self.inventario_state.emit_event("PLAYER_USE_ITEM", 
                                                       item_id=item.id if hasattr(item, 'id') else None,
                                                       item_name=nome_item)
                    # Per retrocompatibilità chiamiamo anche il metodo diretto
                    self.inventario_state.gestore_oggetti.usa_oggetto_selezionato(game_ctx, item)
                    return True
        
        return False
        
    def _handle_equipaggia_oggetto(self, choice, game_ctx):
        """
        Gestisce le scelte del menu equipaggiamento oggetti.
        
        Args:
            choice: La scelta effettuata
            game_ctx: Il contesto di gioco
            
        Returns:
            bool: True se la scelta è stata gestita, False altrimenti
        """
        if choice == "Annulla":
            self.inventario_state.fase = "menu_principale"
            self.inventario_state.ui_aggiornata = False
            # Emetti evento di cambio menu
            if hasattr(self.inventario_state, 'emit_event'):
                self.inventario_state.emit_event("MENU_CHANGED", menu="menu_principale")
            return True
        else:
            # Estrai il nome dell'oggetto dalla scelta (rimuovi la parte del tipo tra parentesi)
            nome_oggetto = choice.split(" (")[0]
            equipaggiabili = self.inventario_state.gestore_oggetti.get_oggetti_equipaggiabili(game_ctx)
            for item in equipaggiabili:
                if item.nome == nome_oggetto:
                    # Emetti evento di equipaggiamento oggetto
                    if hasattr(self.inventario_state, 'emit_event'):
                        self.inventario_state.emit_event("EQUIP_ITEM", 
                                                       item_id=item.id if hasattr(item, 'id') else None,
                                                       item_name=item.nome)
                    # Per retrocompatibilità chiamiamo anche il metodo diretto
                    self.inventario_state.gestore_oggetti.equipaggia_oggetto_selezionato(game_ctx, item)
                    return True
        
        return False
        
    def _handle_rimuovi_equipaggiamento(self, choice, game_ctx):
        """
        Gestisce le scelte del menu rimozione equipaggiamento.
        
        Args:
            choice: La scelta effettuata
            game_ctx: Il contesto di gioco
            
        Returns:
            bool: True se la scelta è stata gestita, False altrimenti
        """
        if choice == "Annulla":
            self.inventario_state.fase = "menu_principale"
            self.inventario_state.ui_aggiornata = False
            # Emetti evento di cambio menu
            if hasattr(self.inventario_state, 'emit_event'):
                self.inventario_state.emit_event("MENU_CHANGED", menu="menu_principale")
            return True
        else:
            opzioni_rimozione = self.inventario_state.gestore_oggetti.get_opzioni_rimozione(game_ctx)
            for tipo, item in opzioni_rimozione:
                opzione_testo = f"{tipo.capitalize()}: {item.nome}"
                if opzione_testo == choice:
                    # Emetti evento di rimozione equipaggiamento
                    if hasattr(self.inventario_state, 'emit_event'):
                        self.inventario_state.emit_event("UNEQUIP_ITEM", 
                                                       item_id=item.id if hasattr(item, 'id') else None,
                                                       item_name=item.nome,
                                                       slot_type=tipo)
                    # Per retrocompatibilità chiamiamo anche il metodo diretto
                    self.inventario_state.gestore_oggetti.rimuovi_equipaggiamento_selezionato(game_ctx, item)
                    return True
        
        return False
        
    def _handle_esamina_oggetto(self, choice, game_ctx):
        """
        Gestisce le scelte del menu esame oggetti.
        
        Args:
            choice: La scelta effettuata
            game_ctx: Il contesto di gioco
            
        Returns:
            bool: True se la scelta è stata gestita, False altrimenti
        """
        if choice == "Annulla":
            self.inventario_state.fase = "menu_principale"
            self.inventario_state.ui_aggiornata = False
            # Emetti evento di cambio menu
            if hasattr(self.inventario_state, 'emit_event'):
                self.inventario_state.emit_event("MENU_CHANGED", menu="menu_principale")
            return True
        else:
            for item in game_ctx.giocatore.inventario:
                nome_item = item.nome if hasattr(item, 'nome') else str(item)
                if nome_item == choice:
                    # Emetti evento di esame oggetto
                    if hasattr(self.inventario_state, 'emit_event'):
                        self.inventario_state.emit_event("EXAMINE_ITEM", 
                                                       item_id=item.id if hasattr(item, 'id') else None,
                                                       item_name=nome_item)
                    # Per retrocompatibilità chiamiamo anche il metodo diretto
                    self.inventario_state.gestore_oggetti.esamina_oggetto_selezionato(game_ctx, item)
                    return True
        
        return False
        
    def torna_indietro(self, gioco):
        """
        Torna allo stato precedente.
        
        Args:
            gioco: L'istanza del gioco
        """
        # Effetto sonoro
        gioco.io.play_sound({
            "sound_id": "menu_back",
            "volume": 0.5
        })
        
        # Transizione
        gioco.io.mostra_transizione("fade", 0.3)
        
        # Emetti evento prima di tornare indietro
        if hasattr(self.inventario_state, 'emit_event'):
            self.inventario_state.emit_event("UI_INVENTORY_TOGGLE")
        
        # Torna allo stato precedente
        if gioco.stato_corrente() == self.inventario_state:
            if hasattr(self.inventario_state, 'pop_state'):
                # Usa il metodo basato su eventi se disponibile
                self.inventario_state.pop_state()
            else:
                # Retrocompatibilità con il vecchio sistema
                gioco.pop_stato() 