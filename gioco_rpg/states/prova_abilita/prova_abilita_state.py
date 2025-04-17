from states.base.base_game_state import BaseGameState
from util.dado import Dado
from entities.entita import ABILITA_ASSOCIATE


class ProvaAbilitaState(BaseGameState):
    def __init__(self, contesto=None):
        """
        Inizializza lo stato di prova di abilità.
        
        Args:
            contesto (dict, optional): Contesto opzionale per la prova (es. oggetto associato)
        """
        super().__init__()
        self.contesto = contesto or {}
        self.fase = "scegli_abilita"  # Fase iniziale
        self.ultimo_input = None  # Per memorizzare l'ultimo input dell'utente
        self.abilita_scelta = None  # L'abilità scelta dall'utente
        self.dati_contestuali = {}  # Per memorizzare dati tra più fasi
        self.ui_aggiornata = False  # Flag per l'aggiornamento UI
        self.menu_attivo = None
        
    def esegui(self, gioco):
        """
        Esecuzione dello stato
        
        Args:
            gioco: Istanza del gioco
        """
        # Salva il contesto di gioco
        self.set_game_context(gioco)
        
        # Aggiorna il renderer grafico se necessario
        if not self.ui_aggiornata:
            from states.prova_abilita.ui import aggiorna_renderer
            aggiorna_renderer(self, gioco)
            self.ui_aggiornata = True
        
        # Mostra menu iniziale se non ne è già attivo uno
        if not self.menu_attivo:
            from states.prova_abilita.ui import esegui_menu_principale
            esegui_menu_principale(self, gioco)
            self.menu_attivo = "principale"
        
        # Elabora gli eventi UI
        super().esegui(gioco)
    
    def _handle_dialog_choice(self, event):
        """
        Handler per le scelte dai dialoghi
        
        Args:
            event: Evento di scelta da dialogo
        """
        from states.prova_abilita.ui_handlers import gestisci_scelta_dialogo
        gestisci_scelta_dialogo(self, event)
    
    def _handle_click_event(self, event):
        """
        Handler per eventi di click
        
        Args:
            event: Evento di click
        """
        from states.prova_abilita.ui_handlers import gestisci_evento_click
        gestisci_evento_click(self, event)
    
    def _gestisci_successo(self, gioco, abilita):
        """Gestisce gli effetti del successo nella prova"""
        from states.prova_abilita.esecuzione import gestisci_successo
        gestisci_successo(self, gioco, abilita)
            
    def _gestisci_fallimento(self, gioco, abilita):
        """Gestisce gli effetti del fallimento nella prova"""
        from states.prova_abilita.esecuzione import gestisci_fallimento
        gestisci_fallimento(self, gioco, abilita)
    
    def _gestisci_successo_npg(self, gioco, abilita, npg):
        """Gestisce gli effetti del successo nella prova contro un NPG"""
        from states.prova_abilita.esecuzione import gestisci_successo_npg
        gestisci_successo_npg(self, gioco, abilita, npg)
    
    def _gestisci_fallimento_npg(self, gioco, abilita, npg):
        """Gestisce il fallimento di una prova contro un NPG"""
        from states.prova_abilita.esecuzione import gestisci_fallimento_npg
        gestisci_fallimento_npg(self, gioco, abilita, npg)
        
    def ottieni_mappa_corrente(self, gioco):
        """Ottiene la mappa corrente"""
        from states.prova_abilita.interazioni import ottieni_mappa_corrente
        return ottieni_mappa_corrente(self, gioco)
    
    def ottieni_npg_vicini(self, gioco):
        """Ottiene i NPG vicini al giocatore"""
        from states.prova_abilita.interazioni import ottieni_npg_vicini
        return ottieni_npg_vicini(self, gioco)
    
    def ottieni_oggetti_vicini(self, gioco):
        """Ottiene gli oggetti vicini al giocatore"""
        from states.prova_abilita.interazioni import ottieni_oggetti_vicini
        return ottieni_oggetti_vicini(self, gioco)
        
    def to_dict(self):
        """
        Converte lo stato in un dizionario per la serializzazione.
        
        Returns:
            dict: Rappresentazione dello stato in formato dizionario
        """
        from states.prova_abilita.serializzazione import to_dict
        return to_dict(self)

    @classmethod
    def from_dict(cls, data, game=None):
        """
        Crea un'istanza di ProvaAbilitaState da un dizionario.
        
        Args:
            data (dict): Dizionario con i dati dello stato
            game: Istanza del gioco (opzionale)
            
        Returns:
            ProvaAbilitaState: Nuova istanza dello stato
        """
        from states.prova_abilita.serializzazione import from_dict
        return from_dict(cls, data, game) 