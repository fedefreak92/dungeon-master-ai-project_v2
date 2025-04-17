from states.base_state import BaseGameState
from states.combattimento import CombattimentoState

class MenuState(BaseGameState):
    def __init__(self, gioco=None):
        """Inizializza lo stato del menu"""
        super().__init__(gioco)
        self.ui_aggiornata = False
        
    def _init_commands(self):
        """Inizializza i comandi disponibili per questo stato"""
        self.commands = {
            "inizia_gioco": self._inizia_gioco,
            "esci_gioco": self._esci_gioco
        }
    
    def esegui(self, gioco):
        """
        Esecuzione dello stato menu
        
        Args:
            gioco: Istanza del gioco
        """
        # Salva il contesto di gioco
        self.set_game_context(gioco)
        
        # Aggiorna il renderer grafico se necessario
        if not self.ui_aggiornata:
            self.aggiorna_renderer(gioco)
            
            # Mostra titolo del gioco
            gioco.io.mostra_ui_elemento({
                "type": "text",
                "id": "titolo_gioco",
                "text": "RPG Adventure",
                "x": 400,
                "y": 100, 
                "font_size": 48,
                "centered": True,
                "color": "#FFFFFF"
            })
            
            # Mostra il menu principale con pulsanti
            gioco.io.mostra_dialogo("Menu Principale", "Seleziona un'opzione:", [
                "Inizia Gioco",
                "Esci"
            ])
            
            self.ui_aggiornata = True
        
        # Elabora gli eventi UI - questo sostituisce l'input testuale
        super().esegui(gioco)
    
    def _handle_dialog_choice(self, event):
        """
        Handler per le scelte dai dialoghi
        
        Args:
            event: Evento di scelta da dialogo
        """
        if not hasattr(event, "data") or not event.data:
            return
        
        choice = event.data.get("choice")
        if not choice:
            return
            
        game_ctx = self.gioco
        if not game_ctx:
            return
            
        if choice == "Inizia Gioco":
            self._inizia_gioco(game_ctx)
        elif choice == "Esci":
            self._esci_gioco(game_ctx)
    
    def _inizia_gioco(self, gioco):
        """
        Avvia il gioco
        
        Args:
            gioco: Istanza del gioco
        """
        # Effetto sonoro
        gioco.io.play_sound({
            "sound_id": "menu_select",
            "volume": 0.7
        })
        
        # Transizione grafica
        gioco.io.mostra_transizione("fade", 0.5)
        
        # Cambio stato
        gioco.cambia_stato(CombattimentoState())
    
    def _esci_gioco(self, gioco):
        """
        Esce dal gioco
        
        Args:
            gioco: Istanza del gioco
        """
        # Effetto sonoro
        gioco.io.play_sound({
            "sound_id": "menu_back",
            "volume": 0.5
        })
        
        # Chiedi conferma prima di uscire
        gioco.io.mostra_dialogo(
            "Conferma", 
            "Sei sicuro di voler uscire dal gioco?", 
            ["Sì", "No"]
        )
        self.in_conferma_uscita = True
    
    def _handle_keypress(self, event):
        """
        Handler per la pressione dei tasti
        
        Args:
            event: Evento tastiera
        """
        if not hasattr(event, "data") or not event.data:
            return
        
        key = event.data.get("key")
        if not key:
            return
            
        game_ctx = self.gioco
        if not game_ctx:
            return
            
        # Gestione tasti di scelta rapida
        if key == "Escape":
            if hasattr(self, "in_conferma_uscita") and self.in_conferma_uscita:
                # Se siamo nella conferma, "Escape" è un "No"
                self.in_conferma_uscita = False
                self.ui_aggiornata = False
            else:
                # Altrimenti apri la conferma di uscita
                self._esci_gioco(game_ctx)
    
    def to_dict(self):
        """
        Converte lo stato in un dizionario per la serializzazione.
        
        Returns:
            dict: Rappresentazione dello stato in formato dizionario
        """
        data = super().to_dict()
        data.update({
            "ui_aggiornata": self.ui_aggiornata,
            "in_conferma_uscita": getattr(self, "in_conferma_uscita", False)
        })
        return data

    @classmethod
    def from_dict(cls, data, game=None):
        """
        Crea un'istanza di MenuState da un dizionario.
        
        Args:
            data (dict): Dizionario con i dati dello stato
            game: Istanza del gioco (opzionale)
            
        Returns:
            MenuState: Nuova istanza dello stato
        """
        state = cls(game)
        state.ui_aggiornata = data.get("ui_aggiornata", False)
        state.in_conferma_uscita = data.get("in_conferma_uscita", False)
        return state 

# Alias per compatibilità con i test
MenuPrincipaleState = MenuState 