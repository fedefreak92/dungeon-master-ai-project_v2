from states.base_state import EnhancedBaseState
from states.combattimento import CombattimentoState
import core.events as Events

class MenuState(EnhancedBaseState):
    def __init__(self, gioco=None):
        """Inizializza lo stato del menu"""
        super().__init__()
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
        self.event_bus.on(Events.KEY_PRESSED, self._handle_key_pressed)
        
    def _init_commands(self):
        """Inizializza i comandi disponibili per questo stato"""
        self.commands = {
            "inizia_gioco": self._inizia_gioco,
            "esci_gioco": self._esci_gioco
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
            
            # Mostra titolo del gioco
            gioco.io.mostra_ui_elemento({
                "type": "text",
                "id": "titolo_gioco",
                "text": "RPG Adventure",
                "x": 400,
                "y": 100, 
                "font_size": 48,
                "centered": True,
                "color": "#FFFFFF"
            })
            
            # Emetti evento di apertura dialogo
            self.emit_event(Events.UI_DIALOG_OPEN, 
                           dialog_id="menu_principale",
                           title="Menu Principale", 
                           message="Seleziona un'opzione:", 
                           options=["Inizia Gioco", "Esci"])
            
            self.ui_aggiornata = True
    
    def esegui(self, gioco):
        """
        Esecuzione dello stato menu
        Mantenuta per retrocompatibilità.
        
        Args:
            gioco: Istanza del gioco
        """
        # Salva il contesto di gioco
        self.set_game_context(gioco)
        
        # Aggiorna il renderer grafico se necessario
        if not self.ui_aggiornata:
            self.aggiorna_renderer(gioco)
            
            # Mostra titolo del gioco
            gioco.io.mostra_ui_elemento({
                "type": "text",
                "id": "titolo_gioco",
                "text": "RPG Adventure",
                "x": 400,
                "y": 100, 
                "font_size": 48,
                "centered": True,
                "color": "#FFFFFF"
            })
            
            # Mostra il menu principale con pulsanti
            gioco.io.mostra_dialogo("Menu Principale", "Seleziona un'opzione:", [
                "Inizia Gioco",
                "Esci"
            ])
            
            self.ui_aggiornata = True
        
        # Aggiungi chiamata a update per integrazione con EventBus
        self.update(0.033)  # Valore dt predefinito
        
        # Elabora gli eventi UI
        super().esegui(gioco)
    
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
        options = kwargs.get("options", ["Inizia Gioco", "Esci"])
        
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
        if not choice or menu_id != "menu_principale":
            return
            
        gioco = self.gioco
        if not gioco:
            return
            
        if choice == "Inizia Gioco":
            self._inizia_gioco(gioco)
        elif choice == "Esci":
            self._esci_gioco(gioco)
        elif choice == "Sì" and hasattr(self, "in_conferma_uscita") and self.in_conferma_uscita:
            # Chiudi il gioco
            self.emit_event(Events.GAME_EXIT)
        elif choice == "No" and hasattr(self, "in_conferma_uscita") and self.in_conferma_uscita:
            # Annulla uscita
            self.in_conferma_uscita = False
            self.ui_aggiornata = False
    
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
        self._handle_menu_selection(choice=choice, menu_id="menu_principale")
    
    def _handle_key_pressed(self, key=None, **kwargs):
        """
        Handler per la pressione dei tasti
        
        Args:
            key: Tasto premuto
            **kwargs: Parametri aggiuntivi
        """
        if not key:
            return
            
        gioco = self.gioco
        if not gioco:
            return
            
        # Gestione tasti di scelta rapida
        if key == "Escape":
            if hasattr(self, "in_conferma_uscita") and self.in_conferma_uscita:
                # Se siamo nella conferma, "Escape" è un "No"
                self.in_conferma_uscita = False
                self.ui_aggiornata = False
            else:
                # Altrimenti apri la conferma di uscita
                self._esci_gioco(gioco)
    
    def _handle_keypress(self, event):
        """
        Handler legacy per la pressione dei tasti.
        Mantenuto per retrocompatibilità.
        
        Args:
            event: Evento tastiera
        """
        if not hasattr(event, "data") or not event.data:
            return
        
        key = event.data.get("key")
        if not key:
            return
            
        # Converti in formato nuovo
        self._handle_key_pressed(key=key)
    
    def _inizia_gioco(self, gioco):
        """
        Avvia il gioco
        
        Args:
            gioco: Istanza del gioco
        """
        # Effetto sonoro
        gioco.io.play_sound({
            "sound_id": "menu_select",
            "volume": 0.7
        })
        
        # Transizione grafica
        gioco.io.mostra_transizione("fade", 0.5)
        
        # Emetti evento di cambio stato
        self.emit_event(Events.CHANGE_STATE, new_state="combattimento")
        
        # Cambio stato per retrocompatibilità
        gioco.cambia_stato(CombattimentoState())
    
    def _esci_gioco(self, gioco):
        """
        Esce dal gioco
        
        Args:
            gioco: Istanza del gioco
        """
        # Effetto sonoro
        gioco.io.play_sound({
            "sound_id": "menu_back",
            "volume": 0.5
        })
        
        # Emetti evento di apertura dialogo di conferma
        self.emit_event(Events.UI_DIALOG_OPEN, 
                       dialog_id="conferma_uscita",
                       title="Conferma", 
                       message="Sei sicuro di voler uscire dal gioco?", 
                       options=["Sì", "No"])
        
        # Per retrocompatibilità
        gioco.io.mostra_dialogo(
            "Conferma", 
            "Sei sicuro di voler uscire dal gioco?", 
            ["Sì", "No"]
        )
        self.in_conferma_uscita = True
    
    def to_dict(self):
        """
        Converte lo stato in un dizionario per la serializzazione.
        
        Returns:
            dict: Rappresentazione dello stato in formato dizionario
        """
        data = super().to_dict()
        data.update({
            "ui_aggiornata": self.ui_aggiornata,
            "in_conferma_uscita": getattr(self, "in_conferma_uscita", False)
        })
        return data

    @classmethod
    def from_dict(cls, data, game=None):
        """
        Crea un'istanza di MenuState da un dizionario.
        
        Args:
            data (dict): Dizionario con i dati dello stato
            game: Istanza del gioco (opzionale)
            
        Returns:
            MenuState: Nuova istanza dello stato
        """
        state = cls(game)
        state.ui_aggiornata = data.get("ui_aggiornata", False)
        state.in_conferma_uscita = data.get("in_conferma_uscita", False)
        return state 

# Alias per compatibilità con i test
MenuPrincipaleState = MenuState 