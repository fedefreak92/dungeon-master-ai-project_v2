from states.base.base_state import BaseState
from states.base.ui import BaseUI

class BaseGameState(BaseState):
    """
    Classe base per stati di gioco con gestione dei comandi.
    Estende BaseState aggiungendo un meccanismo per i comandi di gioco.
    """
    def __init__(self, gioco=None):
        """Inizializza lo stato di gioco"""
        super().__init__()
        
        if gioco:
            self.set_game_context(gioco)
            
        # Inizializza comandi e gestione input
        self.input_in_attesa = False
        self.last_input = None
        self.commands = {}
        self._init_commands()
        
        # Stato UI
        self.ui_aggiornata = False
        
        # Registra handler eventi
        if gioco:
            self._register_ui_handlers(gioco.io)
    
    def _init_commands(self):
        """
        Inizializza i comandi disponibili per questo stato.
        Da sovrascrivere nelle classi figlie.
        """
        pass
    
    def _register_ui_handlers(self, io_handler):
        """
        Registra gli handler per gli eventi UI
        
        Args:
            io_handler: L'handler IO per registrare gli eventi
        """
        io_handler.register_event_handler("click", self._handle_click_event)
        io_handler.register_event_handler("menu_action", self._handle_menu_action)
        io_handler.register_event_handler("dialog_choice", self._handle_dialog_choice)
        io_handler.register_event_handler("keypress", self._handle_keypress)
    
    def _unregister_ui_handlers(self, io_handler):
        """
        Rimuove gli handler per gli eventi UI
        
        Args:
            io_handler: L'handler IO da cui rimuovere gli handler
        """
        io_handler.unregister_event_handler("click", self._handle_click_event)
        io_handler.unregister_event_handler("menu_action", self._handle_menu_action)
        io_handler.unregister_event_handler("dialog_choice", self._handle_dialog_choice)
        io_handler.unregister_event_handler("keypress", self._handle_keypress)
    
    def _handle_click_event(self, event):
        """Handler per eventi di click"""
        pass
    
    def _handle_menu_action(self, event):
        """Handler per azioni da menu contestuali"""
        pass
    
    def _handle_dialog_choice(self, event):
        """Handler per scelte da dialoghi"""
        pass
    
    def _handle_keypress(self, event):
        """Handler per tasti premuti"""
        pass
    
    def entra(self, gioco=None):
        """
        Inizializza lo stato all'ingresso.
        
        Args:
            gioco: L'istanza del gioco
        """
        super().entra(gioco)
        
        if gioco:
            # Registra handler per eventi UI
            self._register_ui_handlers(gioco.io)
            
            # Aggiorna il renderer grafico
            self.aggiorna_renderer(gioco)
            self.ui_aggiornata = True
    
    def esci(self, gioco=None):
        """
        Pulisce lo stato all'uscita.
        
        Args:
            gioco: L'istanza del gioco
        """
        game_ctx = gioco if gioco else getattr(self, 'gioco', None)
        if game_ctx:
            # Rimuovi handler per eventi UI
            self._unregister_ui_handlers(game_ctx.io)
        
        super().esci(gioco)
    
    def riprendi(self, gioco=None):
        """
        Riprende lo stato dopo essere stato in pausa.
        
        Args:
            gioco: L'istanza del gioco
        """
        super().riprendi(gioco)
        
        if gioco:
            # Registra nuovamente handler per eventi UI
            self._register_ui_handlers(gioco.io)
            
            # Aggiorna il renderer grafico
            self.aggiorna_renderer(gioco)
            self.ui_aggiornata = True
    
    def pausa(self, gioco=None):
        """
        Mette in pausa lo stato.
        
        Args:
            gioco: L'istanza del gioco
        """
        game_ctx = gioco if gioco else getattr(self, 'gioco', None)
        if game_ctx:
            # Rimuovi handler per eventi UI
            self._unregister_ui_handlers(game_ctx.io)
        
        super().pausa(gioco)
    
    def esegui(self, gioco=None):
        """
        Esegue lo stato di gioco.
        
        Args:
            gioco: L'istanza del gioco
        """
        # Usa il contesto memorizzato se disponibile
        game_ctx = gioco if gioco else getattr(self, 'gioco', None)
        if not game_ctx:
            raise ValueError("Contesto di gioco non disponibile")
        
        # Controlla se è necessario aggiornare l'UI
        if not self.ui_aggiornata:
            self.aggiorna_renderer(game_ctx)
            self.ui_aggiornata = True
        
        # Processa gli eventi al posto di gestire input testuale
        # Gli handler registrati si occuperanno delle azioni
        if hasattr(game_ctx.io, 'process_events'):
            game_ctx.io.process_events()
    
    def aggiorna_renderer(self, gioco=None):
        """
        Aggiorna il renderer grafico.
        Delega a BaseUI per l'aggiornamento.
        
        Args:
            gioco: L'istanza del gioco
            
        Returns:
            bool: True se l'aggiornamento è riuscito
        """
        return BaseUI.aggiorna_renderer(self, gioco)
    
    def to_dict(self):
        """
        Serializza lo stato in un dizionario.
        
        Returns:
            dict: Rappresentazione dello stato
        """
        from states.base.serializzazione import BaseSerializzazione
        data = BaseSerializzazione.to_dict(self)
        
        # Aggiungi attributi aggiuntivi
        data.update({
            "input_in_attesa": self.input_in_attesa,
            "last_input": self.last_input,
            "ui_aggiornata": self.ui_aggiornata
        })
        
        return data
    
    @classmethod
    def from_dict(cls, data, game=None):
        """
        Crea un'istanza dello stato da un dizionario.
        
        Args:
            data (dict): Dati serializzati
            game: Istanza del gioco
            
        Returns:
            BaseGameState: Nuova istanza
        """
        instance = cls(game)
        
        # Imposta attributi di base
        if "input_in_attesa" in data:
            instance.input_in_attesa = data["input_in_attesa"]
        if "last_input" in data:
            instance.last_input = data["last_input"]
        if "ui_aggiornata" in data:
            instance.ui_aggiornata = data["ui_aggiornata"]
        
        return instance 