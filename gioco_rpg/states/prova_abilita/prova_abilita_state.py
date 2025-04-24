from states.base.enhanced_base_state import EnhancedBaseState
import core.events as Events
from util.dado import Dado
from entities.entita import ABILITA_ASSOCIATE


class ProvaAbilitaState(EnhancedBaseState):
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
        
        # Registra handler per eventi
        self._register_event_handlers()
        
    def _register_event_handlers(self):
        """Registra gli handler per eventi relativi a questo stato"""
        # Eventi di prova abilità
        self.event_bus.on(Events.ABILITA_SCELTA, self._handle_abilita_scelta)
        self.event_bus.on(Events.PROVA_ABILITA_INIZIA, self._handle_prova_inizia)
        self.event_bus.on(Events.PROVA_ABILITA_ESEGUI, self._handle_prova_esegui)
        self.event_bus.on(Events.PROVA_ABILITA_TERMINA, self._handle_prova_termina)
        self.event_bus.on(Events.PROVA_ABILITA_NPC_SELEZIONATO, self._handle_npc_selezionato)
        self.event_bus.on(Events.PROVA_ABILITA_OGGETTO_SELEZIONATO, self._handle_oggetto_selezionato)
        self.event_bus.on(Events.PROVA_ABILITA_DIFFICOLTA_IMPOSTATA, self._handle_difficolta_impostata)
        
        # Eventi UI
        self.event_bus.on(Events.UI_DIALOG_OPEN, self._handle_dialog_open)
        self.event_bus.on(Events.UI_DIALOG_CLOSE, self._handle_dialog_close)
        
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
        
        # Logica di aggiornamento specifica dello stato
        if not self.ui_aggiornata:
            from states.prova_abilita.ui import aggiorna_renderer
            aggiorna_renderer(self, gioco)
            self.ui_aggiornata = True
        
        # Mostra menu iniziale se non ne è già attivo uno
        if not self.menu_attivo:
            from states.prova_abilita.ui import esegui_menu_principale
            esegui_menu_principale(self, gioco)
            self.menu_attivo = "principale"
    
    def esegui(self, gioco):
        """
        Implementazione dell'esecuzione dello stato.
        Mantenuta per retrocompatibilità.
        
        Args:
            gioco: L'istanza del gioco
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
        
        # Aggiungi chiamata a update per integrazione con EventBus
        self.update(0.033)  # Valore dt predefinito
        
        # Elabora gli eventi UI
        super().esegui(gioco)
    
    # Handler per eventi
    def _handle_dialog_open(self, dialog=None, **kwargs):
        """Handler per apertura dialogo"""
        if not dialog:
            return
        # Implementa logica di apertura dialogo
    
    def _handle_dialog_close(self, **kwargs):
        """Handler per chiusura dialogo"""
        # Implementa logica di chiusura dialogo
    
    def _handle_abilita_scelta(self, abilita=None, **kwargs):
        """
        Handler per la scelta di un'abilità
        
        Args:
            abilita: L'abilità scelta
        """
        if not abilita:
            return
            
        self.abilita_scelta = abilita
        self.fase = "esecuzione"
        
        # Emetti evento per aggiornare UI
        self.emit_event(Events.UI_UPDATE, 
                      fase=self.fase, 
                      abilita_scelta=abilita)
        
    def _handle_prova_inizia(self, contesto=None, **kwargs):
        """
        Handler per l'inizio di una prova di abilità
        
        Args:
            contesto: Contesto opzionale per la prova
        """
        if contesto:
            self.contesto = contesto
            
        self.fase = "scegli_abilita"
        # Emetti evento per aggiornare UI
        self.emit_event(Events.UI_UPDATE, 
                      fase=self.fase,
                      messaggio="Seleziona un'abilità per la prova")
    
    def _handle_prova_esegui(self, difficolta=None, target_id=None, **kwargs):
        """
        Handler per l'esecuzione della prova
        
        Args:
            difficolta: Valore di difficoltà della prova
            target_id: ID opzionale del target della prova
        """
        gioco = self.gioco
        if not gioco or not self.abilita_scelta:
            return
            
        # Ottieni l'entità del giocatore
        giocatore = gioco.get_player_entity()
        
        # Ottieni il target se specificato
        target = None
        if target_id:
            target = gioco.get_entity(target_id)
        
        # Esegui la prova
        from states.prova_abilita.esecuzione import esegui_prova
        risultato = esegui_prova(self, gioco, giocatore, self.abilita_scelta, 
                               difficolta or 10, target)
        
        # Aggiorna lo stato
        self.fase = "risultato"
        self.dati_contestuali['risultato'] = risultato
        
        # Emetti evento con il risultato
        self.emit_event(Events.PROVA_ABILITA_RISULTATO, 
                      risultato=risultato,
                      fase=self.fase)
    
    def _handle_prova_termina(self, **kwargs):
        """Handler per la terminazione della prova"""
        self.contesto = {}
        self.abilita_scelta = None
        self.dati_contestuali = {}
        self.fase = "terminata"
        
        # Emetti evento per aggiornare UI
        self.emit_event(Events.UI_UPDATE, 
                      fase=self.fase,
                      terminata=True)
    
    def _handle_npc_selezionato(self, npg_id=None, **kwargs):
        """
        Handler per la selezione di un NPG
        
        Args:
            npg_id: ID dell'NPG selezionato
        """
        if not npg_id:
            return
            
        gioco = self.gioco
        if not gioco:
            return
        
        # Ottieni l'NPG
        npg = gioco.get_entity(npg_id)
        if not npg:
            return
            
        self.dati_contestuali["target_id"] = npg_id
        self.dati_contestuali["target_nome"] = npg.nome if hasattr(npg, "nome") else f"NPG {npg_id}"
        
        # Aggiorna la fase in base al contesto
        if self.dati_contestuali.get("tipo_prova") == "confronto":
            self.fase = "scegli_abilita"
        else:
            self.fase = "scegli_abilita_npg"
            
        # Emetti evento per aggiornare UI
        self.emit_event(Events.UI_UPDATE, 
                      fase=self.fase,
                      messaggio=f"NPG selezionato: {self.dati_contestuali['target_nome']}",
                      target=self.dati_contestuali['target_nome'])
    
    def _handle_oggetto_selezionato(self, oggetto_id=None, **kwargs):
        """
        Handler per la selezione di un oggetto
        
        Args:
            oggetto_id: ID dell'oggetto selezionato
        """
        if not oggetto_id:
            return
            
        gioco = self.gioco
        if not gioco:
            return
        
        # Ottieni l'oggetto
        oggetto = gioco.get_entity(oggetto_id)
        if not oggetto:
            return
            
        self.dati_contestuali["target_id"] = oggetto_id
        self.dati_contestuali["target_nome"] = oggetto.nome if hasattr(oggetto, "nome") else f"Oggetto {oggetto_id}"
        self.fase = "scegli_abilita_oggetto"
        
        # Emetti evento per aggiornare UI
        self.emit_event(Events.UI_UPDATE, 
                      fase=self.fase,
                      messaggio=f"Oggetto selezionato: {self.dati_contestuali['target_nome']}",
                      target=self.dati_contestuali['target_nome'])
    
    def _handle_difficolta_impostata(self, difficolta=None, **kwargs):
        """
        Handler per l'impostazione della difficoltà
        
        Args:
            difficolta: Il valore di difficoltà impostato
        """
        if not difficolta:
            return
            
        try:
            difficolta = int(difficolta)
            if difficolta < 5 or difficolta > 30:
                return
        except ValueError:
            return
            
        # Aggiorna lo stato con la difficoltà impostata
        self.dati_contestuali["difficolta"] = difficolta
        self.fase = "esegui_prova"
        
        # Emetti evento per aggiornare UI
        self.emit_event(Events.UI_UPDATE, 
                      fase=self.fase,
                      messaggio=f"Difficoltà impostata a {difficolta}. Esecuzione prova in corso...",
                      in_corso=True)
        
        # Esegui la prova
        self.emit_event(Events.PROVA_ABILITA_ESEGUI,
                       difficolta=difficolta,
                       target_id=self.dati_contestuali.get("target_id"))
    
    # Metodi convertiti per utilizzare eventi
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
        """
        Gestisce gli effetti del successo nella prova.
        Wrapper per retrocompatibilità che ora emette un evento.
        """
        # Emetti evento
        self.emit_event(Events.PROVA_ABILITA_RISULTATO, 
                      esito="successo", 
                      abilita=abilita)
        
        # Mantieni per retrocompatibilità
        from states.prova_abilita.esecuzione import gestisci_successo
        gestisci_successo(self, gioco, abilita)
            
    def _gestisci_fallimento(self, gioco, abilita):
        """
        Gestisce gli effetti del fallimento nella prova.
        Wrapper per retrocompatibilità che ora emette un evento.
        """
        # Emetti evento
        self.emit_event(Events.PROVA_ABILITA_RISULTATO, 
                      esito="fallimento", 
                      abilita=abilita)
        
        # Mantieni per retrocompatibilità
        from states.prova_abilita.esecuzione import gestisci_fallimento
        gestisci_fallimento(self, gioco, abilita)
    
    def _gestisci_successo_npg(self, gioco, abilita, npg):
        """
        Gestisce gli effetti del successo nella prova contro un NPG.
        Wrapper per retrocompatibilità che ora emette un evento.
        """
        # Emetti evento
        self.emit_event(Events.PROVA_ABILITA_RISULTATO, 
                      esito="successo", 
                      abilita=abilita,
                      target_id=npg.id if hasattr(npg, "id") else None)
        
        # Mantieni per retrocompatibilità
        from states.prova_abilita.esecuzione import gestisci_successo_npg
        gestisci_successo_npg(self, gioco, abilita, npg)
    
    def _gestisci_fallimento_npg(self, gioco, abilita, npg):
        """
        Gestisce il fallimento di una prova contro un NPG.
        Wrapper per retrocompatibilità che ora emette un evento.
        """
        # Emetti evento
        self.emit_event(Events.PROVA_ABILITA_RISULTATO, 
                      esito="fallimento", 
                      abilita=abilita,
                      target_id=npg.id if hasattr(npg, "id") else None)
        
        # Mantieni per retrocompatibilità
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