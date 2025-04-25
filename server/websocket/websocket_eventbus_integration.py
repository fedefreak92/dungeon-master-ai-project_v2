"""
Integrazione tra WebSocket e EventBus per la gestione degli eventi di gioco.

Questo modulo si occupa di configurare correttamente le integrazioni
tra il sistema di eventi (EventBus) e il sistema di comunicazione WebSocket,
consentendo il corretto scambio di informazioni tra server e client
in base allo stato corrente del gioco.
"""

import logging
from typing import Dict, Any, Optional, List, Callable
import time

from core.event_bus import EventBus, EventType, GameEvent
from server.websocket.websocket_event_bridge import WebSocketEventBridge

logger = logging.getLogger(__name__)

class WebSocketEventBusIntegration:
    """
    Classe responsabile dell'integrazione tra WebSocket e EventBus.
    
    Si occupa di:
    - Registrare e rimuovere handler per eventi in base allo stato di gioco corrente
    - Gestire il ciclo di vita degli handler eventi
    - Fornire un'interfaccia unificata per l'integrazione
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Restituisce l'istanza singleton dell'integrazione."""
        if cls._instance is None:
            cls._instance = WebSocketEventBusIntegration()
        return cls._instance
    
    def __init__(self):
        """
        Inizializza l'integrazione tra WebSocket e EventBus.
        Questo costruttore dovrebbe essere chiamato solo tramite get_instance().
        """
        if WebSocketEventBusIntegration._instance is not None:
            raise RuntimeError("WebSocketEventBusIntegration è un singleton. Usa get_instance().")
        
        self.event_bus = EventBus.get_instance()
        self.ws_bridge = WebSocketEventBridge.get_instance()
        
        # Mantiene traccia degli handler registrati per ogni stato di gioco
        # {state_name: [handler_id, ...]}
        self.state_handlers = {}
        
        logger.info("WebSocketEventBusIntegration inizializzato")
    
    def _normalize_position(self, position):
        """
        Normalizza una posizione in formato dizionario.
        
        Args:
            position: Posizione in vari formati (tuple, list, dict)
            
        Returns:
            dict: Posizione normalizzata in formato {'x': x, 'y': y}
        """
        if position is None:
            return None
            
        if isinstance(position, dict) and 'x' in position and 'y' in position:
            # Già nel formato corretto
            return position
        
        if isinstance(position, (tuple, list)) and len(position) >= 2:
            # Converti tuple/liste in dizionario
            return {'x': position[0], 'y': position[1]}
        
        # Formato non riconosciuto, ritorna come è
        return position
    
    def initialize(self):
        """
        Inizializza l'integrazione con le configurazioni di base.
        Questo metodo dovrebbe essere chiamato dopo aver configurato
        il WebSocketEventBridge con l'istanza SocketIO.
        """
        logger.info("Inizializzazione dell'integrazione WebSocket-EventBus")
        
        # Registra handler globali che esistono indipendentemente dallo stato di gioco
        self._register_global_handlers()
        
        logger.info("Integrazione WebSocket-EventBus inizializzata con successo")
    
    def _register_global_handlers(self):
        """
        Registra gli handler degli eventi che devono essere sempre attivi,
        indipendentemente dallo stato di gioco corrente.
        """
        # Eventi di autenticazione e connessione
        self.event_bus.register(EventType.PLAYER_CONNECTED, self._handle_player_connected)
        self.event_bus.register(EventType.PLAYER_DISCONNECTED, self._handle_player_disconnected)
        self.event_bus.register(EventType.PLAYER_AUTHENTICATED, self._handle_player_authenticated)
        
        # Eventi di notifica
        self.event_bus.register(EventType.NOTIFICATION, self._handle_notification)
        
        # Eventi di stato del server
        self.event_bus.register(EventType.SERVER_STATUS, self._handle_server_status)
        
        logger.info("Handler globali registrati con successo")
    
    def register_state_handlers(self, state_name: str):
        """
        Registra gli handler specifici per uno stato di gioco.
        
        Args:
            state_name: Nome dello stato di gioco (es. "MappaState")
        """
        if state_name in self.state_handlers:
            logger.warning(f"Gli handler per lo stato {state_name} sono già registrati")
            return
        
        self.state_handlers[state_name] = []
        
        # In base al nome dello stato, registra i relativi handler
        if state_name == "MappaState":
            self._register_mappa_state_handlers()
        elif state_name == "CombatState":
            self._register_combat_state_handlers()
        elif state_name == "DialogState":
            self._register_dialog_state_handlers()
        elif state_name == "InventoryState":
            self._register_inventory_state_handlers()
        else:
            logger.warning(f"Nessun handler specifico per lo stato {state_name}")
        
        logger.info(f"Handler registrati per lo stato {state_name}")
    
    def unregister_state_handlers(self, state_name: str):
        """
        Rimuove gli handler specifici per uno stato di gioco.
        
        Args:
            state_name: Nome dello stato di gioco (es. "MappaState")
        """
        if state_name not in self.state_handlers:
            logger.warning(f"Nessun handler registrato per lo stato {state_name}")
            return
        
        # Rimuovi tutti gli handler registrati per questo stato
        for handler_id in self.state_handlers[state_name]:
            self.event_bus.unregister_by_id(handler_id)
        
        # Pulisci la lista degli handler
        del self.state_handlers[state_name]
        
        logger.info(f"Handler rimossi per lo stato {state_name}")
    
    def _register_mappa_state_handlers(self):
        """
        Registra gli handler specifici per lo stato "MappaState".
        """
        # Lista per tenere traccia degli ID degli handler registrati
        handler_ids = []
        
        # Eventi di movimento e posizione
        handler_id = self.event_bus.register(EventType.PLAYER_MOVED, self._handle_player_moved)
        handler_ids.append(handler_id)
        
        handler_id = self.event_bus.register(EventType.ENTITY_MOVED, self._handle_entity_moved)
        handler_ids.append(handler_id)
        
        handler_id = self.event_bus.register(EventType.MOVEMENT_BLOCKED, self._handle_movement_blocked)
        handler_ids.append(handler_id)
        
        # Eventi di mappa
        handler_id = self.event_bus.register(EventType.MAP_CHANGED, self._handle_map_changed)
        handler_ids.append(handler_id)
        
        handler_id = self.event_bus.register(EventType.ENTITY_SPAWNED, self._handle_entity_spawned)
        handler_ids.append(handler_id)
        
        handler_id = self.event_bus.register(EventType.ENTITY_DESPAWNED, self._handle_entity_despawned)
        handler_ids.append(handler_id)
        
        # Ricevi eventi dai client
        handler_id = self.event_bus.register(EventType.PLAYER_MOVE_REQUESTED, self._handle_player_move_requested)
        handler_ids.append(handler_id)
        
        handler_id = self.event_bus.register(EventType.PLAYER_INTERACT, self._handle_player_interact)
        handler_ids.append(handler_id)
        
        # Salva gli ID degli handler per poterli rimuovere in seguito
        self.state_handlers["MappaState"] = handler_ids
        
        logger.info(f"Registrati {len(handler_ids)} handler per MappaState")
    
    def _register_combat_state_handlers(self):
        """
        Registra gli handler specifici per lo stato "CombatState".
        """
        # Lista per tenere traccia degli ID degli handler registrati
        handler_ids = []
        
        # Eventi di combattimento
        handler_id = self.event_bus.register(EventType.COMBAT_STARTED, self._handle_combat_started)
        handler_ids.append(handler_id)
        
        handler_id = self.event_bus.register(EventType.COMBAT_ENDED, self._handle_combat_ended)
        handler_ids.append(handler_id)
        
        handler_id = self.event_bus.register(EventType.COMBAT_TURN, self._handle_combat_turn)
        handler_ids.append(handler_id)
        
        handler_id = self.event_bus.register(EventType.ENTITY_ATTACKED, self._handle_entity_attacked)
        handler_ids.append(handler_id)
        
        handler_id = self.event_bus.register(EventType.ENTITY_DAMAGED, self._handle_entity_damaged)
        handler_ids.append(handler_id)
        
        handler_id = self.event_bus.register(EventType.ENTITY_HEALED, self._handle_entity_healed)
        handler_ids.append(handler_id)
        
        handler_id = self.event_bus.register(EventType.ENTITY_DIED, self._handle_entity_died)
        handler_ids.append(handler_id)
        
        # Ricevi eventi dai client
        handler_id = self.event_bus.register(EventType.COMBAT_ACTION, self._handle_combat_action)
        handler_ids.append(handler_id)
        
        # Salva gli ID degli handler per poterli rimuovere in seguito
        self.state_handlers["CombatState"] = handler_ids
        
        logger.info(f"Registrati {len(handler_ids)} handler per CombatState")
    
    def _register_dialog_state_handlers(self):
        """
        Registra gli handler specifici per lo stato "DialogState".
        """
        # Lista per tenere traccia degli ID degli handler registrati
        handler_ids = []
        
        # Eventi di dialogo
        handler_id = self.event_bus.register(EventType.DIALOG_STARTED, self._handle_dialog_started)
        handler_ids.append(handler_id)
        
        handler_id = self.event_bus.register(EventType.DIALOG_UPDATED, self._handle_dialog_updated)
        handler_ids.append(handler_id)
        
        handler_id = self.event_bus.register(EventType.DIALOG_ENDED, self._handle_dialog_ended)
        handler_ids.append(handler_id)
        
        # Ricevi eventi dai client
        handler_id = self.event_bus.register(EventType.DIALOG_RESPONSE, self._handle_dialog_response)
        handler_ids.append(handler_id)
        
        # Salva gli ID degli handler per poterli rimuovere in seguito
        self.state_handlers["DialogState"] = handler_ids
        
        logger.info(f"Registrati {len(handler_ids)} handler per DialogState")
    
    def _register_inventory_state_handlers(self):
        """
        Registra gli handler specifici per lo stato "InventoryState".
        """
        # Lista per tenere traccia degli ID degli handler registrati
        handler_ids = []
        
        # Eventi di inventario
        handler_id = self.event_bus.register(EventType.INVENTORY_CHANGED, self._handle_inventory_changed)
        handler_ids.append(handler_id)
        
        handler_id = self.event_bus.register(EventType.ITEM_ADDED, self._handle_item_added)
        handler_ids.append(handler_id)
        
        handler_id = self.event_bus.register(EventType.ITEM_REMOVED, self._handle_item_removed)
        handler_ids.append(handler_id)
        
        handler_id = self.event_bus.register(EventType.ITEM_USED, self._handle_item_used)
        handler_ids.append(handler_id)
        
        # Ricevi eventi dai client
        handler_id = self.event_bus.register(EventType.ITEM_USE_REQUESTED, self._handle_item_use_requested)
        handler_ids.append(handler_id)
        
        # Salva gli ID degli handler per poterli rimuovere in seguito
        self.state_handlers["InventoryState"] = handler_ids
        
        logger.info(f"Registrati {len(handler_ids)} handler per InventoryState")
    
    # Handler globali
    
    def _handle_player_connected(self, event: GameEvent):
        """Handler per EventType.PLAYER_CONNECTED"""
        # Non è necessario fare altro, la connessione viene già gestita
        # dal WebSocketEventBridge tramite gli handler socketio.on('connect')
        player_id = event.data.get('player_id')
        logger.debug(f"Gestito evento PLAYER_CONNECTED per il giocatore {player_id}")
    
    def _handle_player_disconnected(self, event: GameEvent):
        """Handler per EventType.PLAYER_DISCONNECTED"""
        # Non è necessario fare altro, la disconnessione viene già gestita
        # dal WebSocketEventBridge tramite gli handler socketio.on('disconnect')
        player_id = event.data.get('player_id')
        logger.debug(f"Gestito evento PLAYER_DISCONNECTED per il giocatore {player_id}")
    
    def _handle_player_authenticated(self, event: GameEvent):
        """Handler per EventType.PLAYER_AUTHENTICATED"""
        # Potrebbe essere necessario recuperare lo stato del gioco per il giocatore
        # e inviarglielo come parte dell'autenticazione
        player_id = event.data.get('player_id')
        logger.debug(f"Gestito evento PLAYER_AUTHENTICATED per il giocatore {player_id}")
    
    def _handle_notification(self, event: GameEvent):
        """Handler per EventType.NOTIFICATION"""
        # Questo evento viene già gestito direttamente dal WebSocketEventBridge
        pass
    
    def _handle_server_status(self, event: GameEvent):
        """Handler per EventType.SERVER_STATUS"""
        # Questo evento viene già gestito direttamente dal WebSocketEventBridge
        pass
    
    # Handler per MappaState
    
    def _handle_player_moved(self, event: GameEvent):
        """Handler per EventType.PLAYER_MOVED"""
        # Questo evento viene già gestito direttamente dal WebSocketEventBridge
        # nel metodo _handle_entity_moved 
        pass
    
    def _handle_entity_moved(self, event: GameEvent):
        """Handler per EventType.ENTITY_MOVED"""
        # Questo evento viene già gestito direttamente dal WebSocketEventBridge
        pass
    
    def _handle_movement_blocked(self, event: GameEvent):
        """Handler per EventType.MOVEMENT_BLOCKED"""
        player_id = event.data.get('player_id')
        reason = event.data.get('reason', 'obstacle')
        position = event.data.get('position')
        direction = event.data.get('direction')
        
        # Normalizza la posizione
        normalized_position = self._normalize_position(position)
        
        # Prepara un messaggio per il client in base al motivo del blocco
        message = "Non puoi andare in quella direzione."
        if reason == 'wall':
            message = "C'è un muro che blocca il passaggio."
        elif reason == 'water':
            message = "Non puoi attraversare l'acqua."
        elif reason == 'entity':
            message = "C'è qualcosa che blocca il passaggio."
        elif reason == 'boundary':
            message = "Hai raggiunto il confine della mappa."
        elif reason == 'npc':
            message = "C'è un personaggio che blocca il passaggio."
        
        # Invia la notifica al giocatore
        self.ws_bridge.emit_to_player(player_id, 'movement_blocked', {
            'reason': reason,
            'message': message,
            'position': normalized_position,
            'direction': direction
        })
    
    def _handle_map_changed(self, event: GameEvent):
        """Handler per EventType.MAP_CHANGED"""
        # Questo evento viene già gestito direttamente dal WebSocketEventBridge
        pass
    
    def _handle_entity_spawned(self, event: GameEvent):
        """Handler per EventType.ENTITY_SPAWNED"""
        # Questo evento viene già gestito direttamente dal WebSocketEventBridge
        pass
    
    def _handle_entity_despawned(self, event: GameEvent):
        """Handler per EventType.ENTITY_DESPAWNED"""
        # Questo evento viene già gestito direttamente dal WebSocketEventBridge
        pass
    
    def _handle_player_move_requested(self, event: GameEvent):
        """Handler per EventType.PLAYER_MOVE_REQUESTED"""
        # Questo evento viene inviato dal client e deve essere elaborato dal MappaState
        # L'evento è già nell'EventBus, ma aggiungiamo log dettagliati per debug
        player_id = event.data.get('player_id')
        direction = event.data.get('direction')
        position = event.data.get('position')
        timestamp = event.data.get('timestamp')
        
        # Normalizza la posizione
        normalized_position = self._normalize_position(position)
        
        # Log dettagliato per tracciamento
        if normalized_position:
            pos_str = f"({normalized_position['x']}, {normalized_position['y']})"
            logger.debug(f"Richiesta movimento dal giocatore {player_id} nella direzione {direction} dalla posizione {pos_str}")
        else:
            logger.debug(f"Richiesta movimento dal giocatore {player_id} nella direzione {direction}")
        
        # Se c'è un timestamp, registra il tempo di elaborazione
        if timestamp:
            delay = time.time() - timestamp
            logger.debug(f"Tempo di elaborazione richiesta movimento: {delay*1000:.2f}ms")
    
    def _handle_player_interact(self, event: GameEvent):
        """Handler per EventType.PLAYER_INTERACT"""
        # Questo evento viene inviato dal client e deve essere elaborato dal MappaState
        # Qui non è necessario fare altro perché l'evento è già nell'EventBus
        player_id = event.data.get('player_id')
        target_id = event.data.get('target_id')
        logger.debug(f"Ricevuta richiesta di interazione dal giocatore {player_id} con il target {target_id}")
    
    # Handler per CombatState
    
    def _handle_combat_started(self, event: GameEvent):
        """Handler per EventType.COMBAT_STARTED"""
        # Questo evento viene già gestito direttamente dal WebSocketEventBridge
        pass
    
    def _handle_combat_ended(self, event: GameEvent):
        """Handler per EventType.COMBAT_ENDED"""
        # Questo evento viene già gestito direttamente dal WebSocketEventBridge
        pass
    
    def _handle_combat_turn(self, event: GameEvent):
        """Handler per EventType.COMBAT_TURN"""
        # Questo evento viene già gestito direttamente dal WebSocketEventBridge
        pass
    
    def _handle_entity_attacked(self, event: GameEvent):
        """Handler per EventType.ENTITY_ATTACKED"""
        # Questo evento viene già gestito direttamente dal WebSocketEventBridge
        pass
    
    def _handle_entity_damaged(self, event: GameEvent):
        """Handler per EventType.ENTITY_DAMAGED"""
        # Questo evento viene già gestito direttamente dal WebSocketEventBridge
        pass
    
    def _handle_entity_healed(self, event: GameEvent):
        """Handler per EventType.ENTITY_HEALED"""
        # Questo evento viene già gestito direttamente dal WebSocketEventBridge
        pass
    
    def _handle_entity_died(self, event: GameEvent):
        """Handler per EventType.ENTITY_DIED"""
        # Questo evento viene già gestito direttamente dal WebSocketEventBridge
        pass
    
    def _handle_combat_action(self, event: GameEvent):
        """Handler per EventType.COMBAT_ACTION"""
        # Questo evento viene inviato dal client e deve essere elaborato dal CombatState
        # Qui non è necessario fare altro perché l'evento è già nell'EventBus
        player_id = event.data.get('player_id')
        action = event.data.get('action')
        logger.debug(f"Ricevuta azione di combattimento {action} dal giocatore {player_id}")
    
    # Handler per DialogState
    
    def _handle_dialog_started(self, event: GameEvent):
        """Handler per EventType.DIALOG_STARTED"""
        # Questo evento viene già gestito direttamente dal WebSocketEventBridge
        pass
    
    def _handle_dialog_updated(self, event: GameEvent):
        """Handler per EventType.DIALOG_UPDATED"""
        # Questo evento viene già gestito direttamente dal WebSocketEventBridge
        pass
    
    def _handle_dialog_ended(self, event: GameEvent):
        """Handler per EventType.DIALOG_ENDED"""
        # Questo evento viene già gestito direttamente dal WebSocketEventBridge
        pass
    
    def _handle_dialog_response(self, event: GameEvent):
        """Handler per EventType.DIALOG_RESPONSE"""
        # Questo evento viene inviato dal client e deve essere elaborato dal DialogState
        # Qui non è necessario fare altro perché l'evento è già nell'EventBus
        player_id = event.data.get('player_id')
        response_id = event.data.get('response_id')
        logger.debug(f"Ricevuta risposta di dialogo {response_id} dal giocatore {player_id}")
    
    # Handler per InventoryState
    
    def _handle_inventory_changed(self, event: GameEvent):
        """Handler per EventType.INVENTORY_CHANGED"""
        # Questo evento viene già gestito direttamente dal WebSocketEventBridge
        pass
    
    def _handle_item_added(self, event: GameEvent):
        """Handler per EventType.ITEM_ADDED"""
        # Questo evento viene già gestito direttamente dal WebSocketEventBridge
        pass
    
    def _handle_item_removed(self, event: GameEvent):
        """Handler per EventType.ITEM_REMOVED"""
        # Questo evento viene già gestito direttamente dal WebSocketEventBridge
        pass
    
    def _handle_item_used(self, event: GameEvent):
        """Handler per EventType.ITEM_USED"""
        # Questo evento viene già gestito direttamente dal WebSocketEventBridge
        pass
    
    def _handle_item_use_requested(self, event: GameEvent):
        """Handler per EventType.ITEM_USE_REQUESTED"""
        # Questo evento viene inviato dal client e deve essere elaborato dall'InventoryState
        # Qui non è necessario fare altro perché l'evento è già nell'EventBus
        player_id = event.data.get('player_id')
        item_id = event.data.get('item_id')
        logger.debug(f"Ricevuta richiesta di utilizzo item {item_id} dal giocatore {player_id}") 