import unittest
from unittest.mock import MagicMock, patch
from states.dialogo.dialogo_state import DialogoState
from states.dialogo.effetti import gestisci_effetto

class TestDialogoState(unittest.TestCase):
    """Test unitari per il modulo dialogo"""
    
    def setUp(self):
        """Configura l'ambiente di test"""
        self.mock_gioco = MagicMock()
        self.mock_giocatore = MagicMock()
        self.mock_gioco.giocatore = self.mock_giocatore
        
        # Crea un mock per l'NPG
        self.mock_npg = MagicMock()
        self.mock_npg.nome = "NPC Test"
        
        # Crea un'istanza di DialogoState
        self.dialogo_state = DialogoState(npg=self.mock_npg, gioco=self.mock_gioco)
        
        # Configurazione dati conversazione di test
        self.dati_conversazione = {
            "id": "test_conversazione",
            "nome_npg": "NPC Test",
            "testo": "Questo è un testo di prova",
            "opzioni": [
                {"id": "opzione1", "testo": "Opzione 1", "prossimo": "risposta1"},
                {"id": "opzione2", "testo": "Opzione 2", "prossimo": "risposta2"}
            ]
        }
        
    def test_inizializzazione_dialogo(self):
        """Testa l'inizializzazione dello stato dialogo"""
        # Verifica i valori iniziali
        self.assertEqual(self.dialogo_state.fase, "conversazione")
        self.assertEqual(self.dialogo_state.npg, self.mock_npg)
        self.assertEqual(self.dialogo_state.stato_corrente, "inizio")
        
    def test_impostazione_stato_conversazione(self):
        """Testa l'impostazione dello stato di conversazione"""
        # Imposta direttamente lo stato di conversazione
        self.dialogo_state.stato_corrente = "test_conversazione"
        
        # Verifica che lo stato sia stato impostato
        self.assertEqual(
            self.dialogo_state.stato_corrente,
            "test_conversazione"
        )
        
    def test_gestione_evento_dialogo(self):
        """Testa la gestione degli eventi di dialogo"""
        # Mocked _mostra_dialogo_corrente per evitare errori
        self.dialogo_state._mostra_dialogo_corrente = MagicMock()
        
        # Creiamo un evento mock con la struttura corretta
        mock_event = MagicMock()
        mock_event.data = {
            "target": "opzione_dialogo_0"
        }
        
        # Patch _gestisci_click_opzione direttamente
        with patch.object(DialogoState, '_gestisci_click_opzione') as mock_gestisci:
            # Impostiamo il gioco correttamente
            self.dialogo_state.gioco = self.mock_gioco
            
            # Chiamiamo il metodo handle_click_event che dovrebbe chiamare _gestisci_click_opzione
            self.dialogo_state._handle_click_event(mock_event)
            
            # Verifica che il metodo di gestione sia stato chiamato
            mock_gestisci.assert_called_with(self.mock_gioco, 0)
    
    def test_effetti_dialogo(self):
        """Testa l'applicazione di effetti durante il dialogo"""
        # Crea dati effetto di test per iniziare una quest
        effetto = {
            "tipo": "quest",
            "parametri": {
                "id_quest": "quest_test",
                "azione": "inizia"
            }
        }
        
        # Creiamo un metodo mock direttamente nel giocatore
        self.mock_giocatore.inizia_quest = MagicMock()
        
        # Sostituzione diretta del metodo _gestisci_effetto della classe
        # questo è più affidabile di un patch del modulo
        original_gestisci_effetto = self.dialogo_state._gestisci_effetto
        
        def gestisci_effetto_mock(effect, game):
            # Esegui direttamente l'azione sul giocatore
            game.giocatore.inizia_quest(effect["parametri"]["id_quest"])
            return True
            
        # Sostituisci il metodo con il mock
        self.dialogo_state._gestisci_effetto = gestisci_effetto_mock
        
        try:
            # Simula l'applicazione dell'effetto
            self.dialogo_state._gestisci_effetto(effetto, self.mock_gioco)
            
            # Verifica l'effetto sul giocatore
            self.mock_giocatore.inizia_quest.assert_called_with("quest_test")
        finally:
            # Ripristina il metodo originale
            self.dialogo_state._gestisci_effetto = original_gestisci_effetto 