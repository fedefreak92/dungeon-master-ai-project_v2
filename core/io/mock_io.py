from .base import GameIO

class MockIO(GameIO):
    """
    Implementazione di IO per test e debugging.
    Simula l'interfaccia IO senza effettivamente mostrare nulla a video.
    Utile per unit test e debugging automatizzato.
    """
    
    def __init__(self):
        super().__init__()
        self.output_buffer = []
        self.input_buffer = []
        self.input_index = 0
    
    def mostra_messaggio(self, testo: str):
        """Mostra un messaggio simulato"""
        self.output_buffer.append({"tipo": "messaggio", "testo": testo})
    
    def messaggio_sistema(self, testo: str):
        """Mostra un messaggio di sistema simulato"""
        self.output_buffer.append({"tipo": "sistema", "testo": testo})
    
    def messaggio_errore(self, testo: str):
        """Mostra un messaggio di errore simulato"""
        self.output_buffer.append({"tipo": "errore", "testo": testo})
    
    def richiedi_input(self, prompt: str = "") -> str:
        """
        Simula la richiesta di input restituendo il prossimo elemento nel buffer
        
        Args:
            prompt (str): Il prompt da mostrare (ignorato in MockIO)
        
        Returns:
            str: Il prossimo input simulato
        """
        # Se non ci sono input nel buffer, restituisci una stringa vuota
        if not self.input_buffer or self.input_index >= len(self.input_buffer):
            return ""
            
        # Restituisci il prossimo input e incrementa l'indice
        input_value = self.input_buffer[self.input_index]
        self.input_index += 1
        return input_value
    
    def add_input_sequence(self, sequence):
        """
        Aggiunge una sequenza di input al buffer
        
        Args:
            sequence (list): Lista di stringhe da usare come input
        """
        self.input_buffer.extend(sequence)
        
    def get_output_messages(self):
        """
        Restituisce tutti i messaggi nel buffer di output
        
        Returns:
            list: Lista di messaggi
        """
        return self.output_buffer
    
    def clear(self):
        """Pulisce il buffer dei messaggi"""
        self.output_buffer = []
    
    def mostra_transizione(self, testo):
        """Simula una transizione"""
        self.mostra_messaggio(testo)
    
    def mostra_notifica(self, testo):
        """Simula una notifica"""
        self.messaggio_sistema(testo)
    
    def mostra_dialogo(self, titolo, testo, opzioni=None):
        """
        Simula un dialogo
        
        Args:
            titolo (str): Titolo del dialogo
            testo (str): Testo del dialogo
            opzioni (list, optional): Opzioni di dialogo
            
        Returns:
            str: ID fittizio del dialogo
        """
        self.mostra_messaggio(f"{titolo}: {testo}")
        return "mock-dialog-id"
    
    def chiudi_dialogo(self, id_dialogo=None):
        """
        Simula la chiusura di un dialogo
        
        Args:
            id_dialogo (str, optional): ID del dialogo da chiudere
        """
        pass
    
    def get_output_structured(self):
        """
        Restituisce l'output strutturato
        
        Returns:
            list: Lista strutturata dei messaggi di output
        """
        return self.output_buffer 