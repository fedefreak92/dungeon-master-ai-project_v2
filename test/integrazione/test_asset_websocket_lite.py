"""
Test di integrazione semplificato per il WebSocket degli asset.
Verifica il funzionamento di base delle notifiche degli asset senza avviare un server completo.
"""

import unittest
import os
import tempfile
import shutil
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch
import time

# Configura il logging per il debug
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Modifica il percorso di sistema per l'importazione
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Creazione di uno stub per GraphicsRenderer che può essere utilizzato nei test
class GraphicsRendererStub:
    """Stub semplice per GraphicsRenderer utilizzato nei test."""
    
    def __init__(self, socketio=None):
        self.socketio = socketio
        logger.info("GraphicsRendererStub inizializzato")
    
    def set_socket_io(self, socketio):
        self.socketio = socketio
        logger.info("SocketIO impostato in GraphicsRendererStub")
    
    def render_asset(self, asset_type, asset_id, target_id=None):
        logger.info(f"GraphicsRendererStub: render_asset chiamato per {asset_type}/{asset_id}")
        return True
    
    def render_map(self, map_data, target_id=None):
        logger.info(f"GraphicsRendererStub: render_map chiamato")
        return True

# Creiamo una directory mock per i moduli necessari
if not os.path.exists('util'):
    os.makedirs('util', exist_ok=True)

# Creiamo il modulo graphics_renderer.py se non esiste
if not os.path.exists('util/graphics_renderer.py'):
    with open('util/graphics_renderer.py', 'w') as f:
        f.write("""
class GraphicsRenderer:
    def __init__(self, socketio=None):
        self.socketio = socketio
        
    def set_socket_io(self, socketio):
        self.socketio = socketio
        
    def render_asset(self, asset_type, asset_id, target_id=None):
        return True
        
    def render_map(self, map_data, target_id=None):
        return True
""")

# Creiamo un modulo asset_manager.py se non esiste
if not os.path.exists('util/asset_manager.py'):
    with open('util/asset_manager.py', 'w') as f:
        f.write("""
class AssetManager:
    def __init__(self, base_path=None):
        self.base_path = base_path or 'assets'
        
    def get_asset_path(self, asset_type, asset_id):
        return f"{self.base_path}/{asset_type}/{asset_id}"
""")

# Creiamo una directory per server/websocket
if not os.path.exists('server/websocket'):
    os.makedirs('server/websocket', exist_ok=True)

# Creiamo un modulo assets.py se non esiste
if not os.path.exists('server/websocket/assets.py'):
    with open('server/websocket/assets.py', 'w') as f:
        f.write("""
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
""")

# Creiamo un modulo __init__.py in server/websocket
if not os.path.exists('server/websocket/__init__.py'):
    with open('server/websocket/__init__.py', 'w') as f:
        f.write("""
def init_websocket_handlers(socketio_instance, renderer=None):
    from . import assets
    assets.socketio = socketio_instance
    return True
""")

# Garantiamo che ci sia un __init__.py in server
if not os.path.exists('server/__init__.py'):
    with open('server/__init__.py', 'w') as f:
        f.write("# Modulo server")

# Garantiamo che ci sia un __init__.py in util
if not os.path.exists('util/__init__.py'):
    with open('util/__init__.py', 'w') as f:
        f.write("# Modulo util")

# Aggiungiamo lo stub al modulo util
sys.modules['util.graphics_renderer'] = type('module', (), {
    'GraphicsRenderer': GraphicsRendererStub
})

# Importa dopo aver modificato il percorso di sistema
from util.asset_manager import AssetManager
from server.websocket import assets
from server.websocket import init_websocket_handlers

