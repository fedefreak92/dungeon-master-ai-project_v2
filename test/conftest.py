"""
Configurazione globale per i test pytest.
Questo file contiene fixture e configurazioni comuni utilizzate in tutti i test.
"""

import pytest
import os
import sys
import threading
import time
from unittest.mock import MagicMock, patch
import json
import requests
import logging
import signal

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Aggiungi la directory principale del progetto al percorso Python
# Questo è fondamentale per permettere l'importazione dei moduli del progetto
# all'interno dei test
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Aggiunto {project_root} al sys.path")

# Helper function per inviare richieste POST con header Content-Type corretto
def post_with_json_header(url, data=None):
    """
    Invia una richiesta POST con l'header Content-Type: application/json.
    
    Args:
        url: URL della richiesta
        data: Dizionario dei dati da inviare (opzionale)
        
    Returns:
        Oggetto Response di requests
    """
    headers = {'Content-Type': 'application/json'}
    return requests.post(url, json=data or {}, headers=headers)

# Fixture per un oggetto IO mock
@pytest.fixture
def mock_io():
    """Crea un oggetto IO mock per i test."""
    io = MagicMock()
    io.mostra_messaggio = MagicMock()
    io.messaggio_sistema = MagicMock()
    io.messaggio_errore = MagicMock()
    io.richiedi_input = MagicMock(return_value="")
    return io

# Fixture per un giocatore mock
@pytest.fixture
def mock_giocatore():
    """Crea un giocatore mock per i test."""
    giocatore = MagicMock()
    giocatore.nome = "TestGiocatore"
    giocatore.vita = 100
    giocatore.vita_max = 100
    giocatore.energia = 50
    giocatore.energia_max = 50
    giocatore.inventario = []
    giocatore.equipaggiamento = {}
    return giocatore

# Fixture per un gestore mappe mock
@pytest.fixture
def mock_gestore_mappe():
    """Crea un gestore mappe mock per i test."""
    # Crea la mappa fittizia
    mock_mappa = MagicMock()
    mock_mappa.pos_iniziale_giocatore = (5, 5)
    mock_mappa.dimensioni = (20, 20)
    mock_mappa.nome = "taverna_test"
    
    # Crea il gestore mappe
    gestore = MagicMock()
    gestore.ottieni_mappa = MagicMock(return_value=mock_mappa)
    gestore.imposta_mappa_attuale = MagicMock()
    gestore.carica_mappa = MagicMock(return_value=mock_mappa)
    
    return gestore

# Fixture per avviare il server Flask durante i test
@pytest.fixture(scope="session")
def flask_server():
    """
    Avvia il server Flask in un thread separato e lo mantiene attivo durante i test.
    Assicura che tutte le API siano disponibili per i test di integrazione.
    """
    logger.info("Inizializzazione del server Flask per i test...")
    
    # Importa dopo l'impostazione del sys.path
    from server.app import app, socketio
    
    # Forza la registrazione dei blueprint API necessari
    from server.routes.entity_api import entity_api
    from server.routes.api_map import api_map
    from server.routes.health_api import health_api
    
    if not any(rule.endpoint.startswith('entity_api.') for rule in app.url_map.iter_rules()):
        app.register_blueprint(entity_api, url_prefix='/api')
    
    if not any(rule.endpoint.startswith('api_map.') for rule in app.url_map.iter_rules()):
        app.register_blueprint(api_map, url_prefix='/api/map')
    
    if not any(rule.endpoint.startswith('health_api.') for rule in app.url_map.iter_rules()):
        app.register_blueprint(health_api, url_prefix='/api')
    
    # Esegui il server in modalità test
    app.config['TESTING'] = True
    
    # Avvia il server in un thread separato
    server_thread = threading.Thread(
        target=socketio.run,
        kwargs={"app": app, "host": "localhost", "port": 5000, "debug": False}
    )
    server_thread.daemon = True
    server_thread.start()
    
    # Attendi che il server si avvii completamente
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://localhost:5000/")
            if response.status_code == 200:
                logger.info(f"Server Flask avviato con successo al tentativo {attempt+1}")
                break
        except requests.exceptions.ConnectionError:
            if attempt < max_attempts - 1:
                logger.info(f"In attesa dell'avvio del server... ({attempt+1}/{max_attempts})")
                time.sleep(1)
            else:
                logger.error("Impossibile avviare il server Flask!")
                pytest.skip("Server non disponibile, i test API vengono saltati")
    
    # Restituisci l'URL base del server
    yield "http://localhost:5000"
    
    # Pulizia (non necessaria con thread daemon)
    logger.info("Chiusura del server Flask...")

# Patch globale per evitare l'accesso ai file durante i test
@pytest.fixture(autouse=True)
def no_file_access(monkeypatch):
    """
    Modifica: Permette il caricamento dei file delle mappe ma preserva il mock per gli altri tipi di file.
    Questo evita problemi con i test che richiedono le mappe reali.
    """
    # Invece di intercettare 'open', salviamo l'originale e facciamo passare solo le chiamate per le mappe
    original_open = open
    
    def selective_mock_open(*args, **kwargs):
        # Controlla se il file è una mappa
        file_path = args[0] if args else kwargs.get('file', '')
        # Converti in stringa se è un Path
        file_path = str(file_path)
        
        # Se il percorso contiene 'data/mappe' o 'mappe' e '.json', usa l'open originale
        if ('data/mappe' in file_path or 'mappe/' in file_path) and file_path.endswith('.json'):
            return original_open(*args, **kwargs)
        
        # Altrimenti usa il mock
        mock_file = MagicMock()
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=None)
        mock_file.read = MagicMock(return_value='{"test": true}')
        return mock_file
    
    # Salva l'originale json.load
    original_json_load = json.load
    
    def selective_json_load(*args, **kwargs):
        # Verifica se stiamo caricando una mappa
        if args and hasattr(args[0], 'name'):
            file_name = args[0].name
            if ('data/mappe' in file_name or 'mappe/' in file_name) and file_name.endswith('.json'):
                return original_json_load(*args, **kwargs)
        
        # Altrimenti usa il mock
        return {"test": True, "posizione_iniziale": [5, 5], "dimensioni": [20, 20], 
                "nome": "taverna_test", "larghezza": 20, "altezza": 20, "tipo": "interno",
                "griglia": [[0 for _ in range(20)] for _ in range(20)]}
    
    monkeypatch.setattr('builtins.open', selective_mock_open)
    monkeypatch.setattr('json.load', selective_json_load) 