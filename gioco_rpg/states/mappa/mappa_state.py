"""
Implementazione della classe principale dello stato mappa.
"""

from states.base.enhanced_base_state import EnhancedBaseState
from states.mappa import ui, movimento, interazioni, ui_handlers, serializzazione
from util.funzioni_utili import avanti
import core.events as Events

class MappaState(EnhancedBaseState):
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
        
        # Registra handler per eventi
        self._register_event_handlers()
    
    def _register_event_handlers(self):
        """Registra gli handler per eventi relativi alla mappa"""
        # Eventi di movimento
        self.event_bus.on(Events.ENTITY_MOVED, self._handle_entity_moved)
        self.event_bus.on(Events.MOVEMENT_BLOCKED, self._handle_movement_blocked)
        self.event_bus.on(Events.MAP_CHANGE, self._handle_map_change)
        
        # Eventi di trigger
        self.event_bus.on(Events.TRIGGER_ACTIVATED, self._handle_trigger_activated)
        self.event_bus.on(Events.TREASURE_FOUND, self._handle_treasure_found)
        
        # Altri eventi
        self.event_bus.on(Events.UI_UPDATE, self._handle_ui_update)
    
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
        
        # Aggiorna il renderer grafico se necessario
        if not self.ui_aggiornata:
            self.aggiorna_renderer(gioco)
            
            # Mostra leggenda se attiva
            if self.mostra_leggenda:
                ui.mostra_leggenda(self, gioco)
                
            # Emetti evento di UI aggiornata
            self.emit_event(Events.UI_UPDATE, element="mappa", state=self)
            self.ui_aggiornata = True
            
        # Notifica cambiamenti nella mappa se necessario
        if hasattr(self, 'mappa_aggiornata') and self.mappa_aggiornata:
            self.emit_event(Events.MAP_LOAD, 
                           map_name=gioco.giocatore.mappa_corrente,
                           player_pos=(gioco.giocatore.x, gioco.giocatore.y))
            self.mappa_aggiornata = False
    
    def esegui(self, gioco):
        """
        Implementazione dell'esecuzione dello stato mappa.
        Mantenuta per retrocompatibilità.
        
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
        
        # Aggiorna con EventBus, mantenendo retrocompatibilità
        self.update(0.033)  # Valore dt predefinito
        
        # Processa gli eventi UI
        super().esegui(gioco)
    
    # Handler eventi
    def _handle_entity_moved(self, entity_id, from_pos, to_pos, **kwargs):
        """Gestisce l'evento di movimento di un'entità"""
        gioco = self.gioco
        if not gioco:
            return
            
        # Se l'entità è il giocatore, aggiorna UI
        if entity_id == gioco.giocatore.id:
            self.ui_aggiornata = False  # Forza aggiornamento UI
            
            # Logga movimento (può essere rimosso in produzione)
            gioco.io.mostra_messaggio(f"Ti sei spostato a ({to_pos[0]}, {to_pos[1]})")
            
            # Controlla oggetti e NPC vicini dopo il movimento
            self._mostra_elementi_vicini(gioco)
    
    def _handle_movement_blocked(self, entity_id, from_pos, to_pos, reason, **kwargs):
        """Gestisce l'evento di movimento bloccato"""
        gioco = self.gioco
        if not gioco or entity_id != gioco.giocatore.id:
            return
            
        # Mostra messaggio appropriato in base al motivo del blocco
        if reason == "collision":
            gioco.io.mostra_messaggio("Non puoi andare in quella direzione.")
        elif reason == "obstacle":
            gioco.io.mostra_messaggio("La strada è bloccata da un ostacolo.")
        elif reason == "boundary":
            gioco.io.mostra_messaggio("Hai raggiunto il confine della mappa.")
    
    def _handle_map_change(self, entity_id, from_map, to_map, target_pos=None, **kwargs):
        """Gestisce l'evento di cambio mappa"""
        gioco = self.gioco
        if not gioco or entity_id != gioco.giocatore.id:
            return
            
        # Delega la gestione del cambio mappa al modulo movimento
        movimento.gestisci_cambio_mappa(self, gioco, from_map, to_map, target_pos)
        
        # Segnala che la mappa è stata aggiornata
        self.mappa_aggiornata = True
        self.ui_aggiornata = False
    
    def _handle_trigger_activated(self, trigger_id, trigger_type, entity_id, position, **kwargs):
        """Gestisce l'attivazione di un trigger"""
        gioco = self.gioco
        if not gioco or entity_id != gioco.giocatore.id:
            return
            
        # Gestisci diversi tipi di trigger
        if trigger_type == "porta":
            # Gestito da _handle_map_change, non fare nulla qui
            pass
        elif trigger_type == "trappola":
            gioco.io.mostra_messaggio("Hai attivato una trappola!")
        elif trigger_type == "evento":
            gioco.io.mostra_messaggio("Qualcosa sta succedendo...")
        elif trigger_type == "npg":
            gioco.io.mostra_messaggio("C'è qualcuno qui...")
            # Avvia dialogo con NPG
    
    def _handle_treasure_found(self, entity_id, treasure_id, contents, **kwargs):
        """Gestisce l'evento di tesoro trovato"""
        gioco = self.gioco
        if not gioco or entity_id != gioco.giocatore.id:
            return
            
        gioco.io.mostra_messaggio("Hai trovato un tesoro!")
        # Mostra contenuti e aggiungi all'inventario
        if contents:
            gioco.io.mostra_messaggio(f"Contenuto: {', '.join(item.get('name', 'Oggetto') for item in contents)}")
            # Aggiungi items all'inventario
    
    def _handle_ui_update(self, element, **kwargs):
        """Gestisce l'aggiornamento dell'interfaccia utente"""
        # Aggiorna solo se l'elemento è relativo alla mappa
        if element in ["mappa", "player_position", "all"]:
            self.ui_aggiornata = False
    
    # Wrapper per i metodi nei moduli (mantenuti per retrocompatibilità)
    def _handle_dialog_choice(self, event):
        ui_handlers.handle_dialog_choice(self, event)
        
    def _handle_keypress(self, event):
        ui_handlers.handle_keypress(self, event)
        
    def _handle_click_event(self, event):
        ui_handlers.handle_click_event(self, event)
        
    def _handle_menu_action(self, event):
        ui_handlers.handle_menu_action(self, event)
        
    def _sposta_giocatore(self, gioco, direzione):
        """
        Wrapper per il movimento del giocatore.
        Ora utilizza l'evento PLAYER_MOVE invece di chiamare direttamente
        il metodo movimento.sposta_giocatore.
        """
        # Emetti evento di movimento
        self.emit_event(Events.PLAYER_MOVE, direction=direzione)
        
    def _mostra_opzioni_movimento(self, gioco):
        ui.mostra_opzioni_movimento(self, gioco)
        
    def _mostra_opzioni_interazione(self, gioco):
        ui.mostra_opzioni_interazione(self, gioco)
        
    def _interagisci_con_oggetto(self, gioco):
        # Emetti evento di interazione invece di chiamata diretta
        self.emit_event(Events.PLAYER_INTERACT, interaction_type="object")
        interazioni.interagisci_con_oggetto(self, gioco)
        
    def _interagisci_con_npg(self, gioco):
        # Emetti evento di interazione invece di chiamata diretta
        self.emit_event(Events.PLAYER_INTERACT, interaction_type="npc")
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