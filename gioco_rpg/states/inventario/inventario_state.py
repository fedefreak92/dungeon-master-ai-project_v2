from states.base_state import BaseGameState
from states.inventario.ui_handlers import UIInventarioHandler
from states.inventario.menu_handlers import MenuInventarioHandler
from states.inventario.oggetti import GestoreOggetti
from util.funzioni_utili import avanti

class GestioneInventarioState(BaseGameState):
    """
    Stato di gestione dell'inventario del giocatore.
    Permette di visualizzare, usare, equipaggiare e esaminare gli oggetti.
    """
    
    def __init__(self, stato_precedente=None, gioco=None):
        """
        Inizializza lo stato di gestione inventario.
        
        Args:
            stato_precedente: Lo stato da cui si proviene
            gioco: L'istanza del gioco (opzionale)
        """
        # Inizializzazione sottosistemi
        self.ui_handler = UIInventarioHandler(self)
        self.menu_handler = MenuInventarioHandler(self)
        self.gestore_oggetti = GestoreOggetti(self)
        
        super().__init__(gioco)
        self.stato_precedente = stato_precedente
        self.fase = "menu_principale"  # Fase iniziale
        self.ultimo_input = None
        self.ui_aggiornata = False
    
    def _init_commands(self):
        """Inizializza i comandi disponibili per questo stato"""
        self.commands = {
            "usa_oggetto": self.gestore_oggetti.usa_oggetto_selezionato,
            "equipaggia_oggetto": self.gestore_oggetti.equipaggia_oggetto_selezionato,
            "rimuovi_equipaggiamento": self.gestore_oggetti.rimuovi_equipaggiamento_selezionato,
            "esamina_oggetto": self.gestore_oggetti.esamina_oggetto_selezionato,
            "torna_indietro": self.menu_handler.torna_indietro
        }
    
    def esegui(self, gioco):
        """
        Implementazione dell'esecuzione dello stato di gestione inventario.
        
        Args:
            gioco: L'istanza del gioco
        """
        # Salva il contesto di gioco
        self.set_game_context(gioco)
        
        # Gestione di inventario vuoto
        if self.fase == "menu_principale" and not gioco.giocatore.inventario:
            if not self.ui_aggiornata:
                gioco.io.mostra_messaggio("Il tuo inventario è vuoto.")
                gioco.io.mostra_dialogo("Inventario Vuoto", "Non hai oggetti nel tuo inventario.", ["Torna Indietro"])
                self.ui_aggiornata = True
            return
        
        # Aggiorna il renderer grafico se necessario
        if not self.ui_aggiornata:
            self.ui_handler.aggiorna_renderer(gioco)
            self.ui_aggiornata = True
            
            # Mostra interfaccia inventario in base alla fase corrente
        if self.fase == "menu_principale":
            self.ui_handler.mostra_menu_principale(gioco)
        elif self.fase == "usa_oggetto":
            self.ui_handler.mostra_usa_oggetto(gioco)
        elif self.fase == "equipaggia_oggetto":
            self.ui_handler.mostra_equipaggia_oggetto(gioco)
        elif self.fase == "rimuovi_equipaggiamento":
            self.ui_handler.mostra_rimuovi_equipaggiamento(gioco)
        elif self.fase == "esamina_oggetto":
            self.ui_handler.mostra_esamina_oggetto(gioco)
        
        # Processa gli eventi UI - questo sostituisce l'input testuale
        super().esegui(gioco)
        
    # Alias per compatibilità con i test
    def aggiorna(self, gioco):
        """Alias di esegui per compatibilità con i test"""
        return self.esegui(gioco)
    
    def _register_ui_handlers(self, io_handler):
        """
        Registra i gestori di eventi dell'interfaccia utente.
        
        Args:
            io_handler: L'handler IO del gioco
        """
        self.ui_handler.register_ui_handlers(io_handler)
        
    def _unregister_ui_handlers(self, io_handler):
        """
        Deregistra i gestori di eventi dell'interfaccia utente.
        
        Args:
            io_handler: L'handler IO del gioco
        """
        self.ui_handler.unregister_ui_handlers(io_handler)
        
    def _handle_dialog_choice(self, event):
        """
        Gestisce le scelte dai dialoghi.
        
        Args:
            event: Evento di scelta da dialogo
            
        Returns:
            bool: True se l'evento è stato gestito, False altrimenti
        """
        return self.menu_handler.handle_dialog_choice(event)
    
    def entra(self, gioco=None):
        """
        Metodo chiamato quando si entra nello stato.
        
        Args:
            gioco: L'istanza del gioco
        """
        super().entra(gioco)
        self.ui_aggiornata = False
        
        # Registra i gestori UI
        if gioco:
            self._register_ui_handlers(gioco.io)
            
    def esci(self, gioco=None):
        """
        Metodo chiamato quando si esce dallo stato.
        
        Args:
            gioco: L'istanza del gioco
        """
        # Deregistra i gestori UI
        if gioco:
            self._unregister_ui_handlers(gioco.io)
            
        super().esci(gioco)
        
    def riprendi(self, gioco=None):
        """
        Metodo chiamato quando lo stato torna ad essere attivo
        dopo essere stato in pausa.
        
        Args:
            gioco: L'istanza del gioco
        """
        super().riprendi(gioco)
        self.ui_aggiornata = False
        
        # Registra i gestori UI
        if gioco:
            self._register_ui_handlers(gioco.io)
            
    def pausa(self, gioco=None):
        """
        Metodo chiamato quando lo stato viene temporaneamente sospeso.
        
        Args:
            gioco: L'istanza del gioco
        """
        # Deregistra i gestori UI
        if gioco:
            self._unregister_ui_handlers(gioco.io)
            
        super().pausa(gioco)
    
    def to_dict(self):
        """
        Converte lo stato in un dizionario per la serializzazione.
        
        Returns:
            dict: Rappresentazione dello stato in formato dizionario
        """
        # Ottieni il dizionario base
        data = super().to_dict()
        
        # Aggiungi attributi specifici
        data.update({
            "fase": self.fase,
            "ultimo_input": self.ultimo_input,
            "ui_aggiornata": self.ui_aggiornata
        })
        
        # Se stato_precedente è un oggetto stato con to_dict() lo serializziamo
        if self.stato_precedente and hasattr(self.stato_precedente, 'to_dict'):
            data["stato_precedente"] = self.stato_precedente.to_dict()
        elif self.stato_precedente and hasattr(self.stato_precedente, '__class__'):
            # Altrimenti salviamo solo il tipo
            data["stato_precedente_tipo"] = self.stato_precedente.__class__.__name__
            
        return data

    @classmethod
    def from_dict(cls, data, game=None):
        """
        Crea un'istanza di GestioneInventarioState da un dizionario.
        
        Args:
            data (dict): Dizionario con i dati dello stato
            game: L'istanza del gioco (opzionale)
            
        Returns:
            GestioneInventarioState: Nuova istanza dello stato
        """
        state = cls(gioco=game)
        
        # Ripristina attributi
        state.fase = data.get("fase", "menu_principale")
        state.ultimo_input = data.get("ultimo_input")
        state.ui_aggiornata = data.get("ui_aggiornata", False)
        
        # Nota: stato_precedente verrà gestito dal chiamante
        # perché potrebbe richiedere riferimenti all'intero stack di stati
        
        return state 