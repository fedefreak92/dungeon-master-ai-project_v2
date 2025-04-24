import unittest
from unittest.mock import MagicMock, patch
from states.taverna import TavernaState

class TestTavernaState(unittest.TestCase):
    """Test per il modulo della taverna"""
    
    def setUp(self):
        """Setup per i test"""
        self.mock_gioco = MagicMock()
        self.mock_gioco.giocatore = MagicMock()
        self.mock_gioco.giocatore.nome = "TestPlayer"
        self.taverna = TavernaState(self.mock_gioco)
        
    def test_inizializzazione(self):
        """Verifica che lo stato della taverna sia inizializzato correttamente"""
        self.assertEqual(self.taverna.nome_stato, "taverna")
        self.assertTrue(self.taverna.prima_visita)
        self.assertEqual(self.taverna.fase, "menu_principale")
        self.assertIsNotNone(self.taverna.npg_presenti)
        self.assertIsNotNone(self.taverna.oggetti_interattivi)
        
    def test_npg_taverna(self):
        """Verifica che gli NPC della taverna siano presenti"""
        self.assertIn("Durnan", self.taverna.npg_presenti)
        self.assertIn("Elminster", self.taverna.npg_presenti)
        self.assertIn("Mirt", self.taverna.npg_presenti)
        
    def test_oggetti_interattivi(self):
        """Verifica che gli oggetti interattivi della taverna siano presenti"""
        self.assertIn("bancone", self.taverna.oggetti_interattivi)
        self.assertIn("camino", self.taverna.oggetti_interattivi)
        self.assertIn("baule_nascondiglio", self.taverna.oggetti_interattivi)
        
    @patch('states.taverna.ui_handlers.TavernaUI.mostra_benvenuto')
    def test_prima_visita(self, mock_mostra_benvenuto):
        """Verifica che il benvenuto venga mostrato alla prima visita"""
        self.taverna.esegui(self.mock_gioco)
        mock_mostra_benvenuto.assert_called_once_with(self.mock_gioco)
        
    def test_pausa_e_riprendi(self):
        """Verifica che i metodi pausa e riprendi funzionino correttamente"""
        # Impostiamo uno stato menu attivo iniziale
        self.taverna.menu_attivo = "menu_principale"
        
        # Chiamiamo il metodo pausa
        self.taverna.pausa(self.mock_gioco)
        
        # Verifichiamo che lo stato precedente sia salvato
        self.assertEqual(self.taverna.stato_precedente, "menu_principale")
        
        # Verifichiamo che l'interfaccia mostri la notifica
        self.mock_gioco.io.mostra_transizione.assert_called_once()
        self.mock_gioco.io.mostra_notifica.assert_called_once()
        
        # Resettiamo i mock
        self.mock_gioco.io.mostra_transizione.reset_mock()
        self.mock_gioco.io.mostra_notifica.reset_mock()
        
        # Chiamiamo il metodo riprendi
        self.taverna.riprendi(self.mock_gioco)
        
        # Verifichiamo che l'interfaccia mostri la notifica
        self.mock_gioco.io.mostra_transizione.assert_called_once()
        self.mock_gioco.io.mostra_notifica.assert_called_once()
        
        # Verifichiamo che lo stato precedente sia ripristinato
        self.assertEqual(self.taverna.menu_attivo, "menu_principale")
        self.assertIsNone(self.taverna.stato_precedente)

if __name__ == '__main__':
    unittest.main() 