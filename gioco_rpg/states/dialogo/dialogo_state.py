from states.base_state import BaseGameState
from entities.npg import NPG

# Importa funzioni dai moduli secondari
from states.dialogo.ui import (
    mostra_interfaccia_dialogo,
    mostra_dialogo_corrente,
    mostra_info_npg,
    mostra_inventario_npg
)
from states.dialogo.ui_handlers import (
    handle_dialog_choice,
    handle_click_event,
    handle_menu_action,
    gestisci_click_opzione
)
from states.dialogo.effetti import gestisci_effetto
from states.dialogo.serializzazione import to_dict, from_dict

class DialogoState(BaseGameState):
    """Stato che gestisce il dialogo con un NPG"""
    
    def __init__(self, npg=None, stato_ritorno=None, gioco=None):
        """
        Costruttore dello stato di dialogo
        
        Args:
            npg (NPG, optional): L'NPG con cui dialogare
            stato_ritorno (str, optional): Nome dello stato in cui tornare dopo il dialogo
            gioco: L'istanza del gioco (opzionale)
        """
        super().__init__(gioco)
        self.fase = "conversazione"
        self.npg = npg
        self.stato_corrente = "inizio"
        self.stato_ritorno = stato_ritorno
        self.dati_contestuali = {}  # Per memorizzare dati tra più fasi
        self.ui_aggiornata = False
        
    def _init_commands(self):
        """Inizializza i comandi disponibili per questo stato"""
        # Non utilizziamo più comandi testuali, ma gestiamo tutto tramite gli handler di eventi UI
        self.commands = {}
        
    def esegui(self, gioco):
        """
        Esegue la fase di dialogo
        
        Args:
            gioco (Gioco): Il gioco in cui si sta svolgendo il dialogo
        """
        # Salva il contesto di gioco
        self.set_game_context(gioco)
        
        # Controlla se c'è un NPG valido
        if not self.npg:
            gioco.io.mostra_dialogo("Attenzione", "Non c'è nessuno con cui parlare qui.", ["Continua"])
            return
        
        # Aggiorna il renderer grafico se necessario
        if not self.ui_aggiornata:
            self.aggiorna_renderer(gioco)
            
            # Mostra interfaccia di dialogo
            self._mostra_interfaccia_dialogo(gioco)
            self.ui_aggiornata = True
            
        # Mostra il contenuto del dialogo corrente se necessario
        if not self.dati_contestuali.get("mostrato_dialogo_corrente", False):
            self._mostra_dialogo_corrente(gioco)
            self.dati_contestuali["mostrato_dialogo_corrente"] = True
            
        # Processa gli eventi UI - questo sostituisce l'input testuale
        super().esegui(gioco)
    
    # Collegamento alle funzioni dal modulo ui.py
    _mostra_interfaccia_dialogo = mostra_interfaccia_dialogo
    _mostra_dialogo_corrente = mostra_dialogo_corrente
    _mostra_info_npg = mostra_info_npg
    _mostra_inventario_npg = mostra_inventario_npg
    
    # Collegamento alle funzioni dal modulo ui_handlers.py
    _handle_dialog_choice = handle_dialog_choice
    _handle_click_event = handle_click_event
    _handle_menu_action = handle_menu_action
    _gestisci_click_opzione = gestisci_click_opzione
    
    # Collegamento alle funzioni dal modulo effetti.py
    _gestisci_effetto = gestisci_effetto
    
    def _termina_dialogo(self, gioco):
        """
        Termina il dialogo e torna allo stato precedente
        
        Args:
            gioco: L'istanza del gioco
        """
        # Effetto sonoro
        gioco.io.play_sound({
            "sound_id": "dialog_close",
            "volume": 0.5
        })
        
        # Transizione di chiusura
        gioco.io.mostra_transizione("fade", 0.3)
        
        # Torna allo stato precedente
        gioco.pop_stato()
        
    def pausa(self, gioco):
        """
        Quando il dialogo viene messo in pausa
        salviamo lo stato corrente del dialogo
        """
        super().pausa(gioco)
        gioco.io.mostra_messaggio(f"\nIl dialogo con {self.npg.nome} rimane in sospeso...")
        
    def riprendi(self, gioco):
        """
        Quando il dialogo riprende dopo una pausa
        mostriamo un messaggio di ripresa
        """
        super().riprendi(gioco)
        gioco.io.mostra_messaggio(f"\nRiprendi il dialogo con {self.npg.nome}...")
        
        # Reset della UI
        self.ui_aggiornata = False
        self.dati_contestuali["mostrato_dialogo_corrente"] = False
        
    def esci(self, gioco):
        """
        Quando si esce dal dialogo
        puliamo lo stato
        """
        self.fase = "conversazione"
        gioco.io.mostra_messaggio(f"\nConcludi il dialogo con {self.npg.nome}...")
        super().esci(gioco)
        
    def ha_fatto_scelta(self, stato, scelta=None):
        """
        Verifica se il giocatore ha fatto una particolare scelta durante il dialogo
        
        Args:
            stato (str): Lo stato del dialogo
            scelta (int, optional): La scelta specifica da verificare
            
        Returns:
            bool: True se la scelta è stata fatta, False altrimenti
        """
        if stato not in self.dati_contestuali:
            return False
            
        if scelta is None:
            return True
            
        return self.dati_contestuali[stato] == scelta
        
    # Collegamento alle funzioni dal modulo serializzazione.py
    to_dict = to_dict
    from_dict = classmethod(from_dict) 