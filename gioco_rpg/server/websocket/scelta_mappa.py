import logging
import json
from flask_socketio import emit, join_room
from core.event_bus import EventBus
import core.events as Events

# Modifica l'importazione per evitare l'importazione circolare
# Usa un'importazione relativa invece di una assoluta
from server.websocket.websocket_event_bridge import WebSocketEventBridge
from server.websocket.connection import send_to_client

# Import moduli locali
from server.utils.session import get_session, salva_sessione
from . import socketio, graphics_renderer
from . import core
from .rendering import render_scelta_mappa

# Configura il logger
logger = logging.getLogger(__name__)

class SceltaMappaHandler:
    """
    Gestore degli eventi di scelta mappa per WebSocket.
    Funziona come bridge tra gli eventi del sistema e i messaggi WebSocket.
    """
    
    def __init__(self):
        """Inizializza il gestore per eventi di scelta mappa"""
        self.event_bus = EventBus.get_instance()
        self.bridge = WebSocketEventBridge.get_instance()
        self._register_handlers()
        
    def _register_handlers(self):
        """Registra gli handler per eventi di scelta mappa"""
        # Registra gli eventi UI
        self.event_bus.on(Events.UI_UPDATE, self._handle_ui_update)
        self.event_bus.on(Events.UI_DIALOG_OPEN, self._handle_dialog_open)
        self.event_bus.on(Events.UI_DIALOG_CLOSE, self._handle_dialog_close)
        
        # Registra gli eventi di mappa
        self.event_bus.on(Events.MAP_CHANGE, self._handle_map_change)
        
        # Registra gli eventi WebSocket specifici
        self.bridge.on("selezione_mappa", self._handle_map_selection)
        self.bridge.on("richiesta_lista_mappe", self._handle_map_list_request)
        
    def _handle_ui_update(self, ui_type=None, state=None, **kwargs):
        """
        Gestisce gli aggiornamenti dell'interfaccia utente.
        
        Args:
            ui_type: Tipo di interfaccia da aggiornare
            state: Stato corrente
            **kwargs: Parametri aggiuntivi
        """
        if ui_type != "scelta_mappa":
            return
            
        # Trova la sessione del client
        session_id = kwargs.get("session_id")
        if not session_id:
            return
            
        # Invia aggiornamento UI al client
        client_data = {
            "type": "refresh_ui",
            "ui_type": ui_type,
            "state": state
        }
        send_to_client(session_id, "scelta_mappa_update", client_data)
        
    def _handle_dialog_open(self, dialog_id=None, title=None, message=None, options=None, **kwargs):
        """
        Gestisce l'apertura di dialoghi.
        
        Args:
            dialog_id: ID del dialogo
            title: Titolo del dialogo
            message: Messaggio del dialogo
            options: Opzioni disponibili
            **kwargs: Parametri aggiuntivi
        """
        # Verifica che il dialogo sia relativo alla scelta mappa
        if not dialog_id or not dialog_id.startswith("seleziona_mappa") and not dialog_id.startswith("errore_"):
            return
            
        # Trova la sessione del client
        session_id = kwargs.get("session_id")
        if not session_id:
            return
            
        # Invia dialogo al client
        client_data = {
            "type": "dialog",
            "dialog_id": dialog_id,
            "title": title,
            "message": message,
            "options": options
        }
        send_to_client(session_id, "dialog_open", client_data)
        
    def _handle_dialog_close(self, dialog_id=None, **kwargs):
        """
        Gestisce la chiusura di dialoghi.
        
        Args:
            dialog_id: ID del dialogo
            **kwargs: Parametri aggiuntivi
        """
        if not dialog_id or not dialog_id.startswith("seleziona_mappa") and not dialog_id.startswith("errore_"):
            return
            
        # Trova la sessione del client
        session_id = kwargs.get("session_id")
        if not session_id:
            return
            
        # Invia chiusura dialogo al client
        client_data = {
            "type": "dialog_close",
            "dialog_id": dialog_id
        }
        send_to_client(session_id, "dialog_close", client_data)
        
    def _handle_map_change(self, map_id=None, position_x=None, position_y=None, **kwargs):
        """
        Gestisce il cambio di mappa.
        
        Args:
            map_id: ID della mappa di destinazione
            position_x: Posizione X iniziale
            position_y: Posizione Y iniziale
            **kwargs: Parametri aggiuntivi
        """
        if not map_id:
            return
            
        # Trova la sessione del client
        session_id = kwargs.get("session_id")
        if not session_id:
            return
            
        # Invia evento di cambio mappa al client
        client_data = {
            "type": "map_change",
            "map_id": map_id,
            "position": {
                "x": position_x,
                "y": position_y
            }
        }
        send_to_client(session_id, "map_change", client_data)
        
    def _handle_map_selection(self, client_id, data):
        """
        Gestisce la selezione di una mappa da parte del client.
        
        Args:
            client_id: ID del client
            data: Dati della richiesta
        """
        if not data or "choice" not in data:
            return
            
        # Recupera la scelta e l'ID del menu
        choice = data.get("choice")
        menu_id = data.get("menu_id", "seleziona_mappa")
        
        # Emetti evento di selezione menu
        self.event_bus.emit(Events.MENU_SELECTION, 
                           choice=choice, 
                           menu_id=menu_id, 
                           session_id=client_id)
        
    def _handle_map_list_request(self, client_id, data):
        """
        Gestisce la richiesta di lista mappe da parte del client.
        
        Args:
            client_id: ID del client
            data: Dati della richiesta
        """
        from core.game_singleton import GameSingleton
        
        # Ottieni istanza di gioco associata al client
        game = GameSingleton.get_instance()
        session = game.session_manager.get_session(client_id)
        if not session or not session.gioco:
            return
            
        gioco = session.gioco
        
        # Ottieni lista mappe
        lista_mappe = gioco.gestore_mappe.ottieni_lista_mappe()
        if not lista_mappe:
            return
            
        # Converte la lista mappe in un formato adatto al client
        mappe_client = {}
        for id_mappa, info_mappa in lista_mappe.items():
            mappe_client[id_mappa] = {
                "nome": info_mappa.get("nome", id_mappa),
                "livello_min": info_mappa.get("livello_min", 0),
                "descrizione": info_mappa.get("descrizione", ""),
                "attiva": info_mappa.get("attiva", True)
            }
            
        # Invia lista mappe al client
        client_data = {
            "type": "lista_mappe",
            "mappe": mappe_client,
            "mappa_corrente": gioco.giocatore.mappa_corrente if hasattr(gioco, "giocatore") else None
        }
        send_to_client(client_id, "lista_mappe", client_data)

