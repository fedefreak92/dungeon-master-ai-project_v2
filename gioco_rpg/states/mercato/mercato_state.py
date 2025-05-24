from ..mappa.mappa_state import MappaState
from entities.giocatore import Giocatore
from states.inventario import GestioneInventarioState
from util.funzioni_utili import avanti
import logging
# AGGIUNTO IMPORT PER ITEMFACTORY
from items.item_factory import ItemFactory

# Import moduli specifici del mercato (RIMOSSI - Gestiti da MappaState o caricati dinamicamente)
# from states.mercato.oggetti_interattivi import crea_tutti_oggetti_interattivi 
# from states.mercato.menu_handlers import MenuMercatoHandler
# from states.mercato.ui_handlers import UIMercatoHandler
# from states.mercato.movimento import MovimentoMercatoHandler
# from states.mercato.dialogo import DialogoMercatoHandler

logger = logging.getLogger(__name__) # AGGIUNTO logger

class MercatoState(MappaState):
    """Classe che rappresenta lo stato del mercato.
    Ora è una specializzazione leggera di MappaState (LuogoState).
    """
    
    def __init__(self, game=None):
        """
        Inizializza lo stato del mercato.
        Chiama il costruttore della classe base MappaState.
        
        Args:
            game: L'istanza del gioco (opzionale, per contesto iniziale)
        """
        # MODIFICA: Passare game_state_manager se disponibile da 'game'
        gsm = game.game_state_manager if game and hasattr(game, 'game_state_manager') else None
        super().__init__(nome_luogo="mercato", game_state_manager=gsm) # Chiamata corretta a MappaState.__init__
        
        # RIMOZIONE ATTRIBUTI DUPLICATI (ora in MappaState)
        # self.fase_luogo = "menu_principale" 
        # self.ultimo_input = None
        # self.dati_contestuali_luogo = {}  
        # self.ui_aggiornata = False
        # self.menu_attivo = "principale"
        # self.oggetto_selezionato = None # Gestire localmente se serve ancora per logica specifica es. vendita
        # self.npg_selezionato = None # Gestire localmente se serve ancora
        # self.mostra_mappa = False # Ora è in MappaState
        
        # RIMOZIONE CARICAMENTO OGGETTI (ora in MappaState._carica_dati_luogo)
        # self.oggetti_interattivi = crea_tutti_oggetti_interattivi()
        
        # RIMOZIONE INIZIALIZZAZIONE HANDLER (ora in MappaState._init_handlers)
        # self.menu_handler = MenuMercatoHandler(self)
        # self.ui_handler = UIMercatoHandler(self)
        # self.movimento_handler = MovimentoMercatoHandler(self)
        # self.dialogo_handler = DialogoMercatoHandler(self)

        # Potrebbe essere necessario mantenere alcuni attributi di stato specifici del mercato?
        self.oggetto_selezionato_per_vendita = None # Esempio attributo specifico

        if game: # game qui è l'intera istanza GameManager, non solo game_state_manager
            self.set_game_context(game) # set_game_context è in EnhancedBaseState
    
    # RIMOSSO: def esegui(self, gioco): 
    # La logica principale è ora in MappaState.update() o gestita da eventi.
    # La logica specifica delle fasi (compra_pozione, vendi_oggetto_lista) dovrà 
    # essere attivata dai menu handler specifici (se caricati) o dalla logica 
    # in _handle_azione_specifica_luogo.

    # RIMOSSO: def _visualizza_mappa(self, gioco):
    # La logica di visualizzazione mappa dovrebbe essere gestita dall'UI handler.

    # RIMOSSO: def _init_commands(self):
    # I comandi sono inizializzati in MappaState e possono essere estesi dalla config JSON.

    # RIMOSSO: def _cmd_guarda(self, gioco, parametri=None):
    # Usare _cmd_guarda_ambiente di MappaState.
    
    # RIMOSSO: def _cmd_parla(self, gioco, parametri=None):
    # Gestito da MappaState.process_azione_luogo("dialoga_npg", ...)
    # o MappaState.process_azione_menu("DIALOGO_ARALDO", ...)
    
    # AGGIUNTO: Comando specifico referenziato dalla config JSON
    def _cmd_compra_mercato(self, gioco, parametri=None):
        """Comando per iniziare il processo di acquisto nel mercato."""
        logger.info("Comando 'compra' specifico del mercato eseguito.")
        # Questo comando potrebbe semplicemente impostare una fase o 
        # chiamare un metodo dell'handler del menu specifico (se esiste)
        # per mostrare le opzioni di acquisto.
        if hasattr(self.menu_handler_instance, 'mostra_menu_compra'):
             self.menu_handler_instance.mostra_menu_compra(gioco)
             self.fase_luogo = "compra_oggetti" # Imposta una fase specifica se necessario
             self.ui_aggiornata = False
        else:
             # Fallback se non c'è un menu handler specifico per 'compra'
             logger.warning("Menu handler specifico per 'compra' non disponibile.")
             gioco.io.mostra_messaggio("Opzione di acquisto non disponibile.")
        return True # Indica che il comando è stato gestito

    # AGGIUNTO: Comando specifico referenziato dalla config JSON
    def _cmd_vendi_mercato(self, gioco, parametri=None):
        """Comando per iniziare il processo di vendita nel mercato."""
        logger.info("Comando 'vendi' specifico del mercato eseguito.")
        if hasattr(self.menu_handler_instance, 'mostra_menu_vendi'):
             self.menu_handler_instance.mostra_menu_vendi(gioco)
             self.fase_luogo = "vendi_oggetti" # Imposta una fase specifica
             self.ui_aggiornata = False
        else:
             logger.warning("Menu handler specifico per 'vendi' non disponibile.")
             gioco.io.mostra_messaggio("Opzione di vendita non disponibile.")
        self.ui_aggiornata = False
    
    # RIMOSSO: def _cmd_esamina(self, gioco, parametri=None):
    # Gestito da MappaState._cmd_guarda_ambiente o interazione specifica oggetto.

    # RIMOSSO: def _cmd_inventario(self, gioco, parametri=None):
    # Dovrebbe essere un comando globale o gestito da MappaState.
    
    # RIMOSSO: def _cmd_mappa(self, gioco, parametri=None):
    # Gestito da MappaState._toggle_leggenda o comandi/handler UI specifici.

    # RIMOSSO: def _cmd_aiuto(self, gioco, parametri=None):
    # Gestito da MappaState o un sistema di aiuto globale.
    
    # RIMOSSO: def _cmd_esci(self, gioco, parametri=None):
    # Gestito da MappaState._cmd_torna_indietro.

    def to_dict(self):
        data = super().to_dict() # Ottiene il dizionario da MappaState
        
        oggetto_vendita_data = None
        if self.oggetto_selezionato_per_vendita:
            # Assicurarsi che l'oggetto abbia un metodo to_dict()
            if hasattr(self.oggetto_selezionato_per_vendita, 'to_dict'):
                oggetto_vendita_data = self.oggetto_selezionato_per_vendita.to_dict()
            else:
                logger.warning(f"Oggetto selezionato per vendita '{self.oggetto_selezionato_per_vendita.nome if hasattr(self.oggetto_selezionato_per_vendita, 'nome') else 'Sconosciuto'}' non ha un metodo to_dict(). Non sarà serializzato.")
        
        data["oggetto_selezionato_per_vendita_data"] = oggetto_vendita_data
        return data

    @classmethod
    def from_dict(cls, data, game=None):
        # Lascia che MappaState.from_dict faccia il grosso del lavoro,
        # inclusa la creazione dell'istanza di 'cls' (che sarà MercatoState).
        # MappaState.from_dict è un @classmethod, quindi chiamandolo direttamente
        # con 'data' e 'game' dovrebbe funzionare, e userà 'cls' (MercatoState qui)
        # per creare l'istanza.
        instance = MappaState.from_dict(data, game) # Questo creerà un'istanza di cls (MercatoState)
                                                    # e la popolerà con gli attributi di MappaState.
        
        # Ora aggiungiamo gli attributi specifici di MercatoState
        # È una buona pratica controllare se l'istanza è del tipo corretto,
        # anche se in questo flusso dovrebbe esserlo.
        if isinstance(instance, MercatoState):
            oggetto_data_serializzato = data.get("oggetto_selezionato_per_vendita_data")
            if oggetto_data_serializzato:
                # ItemFactory dovrebbe essere in grado di capire il tipo di item dal dict
                # e restituire l'istanza dell'item corretto.
                # Assicurarsi che ItemFactory.crea_item_da_dict esista e funzioni come previsto.
                try:
                    instance.oggetto_selezionato_per_vendita = ItemFactory.crea_item_da_dict(oggetto_data_serializzato, game=game)
                except Exception as e:
                    logger.error(f"Errore durante la creazione di oggetto_selezionato_per_vendita da ItemFactory: {e}. Dati: {oggetto_data_serializzato}")
                    instance.oggetto_selezionato_per_vendita = None
            else:
                instance.oggetto_selezionato_per_vendita = None
        else:
            # Questo non dovrebbe accadere se la catena di chiamate di @classmethod è corretta.
            logger.error(f"MappaState.from_dict non ha restituito un'istanza di MercatoState come atteso. Tipo restituito: {type(instance)}. L'attributo 'oggetto_selezionato_per_vendita' non sarà ripristinato.")
            # Se instance non è MercatoState, non avrà l'attributo, quindi non impostarlo.

        return instance

    # RIMOSSO: def _register_ui_handlers(self, io_handler):
    # Gli handler sono gestiti da MappaState.

    # RIMOSSO: def _unregister_ui_handlers(self, io_handler):
    # Gli handler sono gestiti da MappaState.

    # RIMOSSO: def entra(self, gioco=None): # Logica spostata in MappaState.enter
    # RIMOSSO: def esci(self, gioco=None): # Logica spostata in MappaState.exit
    # RIMOSSO: def enter(self): # Logica spostata in MappaState.enter
    # RIMOSSO: def exit(self): # Logica spostata in MappaState.exit
    # RIMOSSO: def update(self, input_utente=None): # Logica spostata in MappaState.update

    # RIMOSSO: def gestisci_input_specifico_mercato(self, comando, argomenti):
    # Sostituito da _handle_azione_specifica_luogo e dai metodi _cmd_*.

    # AGGIUNTO: Implementazione del metodo helper per azioni specifiche
    def _handle_azione_specifica_luogo(self, gioco, azione: str, context: dict):
        """Gestisce azioni specifiche del mercato come 'compra' e 'vendi'."""
        logger.info(f"MercatoState gestisce azione specifica: {azione}")
        
        if azione == "compra":
            # Potrebbe mostrare un menu specifico o cambiare fase
            if hasattr(self.menu_handler_instance, 'mostra_menu_compra'):
                self.menu_handler_instance.mostra_menu_compra(gioco)
                self.fase_luogo = "compra_oggetti"
                self.ui_aggiornata = False
            else:
                logger.warning("Menu handler specifico per 'compra' non disponibile via azione.")
                gioco.io.mostra_messaggio("Opzione di acquisto non disponibile.")
        
        elif azione == "vendi":
             if hasattr(self.menu_handler_instance, 'mostra_menu_vendi'):
                self.menu_handler_instance.mostra_menu_vendi(gioco)
                self.fase_luogo = "vendi_oggetti"
             else:
                logger.warning("Menu handler specifico per 'vendi' non disponibile via azione.")
                gioco.io.mostra_messaggio("Opzione di vendita non disponibile.")
             self.ui_aggiornata = False
        
        else:
            # Se non gestita qui, chiama l'implementazione della classe base (che logga un warning)
            super()._handle_azione_specifica_luogo(gioco, azione, context)

    # RIMOSSO: def mostra_merci_del_giorno(self):
    # Logica da integrare nel processo di acquisto/vendita o come evento. 