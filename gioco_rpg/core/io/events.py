import time
import uuid

class EventManager:
    """
    Gestore centralizzato degli eventi di I/O.
    Gestisce code di eventi, dispatching e priorità.
    """
    
    def __init__(self):
        self.event_queue = []  # Coda principale degli eventi
        self.pending_events = []  # Eventi in attesa di invio al client
        self.render_events = []  # Eventi di rendering specifici
        self.event_handlers = {}  # Handler registrati per tipo evento
        self.event_history = []  # Storico eventi per debugging
        self.max_history_size = 1000  # Massimo numero di eventi nello storico
    
    def create_event(self, event_type, event_data=None, priority=0):
        """
        Crea un nuovo evento con un ID univoco
        
        Args:
            event_type (str): Tipo di evento
            event_data (dict): Dati associati all'evento
            priority (int): Priorità dell'evento (maggiore = più prioritario)
            
        Returns:
            dict: Evento creato
        """
        event = {
            "id": str(uuid.uuid4()),
            "type": event_type,
            "data": event_data or {},
            "timestamp": time.time(),
            "priority": priority,
            "processed": False
        }
        return event
    
    def push_event(self, event_type, event_data=None, priority=0):
        """
        Aggiunge un evento alla coda
        
        Args:
            event_type (str): Tipo di evento
            event_data (dict): Dati associati all'evento
            priority (int): Priorità dell'evento (maggiore = più prioritario)
            
        Returns:
            str: ID dell'evento creato
        """
        event = self.create_event(event_type, event_data, priority)
        self.event_queue.append(event)
        
        # Mantieni lo storico entro i limiti
        self.event_history.append(event)
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size:]
            
        return event["id"]
    
    def push_render_event(self, event_type, event_data=None):
        """
        Aggiunge un evento di rendering alla coda specifica
        
        Args:
            event_type (str): Tipo di evento di rendering
            event_data (dict): Dati associati all'evento
            
        Returns:
            str: ID dell'evento creato
        """
        event = self.create_event(event_type, event_data)
        self.render_events.append(event)
        return event["id"]
    
    def get_pending_events(self):
        """
        Restituisce gli eventi in attesa e pulisce la coda
        
        Returns:
            list: Lista degli eventi pendenti
        """
        events = self.pending_events.copy()
        self.pending_events = []
        return events
    
    def get_render_events(self):
        """
        Restituisce tutti gli eventi di rendering in attesa
        
        Returns:
            list: Lista degli eventi di rendering
        """
        events = self.render_events.copy()
        self.render_events = []
        return events
    
    def register_handler(self, event_type, handler_func):
        """
        Registra un handler per un tipo di evento
        
        Args:
            event_type (str): Tipo di evento
            handler_func (callable): Funzione che gestisce l'evento
            
        Returns:
            bool: True se la registrazione è avvenuta correttamente
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
            
        if handler_func not in self.event_handlers[event_type]:
            self.event_handlers[event_type].append(handler_func)
            return True
            
        return False
    
    def unregister_handler(self, event_type, handler_func):
        """
        Rimuove un handler per un tipo di evento
        
        Args:
            event_type (str): Tipo di evento
            handler_func (callable): Funzione che gestisce l'evento
            
        Returns:
            bool: True se la rimozione è avvenuta correttamente
        """
        if event_type in self.event_handlers and handler_func in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler_func)
            if not self.event_handlers[event_type]:
                del self.event_handlers[event_type]
            return True
            
        return False
    
    def process_events(self, max_events=None):
        """
        Elabora gli eventi nella coda, invocando gli handler registrati
        
        Args:
            max_events (int, optional): Numero massimo di eventi da processare
                                      Se None, processa tutti gli eventi in coda
            
        Returns:
            int: Numero di eventi elaborati
        """
        # Ordina gli eventi per priorità (decrescente) e timestamp (crescente)
        sorted_events = sorted(
            self.event_queue,
            key=lambda e: (-e["priority"], e["timestamp"])
        )
        
        # Limita il numero di eventi da processare se specificato
        if max_events:
            events_to_process = sorted_events[:max_events]
        else:
            events_to_process = sorted_events
            
        processed_count = 0
        
        for event in events_to_process:
            # Rimuovi l'evento dalla coda
            self.event_queue.remove(event)
            
            # Se ci sono handler registrati per questo tipo di evento, chiamali
            event_type = event["type"]
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    try:
                        handler(event)
                    except Exception as e:
                        # In un sistema reale, qui andresti a loggare l'errore
                        print(f"Errore nell'handler {handler} per evento {event_type}: {e}")
            
            # Marca l'evento come elaborato nello storico
            event["processed"] = True
            processed_count += 1
            
            # Aggiungi alla coda degli eventi pendenti
            self.pending_events.append(event)
            
        return processed_count
    
    def clear_events(self):
        """
        Pulisce tutte le code degli eventi
        
        Returns:
            int: Numero totale di eventi cancellati
        """
        total_count = len(self.event_queue) + len(self.pending_events) + len(self.render_events)
        self.event_queue = []
        self.pending_events = []
        self.render_events = []
        return total_count
    
    def get_event_stats(self):
        """
        Restituisce statistiche sugli eventi
        
        Returns:
            dict: Statistiche sugli eventi
        """
        event_types = {}
        for event in self.event_history:
            event_type = event["type"]
            if event_type not in event_types:
                event_types[event_type] = 0
            event_types[event_type] += 1
            
        return {
            "queue_size": len(self.event_queue),
            "pending_size": len(self.pending_events),
            "render_size": len(self.render_events),
            "history_size": len(self.event_history),
            "event_types": event_types
        } 