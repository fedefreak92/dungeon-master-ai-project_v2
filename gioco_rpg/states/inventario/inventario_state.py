from states.base.enhanced_base_state import EnhancedBaseState
import core.events as Events
from states.inventario.ui_handlers import UIInventarioHandler
from states.inventario.menu_handlers import MenuInventarioHandler
from states.inventario.oggetti import GestoreOggetti
from util.funzioni_utili import avanti


class GestioneInventarioState(EnhancedBaseState):
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
        # Inizializzazione della classe base
        super().__init__()
        
        # Inizializzazione sottosistemi
        self.ui_handler = UIInventarioHandler(self)
        self.menu_handler = MenuInventarioHandler(self)
        self.gestore_oggetti = GestoreOggetti(self)
        
        # Imposta il contesto di gioco se fornito
        if gioco:
            self.set_game_context(gioco)
            
        self.stato_precedente = stato_precedente
        self.fase = "menu_principale"  # Fase iniziale
        self.ultimo_input = None
        self.ui_aggiornata = False
        
        # Registra handler per eventi
        self._register_event_handlers()
        
    def _register_event_handlers(self):
        """Registra gli handler per eventi relativi a questo stato"""
        # Eventi UI
        self.event_bus.on(Events.UI_DIALOG_OPEN, self._handle_dialog_open)
        self.event_bus.on(Events.UI_DIALOG_CLOSE, self._handle_dialog_close)
        self.event_bus.on(Events.UI_INVENTORY_TOGGLE, self._handle_inventory_toggle)
        
        # Eventi oggetti
        self.event_bus.on(Events.PLAYER_USE_ITEM, self._handle_use_item)
        self.event_bus.on("EQUIP_ITEM", self._handle_equip_item)
        self.event_bus.on("UNEQUIP_ITEM", self._handle_unequip_item)
        self.event_bus.on("EXAMINE_ITEM", self._handle_examine_item)
        
        # Eventi menu
        self.event_bus.on("MENU_SELECTION", self._handle_menu_selection)
        
    def _init_commands(self):
        """Inizializza i comandi disponibili per questo stato"""
        self.commands = {
            "usa_oggetto": self.gestore_oggetti.usa_oggetto_selezionato,
            "equipaggia_oggetto": self.gestore_oggetti.equipaggia_oggetto_selezionato,
            "rimuovi_equipaggiamento": self.gestore_oggetti.rimuovi_equipaggiamento_selezionato,
            "esamina_oggetto": self.gestore_oggetti.esamina_oggetto_selezionato,
            "torna_indietro": self.menu_handler.torna_indietro
        }
    
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
        
        # Gestione di inventario vuoto
        if self.fase == "menu_principale" and not gioco.giocatore.inventario:
            if not self.ui_aggiornata:
                gioco.io.mostra_messaggio("Il tuo inventario è vuoto.")
                gioco.io.mostra_dialogo("Inventario Vuoto", "Non hai oggetti nel tuo inventario.", ["Torna Indietro"])
                self.ui_aggiornata = True
            return
        
        # Logica di aggiornamento specifica dello stato
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
    
    def esegui(self, gioco):
        """
        Implementazione dell'esecuzione dello stato di gestione inventario.
        Mantenuta per retrocompatibilità.
        
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
        
        # Aggiungi chiamata a update per integrazione con EventBus
        self.update(0.033)  # Valore dt predefinito
        
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
        (Metodo legacy per retrocompatibilità)
        
        Args:
            event: Evento di scelta da dialogo
            
        Returns:
            bool: True se l'evento è stato gestito, False altrimenti
        """
        return self.menu_handler.handle_dialog_choice(event)
    
    # Handler per eventi EventBus
    def _handle_dialog_open(self, dialog=None, dialog_id=None, **kwargs):
        """
        Gestisce l'apertura di un dialogo
        
        Args:
            dialog: Dati del dialogo
            dialog_id: ID del dialogo
            **kwargs: Parametri aggiuntivi
        """
        gioco = self.gioco
        if not gioco:
            return
            
        # Logica di apertura dialogo...
    
    def _handle_dialog_close(self, **kwargs):
        """
        Gestisce la chiusura di un dialogo
        """
        gioco = self.gioco
        if not gioco:
            return
            
        # Logica di chiusura dialogo...
    
    def _handle_inventory_toggle(self, **kwargs):
        """
        Gestisce l'apertura/chiusura dell'inventario
        """
        gioco = self.gioco
        if not gioco:
            return
            
        # Se siamo nell'inventario, usciamo
        if gioco.stato_corrente() == self:
            self.menu_handler.torna_indietro(gioco)
    
    def _handle_use_item(self, item_id=None, **kwargs):
        """
        Gestisce l'uso di un oggetto
        
        Args:
            item_id: ID dell'oggetto da usare
            **kwargs: Parametri aggiuntivi
        """
        gioco = self.gioco
        if not gioco:
            return
            
        # Trova l'oggetto corrispondente all'ID
        for item in gioco.giocatore.inventario:
            if hasattr(item, 'id') and item.id == item_id:
                self.gestore_oggetti.usa_oggetto_selezionato(gioco, item)
                break
    
    def _handle_equip_item(self, item_id=None, **kwargs):
        """
        Gestisce l'equipaggiamento di un oggetto
        
        Args:
            item_id: ID dell'oggetto da equipaggiare
            **kwargs: Parametri aggiuntivi
        """
        gioco = self.gioco
        if not gioco:
            return
            
        # Trova l'oggetto corrispondente all'ID
        for item in gioco.giocatore.inventario:
            if hasattr(item, 'id') and item.id == item_id:
                self.gestore_oggetti.equipaggia_oggetto_selezionato(gioco, item)
                break
    
    def _handle_unequip_item(self, item_id=None, **kwargs):
        """
        Gestisce la rimozione di un equipaggiamento
        
        Args:
            item_id: ID dell'oggetto da rimuovere
            **kwargs: Parametri aggiuntivi
        """
        gioco = self.gioco
        if not gioco:
            return
            
        # Trova l'oggetto corrispondente all'ID
        opzioni_rimozione = self.gestore_oggetti.get_opzioni_rimozione(gioco)
        for tipo, item in opzioni_rimozione:
            if hasattr(item, 'id') and item.id == item_id:
                self.gestore_oggetti.rimuovi_equipaggiamento_selezionato(gioco, item)
                break
    
    def _handle_examine_item(self, item_id=None, **kwargs):
        """
        Gestisce l'esame di un oggetto
        
        Args:
            item_id: ID dell'oggetto da esaminare
            **kwargs: Parametri aggiuntivi
        """
        gioco = self.gioco
        if not gioco:
            return
            
        # Trova l'oggetto corrispondente all'ID
        for item in gioco.giocatore.inventario:
            if hasattr(item, 'id') and item.id == item_id:
                self.gestore_oggetti.esamina_oggetto_selezionato(gioco, item)
                break
    
    def _handle_menu_selection(self, menu_id=None, choice=None, **kwargs):
        """
        Gestisce la selezione da un menu
        
        Args:
            menu_id: ID del menu
            choice: Scelta selezionata
            **kwargs: Parametri aggiuntivi
        """
        if not menu_id or not choice:
            return
            
        gioco = self.gioco
        if not gioco:
            return
            
        # Crea un evento di tipo legacy per retrocompatibilità
        class LegacyEvent:
            def __init__(self, data):
                self.data = data
                
        legacy_event = LegacyEvent({"choice": choice})
        self.menu_handler.handle_dialog_choice(legacy_event)
    
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