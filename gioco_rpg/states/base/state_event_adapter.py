from core.event_bus import EventBus
import core.events as Events
import logging

logger = logging.getLogger(__name__)

class StateEventAdapter:
    """
    Adattatore per collegare il sistema di stati con l'EventBus.
    Permette una migrazione graduale senza riscrivere tutto subito.
    """
    def __init__(self, state_manager):
        self.state_manager = state_manager
        self.event_bus = EventBus.get_instance()
        self._register_handlers()
    
    def _register_handlers(self):
        """Registra gli handler per gli eventi relativi agli stati"""
        self.event_bus.on(Events.PUSH_STATE, self._handle_push_state)
        self.event_bus.on(Events.POP_STATE, self._handle_pop_state)
        self.event_bus.on(Events.CHANGE_STATE, self._handle_change_state)
    
    def _handle_push_state(self, state_class, **kwargs):
        """Gestisce la richiesta di push di un nuovo stato sullo stack"""
        logger.debug(f"Evento PUSH_STATE ricevuto per {state_class.__name__}")
        new_state = state_class(**kwargs)
        self.state_manager.push_state(new_state)
        # Emetti evento per informare che lo stato è stato inserito
        self.event_bus.emit(Events.ENTER_STATE, state=new_state)
    
    def _handle_pop_state(self):
        """Gestisce la richiesta di pop dello stato corrente dallo stack"""
        if self.state_manager.stack:
            old_state = self.state_manager.pop_state()
            logger.debug(f"Evento POP_STATE: rimosso {old_state.__class__.__name__}")
            # Emetti evento per informare che lo stato è stato rimosso
            self.event_bus.emit(Events.EXIT_STATE, state=old_state)
    
    def _handle_change_state(self, state_class, **kwargs):
        """Gestisce la richiesta di cambio di stato (pop + push)"""
        logger.debug(f"Evento CHANGE_STATE ricevuto per {state_class.__name__}")
        if self.state_manager.stack:
            old_state = self.state_manager.pop_state()
            self.event_bus.emit(Events.EXIT_STATE, state=old_state)
        
        new_state = state_class(**kwargs)
        self.state_manager.push_state(new_state)
        self.event_bus.emit(Events.ENTER_STATE, state=new_state) 