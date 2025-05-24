"""
Pacchetto websocket per gestire le comunicazioni WebSocket

Contiene gli handler per gli eventi WebSocket.
"""

from flask_socketio import SocketIO
import logging

# Configura il logger
logger = logging.getLogger(__name__)

# Variabili globali condivise
socketio = None
graphics_renderer = None
websocket_manager = None

def init_websocket_handlers(socket_io, renderer, ws_manager):
    """
    Inizializza tutti gli handler WebSocket con i riferimenti richiesti
    
    Args:
        socket_io: Istanza di Flask-SocketIO
        renderer: Istanza del renderer grafico
        ws_manager: Istanza di WebSocketManager
    """
    global socketio, graphics_renderer, websocket_manager
    socketio = socket_io
    graphics_renderer = renderer
    websocket_manager = ws_manager
    
    # Importa e inizializza tutti i moduli di handler
    try:
        from .core import register_handlers
        register_handlers(socketio)
        logger.info("Handler WebSocket core registrati")
    except ImportError as e:
        logger.error(f"Errore durante l'importazione degli handler core: {e}")
        
    try:
        from .connection import register_handlers as register_connection_handlers
        register_connection_handlers(socketio)
        logger.info("Handler WebSocket connection registrati")
    except ImportError as e:
        logger.error(f"Errore durante l'importazione degli handler connection: {e}")
        
    try:
        from .game_events import register_handlers as register_game_events_handlers
        register_game_events_handlers(socketio)
        logger.info("Handler WebSocket game_events registrati")
    except ImportError as e:
        logger.error(f"Errore durante l'importazione degli handler game_events: {e}")
    
    try:
        from .rendering import register_handlers as register_rendering_handlers
        register_rendering_handlers(socketio)
        logger.info("Handler WebSocket rendering registrati")
    except ImportError as e:
        logger.error(f"Errore durante l'importazione degli handler rendering: {e}")
    
    try:
        from .audio import register_handlers as register_audio_handlers
        register_audio_handlers(socketio)
        logger.info("Handler WebSocket audio registrati")
    except ImportError as e:
        logger.error(f"Errore durante l'importazione degli handler audio: {e}")
    
    try:
        from .prova_abilita import register_handlers as register_prova_abilita_handlers
        register_prova_abilita_handlers(socketio)
        logger.info("Handler WebSocket prova_abilita registrati")
    except ImportError as e:
        logger.error(f"Errore durante l'importazione degli handler prova_abilita: {e}")
    
    try:
        from .combattimento import register_handlers as register_combattimento_handlers
        register_combattimento_handlers(socketio)
        logger.info("Handler WebSocket combattimento registrati")
    except ImportError as e:
        logger.error(f"Errore durante l'importazione degli handler combattimento: {e}")
    
    try:
        from .taverna import register_handlers as register_taverna_handlers
        register_taverna_handlers(socketio)
        logger.info("Handler WebSocket taverna registrati")
    except ImportError as e:
        logger.error(f"Errore durante l'importazione degli handler taverna: {e}")
    
    try:
        from .mercato import register_mercato_event_handlers
        register_mercato_event_handlers(socketio, websocket_manager)
        logger.info("Handler WebSocket mercato registrati")
    except ImportError as e:
        logger.error(f"Errore durante l'importazione degli handler mercato: {e}")
    
    try:
        from .scelta_mappa import register_handlers as register_scelta_mappa_handlers
        register_scelta_mappa_handlers(socketio)
        logger.info("Handler WebSocket scelta_mappa registrati")
    except ImportError as e:
        logger.error(f"Errore durante l'importazione degli handler scelta_mappa: {e}")
    
    try:
        from .dialogo import register_handlers as register_dialogo_handlers
        register_dialogo_handlers(socketio)
        logger.info("Handler WebSocket dialogo registrati")
    except ImportError as e:
        logger.error(f"Errore durante l'importazione degli handler dialogo: {e}")
    
    try:
        from .assets import register_handlers as register_assets_handlers
        register_assets_handlers(socketio)
        logger.info("Handler WebSocket assets registrati")
    except ImportError as e:
        logger.error(f"Errore durante l'importazione degli handler assets: {e}")
    
    # Assicurati che WebSocketEventBridge sia stato inizializzato correttamente
    try:
        from server.websocket.websocket_event_bridge import WebSocketEventBridge
        ws_bridge = WebSocketEventBridge.get_instance()
        if ws_bridge.socketio is None:
            ws_bridge.set_socketio(socketio)
            logger.info("WebSocketEventBridge configurato con socketio")
    except ImportError as e:
        logger.error(f"Errore durante l'inizializzazione di WebSocketEventBridge: {e}")
    
    logger.info("Tutti gli handler WebSocket sono stati inizializzati")

# Esporta la funzione per i test
__all__ = ['init_websocket_handlers'] 