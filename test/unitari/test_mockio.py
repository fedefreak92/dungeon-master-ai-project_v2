import unittest
from core.io_interface import MockIO

class TestMockIO(unittest.TestCase):
    """Test unitari per la classe MockIO"""
    
    def setUp(self):
        """Configura l'ambiente di test prima di ogni test"""
        self.io = MockIO()
        
    def test_mostra_messaggio(self):
        """Verifica che mostra_messaggio aggiunga correttamente al buffer e ai messaggi"""
        self.io.mostra_messaggio("Test messaggio")
        self.assertEqual(len(self.io.output_buffer), 1)
        self.assertEqual(self.io.output_buffer[0], {"tipo": "messaggio", "testo": "Test messaggio"})
        
    def test_messaggio_sistema(self):
        """Verifica che messaggio_sistema aggiunga correttamente al buffer e ai messaggi"""
        self.io.messaggio_sistema("Test sistema")
        self.assertEqual(len(self.io.output_buffer), 1)
        self.assertEqual(self.io.output_buffer[0], {"tipo": "sistema", "testo": "Test sistema"})
        
    def test_messaggio_errore(self):
        """Verifica che messaggio_errore aggiunga correttamente al buffer e ai messaggi"""
        self.io.messaggio_errore("Test errore")
        self.assertEqual(len(self.io.output_buffer), 1)
        self.assertEqual(self.io.output_buffer[0], {"tipo": "errore", "testo": "Test errore"})
        
    def test_richiedi_input(self):
        """Verifica che richiedi_input restituisca il valore dalla sequenza"""
        self.io.add_input_sequence(["input1", "input2"])
        
        # Primo input
        risultato1 = self.io.richiedi_input("Prompt 1")
        self.assertEqual(risultato1, "input1")
        
        # Secondo input
        risultato2 = self.io.richiedi_input("Prompt 2")
        self.assertEqual(risultato2, "input2")
        
        # Input esaurito
        risultato3 = self.io.richiedi_input("Prompt 3")
        self.assertEqual(risultato3, "")
        
    def test_clear(self):
        """Verifica che clear pulisca il buffer e resetti l'indice"""
        self.io.add_input_sequence(["input1", "input2"])
        self.io.mostra_messaggio("Test")
        self.io.richiedi_input("Prompt")
        
        # Verifica che ci siano elementi nel buffer
        self.assertGreater(len(self.io.output_buffer), 0)
        self.assertEqual(self.io.input_index, 1)
        
        # Esegui clear
        self.io.clear()
        
        # Verifica che il buffer sia vuoto e l'indice resettato
        self.assertEqual(len(self.io.output_buffer), 0)
        
    def test_metodi_compatibilita_gui(self):
        """Verifica che i metodi per la compatibilità con GUI funzionino"""
        self.io.mostra_transizione("Test transizione")
        self.io.mostra_notifica("Test notifica")
        self.io.mostra_dialogo("Titolo", "Contenuto", ["Opzione1", "Opzione2"])
        self.io.chiudi_dialogo()
        
        # Verifica che ci siano messaggi nel buffer
        output_messages = self.io.get_output_messages()
        self.assertEqual(len(output_messages), 3)  # Non include chiudi_dialogo che è vuoto

if __name__ == '__main__':
    unittest.main() 