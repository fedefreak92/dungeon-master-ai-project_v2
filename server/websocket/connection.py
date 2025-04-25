import logging
from flask import request, current_app
from flask_socketio import emit, join_room, leave_room
import traceback
import json
import time
from datetime import datetime, timedelta

# Moduli locali
from server.utils.session import socket_sessioni, carica_sessione, salva_sessione
from core.ecs.system import RenderSystem
from . import socketio, graphics_renderer

# Configura il logger
logger = logging.getLogger(__name__)

# Tracking per client connessi
active_clients = {}

# Aggiungi questa variabile per tracciare le disconnessioni temporanee
temp_disconnected_clients = {}

def send_to_client(session_id, event_name, data):
    """
    Invia un evento a un client specifico tramite il suo ID sessione.
    
    Args:
        session_id (str): ID della sessione del client
        event_name (str): Nome dell'evento da emettere
        data (dict): Dati da inviare con l'evento
    """
    try:
        room_id = f"session_{session_id}"
        socketio.emit(event_name, data, room=room_id)
        logger.debug(f"Evento {event_name} inviato alla sessione {session_id}")
        return True
    except Exception as e:
        logger.error(f"Errore nell'invio dell'evento {event_name} alla sessione {session_id}: {e}")
        return False

def handle_connect():
    """Gestisce la connessione di un nuovo client"""
    try:
        client_id = request.sid
        logger.info(f"Nuovo client connesso: {client_id}")
        
        # Ottieni informazioni sulla richiesta
        transport = request.environ.get('wsgi.websocket_version', 'Unknown')
        user_agent = request.headers.get('User-Agent', 'Unknown')
        logger.info(f"Dettagli connessione - Client: {client_id}, Transport: {transport}, User-Agent: {user_agent}")
        
        # Registra il client attivo
        active_clients[client_id] = {
            'connected_at': datetime.now(),
            'last_ping': datetime.now(),
            'ping_count': 0,
            'session_id': None,
            'user_agent': user_agent,
            'transport': transport
        }
        
        # Ottieni informazioni sulla connessione Socket.IO
        socket_info = {
            'id': client_id,
            'async_mode': socketio.async_mode,
            'transport': transport,
            'protocol_version': request.environ.get('HTTP_SEC_WEBSOCKET_VERSION', 'Unknown')
        }
        logger.info(f"Socket.IO info: {json.dumps(socket_info)}")
        
        emit('connection_established', {
            'status': 'ok',
            'client_id': client_id,
            'server_info': {
                'version': '1.0.0',
                'transport': transport,
                'async_mode': socketio.async_mode,
                'session_count': len(socket_sessioni),
                'connected_clients': len(active_clients)
            }
        })
    except Exception as e:
        logger.error(f"Errore durante gestione connessione client: {e}")
        logger.error(traceback.format_exc())
        emit('error', {'message': 'Errore interno del server durante la connessione'})

def handle_disconnect():
    """Gestisce la disconnessione di un client"""
    try:
        client_id = request.sid
        logger.info(f"Client disconnesso: {client_id}")
        
        # Salva temporaneamente l'associazione socket-sessione per permettere riconnessioni rapide
        if client_id in socket_sessioni:
            id_sessione = socket_sessioni[client_id]
            
            # Mantieni l'associazione per un breve periodo
            temp_disconnected_clients[client_id] = {
                'session_id': id_sessione,
                'disconnected_at': datetime.now(),
                'expiry': datetime.now() + timedelta(seconds=30)  # 30 secondi di tempo per riconnettersi
            }
            
            logger.info(f"Associazione socket-sessione {client_id} -> {id_sessione} conservata temporaneamente per facilitare riconnessione")
            
            # Salva comunque la sessione
            sessione = carica_sessione(id_sessione)
            if sessione:
                try:
                    salva_sessione(id_sessione, sessione)
                    logger.info(f"Sessione {id_sessione} salvata dopo disconnessione del client {client_id}")
                except Exception as e:
                    logger.error(f"Errore durante il salvataggio della sessione {id_sessione}: {e}")
            
            # Non rimuoviamo ancora dalla stanza ma lasciamo l'associazione per facilitare la riconnessione
            # leave_room(f"session_{id_sessione}")
            # del socket_sessioni[client_id]
        
        # Rimuovi dal tracking dei client attivi
        if client_id in active_clients:
            client_data = active_clients[client_id]
            connection_duration = datetime.now() - client_data['connected_at']
            logger.info(f"Statistiche client {client_id}: connesso per {connection_duration.total_seconds()}s, ping: {client_data['ping_count']}")
            del active_clients[client_id]
    except Exception as e:
        logger.error(f"Errore durante gestione disconnessione client: {e}")
        logger.error(traceback.format_exc())

