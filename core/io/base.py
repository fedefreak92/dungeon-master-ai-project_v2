from abc import ABC, abstractmethod
import time
import uuid

class GameIO(ABC):
    """
    Interfaccia astratta base per la gestione di input/output del gioco.
    Definisce metodi comuni per tutte le implementazioni di I/O.
    """
    def __init__(self):
        self.event_queue = []  # Coda degli eventi da processare
        self.pending_events = []  # Eventi in attesa di essere inviati al client
        self.render_events = []  # Eventi di rendering in attesa
    
    @abstractmethod
    def mostra_messaggio(self, testo: str):
        """Mostra un messaggio narrativo del gioco attraverso l'interfaccia"""
        pass

    @abstractmethod
    def messaggio_sistema(self, testo: str):
        """Mostra un messaggio tecnico/di sistema attraverso l'interfaccia"""
        pass
        
    @abstractmethod
    def messaggio_errore(self, testo: str):
        """Mostra un messaggio di errore attraverso l'interfaccia"""
        pass

    def push_event(self, event_type: str, event_data: dict = None):
        """
        Aggiunge un evento alla coda eventi
        
        Args:
            event_type (str): Tipo di evento
            event_data (dict): Dati associati all'evento
        """
        event = {
            "id": str(uuid.uuid4()),
            "type": event_type,
            "data": event_data or {},
            "timestamp": time.time()
        }
        self.event_queue.append(event)
        
    def process_events(self):
        """
        Elabora gli eventi nella coda
        """
        # Implementazione di default vuota
        # Ogni classe derivata deve implementare la propria logica
        pass
        
    def get_pending_events(self):
        """
        Restituisce gli eventi in attesa e pulisce la coda
        
        Returns:
            list: Lista degli eventi pendenti
        """
        events = self.pending_events.copy()
        self.pending_events = []
        return events
    
    def push_render_event(self, event_type: str, event_data: dict = None):
        """
        Aggiunge un evento di rendering alla coda
        
        Args:
            event_type (str): Tipo di evento di rendering
            event_data (dict): Dati associati all'evento
        """
        event = {
            "id": str(uuid.uuid4()),
            "type": event_type,
            "data": event_data or {},
            "timestamp": time.time()
        }
        self.render_events.append(event)
        
    def get_render_events(self):
        """
        Restituisce tutti gli eventi di rendering in attesa
        
        Returns:
            list: Lista degli eventi di rendering
        """
        events = self.render_events.copy()
        self.render_events = []
        return events 