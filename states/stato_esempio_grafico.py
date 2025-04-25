from states.base_state import EnhancedBaseState
import core.events as Events

class EsempioStatoGrafico(EnhancedBaseState):
    """
    Stato di esempio che mostra come convertire input testuali in eventi UI.
    Questo è un modello da seguire per aggiornare tutti gli stati del gioco.
    """
    
    def __init__(self, gioco=None):
        """Inizializza lo stato di esempio"""
        super().__init__()
        self.ultima_scelta = None
        self.menu_attivo = None
        self.ui_aggiornata = False
        
        # Imposta il contesto di gioco se fornito
        if gioco:
            self.set_game_context(gioco)
            
        # Registra gli handler degli eventi
        self._register_event_handlers()
        
    def _register_event_handlers(self):
        """Registra gli handler per eventi relativi a questo stato"""
        self.event_bus.on(Events.UI_DIALOG_OPEN, self._handle_dialog_open)
        self.event_bus.on(Events.UI_DIALOG_CLOSE, self._handle_dialog_close)
        self.event_bus.on(Events.MENU_SELECTION, self._handle_menu_selection)
        self.event_bus.on(Events.UI_CLICK, self._handle_click_event)
        
    def _init_commands(self):
        """Inizializza i comandi disponibili per questo stato"""
        # Definire mapping comandi -> funzioni
        self.commands = {
            "esegui_azione_a": self._azione_a,
            "esegui_azione_b": self._azione_b,
            "torna_indietro": self._torna_indietro
        }
    
    def update(self, dt):
        """
        Aggiornamento basato su eventi.
        
        Args:
            dt: Delta time, tempo trascorso dall'ultimo aggiornamento
        """
        gioco = self.gioco
        if not gioco:
            return
            
        # Aggiorna il renderer grafico se necessario
        if not self.ui_aggiornata:
            self.aggiorna_renderer(gioco)
            self.ui_aggiornata = True
            
        # Mostra menu iniziale se non ne è già attivo uno
        if not self.menu_attivo:
            self._mostra_menu_principale(gioco)
            self.menu_attivo = "principale"
    
    def esegui(self, gioco):
        """
        Esecuzione dello stato
        Mantenuta per retrocompatibilità.
        
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
        
        # Chiama update per integrazione con EventBus
        self.update(0.033)  # Valore dt predefinito
        
        # Elabora gli eventi UI
        super().esegui(gioco)
    
    def _mostra_menu_principale(self, gioco):
        """
        Mostra il menu principale tramite UI
        
        Args:
            gioco: Istanza del gioco
        """
        # Emetti evento di apertura dialogo
        self.emit_event(Events.UI_DIALOG_OPEN, 
                       dialog_id="menu_principale",
                       title="Menu Principale", 
                       message="Seleziona un'opzione:", 
                       options=["Azione A", "Azione B", "Torna indietro"])
        
    def _handle_dialog_open(self, dialog_id=None, **kwargs):
        """
        Handler per l'apertura di un dialogo
        
        Args:
            dialog_id: ID del dialogo da aprire
            **kwargs: Parametri aggiuntivi
        """
        gioco = self.gioco
        if not gioco or dialog_id != "menu_principale":
            return
            
        # Mostra il dialogo usando il vecchio sistema per retrocompatibilità
        title = kwargs.get("title", "Menu Principale")
        message = kwargs.get("message", "Seleziona un'opzione:")
        options = kwargs.get("options", [])
        
        gioco.io.mostra_dialogo(title, message, options)
    
    def _handle_dialog_close(self, **kwargs):
        """Handler per la chiusura di un dialogo"""
        pass
        
    def _handle_menu_selection(self, choice=None, menu_id=None, **kwargs):
        """
        Handler per le selezioni dal menu
        
        Args:
            choice: Opzione selezionata
            menu_id: ID del menu
            **kwargs: Parametri aggiuntivi
        """
        if not choice:
            return
            
        gioco = self.gioco
        if not gioco:
            return
            
        # Memorizza l'ultima scelta
        self.ultima_scelta = choice
        
        # Gestione menu principale
        if self.menu_attivo == "principale" and menu_id == "menu_principale":
            if choice == "Azione A":
                self._azione_a(gioco)
            elif choice == "Azione B":
                self._azione_b(gioco)
            elif choice == "Torna indietro":
                self._torna_indietro(gioco)
        
        # Gestione menu secondario (esempio)
        elif self.menu_attivo == "secondario" and menu_id == "menu_secondario":
            if choice == "Opzione 1":
                self._opzione_1(gioco)
            elif choice == "Opzione 2":
                self._opzione_2(gioco)
            elif choice == "Indietro":
                self._mostra_menu_principale(gioco)
                self.menu_attivo = "principale"
    
    def _handle_dialog_choice(self, event):
        """
        Handler legacy per le scelte dai dialoghi.
        Mantenuto per retrocompatibilità.
        
        Args:
            event: Evento di scelta da dialogo
        """
        if not hasattr(event, "data") or not event.data:
            return
        
        choice = event.data.get("choice")
        if not choice:
            return
            
        # Converti in formato nuovo
        menu_id = "menu_principale"
        if self.menu_attivo == "secondario":
            menu_id = "menu_secondario"
            
        self._handle_menu_selection(choice=choice, menu_id=menu_id)
    
    def _handle_click_event(self, target=None, **kwargs):
        """
        Handler per eventi di click
        
        Args:
            target: Elemento cliccato
            **kwargs: Parametri aggiuntivi
        """
        if not target:
            return
            
        gioco = self.gioco
        if not gioco:
            return
            
        # Esempio di gestione click su elementi interattivi
        if target.startswith("oggetto_"):
            obj_id = target.replace("oggetto_", "")
            self._interagisci_con_oggetto(gioco, obj_id)
        elif target.startswith("npc_"):
            npc_id = target.replace("npc_", "")
            self._interagisci_con_npc(gioco, npc_id)
    
    def _azione_a(self, gioco):
        """
        Esegue l'azione A
        
        Args:
            gioco: Istanza del gioco
        """
        gioco.io.mostra_messaggio("Hai scelto l'Azione A!")
        
        # Esempio di mostrare un menu secondario usando eventi
        self.emit_event(Events.UI_DIALOG_OPEN, 
                       dialog_id="menu_secondario",
                       title="Menu Secondario", 
                       message="Seleziona un'opzione:", 
                       options=["Opzione 1", "Opzione 2", "Indietro"])
        
        self.menu_attivo = "secondario"
        
    def _azione_b(self, gioco):
        """
        Esegue l'azione B
        
        Args:
            gioco: Istanza del gioco
        """
        gioco.io.mostra_messaggio("Hai scelto l'Azione B!")
        
        # Esempio di interazione usando eventi
        self.emit_event(Events.UI_ADD_INTERACTIVE_ELEMENT, 
                       element_id="oggetto_speciale",
                       element_type="oggetto",
                       position=(10, 10),
                       sprite="special_item")
        
        self.ui_aggiornata = False  # Richiedi aggiornamento del renderer
    
    def _torna_indietro(self, gioco):
        """
        Torna allo stato precedente
        
        Args:
            gioco: Istanza del gioco
        """
        # Usa eventi per il pop dello stato
        self.emit_event(Events.POP_STATE)
        
        # Mantieni per retrocompatibilità
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
        # Usa eventi per interagire con l'oggetto
        self.emit_event(Events.PLAYER_INTERACT, 
                       interaction_type="object",
                       object_id=obj_id)
        
        # Codice di retrocompatibilità
        gioco.io.mostra_messaggio(f"Interagisci con oggetto: {obj_id}")
        
        # Altre operazioni specifiche...
    
    def _interagisci_con_npc(self, gioco, npc_id):
        """
        Interagisce con un NPC
        
        Args:
            gioco: Istanza del gioco
            npc_id: ID dell'NPC
        """
        # Usa eventi per interagire con l'NPC
        self.emit_event(Events.PLAYER_INTERACT, 
                       interaction_type="npc",
                       npc_id=npc_id)
        
        # Codice di retrocompatibilità
        gioco.io.mostra_messaggio(f"Interagisci con NPC: {npc_id}")
        
        # Altre operazioni specifiche...
    
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