
import logging

logger = logging.getLogger(__name__)
socketio = None
ASSETS_ROOM = 'assets_room'

def notify_asset_update(asset_type, asset_id):
    if socketio is None:
        logger.warning("SocketIO non inizializzato, impossibile inviare notifica asset")
        return False
        
    try:
        socketio.emit('asset_updated', {
            'type': asset_type,
            'id': asset_id
        }, room=ASSETS_ROOM)
        return True
    except Exception as e:
        logger.error(f"Errore nell'inviare notifica asset: {e}")
        return False