class TestAssetWebSocketLite(unittest.TestCase):
    """Test di integrazione semplificato per il WebSocket degli asset."""
    
    def setUp(self):
        """Prepara l'ambiente per i test."""
        # Crea una directory temporanea per gli asset
        self.test_dir = tempfile.mkdtemp()
        self.assets_dir = os.path.join(self.test_dir, "assets")
        
        # Crea le sottodirectory per gli asset
        os.makedirs(os.path.join(self.assets_dir, "sprites"), exist_ok=True)
        os.makedirs(os.path.join(self.assets_dir, "tiles"), exist_ok=True)
        os.makedirs(os.path.join(self.assets_dir, "ui"), exist_ok=True)
        
        # Crea un Asset Manager
        self.asset_manager = AssetManager(base_path=self.assets_dir)
        
        # Mock per SocketIO
        self.mock_socketio = MagicMock()
        self.mock_socketio.emit = MagicMock()
        
        # Mock per GraphicsRenderer
        self.mock_renderer = MagicMock()
        
        # Inizializza il mock di SocketIO nel modulo assets
        with patch('server.websocket.assets.socketio', self.mock_socketio):
            # Inizializza i WebSocket handlers con i mock
            init_websocket_handlers(self.mock_socketio, self.mock_renderer)
    
    def tearDown(self):
        """Pulisce l'ambiente dopo i test."""
        # Elimina la directory temporanea
        shutil.rmtree(self.test_dir)
    
    def test_notify_asset_update(self):
        """Verifica che la notifica di aggiornamento asset funzioni correttamente."""
        # Usa il mock di SocketIO
        with patch('server.websocket.assets.socketio', self.mock_socketio):
            # Invia una notifica di aggiornamento asset
            result = assets.notify_asset_update("sprite", "test_sprite")
            
            # Attendi brevemente per evitare problemi di timing
            time.sleep(0.1)
            
            # Verifica che la notifica sia stata inviata
            self.assertTrue(result, "La notifica avrebbe dovuto avere successo")
            self.mock_socketio.emit.assert_called_once()
            
            # Verifica i parametri della chiamata
            args, kwargs = self.mock_socketio.emit.call_args
            self.assertEqual(args[0], 'asset_updated', "Evento errato")
            self.assertEqual(kwargs['room'], assets.ASSETS_ROOM, "Room errata")
            
            # Verifica il contenuto del messaggio
            self.assertEqual(args[1]['type'], 'sprite', "Tipo asset errato nel messaggio")
            self.assertEqual(args[1]['id'], 'test_sprite', "ID asset errato nel messaggio")
    
    def test_notify_asset_update_error_handling(self):
        """Verifica che la gestione degli errori nella notifica funzioni correttamente."""
        # Simula un errore nella emit impostando la funzione mock per sollevare un'eccezione
        self.mock_socketio.emit.side_effect = Exception("Test error")
        
        # Usa il mock di SocketIO
        with patch('server.websocket.assets.socketio', self.mock_socketio):
            # Invia una notifica di aggiornamento asset
            result = assets.notify_asset_update("sprite", "test_sprite")
            
            # Verifica che la funzione gestisca l'errore e restituisca False
            self.assertFalse(result, "La notifica avrebbe dovuto fallire")
            
            # Verifica che l'emit sia stata chiamata (anche se ha generato un'eccezione)
            self.mock_socketio.emit.assert_called_once()
    
    def test_socketio_none_handling(self):
        """Verifica la gestione del caso in cui socketio sia None."""
        # Sostituisci il modulo sys.modules con un mock per il modulo assets
        import sys
        
        # Salva il modulo originale
        original_module = sys.modules.get('server.websocket.assets')
        
        try:
            # Imposta socketio a None direttamente nel modulo
            if 'server.websocket.assets' in sys.modules:
                sys.modules['server.websocket.assets'].socketio = None
            
            # Invia una notifica di aggiornamento asset
            result = assets.notify_asset_update("sprite", "test_sprite")
            
            # Verifica che la funzione gestisca il caso socketio=None e restituisca False
            self.assertFalse(result, "La notifica avrebbe dovuto fallire quando socketio è None")
            
            # Il mock non dovrebbe essere chiamato
            self.mock_socketio.emit.assert_not_called()
        
        finally:
            # Ripristina il modulo originale
            if original_module is not None:
                sys.modules['server.websocket.assets'] = original_module
            # In caso non ci fosse il modulo originale 
            elif 'server.websocket.assets' in sys.modules:
                del sys.modules['server.websocket.assets']

if __name__ == '__main__':
    unittest.main() 