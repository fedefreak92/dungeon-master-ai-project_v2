"""
Implementazione della classe principale dello stato mappa.
"""

from states.base_state import BaseState
from states.mappa import ui, movimento, interazioni, ui_handlers, serializzazione
from util.funzioni_utili import avanti

class MappaState(BaseState):
    def __init__(self, stato_origine=None):
        """
        Inizializza lo stato mappa.
        
        Args:
            stato_origine: Lo stato da cui proviene (es. TavernaState o MercatoState)
        """
        super().__init__()
        self.stato_origine = stato_origine
        self.mostra_leggenda = True
        self.menu_attivo = None
        self.ui_aggiornata = False
        self.ultima_scelta = None
        self.attesa_risposta_mappa = None
        
        # Direzioni di movimento
        self.direzioni = {
            "nord": (0, -1),
            "sud": (0, 1),
            "est": (1, 0),
            "ovest": (-1, 0)
        }
        
        # Inizializza i comandi
        self._init_commands()
    
    def _init_commands(self):
        """Inizializza i comandi disponibili per questo stato"""
        # Definire mapping comandi -> funzioni
        self.commands = {
            "muovi": self._sposta_giocatore,
            "interagisci": self._mostra_opzioni_interazione,
            "mostra_elementi": self._mostra_elementi_vicini,
            "leggenda": self._toggle_leggenda,
            "torna_indietro": self._torna_indietro
        }
    
    def esegui(self, gioco):
        """
        Implementazione dell'esecuzione dello stato mappa
        
        Args:
            gioco: L'istanza del gioco
        """
        # Salva il contesto di gioco
        self.set_game_context(gioco)
        
        # Ottieni la mappa corrente
        mappa_corrente = gioco.gestore_mappe.ottieni_mappa(gioco.giocatore.mappa_corrente)
        nome_mappa = gioco.giocatore.mappa_corrente.upper()
        
        gioco.io.mostra_messaggio(f"\n=== MAPPA DI {nome_mappa} ===")
        
        # Utilizziamo il renderer grafico invece della rappresentazione ASCII
        if not self.ui_aggiornata:
            self.aggiorna_renderer(gioco)
            self.ui_aggiornata = True
        
        if self.mostra_leggenda:
            ui.mostra_leggenda(self, gioco)
        
        # Mostra informazioni sulla posizione del giocatore
        gioco.io.mostra_messaggio(f"\nPosizione attuale: ({gioco.giocatore.x}, {gioco.giocatore.y})")
        
        # Mostra menù interattivo se non è già attivo
        if not self.menu_attivo:
            ui.mostra_menu_principale(self, gioco)
        
        # Processa gli eventi UI
        super().esegui(gioco)
    
    # Wrapper per i metodi nei moduli
    def _handle_dialog_choice(self, event):
        ui_handlers.handle_dialog_choice(self, event)
        
    def _handle_keypress(self, event):
        ui_handlers.handle_keypress(self, event)
        
    def _handle_click_event(self, event):
        ui_handlers.handle_click_event(self, event)
        
    def _handle_menu_action(self, event):
        ui_handlers.handle_menu_action(self, event)
        
    def _sposta_giocatore(self, gioco, direzione):
        movimento.sposta_giocatore(self, gioco, direzione)
        
    def _mostra_opzioni_movimento(self, gioco):
        ui.mostra_opzioni_movimento(self, gioco)
        
    def _mostra_opzioni_interazione(self, gioco):
        ui.mostra_opzioni_interazione(self, gioco)
        
    def _interagisci_con_oggetto(self, gioco):
        interazioni.interagisci_con_oggetto(self, gioco)
        
    def _interagisci_con_npg(self, gioco):
        interazioni.interagisci_con_npg(self, gioco)
        
    def _esamina_area(self, gioco):
        interazioni.esamina_area(self, gioco)
        
    def _gestisci_cambio_mappa(self, gioco, mappa_origine, mappa_destinazione):
        movimento.gestisci_cambio_mappa(self, gioco, mappa_origine, mappa_destinazione)
        
    def _mostra_elementi_vicini(self, gioco):
        ui.mostra_elementi_vicini(self, gioco)
        
    def _mostra_menu_principale(self, gioco):
        ui.mostra_menu_principale(self, gioco)
        
    def _toggle_leggenda(self, gioco):
        ui.toggle_leggenda(self, gioco)
        
    def _torna_indietro(self, gioco):
        interazioni.torna_indietro(self, gioco)
        
    def to_dict(self):
        """
        Converte lo stato in un dizionario per la serializzazione.
        
        Returns:
            dict: Rappresentazione dello stato in formato dizionario
        """
        return serializzazione.to_dict(self)

    @classmethod
    def from_dict(cls, data, game=None):
        """
        Crea un'istanza di MappaState da un dizionario.
        
        Args:
            data (dict): Dizionario con i dati dello stato
            game: Istanza del gioco (opzionale)
            
        Returns:
            MappaState: Nuova istanza dello stato
        """
        return serializzazione.from_dict(cls, data, game)
        
    def get_base_dict(self):
        """
        Ottiene il dizionario base dallo stato genitore.
        
        Returns:
            dict: Dizionario base
        """
        return super().to_dict() 