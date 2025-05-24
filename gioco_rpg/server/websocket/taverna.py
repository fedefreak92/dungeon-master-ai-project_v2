import asyncio
# from functools import partial # Non più usato
from flask_socketio import SocketIO, emit
from engineio.payload import Payload

# from বিশ্ব.게임_상태_저장_서비스 import GameStateService # RIMOSSO
# from entities.giocatore import Giocatore # RIMOSSO se non usato direttamente
# from server.init.database import db # RIMOSSO
from util.logging_config import get_logger # MODIFICATO
# from server.websocket.connection import ConnectionManager, authenticated_async # RIMOSSO
# from server.websocket.game_events import GameEventService # RIMOSSO
# from server.websocket.rendering import RenderingService # RIMOSSO
from server.websocket.websocket_manager import WebSocketManager
from states.mappa.mappa_state import MappaState
from core.event_bus import EventBus

logger = get_logger(__name__) # AGGIUNTO

Payload.max_decode_packets = 500

WEBSOCKET_TAVERNA_SERVICE_INSTANCE = None

def _get_valid_mappa_state_or_emit_error(sid, nome_luogo_atteso):
    """
    Recupera lo stato MappaState valido per il SID e il nome_luogo atteso.
    Emette un errore via WebSocket e logga se lo stato non è valido.
    Restituisce (MappaState | None, user_id | None).
    """
    websocket_manager = WebSocketManager.get_instance()
    if not websocket_manager or not hasattr(websocket_manager, 'connection_manager'):
        emit('errore_stato', {'errore': 'WebSocketManager non inizializzato correttamente.', 'details': 'connection_manager_missing'}, room=sid)
        logger.error("WebSocketManager o connection_manager non disponibile in _get_valid_mappa_state_or_emit_error.")
        return None, None 
        
    user_id = websocket_manager.connection_manager.get_user_id(sid)
    if not user_id:
        emit('errore_stato', {'errore': 'Utente non autenticato o sessione non valida.', 'details': 'user_id_missing'}, room=sid)
        logger.warning(f"Auth fallita per SID {sid} in _get_valid_mappa_state_or_emit_error.")
        return None, None
        
    player_instance = None
    # Tenta di ottenere player_instance tramite un metodo diretto se esiste
    if hasattr(websocket_manager, 'get_player_instance_by_sid'):
        player_instance = websocket_manager.get_player_instance_by_sid(sid) 
    
    # Fallback alla logica con session_id se il metodo diretto non ha funzionato
    if not player_instance:
        session_id = websocket_manager.connection_manager.get_session_id(sid)
        if not session_id:
            emit('errore_stato', {'errore': 'ID Sessione non trovato per il SID.', 'details': 'session_id_missing'}, room=sid)
            logger.warning(f"Session ID non trovato per SID {sid} in _get_valid_mappa_state.")
            return None, user_id # user_id potrebbe essere ancora valido per logging
        
        if hasattr(websocket_manager, 'get_player_instance'):
            player_instance = websocket_manager.get_player_instance(session_id)
        else:
            logger.error(f"WebSocketManager non ha il metodo get_player_instance. SID: {sid}")
            emit('errore_stato', {'errore': 'Errore interno del server (player lookup).', 'details': 'player_lookup_method_missing'}, room=sid)
            return None, user_id

    if not player_instance:
        emit('errore_stato', {'errore': f'Istanza giocatore non trovata.', 'details': f'player_instance_missing_for_sid_{sid}'}, room=sid)
        logger.warning(f"Istanza giocatore non trovata per SID {sid} (user_id: {user_id}).")
        return None, user_id
         
    stato_corrente = player_instance.stato_corrente

    if not stato_corrente:
        emit('errore_stato', {'errore': f'Stato corrente non trovato per l\'utente {user_id}.', 'details': 'current_state_missing'}, room=sid)
        logger.warning(f"Stato corrente non trovato per user_id {user_id} (SID: {sid}).")
        return None, user_id

    if not isinstance(stato_corrente, MappaState):
        emit('errore_stato', {'errore': 'Tipo di stato non valido. Non sei in un luogo (MappaState).', 'actual_state': type(stato_corrente).__name__}, room=sid)
        logger.warning(f"Stato non MappaState per user_id {user_id} (SID: {sid}). Stato attuale: {type(stato_corrente).__name__}")
        return None, user_id
    
    if stato_corrente.nome_luogo != nome_luogo_atteso:
        emit('errore_stato', {'errore': f'Non sei nel luogo corretto. Attualmente in "{stato_corrente.nome_luogo}", atteso "{nome_luogo_atteso}".'}, room=sid)
        logger.warning(f"Luogo errato per user_id {user_id} (SID: {sid}). Attuale: {stato_corrente.nome_luogo}, Atteso: {nome_luogo_atteso}")
        return None, user_id
        
    # Verifica e tentativo di sincronizzazione del contesto di gioco in MappaState
    game_context_ok = False
    if hasattr(stato_corrente, 'gioco') and stato_corrente.gioco and \
       hasattr(stato_corrente.gioco, 'giocatore') and stato_corrente.gioco.giocatore == player_instance:
        game_context_ok = True

    if not game_context_ok:
        logger.warning(f"Contesto di gioco in MappaState (luogo: {stato_corrente.nome_luogo}) non allineato per user_id {user_id} (SID: {sid}). Tentativo di impostazione.")
        if hasattr(player_instance, 'game_context') and hasattr(stato_corrente, 'set_game_context'): # Assicurati che player_instance abbia game_context
            stato_corrente.set_game_context(player_instance.game_context) 
            # Riverifica dopo il tentativo di set_game_context
            if hasattr(stato_corrente, 'gioco') and stato_corrente.gioco and \
               hasattr(stato_corrente.gioco, 'giocatore') and stato_corrente.gioco.giocatore == player_instance:
                game_context_ok = True
                logger.info(f"Contesto di gioco REIMPOSTATO con successo per user_id {user_id} in MappaState.")
            
        if not game_context_ok: # Se ancora non ok dopo il tentativo
            logger.error(f"FALLIMENTO IMPOSTAZIONE/VERIFICA CONTESTO GIOCO per user_id {user_id} in MappaState '{stato_corrente.nome_stato}'. Player in context: {getattr(getattr(stato_corrente.gioco, 'giocatore', None), 'nome', 'N/A')}, expected: {player_instance.nome}")
            emit('errore_stato', {'errore': 'Errore interno: contesto di gioco non sincronizzato.', 'details': 'game_context_mismatch'}, room=sid)
            return None, user_id

    logger.debug(f"Stato valido '{stato_corrente.nome_luogo}' (tipo: {type(stato_corrente).__name__}) recuperato per user_id {user_id} (SID: {sid}).")
    return stato_corrente, user_id

