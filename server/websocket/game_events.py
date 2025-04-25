import logging
from flask_socketio import emit
from flask import request

# Import moduli locali
from server.utils.session import salva_sessione
from . import core

# Configura il logger
logger = logging.getLogger(__name__)

def handle_game_event(data):
    """
    Gestisce un evento di gioco inviato dal client
    
    Args:
        data (dict): Contiene id_sessione, tipo_evento e dati_evento
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'tipo_evento']):
        return
        
    id_sessione = data['id_sessione']
    tipo_evento = data['tipo_evento']
    dati_evento = data.get('dati_evento', {})
    
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        return
    
    # Gestisci l'evento nel mondo ECS
    risultato = sessione.process_event(tipo_evento, dati_evento)
    
    # Salva la sessione aggiornata
    salva_sessione(id_sessione, sessione)
    
    # Comunica il risultato al client
    emit('event_result', {
        'success': True,
        'result': risultato,
        'world_state': sessione.get_player_view()
    })

def handle_player_input(data):
    """
    Gestisce l'input del giocatore dal frontend
    
    Args:
        data (dict): Contiene id_sessione, tipo_input e dati_input
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'tipo_input']):
        return
        
    id_sessione = data['id_sessione']
    tipo_input = data['tipo_input']
    dati_input = data.get('dati_input', {})
    
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        return
    
    # Trasforma l'input in un evento ECS appropriato
    if tipo_input == 'move':
        direzione = dati_input.get('direzione')
        if direzione:
            risultato = sessione.process_event('player_move', {'direction': direzione})
    elif tipo_input == 'action':
        azione = dati_input.get('azione')
        if azione:
            risultato = sessione.process_event('player_action', {'action': azione})
    elif tipo_input == 'interact':
        target_id = dati_input.get('target_id')
        if target_id:
            risultato = sessione.process_event('player_interact', {'target_id': target_id})
    else:
        emit('error', {'message': 'Tipo input non valido'})
        return
    
    # Salva la sessione aggiornata
    salva_sessione(id_sessione, sessione)
    
    # Comunica il risultato al client
    emit('game_update', {
        'success': True,
        'world_state': sessione.get_player_view()
    })

def handle_request_game_state(data):
    """
    Gestisce una richiesta di stato completo del gioco
    
    Args:
        data (dict): Contiene id_sessione
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione']):
        return
        
    id_sessione = data['id_sessione']
    
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        return
    
    # Ottieni la vista completa del gioco
    try:
        game_state = {
            'player': sessione.get_player_entity().serialize(),
            'entities': [e.serialize() for e in sessione.get_entities()],
            'world': sessione.serialize()
        }
        
        emit('full_game_state', game_state)
    except Exception as e:
        logger.error(f"Errore nell'ottenere lo stato del gioco: {e}")
        emit('error', {'message': f'Errore nel caricamento dello stato: {str(e)}'})

def register_handlers(socketio_instance):
    """
    Registra gli handler degli eventi di gioco
    
    Args:
        socketio_instance: Istanza SocketIO
    """
    socketio_instance.on_event('game_event', handle_game_event)
    socketio_instance.on_event('player_input', handle_player_input)
    socketio_instance.on_event('request_game_state', handle_request_game_state)
    
    logger.info("Handler degli eventi di gioco registrati") 