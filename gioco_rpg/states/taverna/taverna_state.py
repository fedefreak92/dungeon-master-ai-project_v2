from states.base.enhanced_base_state import EnhancedBaseState
from .ui_handlers import TavernaUI
from .menu_handlers import MenuTavernaHandler
from .oggetti_interattivi import inizializza_oggetti_taverna
from .serializzazione import to_dict as serialize_to_dict, from_dict as deserialize_from_dict
from entities.npg import NPG
import logging
import core.events as Events

class TavernaState(EnhancedBaseState):
    """Classe che rappresenta lo stato della taverna"""
    
    def __init__(self, game=None):
        super().__init__()
        self.nome_stato = "taverna"
        self.ultima_scelta = None
        self.prima_visita = True
        self.fase = "menu_principale"
        self.ultimo_input = None
        self.dati_contestuali = {}
        self.menu_attivo = "menu_principale"  # Inizializza menu_attivo
        
        # Inizializza handler UI e menu
        self.ui_handler = TavernaUI(self)
        self.menu_handler = MenuTavernaHandler(self)
        
        # Carica gli NPC specifici della taverna
        self.npg_presenti = {
            "Durnan": NPG("Durnan"),
            "Elminster": NPG("Elminster"),
            "Mirt": NPG("Mirt")
        }
        self.nome_npg_attivo = None
        self.stato_conversazione = "inizio"
        self.stato_precedente = None
        
        # Inizializza oggetti interattivi
        self.oggetti_interattivi = inizializza_oggetti_taverna()
        
        # Attributo per tenere traccia della visualizzazione mappa
        self.mostra_mappa = False
        
        # Direzioni di movimento
        self.direzioni = {
            "nord": (0, -1),
            "sud": (0, 1),
            "est": (1, 0),
            "ovest": (-1, 0)
        }
        
        # Salva il riferimento al gioco per gli handler di eventi
        if game:
            self.set_game_context(game)
        
        # Inizializza menu e comandi
        self._init_commands()
        
        # Registra gli handler di eventi
        self._register_event_handlers()

    def _register_event_handlers(self):
        """Registra gli handler per eventi relativi alla taverna"""
        self.event_bus.on(Events.PLAYER_MOVE, self._handle_player_move)
        self.event_bus.on(Events.PLAYER_INTERACT, self._handle_player_interact)
        self.event_bus.on(Events.MENU_SELECTION, self._handle_menu_selection)
        self.event_bus.on(Events.MENU_CHANGED, self._handle_menu_changed)
        self.event_bus.on(Events.UI_DIALOG_OPEN, self._handle_dialog_open)
        self.event_bus.on(Events.UI_DIALOG_CLOSE, self._handle_dialog_close)
        self.event_bus.on("TAVERNA_DIALOGO_INIZIATO", self._handle_dialogo_iniziato)
        self.event_bus.on("TAVERNA_DIALOGO_TERMINATO", self._handle_dialogo_terminato)
        
    def _handle_player_move(self, direction, **kwargs):
        """Gestisce l'evento di movimento del giocatore"""
        gioco = self.gioco
        if not gioco:
            return
            
        # Logica di movimento specifica della taverna
        # Implementazione da spostare dal file movimento.py
        
    def _handle_player_interact(self, interaction_type=None, entity_id=None, **kwargs):
        """Gestisce l'evento di interazione del giocatore"""
        gioco = self.gioco
        if not gioco:
            return
            
        # Logica di interazione specifica della taverna
        # Implementazione da spostare dal file oggetti_interattivi.py
    
    def _handle_menu_selection(self, menu_id=None, selection=None, **kwargs):
        """Gestisce l'evento di selezione di un elemento del menu"""
        gioco = self.gioco
        if not gioco:
            return
            
        # Delega al menu handler
        if hasattr(self.menu_handler, f"gestisci_{selection}"):
            getattr(self.menu_handler, f"gestisci_{selection}")(gioco)
    
    def _handle_menu_changed(self, menu_id=None, **kwargs):
        """Gestisce l'evento di cambio menu"""
        gioco = self.gioco
        if not gioco:
            return
            
        self.menu_attivo = menu_id
        self.ui_aggiornata = False
    
    def _handle_dialog_open(self, dialog_id=None, **kwargs):
        """Gestisce l'evento di apertura dialogo"""
        gioco = self.gioco
        if not gioco:
            return
            
        # Logica per l'apertura di un dialogo
        
    def _handle_dialog_close(self, **kwargs):
        """Gestisce l'evento di chiusura dialogo"""
        gioco = self.gioco
        if not gioco:
            return
            
        # Logica per la chiusura di un dialogo
    
    def _handle_dialogo_iniziato(self, npg_id=None, **kwargs):
        """Gestisce l'evento di inizio dialogo con un NPG"""
        self.nome_npg_attivo = npg_id
        self.stato_conversazione = "inizio"
    
    def _handle_dialogo_terminato(self, **kwargs):
        """Gestisce l'evento di fine dialogo con un NPG"""
        self.nome_npg_attivo = None
        self.stato_conversazione = "inizio"

    def _init_commands(self):
        """Inizializza i comandi e le loro mappature per questo stato"""
        # Questo è un metodo temporaneo che può essere implementato completamente in futuro
        pass

    def esegui(self, gioco):
        """
        Implementazione dell'esecuzione dello stato.
        Mantenuta per retrocompatibilità.
        
        Args:
            gioco: L'istanza del gioco
        """
        # Salva il contesto di gioco
        self.set_game_context(gioco)
        
        if self.prima_visita:
            self.ui_handler.mostra_benvenuto(gioco)
            return
            
        if self.fase == "menu_principale" and self.menu_attivo != "menu_principale":
            self.menu_handler.mostra_menu_principale(gioco)
            
        # Gestisci la fase corrente
        elif self.fase != "menu_principale" and hasattr(self.menu_handler, f"gestisci_{self.fase}"):
            getattr(self.menu_handler, f"gestisci_{self.fase}")(gioco)
        
        # Aggiorna il renderer se necessario
        if not getattr(self, "ui_aggiornata", False):
            self.ui_handler.aggiorna_renderer(gioco)
            self.ui_aggiornata = True
            
        # Aggiungi chiamata a update per integrazione con EventBus
        self.update(0.033)  # Valore dt predefinito
    
    def update(self, dt):
        """
        Nuovo metodo di aggiornamento basato su EventBus.
        Sostituisce gradualmente esegui().
        
        Args:
            dt: Delta time, tempo trascorso dall'ultimo aggiornamento
        """
        # Ottieni il contesto di gioco
        gioco = self.gioco
        if not gioco:
            return
        
        # Logica di aggiornamento specifica dello stato
        if not getattr(self, "ui_aggiornata", False):
            self.ui_handler.aggiorna_renderer(gioco)
            self.ui_aggiornata = True
    
    def pausa(self, gioco=None):
        """
        Quando la taverna viene messa in pausa (es. durante un dialogo)
        mostriamo una notifica grafica
        """
        # Usa il nuovo sistema EventBus ma mantieni il comportamento originale
        super().pausa(gioco)
        
        # Se il gioco è fornito, salva il contesto
        if gioco:
            self.set_game_context(gioco)
        
        gioco = self.gioco
        if not gioco:
            return
            
        # Memorizza lo stato corrente
        self.stato_precedente = self.menu_attivo
        
        # Mostra un effetto di dissolvenza
        gioco.io.mostra_transizione("fade", 0.2)
        
        # Mostra un messaggio di notifica
        gioco.io.mostra_notifica({
            "text": "La taverna rimane in attesa...",
            "duration": 1.5,
            "type": "info"
        })
        
    def riprendi(self, gioco=None):
        """
        Quando la taverna riprende dopo una pausa
        mostriamo una notifica di ripresa
        """
        # Usa il nuovo sistema EventBus ma mantieni il comportamento originale
        super().riprendi(gioco)
        
        # Se il gioco è fornito, salva il contesto
        if gioco:
            self.set_game_context(gioco)
        
        gioco = self.gioco
        if not gioco:
            return
            
        # Mostra un effetto di dissolvenza
        gioco.io.mostra_transizione("fade", 0.2)
        
        # Mostra un messaggio di notifica
        gioco.io.mostra_notifica({
            "text": "Torni alla taverna...",
            "duration": 1.5,
            "type": "info"
        })
        
        # Ripristina il menu precedente o torna al menu principale
        if self.stato_precedente:
            self.menu_attivo = self.stato_precedente
            self.stato_precedente = None
        else:
            # Quando riprendiamo senza uno stato precedente, torniamo al menu principale
            self.fase = "menu_principale"
            self.menu_handler.mostra_menu_principale(gioco)
            
    # Metodi per serializzazione e persistenza
    def to_dict(self):
        """
        Converte lo stato della taverna in un dizionario per la serializzazione.
        
        Returns:
            dict: Rappresentazione dello stato in formato dizionario
        """
        # Utilizziamo il metodo di serializzazione dal modulo serializzazione.py
        return serialize_to_dict(self)
    
    @classmethod
    def from_dict(cls, data, game=None):
        """
        Crea un'istanza di TavernaState da un dizionario.
        
        Args:
            data (dict): Dizionario con i dati dello stato
            game: Istanza del gioco (opzionale)
            
        Returns:
            TavernaState: Nuova istanza di TavernaState
        """
        # Utilizziamo il metodo di deserializzazione dal modulo serializzazione.py
        return deserialize_from_dict(cls, data, game) 