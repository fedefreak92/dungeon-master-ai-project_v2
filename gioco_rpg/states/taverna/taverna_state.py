from states.mappa.mappa_state import MappaState
from states.dialogo import DialogoState
# from ઘટનાઓ.jogador_event_handler import JogadorEventHandler # Esempio, potrebbe non essere corretto - COMMENTATO
from . import taverna_menu_handlers, taverna_ui_handlers # Handler specifici
import logging

logger = logging.getLogger(__name__)

class TavernaState(MappaState):
    """
    Classe che rappresenta lo stato della taverna.
    Ora è una specializzazione leggera di MappaState, focalizzata
    su comportamenti unici della taverna che non sono gestibili
    dalla configurazione JSON o dagli handler generici/dinamici di MappaState.
    """
    
    def __init__(self, nome_luogo="taverna", game_state_manager=None, stato_origine=None):
        """
        Inizializza lo stato della Taverna.
        
        Args:
            nome_luogo: Il nome del luogo (opzionale, default "taverna").
            game_state_manager: Il gestore degli stati del gioco. Se MappaState lo passa
                                al costruttore di EnhancedBaseState, sarà disponibile.
            stato_origine: Lo stato da cui si proviene (opzionale).
        """
        super().__init__(nome_luogo, game_state_manager, stato_origine)
        self.nome_stato = "luogo_taverna" # Sovrascrive quello di MappaState se necessario
        self.prima_visita = True  # <<< AGGIUNTO INIZIALIZZAZIONE
        self.personaggi_specifici = ["Oste", "Avventore Misterioso"] # Esempio
        self.oggetti_specifici = ["Boccale di birra", "Vecchia mappa"]
        # Carica o definisci NPG specifici, oggetti, menu per la taverna
        self._carica_dati_specifici_taverna()
        logger.info(f"TavernaState '{self.nome_stato}' inizializzato.")
        if self.game_state_manager:
            logger.info("GameStateManager è disponibile in TavernaState.")
        else:
            logger.warning("GameStateManager NON è disponibile in TavernaState.")

    def _carica_dati_specifici_taverna(self):
        # Qui potresti caricare NPC come "Oste", oggetti interattivi specifici della taverna,
        # configurare menu speciali, ecc.
        # Esempio:
        # self.npg_presenti["Oste"] = self.gioco.npg_manager.crea_npc("oste_taverna")
        # self.oggetti_interattivi["bancone"] = OggettoInterattivo("Bancone", "Un bancone di legno massiccio.")
        pass

    def enter(self):
        """
        Chiamato quando si entra nello stato Taverna.
        """
        super().enter() # Chiama l'enter della classe base (MappaState/EnhancedBaseState)
        logger.info(f"Entrando in TavernaState: {self.nome_luogo}")
        if self.prima_visita:
            self.gioco.io.mostra_messaggio("Entri nella taverna. L'aria è densa di fumo e risate.")
            # self.prima_visita = False # Commentato per ora, gestisci la logica di prima visita come preferisci
        else:
            self.gioco.io.mostra_messaggio("Torni nella taverna.")
        # Logica aggiuntiva all'ingresso nella taverna
        # Ad esempio, mostra il menu principale della taverna
        if hasattr(self.ui_handler_instance, 'mostra_menu_principale'):
            self.ui_handler_instance.mostra_menu_principale(self, self.gioco)
        
        logger.debug(f"Entrato in TavernaState (Luogo: {self.nome_luogo}). UI Handler: {type(self.ui_handler_instance).__name__}, Menu Handler: {type(self.menu_handler_instance).__name__}")

    def exit(self):
        super().exit()
        logger.info(f"Uscendo da TavernaState: {self.nome_luogo}")
        # Logica all'uscita dalla taverna

    def update(self, dt):
        super().update(dt)
        # Logica di aggiornamento specifica della taverna, se necessaria

    # Potresti sovrascrivere _handle_azione_specifica_luogo per azioni uniche della taverna
    def _handle_azione_specifica_luogo(self, giocatore, azione_id: str, context: dict):
        logger.debug(f"[TavernaState] Ricevuta azione specifica: {azione_id} con contesto {context}")
        if azione_id == "ORDINA_BEVANDA":
            # Logica per ordinare una bevanda
            bevanda = context.get("bevanda", "birra")
            self.gioco.io.mostra_messaggio(f"{giocatore.nome} ordina una {bevanda}.")
            # ... (decrementa oro, aggiungi effetto, ecc.)
            self.event_bus.emit("BEVANDA_ORDINATA", giocatore_id=giocatore.id, tipo_bevanda=bevanda)
            return {"success": True, "message": f"Hai ordinato una {bevanda}"}
        elif azione_id == "GIOCO_DADI":
            # Logica per un minigioco di dadi
            self.gioco.io.mostra_messaggio(f"{giocatore.nome} decide di giocare a dadi.")
            # ... (avvia stato minigioco, ecc.)
            # self.gioco.push_stato(GiocoDadiState(self))
            return {"success": True, "message": "Ti prepari a lanciare i dadi..."}
        else:
            # Se l'azione non è gestita qui, chiama l'implementazione della classe base (MappaState)
            return super()._handle_azione_specifica_luogo(giocatore, azione_id, context)

    # ... altri metodi specifici per la taverna ...

# Registra gli handler specifici se necessario (anche se ora MappaState ha caricamento dinamico)
# TavernaState.register_ui_handler(taverna_ui_handlers.TavernaUIHandler)
# TavernaState.register_menu_handler(taverna_menu_handlers.TavernaMenuHandler)