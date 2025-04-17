from abc import ABC, abstractmethod
import time
import json
import uuid

# Interfaccia astratta per I/O del gioco orientata alla grafica
class GameIO(ABC):
    def __init__(self):
        self.event_queue = []  # Coda degli eventi da processare
        self.pending_events = []  # Eventi in attesa di essere inviati al client
        self.render_events = []  # Eventi di rendering in attesa
    
    @abstractmethod
    def mostra_messaggio(self, testo: str):
        """Mostra un messaggio narrativo del gioco attraverso l'interfaccia grafica"""
        pass

    @abstractmethod
    def messaggio_sistema(self, testo: str):
        """Mostra un messaggio tecnico/di sistema attraverso l'interfaccia grafica"""
        pass
        
    @abstractmethod
    def messaggio_errore(self, testo: str):
        """Mostra un messaggio di errore attraverso l'interfaccia grafica"""
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

# Implementazione per l'interfaccia grafica 2D
class GUI2DIO(GameIO):
    def __init__(self):
        super().__init__()
        self.buffer = []
        # Aggiungiamo stati e informazioni specifiche per la UI
        self.eventi_ui = []  # eventi per gestire azioni UI asincrone
        self.elementi_interattivi = {}  # tracciamento elementi cliccabili
        # Strutture dati per tenere traccia dello stato visuale
        self.mappa_visuale = {
            "celle": [],      # dati delle celle di mappa
            "entita": [],     # personaggi, NPC, oggetti
            "visibilita": []  # fog of war
        }
        self.ui_attiva = {
            "dialoghi": [],
            "menu_contestuale": None,
            "inventario_aperto": False,
            "tooltip": None
        }
        self.animazioni_attive = []
        # Eventi grafici in attesa
        self.eventi_grafici = []
        # Mappatura degli event handler
        self.event_handlers = {}
        
    def mostra_messaggio(self, testo: str):
        """
        Mostra un messaggio narrativo in UI grafica
        """
        self.buffer.append({"tipo": "narrativo", "testo": testo})
        # Genera anche un evento grafico
        self.push_graphic_event("message", {"text": testo, "type": "narrative"})
        
    def messaggio_sistema(self, testo: str):
        """Mostra un messaggio di sistema in UI grafica"""
        self.buffer.append({"tipo": "sistema", "testo": testo})
        # Genera anche un evento grafico
        self.push_graphic_event("message", {"text": testo, "type": "system"})
        
    def messaggio_errore(self, testo: str):
        """Mostra un messaggio di errore in UI grafica"""
        self.buffer.append({"tipo": "errore", "testo": testo})
        # Genera anche un evento grafico
        self.push_graphic_event("message", {"text": testo, "type": "error"})

    def get_output_structured(self) -> list:
        """Restituisce l'output strutturato come lista di dizionari"""
        return self.buffer
        
    def clear(self):
        """Pulisce il buffer dei messaggi"""
        self.buffer = []

    # Metodi specifici per l'interfaccia grafica 2D
    
    def aggiorna_mappa(self, dati_mappa: dict):
        """
        Aggiorna lo stato visuale della mappa
        
        Args:
            dati_mappa (dict): Dati completi sulla mappa da visualizzare
        """
        self.mappa_visuale = dati_mappa
        # Genera un evento grafico di aggiornamento mappa
        self.push_graphic_event("map_update", dati_mappa)
    
    def aggiungi_elemento_interattivo(self, id_elemento: str, tipo: str, posizione: tuple, 
                                     sprite: str, callbacks: dict = None):
        """
        Aggiunge un elemento interattivo alla UI
        
        Args:
            id_elemento (str): Identificativo unico dell'elemento
            tipo (str): Tipo di elemento (npc, oggetto, porta, ecc.)
            posizione (tuple): Posizione (x, y) sulla mappa
            sprite (str): Nome/path dello sprite da visualizzare
            callbacks (dict): Dizionario di funzioni callback per eventi
        """
        self.elementi_interattivi[id_elemento] = {
            "tipo": tipo,
            "posizione": posizione,
            "sprite": sprite,
            "callbacks": callbacks or {},
            "stato": "normale"  # normale, hover, selezionato, ecc.
        }
        # Genera un evento grafico di aggiunta elemento
        self.push_graphic_event("add_interactive_element", {
            "id": id_elemento,
            "type": tipo,
            "position": posizione,
            "sprite": sprite,
            "state": "normale"
        })
    
    def rimuovi_elemento_interattivo(self, id_elemento: str):
        """Rimuove un elemento interattivo dalla UI"""
        if id_elemento in self.elementi_interattivi:
            del self.elementi_interattivi[id_elemento]
            # Genera un evento grafico di rimozione elemento
            self.push_graphic_event("remove_interactive_element", {"id": id_elemento})
    
    def mostra_menu_contestuale(self, posizione: tuple, opzioni: list):
        """
        Mostra un menu contestuale in una posizione specifica
        
        Args:
            posizione (tuple): Posizione (x, y) del menu
            opzioni (list): Lista di opzioni disponibili
        """
        self.ui_attiva["menu_contestuale"] = {
            "posizione": posizione,
            "opzioni": opzioni
        }
        # Genera un evento grafico di visualizzazione menu
        self.push_graphic_event("show_context_menu", {
            "position": posizione,
            "options": opzioni
        })
    
    def nascondi_menu_contestuale(self):
        """Nasconde il menu contestuale"""
        self.ui_attiva["menu_contestuale"] = None
        # Genera un evento grafico di nascondimento menu
        self.push_graphic_event("hide_context_menu", {})
    
    def mostra_inventario(self, items: list, capacity: int):
        """
        Mostra l'inventario del giocatore
        
        Args:
            items (list): Lista degli oggetti nell'inventario
            capacity (int): Capacità massima dell'inventario
        """
        self.ui_attiva["inventario_aperto"] = True
        # Genera un evento grafico per visualizzare l'inventario
        self.push_graphic_event("show_inventory", {
            "items": items,
            "capacity": capacity
        })
    
    def nascondi_inventario(self):
        """Nasconde l'inventario"""
        self.ui_attiva["inventario_aperto"] = False
        # Genera un evento grafico per nascondere l'inventario
        self.push_graphic_event("hide_inventory", {})
    
    def mostra_dialogo(self, titolo: str, testo: str, opzioni: list = None):
        """
        Mostra una finestra di dialogo
        
        Args:
            titolo (str): Titolo della finestra di dialogo
            testo (str): Contenuto del dialogo
            opzioni (list): Opzioni di risposta disponibili
            
        Returns:
            str: ID del dialogo creato
        """
        id_dialogo = str(uuid.uuid4())
        dialogo = {
            "id": id_dialogo,
            "titolo": titolo,
            "testo": testo,
            "opzioni": opzioni or []
        }
        self.ui_attiva["dialoghi"].append(dialogo)
        # Genera un evento grafico per visualizzare il dialogo
        self.push_graphic_event("show_dialog", {
            "id": id_dialogo,
            "title": titolo,
            "text": testo,
            "options": opzioni or []
        })
        return id_dialogo
    
    def chiudi_dialogo(self, id_dialogo: str = None):
        """
        Chiude una finestra di dialogo
        
        Args:
            id_dialogo (str, optional): ID del dialogo da chiudere.
                                      Se None, chiude l'ultimo dialogo aperto.
        """
        if not self.ui_attiva["dialoghi"]:
            return
            
        if id_dialogo is None:
            # Rimuovi l'ultimo dialogo
            dialogo = self.ui_attiva["dialoghi"].pop()
            id_dialogo = dialogo["id"]
        else:
            # Rimuovi il dialogo specifico
            self.ui_attiva["dialoghi"] = [d for d in self.ui_attiva["dialoghi"] 
                                         if d["id"] != id_dialogo]
                                         
        # Genera un evento grafico per chiudere il dialogo
        self.push_graphic_event("close_dialog", {"id": id_dialogo})
    
    def aggiungi_animazione(self, tipo: str, target: str, durata: float, 
                          parametri: dict = None):
        """
        Aggiunge un'animazione alla UI
        
        Args:
            tipo (str): Tipo di animazione (movimento, rotazione, fade, ecc.)
            target (str): ID dell'elemento target dell'animazione
            durata (float): Durata dell'animazione in secondi
            parametri (dict): Parametri specifici dell'animazione
            
        Returns:
            str: ID dell'animazione creata
        """
        id_animazione = str(uuid.uuid4())
        animazione = {
            "id": id_animazione,
            "tipo": tipo,
            "target": target,
            "durata": durata,
            "parametri": parametri or {},
            "inizio": time.time(),
            "stato": "attiva"
        }
        self.animazioni_attive.append(animazione)
        # Genera un evento grafico per avviare l'animazione
        self.push_graphic_event("start_animation", {
            "id": id_animazione,
            "type": tipo,
            "target": target,
            "duration": durata,
            "parameters": parametri or {}
        })
        return id_animazione
    
    def mostra_tooltip(self, testo: str, posizione: tuple, durata: float = None):
        """
        Mostra un tooltip
        
        Args:
            testo (str): Testo del tooltip
            posizione (tuple): Posizione (x, y) del tooltip
            durata (float, optional): Durata in secondi, se None rimane fino a nascondi_tooltip
            
        Returns:
            str: ID del tooltip creato
        """
        id_tooltip = str(uuid.uuid4())
        self.ui_attiva["tooltip"] = {
            "id": id_tooltip,
            "testo": testo,
            "posizione": posizione,
            "creato": time.time(),
            "durata": durata
        }
        # Genera un evento grafico per visualizzare il tooltip
        self.push_graphic_event("show_tooltip", {
            "id": id_tooltip,
            "text": testo,
            "position": posizione,
            "duration": durata
        })
        return id_tooltip
    
    def nascondi_tooltip(self):
        """Nasconde il tooltip attivo"""
        if not self.ui_attiva["tooltip"]:
            return
            
        id_tooltip = self.ui_attiva["tooltip"]["id"]
        self.ui_attiva["tooltip"] = None
        # Genera un evento grafico per nascondere il tooltip
        self.push_graphic_event("hide_tooltip", {"id": id_tooltip})
    
    def gestisci_evento_input(self, tipo_evento: str, target: str = None, 
                            dati_evento: dict = None) -> str:
        """
        Gestisce un evento di input dall'utente
        
        Args:
            tipo_evento (str): Tipo di evento (click, hover, key_press, ecc.)
            target (str, optional): ID dell'elemento target dell'evento
            dati_evento (dict, optional): Dati aggiuntivi dell'evento
            
        Returns:
            str: Risposta o azione risultante dall'evento
        """
        dati_evento = dati_evento or {}
        risposta = None
        
        # Gestione eventi in base al tipo
        if tipo_evento == "click":
            # Se c'è un menu contestuale attivo
            if self.ui_attiva["menu_contestuale"]:
                indice_opzione = dati_evento.get("indice_opzione")
                if indice_opzione is not None:
                    opzioni = self.ui_attiva["menu_contestuale"]["opzioni"]
                    if 0 <= indice_opzione < len(opzioni):
                        risposta = opzioni[indice_opzione]
                self.nascondi_menu_contestuale()
                
            # Se c'è un dialogo attivo
            elif self.ui_attiva["dialoghi"]:
                indice_opzione = dati_evento.get("indice_opzione")
                if indice_opzione is not None:
                    dialogo = self.ui_attiva["dialoghi"][-1]
                    opzioni = dialogo["opzioni"]
                    if 0 <= indice_opzione < len(opzioni):
                        risposta = opzioni[indice_opzione]
                        self.chiudi_dialogo(dialogo["id"])
                        
            # Click su un elemento interattivo
            elif target in self.elementi_interattivi:
                elemento = self.elementi_interattivi[target]
                callback_click = elemento["callbacks"].get("click")
                if callback_click:
                    risposta = callback_click(target, dati_evento)
                    
        elif tipo_evento == "hover":
            # Hover su un elemento interattivo
            if target in self.elementi_interattivi:
                elemento = self.elementi_interattivi[target]
                callback_hover = elemento["callbacks"].get("hover")
                if callback_hover:
                    risposta = callback_hover(target, dati_evento)
                    
                # Aggiorna lo stato visivo dell'elemento
                if elemento["stato"] != "hover":
                    elemento["stato"] = "hover"
                    self.push_graphic_event("update_element_state", {
                        "id": target,
                        "state": "hover"
                    })
                    
        elif tipo_evento == "key_press":
            # Gestione input da tastiera
            # Può essere usato per movimenti, scorciatoie, ecc.
            tasto = dati_evento.get("key")
            if tasto:
                # In un'implementazione completa, qui gestiresti 
                # diversi tasti e funzionalità
                risposta = {"tipo": "key_press", "key": tasto}
        
        # Mantieni traccia dell'evento UI
        self.eventi_ui.append({
            "tipo": tipo_evento,
            "target": target,
            "dati": dati_evento,
            "timestamp": time.time(),
            "risposta": risposta
        })
        
        # Se ci sono handler registrati per questo tipo di evento, chiamali
        if tipo_evento in self.event_handlers:
            for handler in self.event_handlers[tipo_evento]:
                handler_result = handler(tipo_evento, target, dati_evento)
                if handler_result is not None:
                    risposta = handler_result
        
        return risposta
    
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
    
    def process_events(self):
        """
        Elabora gli eventi nella coda
        
        In un'implementazione reale, qui gestiresti eventi provenienti
        da un'interfaccia UI reale (clic del mouse, pressioni tasti, ecc.)
        e li tradurresti in azioni di gioco.
        """
        # Ciclo delle animazioni attive per verificare se sono terminate
        current_time = time.time()
        for anim in self.animazioni_attive[:]:
            if anim["stato"] == "attiva" and current_time >= anim["inizio"] + anim["durata"]:
                anim["stato"] = "completata"
                self.push_graphic_event("animation_complete", {"id": anim["id"]})
                self.animazioni_attive.remove(anim)
        
        # Verifica se un tooltip con durata è scaduto
        if self.ui_attiva["tooltip"] and self.ui_attiva["tooltip"]["durata"]:
            tooltip = self.ui_attiva["tooltip"]
            if current_time >= tooltip["creato"] + tooltip["durata"]:
                self.nascondi_tooltip()
    
    def push_graphic_event(self, event_type, event_data):
        """
        Aggiunge un evento grafico alla coda eventi
        
        Args:
            event_type (str): Tipo di evento grafico
            event_data (dict): Dati dell'evento
        """
        event = {
            "id": str(uuid.uuid4()),
            "type": event_type,
            "data": event_data,
            "timestamp": time.time()
        }
        self.eventi_grafici.append(event)
        self.pending_events.append(event)  # Aggiungi anche alla coda eventi generali
    
    def get_stato_ui(self) -> dict:
        """
        Restituisce lo stato attuale dell'interfaccia
        
        Returns:
            dict: Stato completo dell'interfaccia
        """
        return {
            "elementi_interattivi": self.elementi_interattivi,
            "mappa_visuale": self.mappa_visuale,
            "ui_attiva": self.ui_attiva,
            "animazioni_attive": self.animazioni_attive,
            "buffer_messaggi": self.buffer
        }

class MockIO(GameIO):
    """Implementazione di IO per test e debugging"""
    
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
        """Simula un dialogo"""
        self.mostra_messaggio(f"{titolo}: {testo}")
    
    def chiudi_dialogo(self, id_dialogo=None):
        """Simula la chiusura di un dialogo"""
        pass
    
    def get_output_structured(self):
        """Restituisce l'output strutturato"""
        return self.output_buffer

# Classe adattatore per interfaccia IO
class IOInterface(GameIO):
    """
    Classe adattatore che incapsula l'interfaccia IO per la sessione.
    Estende GameIO per mantenere la compatibilità con il sistema.
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