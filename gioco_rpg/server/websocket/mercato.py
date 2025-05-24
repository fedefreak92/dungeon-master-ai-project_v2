import logging
import json
import requests
from flask_socketio import emit, join_room
import asyncio
from flask_socketio import SocketIO, leave_room
from engineio.payload import Payload
# from বিশ্ব.게임_상태_저장_서비스 import GameStateService # Commentato
from entities.giocatore import Giocatore
from util.logging_config import get_logger
# from server.websocket.connection import ConnectionManager, authenticated_async # RIMOSSO
# from server.websocket.game_events import GameEventService # RIMOSSO
# from server.websocket.rendering import RenderingService # RIMOSSO
from server.websocket.websocket_manager import WebSocketManager
from states.mappa.mappa_state import MappaState
import functools

# Import moduli locali
# from server.utils.session import get_session, salva_sessione # Probabilmente non necessari qui
# from . import socketio, graphics_renderer # Probabilmente non necessari qui se si usa WebSocketManager
# from . import core # Probabilmente non necessario qui

Payload.max_decode_packets = 500

WEBSOCKET_MERCATO_SERVICE_INSTANCE = None

logger = get_logger(__name__)

# Funzione helper (riutilizzata o adattata da taverna.py)
def _get_valid_mappa_state_or_emit_error(sid, nome_luogo_atteso):
    websocket_manager = WebSocketManager.get_instance()
    if not websocket_manager or not hasattr(websocket_manager, 'connection_manager'): 
        emit('errore_stato', {'errore': 'WebSocketManager non inizializzato correttamente.'}, room=sid)
        logger.error("WebSocketManager o connection_manager non disponibile in _get_valid_mappa_state.")
        return None, None 
        
    user_id = websocket_manager.connection_manager.get_user_id(sid)
    if not user_id:
        emit('errore_stato', {'errore': 'Utente non autenticato o sessione non valida.'}, room=sid)
        logger.warning(f"Auth fallita per SID {sid} in _get_valid_mappa_state_or_emit_error.")
        return None, None

    # Ottieni session_id e poi giocatore da WebSocketManager
    session_id = websocket_manager.connection_manager.get_session_id(sid) # Metodo ipotetico
    if not session_id:
         emit('errore_stato', {'errore': 'ID Sessione non trovato per il SID.'}, room=sid)
         logger.warning(f"Session ID non trovato per SID {sid}.")
         return None, user_id

    giocatore = websocket_manager.get_player_instance(session_id) # Metodo ipotetico
    if not giocatore:
         emit('errore_stato', {'errore': f'Istanza giocatore non trovata per sessione {session_id}.'}, room=sid)
         logger.warning(f"Istanza giocatore non trovata per session_id {session_id} (SID: {sid}).")
         return None, user_id
         
    stato_corrente = giocatore.stato_corrente

    # Validazione stato
    if not stato_corrente:
        emit('errore_stato', {'errore': f'Stato corrente non trovato per l\'utente {user_id}.'}, room=sid)
        logger.warning(f"Stato corrente non trovato per user_id {user_id} (SID: {sid}, session_id: {session_id}).")
        return None, user_id

    if not isinstance(stato_corrente, MappaState):
        emit('errore_stato', {'errore': 'Tipo di stato non valido. Non sei in un luogo (MappaState).'}, room=sid)
        logger.warning(f"Stato non MappaState per user_id {user_id} (SID: {sid}). Stato: {type(stato_corrente).__name__}")
        return None, user_id
    
    if stato_corrente.nome_luogo != nome_luogo_atteso:
        emit('errore_stato', {'errore': f'Non sei nel luogo corretto. Attualmente in "{stato_corrente.nome_luogo}", atteso "{nome_luogo_atteso}".'}, room=sid)
        logger.warning(f"Luogo errato per user_id {user_id} (SID: {sid}). Attuale: {stato_corrente.nome_luogo}, Atteso: {nome_luogo_atteso}")
        return None, user_id
        
    logger.debug(f"Stato valido {stato_corrente.nome_luogo} recuperato per user_id {user_id} (SID: {sid}).")
    return stato_corrente, user_id

