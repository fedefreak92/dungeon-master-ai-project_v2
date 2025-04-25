import logging
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
        
        # Emetti anche evento attraverso EventBus
        event_bus = EventBus.get_instance()
        event_bus.emit(Events.UI_DIALOG_OPEN, 
                      dialog_id="dialogo_principale",
                      npc_id=npg.id if hasattr(npg, "id") else None,
                      session_id=id_sessione,
                      dialog_data=dati_conversazione)
        
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
        # Ottieni la sessione
        sessione = core.get_session(id_sessione)
        if not sessione:
            emit('error', {'message': 'Sessione non trovata'})
            return
            
        # Ottieni lo stato dialogo
        dialogo_state = sessione.get_state("dialogo")
        if not dialogo_state:
            emit('error', {'message': 'Stato dialogo non disponibile'})
            return
            
        # Ottieni i dati della conversazione per lo stato corrente
        npg = dialogo_state.npg
        stato_corrente = dialogo_state.stato_corrente
        dati_conversazione = npg.ottieni_conversazione(stato_corrente)
        
        if dati_conversazione and "opzioni" in dati_conversazione:
            opzioni = dati_conversazione["opzioni"]
            if scelta_indice < len(opzioni):
                testo_opzione, destinazione = opzioni[scelta_indice]
                
                # Emetti evento attraverso EventBus
                event_bus = EventBus.get_instance()
                event_bus.emit(Events.DIALOG_CHOICE, 
                              choice=testo_opzione,
                              dialog_id=stato_corrente,
                              destination=destinazione,
                              session_id=id_sessione)
                
                # Se la destinazione è None, termina il dialogo
                if destinazione is None:
                    event_bus.emit(Events.UI_DIALOG_CLOSE, session_id=id_sessione)
                    socketio.emit('cambio_stato', {
                        'stato': 'precedente',
                        'parametri': {}
                    }, room=room_id)
                    emit('dialogo_aggiornato', {
                        'success': True,
                        'terminato': True
                    })
                else:
                    # Aggiorna lo stato corrente del dialogo
                    dialogo_state.stato_corrente = destinazione
                    dialogo_state.dati_contestuali["mostrato_dialogo_corrente"] = False
                    
                    # Ottieni i dati della nuova conversazione
                    dati_nuova_conversazione = npg.ottieni_conversazione(destinazione)
                    
                    # Salva la sessione aggiornata
                    salva_sessione(id_sessione, sessione)
                    
                    # Emetti evento per aggiornare l'interfaccia
                    emit('dialogo_aggiornato', {
                        'success': True,
                        'dialogo': dati_nuova_conversazione,
                        'terminato': False
                    })
            else:
                emit('error', {'message': 'Indice scelta non valido'})
        else:
            emit('error', {'message': 'Opzioni dialogo non disponibili'})
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
        # Ottieni la sessione
        sessione = core.get_session(id_sessione)
        if not sessione:
            emit('error', {'message': 'Sessione non trovata'})
            return
            
        # Ottieni lo stato dialogo
        dialogo_state = sessione.get_state("dialogo")
        if not dialogo_state:
            emit('error', {'message': 'Stato dialogo non disponibile'})
            return
            
        # Applica l'effetto
        dialogo_state._gestisci_effetto(effetto, sessione)
        
        # Emetti evento attraverso EventBus
        event_bus = EventBus.get_instance()
        npg = dialogo_state.npg
        event_bus.emit(Events.INVENTORY_ITEM_USED, 
                      effect_type=effetto if isinstance(effetto, str) else effetto.get("tipo", ""),
                      source_entity=npg.id if hasattr(npg, "id") else None,
                      target_entity=sessione.giocatore.id if hasattr(sessione, "giocatore") else None,
                      session_id=id_sessione)
        
        # Salva la sessione aggiornata
        salva_sessione(id_sessione, sessione)
        
        emit('dialogo_effetto_applicato', {
            'success': True,
            'effetto': effetto
        })
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
    
    # Ottieni l'EventBus
    event_bus = EventBus.get_instance()
    
    # Gestisci l'azione del menu
    if action == "Info Personaggio":
        # Emetti evento per mostrare info del personaggio
        event_bus.emit(Events.UI_DIALOG_OPEN, 
                      dialog_id="info_npg",
                      session_id=id_sessione)
        
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
        # Emetti evento per mostrare inventario dell'NPG
        event_bus.emit(Events.UI_DIALOG_OPEN, 
                      dialog_id="inventario_npg",
                      session_id=id_sessione)
        
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
        # Emetti evento per terminare il dialogo
        event_bus.emit(Events.UI_DIALOG_CLOSE, session_id=id_sessione)
        
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
    
    # Ottieni il WebSocketEventBridge per registrare ulteriori handler
    from server.websocket.websocket_event_bridge import WebSocketEventBridge
    bridge = WebSocketEventBridge.get_instance()
    
    # Aggiungi handler per eventi specifici del dialogo
    bridge.on('dialog_choice', handle_dialog_choice_ws)
    bridge.on('dialog_menu_action', handle_dialog_menu_action_ws)
    
    logger.info("Handler WebSocket del dialogo registrati")
    
def handle_dialog_choice_ws(client_id, data):
    """
    Handler per le scelte di dialogo inviate tramite WebSocket
    
    Args:
        client_id: ID del client
        data: Dati dell'evento
    """
    # Simula formato dati per il handler esistente
    handle_dialogo_scelta({
        'id_sessione': data.get('session_id'),
        'scelta_indice': data.get('choice_index', 0)
    })
    
def handle_dialog_menu_action_ws(client_id, data):
    """
    Handler per le azioni del menu contestuale inviate tramite WebSocket
    
    Args:
        client_id: ID del client
        data: Dati dell'evento
    """
    # Simula formato dati per il handler esistente
    handle_dialogo_menu_action({
        'id_sessione': data.get('session_id'),
        'action': data.get('action')
    }) 