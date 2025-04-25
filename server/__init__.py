"""
Pacchetto server per il gioco RPG.

Implementa tutte le funzionalità legate al server Flask e alla comunicazione WebSocket.
"""

# Importazioni ritardate per evitare cicli
def get_app():
    """Restituisce l'istanza dell'app Flask"""
    from server.app import app
    return app

def get_socketio():
    """Restituisce l'istanza di SocketIO"""
    from server.app import socketio
    return socketio

def get_run_server():
    """Restituisce la funzione run_server"""
    from server.app import run_server
    return run_server

# Per retrocompatibilità, inizializziamo queste variabili con le proprietà
import sys
class LazyObject:
    def __init__(self, get_func):
        self._get_func = get_func
        self._obj = None
        
    def __getattr__(self, name):
        if self._obj is None:
            self._obj = self._get_func()
        return getattr(self._obj, name)
    
    def __call__(self, *args, **kwargs):
        if self._obj is None:
            self._obj = self._get_func()
        if callable(self._obj):
            return self._obj(*args, **kwargs)
        else:
            raise TypeError(f"L'oggetto {self._obj} non è callable")

# Esponi le variabili come lazy objects
app = LazyObject(get_app)
socketio = LazyObject(get_socketio)
run_server = LazyObject(get_run_server)

__all__ = ['app', 'socketio', 'run_server', 'get_app', 'get_socketio', 'get_run_server'] 