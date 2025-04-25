import logging
import json
import requests
from flask_socketio import emit, join_room

# Import moduli locali
from server.utils.session import get_session, salva_sessione
from . import socketio, graphics_renderer
from . import core
from core.event_bus import EventBus
import core.events as Events

# Configura il logger
logger = logging.getLogger(__name__)

def handle_taverna_inizializza(data):
    """
    Inizializza lo stato taverna e invia i dati iniziali al client
    
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
    
    # Ottieni lo stato taverna
    taverna_state = sessione.get_state("taverna")
    if not taverna_state:
        emit('error', {'message': 'Stato taverna non disponibile'})
        return
    
    # Crea il room_id per questa sessione
    room_id = f"session_{id_sessione}"
    join_room(room_id)
    
    # Preparazione dati iniziali
    dati_taverna = {
        "stato": taverna_state.to_dict(),
        "npg_presenti": {nome: npg.to_dict() for nome, npg in taverna_state.npg_presenti.items()},
        "oggetti_interattivi": {id: obj.to_dict() for id, obj in taverna_state.oggetti_interattivi.items()}
    }
    
    # Ottieni la mappa della taverna se disponibile
    try:
        mappa = sessione.gestore_mappe.ottieni_mappa("taverna")
        if mappa:
            dati_taverna["mappa"] = mappa.to_dict()
            # Aggiungi la posizione del giocatore
            giocatore = sessione.giocatore
            posizione = giocatore.get_posizione("taverna")
            dati_taverna["posizione_giocatore"] = {"x": posizione[0], "y": posizione[1]}
    except Exception as e:
        logger.error(f"Errore nel recupero della mappa: {e}")
    
    # Invia i dati iniziali al client
    emit('taverna_inizializzata', dati_taverna)
    
    # Aggiorna il renderer
    try:
        graphics_renderer.render_taverna(taverna_state, sessione)
    except Exception as e:
        logger.error(f"Errore durante il rendering della taverna: {e}")

def handle_taverna_interagisci(data):
    """
    Gestisce l'interazione con un oggetto nella taverna
    
    Args:
        data (dict): Contiene id_sessione e oggetto_id
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'oggetto_id']):
        return
        
    id_sessione = data['id_sessione']
    oggetto_id = data['oggetto_id']
    
    # Crea il room_id per questa sessione
    room_id = f"session_{id_sessione}"
    
    try:
        # Ottieni la sessione
        sessione = core.get_session(id_sessione)
        if not sessione:
            emit('error', {'message': 'Sessione non trovata'})
            return
            
        # Ottieni lo stato taverna
        taverna_state = sessione.get_state("taverna")
        if not taverna_state:
            emit('error', {'message': 'Stato taverna non disponibile'})
            return
        
        # Verifica se lo stato supporta EventBus
        if hasattr(taverna_state, 'event_bus'):
            # Usa l'EventBus per emettere l'evento di interazione
            taverna_state.emit_event(Events.PLAYER_INTERACT, 
                                    interaction_type="object", 
                                    entity_id=oggetto_id)
                                    
            # Emetti evento per aggiornare l'interfaccia
            emit('taverna_oggetto_interagito', {
                'oggetto_id': oggetto_id,
                'risultato': "Interazione avviata"
            })
            
            # Aggiorna il renderer
            graphics_renderer.render_taverna(taverna_state, sessione)
        else:
            # Fallback al vecchio metodo REST
            response = requests.post(
                "http://localhost:5000/game/taverna/interagisci",
                json={
                    "id_sessione": id_sessione,
                    "oggetto_id": oggetto_id
                }
            )
            
            if response.status_code == 200:
                result_data = response.json()
                
                # Emetti evento per aggiornare l'interfaccia
                emit('taverna_oggetto_interagito', {
                    'oggetto_id': oggetto_id,
                    'risultato': result_data.get('risultato')
                })
                
                # Emetti anche un evento per tutti i client nella stessa sessione
                socketio.emit('taverna_oggetto_interagito', {
                    'oggetto_id': oggetto_id,
                    'risultato': result_data.get('risultato')
                }, room=room_id)
                
                # Aggiorna il renderer
                graphics_renderer.render_taverna(taverna_state, sessione)
            else:
                emit('error', {'message': 'Errore nell\'interazione con l\'oggetto'})
    except Exception as e:
        logger.error(f"Errore nell'interazione con l'oggetto: {e}")
        emit('error', {'message': f'Errore interno: {str(e)}'})