def handle_join_game(data):
    """
    Gestisce l'ingresso di un client in una sessione di gioco
    
    Args:
        data (dict): Contiene id_sessione e altri metadati
    """
    try:
        from . import core
        client_id = request.sid
        
        # Valida i dati ricevuti
        if not isinstance(data, dict):
            logger.warning(f"Client {client_id} ha inviato dati non validi: {data}")
            emit('error', {'message': 'Formato dati non valido'})
            return
            
        id_sessione = data.get('id_sessione')
        if not id_sessione:
            logger.warning(f"Client {client_id} ha tentato di unirsi senza ID sessione")
            emit('error', {'message': 'ID sessione richiesto'})
            return
        
        # Verifica se il client è già associato ad un'altra sessione
        if client_id in socket_sessioni and socket_sessioni[client_id] != id_sessione:
            old_session = socket_sessioni[client_id]
            leave_room(f"session_{old_session}")
            logger.info(f"Client {client_id} trasferito dalla sessione {old_session} alla sessione {id_sessione}")
            
        # Unisci il client alla room corrispondente all'ID sessione
        room_id = f"session_{id_sessione}"
        join_room(room_id)
        socket_sessioni[client_id] = id_sessione
        logger.info(f"Client {client_id} unito alla sessione {id_sessione}")
        
        # Aggiorna tracking client
        if client_id in active_clients:
            active_clients[client_id]['session_id'] = id_sessione
        
        # Ottieni la sessione
        sessione = core.get_session(id_sessione)
        if not sessione:
            logger.warning(f"Sessione {id_sessione} richiesta dal client {client_id} non trovata")
            leave_room(room_id)
            del socket_sessioni[client_id]
            emit('error', {'message': 'Sessione non trovata'})
            return
        
        # Configura il renderer grafico per questa sessione se non è già configurato
        render_system = None
        for system in sessione.systems:
            if isinstance(system, RenderSystem):
                render_system = system
                break
        
        if not render_system:
            # Crea e registra un nuovo sistema di rendering
            render_system = RenderSystem(graphics_renderer)
            sessione.add_system(render_system)
            logger.info(f"Creato nuovo sistema di rendering per la sessione {id_sessione}")
        else:
            # Aggiorna il renderer nel sistema esistente
            render_system.set_renderer(graphics_renderer)
            logger.info(f"Aggiornato renderer grafico esistente per la sessione {id_sessione}")
            
        # Invia lo stato corrente al client
        try:
            stato_serializzato = sessione.serialize()
            emit('game_state', {
                'world': stato_serializzato
            })
        except Exception as e:
            logger.error(f"Errore durante la serializzazione dello stato di gioco: {e}")
            logger.error(traceback.format_exc())
            emit('error', {'message': "Errore durante l'invio dello stato di gioco"})
            return
        
        # Invia anche la configurazione del renderer
        try:
            info_renderer = graphics_renderer.get_renderer_info()
            emit('renderer_config', info_renderer)
        except Exception as e:
            logger.error(f"Errore durante l'invio della configurazione del renderer: {e}")
            logger.error(traceback.format_exc())
            emit('error', {'message': "Errore durante l'invio della configurazione del renderer"})
            return
            
        # Conferma che il join è avvenuto con successo
        emit('join_success', {
            'session_id': id_sessione,
            'client_id': client_id,
            'timestamp': socketio.time(),
            'connection_info': {
                'transport': request.environ.get('wsgi.websocket_version', 'Unknown'),
                'async_mode': socketio.async_mode
            }
        })
        
    except Exception as e:
        logger.error(f"Errore durante l'elaborazione di join_game: {e}")
        logger.error(traceback.format_exc())
        emit('error', {'message': 'Errore interno del server durante join_game'})

def handle_ping(data):
    """
    Gestisce i ping dal client per mantenere attiva la connessione
    
    Args:
        data (dict): Dati opzionali del ping
    """
    client_id = request.sid
    try:
        # Aggiorna stato client
        if client_id in active_clients:
            active_clients[client_id]['last_ping'] = datetime.now()
            active_clients[client_id]['ping_count'] += 1
        
        # Invia pong come risposta
        timestamp = data.get('timestamp', 0) if isinstance(data, dict) else 0
        emit('pong', {
            'timestamp': timestamp,
            'server_timestamp': socketio.time(),
            'latency': data.get('client_timestamp', 0) - timestamp if isinstance(data, dict) and 'client_timestamp' in data else None
        })
    except Exception as e:
        logger.error(f"Errore durante gestione ping dal client {client_id}: {e}")