def register_taverna_websocket_handlers(socketio_instance: SocketIO):
    """
    Registra gli handler WebSocket per le interazioni nella taverna.
    """
    logger.info("Registrazione handler WebSocket per la Taverna...")

    @socketio_instance.on('muovi_taverna')
    async def handle_muovi_taverna(sid, data):
        logger.debug(f"Evento 'muovi_taverna' ricevuto da SID {sid} con dati: {data}")
        stato_luogo, user_id = _get_valid_mappa_state_or_emit_error(sid, "taverna")
        if stato_luogo and user_id: 
            direzione = data.get('direzione')
            if direzione:
                # Assumendo che process_azione_luogo sia sincrona e potenzialmente CPU-bound
                await asyncio.to_thread(stato_luogo.process_azione_luogo, 
                                        user_id=user_id,
                                        azione="muovi", 
                                        dati_azione={"direzione": direzione})
            else:
                logger.warning(f"Direzione mancante per 'muovi_taverna' da SID {sid}.")
                emit('errore_azione', {'errore': 'Direzione mancante per il movimento.', 'event': 'muovi_taverna'}, room=sid)

    @socketio_instance.on('interagisci_oggetto_taverna')
    async def handle_interagisci_oggetto_taverna(sid, data):
        logger.debug(f"Evento 'interagisci_oggetto_taverna' ricevuto da SID {sid} con dati: {data}")
        stato_luogo, user_id = _get_valid_mappa_state_or_emit_error(sid, "taverna")
        if stato_luogo and user_id:
            oggetto_id = data.get('oggetto_id')
            if oggetto_id:
                await asyncio.to_thread(stato_luogo.process_azione_luogo,
                                        user_id=user_id, 
                                        azione="interagisci_oggetto", 
                                        dati_azione={"oggetto_id": oggetto_id})
            else:
                logger.warning(f"ID oggetto mancante per 'interagisci_oggetto_taverna' da SID {sid}.")
                emit('errore_azione', {'errore': "ID oggetto mancante per l'interazione.", 'event': 'interagisci_oggetto_taverna'}, room=sid)

    @socketio_instance.on('dialoga_npg_taverna')
    async def handle_dialoga_npg_taverna(sid, data):
        logger.debug(f"Evento 'dialoga_npg_taverna' ricevuto da SID {sid} con dati: {data}")
        stato_luogo, user_id = _get_valid_mappa_state_or_emit_error(sid, "taverna")
        if stato_luogo and user_id:
            npg_id = data.get('npg_id')
            opzione_dialogo = data.get('opzione_dialogo') # Può essere None per iniziare
            if npg_id:
                await asyncio.to_thread(stato_luogo.process_azione_luogo,
                                        user_id=user_id, 
                                        azione="dialoga_npg", 
                                        dati_azione={"npg_id": npg_id, "opzione": opzione_dialogo})
            else:
                logger.warning(f"ID NPG mancante per 'dialoga_npg_taverna' da SID {sid}.")
                emit('errore_azione', {'errore': 'ID NPG mancante per il dialogo.', 'event': 'dialoga_npg_taverna'}, room=sid)
    
    @socketio_instance.on('azione_specifica_taverna')
    async def handle_azione_specifica_taverna(sid, data):
        logger.debug(f"Evento 'azione_specifica_taverna' ricevuto da SID {sid} con dati: {data}")
        stato_luogo, user_id = _get_valid_mappa_state_or_emit_error(sid, "taverna")
        if stato_luogo and user_id:
            nome_azione_specifica = data.get('nome_azione') 
            dati_aggiuntivi = data.get('dati_payload')    
            
            if nome_azione_specifica:
                # L'azione viene passata direttamente a process_azione_luogo,
                # che poi la delegherà a _handle_azione_specifica_luogo in MappaState o TavernaState.
                await asyncio.to_thread(stato_luogo.process_azione_luogo,
                                        user_id=user_id,
                                        azione=nome_azione_specifica, 
                                        dati_azione=dati_aggiuntivi if dati_aggiuntivi is not None else {})
            else:
                logger.warning(f"Nome azione specifica mancante per 'azione_specifica_taverna' da SID {sid}.")
                emit('errore_azione', {'errore': 'Nome azione specifica mancante.', 'event': 'azione_specifica_taverna'}, room=sid)

    logger.info("Handler WebSocket per la Taverna registrati con successo.")

def initialize_taverna_websocket_service(sio_param, conn_manager_param, rendering_service_param, game_event_param, websocket_manager_param):
    # Se questa classe viene usata per più luoghi, potrebbe essere istanziata una volta come LuogoWebService
    # e gli handler registrati dinamicamente con functools.partial per ogni nome_luogo.
    global WEBSOCKET_TAVERNA_SERVICE_INSTANCE # Assicura che si riferisca alla variabile globale
    if WEBSOCKET_TAVERNA_SERVICE_INSTANCE is None:
        WEBSOCKET_TAVERNA_SERVICE_INSTANCE = TavernaWebsocketService(sio_param)
    return WEBSOCKET_TAVERNA_SERVICE_INSTANCE

def get_taverna_websocket_service():
    return WEBSOCKET_TAVERNA_SERVICE_INSTANCE

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
        emit('error', {'message': 'Stato taverna non disponibile'})
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