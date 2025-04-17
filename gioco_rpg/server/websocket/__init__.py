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

def init_websocket_handlers(socket_io, renderer):
    """
    Inizializza tutti gli handler WebSocket con i riferimenti richiesti
    
    Args:
        socket_io: Istanza di Flask-SocketIO
        renderer: Istanza del renderer grafico
    """
    global socketio, graphics_renderer
    socketio = socket_io
    graphics_renderer = renderer
    
    # Importa e inizializza tutti i moduli di handler
    from .core import register_handlers
    from .connection import register_handlers as register_connection_handlers
    from .game_events import register_handlers as register_game_events_handlers
    from .rendering import register_handlers as register_rendering_handlers
    from .audio import register_handlers as register_audio_handlers
    from .prova_abilita import register_handlers as register_prova_abilita_handlers
    from .combattimento import register_handlers as register_combattimento_handlers
    from .taverna import register_handlers as register_taverna_handlers
    from .mercato import register_handlers as register_mercato_handlers
    from .scelta_mappa import register_handlers as register_scelta_mappa_handlers
    from .dialogo import register_handlers as register_dialogo_handlers
    from .assets import register_handlers as register_assets_handlers
    
    # Registra tutti gli handler
    register_handlers(socketio)
    register_connection_handlers(socketio)
    register_game_events_handlers(socketio)
    register_rendering_handlers(socketio)
    register_audio_handlers(socketio)
    register_prova_abilita_handlers(socketio)
    register_combattimento_handlers(socketio)
    register_taverna_handlers(socketio)
    register_mercato_handlers(socketio)
    register_scelta_mappa_handlers(socketio)
    register_dialogo_handlers(socketio)
    register_assets_handlers(socketio)
    
    logger.info("Tutti gli handler WebSocket sono stati inizializzati") 