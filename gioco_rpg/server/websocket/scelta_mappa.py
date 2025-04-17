import logging
import json
import requests
from flask_socketio import emit, join_room

# Import moduli locali
from server.utils.session import get_session, salva_sessione
from . import socketio, graphics_renderer
from . import core
from .rendering import render_scelta_mappa

# Configura il logger
logger = logging.getLogger(__name__)

def handle_scelta_mappa_inizializza(data):
    """
    Inizializza lo stato SceltaMappaState e invia i dati iniziali al client
    
    Args:
        data (dict): Contiene id_sessione e eventuali parametri aggiuntivi
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione']):
        return
        
    id_sessione = data['id_sessione']
    
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        return
    
    # Ottieni lo stato scelta_mappa
    scelta_mappa_state = sessione.get_state("scelta_mappa")
    if not scelta_mappa_state:
        emit('error', {'message': 'Stato scelta_mappa non disponibile'})
        return
    
    # Crea il room_id per questa sessione
    room_id = f"session_{id_sessione}"
    join_room(room_id)
    
    # Ottieni la lista delle mappe disponibili
    try:
        response = requests.get(
            "http://localhost:5000/game/scelta_mappa/liste_mappe",
            params={"id_sessione": id_sessione}
        )
        
        if response.status_code == 200:
            result_data = response.json()
            
            # Preparazione dati iniziali
            dati_scelta_mappa = {
                "stato": scelta_mappa_state.to_dict(),
                "mappe": result_data.get("mappe", {}),
                "mappa_corrente": result_data.get("mappa_corrente")
            }
            
            # Invia i dati iniziali al client
            emit('scelta_mappa_inizializzata', dati_scelta_mappa)
            
            # Esegui il rendering della scelta mappa
            render_scelta_mappa(scelta_mappa_state, sessione)
        else:
            emit('error', {'message': 'Errore nel recupero delle mappe disponibili'})
    except Exception as e:
        logger.error(f"Errore nell'inizializzazione dello stato scelta_mappa: {e}")
        emit('error', {'message': f'Errore interno: {str(e)}'})

def handle_scelta_mappa_cambia(data):
    """
    Gestisce la richiesta di cambio mappa
    
    Args:
        data (dict): Contiene id_sessione e id_mappa
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'id_mappa']):
        return
        
    id_sessione = data['id_sessione']
    id_mappa = data['id_mappa']
    
    # Crea il room_id per questa sessione
    room_id = f"session_{id_sessione}"
    
    try:
        # Usa l'endpoint per cambiare mappa
        response = requests.post(
            "http://localhost:5000/game/scelta_mappa/cambia_mappa",
            json={
                "id_sessione": id_sessione,
                "id_mappa": id_mappa
            }
        )
        
        if response.status_code == 200:
            result_data = response.json()
            
            # Emetti evento per aggiornare l'interfaccia
            emit('scelta_mappa_cambiata', {
                'success': True,
                'mappa': result_data.get('mappa'),
                'posizione': result_data.get('posizione')
            })
            
            # Emetti anche un evento per tutti i client nella stessa sessione
            socketio.emit('scelta_mappa_cambiata', {
                'success': True,
                'mappa': result_data.get('mappa'),
                'posizione': result_data.get('posizione')
            }, room=room_id)
            
            # Notifica la transizione di stato
            socketio.emit('cambio_stato', {
                'stato': 'mappa',
                'parametri': {}
            }, room=room_id)
        elif response.status_code == 403:
            # Livello insufficiente
            result_data = response.json()
            emit('error', {'message': result_data.get('error')})
            emit('livello_insufficiente', {
                'id_mappa': id_mappa,
                'error': result_data.get('error')
            })
            
            # Ottieni lo stato e la sessione per il re-rendering
            sessione = core.get_session(id_sessione)
            if sessione:
                scelta_mappa_state = sessione.get_state("scelta_mappa")
                if scelta_mappa_state:
                    # Aggiorna il renderer con il messaggio di errore
                    render_scelta_mappa(scelta_mappa_state, sessione)
        else:
            emit('error', {'message': 'Errore nel cambio mappa'})
    except Exception as e:
        logger.error(f"Errore nel cambio mappa: {e}")
        emit('error', {'message': f'Errore interno: {str(e)}'})

