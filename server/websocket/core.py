"""
Core WebSocket functionality
Modulo di base per la gestione delle funzionalità WebSocket comuni.
"""

import logging
from flask_socketio import emit
from flask import request

# Import dei moduli necessari
from server.utils.session import get_session

# Configura il logger
logger = logging.getLogger(__name__)

def validate_request_data(data, required_fields=None):
    """
    Verifica che i dati richiesti siano presenti e validi
    
    Args:
        data (dict): Dati da validare
        required_fields (list): Lista di campi obbligatori
        
    Returns:
        bool: True se i dati sono validi, False altrimenti
    """
    if data is None:
        logger.error("Dati della richiesta mancanti")
        emit('error', {'message': 'Dati della richiesta mancanti'})
        return False
        
    if not isinstance(data, dict):
        logger.error(f"Formato dati non valido: {type(data)}")
        emit('error', {'message': 'Formato dati non valido'})
        return False
        
    if required_fields:
        for field in required_fields:
            if field not in data:
                logger.error(f"Campo obbligatorio mancante: {field}")
                emit('error', {'message': f'Campo obbligatorio mancante: {field}'})
                return False
                
    return True

def get_session(session_id):
    """
    Ottiene una sessione di gioco dato l'ID
    
    Args:
        session_id (str): ID della sessione
        
    Returns:
        Session: Oggetto sessione o None se non trovata
    """
    if not session_id:
        logger.error("ID sessione mancante")
        emit('error', {'message': 'ID sessione mancante'})
        return None
        
    try:
        session = get_session(session_id)
        if not session:
            logger.error(f"Sessione non trovata: {session_id}")
            emit('error', {'message': 'Sessione non trovata'})
            return None
            
        return session
    except Exception as e:
        logger.error(f"Errore durante il recupero della sessione: {e}")
        emit('error', {'message': f'Errore durante il recupero della sessione: {e}'})
        return None

def handle_ping(data):
    """
    Gestore per il ping del client
    
    Args:
        data (dict): Dati della richiesta
    """
    logger.debug("Ricevuto ping dal client")
    emit('pong', {'timestamp': data.get('timestamp', 0)})

def handle_connect():
    """
    Gestore per la connessione di un client
    """
    logger.info(f"Nuovo client connesso: {request.sid}")
    emit('welcome', {'message': 'Benvenuto al server di gioco RPG'})

def handle_disconnect():
    """
    Gestore per la disconnessione di un client
    """
    logger.info(f"Client disconnesso: {request.sid}")

def handle_error(e):
    """
    Gestore per gli errori WebSocket
    
    Args:
        e: Eccezione sollevata
    """
    logger.error(f"Errore WebSocket: {e}")

def register_handlers(socketio_instance):
    """
    Registra gli handler di base per WebSocket
    
    Args:
        socketio_instance: Istanza SocketIO dell'applicazione
    """
    # Eventi di connessione di base
    socketio_instance.on_event('connect', handle_connect)
    socketio_instance.on_event('disconnect', handle_disconnect)
    socketio_instance.on_event('ping', handle_ping)
    
    # Registrazione del gestore errori
    @socketio_instance.on_error()
    def error_handler(e):
        handle_error(e)
    
    logger.info("Handler WebSocket core registrati") 