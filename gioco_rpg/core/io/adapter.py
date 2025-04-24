import time
import uuid
from .base import GameIO

class IOInterface(GameIO):
    """
    Classe adattatore che incapsula l'interfaccia IO per la sessione.
    Estende GameIO per mantenere la compatibilità con il sistema
    e permette di inoltrare gli eventi alla sessione di gioco.
    """
    
    def __init__(self, sessione=None):
        """
        Inizializza l'interfaccia IO con riferimento alla sessione
        
        Args:
            sessione: Sessione di gioco associata
        """
        super().__init__()
        self.sessione = sessione
        self.buffer_messaggi = []
        self.eventi_ui = []
        self.event_handlers = {}
        self.buffer = []  # Per compatibilità con altre implementazioni IO
        
    def mostra_messaggio(self, testo: str):
        """
        Mostra un messaggio narrativo
        
        Args:
            testo (str): Testo del messaggio
        """
        self.buffer_messaggi.append({"tipo": "narrativo", "testo": testo})
        self.buffer.append({"tipo": "narrativo", "testo": testo})
        self.push_event("messaggio", {"testo": testo, "tipo": "narrativo"})
        
    def messaggio_sistema(self, testo: str):
        """
        Mostra un messaggio di sistema
        
        Args:
            testo (str): Testo del messaggio
        """
        self.buffer_messaggi.append({"tipo": "sistema", "testo": testo})
        self.buffer.append({"tipo": "sistema", "testo": testo})
        self.push_event("messaggio", {"testo": testo, "tipo": "sistema"})
        
    def messaggio_errore(self, testo: str):
        """
        Mostra un messaggio di errore
        
        Args:
            testo (str): Testo del messaggio
        """
        self.buffer_messaggi.append({"tipo": "errore", "testo": testo})
        self.buffer.append({"tipo": "errore", "testo": testo})
        self.push_event("messaggio", {"testo": testo, "tipo": "errore"})
    
    def invia_evento_ui(self, tipo_evento: str, dati: dict = None):
        """
        Invia un evento UI alla sessione
        
        Args:
            tipo_evento (str): Tipo di evento
            dati (dict): Dati dell'evento
        """
        evento = {
            "tipo": tipo_evento,
            "dati": dati or {},
            "timestamp": time.time()
        }
        self.eventi_ui.append(evento)
        self.push_event("ui_evento", evento)
    
    def get_buffer_messaggi(self):
        """
        Restituisce il buffer dei messaggi
        
        Returns:
            list: Lista dei messaggi
        """
        return self.buffer_messaggi
        
    def clear_buffer(self):
        """Pulisce il buffer dei messaggi"""
        self.buffer_messaggi = []
        self.buffer = []
        
    def get_output_structured(self):
        """Restituisce l'output strutturato"""
        return self.buffer
        
    def clear(self):
        """Pulisce il buffer dei messaggi"""
        self.buffer = []
        self.buffer_messaggi = []
        
    def process_events(self):
        """
        Elabora gli eventi nella coda
        """
        # Implementazione base per elaborare gli eventi
        # Nelle classi derivate può essere sovrascritto con logica più complessa
        pass
    
    def mostra_dialogo(self, titolo, testo, opzioni=None):
        """
        Mostra un dialogo
        
        Args:
            titolo (str): Titolo del dialogo
            testo (str): Testo del dialogo
            opzioni (list, optional): Opzioni del dialogo
            
        Returns:
            str: ID del dialogo
        """
        id_dialogo = str(uuid.uuid4())
        dialogo = {
            "id": id_dialogo,
            "titolo": titolo,
            "testo": testo,
            "opzioni": opzioni or []
        }
        self.buffer.append({"tipo": "dialogo", "contenuto": dialogo})
        self.push_event("dialogo", dialogo)
        return id_dialogo
        
    def chiudi_dialogo(self, id_dialogo=None):
        """
        Chiude un dialogo
        
        Args:
            id_dialogo (str, optional): ID del dialogo da chiudere
        """
        # Implementazione semplice
        self.push_event("chiudi_dialogo", {"id": id_dialogo})
        
    def mostra_notifica(self, testo):
        """
        Mostra una notifica
        
        Args:
            testo (str): Testo della notifica
        """
        self.messaggio_sistema(testo)
        
    def mostra_transizione(self, testo):
        """
        Mostra una transizione
        
        Args:
            testo (str): Testo della transizione
        """
        self.mostra_messaggio(testo)
        
    def push_graphic_event(self, event_type, event_data):
        """
        Aggiunge un evento grafico alla coda eventi
        
        Args:
            event_type (str): Tipo di evento grafico
            event_data (dict): Dati dell'evento
        """
        # Reindirizza al metodo push_event standard
        self.push_event(event_type, event_data)
        
    def aggiorna_mappa(self, dati_mappa):
        """
        Aggiorna lo stato visuale della mappa
        
        Args:
            dati_mappa (dict): Dati completi sulla mappa da visualizzare
        """
        self.push_event("map_update", dati_mappa)
        
    def mostra_menu_contestuale(self, posizione, opzioni):
        """
        Mostra un menu contestuale
        
        Args:
            posizione (tuple): Posizione (x, y) del menu
            opzioni (list): Lista di opzioni disponibili
        """
        self.push_event("menu_contestuale", {
            "posizione": posizione,
            "opzioni": opzioni
        })
        
    def nascondi_menu_contestuale(self):
        """Nasconde il menu contestuale"""
        self.push_event("nascondi_menu_contestuale", {})
        
    def mostra_inventario(self, items, capacity):
        """
        Mostra l'inventario
        
        Args:
            items (list): Lista degli oggetti nell'inventario
            capacity (int): Capacità massima dell'inventario
        """
        self.push_event("mostra_inventario", {
            "items": items,
            "capacity": capacity
        })
        
    def nascondi_inventario(self):
        """Nasconde l'inventario"""
        self.push_event("nascondi_inventario", {})
        
    def register_event_handler(self, event_type, handler):
        """
        Registra un handler per un tipo di evento
        
        Args:
            event_type (str): Tipo di evento
            handler (callable): Funzione che gestisce l'evento
            
        Returns:
            bool: True se la registrazione è avvenuta correttamente
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
            
        if handler not in self.event_handlers[event_type]:
            self.event_handlers[event_type].append(handler)
            return True
            
        return False
    
    def unregister_event_handler(self, event_type, handler):
        """
        Rimuove un handler per un tipo di evento
        
        Args:
            event_type (str): Tipo di evento
            handler (callable): Funzione che gestisce l'evento
            
        Returns:
            bool: True se la rimozione è avvenuta correttamente
        """
        if event_type in self.event_handlers and handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)
            if not self.event_handlers[event_type]:
                del self.event_handlers[event_type]
            return True
            
        return False 