# Crea un'istanza del gestore per il singleton di EventBus
scelta_mappa_handler = SceltaMappaHandler()

def init_scelta_mappa_handlers():
    """Inizializza gli handler per eventi di scelta mappa"""
    global scelta_mappa_handler
    if not scelta_mappa_handler:
        scelta_mappa_handler = SceltaMappaHandler()
    return scelta_mappa_handler

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
    
    # Ottieni la lista delle mappe disponibili direttamente dal gestore mappe
    try:
        # Ottieni le mappe direttamente dal gestore della sessione
        mappe = sessione.gestore_mappe.ottieni_lista_mappe()
        
        # Preparazione dati iniziali
        dati_scelta_mappa = {
            "stato": scelta_mappa_state.to_dict(),
            "mappe": mappe,
            "mappa_corrente": sessione.giocatore.mappa_corrente
        }
        
        # Invia i dati iniziali al client
        emit('scelta_mappa_inizializzata', dati_scelta_mappa)
        
        # Esegui il rendering della scelta mappa
        render_scelta_mappa(scelta_mappa_state, sessione)
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
        # Ottieni la sessione
        sessione = core.get_session(id_sessione)
        if not sessione:
            emit('error', {'message': 'Sessione non trovata'})
            return
            
        # Ottieni la mappa e verifica i requisiti
        lista_mappe = sessione.gestore_mappe.ottieni_lista_mappe()
        if id_mappa not in lista_mappe:
            emit('error', {'message': 'Mappa non disponibile'})
            return
        
        # Verifica il livello minimo richiesto
        info_mappa = lista_mappe[id_mappa]
        livello_min = info_mappa.get("livello_min", 0)
        if sessione.giocatore.livello < livello_min:
            error_msg = f"Livello insufficiente! Devi essere almeno di livello {livello_min}."
            emit('error', {'message': error_msg})
            emit('livello_insufficiente', {
                'id_mappa': id_mappa,
                'error': error_msg
            })
            
            # Ottieni lo stato per il re-rendering
            scelta_mappa_state = sessione.get_state("scelta_mappa")
            if scelta_mappa_state:
                # Aggiorna il renderer con il messaggio di errore
                render_scelta_mappa(scelta_mappa_state, sessione)
            return
        
        # Ottieni la mappa e le coordinate iniziali
        mappa = sessione.gestore_mappe.ottieni_mappa(id_mappa)
        if not mappa:
            emit('error', {'message': 'Impossibile caricare la mappa'})
            return
        
        x, y = mappa.pos_iniziale_giocatore
        
        # Cambia la mappa corrente
        success = sessione.cambia_mappa(id_mappa, x, y)
        
        if success:
            # Salva la sessione aggiornata
            salva_sessione(id_sessione, sessione)
            
            # Prepara i dati della risposta
            result_data = {
                'success': True,
                'mapId': id_mappa,
                'position': {'x': x, 'y': y}
            }
            
            # Emetti evento per tutti i client nella stessa sessione
            socketio.emit('map_change_complete', result_data, room=room_id)
            logger.info(f"Notifica cambio mappa inviata a tutti i client nella sessione {id_sessione}")
            
            # Emetti l'evento originale per compatibilità
            emit('scelta_mappa_cambiata', {
                'success': True,
                'mappa': id_mappa,
                'posizione': {'x': x, 'y': y}
            })
            
            # Notifica anche il cambio di stato del gioco
            socketio.emit('cambio_stato', {
                'stato': 'mappa',
                'parametri': {
                    'mappa': id_mappa,
                    'posizione': {'x': x, 'y': y}
                }
            }, room=room_id)
            
            # Notifica il cambiamento della mappa per permettere una connessione WebSocket più stabile
            socketio.emit('game_state_update', {
                'currentMap': id_mappa,
                'player_position': {'x': x, 'y': y}
            }, room=room_id)
        else:
            emit('error', {'message': 'Impossibile viaggiare verso questa destinazione.'})
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
            # Verifica requisiti di livello
            info_mappa = lista_mappe[id_mappa_selezionata]
            livello_min = info_mappa.get("livello_min", 0)
            
            if sessione.giocatore.livello < livello_min:
                error_msg = f"Livello insufficiente! Devi essere almeno di livello {livello_min}."
                emit('error', {'message': error_msg})
                
                # Rirender dopo l'errore
                render_scelta_mappa(scelta_mappa_state, sessione)
                return
            
            # Ottieni la mappa e le coordinate iniziali
            mappa = sessione.gestore_mappe.ottieni_mappa(id_mappa_selezionata)
            if not mappa:
                emit('error', {'message': 'Impossibile caricare la mappa'})
                return
            
            x, y = mappa.pos_iniziale_giocatore
            
            # Cambia la mappa corrente
            success = sessione.cambia_mappa(id_mappa_selezionata, x, y)
            
            if success:
                # Salva la sessione aggiornata
                salva_sessione(id_sessione, sessione)
                
                # Prepara i dati del risultato
                result_data = {
                    'success': True,
                    'mappa': id_mappa_selezionata,
                    'posizione': {'x': x, 'y': y}
                }
                
                # Emetti evento per aggiornare l'interfaccia
                emit('scelta_mappa_cambiata', result_data)
                
                # Emetti anche un evento per tutti i client nella stessa sessione
                socketio.emit('scelta_mappa_cambiata', result_data, room=room_id)
                
                # Notifica la transizione di stato
                socketio.emit('cambio_stato', {
                    'stato': 'mappa',
                    'parametri': {}
                }, room=room_id)
            else:
                emit('error', {'message': 'Impossibile viaggiare verso questa destinazione'})
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