from states.base.enhanced_base_state import EnhancedBaseState
from entities.npg import NPG
import core.events as Events

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

class DialogoState(EnhancedBaseState):
    """Stato che gestisce il dialogo con un NPG"""
    
    def __init__(self, npg=None, stato_ritorno=None, gioco=None):
        """
        Costruttore dello stato di dialogo
        
        Args:
            npg (NPG, optional): L'NPG con cui dialogare
            stato_ritorno (str, optional): Nome dello stato in cui tornare dopo il dialogo
            gioco: L'istanza del gioco (opzionale)
        """
        super().__init__()
        self.fase = "conversazione"
        self.npg = npg
        self.stato_corrente = "inizio"
        self.stato_ritorno = stato_ritorno
        self.dati_contestuali = {}  # Per memorizzare dati tra più fasi
        self.ui_aggiornata = False
        
        if gioco:
            self.set_game_context(gioco)
            
        # Registra handler per eventi
        self._register_event_handlers()
        
    def _register_event_handlers(self):
        """Registra gli handler per eventi relativi al dialogo"""
        self.event_bus.on(Events.UI_DIALOG_OPEN, self._handle_dialog_open)
        self.event_bus.on(Events.UI_DIALOG_CLOSE, self._handle_dialog_close)
        self.event_bus.on(Events.DIALOG_CHOICE, self._handle_dialog_choice_event)
        self.event_bus.on(Events.MENU_SELECTION, self._handle_menu_selection)
        
    def update(self, dt):
        """
        Aggiornamento basato su eventi per lo stato dialogo
        
        Args:
            dt: Delta time, tempo trascorso dall'ultimo aggiornamento
        """
        gioco = self.gioco
        if not gioco:
            return
            
        # Controlla se c'è un NPG valido
        if not self.npg:
            self.emit_event(Events.UI_DIALOG_OPEN, 
                           dialog_id="warning_dialog",
                           title="Attenzione", 
                           content="Non c'è nessuno con cui parlare qui.", 
                           options=["Continua"])
            return
            
        # Aggiorna il renderer grafico se necessario
        if not self.ui_aggiornata:
            self._mostra_interfaccia_dialogo(gioco)
            self.ui_aggiornata = True
            
        # Mostra il contenuto del dialogo corrente se necessario
        if not self.dati_contestuali.get("mostrato_dialogo_corrente", False):
            self._mostra_dialogo_corrente(gioco)
            self.dati_contestuali["mostrato_dialogo_corrente"] = True
            
    def esegui(self, gioco):
        """
        Implementazione dell'esecuzione dello stato.
        Mantenuta per retrocompatibilità.
        
        Args:
            gioco: L'istanza del gioco
        """
        # Salva il contesto di gioco
        self.set_game_context(gioco)
        
        # Aggiungi chiamata a update per integrazione con EventBus
        self.update(0.033)  # Valore dt predefinito
        
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
    
    # Handler per eventi specifici
    def _handle_dialog_open(self, dialog_id=None, title=None, content=None, options=None, **kwargs):
        """
        Gestisce l'apertura di un dialogo
        
        Args:
            dialog_id: Identificatore del dialogo
            title: Titolo del dialogo
            content: Contenuto del dialogo
            options: Opzioni disponibili
            **kwargs: Altri parametri
        """
        gioco = self.gioco
        if not gioco:
            return
            
        if dialog_id == "info_npg":
            self._mostra_info_npg(gioco)
        elif dialog_id == "inventario_npg":
            self._mostra_inventario_npg(gioco)
            
    def _handle_dialog_close(self, **kwargs):
        """
        Gestisce la chiusura di un dialogo
        
        Args:
            **kwargs: Parametri aggiuntivi
        """
        gioco = self.gioco
        if not gioco:
            return
            
        if self.fase == "fine":
            self._termina_dialogo(gioco)
            
    def _handle_dialog_choice_event(self, choice=None, dialog_id=None, **kwargs):
        """
        Gestisce la scelta da un dialogo tramite evento
        
        Args:
            choice: La scelta effettuata
            dialog_id: ID del dialogo
            **kwargs: Altri parametri
        """
        if not choice:
            return
            
        # Crea un oggetto evento compatibile con il vecchio handler
        event = type('Event', (), {'data': {'choice': choice}})
        self._handle_dialog_choice(event)
        
    def _handle_menu_selection(self, menu_id=None, selection=None, **kwargs):
        """
        Gestisce la selezione da un menu contestuale
        
        Args:
            menu_id: ID del menu
            selection: Elemento selezionato
            **kwargs: Altri parametri
        """
        if not selection:
            return
            
        gioco = self.gioco
        if not gioco:
            return
            
        # Crea un oggetto evento compatibile con il vecchio handler
        event = type('Event', (), {'data': {'action': selection}})
        self._handle_menu_action(event)
    
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
        
        # Torna allo stato precedente usando EventBus
        self.pop_state()
        
    def pausa(self, gioco=None):
        """
        Quando il dialogo viene messo in pausa
        salviamo lo stato corrente del dialogo
        """
        game_ctx = gioco if gioco else self.gioco
        super().pausa(game_ctx)
        
        if game_ctx and self.npg:
            game_ctx.io.mostra_messaggio(f"\nIl dialogo con {self.npg.nome} rimane in sospeso...")
        
    def riprendi(self, gioco=None):
        """
        Quando il dialogo riprende dopo una pausa
        mostriamo un messaggio di ripresa
        """
        game_ctx = gioco if gioco else self.gioco
        super().riprendi(game_ctx)
        
        if game_ctx and self.npg:
            game_ctx.io.mostra_messaggio(f"\nRiprendi il dialogo con {self.npg.nome}...")
        
        # Reset della UI
        self.ui_aggiornata = False
        self.dati_contestuali["mostrato_dialogo_corrente"] = False
        
    def esci(self, gioco=None):
        """
        Quando si esce dal dialogo
        puliamo lo stato
        """
        self.fase = "conversazione"
        
        game_ctx = gioco if gioco else self.gioco
        if game_ctx and self.npg:
            game_ctx.io.mostra_messaggio(f"\nConcludi il dialogo con {self.npg.nome}...")
            
        super().esci(game_ctx)
        
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