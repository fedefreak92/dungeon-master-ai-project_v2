from states.base_state import BaseGameState

class EsempioStatoGrafico(BaseGameState):
    """
    Stato di esempio che mostra come convertire input testuali in eventi UI.
    Questo è un modello da seguire per aggiornare tutti gli stati del gioco.
    """
    
    def __init__(self, gioco=None):
        """Inizializza lo stato di esempio"""
        super().__init__(gioco)
        self.ultima_scelta = None
        self.menu_attivo = None
        
    def _init_commands(self):
        """Inizializza i comandi disponibili per questo stato"""
        # Definire mapping comandi -> funzioni
        self.commands = {
            "esegui_azione_a": self._azione_a,
            "esegui_azione_b": self._azione_b,
            "torna_indietro": self._torna_indietro
        }
    
    def esegui(self, gioco):
        """
        Esecuzione dello stato
        
        Args:
            gioco: Istanza del gioco
        """
        # Salva il contesto di gioco
        self.set_game_context(gioco)
        
        # Aggiorna il renderer grafico se necessario
        if not self.ui_aggiornata:
            self.aggiorna_renderer(gioco)
            self.ui_aggiornata = True
        
        # Mostra menu iniziale se non ne è già attivo uno
        if not self.menu_attivo:
            self._mostra_menu_principale(gioco)
            self.menu_attivo = "principale"
        
        # Elabora gli eventi UI - questo sostituisce l'input testuale
        # Gli handler registrati (_handle_click_event, _handle_dialog_choice, ecc.)
        # si occuperanno di gestire le interazioni dell'utente
        super().esegui(gioco)
    
    def _mostra_menu_principale(self, gioco):
        """
        Mostra il menu principale tramite UI
        
        Args:
            gioco: Istanza del gioco
        """
        # PRIMA:
        # gioco.io.mostra_messaggio("Menu Principale:")
        # gioco.io.mostra_messaggio("1. Azione A")
        # gioco.io.mostra_messaggio("2. Azione B")
        # gioco.io.mostra_messaggio("3. Torna indietro")
        # scelta = gioco.io.richiedi_input("Scelta: ")
        
        # DOPO:
        gioco.io.mostra_dialogo("Menu Principale", "Seleziona un'opzione:", [
            "Azione A",
            "Azione B",
            "Torna indietro"
        ])
    
    def _handle_dialog_choice(self, event):
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
            
        # Memorizza l'ultima scelta
        self.ultima_scelta = choice
        
        # Gestione menu principale
        if self.menu_attivo == "principale":
            if choice == "Azione A":
                self._azione_a(game_ctx)
            elif choice == "Azione B":
                self._azione_b(game_ctx)
            elif choice == "Torna indietro":
                self._torna_indietro(game_ctx)
        
        # Gestione menu secondario (esempio)
        elif self.menu_attivo == "secondario":
            if choice == "Opzione 1":
                self._opzione_1(game_ctx)
            elif choice == "Opzione 2":
                self._opzione_2(game_ctx)
            elif choice == "Indietro":
                self._mostra_menu_principale(game_ctx)
                self.menu_attivo = "principale"
    
    def _handle_click_event(self, event):
        """
        Handler per eventi di click
        
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
            
        # Esempio di gestione click su elementi interattivi
        if target.startswith("oggetto_"):
            obj_id = target.replace("oggetto_", "")
            self._interagisci_con_oggetto(game_ctx, obj_id)
        elif target.startswith("npc_"):
            npc_id = target.replace("npc_", "")
            self._interagisci_con_npc(game_ctx, npc_id)
    
    def _azione_a(self, gioco):
        """
        Esegue l'azione A
        
        Args:
            gioco: Istanza del gioco
        """
        gioco.io.mostra_messaggio("Hai scelto l'Azione A!")
        
        # Esempio di mostrare un menu secondario
        gioco.io.mostra_dialogo("Menu Secondario", "Seleziona un'opzione:", [
            "Opzione 1",
            "Opzione 2",
            "Indietro"
        ])
        
        self.menu_attivo = "secondario"
        
    def _azione_b(self, gioco):
        """
        Esegue l'azione B
        
        Args:
            gioco: Istanza del gioco
        """
        gioco.io.mostra_messaggio("Hai scelto l'Azione B!")
        
        # Esempio di interazione senza input testuale
        gioco.io.aggiungi_elemento_interattivo(
            "oggetto_speciale", 
            "oggetto",
            (10, 10),
            "special_item",
            {
                "onClick": lambda elem, event: self._interagisci_con_oggetto(gioco, "speciale")
            }
        )
        
        self.ui_aggiornata = False  # Richiedi aggiornamento del renderer
    
    def _torna_indietro(self, gioco):
        """
        Torna allo stato precedente
        
        Args:
            gioco: Istanza del gioco
        """
        if gioco.stato_corrente() == self:
            gioco.pop_stato()
    
    def _opzione_1(self, gioco):
        """
        Esegue l'opzione 1
        
        Args:
            gioco: Istanza del gioco
        """
        gioco.io.mostra_messaggio("Hai scelto l'Opzione 1!")
        
        # Altre operazioni...
        
        # Torna al menu principale
        self._mostra_menu_principale(gioco)
        self.menu_attivo = "principale"
    
    def _opzione_2(self, gioco):
        """
        Esegue l'opzione 2
        
        Args:
            gioco: Istanza del gioco
        """
        gioco.io.mostra_messaggio("Hai scelto l'Opzione 2!")
        
        # Altre operazioni...
        
        # Torna al menu principale
        self._mostra_menu_principale(gioco)
        self.menu_attivo = "principale"
    
    def _interagisci_con_oggetto(self, gioco, obj_id):
        """
        Interagisce con un oggetto
        
        Args:
            gioco: Istanza del gioco
            obj_id: ID dell'oggetto
        """
        gioco.io.mostra_messaggio(f"Stai interagendo con l'oggetto {obj_id}")
        
        # Mostra menu contestuale per l'oggetto
        gioco.io.mostra_menu_contestuale((10, 10), [
            "Esamina",
            "Raccogli",
            "Usa"
        ])
    
    def _interagisci_con_npc(self, gioco, npc_id):
        """
        Interagisce con un NPC
        
        Args:
            gioco: Istanza del gioco
            npc_id: ID del personaggio
        """
        gioco.io.mostra_messaggio(f"Stai interagendo con il personaggio {npc_id}")
        
        # Mostra dialogo con il personaggio
        gioco.io.mostra_dialogo(f"Dialogo con {npc_id}", 
                               "Cosa vuoi fare?", 
                               ["Parla", "Commercia", "Addio"])
    
    def _handle_menu_action(self, event):
        """
        Handler per azioni menu
        
        Args:
            event: Evento menu
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
        if action == "Esamina":
            game_ctx.io.mostra_messaggio("Stai esaminando l'oggetto...")
        elif action == "Raccogli":
            game_ctx.io.mostra_messaggio("Hai raccolto l'oggetto!")
        elif action == "Usa":
            game_ctx.io.mostra_messaggio("Stai usando l'oggetto...")
    
    def to_dict(self):
        """
        Serializza lo stato
        
        Returns:
            dict: Rappresentazione dello stato
        """
        data = super().to_dict()
        data.update({
            "ultima_scelta": self.ultima_scelta,
            "menu_attivo": self.menu_attivo
        })
        return data
    
    @classmethod
    def from_dict(cls, data, game=None):
        """
        Crea un'istanza dello stato da un dizionario
        
        Args:
            data: Dati serializzati
            game: Istanza del gioco
            
        Returns:
            EsempioStatoGrafico: Nuova istanza
        """
        instance = super().from_dict(data, game)
        
        if "ultima_scelta" in data:
            instance.ultima_scelta = data["ultima_scelta"]
        if "menu_attivo" in data:
            instance.menu_attivo = data["menu_attivo"]
            
        return instance 