import logging
import requests
from flask_socketio import emit, join_room

# Import moduli locali
from server.utils.session import get_session, salva_sessione
from . import socketio, graphics_renderer
from . import core

# Configura il logger
logger = logging.getLogger(__name__)

def handle_dialogo_inizializza(data):
    """
    Inizializza lo stato DialogoState e invia i dati iniziali al client
    
    Args:
        data (dict): Contiene id_sessione e parametri del dialogo
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione']):
        return
        
    id_sessione = data['id_sessione']
    
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        return
    
    # Ottieni lo stato dialogo
    dialogo_state = sessione.get_state("dialogo")
    if not dialogo_state:
        emit('error', {'message': 'Stato dialogo non disponibile'})
        return
    
    # Crea il room_id per questa sessione
    room_id = f"session_{id_sessione}"
    join_room(room_id)
    
    # Invia i dati iniziali del dialogo
    npg = dialogo_state.npg
    stato_corrente = dialogo_state.stato_corrente
    
    if npg:
        # Ottieni i dati della conversazione corrente
        dati_conversazione = npg.ottieni_conversazione(stato_corrente)
        
        # Prepara la risposta
        risposta = {
            'success': True,
            'npg': {
                'nome': npg.nome,
                'descrizione': getattr(npg, 'descrizione', ''),
                'immagine': getattr(npg, 'immagine', 'npc_default')
            },
            'dialogo': dati_conversazione
        }
        
        emit('dialogo_inizializzato', risposta)
    else:
        emit('error', {'message': 'NPG non trovato nel dialogo'})

def handle_dialogo_scelta(data):
    """
    Gestisce una scelta fatta durante il dialogo
    
    Args:
        data (dict): Contiene id_sessione e scelta_indice
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'scelta_indice']):
        return
        
    id_sessione = data['id_sessione']
    scelta_indice = data['scelta_indice']
    
    # Crea il room_id per questa sessione
    room_id = f"session_{id_sessione}"
    
    try:
        # Usa l'endpoint per gestire la scelta
        response = requests.post(
            "http://localhost:5000/game/dialogo/scelta",
            json={
                "id_sessione": id_sessione,
                "scelta_indice": scelta_indice
            }
        )
        
        if response.status_code == 200:
            result_data = response.json()
            
            # Emetti evento per aggiornare l'interfaccia
            emit('dialogo_aggiornato', {
                'success': True,
                'dialogo': result_data.get('dialogo'),
                'terminato': result_data.get('terminato', False)
            })
            
            # Se il dialogo è terminato, emetti un evento di cambio stato
            if result_data.get('terminato', False):
                socketio.emit('cambio_stato', {
                    'stato': 'precedente',
                    'parametri': {}
                }, room=room_id)
        else:
            emit('error', {'message': 'Errore nella scelta del dialogo'})
    except Exception as e:
        logger.error(f"Errore nella gestione della scelta: {e}")
        emit('error', {'message': f'Errore interno: {str(e)}'})

def handle_dialogo_effetto(data):
    """
    Gestisce un effetto durante il dialogo
    
    Args:
        data (dict): Contiene id_sessione ed effetto
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'effetto']):
        return
        
    id_sessione = data['id_sessione']
    effetto = data['effetto']
    
    try:
        # Usa l'endpoint per gestire l'effetto
        response = requests.post(
            "http://localhost:5000/game/dialogo/effetto",
            json={
                "id_sessione": id_sessione,
                "effetto": effetto
            }
        )
        
        if response.status_code == 200:
            emit('dialogo_effetto_applicato', {
                'success': True,
                'effetto': effetto
            })
        else:
            emit('error', {'message': 'Errore nell\'applicazione dell\'effetto'})
    except Exception as e:
        logger.error(f"Errore nella gestione dell'effetto: {e}")
        emit('error', {'message': f'Errore interno: {str(e)}'})

def handle_dialogo_menu_action(data):
    """
    Gestisce le azioni del menu contestuale durante il dialogo
    
    Args:
        data (dict): Contiene id_sessione e action
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'action']):
        return
        
    id_sessione = data['id_sessione']
    action = data['action']
    
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        return
    
    # Ottieni lo stato dialogo
    dialogo_state = sessione.get_state("dialogo")
    if not dialogo_state:
        emit('error', {'message': 'Stato dialogo non disponibile'})
        return
    
    # Simula l'azione del menu
    if action == "Info Personaggio":
        # Mostra info del personaggio
        npg = dialogo_state.npg
        if npg:
            info = {
                'nome': npg.nome,
                'descrizione': getattr(npg, 'descrizione', ''),
                'professione': getattr(npg, 'professione', '')
            }
            emit('dialogo_info_npg', info)
    elif action == "Mostra Inventario":
        # Mostra inventario dell'NPG
        npg = dialogo_state.npg
        if npg and hasattr(npg, 'inventario'):
            items = []
            for item in npg.inventario:
                if hasattr(item, 'nome'):
                    items.append(item.nome)
                else:
                    items.append(str(item))
            
            emit('dialogo_inventario_npg', {
                'npg_nome': npg.nome,
                'items': items
            })
    elif action == "Termina Dialogo":
        # Termina il dialogo
        sessione.pop_stato()
        salva_sessione(id_sessione, sessione)
        
        # Notifica la fine del dialogo
        room_id = f"session_{id_sessione}"
        socketio.emit('cambio_stato', {
            'stato': 'precedente',
            'parametri': {}
        }, room=room_id)
        
        emit('dialogo_terminato', {'success': True})

def register_handlers(socketio_instance):
    """
    Registra gli handler WebSocket per il dialogo
    
    Args:
        socketio_instance: Istanza di Flask-SocketIO
    """
    socketio_instance.on_event('dialogo_inizializza', handle_dialogo_inizializza)
    socketio_instance.on_event('dialogo_scelta', handle_dialogo_scelta)
    socketio_instance.on_event('dialogo_effetto', handle_dialogo_effetto)
    socketio_instance.on_event('dialogo_menu_action', handle_dialogo_menu_action)
    
    logger.info("Handler WebSocket del dialogo registrati") 