def handle_taverna_dialoga(data):
    """
    Gestisce il dialogo con un NPG nella taverna
    
    Args:
        data (dict): Contiene id_sessione, npg_nome e opzionalmente opzione_scelta
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'npg_nome']):
        return
        
    id_sessione = data['id_sessione']
    npg_nome = data['npg_nome']
    opzione_scelta = data.get('opzione_scelta')
    
    # Crea il room_id per questa sessione
    room_id = f"session_{id_sessione}"
    
    try:
        # Ottieni la sessione
        sessione = core.get_session(id_sessione)
        if not sessione:
            emit('error', {'message': 'Sessione non trovata'})
            return
            
        # Ottieni lo stato taverna
        taverna_state = sessione.get_state("taverna")
        if not taverna_state:
            emit('error', {'message': 'Stato taverna non disponibile'})
            return
        
        # Verifica se lo stato supporta EventBus
        if hasattr(taverna_state, 'event_bus'):
            # Usa l'EventBus per emettere l'evento di dialogo
            taverna_state.emit_event("TAVERNA_DIALOGO_INIZIATO", 
                                   npg_id=npg_nome)
                                   
            # Se c'è un'opzione scelta, emetti anche l'evento di selezione dialogo
            if opzione_scelta:
                taverna_state.emit_event(Events.DIALOG_CHOICE, 
                                       npg_id=npg_nome,
                                       choice=opzione_scelta)
            
            # Emetti evento per aggiornare l'interfaccia
            emit('taverna_dialogo_aggiornato', {
                'npg_nome': npg_nome,
                'dialogo': "Dialogo avviato"
            })
            
            # Aggiorna il renderer
            graphics_renderer.render_taverna(taverna_state, sessione)
        else:
            # Fallback al vecchio metodo REST
            response = requests.post(
                "http://localhost:5000/game/taverna/dialoga",
                json={
                    "id_sessione": id_sessione,
                    "npg_nome": npg_nome,
                    "opzione_scelta": opzione_scelta
                }
            )
            
            if response.status_code == 200:
                result_data = response.json()
                
                # Emetti evento per aggiornare l'interfaccia
                emit('taverna_dialogo_aggiornato', {
                    'npg_nome': npg_nome,
                    'dialogo': result_data.get('dialogo')
                })
                
                # Emetti anche un evento per tutti i client nella stessa sessione
                socketio.emit('taverna_dialogo_aggiornato', {
                    'npg_nome': npg_nome,
                    'dialogo': result_data.get('dialogo')
                }, room=room_id)
            else:
                emit('error', {'message': 'Errore nel dialogo con l\'NPG'})
    except Exception as e:
        logger.error(f"Errore nel dialogo con l'NPG: {e}")
        emit('error', {'message': f'Errore interno: {str(e)}'})

def handle_taverna_menu(data):
    """
    Gestisce l'interazione con i menu della taverna
    
    Args:
        data (dict): Contiene id_sessione, menu_id e opzionalmente scelta
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'menu_id']):
        return
        
    id_sessione = data['id_sessione']
    menu_id = data['menu_id']
    scelta = data.get('scelta')
    
    # Crea il room_id per questa sessione
    room_id = f"session_{id_sessione}"
    
    try:
        # Ottieni la sessione
        sessione = core.get_session(id_sessione)
        if not sessione:
            emit('error', {'message': 'Sessione non trovata'})
            return
            
        # Ottieni lo stato taverna
        taverna_state = sessione.get_state("taverna")
        if not taverna_state:
            emit('error', {'message': 'Stato taverna non disponibile'})
            return
        
        # Verifica se lo stato supporta EventBus
        if hasattr(taverna_state, 'event_bus'):
            # Usa l'EventBus per emettere l'evento di cambio menu
            taverna_state.emit_event(Events.MENU_CHANGED, menu_id=menu_id)
            
            # Se c'è una scelta, emetti anche l'evento di selezione menu
            if scelta:
                taverna_state.emit_event(Events.MENU_SELECTION, 
                                       menu_id=menu_id,
                                       selection=scelta)
            
            # Emetti evento per aggiornare l'interfaccia
            emit('taverna_menu_aggiornato', {
                'menu_id': menu_id,
                'risultato': "Menu aggiornato"
            })
            
            # Aggiorna il renderer
            graphics_renderer.render_taverna(taverna_state, sessione)
        else:
            # Fallback al vecchio metodo REST
            response = requests.post(
                "http://localhost:5000/game/taverna/menu",
                json={
                    "id_sessione": id_sessione,
                    "menu_id": menu_id,
                    "scelta": scelta
                }
            )
            
            if response.status_code == 200:
                result_data = response.json()
                
                # Emetti evento per aggiornare l'interfaccia
                emit('taverna_menu_aggiornato', {
                    'menu_id': menu_id,
                    'risultato': result_data.get('risultato')
                })
                
                # Emetti anche un evento per tutti i client nella stessa sessione
                socketio.emit('taverna_menu_aggiornato', {
                    'menu_id': menu_id,
                    'risultato': result_data.get('risultato')
                }, room=room_id)
                
                # Aggiorna il renderer
                graphics_renderer.render_taverna(taverna_state, sessione)
            else:
                emit('error', {'message': 'Errore nella gestione del menu'})
    except Exception as e:
        logger.error(f"Errore nella gestione del menu: {e}")
        emit('error', {'message': f'Errore interno: {str(e)}'})

