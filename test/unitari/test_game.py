import unittest
from unittest.mock import MagicMock, patch
from core.game import Game
from entities.giocatore import Giocatore

class TestGame(unittest.TestCase):
    """Test unitari per la classe Game"""
    
    def setUp(self):
        """Configura l'ambiente di test prima di ogni test"""
        self.mock_io = MagicMock()
        self.mock_stato = MagicMock()
        self.giocatore = MagicMock()
        self.giocatore.nome = "TestGiocatore"
        
        # Patch più profondo per evitare completamente l'inizializzazione del gestore mappe reale
        # Per farlo, sostituiamo direttamente l'inizializzazione in Game.__init__
        self.game_init_patcher = patch('core.game.GestitoreMappe', autospec=True)
        self.mock_gestore_class = self.game_init_patcher.start()
        
        # Configura il mock del gestore mappe
        self.mock_gestore = MagicMock()
        
        # Configura la mappa mock
        self.mock_mappa = MagicMock()
        self.mock_mappa.pos_iniziale_giocatore = (5, 5)
        self.mock_mappa.dimensioni = (20, 20)
        self.mock_mappa.id = "taverna"
        
        # Dictionary di mappe fittizie
        self.mappe_fittizie = {
            "taverna": self.mock_mappa
        }
        
        # Imposta i metodi del gestore mappe
        self.mock_gestore.mappe = self.mappe_fittizie
        self.mock_gestore.ottieni_mappa = MagicMock(return_value=self.mock_mappa)
        self.mock_gestore.imposta_mappa_attuale = MagicMock()
        
        # Imposta il ritorno del costruttore
        self.mock_gestore_class.return_value = self.mock_gestore
        
        # Crea l'istanza di Game con i mock
        self.game = Game(self.giocatore, self.mock_stato, self.mock_io)
        
    def tearDown(self):
        """Pulisce l'ambiente dopo ogni test"""
        self.game_init_patcher.stop()
        
    def test_inizializzazione(self):
        """Verifica che il gioco sia inizializzato correttamente"""
        self.assertEqual(self.game.giocatore.nome, "TestGiocatore")
        self.assertTrue(self.game.attivo)
        self.assertIsNotNone(self.game.gestore_mappe)
        self.assertIsNotNone(self.game.io)
        
    def test_push_stato(self):
        """Verifica che il push di uno stato funzioni correttamente"""
        nuovo_stato = MagicMock()
        self.game.push_stato(nuovo_stato)
        
        # Verifica che lo stato sia stato aggiunto allo stack
        self.assertIn(nuovo_stato, self.game.stato_stack)
        # Verifica che il metodo entra sia stato chiamato
        nuovo_stato.entra.assert_called_once_with(self.game)
        
    def test_pop_stato(self):
        """Verifica che il pop di uno stato funzioni correttamente"""
        # Aggiungi due stati allo stack
        stato1 = MagicMock()
        stato2 = MagicMock()
        self.game.stato_stack = [stato1, stato2]
        
        # Esegui il pop dello stato
        self.game.pop_stato()
        
        # Verifica che il metodo esci sia stato chiamato sullo stato rimosso
        stato2.esci.assert_called_once_with(self.game)
        # Verifica che lo stack contenga solo lo stato1
        self.assertEqual(len(self.game.stato_stack), 1)
        self.assertEqual(self.game.stato_stack[0], stato1)
        # Verifica che il metodo riprendi sia stato chiamato sullo stato1
        stato1.riprendi.assert_called_once_with(self.game)
        
    def test_cambia_stato(self):
        """Verifica che il cambio di stato funzioni correttamente"""
        # Aggiungi uno stato iniziale allo stack
        stato_iniziale = MagicMock()
        self.game.stato_stack = [stato_iniziale]
        
        # Crea un nuovo stato
        nuovo_stato = MagicMock()
        
        # Esegui il cambio di stato
        self.game.cambia_stato(nuovo_stato)
        
        # Verifica che il metodo esci sia stato chiamato sullo stato iniziale
        stato_iniziale.esci.assert_called_once_with(self.game)
        # Verifica che lo stack contenga solo il nuovo stato
        self.assertEqual(len(self.game.stato_stack), 1)
        self.assertEqual(self.game.stato_stack[0], nuovo_stato)
        # Verifica che il metodo entra sia stato chiamato sul nuovo stato
        nuovo_stato.entra.assert_called_once_with(self.game)
        
    def test_imposta_mappa_iniziale(self):
        """Verifica che l'impostazione della mappa iniziale funzioni correttamente"""
        # Imposta la mappa iniziale
        risultato = self.game.imposta_mappa_iniziale("taverna")
        
        # Verifica che il metodo ottieni_mappa sia stato chiamato
        self.game.gestore_mappe.ottieni_mappa.assert_called_once_with("taverna")
        # Verifica che il metodo imposta_mappa_attuale sia stato chiamato
        self.game.gestore_mappe.imposta_mappa_attuale.assert_called_once_with("taverna")
        # Verifica che il giocatore sia stato posizionato correttamente
        self.giocatore.imposta_posizione.assert_called_once_with("taverna", 5, 5)
        # Verifica che il metodo restituisca True
        self.assertTrue(risultato)

if __name__ == '__main__':
    unittest.main() 