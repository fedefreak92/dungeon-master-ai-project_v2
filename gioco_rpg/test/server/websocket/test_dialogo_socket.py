import unittest
from unittest.mock import MagicMock, patch
from flask import Flask
from flask_socketio import SocketIO
from server.websocket.dialogo import handle_dialogo_inizializza, handle_dialogo_scelta

class TestDialogoWebSocket(unittest.TestCase):
    """Test per gli eventi WebSocket del dialogo"""
    
    def setUp(self):
        """Configura l'ambiente di test"""
        # Crea una Flask app e SocketIO
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app)
        
        # Patch emit
        self.patcher_emit = patch('server.websocket.dialogo.emit')
        self.mock_emit = self.patcher_emit.start()
        
        # Patch join_room
        self.patcher_join_room = patch('server.websocket.dialogo.join_room')
        self.mock_join_room = self.patcher_join_room.start()
        
        # Patch get_session dal modulo core 
        self.patcher_get_session = patch('server.websocket.core.get_session')
        self.mock_get_session = self.patcher_get_session.start()
        
        # Configura una sessione mock
        self.mock_sessione = MagicMock()
        self.mock_get_session.return_value = self.mock_sessione
        
        # Patch validate_request_data per evitare validazioni che potrebbero fallire
        self.patcher_validate = patch('server.websocket.core.validate_request_data', return_value=True)
        self.mock_validate = self.patcher_validate.start()
        
    def tearDown(self):
        """Pulisce dopo il test"""
        self.patcher_emit.stop()
        self.patcher_join_room.stop()
        self.patcher_get_session.stop()
        self.patcher_validate.stop()
    
    def test_inizializza_dialogo(self):
        """Testa l'inizializzazione di un dialogo via WebSocket"""
        # Dati per la richiesta
        dati = {
            'id_sessione': 'sessione_test',
            'id_conversazione': 'conversazione_test'
        }
        
        # Configura il mock della sessione per restituire uno stato dialogo
        dialogo_state_mock = MagicMock()
        dialogo_state_mock.npg = MagicMock()
        dialogo_state_mock.npg.nome = "NPC Test"
        dialogo_state_mock.npg.ottieni_conversazione.return_value = {
            "testo": "Testo di dialogo", 
            "opzioni": []
        }
        dialogo_state_mock.stato_corrente = "inizio"
        
        # Cambia la risposta del metodo get_state
        self.mock_sessione.get_state.return_value = dialogo_state_mock
        
        # Usa il contesto dell'app per evitare l'errore di contesto richiesta
        with self.app.test_request_context():
            # Chiama l'handler
            handle_dialogo_inizializza(dati)
            
            # Verifica che join_room sia stato chiamato
            self.mock_join_room.assert_called_once_with('session_sessione_test')
            
            # Verifica che emit sia stato chiamato per inviare lo stato
            self.mock_emit.assert_called()
    
    def test_scegli_opzione_dialogo(self):
        """Testa la selezione di un'opzione di dialogo via WebSocket"""
        # Dati per la richiesta
        dati = {
            'id_sessione': 'sessione_test',
            'scelta_indice': 0
        }
        
        # Patch la funzione requests.post
        with patch('server.websocket.dialogo.requests.post') as mock_post:
            # Configura la risposta mock
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'dialogo': {'testo': 'Risposta di test'},
                'terminato': False
            }
            mock_post.return_value = mock_response
            
            # Usa il contesto dell'app per evitare l'errore di contesto richiesta
            with self.app.test_request_context():
                # Chiama l'handler
                handle_dialogo_scelta(dati)
                
                # Verifica che requests.post sia stato chiamato con i parametri corretti
                mock_post.assert_called_with(
                    "http://localhost:5000/game/dialogo/scelta",
                    json={
                        "id_sessione": 'sessione_test',
                        "scelta_indice": 0
                    }
                )
                
                # Verifica che emit sia stato chiamato per aggiornare il client
                self.mock_emit.assert_called() 