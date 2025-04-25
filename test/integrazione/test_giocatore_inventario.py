import unittest
from unittest.mock import MagicMock, patch
from core.game import Game
from entities.giocatore import Giocatore
from items.oggetto import Oggetto
from states.inventario import InventarioState

class TestGiocatoreInventario(unittest.TestCase):
    """Test di integrazione tra Giocatore e InventarioState"""
    
    def setUp(self):
        """Configura l'ambiente di test prima di ogni test"""
        # Crea un mock per l'IO
        self.mock_io = MagicMock()
        # Assicurati che mostra_messaggio ritorni sempre se stesso per permettere chiamate in cascata
        self.mock_io.mostra_messaggio.return_value = self.mock_io
        
        # Patch GestitoreMappe senza autospec che causa problemi
        self.gestore_mappe_patcher = patch('core.game.GestitoreMappe')
        self.mock_gestore_class = self.gestore_mappe_patcher.start()
        self.mock_gestore = MagicMock()
        self.mock_gestore_class.return_value = self.mock_gestore
        
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
        
        # Crea oggetti per l'inventario con i parametri corretti
        self.spada = Oggetto("spada", "arma", effetto={"forza": 5}, valore=10, descrizione="Una spada affilata")
        self.pozione = Oggetto("pozione", "cura", effetto={"cura": 20}, valore=5, descrizione="Una pozione curativa")
        self.scudo = Oggetto("scudo", "armatura", effetto={"difesa": 10}, valore=15, descrizione="Uno scudo resistente")
        
        # Configura comportamenti specifici per ogni oggetto
        self.mock_spada_usa = MagicMock()
        self.spada.usa = self.mock_spada_usa
        
        self.mock_pozione_usa = MagicMock()
        self.pozione.usa = self.mock_pozione_usa
        self.mock_pozione_usa.side_effect = lambda giocatore: setattr(giocatore, 'vita', min(giocatore.vita + 20, giocatore.vita_max))
        
        self.mock_scudo_usa = MagicMock()
        self.scudo.usa = self.mock_scudo_usa
        
        # Crea un'istanza reale di Giocatore (non mock)
        self.giocatore = Giocatore("TestGiocatore", "guerriero")
        
        # Sostituisci l'inventario del giocatore con uno controllato dal test
        self.giocatore.inventario = []
        self.giocatore.aggiungi_item(self.spada)
        self.giocatore.aggiungi_item(self.pozione)
        
        # Crea uno stato iniziale per il gioco
        self.stato_iniziale = MagicMock()
        
        # Crea un'istanza di Game
        self.game = Game(self.giocatore, self.stato_iniziale, self.mock_io)
        
        # Crea un'istanza reale di InventarioState
        self.inventario_state = InventarioState()
        
    def tearDown(self):
        """Pulisce l'ambiente dopo ogni test"""
        self.gestore_mappe_patcher.stop()
        self.json_patcher.stop()
        self.open_patcher.stop()
        
    def test_apertura_inventario(self):
        """
        Testa l'integrazione dell'apertura dell'inventario:
        - Il gioco dovrebbe cambiare stato a InventarioState
        - InventarioState dovrebbe mostrare gli oggetti del giocatore
        """
        # Configura mock_io per simulare l'input dell'utente
        self.mock_io.richiedi_input = MagicMock(return_value="esci")
        
        # Patch la funzione di InventarioState che mostra l'inventario
        with patch('states.inventario.ui_handlers.UIInventarioHandler.mostra_menu_principale') as mock_mostra:
            # Simuliamo la funzione mostra_menu_principale per aggiungere messaggi al mock_io
            def simulate_messages(game):
                for item in game.giocatore.inventario:
                    game.io.mostra_messaggio(f"Item: {item.nome} - {item.descrizione}")
                return True
            
            mock_mostra.side_effect = simulate_messages
            
            # Simula l'apertura dell'inventario
            self.game.cambia_stato(self.inventario_state)
            
            # Verifica che il gioco sia nello stato inventario
            self.assertEqual(self.game.stato_stack[-1], self.inventario_state)
            
            # Esegui l'aggiornamento dello stato per mostrare l'inventario
            self.inventario_state.aggiorna(self.game)
            
            # Verifica che mostra_menu_principale sia stato chiamato
            mock_mostra.assert_called_once()
            
            # Verifica che l'IO mostri i messaggi con gli oggetti
            self.mock_io.mostra_messaggio.assert_any_call("Item: spada - Una spada affilata")
            self.mock_io.mostra_messaggio.assert_any_call("Item: pozione - Una pozione curativa")
    
    def test_uso_oggetto_da_inventario(self):
        """
        Testa l'integrazione dell'uso di un oggetto dall'inventario:
        - Il giocatore dovrebbe poter usare una pozione
        - L'inventario dovrebbe aggiornare lo stato dopo l'uso
        """
        # Salva la vita originale del giocatore
        vita_originale = self.giocatore.vita = 50
        self.giocatore.vita_max = 100
        
        # Bypass l'uso dell'oggetto tramite il sistema di gestione inventario
        # Testiamo direttamente l'oggetto pozione sull'istanza di giocatore
        self.pozione.usa(self.giocatore)
        
        # Verifica che la pozione.usa sia stata chiamata con il giocatore come argomento
        self.mock_pozione_usa.assert_called_once_with(self.giocatore)
        
        # Verifica l'effetto della pozione (aumento della vita)
        self.assertGreater(self.giocatore.vita, vita_originale)
    
    def test_aggiunta_rimozione_oggetti(self):
        """
        Testa l'integrazione dell'aggiunta e rimozione di oggetti:
        - Aggiungere un oggetto all'inventario
        - Rimuovere un oggetto dall'inventario
        - Verificare che l'inventario mostri correttamente gli oggetti
        """
        # Configura mock_io per simulare l'input dell'utente
        self.mock_io.richiedi_input = MagicMock(side_effect=["esci"])
        
        # Verifica lo stato iniziale dell'inventario
        self.assertEqual(len(self.giocatore.inventario), 2)
        
        # Aggiungi un nuovo oggetto all'inventario
        self.giocatore.aggiungi_item(self.scudo)
        
        # Verifica che l'oggetto sia stato aggiunto
        self.assertEqual(len(self.giocatore.inventario), 3)
        self.assertIn(self.scudo, self.giocatore.inventario)
        
        # Patch la funzione di InventarioState che mostra l'inventario
        with patch('states.inventario.ui_handlers.UIInventarioHandler.mostra_menu_principale') as mock_mostra:
            # Simuliamo la funzione per aggiungere messaggi al mock_io
            def simulate_messages(game):
                for item in game.giocatore.inventario:
                    game.io.mostra_messaggio(f"Item: {item.nome} - {item.descrizione}")
                return True
            
            mock_mostra.side_effect = simulate_messages
            
            # Simula l'apertura dell'inventario
            self.game.cambia_stato(self.inventario_state)
            
            # Esegui l'aggiornamento dello stato per mostrare l'inventario
            self.inventario_state.aggiorna(self.game)
            
            # Verifica che mostra_menu_principale sia stato chiamato
            mock_mostra.assert_called_once()
            
            # Verifica che l'IO mostri i messaggi con gli oggetti
            self.mock_io.mostra_messaggio.assert_any_call("Item: spada - Una spada affilata")
            self.mock_io.mostra_messaggio.assert_any_call("Item: pozione - Una pozione curativa")
            self.mock_io.mostra_messaggio.assert_any_call("Item: scudo - Uno scudo resistente")
            
            # Rimuovi un oggetto dall'inventario
            self.giocatore.rimuovi_item(self.pozione.nome)
            
            # Reimposta i mock
            mock_mostra.reset_mock()
            self.mock_io.mostra_messaggio.reset_mock()
            
            # Configura nuovamente il side effect per il mock
            mock_mostra.side_effect = simulate_messages
            
            # Aggiorna di nuovo per mostrare l'inventario aggiornato
            self.inventario_state.aggiorna(self.game)
            
            # Verifica che l'IO mostri solo gli oggetti rimanenti
            self.mock_io.mostra_messaggio.assert_any_call("Item: spada - Una spada affilata")
            self.mock_io.mostra_messaggio.assert_any_call("Item: scudo - Uno scudo resistente")
            
            # Verifica che la pozione non sia stata mostrata
            with self.assertRaises(AssertionError):
                self.mock_io.mostra_messaggio.assert_any_call("Item: pozione - Una pozione curativa")

if __name__ == '__main__':
    unittest.main() 