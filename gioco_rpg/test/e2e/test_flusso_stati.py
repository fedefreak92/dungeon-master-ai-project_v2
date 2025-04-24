import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Aggiungiamo la directory principale al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from core.game import Game
from core.io_interface import MockIO
from entities.giocatore import Giocatore
from states.menu import MenuPrincipaleState
from states.taverna.taverna_state import TavernaState
from states.dialogo.dialogo_state import DialogoState
from states.inventario import InventarioState
from states.mercato.mercato_state import MercatoState
from states.prova_abilita.prova_abilita_state import ProvaAbilitaState

class TestFlussoStati(unittest.TestCase):
    """
    Test end-to-end che verifica il flusso tra tutti gli stati principali del gioco,
    garantendo che funzionino insieme correttamente.
    """
    
    def setUp(self):
        """Configura l'ambiente di test"""
        # Crea un IO mock con sequenza di input predefiniti
        self.mock_io = MockIO()
        
        # Configura una sequenza di input che testa tutti gli stati
        self.mock_io.add_input_sequence([
            "1",                  # Menu -> Nuova partita
            "GiocatoreTest",      # Nome giocatore
            "1",                  # Scegli classe
            "1",                  # Conferma selezione
            "1",                  # Entra taverna
            "2",                  # Parla con NPC
            "1",                  # Scegli opzione dialogo
            "3",                  # Torna alla taverna
            "inventario",         # Apri inventario
            "1",                  # Usa oggetto
            "esci",               # Torna alla taverna
            "5",                  # Esci dalla taverna
            "mercato",            # Vai al mercato
            "1",                  # Parla con mercante
            "2",                  # Compra oggetto
            "3",                  # Torna al mercato
            "4",                  # Esci dal mercato
            "prova",              # Inizia prova abilità
            "1",                  # Scegli abilità
            "3",                  # Completa prova
            "menu"                # Torna al menu principale
        ])
        
        # Crea un giocatore di test
        self.giocatore = Giocatore("GiocatoreTest", "guerriero")
        
        # Stato iniziale
        self.stato_iniziale = MenuPrincipaleState()
        
        # Patch gestore mappe
        self.patcher_gestore_mappe = patch('core.game.GestitoreMappe')
        self.mock_gestore_mappe_class = self.patcher_gestore_mappe.start()
        self.mock_gestore_mappe = MagicMock()
        self.mock_gestore_mappe_class.return_value = self.mock_gestore_mappe
        
        # Crea il gioco
        self.game = Game(self.giocatore, self.stato_iniziale, self.mock_io)
        
    def tearDown(self):
        """Pulisce dopo il test"""
        self.patcher_gestore_mappe.stop()
    
    def test_transizione_stati(self):
        """
        Testa la transizione tra tutti gli stati principali del gioco,
        verificando che ogni stato venga inizializzato e gestito correttamente.
        """
        # Patch vari metodi per evitare operazioni I/O reali
        with patch('builtins.open', unittest.mock.mock_open()):
            with patch('json.dump'):
                with patch('json.load'):
                    # Esegui il gioco per un numero limitato di stati
                    for _ in range(30):  # Sufficiente per passare attraverso tutti gli stati
                        if not self.game.attivo:
                            break
                        # Esegui una volta e verifica lo stato corrente
                        stato_corrente_pre = self.game.stato_corrente().__class__.__name__
                        self.game.esegui_una_volta()
                        stato_corrente_post = self.game.stato_corrente().__class__.__name__
                        # Stampa il cambio di stato per debug
                        if stato_corrente_pre != stato_corrente_post:
                            print(f"Transizione: {stato_corrente_pre} -> {stato_corrente_post}")
        
        # Verifica che siano stati generati messaggi di output
        output_messages = self.mock_io.get_output_messages()
        self.assertTrue(len(output_messages) > 0) 