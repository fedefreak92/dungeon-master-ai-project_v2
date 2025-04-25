import unittest
from unittest.mock import MagicMock, patch
from states.prova_abilita.prova_abilita_state import ProvaAbilitaState
from states.prova_abilita.esecuzione import esegui_prova_base_grafica, esegui_prova
from util.dado import Dado

class TestProvaAbilita(unittest.TestCase):
    """Test unitari per il modulo prova_abilita"""
    
    def setUp(self):
        """Configura l'ambiente di test"""
        self.mock_gioco = MagicMock()
        self.mock_giocatore = MagicMock()
        self.mock_gioco.giocatore = self.mock_giocatore
        self.mock_giocatore.modificatore_abilita.return_value = 3
        self.mock_giocatore.nome = "TestGiocatore"
        
        # Configura un'istanza reale dello stato
        self.prova_state = ProvaAbilitaState()
        self.prova_state.abilita_scelta = "forza"
        
    def test_inizializzazione(self):
        """Testa l'inizializzazione dello stato prova abilità"""
        # Verifica che lo stato sia inizializzato con la fase corretta
        self.assertEqual(self.prova_state.fase, "scegli_abilita")
        self.assertEqual(self.prova_state.abilita_scelta, "forza")
        
    @patch('states.prova_abilita.esecuzione.ABILITA_ASSOCIATE', ["forza"])
    def test_esecuzione_prova(self):
        """Testa l'esecuzione di una prova di abilità"""
        # Patch il dado per avere un risultato fisso
        with patch('util.dado.Dado.tira', return_value=15):
            # Esegui la prova con difficoltà 10
            esegui_prova_base_grafica(self.prova_state, self.mock_gioco, 10)
            
            # Verifica che il messaggio sia stato mostrato almeno una volta
            # (potrebbe essere chiamato più volte per mostrare diversi messaggi)
            self.mock_gioco.io.mostra_dialogo.assert_called()
            
            # Verifichiamo che il secondo messaggio mostrato includa informazioni sul tiro
            calls = self.mock_gioco.io.mostra_dialogo.call_args_list
            self.assertEqual(len(calls), 2)
            self.assertIn("TestGiocatore tira un 15 + 3 (forza) = 18", calls[1][0][1])
            self.assertIn("Difficoltà: 10", calls[1][0][1])
            
    def test_confronto_abilita(self):
        """Testa il confronto tra due entità"""
        mock_entita1 = MagicMock()
        mock_entita1.id = "entita1"
        mock_entita1.name = "Entità 1"
        mock_entita1.modificatore_abilita.return_value = 3
        
        mock_entita2 = MagicMock()
        mock_entita2.id = "entita2"
        mock_entita2.name = "Entità 2"
        mock_entita2.modificatore_abilita.return_value = 2
        
        mock_sessione = MagicMock()
        
        # Patch il dado per avere risultati fissi
        with patch('util.dado.Dado.tira', side_effect=[15, 10]):
            # Esegui la prova di confronto
            risultato = esegui_prova(
                self.prova_state, 
                mock_sessione, 
                mock_entita1, 
                "forza", 
                0, 
                target=mock_entita2
            )
            
            # Verifica il risultato
            self.assertTrue(risultato["successo"])
            self.assertEqual(risultato["entita"]["id"], "entita1")
            self.assertEqual(risultato["abilita"], "forza") 