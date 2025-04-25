"""
Game loop principale basato su EventBus.
Questa implementazione sostituisce gradualmente il game loop tradizionale.
"""

import time
import logging
from core.event_bus import EventBus
import core.events as Events
from states.base.state_event_adapter import StateEventAdapter

logger = logging.getLogger(__name__)

class StateManager:
    """
    Gestore degli stati di gioco compatibile con EventBus.
    """
    def __init__(self):
        self.stack = []
    
    @property
    def current_state(self):
        """Restituisce lo stato corrente in cima allo stack"""
        return self.stack[-1] if self.stack else None
    
    def push_state(self, state):
        """Aggiunge uno stato in cima allo stack"""
        self.stack.append(state)
    
    def pop_state(self):
        """Rimuove e restituisce lo stato in cima allo stack"""
        return self.stack.pop() if self.stack else None

class EventBusGameLoop:
    """
    Implementazione del game loop basata su EventBus.
    """
    def __init__(self, game_instance=None):
        """
        Inizializza il game loop basato su eventi.
        
        Args:
            game_instance: Istanza del gioco con i componenti esistenti (opzionale)
        """
        self.running = False
        self.event_bus = EventBus.get_instance()
        
        # Inizializza o usa il gestore stati esistente
        if game_instance and hasattr(game_instance, 'stato_stack'):
            # Adatta lo stato_stack esistente
            self.state_manager = StateManager()
            self.state_manager.stack = game_instance.stato_stack
            self.game = game_instance
        else:
            self.state_manager = StateManager()
            self.game = None
        
        # Adapter per collegare gli stati esistenti all'EventBus
        self.state_adapter = StateEventAdapter(self.state_manager)
        
        # Registra sistemi di base all'EventBus
        self._register_core_systems()
        
        # Tempo frame
        self.last_time = 0
        self.target_fps = 60
        self.frame_time = 1.0 / self.target_fps
    
    def _register_core_systems(self):
        """Registra i sistemi core all'EventBus"""
        self.event_bus.on(Events.TICK, self._update_active_state)
        self.event_bus.on(Events.SHUTDOWN, self._handle_shutdown)
        # Altri sistemi...
    
    def _update_active_state(self, dt):
        """Aggiorna lo stato attivo nel game loop"""
        if self.state_manager.current_state:
            # Supporto sia per stati vecchi che nuovi
            if hasattr(self.state_manager.current_state, 'update'):
                self.state_manager.current_state.update(dt)
            else:
                # Retrocompatibilità
                self.state_manager.current_state.esegui(self.game)
    
    def _handle_shutdown(self):
        """Gestisce la richiesta di shutdown"""
        logger.info("Richiesta di shutdown ricevuta")
        self.running = False
    
    def run(self, initial_state=None):
        """
        Game loop principale basato su eventi.
        
        Args:
            initial_state: Stato iniziale da cui partire (opzionale)
        """
        self.running = True
        self.last_time = time.time()
        
        # Configura stato iniziale se fornito
        if initial_state and not self.state_manager.stack:
            self.state_manager.push_state(initial_state)
            # Emetti evento di ingresso nello stato
            self.event_bus.emit(Events.ENTER_STATE, state=initial_state)
        
        # Emetti evento di inizializzazione
        self.event_bus.emit(Events.INIT)
        
        logger.info("Avvio game loop basato su eventi")
        try:
            while self.running:
                # Calcola delta time
                current_time = time.time()
                dt = current_time - self.last_time
                self.last_time = current_time
                
                # Processa eventi della UI se il gioco ha un handler IO
                if self.game and hasattr(self.game, 'io'):
                    self.game.io.process_events()
                
                # Emetti evento TICK con delta time
                self.event_bus.emit(Events.TICK, dt=dt)
                
                # Processa tutti gli eventi in coda
                processed = self.event_bus.process(max_iter=100)
                if processed == 100:
                    logger.warning("Game loop ha processato il massimo numero di eventi, "
                                  "potrebbero essercene altri in coda. "
                                  "Considera di aumentare max_iter o ottimizzare gli handler.")
                
                # Limita il framerate
                sleep_time = max(0, self.frame_time - (time.time() - current_time))
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    # Se il frame ha richiesto più tempo del previsto, logga un warning
                    if -sleep_time > 0.01:  # Se siamo oltre 10ms in ritardo
                        logger.warning(f"Frame time exceeded: richiesti {-sleep_time*1000:.1f}ms oltre il limite")
        
        except KeyboardInterrupt:
            logger.info("Interruzione da tastiera")
        except Exception as e:
            logger.error(f"Errore nel game loop: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            logger.info("Chiusura game loop")
            # Emetti evento di shutdown per pulizia
            self.event_bus.emit_immediate(Events.SHUTDOWN)
    
    def set_target_fps(self, fps):
        """Imposta i frame al secondo desiderati"""
        self.target_fps = max(1, fps)
        self.frame_time = 1.0 / self.target_fps
    
    def shutdown(self):
        """Richiede la chiusura del game loop"""
        self.event_bus.emit(Events.SHUTDOWN)
    
    def set_game_context(self, game):
        """Imposta il contesto di gioco esistente"""
        self.game = game
        # Aggiorna anche il game context negli stati
        for state in self.state_manager.stack:
            if hasattr(state, 'set_game_context'):
                state.set_game_context(game) 