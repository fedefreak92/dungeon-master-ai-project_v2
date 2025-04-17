from states.base_state import BaseGameState
from .ui_handlers import TavernaUI
from .menu_handlers import MenuTavernaHandler
from .oggetti_interattivi import inizializza_oggetti_taverna
from entities.npg import NPG
import logging

class TavernaState(BaseGameState):
    """Classe che rappresenta lo stato della taverna"""
    
    def __init__(self, game):
        super().__init__(game)
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
        self.gioco = game
        
        # Implementa il metodo register_event_handler se non è già fornito dalla classe base
        if not hasattr(self, 'register_event_handler'):
            self.register_event_handler = self._register_event_handler
        
        # Inizializza menu e comandi
        self._init_commands()

    def _register_event_handler(self, event_name, handler):
        """
        Registra un handler per un evento specifico
        
        Args:
            event_name (str): Nome dell'evento
            handler (callable): Funzione da chiamare quando l'evento si verifica
        """
        if hasattr(self, 'gioco') and self.gioco is not None:
            if hasattr(self.gioco, 'io') and self.gioco.io is not None:
                self.gioco.io.register_event_handler(event_name, handler)
            else:
                logger = logging.getLogger(__name__)
                logger.warning(f"Impossibile registrare handler: self.gioco.io non è disponibile")
        else:
            logger = logging.getLogger(__name__)
            logger.warning(f"Impossibile registrare handler: self.gioco non è disponibile")
        
    def _init_commands(self):
        """Inizializza i comandi e le loro mappature per questo stato"""
        # Questo è un metodo temporaneo che può essere implementato completamente in futuro
        pass

    def esegui(self, gioco):
        # Memorizza il riferimento al gioco per gli handler di eventi
        self.gioco = gioco
        
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
    
    def pausa(self, gioco):
        """
        Quando la taverna viene messa in pausa (es. durante un dialogo)
        mostriamo una notifica grafica
        """
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
        
    def riprendi(self, gioco):
        """
        Quando la taverna riprende dopo una pausa
        mostriamo una notifica di ripresa
        """
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
        # Ottieni il dizionario base
        data = super().to_dict()
        
        # Rimuovi il dizionario npg_presenti prima, dato che verrà serializzato separatamente
        if "npg_presenti" in data:
            del data["npg_presenti"]
            
        # Serializza manualmente gli NPG per evitare problemi di serializzazione
        npg_dict = {}
        try:
            for nome, npg in self.npg_presenti.items():
                if hasattr(npg, 'to_dict') and callable(getattr(npg, 'to_dict')):
                    npg_dict[nome] = npg.to_dict()
        except:
            # In caso di errore, salviamo solo i nomi degli NPG
            npg_dict = {nome: {"nome": nome} for nome in self.npg_presenti.keys()}
            
        # Aggiungi attributi specifici
        data.update({
            "fase": self.fase,
            "ultimo_input": self.ultimo_input,
            "ultima_scelta": self.ultima_scelta,
            "npg_nomi": list(self.npg_presenti.keys())  # Salva solo i nomi degli NPG
            # Non serializzare oggetti_interattivi poiché sono generati dinamicamente
        })
        
        return data
    
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
        # Creiamo un oggetto senza chiamare __init__ per evitare l'errore del parametro mancante
        state = object.__new__(cls)
        
        # Inizializziamo manualmente gli attributi basilari
        state.nome_stato = "taverna"
        state.ultima_scelta = None
        state.prima_visita = False  # Non è la prima visita durante un caricamento
        state.fase = "menu_principale"
        state.ultimo_input = None
        state.dati_contestuali = {}
        state.gioco = game  # Importante: inizializza gioco invece di game
        state.menu_attivo = "menu_principale"  # Inizializza menu_attivo
        
        # Inizializza handler UI e menu
        state.ui_handler = TavernaUI(state)
        state.menu_handler = MenuTavernaHandler(state)
        
        # Ricrea gli NPG dai nomi
        state.npg_presenti = {}
        npg_nomi = data.get("npg_nomi", ["Durnan", "Elminster", "Mirt"])
        for nome in npg_nomi:
            from entities.npg import NPG
            state.npg_presenti[nome] = NPG(nome)
        
        # Inizializza gli oggetti interattivi vuoti (verranno caricati dal sistema JSON)
        state.oggetti_interattivi = {}
        
        # Carica altri attributi dal dizionario se presenti
        state.fase = data.get("fase", "menu_principale")
        state.ultimo_input = data.get("ultimo_input")
        state.ultima_scelta = data.get("ultima_scelta")
        state.nome_npg_attivo = None
        state.stato_conversazione = "inizio"
        state.stato_precedente = None
        state.mostra_mappa = False
        
        # Direzioni di movimento
        state.direzioni = {
            "nord": (0, -1),
            "sud": (0, 1),
            "est": (1, 0),
            "ovest": (-1, 0)
        }
        
        # Inizializza menu e comandi
        if hasattr(state, '_init_commands'):
            state._init_commands()
            
        # Implementa il metodo register_event_handler se non è già fornito
        if not hasattr(state, 'register_event_handler'):
            state.register_event_handler = state._register_event_handler
        
        return state
        
    def __getstate__(self):
        """
        Metodo speciale per la serializzazione con pickle.
        
        Returns:
            dict: Stato dell'oggetto serializzabile
        """
        state = self.__dict__.copy()
        # Rimuovi oggetti che non possono essere serializzati
        if 'gioco' in state:
            del state['gioco']
        if 'ui_handler' in state:
            del state['ui_handler']
        if 'menu_handler' in state:
            del state['menu_handler']
        if 'register_event_handler' in state and callable(state['register_event_handler']):
            del state['register_event_handler']
        # Tratta gli NPG in modo speciale
        state['npg_presenti'] = {k: v.__getstate__() if hasattr(v, '__getstate__') else {'nome': v.nome} for k, v in self.npg_presenti.items()}
        return state
        
    def __setstate__(self, state):
        """
        Metodo speciale per la deserializzazione con pickle.
        
        Args:
            state (dict): Stato dell'oggetto da deserializzare
        """
        # Ripristina lo stato
        self.__dict__.update(state)
        # Ricrea oggetti UI quando necessario
        from .ui_handlers import TavernaUI
        from .menu_handlers import MenuTavernaHandler
        self.ui_handler = TavernaUI(self)
        self.menu_handler = MenuTavernaHandler(self)
        # Ricrea gli NPG
        from entities.npg import NPG
        self.npg_presenti = {k: NPG.from_dict(v) if isinstance(v, dict) else NPG(v.get('nome', k)) for k, v in state.get('npg_presenti', {}).items()}
        
    def serialize(self):
        """
        Serializza lo stato per la trasmissione JSON.
        
        Returns:
            dict: Rappresentazione serializzabile dell'oggetto
        """
        return self.to_dict() 