def check_zombie_connections():
    """
    Verifica connessioni zombie e disconnette i client inattivi
    Da eseguire periodicamente
    """
    try:
        current_time = datetime.now()
        zombie_threshold = current_time - timedelta(minutes=5)
        zombies = []
        
        for client_id, data in active_clients.items():
            if data['last_ping'] < zombie_threshold:
                zombies.append(client_id)
                
        for zombie in zombies:
            logger.warning(f"Disconnessione client zombie: {zombie}, ultimo ping: {active_clients[zombie]['last_ping']}")
            try:
                # Modifica: invece di usare socketio.disconnect() che non esiste
                # Usiamo socketio.emit con un evento che il client interpreterà come richiesta di disconnessione
                socketio.emit('force_disconnect', {'reason': 'zombie_timeout'}, room=zombie)
                # Se il client è in una stanza, lo rimuoviamo
                if zombie in socket_sessioni:
                    session_id = socket_sessioni[zombie]
                    room_id = f"session_{session_id}"
                    leave_room(room_id)
            except Exception as e:
                logger.error(f"Errore durante disconnessione zombie {zombie}: {e}")
            
            # Rimuovi dai tracking anche se la disconnessione fallisce
            if zombie in active_clients:
                del active_clients[zombie]
                
            # Rimuovi anche dalle mappature di sessione se presente
            if zombie in socket_sessioni:
                del socket_sessioni[zombie]
                
        if zombies:
            logger.info(f"Rimossi {len(zombies)} client zombie. Rimanenti: {len(active_clients)}")
            
    except Exception as e:
        logger.error(f"Errore durante verifica connessioni zombie: {e}")

def handle_connection_test(data):
    """
    Endpoint di test per verificare la connessione WebSocket
    
    Args:
        data (dict): Dati di test opzionali
    """
    client_id = request.sid
    try:
        logger.info(f"Test connessione ricevuto dal client {client_id}")
        
        # Echo dei dati ricevuti più alcune informazioni aggiuntive
        response = {
            'echo': data,
            'server_info': {
                'time': socketio.time(),
                'transport': request.environ.get('wsgi.websocket_version', 'Unknown'),
                'client_id': client_id,
                'socketio_mode': socketio.async_mode,
                'server_port': current_app.config.get('SERVER_PORT', 'Unknown'),
                'active_clients': len(active_clients),
                'active_sessions': len(socket_sessioni)
            }
        }
        
        emit('connection_test_response', response)
    except Exception as e:
        logger.error(f"Errore durante test connessione dal client {client_id}: {e}")
        emit('error', {'message': 'Errore durante il test di connessione'})

def handle_socket_error(error):
    """
    Gestisce gli errori di Socket.IO
    
    Args:
        error: Oggetto errore
    """
    try:
        logger.error(f"Errore Socket.IO: {error}")
        if request and hasattr(request, 'sid'):
            client_id = request.sid
            logger.error(f"Errore Socket.IO per client {client_id}")
    except Exception as e:
        logger.error(f"Errore durante la gestione dell'errore Socket.IO: {e}")
        logger.error(traceback.format_exc())

