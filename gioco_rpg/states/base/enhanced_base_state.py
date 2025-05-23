from core.event_bus import EventBus
import core.events as Events

class EnhancedBaseState:
    """
    Classe base per tutti gli stati del gioco.
    Versione aggiornata che supporta anche EventBus, mantenendo
    la compatibilità con l'implementazione precedente.
    """
    def __init__(self):
        """Inizializza lo stato base"""
        self.gioco = None
        self.event_bus = EventBus.get_instance()
        
    def set_game_context(self, gioco):
        """Imposta il contesto di gioco per questo stato"""
        self.gioco = gioco
    
    def esegui(self, gioco=None):
        """
        Comportamento legacy per compatibilità
        
        Args:
            gioco: L'istanza del gioco che contiene lo stato corrente e il giocatore
        """
        # Usa il contesto memorizzato se disponibile
        game_ctx = gioco if gioco else getattr(self, 'gioco', None)
        if not game_ctx:
            raise ValueError("Contesto di gioco non disponibile. Usa set_game_context() prima di eseguire.")
            
        # Per retrocompatibilità, chiama update se implementato
        if hasattr(self, 'update') and callable(getattr(self, 'update')):
            self.update(0.033)  # Aggiornamento con valore dt predefinito
        else:
            raise NotImplementedError("Ogni stato deve implementare esegui() o update()")
    
    def update(self, dt):
        """
        Nuovo metodo per aggiornamenti basati su eventi.
        Da implementare negli stati che utilizzano EventBus.
        
        Args:
            dt: Delta time, tempo trascorso dall'ultimo aggiornamento
        """
        pass
    
    def entra(self, gioco=None):
        """Metodo chiamato quando si entra nello stato"""
        if gioco:
            self.set_game_context(gioco)
        # Emetti evento per segnalare l'ingresso nello stato
        self.event_bus.emit(Events.ENTER_STATE, state=self)
    
    def esci(self, gioco=None):
        """Metodo chiamato quando si esce dallo stato"""
        # Emetti evento per segnalare l'uscita dallo stato
        self.event_bus.emit(Events.EXIT_STATE, state=self)
    
    def pausa(self, gioco=None):
        """Metodo chiamato quando lo stato viene temporaneamente sospeso"""
        # Emetti evento per segnalare la pausa dello stato
        self.event_bus.emit("STATE_PAUSED", state=self)
    
    def riprendi(self, gioco=None):
        """Metodo chiamato quando lo stato torna ad essere attivo"""
        # Emetti evento per segnalare la ripresa dello stato
        self.event_bus.emit("STATE_RESUMED", state=self)
    
    # Metodi helper per eventi
    def emit_event(self, event_type, **data):
        """Helper per emettere eventi dall'interno dello stato"""
        self.event_bus.emit(event_type, **data)
    
    def push_state(self, state_class, **kwargs):
        """Richiedi un push di un nuovo stato usando EventBus"""
        self.event_bus.emit(Events.PUSH_STATE, state_class=state_class, **kwargs)
    
    def pop_state(self):
        """Richiedi un pop dello stato corrente usando EventBus"""
        self.event_bus.emit(Events.POP_STATE)
    
    def change_state(self, state_class, **kwargs):
        """Richiedi un cambio di stato usando EventBus"""
        self.event_bus.emit(Events.CHANGE_STATE, state_class=state_class, **kwargs)
    
    # Metodi per azioni di gioco basate su eventi
    def move_player(self, direction):
        """Muove il giocatore usando il sistema di eventi"""
        self.event_bus.emit(Events.PLAYER_MOVE, direction=direction)
    
    def player_attack(self, target_id):
        """Fa attaccare il giocatore usando il sistema di eventi"""
        self.event_bus.emit(Events.PLAYER_ATTACK, target_id=target_id)
    
    def player_use_item(self, item_id):
        """Fa usare un oggetto al giocatore usando il sistema di eventi"""
        self.event_bus.emit(Events.PLAYER_USE_ITEM, item_id=item_id)
    
    def player_interact(self, entity_id=None):
        """Fa interagire il giocatore con un'entità usando il sistema di eventi"""
        self.event_bus.emit(Events.PLAYER_INTERACT, entity_id=entity_id)
    
    def open_dialog(self, dialog_data):
        """Apre un dialogo usando il sistema di eventi"""
        self.event_bus.emit(Events.UI_DIALOG_OPEN, dialog=dialog_data)
    
    def close_dialog(self):
        """Chiude un dialogo usando il sistema di eventi"""
        self.event_bus.emit(Events.UI_DIALOG_CLOSE)
    
    def toggle_inventory(self):
        """Apre/chiude l'inventario usando il sistema di eventi"""
        self.event_bus.emit(Events.UI_INVENTORY_TOGGLE) 
        
    def to_dict(self):
        """
        Serializza lo stato in un dizionario per la persistenza.
        Implementazione base che le sottoclassi possono estendere.
        
        Returns:
            dict: Dizionario con i dati essenziali dello stato
        """
        data = {}
        data["nome_stato"] = getattr(self, "nome_stato", self.__class__.__name__)
        data["__type__"] = self.__class__.__name__ # Aggiungiamo il tipo esplicito per la deserializzazione

        attrs_to_skip = ["gioco", "event_bus", "ui_handler_instance", "menu_handler_instance", "ui_handler", "menu_handler", "commands"]

        for attr_name, attr_value in self.__dict__.items():
            if attr_name in attrs_to_skip or attr_name.startswith("_") or callable(attr_value):
                continue
            
            try:
                if hasattr(attr_value, 'to_dict') and callable(getattr(attr_value, 'to_dict')):
                    data[attr_name] = attr_value.to_dict()
                elif isinstance(attr_value, (dict, list, str, int, float, bool)) or attr_value is None:
                    # Tenta di serializzare solo se è un tipo JSON-compatibile noto o un altro dict/list
                    # Per dict e list, json.dumps gestirà la ricorsione e gli errori interni.
                    data[attr_name] = attr_value 
                # Altri tipi complessi non verranno aggiunti se non hanno to_dict
                # o non sono tipi primitivi/collezioni JSON standard.
            except Exception as e:
                # Non aggiungere l'attributo se la sua serializzazione (o il check) fallisce
                # logging.debug(f"Attributo '{attr_name}' saltato durante la serializzazione di EnhancedBaseState a causa di errore: {e}")
                pass # Salta l'attributo se c'è un problema
                
        return data 