class MercatoWebsocketService:
    def __init__(self, sio_param, websocket_manager_param, rendering_service_param, game_event_service_param):
        self.sio = sio_param
        self.websocket_manager = websocket_manager_param
        self.rendering_service = rendering_service_param
        self.game_event_service = game_event_service_param
        self.register_mercato_events()

        global WEBSOCKET_MERCATO_SERVICE_INSTANCE
        WEBSOCKET_MERCATO_SERVICE_INSTANCE = self

    def register_mercato_events(self):
        event_handlers = {
            "richiedi_stato_mercato": self.handle_richiedi_stato_luogo,
            "azione_mercato": self.handle_azione_in_luogo,
            "compra_oggetto_mercato": self.handle_compra_oggetto_in_luogo,
            "vendi_oggetto_mercato": self.handle_vendi_oggetto_in_luogo,
            "parla_npg_mercato": self.handle_parla_npg_in_luogo,
        }
        for event, handler_method in event_handlers.items():
            specific_handler = functools.partial(handler_method, nome_luogo_specifico="mercato")
            self.sio.on(event, specific_handler) # Rimosso decorator

    async def _get_valid_mappa_state_or_emit_error(self, sid, nome_luogo_atteso: str):
        # Usa la funzione helper globale
        stato, user_id = _get_valid_mappa_state_or_emit_error(sid, nome_luogo_atteso)
        # Se la classe necessita di user_id, salvarlo o passarlo
        # Esempio: self.current_user_id = user_id 
        return stato # Restituisce solo lo stato per coerenza con la vecchia firma (se non serve user_id altrove nella classe)

    # Adattare gli handler per usare la funzione helper
    async def handle_richiedi_stato_luogo(self, sid, data=None, nome_luogo_specifico="mercato"):
        logger.debug(f"Luogo ({nome_luogo_specifico}): Ricevuta richiesta stato da SID: {sid}, data: {data}")
        stato_luogo, user_id = _get_valid_mappa_state_or_emit_error(sid, nome_luogo_specifico)
        if not stato_luogo: return
        try:
            dati_stato_luogo = stato_luogo.to_dict_per_client() if hasattr(stato_luogo, 'to_dict_per_client') else stato_luogo.to_dict()
            await self.sio.emit(f'stato_{nome_luogo_specifico}', dati_stato_luogo, room=sid)
        except Exception as e:
            logger.error(f"Errore invio stato mercato: {e}")
            await self.sio.emit('errore_generico', {'messaggio': 'Errore recupero stato mercato.'}, room=sid)

    async def handle_azione_in_luogo(self, sid, data, nome_luogo_specifico="mercato"):
        logger.debug(f"Luogo ({nome_luogo_specifico}): Ricevuta azione da SID: {sid}, data: {data}")
        stato_luogo, user_id = _get_valid_mappa_state_or_emit_error(sid, nome_luogo_specifico)
        if not stato_luogo or not user_id: return
        azione = data.get('azione')
        parametri = data.get('parametri', {})
        if not azione:
            await self.sio.emit('errore_azione', {'messaggio': 'Azione mancante'}, room=sid)
            return
        try:
            risultato_azione = await stato_luogo.process_azione_luogo(user_id, azione, parametri)
            # Emettere risultato o affidarsi a eventi da RenderingService
        except Exception as e:
             await self.sio.emit('errore_azione', {'messaggio': f'Errore esecuzione azione: {str(e)}'}, room=sid)

    async def handle_compra_oggetto_in_luogo(self, sid, data, nome_luogo_specifico="mercato"):
        logger.debug(f"Luogo ({nome_luogo_specifico}): Ricevuta richiesta compra: {data}")
        stato_luogo, user_id = _get_valid_mappa_state_or_emit_error(sid, nome_luogo_specifico)
        if not stato_luogo or not user_id: return

        try:
            item_id = data.get('item_id') # Assumendo che il client invii 'item_id'
            quantita = data.get('quantita', 1)
            if not item_id:
                 await self.sio.emit('errore_azione', {'messaggio': 'ID oggetto mancante per comprare'}, room=sid)
                 return
            # Chiama il metodo generico dello stato
            await stato_luogo.process_azione_luogo(user_id, "compra", {"item_id": item_id, "quantita": quantita})
        except Exception as e:
             await self.sio.emit('errore_azione', {'messaggio': f'Errore durante acquisto: {str(e)}'}, room=sid)

    async def handle_vendi_oggetto_in_luogo(self, sid, data, nome_luogo_specifico="mercato"):
        logger.debug(f"Luogo ({nome_luogo_specifico}): Ricevuta richiesta vendi: {data}")
        stato_luogo, user_id = _get_valid_mappa_state_or_emit_error(sid, nome_luogo_specifico)
        if not stato_luogo or not user_id: return
        try:
            item_id = data.get('item_id') # Assumendo che il client invii 'item_id'
            quantita = data.get('quantita', 1)
            if not item_id:
                 await self.sio.emit('errore_azione', {'messaggio': 'ID oggetto mancante per vendere'}, room=sid)
                 return
            # Chiama il metodo generico dello stato
            await stato_luogo.process_azione_luogo(user_id, "vendi", {"item_id": item_id, "quantita": quantita})
        except Exception as e:
             await self.sio.emit('errore_azione', {'messaggio': f'Errore durante vendita: {str(e)}'}, room=sid)

    async def handle_parla_npg_in_luogo(self, sid, data, nome_luogo_specifico="mercato"):
        logger.debug(f"Luogo ({nome_luogo_specifico}): Ricevuta richiesta parla NPG: {data}")
        stato_luogo, user_id = _get_valid_mappa_state_or_emit_error(sid, nome_luogo_specifico)
        if not stato_luogo or not user_id: return
        try:
            npg_id = data.get('npg_id')
            opzione = data.get('opzione') # Opzionale
            if not npg_id:
                await self.sio.emit('errore_azione', {'messaggio': 'ID NPG mancante per dialogo'}, room=sid)
                return
            # Chiama il metodo generico dello stato
            await stato_luogo.process_azione_luogo(user_id, "dialoga_npg", {"npg_id": npg_id, "opzione": opzione})
        except Exception as e:
            await self.sio.emit('errore_azione', {'messaggio': f'Errore durante dialogo NPG: {str(e)}'}, room=sid)

