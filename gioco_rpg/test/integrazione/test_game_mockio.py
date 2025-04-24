import unittest
from unittest.mock import MagicMock, patch
from core.game import Game
from core.io_interface import MockIO
from entities.giocatore import Giocatore

class TestGameMockIO(unittest.TestCase):
    """Test di integrazione tra Game e MockIO"""
    
    def setUp(self):
        """Configura l'ambiente di test prima di ogni test"""
        # Patch per il caricamento dei dati delle classi dal file JSON
        self.json_patcher = patch('json.load')
        self.mock_json_load = self.json_patcher.start()
        self.mock_json_load.return_value = {
            "guerriero": {
                "statistiche_base": {
                    "hp_base": 25,
                    "forza": 15,
                    "destrezza": 10,
                    "costituzione": 14,
                    "intelligenza": 8,
                    "saggezza": 10,
                    "carisma": 10
                }
            }
        }
        
        # Patch per l'apertura di file
        self.open_patcher = patch('builtins.open', new_callable=MagicMock())
        self.mock_open = self.open_patcher.start()
        
        # Patch GestitoreMappe
        self.gestore_mappe_patcher = patch('core.game.GestitoreMappe')
        self.mock_gestore_class = self.gestore_mappe_patcher.start()
        self.mock_gestore = MagicMock()
        self.mock_gestore_class.return_value = self.mock_gestore
        
        # Crea un mock per lo stato iniziale
        self.mock_stato = MagicMock()
        
        # Crea un giocatore
        self.giocatore = Giocatore("TestGiocatore", "guerriero")
        
        # Crea un'istanza di MockIO
        self.io = MockIO()
        
        # Crea un'istanza di Game
        self.game = Game(self.giocatore, self.mock_stato, self.io)
        
    def tearDown(self):
        """Pulisce l'ambiente dopo ogni test"""
        self.json_patcher.stop()
        self.open_patcher.stop()
        self.gestore_mappe_patcher.stop()
        
    def test_mostra_messaggio(self):
        """Verifica che i messaggi mostrati tramite Game vengano registrati in MockIO"""
        # Mostra un messaggio tramite l'io in Game
        self.game.io.mostra_messaggio("Test messaggio")
        
        # Verifica che il messaggio sia registrato in MockIO
        output_messages = self.io.get_output_messages()
        self.assertTrue(any(msg.get("testo") == "Test messaggio" for msg in output_messages))
        
    def test_interazione_input(self):
        """Verifica che l'input fornito da MockIO venga utilizzato dal Game"""
        # Configura una sequenza di input
        self.io.add_input_sequence(["comando di test"])
        
        # Richiedi input
        input_ricevuto = self.game.io.richiedi_input("Inserisci comando:")
        
        # Verifica che il gioco abbia ricevuto l'input corretto
        self.assertEqual(input_ricevuto, "comando di test")
        
    def test_cambio_stato(self):
        """Verifica che il cambio di stato nel gioco generi messaggi corretti in MockIO"""
        # Crea uno stato mock con metodi mock
        nuovo_stato = MagicMock()
        
        # Configura il mock per generare un messaggio quando entra
        nuovo_stato.entra = MagicMock(side_effect=lambda game: game.io.mostra_messaggio("Entrato in nuovo stato"))
        
        # Cambia lo stato
        self.game.cambia_stato(nuovo_stato)
        
        # Verifica che il messaggio di entrata sia stato registrato in MockIO
        output_messages = self.io.get_output_messages()
        self.assertTrue(any(msg.get("testo") == "Entrato in nuovo stato" for msg in output_messages))
        
        # Verifica che lo stato sia stato cambiato
        self.assertEqual(self.game.stato_stack[-1], nuovo_stato)

if __name__ == '__main__':
    unittest.main() 