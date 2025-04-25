"""
WebSocketEventBridge - Ponte tra EventBus e la comunicazione WebSocket.

Questo modulo implementa un bridge tra il sistema di eventi interno (EventBus)
e la comunicazione con i client tramite WebSocket (Socket.IO), consentendo
la propagazione bidirezionale degli eventi tra server e client.
"""

import logging
import json
from typing import Dict, Any, Callable, List, Optional, Union
from flask_socketio import SocketIO

# Modificare le importazioni per utilizzare importazioni relative o dirette
# Importa EventBus da event_bus e EventType da events
from core.event_bus import EventBus
from core.events import EventType

# Definiamo GameEvent localmente per non creare dipendenze
class GameEvent:
    """Classe che rappresenta un evento del gioco"""
    def __init__(self, event_type, data=None):
        self.type = event_type
        self.data = data or {}
    
    def __str__(self):
        return f"GameEvent(type={self.type}, data={self.data})"

logger = logging.getLogger(__name__)

class WebSocketEventBridge:
    """
    Bridge tra il sistema EventBus e la comunicazione WebSocket.
    
    Questa classe singleton fornisce un'infrastruttura per collegare 
    gli eventi interni del gioco (generati dall'EventBus) ai client
    connessi tramite WebSocket, e viceversa.
    """
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Restituisce l'istanza singleton del bridge."""
        if cls._instance is None:
            cls._instance = WebSocketEventBridge()
        return cls._instance
    
    def __init__(self):
        """
        Inizializza il bridge.
        Questo costruttore dovrebbe essere chiamato solo tramite get_instance().
        """
        if WebSocketEventBridge._instance is not None:
            raise RuntimeError("WebSocketEventBridge è un singleton. Usa get_instance().")
        
        self.socketio = None
        self.event_bus = EventBus.get_instance()
        self.connected_clients = {}  # Dictionary di sid -> player_id
        self.player_sessions = {}    # Dictionary di player_id -> sid
        self._handlers_initialized = False
        self._ws_event_handlers = {}  # Dictionary per gestori di eventi WebSocket
        
        # Registrazione degli handler EventBus
        self._register_eventbus_handlers()
        
        logger.info("WebSocketEventBridge inizializzato")
    
    def on(self, event_name: str, handler: Callable):
        """
        Registra un handler per un evento WebSocket specifico.
        Simile a event_bus.on() ma per eventi WebSocket.
        
        Args:
            event_name: Nome dell'evento WebSocket
            handler: Funzione di callback per gestire l'evento
        
        Returns:
            Callable: Funzione per annullare la registrazione
        """
        if event_name not in self._ws_event_handlers:
            self._ws_event_handlers[event_name] = []
        
        self._ws_event_handlers[event_name].append(handler)
        
        # Restituisce una funzione per cancellare la registrazione
        def unregister():
            if event_name in self._ws_event_handlers and handler in self._ws_event_handlers[event_name]:
                self._ws_event_handlers[event_name].remove(handler)
                if not self._ws_event_handlers[event_name]:
                    del self._ws_event_handlers[event_name]
                return True
            return False
        
        return unregister
    
    def handle_ws_event(self, event_name: str, client_id: str, data: Dict[str, Any]):
        """
        Gestisce un evento WebSocket ricevuto.
        
        Args:
            event_name: Nome dell'evento WebSocket
            client_id: ID del client che ha inviato l'evento
            data: Dati dell'evento
        
        Returns:
            bool: True se l'evento è stato gestito, False altrimenti
        """
        if event_name not in self._ws_event_handlers:
            logger.warning(f"Nessun handler registrato per l'evento WebSocket: {event_name}")
            return False
        
        handled = False
        for handler in self._ws_event_handlers[event_name]:
            try:
                handler(client_id, data)
                handled = True
            except Exception as e:
                logger.error(f"Errore durante la gestione dell'evento WebSocket {event_name}: {e}")
        
        return handled
    
    def set_socketio(self, socketio: SocketIO):
        """
        Imposta l'istanza SocketIO da utilizzare per le comunicazioni.
        
        Args:
            socketio: L'istanza SocketIO dell'applicazione Flask
        """
        self.socketio = socketio
        logger.info("Istanza SocketIO impostata nel WebSocketEventBridge")
        
        # Opzionalmente, inizializza gli handler qui se non sono già stati inizializzati
        if hasattr(self, '_handlers_initialized') and self._handlers_initialized:
            logger.info("Gli handler WebSocket sono già stati inizializzati")
        else:
            try:
                self.init_websocket_handlers()
                self._handlers_initialized = True
            except Exception as e:
                logger.error(f"Errore durante l'inizializzazione degli handler WebSocket: {e}")
    
    def init_websocket_handlers(self):
        """
        Inizializza gli handler per gli eventi WebSocket in arrivo dai client.
        Deve essere chiamato dopo aver impostato l'istanza socketio.
        """
        if self.socketio is None:
            raise RuntimeError("SocketIO non impostato. Chiama set_socketio prima.")
        
        # Handler per la connessione di un client
        @self.socketio.on('connect')
        def handle_connect():
            sid = self._get_current_sid()
            logger.info(f"Nuova connessione WebSocket: {sid}")
            # Il player_id verrà impostato durante l'autenticazione
        
        # Handler per la disconnessione di un client
        @self.socketio.on('disconnect')
        def handle_disconnect():
            sid = self._get_current_sid()
            logger.info(f"Disconnessione WebSocket: {sid}")
            
            # Trova il player_id associato a questo sid
            player_id = None
            for pid, session_sid in self.player_sessions.items():
                if session_sid == sid:
                    player_id = pid
                    break
            
            if player_id:
                # Emetti un evento di disconnessione al sistema EventBus
                self.event_bus.emit(EventType.PLAYER_LEAVE, 
                                   player_id=player_id,
                                   sid=sid)
                
                # Rimuovi il client dalle strutture dati
                if sid in self.connected_clients:
                    del self.connected_clients[sid]
                if player_id in self.player_sessions:
                    del self.player_sessions[player_id]
        
        # Handler generico per tutti gli eventi registrati tramite on()
        @self.socketio.on('*')
        def handle_any_event(event_name, data):
            if not event_name:
                return
                
            sid = self._get_current_sid()
            
            # Gestisci l'evento utilizzando gli handler registrati
            self.handle_ws_event(event_name, sid, data)
        
        # Registra handler per eventi specifici
        for event_name in self._ws_event_handlers.keys():
            # Crea una closure per ogni evento
            def create_handler(name):
                @self.socketio.on(name)
                def event_handler(data):
                    sid = self._get_current_sid()
                    self.handle_ws_event(name, sid, data)
            
            create_handler(event_name)
        
        logger.info("Handler WebSocket inizializzati con successo")
    
    def _register_eventbus_handlers(self):
        """
        Registra gli handler per gli eventi EventBus che devono essere propagati
        ai client tramite WebSocket.
        """
        # Gestione dei player
        self.event_bus.on(EventType.PLAYER_JOIN, self._handle_player_joined)
        self.event_bus.on(EventType.PLAYER_LEAVE, self._handle_player_left)
        self.event_bus.on(EventType.PLAYER_MOVE, self._handle_entity_moved)
        
        # Gestione della mappa
        self.event_bus.on(EventType.MAP_CHANGE, self._handle_map_changed)
        self.event_bus.on(EventType.ENTITY_SPAWN, self._handle_entity_spawned)
        self.event_bus.on(EventType.ENTITY_DESPAWN, self._handle_entity_despawned)
        self.event_bus.on(EventType.ENTITY_MOVED, self._handle_entity_moved)
        self.event_bus.on(EventType.MOVEMENT_BLOCKED, self._handle_movement_blocked)
        self.event_bus.on(EventType.UI_UPDATE, self._handle_ui_update)
        
        # Gestione del combattimento
        self.event_bus.on(EventType.COMBAT_START, self._handle_combat_started)
        self.event_bus.on(EventType.COMBAT_END, self._handle_combat_ended)
        self.event_bus.on(EventType.COMBAT_TURN, self._handle_combat_turn)
        self.event_bus.on(EventType.DAMAGE_DEALT, self._handle_entity_attacked)
        self.event_bus.on(EventType.DAMAGE_TAKEN, self._handle_entity_damaged)
        
        # Eventi base sufficienti per avviare il server
        # Altri eventi possono essere aggiunti in seguito
        
        logger.info("Handler EventBus registrati con successo")
    
    def _get_current_sid(self):
        """
        Ottiene l'ID della sessione corrente (request specific).
        
        Returns:
            str: L'ID della sessione WebSocket
        """
        from flask import request
        return request.sid
    
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
    
    def emit_to_player(self, player_id: str, event_name: str, data: Dict[str, Any]):
        """
        Emette un evento WebSocket a un giocatore specifico.
        
        Args:
            player_id: ID del giocatore
            event_name: Nome dell'evento da emettere
            data: Dati dell'evento
        
        Returns:
            bool: True se l'evento è stato emesso, False altrimenti
        """
        if self.socketio is None:
            logger.error("SocketIO non impostato. Impossibile emettere eventi.")
            return False
        
        # Trova la sessione del giocatore
        sid = self.player_sessions.get(player_id)
        if not sid:
            logger.warning(f"Impossibile emettere evento a giocatore non connesso: {player_id}")
            return False
        
        # Emetti l'evento alla sessione specifica
        try:
            self.socketio.emit(event_name, data, room=sid)
            return True
        except Exception as e:
            logger.error(f"Errore durante l'emissione dell'evento {event_name} a {player_id}: {e}")
            return False
    
    def emit_to_all(self, event_name: str, data: Dict[str, Any]):
        """
        Emette un evento WebSocket a tutti i client connessi.
        
        Args:
            event_name: Nome dell'evento da emettere
            data: Dati dell'evento
        
        Returns:
            bool: True se l'evento è stato emesso, False altrimenti
        """
        if self.socketio is None:
            logger.error("SocketIO non impostato. Impossibile emettere eventi.")
            return False
        
        try:
            self.socketio.emit(event_name, data)
            return True
        except Exception as e:
            logger.error(f"Errore durante l'emissione dell'evento {event_name} a tutti: {e}")
            return False
    
    def emit_to_room(self, room: str, event_name: str, data: Dict[str, Any]):
        """
        Emette un evento WebSocket a una stanza specifica.
        
        Args:
            room: Nome della stanza
            event_name: Nome dell'evento da emettere
            data: Dati dell'evento
        
        Returns:
            bool: True se l'evento è stato emesso, False altrimenti
        """
        if self.socketio is None:
            logger.error("SocketIO non impostato. Impossibile emettere eventi.")
            return False
        
        try:
            self.socketio.emit(event_name, data, room=room)
            return True
        except Exception as e:
            logger.error(f"Errore durante l'emissione dell'evento {event_name} alla stanza {room}: {e}")
            return False
    
    # Handler per gli eventi EventBus da propagare ai client
    
    def _handle_player_joined(self, event: GameEvent):
        """Handler per EventType.PLAYER_JOINED"""
        player_id = event.data.get('player_id')
        player_data = event.data.get('player_data', {})
        
        # Notifica tutti i client che un nuovo giocatore è entrato
        self.emit_to_all('player_joined', {
            'player_id': player_id,
            'player_data': player_data
        })
    
    def _handle_player_left(self, event: GameEvent):
        """Handler per EventType.PLAYER_LEFT"""
        player_id = event.data.get('player_id')
        
        # Notifica tutti i client che un giocatore è uscito
        self.emit_to_all('player_left', {
            'player_id': player_id
        })
    
    def _handle_entity_moved(self, event: GameEvent):
        """Handler per EventType.ENTITY_MOVED e PLAYER_MOVED"""
        entity_id = event.data.get('entity_id')
        entity_type = event.data.get('entity_type')
        
        # Estrai posizione supportando diversi formati
        position = event.data.get('position')
        from_position = event.data.get('from_position')
        to_position = position
        
        # Normalizza la posizione
        normalized_position = self._normalize_position(position)
        normalized_from_position = self._normalize_position(from_position)
        normalized_to_position = self._normalize_position(to_position)
        
        # Costruisci il payload con supporto per posizioni precedenti se disponibili
        payload = {
            'entity_id': entity_id,
            'entity_type': entity_type,
            'position': normalized_position
        }
        
        # Aggiungi informazioni sulla posizione precedente se disponibili
        if normalized_from_position:
            payload['from_position'] = normalized_from_position
            payload['to_position'] = normalized_to_position
        
        # Notifica tutti i client che un'entità si è mossa
        self.emit_to_all('entity_moved', payload)
    
    def _handle_player_stats_changed(self, event: GameEvent):
        """Handler per EventType.PLAYER_STATS_CHANGED"""
        player_id = event.data.get('player_id')
        stats = event.data.get('stats', {})
        
        # Notifica il client specifico del cambio stat
        self.emit_to_player(player_id, 'player_stats_changed', {
            'player_id': player_id,
            'stats': stats
        })
    
    def _handle_map_changed(self, event: GameEvent):
        """Handler per EventType.MAP_CHANGED"""
        map_id = event.data.get('map_id')
        players_affected = event.data.get('players_affected', [])
        
        # Se ci sono giocatori specifici coinvolti nel cambio mappa
        if players_affected:
            for player_id in players_affected:
                # Invia solo i dati rilevanti per questo giocatore
                player_map_data = event.data.get('player_map_data', {}).get(player_id, {})
                
                self.emit_to_player(player_id, 'map_changed', {
                    'map_id': map_id,
                    'map_data': player_map_data or event.data.get('map_data', {})
                })
        else:
            # Notifica tutti i client del cambio mappa
            self.emit_to_all('map_changed', {
                'map_id': map_id,
                'map_data': event.data.get('map_data', {})
            })
    
    def _handle_entity_spawned(self, event: GameEvent):
        """Handler per EventType.ENTITY_SPAWNED"""
        entity_id = event.data.get('entity_id')
        entity_type = event.data.get('entity_type')
        position = event.data.get('position')
        properties = event.data.get('properties', {})
        
        # Normalizza la posizione
        normalized_position = self._normalize_position(position)
        
        # Notifica tutti i client che un'entità è comparsa
        self.emit_to_all('entity_spawned', {
            'entity_id': entity_id,
            'entity_type': entity_type,
            'position': normalized_position,
            'properties': properties
        })
    
    def _handle_entity_despawned(self, event: GameEvent):
        """Handler per EventType.ENTITY_DESPAWNED"""
        entity_id = event.data.get('entity_id')
        
        # Notifica tutti i client che un'entità è scomparsa
        self.emit_to_all('entity_despawned', {
            'entity_id': entity_id
        })
    
    def _handle_movement_blocked(self, event: GameEvent):
        """Handler per EventType.MOVEMENT_BLOCKED"""
        player_id = event.data.get('player_id')
        reason = event.data.get('reason', 'obstacle')
        position = event.data.get('position')
        direction = event.data.get('direction')
        
        # Normalizza la posizione
        normalized_position = self._normalize_position(position)
        
        # Prepara un messaggio appropriato in base al motivo del blocco
        message = "Non puoi andare in quella direzione."
        if reason == 'wall':
            message = "C'è un muro che blocca il passaggio."
        elif reason == 'water':
            message = "Non puoi attraversare l'acqua."
        elif reason == 'entity':
            message = "C'è qualcosa che blocca il passaggio."
        elif reason == 'boundary':
            message = "Hai raggiunto il confine della mappa."
        
        # Notifica il giocatore specifico
        self.emit_to_player(player_id, 'movement_blocked', {
            'player_id': player_id,
            'reason': reason,
            'message': message,
            'position': normalized_position,
            'direction': direction
        })
    
    def _handle_combat_started(self, event: GameEvent):
        """Handler per EventType.COMBAT_STARTED"""
        combat_id = event.data.get('combat_id')
        participants = event.data.get('participants', [])
        
        # Notifica tutti i partecipanti del combattimento
        for participant in participants:
            player_id = participant.get('id')
            if player_id and participant.get('type') == 'player':
                self.emit_to_player(player_id, 'combat_started', {
                    'combat_id': combat_id,
                    'participants': participants,
                    'player_data': participant
                })
    
    def _handle_combat_ended(self, event: GameEvent):
        """Handler per EventType.COMBAT_ENDED"""
        combat_id = event.data.get('combat_id')
        winners = event.data.get('winners', [])
        losers = event.data.get('losers', [])
        rewards = event.data.get('rewards', {})
        
        # Notifica tutti i partecipanti del combattimento
        for player_id in event.data.get('player_ids', []):
            player_rewards = rewards.get(player_id, {})
            self.emit_to_player(player_id, 'combat_ended', {
                'combat_id': combat_id,
                'winners': winners,
                'losers': losers,
                'rewards': player_rewards
            })
    
    def _handle_combat_turn(self, event: GameEvent):
        """Handler per EventType.COMBAT_TURN"""
        combat_id = event.data.get('combat_id')
        entity_id = event.data.get('entity_id')
        actions = event.data.get('available_actions', [])
        
        # Notifica i giocatori coinvolti
        for player_id in event.data.get('player_ids', []):
            is_player_turn = entity_id == player_id
            
            self.emit_to_player(player_id, 'combat_turn', {
                'combat_id': combat_id,
                'entity_id': entity_id,
                'is_your_turn': is_player_turn,
                'available_actions': actions if is_player_turn else []
            })
    
    def _handle_entity_attacked(self, event: GameEvent):
        """Handler per EventType.ENTITY_ATTACKED"""
        attacker_id = event.data.get('attacker_id')
        target_id = event.data.get('target_id')
        attack_data = event.data.get('attack_data', {})
        
        # Notifica i giocatori coinvolti
        for player_id in event.data.get('player_ids', []):
            self.emit_to_player(player_id, 'entity_attacked', {
                'attacker_id': attacker_id,
                'target_id': target_id,
                'attack_data': attack_data
            })
    
    def _handle_entity_damaged(self, event: GameEvent):
        """Handler per EventType.ENTITY_DAMAGED"""
        entity_id = event.data.get('entity_id')
        damage = event.data.get('damage')
        source_id = event.data.get('source_id')
        
        # Notifica tutti i client del danno
        self.emit_to_all('entity_damaged', {
            'entity_id': entity_id,
            'damage': damage,
            'source_id': source_id,
            'current_hp': event.data.get('current_hp')
        })
    
    def _handle_entity_healed(self, event: GameEvent):
        """Handler per EventType.ENTITY_HEALED"""
        entity_id = event.data.get('entity_id')
        healing = event.data.get('healing')
        source_id = event.data.get('source_id')
        
        # Notifica tutti i client della guarigione
        self.emit_to_all('entity_healed', {
            'entity_id': entity_id,
            'healing': healing,
            'source_id': source_id,
            'current_hp': event.data.get('current_hp')
        })
    
    def _handle_entity_died(self, event: GameEvent):
        """Handler per EventType.ENTITY_DIED"""
        entity_id = event.data.get('entity_id')
        
        # Notifica tutti i client della morte
        self.emit_to_all('entity_died', {
            'entity_id': entity_id
        })
    
    def _handle_dialog_started(self, event: GameEvent):
        """Handler per EventType.DIALOG_STARTED"""
        player_id = event.data.get('player_id')
        dialog_id = event.data.get('dialog_id')
        npc_id = event.data.get('npc_id')
        dialog_data = event.data.get('dialog_data', {})
        
        # Notifica il giocatore coinvolto nel dialogo
        self.emit_to_player(player_id, 'dialog_started', {
            'dialog_id': dialog_id,
            'npc_id': npc_id,
            'dialog_data': dialog_data
        })
    
    def _handle_dialog_ended(self, event: GameEvent):
        """Handler per EventType.DIALOG_ENDED"""
        player_id = event.data.get('player_id')
        dialog_id = event.data.get('dialog_id')
        
        # Notifica il giocatore della fine del dialogo
        self.emit_to_player(player_id, 'dialog_ended', {
            'dialog_id': dialog_id
        })
    
    def _handle_dialog_updated(self, event: GameEvent):
        """Handler per EventType.DIALOG_UPDATED"""
        player_id = event.data.get('player_id')
        dialog_id = event.data.get('dialog_id')
        dialog_data = event.data.get('dialog_data', {})
        
        # Notifica il giocatore dell'aggiornamento del dialogo
        self.emit_to_player(player_id, 'dialog_updated', {
            'dialog_id': dialog_id,
            'dialog_data': dialog_data
        })
    
    def _handle_inventory_changed(self, event: GameEvent):
        """Handler per EventType.INVENTORY_CHANGED"""
        player_id = event.data.get('player_id')
        inventory_data = event.data.get('inventory_data', {})
        
        # Notifica il giocatore del cambio inventario
        self.emit_to_player(player_id, 'inventory_changed', {
            'inventory_data': inventory_data
        })
    
    def _handle_item_used(self, event: GameEvent):
        """Handler per EventType.ITEM_USED"""
        player_id = event.data.get('player_id')
        item_id = event.data.get('item_id')
        effects = event.data.get('effects', [])
        
        # Notifica il giocatore dell'uso dell'item
        self.emit_to_player(player_id, 'item_used', {
            'item_id': item_id,
            'effects': effects
        })
    
    def _handle_item_added(self, event: GameEvent):
        """Handler per EventType.ITEM_ADDED"""
        player_id = event.data.get('player_id')
        item_id = event.data.get('item_id')
        item_data = event.data.get('item_data', {})
        
        # Notifica il giocatore dell'aggiunta dell'item
        self.emit_to_player(player_id, 'item_added', {
            'item_id': item_id,
            'item_data': item_data
        })
    
    def _handle_item_removed(self, event: GameEvent):
        """Handler per EventType.ITEM_REMOVED"""
        player_id = event.data.get('player_id')
        item_id = event.data.get('item_id')
        
        # Notifica il giocatore della rimozione dell'item
        self.emit_to_player(player_id, 'item_removed', {
            'item_id': item_id
        })
    
    def _handle_notification(self, event: GameEvent):
        """Handler per EventType.NOTIFICATION"""
        player_id = event.data.get('player_id')
        message = event.data.get('message')
        notification_type = event.data.get('type', 'info')
        
        if player_id:
            # Notifica specifica per un giocatore
            self.emit_to_player(player_id, 'notification', {
                'message': message,
                'type': notification_type
            })
        else:
            # Notifica globale
            self.emit_to_all('notification', {
                'message': message,
                'type': notification_type
            })
    
    def _handle_game_state_changed(self, event: GameEvent):
        """Handler per EventType.GAME_STATE_CHANGED"""
        state_type = event.data.get('state_type')
        state_data = event.data.get('state_data', {})
        players_affected = event.data.get('players_affected', [])
        
        if players_affected:
            # Notifica solo i giocatori specifici
            for player_id in players_affected:
                self.emit_to_player(player_id, 'game_state_changed', {
                    'state_type': state_type,
                    'state_data': state_data
                })
        else:
            # Notifica tutti
            self.emit_to_all('game_state_changed', {
                'state_type': state_type,
                'state_data': state_data
            })
    
    def _handle_game_state_response(self, event: GameEvent):
        """Handler per EventType.GAME_STATE_RESPONSE"""
        player_id = event.data.get('player_id')
        state_type = event.data.get('state_type')
        state_data = event.data.get('state_data', {})
        
        # Notifica il giocatore della risposta allo stato
        self.emit_to_player(player_id, 'game_state_response', {
            'state_type': state_type,
            'state_data': state_data
        })
    
    def _handle_server_status(self, event: GameEvent):
        """Handler per EventType.SERVER_STATUS"""
        status = event.data.get('status')
        message = event.data.get('message')
        
        # Notifica tutti i client dello stato del server
        self.emit_to_all('server_status', {
            'status': status,
            'message': message
        })
        
    def _handle_ui_update(self, event: GameEvent):
        """Handler per EventType.UI_UPDATE"""
        # Estrai informazioni base dall'evento
        player_id = event.data.get('player_id')
        element = event.data.get('element')
        data = event.data.get('data', {})
        
        # Se è specificato un player_id, invia solo a quel giocatore
        if player_id:
            self.emit_to_player(player_id, 'ui_update', {
                'element': element,
                'data': data
            })
        else:
            # Altrimenti invia a tutti
            self.emit_to_all('ui_update', {
                'element': element,
                'data': data
            }) 