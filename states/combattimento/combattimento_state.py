from states.base_state import EnhancedBaseState
from entities.nemico import Nemico
from entities.giocatore import Giocatore
from entities.npg import NPG
from util.dado import Dado
import core.events as Events

# Importa le funzionalità dai moduli separati
from states.combattimento.azioni import AzioniCombattimento
from states.combattimento.turni import GestoreTurni
from states.combattimento.ui import UICombattimento

class CombattimentoState(EnhancedBaseState):
    def __init__(self, nemico=None, npg_ostile=None, gioco=None):
        """
        Inizializza lo stato di combattimento.
        
        Args:
            nemico (Nemico, optional): Un nemico tradizionale
            npg_ostile (NPG, optional): Un NPG diventato ostile
            gioco: L'istanza del gioco (opzionale)
        """
        super().__init__()
        
        # Pre-definisci il metodo esegui_attacco per evitare errori di inizializzazione
        self.esegui_attacco = lambda *args, **kwargs: {"successo": False, "messaggio": "Metodo non ancora inizializzato"}
        
        # Supporto per l'inizializzazione tramite contesto
        if isinstance(nemico, dict) and 'partecipanti' in nemico:
            self._init_from_context(nemico)
            return
            
        # Imposta il contesto di gioco se fornito
        if gioco:
            self.set_game_context(gioco)
            
        self.nemico = nemico
        self.npg_ostile = npg_ostile
        self.turno = 1
        self.avversario = nemico if nemico else npg_ostile
        # Inizializza i dadi per vari tiri durante il combattimento
        self.dado_d20 = Dado(20)
        self.dado_d100 = Dado(100)
        # Aggiungiamo la fase per gestire il flusso asincrono
        self.fase = "scelta"
        # Per memorizzare eventuali dati temporanei tra le fasi
        self.dati_temporanei = {}
        # Stato UI
        self.ui_aggiornata = False
        
        # Inizializza i moduli separati
        self.azioni = AzioniCombattimento(self)
        self.gestore_turni = GestoreTurni(self)
        self.ui = UICombattimento(self)
        
        # Assegna i metodi dell'oggetto azioni
        self.esegui_attacco = lambda *args, **kwargs: self.azioni.esegui_attacco(*args, **kwargs)
        self.usa_abilita = lambda *args, **kwargs: self.azioni.usa_abilita(*args, **kwargs)
        self.usa_oggetto = lambda *args, **kwargs: self.azioni.usa_oggetto(*args, **kwargs)
        self.passa_turno = lambda *args, **kwargs: self.azioni.passa_turno(*args, **kwargs)
        self.determina_azione_ia = lambda *args, **kwargs: self.azioni.determina_azione_ia(*args, **kwargs)
        self.esegui_azione_ia = lambda *args, **kwargs: self.azioni.esegui_azione_ia(*args, **kwargs)
        
        # Registra handler per eventi
        self._register_event_handlers()
        
    def _register_event_handlers(self):
        """Registra gli handler per eventi relativi a questo stato"""
        # Eventi di combattimento
        self.event_bus.on(Events.COMBAT_START, self._handle_combat_start)
        self.event_bus.on(Events.COMBAT_END, self._handle_combat_end)
        self.event_bus.on(Events.COMBAT_NEXT_TURN, self._handle_next_turn)
        self.event_bus.on(Events.ENTITY_ATTACK, self._handle_entity_attack)
        self.event_bus.on(Events.ENTITY_USE_ABILITY, self._handle_entity_use_ability)
        self.event_bus.on(Events.ENTITY_USE_ITEM, self._handle_entity_use_item)
        self.event_bus.on(Events.ENTITY_SKIP_TURN, self._handle_entity_skip_turn)
        self.event_bus.on(Events.ENTITY_FLEE, self._handle_entity_flee)
        self.event_bus.on(Events.ENTITY_DAMAGED, self._handle_entity_damaged)
        self.event_bus.on(Events.ENTITY_HEALED, self._handle_entity_healed)
        
        # Eventi UI
        self.event_bus.on(Events.UI_DIALOG_OPEN, self._handle_dialog_open)
        self.event_bus.on(Events.UI_DIALOG_CLOSE, self._handle_dialog_close)
        self.event_bus.on(Events.MENU_SELECTION, self._handle_menu_selection)
        
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
            self.ui.aggiorna_renderer(gioco)
            self.ui_aggiornata = True
            
            # Emetti evento di UI aggiornata
            self.emit_event(Events.UI_UPDATE, element="combattimento", state=self)
            
        # Gestione delle fasi di combattimento
        if self.fase == "inizializzazione":
            self._inizializza_combattimento()
            self.fase = "scelta"
            
        # Controlla fine combattimento
        if self.controlla_fine_combattimento(gioco):
            self.termina_combattimento()
        
    def _init_from_context(self, contesto):
        """
        Inizializzazione alternativa da un dizionario di contesto
        
        Args:
            contesto (dict): Il contesto del combattimento
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Pre-definisci metodi anche qui per sicurezza
        if not hasattr(self, 'esegui_attacco'):
            self.esegui_attacco = lambda *args, **kwargs: {"successo": False, "messaggio": "Metodo non ancora inizializzato"}
        
        gioco = contesto.get("world")
        # Inizializziamo la classe base
        try:
            super().__init__()
            # Imposta il contesto di gioco
            if gioco:
                self.set_game_context(gioco)
        except Exception as e:
            logger.error(f"Errore nell'inizializzazione della classe base: {e}")
            # Inizializzazione manuale degli attributi
            self.gioco = gioco
            self.callbacks = {}
            self.event_bus = None  # Non possiamo creare un EventBus qui
        
        # Impostazione degli attributi base
        self.partecipanti = contesto.get("partecipanti", [])
        self.turno_corrente = None
        self.round_corrente = 0
        self.in_corso = False
        self.tipo_incontro = contesto.get("tipo_incontro", "casuale")
        self.fase_corrente = "inizializzazione"
        self.target_selezionato = None
        self.messaggi = []
        self.world = contesto.get("world")
        
        # Creiamo gli oggetti azioni come fallback nel caso in cui l'importazione fallisca
        azioni_minime = type('AzioniMinime', (), {
            'attacco': lambda *args: {'successo': False, 'messaggio': 'Funzionalità non disponibile'},
            'difesa': lambda *args: {'successo': False, 'messaggio': 'Funzionalità non disponibile'},
            'esegui_attacco': lambda *args: {'successo': False, 'messaggio': 'Funzionalità non disponibile'},
            'azioni_disponibili': lambda *args: ['attacco', 'difesa', 'fuga'],
            'usa_abilita': lambda *args: {'successo': False, 'messaggio': 'Funzionalità non disponibile'},
            'usa_oggetto': lambda *args: {'successo': False, 'messaggio': 'Funzionalità non disponibile'},
            'passa_turno': lambda *args: {'successo': False, 'messaggio': 'Funzionalità non disponibile'},
            'determina_azione_ia': lambda *args: {'tipo': 'attacco', 'parametri': {}},
            'esegui_azione_ia': lambda *args: {'successo': False, 'messaggio': 'Funzionalità non disponibile'},
            'tenta_fuga': lambda *args: {'successo': False, 'messaggio': 'Funzionalità non disponibile'},
            'mostra_inventario': lambda *args: None,
            'mostra_opzioni_equipaggiamento': lambda *args: None,
            'cambia_equipaggiamento_item': lambda *args: None,
        })()
        
        gestore_turni_minimo = type('GestoreTurniMinimo', (), {
            'prossimo_turno': lambda *args: None,
            'inizializza_turni': lambda *args: None,
            'calcola_iniziativa': lambda *args: [],
            'passa_al_turno_successivo': lambda *args: None,
            'controlla_fine_combattimento': lambda *args: False,
            'determina_vincitore': lambda *args: 'nessuno'
        })()
        
        ui_minima = type('UIMinima', (), {
            'mostra_interfaccia': lambda *args: None,
            'aggiorna': lambda *args: None,
            'aggiorna_barre_hp': lambda *args: None,
            'mostra_menu_scelta': lambda *args: None,
            'aggiorna_renderer': lambda *args: None,
            'mostra_interfaccia_combattimento': lambda *args: None
        })()
        
        # Inizializza i moduli - con gestione fallback
        try:
            logger.info("Tentativo di importazione dei moduli di combattimento...")
            from states.combattimento.azioni import AzioniCombattimento
            from states.combattimento.turni import GestoreTurni
            from states.combattimento.ui import UICombattimento
            
            # Inizializza i moduli
            logger.info("Inizializzazione AzioniCombattimento...")
            self.azioni = AzioniCombattimento(self)
            # Esponi subito i metodi dell'oggetto azioni direttamente nello stato per compatibilità
            self.esegui_attacco = lambda *args, **kwargs: self.azioni.esegui_attacco(*args, **kwargs)
            self.usa_abilita = lambda *args, **kwargs: self.azioni.usa_abilita(*args, **kwargs)
            self.usa_oggetto = lambda *args, **kwargs: self.azioni.usa_oggetto(*args, **kwargs)
            self.passa_turno = lambda *args, **kwargs: self.azioni.passa_turno(*args, **kwargs)
            self.determina_azione_ia = lambda *args, **kwargs: self.azioni.determina_azione_ia(*args, **kwargs)
            self.esegui_azione_ia = lambda *args, **kwargs: self.azioni.esegui_azione_ia(*args, **kwargs)
            
            logger.info("Inizializzazione GestoreTurni...")
            self.gestore_turni = GestoreTurni(self)
            logger.info("Inizializzazione UICombattimento...")
            self.ui = UICombattimento(self)
            logger.info("Moduli di combattimento inizializzati correttamente")
        except ImportError as e:
            logger.error(f"Impossibile importare i moduli di combattimento: {e}")
            # Usa oggetti minimi in caso di fallimento
            self.azioni = azioni_minime
            # Esponi i metodi minimi
            self.esegui_attacco = lambda *args, **kwargs: self.azioni.esegui_attacco(*args, **kwargs)
            self.usa_abilita = lambda *args, **kwargs: self.azioni.usa_abilita(*args, **kwargs)
            self.usa_oggetto = lambda *args, **kwargs: self.azioni.usa_oggetto(*args, **kwargs)
            self.passa_turno = lambda *args, **kwargs: self.azioni.passa_turno(*args, **kwargs)
            self.determina_azione_ia = lambda *args, **kwargs: self.azioni.determina_azione_ia(*args, **kwargs)
            self.esegui_azione_ia = lambda *args, **kwargs: self.azioni.esegui_azione_ia(*args, **kwargs)
            
            self.gestore_turni = gestore_turni_minimo
            self.ui = ui_minima
        except Exception as e:
            logger.error(f"Errore nell'inizializzazione dei moduli di combattimento: {e}")
            # Usa oggetti minimi in caso di fallimento
            self.azioni = azioni_minime
            # Esponi i metodi minimi
            self.esegui_attacco = lambda *args, **kwargs: self.azioni.esegui_attacco(*args, **kwargs)
            self.usa_abilita = lambda *args, **kwargs: self.azioni.usa_abilita(*args, **kwargs)
            self.usa_oggetto = lambda *args, **kwargs: self.azioni.usa_oggetto(*args, **kwargs)
            self.passa_turno = lambda *args, **kwargs: self.azioni.passa_turno(*args, **kwargs)
            self.determina_azione_ia = lambda *args, **kwargs: self.azioni.determina_azione_ia(*args, **kwargs)
            self.esegui_azione_ia = lambda *args, **kwargs: self.azioni.esegui_azione_ia(*args, **kwargs)
            
            self.gestore_turni = gestore_turni_minimo
            self.ui = ui_minima
        
        # Converti partecipanti in ID se sono oggetti
        self.partecipanti = [p.id if hasattr(p, 'id') else p for p in self.partecipanti]
        
        # Metodo per inizializzare il combattimento
        self.inizializza_combattimento = self._inizializza_combattimento
        
        # Metodo per ottenere azioni disponibili
        self.get_azioni_disponibili = self._get_azioni_disponibili
        
        # Se l'inizializzazione ha fallito, assicuriamoci di avere un oggetto azioni
        if not hasattr(self, 'azioni') or self.azioni is None:
            logger.warning("Attributo 'azioni' ancora mancante, creazione manuale finale...")
            self.azioni = azioni_minime
            self.gestore_turni = gestore_turni_minimo
            self.ui = ui_minima
            
            # Assicuriamoci che i metodi siano esposti anche qui
            self.esegui_attacco = lambda *args, **kwargs: self.azioni.esegui_attacco(*args, **kwargs)
            self.usa_abilita = lambda *args, **kwargs: self.azioni.usa_abilita(*args, **kwargs)
            self.usa_oggetto = lambda *args, **kwargs: self.azioni.usa_oggetto(*args, **kwargs)
            self.passa_turno = lambda *args, **kwargs: self.azioni.passa_turno(*args, **kwargs)
            self.determina_azione_ia = lambda *args, **kwargs: self.azioni.determina_azione_ia(*args, **kwargs)
            self.esegui_azione_ia = lambda *args, **kwargs: self.azioni.esegui_azione_ia(*args, **kwargs)
        
        # Tenta di inizializzare i comandi
        try:
            if hasattr(self, '_init_commands'):
                self._init_commands()
        except Exception as e:
            logger.error(f"Errore in _init_commands: {e}")
            # Fallback semplice per i comandi
            self.commands = {
                "attacco": self.esegui_attacco,
                "usa_oggetto": self.azioni.mostra_inventario,
                "cambia_equipaggiamento": self.azioni.mostra_opzioni_equipaggiamento,
                "tenta_fuga": self.azioni.tenta_fuga
            }
            
        logger.info("Oggetto CombattimentoState inizializzato correttamente da contesto")
        
    def _inizializza_combattimento(self):
        """Inizializza il combattimento con il sistema di iniziativa"""
        self.in_corso = True
        self.round_corrente = 1
        self.fase_corrente = "iniziativa"
        
        # Calcola iniziativa per tutti i partecipanti
        for p_id in self.partecipanti:
            entita = self.world.get_entity(p_id)
            if entita:
                # Calcola valore iniziativa basato su destrezza
                destrezza = getattr(entita, "destrezza", 10)
                mod_destrezza = (destrezza - 10) // 2
                tiro_dado = Dado(20).tira() + mod_destrezza
                setattr(entita, "iniziativa", tiro_dado)
                
        # Determina l'ordine di iniziativa
        self.ordine_iniziativa = sorted(
            self.partecipanti,
            key=lambda p_id: getattr(self.world.get_entity(p_id), "iniziativa", 0),
            reverse=True
        )
        
        # Imposta il turno al primo giocatore nella lista di iniziativa
        if self.ordine_iniziativa:
            self.turno_corrente = self.ordine_iniziativa[0]
            self.fase_corrente = "azione"
            
    def _get_azioni_disponibili(self, entita_id, target_id=None):
        """
        Ottiene le azioni disponibili per un'entità
        
        Args:
            entita_id (str): ID dell'entità
            target_id (str, optional): ID del bersaglio
        
        Returns:
            list: Lista di azioni disponibili
        """
        azioni_base = ["attacco", "difesa", "movimento"]
        
        # Ottieni l'entità
        entita = self.world.get_entity(entita_id)
        if not entita:
            return []
            
        # Se l'entità ha abilità speciali, aggiungile
        if hasattr(entita, "abilita_speciali") and entita.abilita_speciali:
            return azioni_base + list(entita.abilita_speciali.keys())
            
        return azioni_base
        
    def _init_commands(self):
        """Inizializza i comandi disponibili per questo stato"""
        self.commands = {
            "attacco": self.esegui_attacco,
            "usa_oggetto": self.azioni.mostra_inventario,
            "cambia_equipaggiamento": self.azioni.mostra_opzioni_equipaggiamento,
            "tenta_fuga": self.azioni.tenta_fuga
        }
        
    def esegui(self, gioco):
        """
        Esecuzione dello stato di combattimento.
        Mantenuta per retrocompatibilità.
        
        Args:
            gioco: Istanza del gioco
        """
        # Salva il contesto di gioco
        self.set_game_context(gioco)
        
        # Aggiorna il renderer grafico se necessario
        if not self.ui_aggiornata:
            self.ui.aggiorna_renderer(gioco)
            self.ui_aggiornata = True
        
        # Inizializza il combattimento se necessario
        if getattr(self, 'fase', None) == "inizializzazione":
            self._inizializza_combattimento()
            self.fase = "scelta"
        
        # Mostra interfaccia di combattimento
        self.ui.mostra_interfaccia_combattimento(gioco)
        
        # Se siamo nel turno del giocatore, mostra menu di scelta
        if self.is_player_turn():
            self.ui.mostra_menu_scelta(gioco)
        else:
            # Altrimenti, esegui turno IA
            self.esegui_turno_ia(gioco)
            
        # Aggiungi chiamata a update per integrazione con EventBus
        self.update(0.033)  # Valore dt predefinito
        
        # Elabora gli eventi UI
        super().esegui(gioco)
        
    # Handler eventi
    def _handle_combat_start(self, **kwargs):
        """Handler per inizio combattimento"""
        gioco = self.gioco
        if not gioco:
            return
            
        self._inizializza_combattimento()
        self.fase = "scelta"
        
        # Aggiorna UI
        self.ui_aggiornata = False
    
    def _handle_combat_end(self, winner=None, **kwargs):
        """Handler per fine combattimento"""
        gioco = self.gioco
        if not gioco:
            return
            
        self.termina_combattimento()
    
    def _handle_next_turn(self, **kwargs):
        """Handler per passaggio al turno successivo"""
        gioco = self.gioco
        if not gioco:
            return
            
        self.gestore_turni.passa_al_turno_successivo()
        
        # Aggiorna UI
        self.ui_aggiornata = False
    
    def _handle_entity_attack(self, attacker_id=None, target_id=None, **kwargs):
        """Handler per attacco di un'entità"""
        gioco = self.gioco
        if not gioco or not attacker_id or not target_id:
            return
            
        # Ottieni le entità
        attacker = gioco.get_entity(attacker_id)
        target = gioco.get_entity(target_id)
        
        if not attacker or not target:
            return
            
        # Esegui attacco
        risultato = self.esegui_attacco(gioco, attacker, target)
        
        # Emetti evento di danno se l'attacco ha avuto successo
        if risultato.get("successo", False) and "danno" in risultato:
            self.emit_event(Events.ENTITY_DAMAGED, 
                          entity_id=target_id, 
                          amount=risultato["danno"],
                          attacker_id=attacker_id)
        
        # Aggiorna UI
        self.ui_aggiornata = False
    
    def _handle_entity_use_ability(self, entity_id=None, ability_id=None, target_id=None, **kwargs):
        """Handler per uso abilità di un'entità"""
        gioco = self.gioco
        if not gioco or not entity_id or not ability_id:
            return
            
        # Ottieni l'entità
        entity = gioco.get_entity(entity_id)
        
        if not entity:
            return
            
        # Ottieni il target se specificato
        target = None
        if target_id:
            target = gioco.get_entity(target_id)
            
        # Usa abilità
        risultato = self.usa_abilita(gioco, entity, ability_id, target)
        
        # Aggiorna UI
        self.ui_aggiornata = False
    
    def _handle_entity_use_item(self, entity_id=None, item_id=None, target_id=None, **kwargs):
        """Handler per uso oggetto di un'entità"""
        gioco = self.gioco
        if not gioco or not entity_id or not item_id:
            return
            
        # Ottieni l'entità
        entity = gioco.get_entity(entity_id)
        
        if not entity:
            return
            
        # Ottieni il target se specificato
        target = None
        if target_id:
            target = gioco.get_entity(target_id)
            
        # Usa oggetto
        risultato = self.usa_oggetto(gioco, entity, item_id, target)
        
        # Aggiorna UI
        self.ui_aggiornata = False
    
    def _handle_entity_skip_turn(self, entity_id=None, **kwargs):
        """Handler per salto turno di un'entità"""
        gioco = self.gioco
        if not gioco or not entity_id:
            return
            
        # Ottieni l'entità
        entity = gioco.get_entity(entity_id)
        
        if not entity:
            return
            
        # Passa turno
        self.passa_turno(gioco, entity)
        
        # Passa al turno successivo
        self.emit_event(Events.COMBAT_NEXT_TURN)
        
        # Aggiorna UI
        self.ui_aggiornata = False
    
    def _handle_entity_flee(self, entity_id=None, **kwargs):
        """Handler per fuga di un'entità"""
        gioco = self.gioco
        if not gioco or not entity_id:
            return
            
        # Ottieni l'entità
        entity = gioco.get_entity(entity_id)
        
        if not entity:
            return
            
        # Tenta fuga
        risultato = self.azioni.tenta_fuga(gioco, entity)
        
        # Se la fuga ha successo, termina il combattimento
        if risultato.get("successo", False):
            self.emit_event(Events.COMBAT_END, winner="fuga")
        
        # Aggiorna UI
        self.ui_aggiornata = False
    
    def _handle_entity_damaged(self, entity_id=None, amount=0, **kwargs):
        """Handler per danno a un'entità"""
        gioco = self.gioco
        if not gioco or not entity_id:
            return
            
        # Aggiorna UI
        self.ui_aggiornata = False
    
    def _handle_entity_healed(self, entity_id=None, amount=0, **kwargs):
        """Handler per guarigione di un'entità"""
        gioco = self.gioco
        if not gioco or not entity_id:
            return
            
        # Aggiorna UI
        self.ui_aggiornata = False
    
    def _handle_dialog_open(self, dialog_id=None, **kwargs):
        """Handler per apertura dialogo"""
        pass
    
    def _handle_dialog_close(self, **kwargs):
        """Handler per chiusura dialogo"""
        pass
    
    def _handle_menu_selection(self, choice=None, menu_id=None, **kwargs):
        """Handler per selezione menu"""
        if not choice or menu_id != "combattimento":
            return
            
        gioco = self.gioco
        if not gioco:
            return
            
        # Processa la scelta in base all'azione
        if choice == "Attacco":
            # Emetti evento per mostrare selezione target
            self.emit_event(Events.UI_DIALOG_OPEN, 
                          dialog_id="seleziona_target",
                          title="Seleziona bersaglio", 
                          message="Scegli un bersaglio da attaccare:", 
                          options=self._get_target_options())
        elif choice == "Abilità":
            # Emetti evento per mostrare selezione abilità
            abilita_disponibili = self.get_abilita_disponibili()
            self.emit_event(Events.UI_DIALOG_OPEN, 
                          dialog_id="seleziona_abilita",
                          title="Seleziona abilità", 
                          message="Scegli un'abilità da utilizzare:", 
                          options=abilita_disponibili)
        elif choice == "Oggetti":
            # Emetti evento per mostrare selezione oggetti
            self.azioni.mostra_inventario(gioco, gioco.giocatore)
        elif choice == "Fuga":
            # Emetti evento di fuga
            self.emit_event(Events.ENTITY_FLEE, entity_id=gioco.giocatore.id)
        elif choice == "Passa":
            # Emetti evento di salto turno
            self.emit_event(Events.ENTITY_SKIP_TURN, entity_id=gioco.giocatore.id)

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
        dialog_id = event.data.get("dialog_id", "")
        
        if not choice:
            return
            
        # Converti in formato nuovo
        self._handle_menu_selection(choice=choice, menu_id="combattimento", dialog_id=dialog_id)
        
    def controlla_fine_combattimento(self, gioco):
        """
        Verifica se il combattimento è terminato.
        
        Args:
            gioco: L'istanza del gioco
            
        Returns:
            bool: True se il combattimento è terminato, False altrimenti
        """
        giocatore = gioco.giocatore
        
        if giocatore.hp <= 0:
            gioco.io.mostra_messaggio(f"\n{self.avversario.nome} ti ha sconfitto! Sei ferito gravemente...")
            giocatore.hp = 1  # Invece di morire, il giocatore resta con 1 HP
            if gioco.stato_corrente():
                gioco.pop_stato()
            return True
            
        if self.avversario.hp <= 0:
            gioco.io.mostra_messaggio(f"\nHai sconfitto {self.avversario.nome}!")
            
            # Gestisci la ricompensa
            oro_guadagnato = min(self.avversario.oro, 20)  # Max 20 monete
            self.avversario.oro -= oro_guadagnato
            giocatore.oro += oro_guadagnato
            
            gioco.io.mostra_messaggio(f"Hai guadagnato {oro_guadagnato} monete d'oro!")
            
            # Controlla se c'è un oggetto da saccheggiare
            if hasattr(self.avversario, 'inventario') and self.avversario.inventario and len(self.avversario.inventario) > 0:
                item = self.avversario.inventario[0]  # Prendi il primo oggetto
                giocatore.aggiungi_item(item)
                gioco.io.mostra_messaggio(f"Hai ottenuto: {item.nome}")
            
            # Guadagna esperienza - Corretto per utilizzare valore_esperienza
            if hasattr(self.avversario, 'valore_esperienza'):
                exp_guadagnata = self.avversario.valore_esperienza * (1 + getattr(self.avversario, 'livello', 0))
            else:
                # Valore predefinito se il nemico non ha l'attributo valore_esperienza
                exp_guadagnata = 25 * (1 + getattr(self.avversario, 'livello', 0))
                
            if giocatore.guadagna_esperienza(exp_guadagnata, gioco):
                gioco.io.mostra_messaggio(f"Hai guadagnato {exp_guadagnata} punti esperienza e sei salito di livello!")
            else:
                gioco.io.mostra_messaggio(f"Hai guadagnato {exp_guadagnata} punti esperienza!")
            
            if gioco.stato_corrente():
                gioco.pop_stato()
            return True
            
        return False
    
    def termina_combattimento(self, forzato=False):
        """
        Termina il combattimento, in modo forzato o naturale.
        
        Args:
            forzato (bool): Se True, termina il combattimento ignorando eventuali condizioni
            
        Returns:
            bool: True se il combattimento è stato terminato, False altrimenti
        """
        # Segna lo stato come non più in corso
        self.in_corso = False
        
        # Ripristina gli stati delle entità se necessario
        for p_id in self.partecipanti:
            if self.world:
                entita = self.world.get_entity(p_id)
                if entita:
                    # Rimuovi eventuali stati temporanei
                    if hasattr(entita, "in_combattimento"):
                        entita.in_combattimento = False
        
        # Registra nel log la fine del combattimento
        messaggio = "Combattimento terminato" + (" forzatamente" if forzato else "")
        self.messaggi.append(messaggio)
        
        # Comunica la fine del combattimento al gestore turni
        if hasattr(self, "gestore_turni") and self.gestore_turni:
            # Reset del turno
            self.turno_corrente = None
        
        return True
    
    @classmethod
    def from_dict(cls, data, game=None):
        """
        Crea un'istanza di CombattimentoState da un dizionario.
        
        Args:
            data (dict): Dizionario con i dati dello stato
            game: Istanza del gioco (opzionale)
            
        Returns:
            CombattimentoState: Nuova istanza di CombattimentoState
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Implementazione cache per evitare reinizializzazioni ripetute
        # Utilizziamo un ID univoco basato sul contenuto di data per il caching
        cache_id = None
        if isinstance(data, dict):
            try:
                # Creiamo un ID univoco basato su turno_corrente, round_corrente e partecipanti
                partecipanti_str = "_".join(str(p) for p in data.get("partecipanti", []))
                turno = data.get("turno_corrente", "")
                round_num = data.get("round_corrente", 0)
                cache_id = f"{partecipanti_str}_{turno}_{round_num}"
                
                # Verifichiamo se l'oggetto è già in cache
                if hasattr(cls, '_instances_cache') and cache_id in cls._instances_cache:
                    logger.info(f"Stato di combattimento recuperato dalla cache (ID: {cache_id})")
                    return cls._instances_cache[cache_id]
            except Exception as e:
                logger.warning(f"Errore nella generazione dell'ID cache: {e}")
                cache_id = None
        
        # Creiamo gli oggetti azioni come fallback nel caso in cui l'importazione fallisca
        azioni_minime = type('AzioniMinime', (), {
            'attacco': lambda *args: {'successo': False, 'messaggio': 'Funzionalità non disponibile'},
            'difesa': lambda *args: {'successo': False, 'messaggio': 'Funzionalità non disponibile'},
            'esegui_attacco': lambda *args: {'successo': False, 'messaggio': 'Funzionalità non disponibile'},
            'azioni_disponibili': lambda *args: ['attacco', 'difesa', 'fuga'],
            'usa_abilita': lambda *args: {'successo': False, 'messaggio': 'Funzionalità non disponibile'},
            'usa_oggetto': lambda *args: {'successo': False, 'messaggio': 'Funzionalità non disponibile'},
            'passa_turno': lambda *args: {'successo': False, 'messaggio': 'Funzionalità non disponibile'},
            'determina_azione_ia': lambda *args: {'tipo': 'attacco', 'parametri': {}},
            'esegui_azione_ia': lambda *args: {'successo': False, 'messaggio': 'Funzionalità non disponibile'},
            'tenta_fuga': lambda *args: {'successo': False, 'messaggio': 'Funzionalità non disponibile'},
            'mostra_inventario': lambda *args: None,
            'mostra_opzioni_equipaggiamento': lambda *args: None,
            'cambia_equipaggiamento_item': lambda *args: None,
        })()
        
        gestore_turni_minimo = type('GestoreTurniMinimo', (), {
            'prossimo_turno': lambda *args: None,
            'inizializza_turni': lambda *args: None,
            'calcola_iniziativa': lambda *args: [],
            'passa_al_turno_successivo': lambda *args: None,
            'controlla_fine_combattimento': lambda *args: False,
            'determina_vincitore': lambda *args: 'nessuno'
        })()
        
        ui_minima = type('UIMinima', (), {
            'mostra_interfaccia': lambda *args: None,
            'aggiorna': lambda *args: None,
            'aggiorna_barre_hp': lambda *args: None,
            'mostra_menu_scelta': lambda *args: None,
            'aggiorna_renderer': lambda *args: None,
            'mostra_interfaccia_combattimento': lambda *args: None
        })()
        
        # Importo qui i moduli necessari con gestione degli errori
        AzioniCombattimento = None
        GestoreTurni = None
        UICombattimento = None
        
        try:
            from entities.nemico import Nemico
            from entities.npg import NPG
            from states.combattimento.azioni import AzioniCombattimento
            from states.combattimento.turni import GestoreTurni
            from states.combattimento.ui import UICombattimento
        except ImportError as e:
            logger.error(f"Errore nell'importazione per from_dict: {e}")
            # Creiamo delle classi placeholder
            Nemico = type('Nemico', (), {'__init__': lambda self, nome: setattr(self, 'nome', nome)})
            NPG = type('NPG', (), {'__init__': lambda self, nome: setattr(self, 'nome', nome)})
            
            # Definiamo le funzioni factory per i fallback
            def _create_azioni_minime(state):
                return azioni_minime
                
            def _create_gestore_turni_minimo(state):
                return gestore_turni_minimo
                
            def _create_ui_minima(state):
                return ui_minima
                
            AzioniCombattimento = _create_azioni_minime
            GestoreTurni = _create_gestore_turni_minimo
            UICombattimento = _create_ui_minima
        
        # Controlla se i dati sono per la nuova versione del combattimento
        if isinstance(data, dict) and "partecipanti" in data:
            # Crea l'istanza ma non chiama __init__
            stato = cls.__new__(cls)
            
            # Inizializza i metodi essenziali per evitare errori
            stato.esegui_attacco = lambda *args, **kwargs: {"successo": False, "messaggio": "Metodo non ancora inizializzato"}
            stato.usa_abilita = lambda *args, **kwargs: {"successo": False, "messaggio": "Metodo non ancora inizializzato"}
            stato.usa_oggetto = lambda *args, **kwargs: {"successo": False, "messaggio": "Metodo non ancora inizializzato"}
            stato.passa_turno = lambda *args, **kwargs: {"successo": False, "messaggio": "Metodo non ancora inizializzato"}
            stato.determina_azione_ia = lambda *args, **kwargs: {"successo": False, "messaggio": "Metodo non ancora inizializzato"}
            stato.esegui_azione_ia = lambda *args, **kwargs: {"successo": False, "messaggio": "Metodo non ancora inizializzato"}
            
            # Inizializza gli attributi base
            stato.partecipanti = data.get("partecipanti", [])
            stato.turno_corrente = data.get("turno_corrente")
            stato.round_corrente = data.get("round_corrente", 0)
            stato.in_corso = data.get("in_corso", False)
            stato.tipo_incontro = data.get("tipo_incontro", "casuale")
            stato.fase_corrente = data.get("fase_corrente", "inizializzazione")
            stato.target_selezionato = data.get("target_selezionato")
            stato.messaggi = data.get("messaggi", [])
            stato.world = game
            stato.fase = data.get("fase", "scelta")
            stato.dati_temporanei = data.get("dati_temporanei", {})
            
            # Inizializza i moduli solo se non sono già inizializzati
            if not hasattr(stato, 'azioni') or stato.azioni is None:
                try:
                    # Inizializza prima i moduli separati per evitare problemi in _init_commands
                    logger.info("Inizializzazione AzioniCombattimento...")
                    stato.azioni = AzioniCombattimento(stato)
                    logger.info("Inizializzazione GestoreTurni...")
                    stato.gestore_turni = GestoreTurni(stato)
                    logger.info("Inizializzazione UICombattimento...")
                    stato.ui = UICombattimento(stato)
                    logger.info("Moduli inizializzati correttamente in from_dict")
                except Exception as e:
                    logger.error(f"Errore nell'inizializzazione dei moduli in from_dict: {e}")
                    logger.info("Utilizzo moduli fallback...")
                    stato.azioni = azioni_minime
                    stato.gestore_turni = gestore_turni_minimo
                    stato.ui = ui_minima
            else:
                logger.info("I moduli sono già inizializzati, salto l'inizializzazione ripetuta")
            
            # Converti partecipanti in ID se sono oggetti
            stato.partecipanti = [p.id if hasattr(p, 'id') else p for p in stato.partecipanti]
            
            # Aggiungi i metodi necessari se non già presenti
            if not hasattr(stato, 'inizializza_combattimento'):
                stato.inizializza_combattimento = stato._inizializza_combattimento
            if not hasattr(stato, 'get_azioni_disponibili'):
                stato.get_azioni_disponibili = stato._get_azioni_disponibili
            
            # Controllo finale per l'attributo azioni
            if not hasattr(stato, 'azioni') or stato.azioni is None:
                logger.warning("Attributo 'azioni' ancora mancante, creazione manuale finale...")
                stato.azioni = azioni_minime
                stato.gestore_turni = gestore_turni_minimo
                stato.ui = ui_minima
                
            # Esponi i metodi dell'oggetto azioni direttamente nello stato per compatibilità
            # solo se non sono già stati esposti
            if hasattr(stato, 'azioni') and not hasattr(stato, 'esegui_attacco'):
                # Crea wrapper per i metodi più importanti
                stato.esegui_attacco = lambda *args, **kwargs: stato.azioni.esegui_attacco(*args, **kwargs)
                stato.usa_abilita = lambda *args, **kwargs: stato.azioni.usa_abilita(*args, **kwargs)
                stato.usa_oggetto = lambda *args, **kwargs: stato.azioni.usa_oggetto(*args, **kwargs)
                stato.passa_turno = lambda *args, **kwargs: stato.azioni.passa_turno(*args, **kwargs)
                stato.determina_azione_ia = lambda *args, **kwargs: stato.azioni.determina_azione_ia(*args, **kwargs)
                stato.esegui_azione_ia = lambda *args, **kwargs: stato.azioni.esegui_azione_ia(*args, **kwargs)
            
            # Ora è sicuro inizializzare i comandi se non già inizializzati
            if hasattr(stato, '_init_commands') and not hasattr(stato, 'commands'):
                try:
                    stato._init_commands()
                except Exception as e:
                    logger.error(f"Errore in _init_commands: {e}")
                    # Fallback semplice per i comandi
                    stato.commands = {
                        "attacco": lambda *args: {'successo': False, 'messaggio': 'Funzionalità non disponibile'},
                        "usa_oggetto": lambda *args: {'successo': False, 'messaggio': 'Funzionalità non disponibile'},
                        "fuga": lambda *args: {'successo': False, 'messaggio': 'Funzionalità non disponibile'}
                    }
            
            # Memorizza l'istanza nella cache se abbiamo un ID valido
            if cache_id:
                if not hasattr(cls, '_instances_cache'):
                    cls._instances_cache = {}
                # Limita la dimensione della cache a 10 elementi
                if len(cls._instances_cache) > 10:
                    # Rimuovi una chiave casuale per fare spazio
                    import random
                    key_to_remove = random.choice(list(cls._instances_cache.keys()))
                    del cls._instances_cache[key_to_remove]
                # Aggiungi l'istanza corrente alla cache
                cls._instances_cache[cache_id] = stato
                logger.info(f"Stato di combattimento memorizzato nella cache (ID: {cache_id})")
                
            return stato
            
        # Se siamo qui, try o non è un dict o non ha "partecipanti"
        logger.warning("Formato dati non supportato in from_dict, creazione oggetto vuoto")
        
        # Crea un oggetto di fallback
        stato = cls.__new__(cls)
        
        # Inizializza i metodi essenziali per evitare errori
        stato.esegui_attacco = lambda *args, **kwargs: {"successo": False, "messaggio": "Metodo non ancora inizializzato"}
        stato.usa_abilita = lambda *args, **kwargs: {"successo": False, "messaggio": "Metodo non ancora inizializzato"}
        stato.usa_oggetto = lambda *args, **kwargs: {"successo": False, "messaggio": "Metodo non ancora inizializzato"}
        stato.passa_turno = lambda *args, **kwargs: {"successo": False, "messaggio": "Metodo non ancora inizializzato"}
        stato.determina_azione_ia = lambda *args, **kwargs: {"successo": False, "messaggio": "Metodo non ancora inizializzato"}
        stato.esegui_azione_ia = lambda *args, **kwargs: {"successo": False, "messaggio": "Metodo non ancora inizializzato"}
        
        # Aggiungi attributi minimi richiesti
        stato.partecipanti = []
        stato.turno_corrente = None
        stato.round_corrente = 0
        stato.in_corso = False
        stato.tipo_incontro = "casuale"
        stato.fase_corrente = "inizializzazione"
        stato.target_selezionato = None
        stato.messaggi = []
        stato.world = game
        stato.fase = "scelta"
        stato.dati_temporanei = {}
        
        # Aggiungi moduli minimi
        stato.azioni = azioni_minime
        stato.gestore_turni = gestore_turni_minimo
        stato.ui = ui_minima
        
        # Aggiungi metodi
        stato.inizializza_combattimento = lambda: None
        stato.get_azioni_disponibili = lambda *args: ["attacco", "difesa", "fuga"]
        
        # Esponi i metodi dell'oggetto azioni direttamente nello stato per compatibilità
        stato.esegui_attacco = lambda *args, **kwargs: stato.azioni.esegui_attacco(*args, **kwargs)
        stato.usa_abilita = lambda *args, **kwargs: stato.azioni.usa_abilita(*args, **kwargs)
        stato.usa_oggetto = lambda *args, **kwargs: stato.azioni.usa_oggetto(*args, **kwargs)
        stato.passa_turno = lambda *args, **kwargs: stato.azioni.passa_turno(*args, **kwargs)
        stato.determina_azione_ia = lambda *args, **kwargs: stato.azioni.determina_azione_ia(*args, **kwargs)
        stato.esegui_azione_ia = lambda *args, **kwargs: stato.azioni.esegui_azione_ia(*args, **kwargs)
        
        return stato
        
    def to_dict(self):
        """
        Converte l'istanza di CombattimentoState in un dizionario per il salvataggio.
        
        Returns:
            dict: Dizionario con i dati dello stato
        """
        # Verifica se è la nuova versione dello stato (con partecipanti)
        if hasattr(self, 'partecipanti'):
            data = {
                "partecipanti": self.partecipanti,
                "turno_corrente": self.turno_corrente,
                "round_corrente": self.round_corrente,
                "in_corso": self.in_corso,
                "tipo_incontro": self.tipo_incontro,
                "fase_corrente": self.fase_corrente,
                "target_selezionato": self.target_selezionato,
                "messaggi": self.messaggi,
                "fase": getattr(self, 'fase', "scelta"),
                "dati_temporanei": getattr(self, 'dati_temporanei', {})
            }
            return data
        
        # Vecchia versione dello stato
        data = {
            "turno": getattr(self, 'turno', 1),
            "fase": getattr(self, 'fase', "scelta"),
            "dati_temporanei": getattr(self, 'dati_temporanei', {})
        }
        
        # Salva l'avversario
        if self.avversario is not None:
            if hasattr(self.avversario, 'to_dict'):
                avversario_dict = self.avversario.to_dict()
                # Aggiungi un campo type per distinguere tra NPG e Nemico
                if self.npg_ostile is not None:
                    avversario_dict["type"] = "NPG"
                data["avversario"] = avversario_dict
        
        return data 