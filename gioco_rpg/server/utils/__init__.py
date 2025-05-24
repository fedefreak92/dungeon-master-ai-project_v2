"""
Pacchetto utils per funzioni di utilità del server

Contiene moduli per la gestione delle sessioni e altre utilità.
"""

import logging

# Importa classi e funzioni specifiche per renderle disponibili a livello di package
# from .json_middleware import AdvancedJSONEncoder # Rimosso perché non trovato o problematico
# from .route_config import configure_routes # Temporaneamente commentato per testare dipendenze
# from .event_bus_setup import setup_event_bus # Temporaneamente commentato perché non trovato
from .session import salva_sessione, carica_sessione, aggiungi_notifica, get_session, sessioni_attive, socket_sessioni, set_socketio, get_session_path, SessionManager, SessionWrapper, risolvi_problemi_sessione

# Configura il logger per il package
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler()) # Evita "No handlers could be found" se non configurato

__all__ = [
    # 'AdvancedJSONEncoder', # Rimosso
    # 'configure_routes', # Temporaneamente commentato
    # 'setup_event_bus', # Temporaneamente commentato
    'salva_sessione',
    'carica_sessione',
    'aggiungi_notifica',
    'get_session',
    'sessioni_attive',
    'socket_sessioni',
    'set_socketio',
    'get_session_path',
    'SessionManager',
    'SessionWrapper',
    'risolvi_problemi_sessione'
] 