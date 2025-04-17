import logging
from flask import request
from flask_socketio import emit, join_room, leave_room

# Moduli locali
from server.utils.session import socket_sessioni, carica_sessione
from core.ecs.system import RenderSystem
from . import socketio, graphics_renderer

# Configura il logger
logger = logging.getLogger(__name__)

def handle_connect():
    """Gestisce la connessione di un nuovo client"""
    logger.info(f"Nuovo client connesso: {request.sid}")
    emit('connection_established', {'status': 'ok'})

def handle_disconnect():
    """Gestisce la disconnessione di un client"""
    logger.info(f"Client disconnesso: {request.sid}")
    
    # Rimuovi dalle sessioni attive se presente
    if request.sid in socket_sessioni:
        id_sessione = socket_sessioni[request.sid]
        leave_room(f"session_{id_sessione}")
        del socket_sessioni[request.sid]
        logger.info(f"Client {request.sid} rimosso dalla sessione {id_sessione}")

def handle_join_game(data):
    """
    Gestisce l'ingresso di un client in una sessione di gioco
    
    Args:
        data (dict): Contiene id_sessione e altri metadati
    """
    from . import core

    id_sessione = data.get('id_sessione')
    if not id_sessione:
        emit('error', {'message': 'ID sessione richiesto'})
        return
        
    # Unisci il client alla room corrispondente all'ID sessione
    room_id = f"session_{id_sessione}"
    join_room(room_id)
    socket_sessioni[request.sid] = id_sessione
    logger.info(f"Client {request.sid} unito alla sessione {id_sessione}")
    
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        leave_room(room_id)
        del socket_sessioni[request.sid]
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
    else:
        # Aggiorna il renderer nel sistema esistente
        render_system.set_renderer(graphics_renderer)
        
    # Invia lo stato corrente al client
    emit('game_state', {
        'world': sessione.serialize()
    })
    
    # Invia anche la configurazione del renderer
    emit('renderer_config', graphics_renderer.get_renderer_info())

def register_handlers(socketio_instance):
    """
    Registra gli handler di connessione
    
    Args:
        socketio_instance: Istanza SocketIO
    """
    socketio_instance.on_event('connect', handle_connect)
    socketio_instance.on_event('disconnect', handle_disconnect)
    socketio_instance.on_event('join_game', handle_join_game)
    
    logger.info("Handler di connessione registrati") 