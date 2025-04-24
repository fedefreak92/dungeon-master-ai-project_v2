"""
Test di debug per problemi di connessione WebSocket.

Questo modulo contiene test specifici per diagnosticare problemi di connessione
WebSocket e comunicazione tra frontend e backend.
"""
import unittest
import os
import sys
import json
import time
import requests
import socketio
from unittest.mock import MagicMock, patch

# Aggiunta del percorso relativo per importare moduli
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

class TestSocketDebug(unittest.TestCase):
    """Test di debug per connessioni WebSocket."""
    
    def setUp(self):
        """Configura l'ambiente di test prima di ogni test."""
        self.server_url = "http://localhost:5000"
        self.sio = socketio.Client()
        self.connected = False
        self.events_received = {}
        self.connection_error = None
        
        # Configura handlers per eventi basilari
        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)
        self.sio.on('connect_error', self.on_connect_error)
        
    def tearDown(self):
        """Pulisce l'ambiente dopo ogni test."""
        if self.connected:
            try:
                self.sio.disconnect()
                print("Socket disconnesso correttamente")
            except Exception as e:
                print(f"Errore durante la disconnessione: {e}")
    
    def on_connect(self):
        """Handler per l'evento di connessione."""
        self.connected = True
        print("Connessione WebSocket stabilita")
    
    def on_disconnect(self):
        """Handler per l'evento di disconnessione."""
        self.connected = False
        print("WebSocket disconnesso")
    
    def on_connect_error(self, data):
        """Handler per errori di connessione."""
        self.connection_error = data
        print(f"Errore di connessione WebSocket: {data}")
    
    def generic_event_handler(self, event_name):
        """Crea un handler generico per un evento."""
        def handler(data):
            print(f"Evento {event_name} ricevuto con dati: {data}")
            if event_name not in self.events_received:
                self.events_received[event_name] = []
            self.events_received[event_name].append(data)
        return handler
    
    def test_server_availability(self):
        """Verifica che il server sia disponibile e risponda correttamente."""
        try:
            response = requests.get(f"{self.server_url}/api/health")
            print(f"Risposta server health check: {response.status_code} - {response.text}")
            self.assertEqual(response.status_code, 200)
        except Exception as e:
            self.fail(f"Server non disponibile: {str(e)}")
    
    def test_socket_connection(self):
        """Verifica la connessione base WebSocket."""
        try:
            self.sio.connect(self.server_url, transports=['websocket'])
            timeout = 5
            start_time = time.time()
            
            # Aspetta fino a quando siamo connessi o scade il timeout
            while not self.connected and time.time() - start_time < timeout:
                time.sleep(0.1)
            
            # Verifica la connessione
            self.assertTrue(self.connected, "La connessione WebSocket non è stata stabilita")
            self.assertIsNone(self.connection_error, f"Errore di connessione: {self.connection_error}")
            
            # Verifica l'ID del socket
            print(f"Socket connesso con ID: {self.sio.sid}")
            self.assertIsNotNone(self.sio.sid)
        except Exception as e:
            self.fail(f"Errore durante il test di connessione socket: {str(e)}")
    
    def test_join_game_message(self):
        """Verifica l'invio del messaggio join_game e la risposta del server."""
        if not self._ensure_connection():
            self.fail("Impossibile stabilire la connessione WebSocket")
        
        # Registra handler per l'evento di risposta
        self.sio.on('join_confirmation', self.generic_event_handler('join_confirmation'))
        self.sio.on('error', self.generic_event_handler('error'))
        
        # Invia il messaggio di join
        test_session_id = "test-session-" + str(int(time.time()))
        join_data = {"id_sessione": test_session_id}
        print(f"Invio messaggio join_game con dati: {join_data}")
        self.sio.emit('join_game', join_data)
        
        # Aspetta la risposta
        timeout = 5
        start_time = time.time()
        while 'join_confirmation' not in self.events_received and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        # Verifica che abbiamo ricevuto una risposta
        self.assertIn('join_confirmation', self.events_received, 
                     "Nessuna conferma di join ricevuta dal server")
        
        # Verifica eventuali errori
        if 'error' in self.events_received:
            print(f"Errori ricevuti: {self.events_received['error']}")
    
    def test_request_map_data(self):
        """Verifica la richiesta dei dati della mappa."""
        if not self._ensure_connection():
            self.fail("Impossibile stabilire la connessione WebSocket")
        
        # Registra handler per l'evento map_data
        self.sio.on('map_data', self.generic_event_handler('map_data'))
        
        # Richiedi dati mappa
        test_session_id = "test-session-" + str(int(time.time()))
        request_data = {"id_sessione": test_session_id}
        print(f"Richiesta dati mappa con dati: {request_data}")
        self.sio.emit('request_map_data', request_data)
        
        # Aspetta la risposta
        timeout = 5
        start_time = time.time()
        while 'map_data' not in self.events_received and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        # Verifica che abbiamo ricevuto una risposta
        response_received = 'map_data' in self.events_received
        print(f"Risposta dati mappa ricevuta: {response_received}")
        if response_received:
            map_data = self.events_received['map_data'][0]
            print(f"Struttura dati mappa ricevuta: {json.dumps(map_data, indent=2)[:500]}...")
            
            # Verifica la struttura dei dati mappa
            self.assertIn('width', map_data, "Manca il campo width nei dati mappa")
            self.assertIn('height', map_data, "Manca il campo height nei dati mappa")
            
            if 'layers' in map_data:
                print(f"Numero di layers: {len(map_data['layers'])}")
                if len(map_data['layers']) > 0:
                    first_layer = map_data['layers'][0]
                    self.assertIn('name', first_layer, "Manca il campo name nel layer")
                    self.assertIn('data', first_layer, "Manca il campo data nel layer")
        else:
            self.fail("Nessun dato mappa ricevuto dal server")
    
    def test_request_entities(self):
        """Verifica la richiesta delle entità sulla mappa."""
        if not self._ensure_connection():
            self.fail("Impossibile stabilire la connessione WebSocket")
        
        # Registra handler per l'evento entities_update
        self.sio.on('entities_update', self.generic_event_handler('entities_update'))
        
        # Richiedi entità
        test_session_id = "test-session-" + str(int(time.time()))
        request_data = {"id_sessione": test_session_id}
        print(f"Richiesta entità con dati: {request_data}")
        self.sio.emit('request_entities', request_data)
        
        # Aspetta la risposta
        timeout = 5
        start_time = time.time()
        while 'entities_update' not in self.events_received and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        # Verifica che abbiamo ricevuto una risposta
        response_received = 'entities_update' in self.events_received
        print(f"Risposta entità ricevuta: {response_received}")
        if response_received:
            entities_data = self.events_received['entities_update'][0]
            print(f"Struttura dati entità ricevuta: {json.dumps(entities_data, indent=2)[:500]}...")
            
            # Verifica la struttura dei dati
            self.assertIn('entities', entities_data, "Manca il campo entities nei dati")
            
            if len(entities_data['entities']) > 0:
                first_entity = entities_data['entities'][0]
                self.assertIn('id', first_entity, "Manca l'id nella prima entità")
                self.assertIn('tipo', first_entity, "Manca il tipo nella prima entità")
                self.assertIn('x', first_entity, "Manca la coordinata x nella prima entità")
                self.assertIn('y', first_entity, "Manca la coordinata y nella prima entità")
        else:
            print("Nessun dato entità ricevuto, potrebbe essere normale se non ci sono entità")
    
    def _ensure_connection(self):
        """Assicura che ci sia una connessione WebSocket attiva."""
        if not self.connected:
            try:
                self.sio.connect(self.server_url, transports=['websocket'])
                timeout = 5
                start_time = time.time()
                
                # Aspetta fino a quando siamo connessi o scade il timeout
                while not self.connected and time.time() - start_time < timeout:
                    time.sleep(0.1)
            except Exception as e:
                print(f"Errore durante la connessione: {e}")
                return False
        
        return self.connected

# Se eseguito direttamente
if __name__ == '__main__':
    unittest.main() 