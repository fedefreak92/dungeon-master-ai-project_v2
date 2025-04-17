import logging
from flask import request
from flask_socketio import emit

# Moduli locali
from server.utils.session import sessioni_attive, socket_sessioni, carica_sessione, salva_sessione
from . import socketio, graphics_renderer

# Configura il logger
logger = logging.getLogger(__name__)

def get_session(id_sessione, emit_error=True):
    """
    Funzione di utilità per ottenere un'istanza di sessione
    
    Args:
        id_sessione: ID della sessione
        emit_error: Se True, emette errori SocketIO in caso di problemi
    
    Returns:
        Istanza sessione o None in caso di errore
    """
    # Verifica se la sessione esiste
    sessione = sessioni_attive.get(id_sessione) or carica_sessione(id_sessione)
    if not sessione and emit_error:
        emit('error', {'message': 'Sessione non trovata'})
        return None
    
    # Metti la sessione nella cache se non c'è già
    if id_sessione not in sessioni_attive and sessione:
        sessioni_attive[id_sessione] = sessione
        
    return sessione

def validate_request_data(data, required_fields, emit_error=True):
    """
    Valida i dati della richiesta
    
    Args:
        data: Dizionario dei dati
        required_fields: Lista di campi obbligatori
        emit_error: Se True, emette errori SocketIO in caso di problemi
    
    Returns:
        True se i dati sono validi, False altrimenti
    """
    for field in required_fields:
        if field not in data:
            if emit_error:
                emit('error', {'message': f'Campo "{field}" richiesto'})
            return False
    return True

def register_handlers(socketio_instance):
    """
    Registra handler comuni
    
    Args:
        socketio_instance: Istanza SocketIO
    """
    logger.info("Registrazione degli handler di base") 