def handle_scelta_mappa_annulla(data):
    """
    Gestisce l'annullamento della scelta mappa e il ritorno allo stato precedente
    
    Args:
        data (dict): Contiene id_sessione
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione']):
        return
        
    id_sessione = data['id_sessione']
    
    # Crea il room_id per questa sessione
    room_id = f"session_{id_sessione}"
    
    try:
        # Ottieni la sessione
        sessione = core.get_session(id_sessione)
        if not sessione:
            emit('error', {'message': 'Sessione non trovata'})
            return
            
        # Esegui il pop dello stato per tornare allo stato precedente
        sessione.pop_stato()
        
        # Salva la sessione
        salva_sessione(id_sessione, sessione)
        
        # Ottieni lo stato corrente dopo il pop
        stato_corrente = sessione.stato_corrente()
        nome_stato = stato_corrente.nome_stato if stato_corrente else None
        
        # Emetti evento per notificare il cambio di stato
        socketio.emit('cambio_stato', {
            'stato': nome_stato,
            'parametri': {}
        }, room=room_id)
        
        emit('scelta_mappa_annullata', {'success': True})
    except Exception as e:
        logger.error(f"Errore nell'annullamento della scelta mappa: {e}")
        emit('error', {'message': f'Errore interno: {str(e)}'})

def handle_scelta_mappa_dialog_choice(data):
    """
    Gestisce le scelte dai dialoghi nella scelta mappa
    
    Args:
        data (dict): Contiene id_sessione e choice (scelta selezionata)
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'choice']):
        return
        
    id_sessione = data['id_sessione']
    choice = data['choice']
    
    # Crea il room_id per questa sessione
    room_id = f"session_{id_sessione}"
    
    try:
        # Ottieni la sessione
        sessione = core.get_session(id_sessione)
        if not sessione:
            emit('error', {'message': 'Sessione non trovata'})
            return
            
        # Ottieni lo stato scelta_mappa
        scelta_mappa_state = sessione.get_state("scelta_mappa")
        if not scelta_mappa_state:
            emit('error', {'message': 'Stato scelta_mappa non disponibile'})
            return
        
        # Se la scelta è "Torna indietro", gestisci il ritorno allo stato precedente
        if choice == "Torna indietro":
            # Esegui la stessa logica di handle_scelta_mappa_annulla
            sessione.pop_stato()
            salva_sessione(id_sessione, sessione)
            
            # Ottieni lo stato corrente dopo il pop
            stato_corrente = sessione.stato_corrente()
            nome_stato = stato_corrente.nome_stato if stato_corrente else None
            
            # Emetti evento per notificare il cambio di stato
            socketio.emit('cambio_stato', {
                'stato': nome_stato,
                'parametri': {}
            }, room=room_id)
            
            emit('scelta_mappa_annullata', {'success': True})
            return
        
        # Estrai il nome della mappa dalla scelta
        nome_mappa = choice.split(" [")[0].split(" (")[0]
        
        # Trova la mappa corrispondente
        lista_mappe = sessione.gestore_mappe.ottieni_lista_mappe()
        id_mappa_selezionata = None
        
        for id_mappa, info_mappa in lista_mappe.items():
            if info_mappa.get("nome", id_mappa) == nome_mappa:
                id_mappa_selezionata = id_mappa
                break
        
        if id_mappa_selezionata:
            # Usa l'endpoint per cambiare mappa
            response = requests.post(
                "http://localhost:5000/game/scelta_mappa/cambia_mappa",
                json={
                    "id_sessione": id_sessione,
                    "id_mappa": id_mappa_selezionata
                }
            )
            
            if response.status_code == 200:
                result_data = response.json()
                
                # Emetti evento per aggiornare l'interfaccia
                emit('scelta_mappa_cambiata', {
                    'success': True,
                    'mappa': result_data.get('mappa'),
                    'posizione': result_data.get('posizione')
                })
                
                # Emetti anche un evento per tutti i client nella stessa sessione
                socketio.emit('scelta_mappa_cambiata', {
                    'success': True,
                    'mappa': result_data.get('mappa'),
                    'posizione': result_data.get('posizione')
                }, room=room_id)
                
                # Notifica la transizione di stato
                socketio.emit('cambio_stato', {
                    'stato': 'mappa',
                    'parametri': {}
                }, room=room_id)
            elif response.status_code == 403:
                # Livello insufficiente
                result_data = response.json()
                emit('error', {'message': result_data.get('error')})
                
                # Rirender dopo l'errore
                render_scelta_mappa(scelta_mappa_state, sessione)
            else:
                emit('error', {'message': 'Errore nel cambio mappa'})
        else:
            emit('error', {'message': 'Mappa non trovata: ' + nome_mappa})
    except Exception as e:
        logger.error(f"Errore nella gestione della scelta di dialogo: {e}")
        emit('error', {'message': f'Errore interno: {str(e)}'})

def register_handlers(socketio_instance):
    """
    Registra gli handler WebSocket per lo stato SceltaMappaState
    
    Args:
        socketio_instance: Istanza di Flask-SocketIO
    """
    socketio_instance.on_event('scelta_mappa_inizializza', handle_scelta_mappa_inizializza)
    socketio_instance.on_event('scelta_mappa_cambia', handle_scelta_mappa_cambia)
    socketio_instance.on_event('scelta_mappa_annulla', handle_scelta_mappa_annulla)
    socketio_instance.on_event('scelta_mappa_dialog_choice', handle_scelta_mappa_dialog_choice)
    
    logger.info("Handler WebSocket della scelta mappa registrati") 