"""
Gestore WebSocket per la comunicazione in tempo reale tra client e server.
"""

import logging
import json
import time
import asyncio
from flask_socketio import SocketIO, emit, disconnect
from flask import current_app, request, g
from datetime import datetime, timedelta

# Import EventBus e tipi di eventi
from core.event_bus import EventBus
import core.events as Events

# Import per recuperare la sessione e quindi il giocatore
from server.utils.session import get_session # ASSUMENDO CHE QUESTO SIA IL PERCORSO CORRETTO
from entities.giocatore import Giocatore # <<< AGGIUNTO IMPORT

# Rimuovi l'importazione diretta per evitare l'importazione circolare
# from server.websocket.websocket_event_bridge import WebSocketEventBridge

# Configura logger
logger = logging.getLogger(__name__)

# Classe per gestire le connessioni WebSocket
class WebSocketManager:
    def __init__(self, app=None, socketio=None):
        # Se non viene passato un socketio già creato, crearne uno nuovo
        if socketio is None:
            # Configura parametri ottimizzati per WebSocket
            ping_timeout = 60000   # 60 secondi, aumentato per evitare disconnessioni premature
            ping_interval = 25000  # 25 secondi, intervallo ottimale per bilanciare responsività e overhead
            cors_allowed = ["http://localhost:3000", "http://localhost:5000", "http://127.0.0.1:3000", "http://127.0.0.1:5000"]
            
            self.socketio = SocketIO(
                app, 
                cors_allowed_origins=cors_allowed, 
                async_mode='eventlet',
                ping_timeout=ping_timeout,
                ping_interval=ping_interval,
                always_connect=True,
                manage_session=False,
                transports=['websocket', 'polling'],  # Preferisci WebSocket, fallback su polling
                logger=True if app and app.debug else False
            )
            logger.info(f"Creata nuova istanza SocketIO con configurazione: ping_timeout={ping_timeout/1000}s, ping_interval={ping_interval/1000}s")
        else:
            self.socketio = socketio
            logger.info("Utilizzata istanza SocketIO esistente")
            
        self.active_connections = 0
        self.connection_map = {}  # socket_id -> session_id
        self.state_versions = {}  # session_id -> versione stato
        self.connection_stats = {}  # socket_id -> statistiche connessione
        
        # Configura EventBus
        self.event_bus = EventBus.get_instance()
        
        # Importa WebSocketEventBridge solo quando necessario (lazy loading)
        # per evitare l'importazione circolare
        from server.websocket.websocket_event_bridge import WebSocketEventBridge
        self.ws_bridge = WebSocketEventBridge.get_instance()
        
        # Registra i gestori di eventi Socket.IO e EventBus
        self._register_handlers()
        self._register_event_handlers()
    
    def _register_event_handlers(self):
        """Registra gli handler degli eventi di EventBus"""
        # Eventi di gioco
        self.event_bus.on(Events.PLAYER_MOVE, self._handle_player_move)
        self.event_bus.on(Events.PLAYER_POSITION_UPDATED, self._handle_player_position_updated)
        self.event_bus.on(Events.MAP_CHANGE, self._handle_map_change)
        self.event_bus.on(Events.UI_UPDATE, self._handle_ui_update)
        self.event_bus.on(Events.UI_DIALOG_OPEN, self._handle_dialog_open)
        self.event_bus.on(Events.UI_DIALOG_CLOSE, self._handle_dialog_close)
        
        # Eventi di autenticazione
        self.event_bus.on(Events.PLAYER_LOGIN, self._handle_player_login)
        self.event_bus.on(Events.PLAYER_LOGOUT, self._handle_player_logout)
        
        # Eventi di stato
        self.event_bus.on(Events.CHANGE_STATE, self._handle_change_state)
        self.event_bus.on(Events.PUSH_STATE, self._handle_push_state)
        self.event_bus.on(Events.POP_STATE, self._handle_pop_state)
        
        logger.info("EventBus handlers registrati per WebSocketManager")

    def _register_handlers(self):
        """Registra gli handler Socket.IO"""
        @self.socketio.on('connect')
        def handle_connect():
            sid = request.sid
            self.active_connections += 1
            
            # Ottieni informazioni sulla connessione in modo più sicuro
            transport = 'polling'  # default
            user_agent = 'Unknown'
            
            # Prova a recuperare informazioni aggiuntive se disponibili
            try:
                if request.environ and 'HTTP_UPGRADE' in request.environ:
                    transport = request.environ['HTTP_UPGRADE']
                if hasattr(request, 'user_agent') and request.user_agent:
                    user_agent = str(request.user_agent)
                elif request.environ and 'HTTP_USER_AGENT' in request.environ:
                    user_agent = request.environ['HTTP_USER_AGENT']
            except Exception as e:
                logger.warning(f"Impossibile ottenere dettagli connessione: {e}")
            
            logger.info(f"Nuova connessione WebSocket: {sid}. Transport: {transport}, Active: {self.active_connections}")
            
            # Inizializza le statistiche di connessione
            self.connection_stats[sid] = {
                'connect_time': time.time(),
                'last_activity': time.time(),
                'packets_received': 0,
                'packets_sent': 0,
                'ping_times': [],
                'avg_latency': 0,
                'transport': transport,
                'user_agent': user_agent
            }
            
            # Emetti evento al bus
            self.event_bus.emit(Events.NETWORK_CONNECT, 
                               socket_id=sid,
                               client_info=user_agent)
            
            # Invia info sul server (versione socketio, ecc)
            # Questo aiuta il client a gestire la connessione
            emit('server_info', {
                'socket_id': sid,
                'time': time.time()
            })
            
            return True
            
        @self.socketio.on('disconnect')
        def handle_disconnect(sid=None):
            """
            Gestisce la disconnessione di un client WebSocket
            """
            # Se sid non è specificato, prova a ottenerlo dalla request
            if sid is None and hasattr(request, 'sid'):
                sid = request.sid
            
            logger.info(f"Client WebSocket disconnesso: {sid}")
            
            # Ottieni info sul client prima di rimuoverlo
            client_info = connection.get_client_info(sid)
            
            self.active_connections = max(0, self.active_connections - 1)
            
            # Rimuovi dalla mappa di connessione
            session_id = self.connection_map.pop(sid, None)
            
            # IMPORTANTE: Rimuovi anche da socket_sessioni per compatibilità con game_events.py
            from server.utils.session import socket_sessioni
            if sid in socket_sessioni:
                del socket_sessioni[sid]
                logger.info(f"[DISCONNECT] Client {sid} rimosso da socket_sessioni")
            
            # Rimuovi statistiche connessione
            if sid in self.connection_stats:
                # Calcola durata sessione
                start_time = self.connection_stats[sid].get('connect_time', time.time())
                session_duration = time.time() - start_time
                
                logger.info(f"Sessione WebSocket {sid} durata: {session_duration:.2f}s, "
                          f"latenza media: {self.connection_stats[sid].get('avg_latency', 0):.2f}ms")
                
                # Rimuovi statistiche
                del self.connection_stats[sid]
            
            logger.info(f"Disconnessione WebSocket: {sid}. Connessioni attive: {self.active_connections}")
            
            # Emetti evento al bus
            self.event_bus.emit(Events.NETWORK_DISCONNECT, 
                               socket_id=sid,
                               session_id=session_id)
                
        @self.socketio.on('ping_test')
        def handle_ping_test(data):
            """
            Gestisce richieste ping/pong per misurare la latenza
            
            Args:
                data (dict): Dati opzionali per il test ping
            """
            sid = request.sid
            
            # Aggiorna il timestamp dell'ultima attività
            if sid in self.connection_stats:
                self.connection_stats[sid]['last_activity'] = time.time()
                self.connection_stats[sid]['packets_received'] += 1
            
            # Risponde immediatamente senza elaborazione per misurare la latenza
            # Il callback lato client calcolerà round-trip time
            return {}  # Risposta vuota è sufficiente per callback

        @self.socketio.on('connection_stats')
        def handle_connection_stats(data):
            """
            Riceve statistiche di connessione dal client
            
            Args:
                data (dict): Statistiche di connessione
            """
            sid = request.sid
            
            if sid in self.connection_stats and isinstance(data, dict):
                # Aggiorna statistiche con dati dal client
                client_latency = data.get('latency')
                if client_latency is not None:
                    # Aggiungi alla lista delle latenze
                    self.connection_stats[sid]['ping_times'].append(client_latency)
                    
                    # Mantieni solo gli ultimi 10 valori
                    if len(self.connection_stats[sid]['ping_times']) > 10:
                        self.connection_stats[sid]['ping_times'].pop(0)
                    
                    # Calcola la media
                    ping_times = self.connection_stats[sid]['ping_times']
                    if ping_times:
                        self.connection_stats[sid]['avg_latency'] = sum(ping_times) / len(ping_times)
            
            # Aggiorna ultimo timestamp attività
            if sid in self.connection_stats:
                self.connection_stats[sid]['last_activity'] = time.time()
                self.connection_stats[sid]['packets_received'] += 1
            
            return {'status': 'ok'}

        @self.socketio.on('authenticate')
        def handle_authenticate(data):
            """
            Gestisce l'autenticazione di un client WebSocket
            
            Args:
                data (dict): Contiene token e altri dati di autenticazione
            """
            sid = request.sid
            logger.info(f"[AUTH_DEBUG] Ricevuto evento 'authenticate' da socket_id: {sid}, data: {data}")
            
            if not isinstance(data, dict) or 'token' not in data:
                logger.warning(f"[AUTH_DEBUG] Autenticazione fallita per {sid}: Token mancante o formato dati errato.")
                emit('auth_error', {'message': 'Token mancante o formato dati errato'})
                disconnect()
                return

            token = data['token']
            client_id = data.get('client_id')
            
            try:
                # Usa il token ricevuto come session_id
                session_id_from_token = token
                logger.info(f"[AUTH_DEBUG] Per {sid}: Token ricevuto utilizzato come session_id: {session_id_from_token}")

                # Qui potresti aggiungere una logica per validare session_id_from_token
                # consultando il SessionManager, ma per ora lo usiamo direttamente.
                # Esempio:
                # from server.utils.session_manager import SessionManager # o il nome corretto del tuo gestore sessioni
                # if not SessionManager.is_valid_session(session_id_from_token):
                #     logger.warning(f"[AUTH_DEBUG] Autenticazione fallita per {sid}: Session ID '{session_id_from_token}' non valido o scaduto.")
                #     emit('auth_error', {'message': 'Session ID non valido o scaduto'})
                #     disconnect()
                #     return

                # Aggiungi alla mappa delle connessioni
                self.connection_map[sid] = session_id_from_token # Usa sid qui, non socket_id che potrebbe essere diverso nel logger
                logger.info(f"[AUTH_DEBUG] Per {sid}: connection_map aggiornata: {self.connection_map}")
                
                # IMPORTANTE: Sincronizza anche socket_sessioni per compatibilità con game_events.py
                from server.utils.session import socket_sessioni
                socket_sessioni[sid] = session_id_from_token
                logger.info(f"[AUTH_DEBUG] Per {sid}: socket_sessioni aggiornata per compatibilità con game_events.py")
                
                # Invia risposta al client
                self.socketio.emit('authenticated', {
                    'session_id': session_id_from_token,
                    'success': True
                }, room=sid)
                logger.info(f"[AUTH_DEBUG] Evento 'authenticated' inviato a {sid} con session_id: {session_id_from_token}")
                
                logger.info(f"Autenticazione riuscita: socket_id={sid}, session_id={session_id_from_token}")

                # Emetti evento al bus con il session_id corretto
                # Questo evento _handle_player_login in ascolto su EventBus.PLAYER_LOGIN non è corretto e causa un loop.
                # L'evento PLAYER_LOGIN dovrebbe essere gestito da un'altra parte del sistema (es. SessionManager o GameManager)
                # dopo che l'autenticazione WebSocket è confermata qui.
                # Per ora, commento l'emissione dell'evento da qui per evitare loop, 
                # ma la logica di gestione post-login andrà rivista.
                # self.event_bus.emit(Events.PLAYER_LOGIN, 
                #                    token=token, 
                #                    session_id=session_id_from_token, 
                #                    socket_id=sid,
                #                    client_id=client_id)
                
            except Exception as e:
                logger.error(f"[AUTH_DEBUG] Errore durante emissione Events.PLAYER_LOGIN per {sid}: {str(e)}")
                emit('auth_error', {'message': f'Errore di autenticazione: {str(e)}'})
                disconnect()
                
        @self.socketio.on('refresh_token')
        def handle_refresh_token(data):
            """
            Gestisce il refresh del token di autenticazione
            
            Args:
                data (dict): Contiene il token di refresh
            """
            sid = request.sid
            
            if not isinstance(data, dict) or 'refresh_token' not in data:
                emit('auth_error', {'message': 'Token di refresh mancante'})
                return
                
            refresh_token = data['refresh_token']
            
            try:
                # Converti il processo in eventi
                self.event_bus.emit(Events.TOKEN_REFRESH, 
                                   refresh_token=refresh_token,
                                   socket_id=sid)
                
                # Nota: la risposta sarà gestita dall'handler dell'evento TOKEN_REFRESH
            except Exception as e:
                logger.error(f"Errore refresh token: {str(e)}")
                emit('auth_error', {'message': f'Errore durante il refresh: {str(e)}'})
            
        @self.socketio.on('player_action')
        def handle_player_action(data):
            """
            Gestisce le azioni del giocatore
            
            Args:
                data (dict): Contiene azione e parametri
            """
            sid = request.sid
            session_id = self.connection_map.get(sid)
            
            logger.info(f"[DEBUG SESSION] Dentro handle_player_action: socket_id={sid}, session_id recuperato={session_id}")

            # Log dettagliato dell'azione ricevuta
            logger.info(f"==== AZIONE RICEVUTA ====")
            logger.info(f"Socket ID: {sid}")
            logger.info(f"Session ID: {session_id}")
            logger.info(f"Azione: {data}")
            
            if not session_id:
                emit('error', {'message': 'Sessione non autenticata'})
                return
                
            if not isinstance(data, dict) or 'action' not in data:
                emit('error', {'message': 'Formato azione non valido'})
                return
                
            action = data['action']
            params = data.get('params', {}) or data.get('data', {}) or {}
            logger.info(f"Azione: {action}, Parametri: {params}")
            
            # Aggiungi session_id e socket_id ai parametri (anche se non sempre usati da process_azione_luogo)
            params['session_id'] = session_id
            params['socket_id'] = sid

            if action == 'move_player':
                if not session_id: 
                    logger.error(f"Session ID non trovato per socket {sid} durante il tentativo di movimento.")
                    emit('error', {'message': 'Sessione non autenticata per il movimento'})
                    return

                try:
                    game_session = get_session(session_id)
                    if not game_session:
                        logger.error(f"GameSession (World) non trovata per session_id {session_id} (socket {sid}).")
                        emit('error', {'message': 'Impossibile recuperare la sessione di gioco.'})
                        return

                    player_instance = getattr(game_session, 'giocatore', None)
                    if not player_instance:
                        logger.error(f"Istanza giocatore (game_session.giocatore) non trovata nella GameSession per session_id {session_id} (socket {sid}).")
                        emit('error', {'message': 'Impossibile recuperare i dati del giocatore per il movimento.'})
                        return
                    
                    logger.info(f"Ottenuto game_session.giocatore. Nome: {getattr(player_instance, 'nome', 'N/A')}, Tipo: {type(player_instance).__name__}, ID: {getattr(player_instance, 'id', 'N/A')}")

                    if not isinstance(player_instance, Giocatore):
                        logger.error(f"ERRORE CRITICO: player_instance recuperata da game_session.giocatore NON è di tipo 'Giocatore', ma '{type(player_instance).__name__}'. La deserializzazione/caricamento del giocatore in session.py o world.py è errata.")
                        emit('error', {'message': 'Errore interno del server: tipo di oggetto giocatore non corretto.'})
                        return

                    user_id_per_azione = getattr(player_instance, 'id', None)

                    if not user_id_per_azione:
                        logger.error(f"User ID (o player.id come fallback) non trovato per socket {sid} / session_id {session_id}.")
                        emit('error', {'message': 'Impossibile identificare l\'utente/giocatore per il movimento.'})
                        return
                    
                    stato_corrente = None
                    if hasattr(game_session, 'get_current_fsm_state') and callable(getattr(game_session, 'get_current_fsm_state')):
                        stato_corrente = game_session.get_current_fsm_state()
                        logger.info(f"Ottenuto stato_corrente da game_session.get_current_fsm_state(): {type(stato_corrente).__name__ if stato_corrente else 'None'} per session {session_id}")
                    else:
                        logger.warning(f"L'oggetto game_session (World) per session {session_id} NON ha il metodo get_current_fsm_state(). Impossibile recuperare lo stato FSM.")
                        # Non possiamo procedere senza uno stato, quindi emettiamo un errore e usciamo.
                        emit('error', {'message': 'Errore interno del server: gestore di stato non trovato.'})
                        return

                    if not stato_corrente or not hasattr(stato_corrente, 'process_azione_luogo') or not callable(getattr(stato_corrente, 'process_azione_luogo')):
                        logger.error(f"Stato corrente recuperato ({type(stato_corrente).__name__ if stato_corrente else 'None'}) non valido o non supporta process_azione_luogo per session_id {session_id} (giocatore {user_id_per_azione}).")
                        emit('error', {'message': 'Stato di gioco non valido o corrotto per il movimento.'})
                        return
                    
                    logger.info(f"Chiamata diretta a stato_corrente.process_azione_luogo ({type(stato_corrente).__name__}) per user/player_id {user_id_per_azione}, session {session_id}, direzione: {params.get('direction')}")
                    
                    # Chiamata al metodo process_azione_luogo della FSM
                    risultato = stato_corrente.process_azione_luogo(user_id_per_azione, "muovi", params)
                    
                    # Se il movimento è avvenuto con successo, l'evento PLAYER_POSITION_UPDATED verrà emesso dalla FSM
                    # e verrà gestito dal metodo _handle_player_position_updated di questa classe
                                        
                    return 

                except Exception as e:
                    logger.error(f"Errore critico durante la gestione di 'move_player' in handle_player_action per session {session_id}: {e}", exc_info=True)
                    emit('error', {'message': f'Errore server durante il tentativo di movimento: {str(e)}'})
                    return
            
            # Gestione delle altre azioni (attack, use_item, interact, save_game)
            event_type = None
            if action == 'attack':
                event_type = Events.PLAYER_ATTACK
            elif action == 'use_item':
                event_type = Events.PLAYER_USE_ITEM
            elif action == 'interact':
                event_type = Events.PLAYER_INTERACT
            elif action == 'save_game':
                # Log dettagliati per debugging
                logger.info(f"==== RICHIESTA SALVATAGGIO RICEVUTA ====")
                logger.info(f"Socket ID: {sid}")
                logger.info(f"Session ID: {session_id}")
                logger.info(f"Dati ricevuti completi: {data}")
                logger.info(f"Parametri estratti: {params}")
                
                # Gestione specifica per il salvataggio del gioco
                # Il nome viene inviato come proprietà name nei parametri 
                name = params.get('name', f"Salvataggio_{int(time.time())}")
                logger.info(f"Nome del salvataggio: {name}")
                
                # Ottieni il session_id corretto dalla mappa di connessione
                if not session_id:
                    logger.error(f"Session ID non trovato per socket {sid}")
                    emit('game_notification', {
                        'type': 'error',
                        'message': 'Errore: sessione non trovata'
                    })
                    return
                
                logger.info(f"Avvio salvataggio per sessione {session_id}, nome: {name}")
                
                # Chiamata REST all'endpoint di salvataggio
                try:
                    from flask import current_app
                    import requests
                    
                    # Prepara i dati per la richiesta
                    save_data = {
                        "id_sessione": session_id,
                        "nome_salvataggio": name
                    }
                    
                    # URL dell'endpoint di salvataggio
                    api_url = f"http://localhost:{current_app.config.get('PORT', 5000)}/save/salva"
                    logger.info(f"Chiamata REST a {api_url} con dati: {save_data}")
                    
                    # Effettua la richiesta POST
                    response = requests.post(api_url, json=save_data)
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('successo'):
                            logger.info(f"Salvataggio completato: {name}")
                            emit('game_notification', {
                                'type': 'success',
                                'message': f'Gioco salvato come "{name}"'
                            })
                        else:
                            logger.error(f"Errore nel salvataggio: {result.get('errore')}")
                            emit('game_notification', {
                                'type': 'error',
                                'message': f'Errore: {result.get("errore", "Errore sconosciuto")}'
                            })
                    else:
                        logger.error(f"Errore HTTP nel salvataggio: {response.status_code}, Risposta: {response.text}")
                        emit('game_notification', {
                            'type': 'error',
                            'message': f'Errore nel salvataggio: codice {response.status_code}'
                        })
                        
                except Exception as e:
                    logger.error(f"Eccezione durante il salvataggio: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    emit('game_notification', {
                        'type': 'error',
                        'message': f'Errore durante il salvataggio: {str(e)}'
                    })
                
                # Non emettiamo un evento EventBus per questa azione
                return
                
            # Se abbiamo un tipo di evento valido, emettilo
            if event_type:
                logger.info(f"[TEMP INFO LOG] Emissione evento {event_type} da azione {action} con params: {params}")
                self.event_bus.emit(event_type, **params)
            else:
                logger.warning(f"Azione non riconosciuta: {action}")
                emit('error', {'message': 'Azione non riconosciuta'})
                
        @self.socketio.on('get_map_data')
        def handle_get_map_data(data):
            """
            Gestisce la richiesta di dati della mappa
            
            Args:
                data (dict): Contiene l'ID della mappa e i parametri aggiuntivi
            """
            sid = request.sid
            session_id = self.connection_map.get(sid)
            
            if not session_id:
                emit('error', {'message': 'Sessione non autenticata'})
                return
                
            if not isinstance(data, dict):
                emit('error', {'message': 'Formato richiesta non valido'})
                return
                
            map_id = data.get('map_id')
            request_id = data.get('request_id')
            
            # Emetti evento di richiesta dati mappa
            self.event_bus.emit(Events.MAP_DATA_REQUESTED, 
                               session_id=session_id,
                               socket_id=sid,
                               map_id=map_id,
                               request_id=request_id)
                
        @self.socketio.on('load_map')
        def handle_load_map(data):
            """
            Gestisce la richiesta di caricamento di una nuova mappa
            
            Args:
                data (dict): Contiene l'ID della mappa da caricare
            """
            sid = request.sid
            session_id = self.connection_map.get(sid)
            
            if not session_id:
                emit('error', {'message': 'Sessione non autenticata'})
                return
                
            if not isinstance(data, dict):
                emit('error', {'message': 'Formato richiesta non valido'})
                return
                
            map_id = data.get('mapId')
            
            if not map_id:
                emit('error', {'message': 'ID mappa mancante o non valido'})
                return
                
            logger.info(f"Richiesta caricamento mappa: {map_id} da sessione {session_id}")
            
            # Emetti evento di richiesta cambio mappa
            self.event_bus.emit(Events.MAP_CHANGE, 
                               session_id=session_id,
                               socket_id=sid,
                               map_id=map_id)
                
        @self.socketio.on('get_game_state')
        def handle_get_game_state(data):
            """
            Gestisce la richiesta dello stato di gioco
            
            Args:
                data (dict): Contiene i parametri della richiesta
            """
            sid = request.sid
            session_id = self.connection_map.get(sid)
            
            if not session_id:
                emit('error', {'message': 'Sessione non autenticata'})
                return
                
            if not isinstance(data, dict):
                emit('error', {'message': 'Formato richiesta non valido'})
                return
                
            include_entities = data.get('include_entities', False)
            include_map = data.get('include_map', False)
            request_id = data.get('request_id')
            
            # Emetti evento di richiesta stato
            self.event_bus.emit(Events.GAME_STATE_REQUESTED, 
                               session_id=session_id,
                               socket_id=sid,
                               include_entities=include_entities,
                               include_map=include_map,
                               request_id=request_id)
                
        @self.socketio.on('request_full_state')
        def handle_request_full_state(data):
            """
            Gestisce la richiesta dello stato completo per sincronizzazione
            
            Args:
                data (dict): Contiene i parametri della richiesta
            """
            sid = request.sid
            session_id = self.connection_map.get(sid)
            
            if not session_id:
                emit('error', {'message': 'Sessione non autenticata'})
                return
                
            # Ottieni la versione del client, se disponibile
            client_version = data.get('version', 0) if isinstance(data, dict) else 0
            request_id = data.get('request_id') if isinstance(data, dict) else None
            
            # Emetti evento di richiesta stato completo
            self.event_bus.emit(Events.FULL_STATE_REQUESTED, 
                               session_id=session_id,
                               socket_id=sid,
                               client_version=client_version,
                               request_id=request_id)
        
        @self.socketio.on('request_recent_updates')
        def handle_request_recent_updates(data):
            """
            Gestisce la richiesta di aggiornamenti recenti dopo una breve disconnessione
            
            Args:
                data (dict): Contiene i parametri della richiesta, inclusa l'ultima versione nota
            """
            sid = request.sid
            session_id = self.connection_map.get(sid)
            
            if not session_id:
                emit('error', {'message': 'Sessione non autenticata'})
                return
            
            # Ottieni l'ultima versione nota dal client
            last_version = data.get('last_version', 0) if isinstance(data, dict) else 0
            current_version = self.state_versions.get(session_id, 0)
            
            # Se la differenza è troppo grande, richiedi sync completo
            if current_version - last_version > 10:
                logger.info(f"Troppe versioni mancanti ({current_version - last_version}), richiedo sync completo")
                # Emetti evento per richiedere sync completo
                self.event_bus.emit(Events.FULL_STATE_REQUESTED, 
                                   session_id=session_id,
                                   socket_id=sid,
                                   client_version=last_version,
                                   force_full=True)
            else:
                # Richiedi solo gli aggiornamenti recenti
                logger.info(f"Richiesta aggiornamenti recenti: versione client {last_version}, server {current_version}")
                self.event_bus.emit(Events.RECENT_UPDATES_REQUESTED,
                                   session_id=session_id,
                                   socket_id=sid,
                                   last_version=last_version,
                                   current_version=current_version)
                
        @self.socketio.on('get_entities')
        def handle_get_entities(data):
            """
            Gestisce la richiesta di entità nella sessione
            
            Args:
                data (dict): Contiene i parametri della richiesta
            """
            sid = request.sid
            session_id = self.connection_map.get(sid)
            
            if not session_id:
                emit('error', {'message': 'Sessione non autenticata'})
                return
                
            include_static = data.get('include_static', False) if isinstance(data, dict) else False
            request_id = data.get('request_id') if isinstance(data, dict) else None
            
            # Emetti evento di richiesta entità
            self.event_bus.emit(Events.ENTITIES_REQUESTED, 
                               session_id=session_id,
                               socket_id=sid,
                               include_static=include_static,
                               request_id=request_id)
    
    # Handler eventi EventBus
    
    def _handle_player_move(self, direction=None, player_id=None, **kwargs):
        """Gestisce l'evento di movimento del giocatore"""
        session_id = kwargs.get('session_id')
        if not session_id or not direction:
            return
            
        # Trasmetti l'aggiornamento a tutti i client nella stessa sessione
        self.broadcast_to_session(session_id, 'player_moved', {
            'direction': direction,
            'player_id': player_id
        })
    
    def _handle_map_change(self, map_id=None, **kwargs):
        """Gestisce l'evento di cambio mappa"""
        session_id = kwargs.get('session_id')
        if not session_id or not map_id:
            return
            
        # Trasmetti il cambio mappa a tutti i client nella sessione
        self.broadcast_to_session(session_id, 'map_changed', {
            'map_id': map_id
        })
    
    def _handle_ui_update(self, ui_type=None, state=None, **kwargs):
        """Gestisce l'evento di aggiornamento UI"""
        socket_id = kwargs.get('socket_id')
        if not socket_id or not ui_type:
            return
            
        # Invia aggiornamento UI al client specifico
        self.socketio.emit('ui_update', {
            'type': ui_type,
            'state': state
        }, room=socket_id)
    
    def _handle_dialog_open(self, dialog_id=None, title=None, message=None, options=None, **kwargs):
        """Gestisce l'evento di apertura dialogo"""
        session_id = kwargs.get('session_id')
        if not session_id or not dialog_id:
            return
            
        # Trasmetti apertura dialogo
        self.broadcast_to_session(session_id, 'dialog_open', {
            'dialog_id': dialog_id,
            'title': title,
            'message': message,
            'options': options
        })
    
    def _handle_dialog_close(self, dialog_id=None, **kwargs):
        """Gestisce l'evento di chiusura dialogo"""
        session_id = kwargs.get('session_id')
        if not session_id or not dialog_id:
            return
            
        # Trasmetti chiusura dialogo
        self.broadcast_to_session(session_id, 'dialog_close', {
            'dialog_id': dialog_id
        })
    
    def _handle_player_login(self, token=None, socket_id=None, **kwargs):
        """Gestisce l'evento di login giocatore"""
        logger.info(f"[AUTH_DEBUG] _handle_player_login chiamato per socket_id: {socket_id}, token: {token}, kwargs: {kwargs}")
        if not socket_id or not token:
            logger.warning(f"[AUTH_DEBUG] _handle_player_login: socket_id o token mancanti.")
            return
            
        try:
            # Qui andrebbe la logica di autenticazione
            # Per ora simulo un'autenticazione di successo
            session_id = "session_" + socket_id[:8]
            logger.info(f"[AUTH_DEBUG] Per {socket_id}: Sessione generata/recuperata: {session_id}")
            
            # Aggiungi alla mappa delle connessioni
            self.connection_map[socket_id] = session_id
            logger.info(f"[AUTH_DEBUG] Per {socket_id}: connection_map aggiornata: {self.connection_map}")
            
            # IMPORTANTE: Sincronizza anche socket_sessioni per compatibilità con game_events.py
            from server.utils.session import socket_sessioni
            socket_sessioni[socket_id] = session_id
            logger.info(f"[AUTH_DEBUG] Per {socket_id}: socket_sessioni aggiornata per compatibilità con game_events.py")
            
            # Invia risposta al client
            self.socketio.emit('authenticated', {
                'session_id': session_id,
                'success': True
            }, room=socket_id)
            logger.info(f"[AUTH_DEBUG] Evento 'authenticated' inviato a {socket_id} con session_id: {session_id}")
            
            logger.info(f"Autenticazione riuscita: socket_id={socket_id}, session_id={session_id}")
        except Exception as e:
            logger.error(f"[AUTH_DEBUG] Errore in _handle_player_login per {socket_id}: {str(e)}")
            self.socketio.emit('auth_error', {
                'message': str(e)
            }, room=socket_id)
    
    def _handle_player_logout(self, session_id=None, **kwargs):
        """Gestisce l'evento di logout giocatore"""
        if not session_id:
            return
            
        # Trova tutti i socket associati a questa sessione
        socket_ids = [sid for sid, sess_id in self.connection_map.items() if sess_id == session_id]
        
        # Rimuovi le connessioni dalla mappa
        for sid in socket_ids:
            self.connection_map.pop(sid, None)
            
        # Notifica i client
        for sid in socket_ids:
            self.socketio.emit('logged_out', {}, room=sid)
    
    def _handle_change_state(self, new_state=None, **kwargs):
        """Gestisce l'evento di cambio stato"""
        session_id = kwargs.get('session_id')
        if not session_id or not new_state:
            return
            
        # Trasmetti cambio stato
        self.broadcast_to_session(session_id, 'state_changed', {
            'state': new_state
        })
    
    def _handle_push_state(self, new_state=None, **kwargs):
        """Gestisce l'evento di push stato"""
        session_id = kwargs.get('session_id')
        if not session_id or not new_state:
            return
            
        # Trasmetti push stato
        self.broadcast_to_session(session_id, 'state_pushed', {
            'state': new_state
        })
    
    def _handle_pop_state(self, **kwargs):
        """Gestisce l'evento di pop stato"""
        session_id = kwargs.get('session_id')
        if not session_id:
            return
            
        # Trasmetti pop stato
        self.broadcast_to_session(session_id, 'state_popped', {})
    
    def _get_session_id(self):
        """
        Ottiene l'ID sessione dal contesto attuale request/g
        
        Returns:
            str: ID della sessione o None
        """
        # Verifica se sid è nel context
        sid = getattr(request, 'sid', None)
        
        # Se c'è sid, cercalo nella connection_map
        if sid in self.connection_map:
            return self.connection_map[sid]
        
        # Se non c'è sid o non è nella mappa, controlla g (context globale)
        return getattr(g, 'session_id', None)
    
    def broadcast_game_state(self, session_id, state_data, changes=None):
        """
        Trasmette lo stato di gioco corrente a tutti i client nella sessione
        
        Args:
            session_id (str): ID della sessione
            state_data (dict): Dati completi dello stato
            changes (dict, optional): Solo le modifiche allo stato (per updates parziali)
        """
        # Incrementa la versione dello stato per questa sessione
        current_version = self.state_versions.get(session_id, 0)
        new_version = current_version + 1
        self.state_versions[session_id] = new_version
        
        # Aggiungi la versione allo stato
        state_data['version'] = new_version
        
        # Se sono specificate solo le modifiche, invia un update parziale
        if changes:
            changes['version'] = new_version
            self.broadcast_to_session(session_id, 'game_state_update', changes)
            return
            
        # Altrimenti invia lo stato completo
        self.broadcast_to_session(session_id, 'game_state', state_data)
        
        logger.debug(f"Stato di gioco (v{new_version}) trasmesso alla sessione {session_id}")
    
    def broadcast_to_session(self, session_id, event, data):
        """
        Trasmette un evento a tutti i client in una sessione
        
        Args:
            session_id (str): ID della sessione
            event (str): Nome dell'evento da emettere
            data (dict): Dati dell'evento
        """
        # Trova tutti i socket associati alla sessione
        socket_ids = [sid for sid, sess_id in self.connection_map.items() if sess_id == session_id]
        
        if not socket_ids:
            logger.warning(f"Nessun client trovato per la sessione {session_id}")
            return
            
        # Crea room name per la sessione
        room = f"session_{session_id}"
        
        # Trasmetti a tutti nella stanza
        self.broadcast_to_room(room, event, data)
    
    def broadcast_to_room(self, room, event, data):
        """
        Trasmette un evento a tutti i client in una stanza
        
        Args:
            room (str): ID della stanza
            event (str): Nome dell'evento da emettere
            data (dict): Dati dell'evento
        """
        try:
            self.socketio.emit(event, data, room=room)
        except Exception as e:
            logger.error(f"Errore durante broadcast a {room}: {str(e)}")
    
    def respond_to_request(self, sid, event_base, request_id, data):
        """
        Risponde a una richiesta specifica da un client
        
        Args:
            sid (str): ID del socket
            event_base (str): Nome base dell'evento (es. 'map_data')
            request_id (str): ID della richiesta
            data (dict): Dati della risposta
        """
        if not sid:
            logger.warning(f"Impossibile rispondere: sid mancante")
            return
            
        # Costruisci il nome dell'evento di risposta
        response_event = f"{event_base}_response"
        
        # Aggiungi l'ID della richiesta
        if request_id:
            data['request_id'] = request_id
            
        # Invia la risposta
        try:
            self.socketio.emit(response_event, data, room=sid)
        except Exception as e:
            logger.error(f"Errore durante risposta a {sid}: {str(e)}")
    
    def get_session_clients(self, session_id):
        """
        Restituisce gli ID dei socket connessi a una sessione
        
        Args:
            session_id (str): ID della sessione
            
        Returns:
            list: Lista di socket ID
        """
        if not session_id:
            return []
            
        return [sid for sid, sess_id in self.connection_map.items() if sess_id == session_id]
    
    def run(self, host='0.0.0.0', port=5001, debug=False):
        """
        Avvia il server WebSocket
        
        Args:
            host (str): Host di ascolto
            port (int): Porta di ascolto
            debug (bool): Modalità debug
        """
        logger.info(f"Avvio server WebSocket su {host}:{port}")
        self.socketio.run(current_app, host=host, port=port, debug=debug)

    def _handle_player_position_updated(self, player_id=None, nuova_posizione=None, mappa_corrente=None, client_socket_id=None, **kwargs):
        """Gestisce l'evento di posizione del giocatore aggiornata e la trasmette.
           client_socket_id è opzionale; se fornito, l'aggiornamento potrebbe essere inviato solo a quel client,
           altrimenti a tutta la sessione.
        """
        session_id = kwargs.get('session_id')
        
        if not session_id:
            logger.warning(f"[WS_PLAYER_POS_UPDATE] session_id mancante, impossibile trasmettere aggiornamento posizione per player {player_id}")
            return
            
        if nuova_posizione is None or not isinstance(nuova_posizione, tuple) or len(nuova_posizione) != 2:
            logger.warning(f"[WS_PLAYER_POS_UPDATE] nuova_posizione non valida per player {player_id} in sessione {session_id}. Dati: {nuova_posizione}")
            return

        if not player_id:
            logger.warning(f"[WS_PLAYER_POS_UPDATE] player_id mancante in sessione {session_id}")
            return
            
        payload = {
            'player_id': player_id,
            'x': nuova_posizione[0],
            'y': nuova_posizione[1],
            'map_id': mappa_corrente 
        }
        
        logger.info(f"[WS_PLAYER_POS_UPDATE] Trasmissione 'player_position_updated' per sessione {session_id}, player {player_id}, payload: {payload}")
        
        # Se client_socket_id è specificato, potremmo voler inviare solo a lui (es. conferma di un'azione)
        # Ma tipicamente l'aggiornamento di posizione va a tutti nella sessione.
        self.broadcast_to_session(session_id, 'player_position_updated', payload)

def init():
    """
    Inizializza e restituisce una nuova istanza di WebSocketManager
    
    Returns:
        WebSocketManager: Istanza del gestore
    """
    manager = WebSocketManager()
    return manager 