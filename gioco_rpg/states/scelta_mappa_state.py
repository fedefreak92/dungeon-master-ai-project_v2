from states.base_state import EnhancedBaseState
from states.taverna import TavernaState
from states.mercato import MercatoState
from states.mappa import MappaState
from util.funzioni_utili import avanti
import core.events as Events

class SceltaMappaState(EnhancedBaseState):
    """
    Stato che permette al giocatore di scegliere tra diverse mappe disponibili.
    Funziona come un hub centrale per navigare tra le diverse aree del gioco.
    """
    
    def __init__(self, gioco=None):
        """
        Inizializza lo stato di scelta mappa.
        
        Args:
            gioco: L'istanza del gioco (opzionale)
        """
        super().__init__()
        self.nome_stato = "scelta_mappa"
        self.stato_precedente = None
        self.ui_aggiornata = False
        # Flag per indicare se è la prima esecuzione dopo il caricamento del gioco
        self.prima_esecuzione = True
        
        # Imposta il contesto di gioco se fornito
        if gioco:
            self.set_game_context(gioco)
            
        # Registra gli handler degli eventi
        self._register_event_handlers()
        
    def _register_event_handlers(self):
        """Registra gli handler per eventi relativi a questo stato"""
        self.event_bus.on(Events.UI_DIALOG_OPEN, self._handle_dialog_open)
        self.event_bus.on(Events.UI_DIALOG_CLOSE, self._handle_dialog_close)
        self.event_bus.on(Events.MENU_SELECTION, self._handle_menu_selection)
        
    def entra(self, gioco=None):
        """
        Metodo chiamato quando si entra nello stato.
        
        Args:
            gioco: L'istanza del gioco (opzionale)
        """
        super().entra(gioco)
        # Salva lo stato corrente della mappa per poter tornare indietro se necessario
        if gioco:
            self.mappa_corrente = gioco.giocatore.mappa_corrente
            self.ui_aggiornata = False
    
    def update(self, dt):
        """
        Aggiornamento basato su eventi.
        
        Args:
            dt: Delta time, tempo trascorso dall'ultimo aggiornamento
        """
        gioco = self.gioco
        if not gioco:
            return
            
        # Ottieni la lista delle mappe disponibili
        lista_mappe = gioco.gestore_mappe.ottieni_lista_mappe()
        
        if not lista_mappe:
            self._mostra_errore(gioco, "Nessuna mappa disponibile.")
            self.emit_event(Events.POP_STATE)
            return
        
        # Aggiorna il renderer grafico se necessario
        if not self.ui_aggiornata:
            self.aggiorna_renderer(gioco)
            self.ui_aggiornata = True
            
        # Mostra le mappe disponibili usando l'interfaccia grafica se prima esecuzione
        if self.prima_esecuzione:
            self._mostra_selezione_mappe(gioco, lista_mappe)
            self.prima_esecuzione = False
    
    def esegui(self, gioco=None):
        """
        Esegue lo stato di scelta mappa.
        Mantenuto per retrocompatibilità.
        """
        # Usa il contesto memorizzato se disponibile
        game_ctx = gioco if gioco else getattr(self, 'gioco', None)
        if not game_ctx:
            raise ValueError("Contesto di gioco non disponibile. Usa set_game_context() prima di eseguire.")
        
        # Aggiorna il renderer grafico se necessario
        if not self.ui_aggiornata:
            self.aggiorna_renderer(game_ctx)
            self.ui_aggiornata = True
            
        # Ottieni la lista delle mappe disponibili
        lista_mappe = game_ctx.gestore_mappe.ottieni_lista_mappe()
        
        if not lista_mappe:
            self._mostra_errore(game_ctx, "Nessuna mappa disponibile.")
            game_ctx.pop_stato()
            return
            
        # Mostra le mappe disponibili usando l'interfaccia grafica
        self._mostra_selezione_mappe(game_ctx, lista_mappe)
        
        # Chiama update per integrazione con EventBus
        self.update(0.033)  # Valore dt predefinito
        
        # Elabora gli eventi UI
        super().esegui(game_ctx)
        
    def _mostra_selezione_mappe(self, gioco, lista_mappe):
        """Mostra la selezione delle mappe usando l'interfaccia grafica"""
        # Genera le opzioni per il dialogo
        opzioni_mappe = []
        id_mappa_giocatore = None
        
        for i, (id_mappa, info_mappa) in enumerate(lista_mappe.items(), 1):
            # Evidenzia la mappa corrente del giocatore
            marker = ""
            if gioco.giocatore.mappa_corrente == id_mappa:
                marker = " [CORRENTE]"
                id_mappa_giocatore = id_mappa
                
            # Ottieni informazioni sulla mappa
            nome_mappa = info_mappa.get("nome", id_mappa)
            livello_min = info_mappa.get("livello_min", 0)
            
            # Aggiungi alla lista di opzioni
            opzioni_mappe.append(f"{nome_mappa}{marker} (Livello: {livello_min}+)")
        
        # Aggiungi l'opzione per tornare indietro
        opzioni_mappe.append("Torna indietro")
        
        # Emetti evento di apertura dialogo
        self.emit_event(Events.UI_DIALOG_OPEN, 
                       dialog_id="seleziona_mappa",
                       title="Seleziona Mappa", 
                       message="Scegli una destinazione:", 
                       options=opzioni_mappe)
    
    def _handle_dialog_open(self, dialog_id=None, **kwargs):
        """
        Handler per l'apertura di un dialogo
        
        Args:
            dialog_id: ID del dialogo da aprire
            **kwargs: Parametri aggiuntivi
        """
        gioco = self.gioco
        if not gioco or dialog_id != "seleziona_mappa":
            return
            
        # Mostra il dialogo usando il vecchio sistema per retrocompatibilità
        title = kwargs.get("title", "Seleziona Mappa")
        message = kwargs.get("message", "Scegli una destinazione:")
        options = kwargs.get("options", [])
        
        gioco.io.mostra_dialogo(title, message, options)
    
    def _handle_dialog_close(self, **kwargs):
        """Handler per la chiusura di un dialogo"""
        pass
        
    def _handle_menu_selection(self, choice=None, menu_id=None, **kwargs):
        """
        Handler per le selezioni dal menu
        
        Args:
            choice: Opzione selezionata
            menu_id: ID del menu
            **kwargs: Parametri aggiuntivi
        """
        if not choice or menu_id != "seleziona_mappa":
            return
            
        gioco = self.gioco
        if not gioco:
            return
            
        # Gestione selezione mappa
        if choice == "Torna indietro":
            self.emit_event(Events.POP_STATE)
            return
            
        # Estrai il nome della mappa dalla scelta
        nome_mappa = choice.split(" [")[0].split(" (")[0]
        
        # Trova la mappa corrispondente
        lista_mappe = gioco.gestore_mappe.ottieni_lista_mappe()
        id_mappa_selezionata = None
        
        for id_mappa, info_mappa in lista_mappe.items():
            if info_mappa.get("nome", id_mappa) == nome_mappa:
                id_mappa_selezionata = id_mappa
                break
                
        if id_mappa_selezionata:
            info_mappa = lista_mappe[id_mappa_selezionata]
            
            # Verifica requisiti
            livello_min = info_mappa.get("livello_min", 0)
            if gioco.giocatore.livello < livello_min:
                self.emit_event(Events.UI_DIALOG_OPEN,
                              dialog_id="errore_livello",
                              title="Livello Insufficiente", 
                              message=f"Non puoi accedere a questa mappa.\nDevi essere almeno di livello {livello_min}.", 
                              options=["OK"])
                return
            
            # Cambia mappa
            self._viaggia_verso_mappa(gioco, id_mappa_selezionata, info_mappa)
    
    def _handle_dialog_choice(self, event):
        """
        Handler legacy per le scelte dai dialoghi.
        Mantenuto per retrocompatibilità.
        
        Args:
            event: Evento di scelta da dialogo
        """
        if not hasattr(event, "data") or not event.data:
            return
        
        choice = event.data.get("choice")
        if not choice:
            return
            
        # Converti in formato nuovo
        self._handle_menu_selection(choice=choice, menu_id="seleziona_mappa")
    
    def _viaggia_verso_mappa(self, gioco, id_mappa, info_mappa):
        """Gestisce il viaggio verso una nuova mappa"""
        # Ottieni la posizione iniziale della mappa
        x, y = None, None
        mappa = gioco.gestore_mappe.ottieni_mappa(id_mappa)
        if mappa:
            x, y = mappa.pos_iniziale_giocatore
        
        # Emetti evento di cambio mappa
        self.emit_event(Events.MAP_CHANGE, 
                       map_id=id_mappa, 
                       position_x=x, 
                       position_y=y)
        
        # Esegui il cambio mappa (per retrocompatibilità)
        success = gioco.cambia_mappa(id_mappa, x, y)
        
        if success:
            # Torna allo stato precedente (solitamente mappa_state)
            self.emit_event(Events.POP_STATE)
            # Per retrocompatibilità
            gioco.pop_stato()
            
            # Aggiorna il renderer se necessario
            if hasattr(gioco.stato_corrente(), 'aggiorna_renderer'):
                gioco.stato_corrente().aggiorna_renderer(gioco)
        else:
            self.emit_event(Events.UI_DIALOG_OPEN,
                          dialog_id="errore_viaggio",
                          title="Viaggio Impossibile", 
                          message="Non è possibile raggiungere questa destinazione.", 
                          options=["OK"])
    
    def _mostra_errore(self, gioco, messaggio):
        """Mostra un messaggio di errore usando l'interfaccia grafica"""
        self.emit_event(Events.UI_DIALOG_OPEN, 
                       dialog_id="errore_generico",
                       title="Errore", 
                       message=messaggio, 
                       options=["OK"])
            
    def aggiorna_renderer(self, gioco):
        """Aggiorna il renderer grafico per lo stato corrente"""
        self.emit_event(Events.UI_UPDATE, 
                       ui_type="scelta_mappa", 
                       state=self.nome_stato)
            
    def to_dict(self):
        """
        Converte lo stato in un dizionario per la serializzazione.
        
        Returns:
            dict: Rappresentazione dello stato in formato dizionario
        """
        data = {
            "nome_stato": self.nome_stato,
            "mappa_corrente": getattr(self, 'mappa_corrente', None),
            "prima_esecuzione": getattr(self, 'prima_esecuzione', False),
            "ui_aggiornata": getattr(self, 'ui_aggiornata', False)
        }
        return data
        
    @classmethod
    def from_dict(cls, data, game=None):
        """
        Crea un'istanza di SceltaMappaState da un dizionario.
        
        Args:
            data (dict): Dizionario con i dati dello stato
            game: Istanza del gioco (opzionale)
            
        Returns:
            SceltaMappaState: Nuova istanza dello stato
        """
        state = cls(game)
        state.mappa_corrente = data.get("mappa_corrente")
        state.prima_esecuzione = data.get("prima_esecuzione", False)
        state.ui_aggiornata = data.get("ui_aggiornata", False)
        return state 