def handle_taverna_movimento(data):
    """
    Gestisce il movimento nella taverna
    
    Args:
        data (dict): Contiene id_sessione e direzione
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'direzione']):
        return
        
    id_sessione = data['id_sessione']
    direzione = data['direzione']
    
    # Crea il room_id per questa sessione
    room_id = f"session_{id_sessione}"
    
    try:
        # Ottieni la sessione
        sessione = core.get_session(id_sessione)
        if not sessione:
            emit('error', {'message': 'Sessione non trovata'})
            return
            
        # Ottieni lo stato taverna
        taverna_state = sessione.get_state("taverna")
        if not taverna_state:
            emit('error', {'message': 'Stato taverna non disponibile'})
            return
        
        # Verifica se lo stato supporta EventBus
        if hasattr(taverna_state, 'event_bus'):
            # Usa l'EventBus per emettere l'evento di movimento
            taverna_state.emit_event(Events.PLAYER_MOVE, direction=direzione)
            
            # Recupera la nuova posizione del giocatore
            giocatore = sessione.giocatore
            posizione = giocatore.get_posizione("taverna")
            
            # Emetti evento per aggiornare l'interfaccia
            emit('taverna_movimento_effettuato', {
                'direzione': direzione,
                'posizione': {'x': posizione[0], 'y': posizione[1]}
            })
            
            # Aggiorna il renderer
            graphics_renderer.render_taverna(taverna_state, sessione)
        else:
            # Fallback al vecchio metodo REST
            response = requests.post(
                "http://localhost:5000/game/taverna/movimento",
                json={
                    "id_sessione": id_sessione,
                    "direzione": direzione
                }
            )
            
            if response.status_code == 200:
                result_data = response.json()
                
                # Emetti evento per aggiornare l'interfaccia
                emit('taverna_movimento_effettuato', {
                    'direzione': direzione,
                    'posizione': result_data.get('posizione')
                })
                
                # Emetti anche un evento per tutti i client nella stessa sessione
                socketio.emit('taverna_movimento_effettuato', {
                    'direzione': direzione,
                    'posizione': result_data.get('posizione')
                }, room=room_id)
                
                # Aggiorna il renderer
                graphics_renderer.render_taverna(taverna_state, sessione)
            else:
                emit('error', {'message': 'Errore nel movimento'})
    except Exception as e:
        logger.error(f"Errore nel movimento: {e}")
        emit('error', {'message': f'Errore interno: {str(e)}'})

def handle_taverna_transizione(data):
    """
    Gestisce la transizione da/verso la taverna
    
    Args:
        data (dict): Contiene id_sessione, destinazione e eventuali parametri
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'destinazione']):
        return
        
    id_sessione = data['id_sessione']
    destinazione = data['destinazione']
    parametri = data.get('parametri', {})
    
    # Crea il room_id per questa sessione
    room_id = f"session_{id_sessione}"
    
    try:
        # Ottieni la sessione
        sessione = core.get_session(id_sessione)
        if not sessione:
            emit('error', {'message': 'Sessione non trovata'})
            return
            
        # Ottieni lo stato taverna
        taverna_state = sessione.get_state("taverna")
        if not taverna_state:
            emit('error', {'message': 'Stato taverna non disponibile'})
            return
        
        # Verifica se lo stato supporta EventBus
        if hasattr(taverna_state, 'event_bus'):
            # Usa l'EventBus per emettere l'evento di transizione
            if destinazione.lower() == "esci":
                taverna_state.emit_event(Events.POP_STATE)
            else:
                taverna_state.emit_event(Events.PUSH_STATE, 
                                       state_class=destinazione,
                                       **parametri)
            
            # Emetti evento per aggiornare l'interfaccia
            emit('taverna_transizione_effettuata', {
                'destinazione': destinazione
            })
        else:
            # Fallback al vecchio metodo REST
            response = requests.post(
                "http://localhost:5000/game/taverna/transizione",
                json={
                    "id_sessione": id_sessione,
                    "destinazione": destinazione,
                    "parametri": parametri
                }
            )
            
            if response.status_code == 200:
                result_data = response.json()
                
                # Emetti evento per aggiornare l'interfaccia
                emit('taverna_transizione_effettuata', {
                    'destinazione': destinazione,
                    'risultato': result_data.get('risultato')
                })
                
                # Emetti anche un evento per tutti i client nella stessa sessione
                socketio.emit('taverna_transizione_effettuata', {
                    'destinazione': destinazione,
                    'risultato': result_data.get('risultato')
                }, room=room_id)
            else:
                emit('error', {'message': 'Errore nella transizione'})
    except Exception as e:
        logger.error(f"Errore nella transizione: {e}")
        emit('error', {'message': f'Errore interno: {str(e)}'})

def register_handlers(socketio_instance):
    """
    Registra gli handler WebSocket per la taverna
    
    Args:
        socketio_instance: Istanza SocketIO
    """
    socketio_instance.on_event('taverna_inizializza', handle_taverna_inizializza)
    socketio_instance.on_event('taverna_interagisci', handle_taverna_interagisci)
    socketio_instance.on_event('taverna_dialoga', handle_taverna_dialoga)
    socketio_instance.on_event('taverna_menu', handle_taverna_menu)
    socketio_instance.on_event('taverna_movimento', handle_taverna_movimento)
    socketio_instance.on_event('taverna_transizione', handle_taverna_transizione)
    
    logger.info("Handler WebSocket della taverna registrati") 