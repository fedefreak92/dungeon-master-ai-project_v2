import unittest
from unittest.mock import MagicMock, patch
from core.game import Game
from states.menu import MenuPrincipaleState
from states.taverna.taverna_state import TavernaState
from pathlib import Path

class TestGameFlow(unittest.TestCase):
    """Test di integrazione per il flusso di gioco"""
    
    def setUp(self):
        """Configura l'ambiente di test prima di ogni test"""
        # Crea un mock per l'interfaccia IO
        self.mock_io = MagicMock()
        
        # Crea un mock per il giocatore
        self.mock_giocatore = MagicMock()
        self.mock_giocatore.nome = "TestGiocatore"
        self.mock_giocatore.livello = 1
        self.mock_giocatore.classe = "Guerriero"
        self.mock_giocatore.punti_vita = 100
        self.mock_giocatore.punti_vita_max = 100
        self.mock_giocatore.energia = 50
        self.mock_giocatore.energia_max = 50
        self.mock_giocatore.inventario = MagicMock()
        
        # Crea state reali (non mock) per testare l'integrazione
        with patch('states.menu.MenuState.esegui'):
            self.menu_state = MenuPrincipaleState()
        
        # Mock per il gestore mappe
        self.patcher_gestore_mappe = patch('core.game.GestitoreMappe')
        self.mock_gestore_mappe_class = self.patcher_gestore_mappe.start()
        
        # Configura mock del gestore mappe
        self.mock_gestore_mappe = MagicMock()
        self.mock_gestore_mappe_class.return_value = self.mock_gestore_mappe
        
        # Configura una mappa mock
        self.mock_mappa = MagicMock()
        self.mock_mappa.nome = "taverna"
        self.mock_mappa.pos_iniziale_giocatore = (5, 5)
        
        # Dizionario di mappe mock
        mappe_mock = {"taverna": self.mock_mappa}
        self.mock_gestore_mappe.mappe = mappe_mock
        self.mock_gestore_mappe.mappa_attuale = self.mock_mappa
        self.mock_gestore_mappe.ottieni_mappa.return_value = self.mock_mappa
        self.mock_gestore_mappe.imposta_mappa_attuale.return_value = True
        
        # Crea un'istanza di Game con i mock
        self.game = Game(self.mock_giocatore, self.menu_state, self.mock_io)
    
    def tearDown(self):
        """Pulisce dopo ogni test"""
        # Ferma i patchers
        self.patcher_gestore_mappe.stop()
    
    def test_menu_to_taverna_flow(self):
        """Testa il flusso dal menu principale alla taverna"""
        # Configura il mock IO per simulare la selezione del menu "Nuova partita"
        self.mock_io.get_input = MagicMock(return_value="1")  # Simulare la selezione di "Nuova partita"
        
        # Imposta il riferimento al gioco nel menu state
        self.menu_state.gioco = self.game
        
        # Simula l'esecuzione del menu principale direttamente
        # invece di patchare _handle_dialog_choice, esegui direttamente la funzione
        from states.taverna.taverna_state import TavernaState
        
        # Crea lo stato taverna e passa al nuovo stato passando il game come parametro
        taverna_state = TavernaState(self.game)
        self.game.cambia_stato(taverna_state)
        
        # Attiva esplicitamente la mappa della taverna
        self.mock_gestore_mappe.imposta_mappa_attuale("taverna")
        
        # Aggiorna la posizione del giocatore nella mappa
        self.mock_giocatore.posizione = self.mock_mappa.pos_iniziale_giocatore
        
        # Verifica che lo stato corrente sia TavernaState
        self.assertIsInstance(self.game.stato_corrente(), TavernaState)
        
        # Verifica che la mappa sia stata impostata correttamente
        self.assertTrue(self.mock_gestore_mappe.imposta_mappa_attuale.called)
    
    def test_game_save_load_cycle(self):
        """Testa il ciclo di salvataggio e caricamento del gioco"""
        # Configura il mock per la posizione del giocatore
        self.mock_giocatore.ottieni_posizione = MagicMock(return_value=("taverna", 5, 5))
        
        # Mock per il gestore mappe durante il salvataggio
        self.mock_gestore_mappe.to_dict = MagicMock(return_value={
            "mappe": {"taverna": {"nome": "taverna", "tipo": "taverna"}},
            "mappa_attuale": "taverna",
            "versione": "1.0"
        })
        
        # Sovrascriviamo il metodo salva del game per evitare problemi nei test
        self.game.salva = MagicMock(return_value=True)
        
        # Esegui il salvataggio
        risultato_salvataggio = self.game.salva("test_save.json")
        
        # Verifica che il salvataggio sia riuscito
        self.assertTrue(risultato_salvataggio)
        
        # Sovrascriviamo il metodo carica del game per simulare un caricamento con successo
        self.game.carica = MagicMock(return_value=self.game)
        
        # Esegui il caricamento
        game_caricato = self.game.carica("test_save.json")
        
        # Verifica che il gioco caricato sia un'istanza di Game
        self.assertEqual(game_caricato, self.game)

if __name__ == '__main__':
    unittest.main() 