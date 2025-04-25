from core.io_interface import GameIO

class UIMercatoHandler:
    def __init__(self, mercato_state):
        """
        Inizializza il gestore dell'interfaccia grafica per il mercato.
        
        Args:
            mercato_state: L'istanza dello stato mercato
        """
        self.mercato_state = mercato_state
        self.handlers_registrati = []
    
    def aggiorna_renderer(self, game_ctx):
        """
        Aggiorna il renderer grafico con gli elementi del mercato.
        
        Args:
            game_ctx: Il contesto di gioco
        """
        # Ottieni il renderer grafico
        renderer = game_ctx.io.get_renderer()
        if not renderer:
            return False
        
        # Pulisci il renderer
        renderer.clear()
        
        # Disegna il titolo e le informazioni
        renderer.draw_title("Mercato del Villaggio")
        renderer.draw_info(f"Oro: {game_ctx.giocatore.oro}")
        
        # Ottieni mappa e posizione del giocatore
        mappa = game_ctx.gestore_mappe.ottieni_mappa_attuale()
        if mappa:
            pos_giocatore = (game_ctx.giocatore.x, game_ctx.giocatore.y)
            
            # Se la visualizzazione mappa è attiva, disegnala
            if self.mercato_state.mostra_mappa:
                renderer.draw_map(mappa, pos_giocatore)
            
            # Disegna gli oggetti interattivi vicini
            oggetti_vicini = self.mercato_state.ottieni_oggetti_vicini(game_ctx, 3)
            for nome_oggetto, oggetto in oggetti_vicini.items():
                posizione = oggetto.get_position() if hasattr(oggetto, 'get_position') else None
                if posizione:
                    renderer.draw_object(nome_oggetto, posizione, "oggetto", oggetto.stato)
            
            # Disegna gli NPC vicini
            npg_vicini = self.mercato_state.ottieni_npg_vicini(game_ctx, 3)
            for nome_npg, npg in npg_vicini.items():
                posizione = npg.get_position() if hasattr(npg, 'get_position') else None
                if posizione:
                    renderer.draw_character(nome_npg, posizione)
        
        # Aggiorna il renderer
        renderer.update()
        return True
    
    def register_ui_handlers(self, io_handler):
        """
        Registra i gestori di eventi dell'interfaccia utente.
        
        Args:
            io_handler: L'handler IO del gioco
        """
        if not io_handler:
            return
        
        # Registra i gestori di eventi
        self.handlers_registrati = [
            io_handler.register_event_handler("click", self._handle_click_event),
            io_handler.register_event_handler("menu_action", self._handle_menu_action),
            io_handler.register_event_handler("dialog_choice", self._handle_dialog_choice),
            io_handler.register_event_handler("keypress", self._handle_keypress)
        ]
    
    def unregister_ui_handlers(self, io_handler):
        """
        Deregistra i gestori di eventi dell'interfaccia utente.
        
        Args:
            io_handler: L'handler IO del gioco
        """
        if not io_handler:
            return
            
        # Deregistra tutti i gestori registrati in precedenza
        for handler_id in self.handlers_registrati:
            io_handler.unregister_event_handler(handler_id)
        
        # Resetta la lista dei gestori registrati
        self.handlers_registrati = []
    
    def _handle_click_event(self, event):
        """
        Gestisce eventi di click.
        
        Args:
            event: L'evento di click
        """
        # Ottieni il contesto di gioco
        gioco = self.mercato_state.gioco
        if not gioco:
            return
            
        # Gestisci clic su oggetti
        if event.get("type") == "object_click":
            obj_id = event.get("object_id")
            self._on_oggetto_click(obj_id, gioco)
            return True
            
        # Gestisci clic su NPC
        elif event.get("type") == "npc_click":
            npc_id = event.get("npc_id")
            self._on_npc_click(npc_id, gioco)
            return True
            
        # Gestisci clic sulla mappa (movimento)
        elif event.get("type") == "map_click":
            x, y = event.get("position", (0, 0))
            self._on_map_click(x, y, gioco)
            return True
            
        return False
    
    def _handle_menu_action(self, event):
        """
        Gestisce azioni del menu.
        
        Args:
            event: L'evento di azione del menu
        """
        # Questo metodo sarà implementato se necessario
        return False
    
    def _handle_dialog_choice(self, event):
        """
        Gestisce scelte di dialogo.
        
        Args:
            event: L'evento di scelta di dialogo
        """
        # Questo metodo sarà implementato se necessario
        return False
    
    def _handle_keypress(self, event):
        """
        Gestisce eventi di tastiera.
        
        Args:
            event: L'evento di pressione tasto
        """
        # Ottieni il contesto di gioco
        gioco = self.mercato_state.gioco
        if not gioco:
            return False
            
        # Ottieni il tasto premuto
        key = event.get("key")
        if not key:
            return False
            
        # Gestione tasti di movimento
        movimento_mappato = {
            "w": "nord",
            "a": "ovest",
            "s": "sud",
            "d": "est",
            "ArrowUp": "nord",
            "ArrowLeft": "ovest",
            "ArrowDown": "sud",
            "ArrowRight": "est"
        }
        
        if key in movimento_mappato:
            direzione = movimento_mappato[key]
            self._muovi_sulla_mappa(gioco, direzione)
            return True
            
        # Altri tasti speciali
        if key == "m":
            # Attiva/disattiva la visualizzazione mappa
            self.mercato_state.mostra_mappa = not self.mercato_state.mostra_mappa
            self.mercato_state.ui_aggiornata = False  # Forza l'aggiornamento dell'UI
            return True
            
        elif key == "e":
            # Interagisci con oggetto/NPC più vicino
            self._interagisci_ambiente(gioco)
            return True
            
        elif key == "i":
            # Apri inventario
            from states.inventario import GestioneInventarioState
            inventario_state = GestioneInventarioState(gioco)
            gioco.push_stato(inventario_state)
            return True
            
        elif key == "Escape":
            # Torna al menu principale
            self.mercato_state.fase = "menu_principale"
            self.mercato_state.ui_aggiornata = False
            return True
            
        return False
    
    def _on_oggetto_click(self, obj_id, gioco):
        """
        Gestisce il click su un oggetto.
        
        Args:
            obj_id: L'ID dell'oggetto cliccato
            gioco: Il contesto di gioco
        """
        oggetto = None
        
        # Cerca l'oggetto tra quelli interattivi
        if obj_id in self.mercato_state.oggetti_interattivi:
            oggetto = self.mercato_state.oggetti_interattivi[obj_id]
        
        # Interagisci con l'oggetto se trovato
        if oggetto and hasattr(oggetto, 'interagisci'):
            messaggio = oggetto.interagisci(gioco.giocatore, gioco)
            gioco.io.mostra_messaggio(messaggio)
            self.mercato_state.ui_aggiornata = False  # Forza l'aggiornamento dell'UI
    
    def _on_npc_click(self, npc_id, gioco):
        """
        Gestisce il click su un NPC.
        
        Args:
            npc_id: L'ID dell'NPC cliccato
            gioco: Il contesto di gioco
        """
        # Cerca l'NPC tra quelli presenti
        if npc_id in self.mercato_state.npg_presenti:
            npg = self.mercato_state.npg_presenti[npc_id]
            
            # Salva l'NPG attivo
            self.mercato_state.nome_npg_attivo = npc_id
            
            # Avvia lo stato di dialogo
            from states.dialogo import DialogoState
            dialogo_state = DialogoState(gioco, npg)
            gioco.push_stato(dialogo_state)
    
    def _on_map_click(self, x, y, gioco):
        """
        Gestisce il click sulla mappa.
        
        Args:
            x: Coordinata X
            y: Coordinata Y
            gioco: Il contesto di gioco
        """
        mappa = gioco.gestore_mappe.ottieni_mappa_attuale()
        if not mappa:
            return
            
        # Calcola il percorso verso la posizione cliccata
        giocatore_x, giocatore_y = gioco.giocatore.x, gioco.giocatore.y
        
        # Implementazione semplificata: muovi verso la direzione generale
        if x > giocatore_x:
            self._muovi_sulla_mappa(gioco, "est")
        elif x < giocatore_x:
            self._muovi_sulla_mappa(gioco, "ovest")
        elif y > giocatore_y:
            self._muovi_sulla_mappa(gioco, "sud")
        elif y < giocatore_y:
            self._muovi_sulla_mappa(gioco, "nord")
    
    def _muovi_sulla_mappa(self, gioco, direzione):
        """
        Muove il giocatore sulla mappa.
        
        Args:
            gioco: Il contesto di gioco
            direzione: La direzione in cui muoversi
        """
        # Esegui il movimento
        successo = self.mercato_state.muovi_giocatore(direzione, gioco)
        
        # Aggiorna l'UI se il movimento è avvenuto
        if successo:
            self.mercato_state.ui_aggiornata = False  # Forza l'aggiornamento dell'UI
            return True
            
        return False
    
    def _interagisci_ambiente(self, gioco):
        """
        Interagisce con l'oggetto o NPC più vicino.
        
        Args:
            gioco: Il contesto di gioco
        """
        # Prima prova a interagire con oggetti
        oggetti_vicini = self.mercato_state.ottieni_oggetti_vicini(gioco, 1)
        if oggetti_vicini:
            # Prendi il primo oggetto trovato
            nome_oggetto, oggetto = next(iter(oggetti_vicini.items()))
            if hasattr(oggetto, 'interagisci'):
                messaggio = oggetto.interagisci(gioco.giocatore, gioco)
                gioco.io.mostra_messaggio(messaggio)
                self.mercato_state.ui_aggiornata = False  # Forza l'aggiornamento dell'UI
                return True
        
        # Se non ci sono oggetti, prova con gli NPC
        npg_vicini = self.mercato_state.ottieni_npg_vicini(gioco, 1)
        if npg_vicini:
            # Prendi il primo NPC trovato
            nome_npg, npg = next(iter(npg_vicini.items()))
            
            # Salva l'NPG attivo
            self.mercato_state.nome_npg_attivo = nome_npg
            
            # Avvia lo stato di dialogo
            from states.dialogo import DialogoState
            dialogo_state = DialogoState(gioco, npg)
            gioco.push_stato(dialogo_state)
            return True
        
        # Se non ci sono né oggetti né NPC vicini
        gioco.io.mostra_messaggio("Non c'è nulla con cui interagire nelle vicinanze.")
        return False 