def handle_reconnect_attempt(data):
    """
    Gestisce un tentativo di riconnessione da parte di un client
    
    Args:
        data (dict): Dati di riconnessione che includono l'ID sessione
    """
    try:
        client_id = request.sid
        logger.info(f"Tentativo di riconnessione ricevuto da client: {client_id}")
        
        # Valida i dati ricevuti
        if not isinstance(data, dict):
            logger.warning(f"Client {client_id} ha inviato dati non validi durante il tentativo di riconnessione: {data}")
            emit('error', {'message': 'Formato dati non valido'})
            return
            
        id_sessione = data.get('id_sessione')
        if not id_sessione:
            logger.warning(f"Client {client_id} ha tentato di riconnettersi senza ID sessione")
            emit('error', {'message': 'ID sessione richiesto per la riconnessione'})
            return
        
        # Verifica se il client precedente è tra quelli disconnessi temporaneamente
        old_client_id = None
        for temp_id, temp_data in temp_disconnected_clients.items():
            if temp_data['session_id'] == id_sessione and datetime.now() <= temp_data['expiry']:
                old_client_id = temp_id
                break
        
        if old_client_id:
            # Trasferisci i dati dal vecchio client al nuovo
            logger.info(f"Riconnessione rapida: trasferimento da client {old_client_id} a {client_id} per sessione {id_sessione}")
            socket_sessioni[client_id] = id_sessione
            
            # Unisci il client alla room della sessione
            room_id = f"session_{id_sessione}"
            join_room(room_id)
            
            # Rimuovi i dati temporanei
            del temp_disconnected_clients[old_client_id]
            
            # Notifica il client che la riconnessione è avvenuta con successo
            emit('reconnect_success', {
                'session_id': id_sessione,
                'client_id': client_id,
                'timestamp': socketio.time(),
                'reconnection_type': 'fast'
            })
            
            # Notifica anche la stanza della riconnessione
            socketio.emit('client_reconnected', {
                'client_id': client_id,
                'timestamp': socketio.time()
            }, room=room_id)
            
            # Aggiorna tracking client
            active_clients[client_id] = {
                'connected_at': datetime.now(),
                'last_ping': datetime.now(),
                'ping_count': 0,
                'session_id': id_sessione,
                'user_agent': request.headers.get('User-Agent', 'Unknown'),
                'transport': request.environ.get('wsgi.websocket_version', 'Unknown')
            }
            
            return
        
        # Se non troviamo una disconnessione temporanea, procediamo con un join normale
        logger.info(f"Riconnessione lenta: nuovo join per client {client_id} alla sessione {id_sessione}")
        emit('reconnect_pending', {
            'message': 'Riconnessione normale richiesta, procedendo con join_game',
            'session_id': id_sessione
        })
        
        # Prepara i dati per il join_game
        join_data = {'id_sessione': id_sessione}
        handle_join_game(join_data)
        
    except Exception as e:
        logger.error(f"Errore durante gestione tentativo di riconnessione: {e}")
        logger.error(traceback.format_exc())
        emit('error', {'message': 'Errore interno durante tentativo di riconnessione'})

def cleanup_temp_disconnections():
    """
    Pulisce le disconnessioni temporanee scadute
    Da chiamare periodicamente
    """
    try:
        current_time = datetime.now()
        expired_clients = []
        
        for client_id, data in temp_disconnected_clients.items():
            if current_time > data['expiry']:
                expired_clients.append(client_id)
        
        for client_id in expired_clients:
            logger.info(f"Pulizia disconnessione temporanea scaduta per client {client_id}, sessione {temp_disconnected_clients[client_id]['session_id']}")
            
            # Se era presente nei socket_sessioni, rimuovilo
            if client_id in socket_sessioni:
                session_id = socket_sessioni[client_id]
                leave_room(f"session_{session_id}")
                del socket_sessioni[client_id]
            
            # Rimuovi dai temporanei
            del temp_disconnected_clients[client_id]
    except Exception as e:
        logger.error(f"Errore durante pulizia disconnessioni temporanee: {e}")
        logger.error(traceback.format_exc())

def register_handlers(socketio_instance):
    """
    Registra tutti gli handler di connessione per il socket
    
    Args:
        socketio_instance: Istanza del socketio da utilizzare
    """
    try:
        from . import core
        
        # Registra handler per eventi base di connessione
        socketio_instance.on_event('connect', handle_connect)
        socketio_instance.on_event('disconnect', handle_disconnect)
        socketio_instance.on_event('join_game', handle_join_game)
        socketio_instance.on_event('ping', handle_ping)
        socketio_instance.on_event('connection_test', handle_connection_test)
        socketio_instance.on_event('reconnect_attempt', handle_reconnect_attempt)
        
        # Registra handler per gli errori Socket.IO
        socketio_instance.on_error(handle_socket_error)
        
        logger.info("Handler di connessione registrati")
        
        # Avvia task periodici
        def zombie_connection_checker():
            """Task periodico per controllare connessioni zombie"""
            while True:
                try:
                    socketio_instance.sleep(300)  # Controlla ogni 5 minuti
                    check_zombie_connections()
                except Exception as e:
                    logger.error(f"Errore durante il controllo connessioni zombie: {e}")
                    
        def temp_disconnection_cleaner():
            """Task periodico per pulire le disconnessioni temporanee scadute"""
            while True:
                try:
                    socketio_instance.sleep(10)  # Controlla ogni 10 secondi
                    cleanup_temp_disconnections()
                except Exception as e:
                    logger.error(f"Errore durante la pulizia disconnessioni temporanee: {e}")
        
        # Avvia i task in background
        socketio_instance.start_background_task(zombie_connection_checker)
        socketio_instance.start_background_task(temp_disconnection_cleaner)
        
        logger.info("Task periodici di pulizia connessioni avviati")
        
    except Exception as e:
        logger.error(f"Errore durante la registrazione degli handler di connessione: {e}")
        logger.error(traceback.format_exc()) 