def register_mercato_event_handlers(sio_instance, websocket_manager_instance):
    """Registra gli handler inizializzando il servizio basato su classe."""
    try:
        # RIMOSSO: websocket_manager = WebSocketManager.get_instance()
        # Ottieni altre dipendenze se necessario (RenderingService, GameEventService)
        # rendering_service = RenderingService.get_instance() # Esempio se servisse
        # game_event_service = GameEventService.get_instance() # Esempio se servisse
        
        # USA websocket_manager_instance passato come argomento
        if not websocket_manager_instance:
             logger.error("WebSocketManager non disponibile durante la registrazione degli handler del mercato.")
             return
             
        # Passa le dipendenze necessarie al costruttore di MercatoWebsocketService
        # Adatta questa chiamata in base alle reali dipendenze del costruttore
        # Assumiamo che MercatoWebsocketService necessiti solo di sio_instance e websocket_manager_instance
        # e che rendering_service e game_event_service non siano più direttamente usati da MercatoWebsocketService
        # o siano accessibili tramite websocket_manager_instance se necessario.
        initialize_mercato_websocket_service(sio_instance, websocket_manager_instance, None, None) 
        logger.info("Servizio WebSocket Mercato (basato su classe) inizializzato e handler registrati.")
    except Exception as e:
        logger.error(f"Errore durante l'inizializzazione del servizio WebSocket Mercato: {e}", exc_info=True)

def initialize_mercato_websocket_service(sio_param, websocket_manager_param, rendering_service_param, game_event_service_param):
    global WEBSOCKET_MERCATO_SERVICE_INSTANCE
    if WEBSOCKET_MERCATO_SERVICE_INSTANCE is None:
        # Passa le dipendenze ricevute al costruttore
        WEBSOCKET_MERCATO_SERVICE_INSTANCE = MercatoWebsocketService(sio_param, websocket_manager_param, rendering_service_param, game_event_service_param)
    return WEBSOCKET_MERCATO_SERVICE_INSTANCE

def get_mercato_websocket_service():
    return WEBSOCKET_MERCATO_SERVICE_INSTANCE