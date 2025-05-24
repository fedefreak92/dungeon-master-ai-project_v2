"""
Implementazione della classe principale dello stato mappa.
"""

from states.base.enhanced_base_state import EnhancedBaseState
# from states.mappa import ui, movimento, interazioni, ui_handlers, serializzazione # Verranno importati dentro _init_handlers o metodi specifici
from util.funzioni_utili import avanti
import core.events as Events
# DA CREARE: from data.data_manager import carica_npg_per_mappa, carica_oggetti_per_mappa
import logging # AGGIUNTO
import importlib # AGGIUNTO per caricamento dinamico
from util.data_manager import get_data_manager # AGGIUNTO
from world.managers.npg_manager import NPGManager # AGGIUNTO
from items.oggetto_interattivo import OggettoInterattivo # AGGIUNTO
# AGGIUNTO IMPORT PER NPG
from entities.npg import NPG
# AGGIUNTO Import dei fallback generici
from .generic_ui_handler import GenericLuogoUIHandler 
from .generic_menu_handler import GenericLuogoMenuHandler
from . import serializzazione # AGGIUNTO IMPORT DEL MODULO DI SERIALIZZAZIONE LOCALE
# AGGIUNTO per navigazione e dialogo
from states.dialogo import DialogoState 
# Import MappaState stesso per creare nuove istanze per la navigazione
# from states.mappa.mappa_state import MappaState # Non necessario importare se stesso
import json # AGGIUNTO PER LOGGING PAYLOAD

logger = logging.getLogger(__name__) # AGGIUNTO logger a livello di modulo

class MappaState(EnhancedBaseState): # Concettualmente, questo è il nostro LuogoState
    def __init__(self, nome_luogo: str, game_state_manager=None, stato_origine=None): # MODIFICATO
        """
        Inizializza lo stato mappa/luogo.
        
        Args:
            nome_luogo (str): Il nome del luogo da caricare (es. "taverna", "mercato").
            game_state_manager: Il gestore degli stati del gioco.
            stato_origine: Lo stato da cui proviene (valutare se ancora necessario)
        """
        super().__init__() # RIMOSSO game_state_manager dalla chiamata a super se non supportato
        # Il game_state_manager (che in genere è self.gioco, cioè l'istanza di World)
        # verrà impostato quando lo stato entra nella FSM del World 
        # tramite World._set_current_fsm_state_internal -> new_state_instance.set_game_context(self)
        if game_state_manager: # Manteniamo la possibilità di passarlo esplicitamente se serve
            self.game_state_manager = game_state_manager
        else:
            self.game_state_manager = None # Inizializza a None
            
        self.nome_luogo = nome_luogo
        self.nome_stato = f"luogo_{nome_luogo}" # Nome stato dinamico
        # self.stato_origine = stato_origine # Valutare se mantenere

        # Attributi generalizzati da TavernaState/MercatoState/MappaState
        self.npg_presenti = {}
        self.oggetti_interattivi = {}
        self.mappa_data = {} # AGGIUNTO per contenere i dati grezzi della mappa (griglia, etc.)
        self.griglia = None # AGGIUNTO
        self.descrizione_luogo = "" # AGGIUNTO
        self.pos_iniziale_giocatore = None # AGGIUNTO
        self.nome_npg_attivo = None
        self.stato_conversazione = "inizio"
        self.fase_luogo = "menu_principale" # Sostituisce self.fase di Taverna/Mercato
        self.dati_contestuali_luogo = {} # Sostituisce self.dati_contestuali

        # AGGIUNTO: Attributi per configurazione caricata
        self.opzioni_menu_principale_luogo = []
        self.testi_ui_specifici_luogo = {}
        self.comandi_aggiuntivi_luogo_config = {}

        self.mostra_leggenda = True
        self.menu_attivo = "principale" # Menu di default, può essere sovrascritto da dati luogo
        self.ui_aggiornata = False
        self.ultima_scelta = None
        self.attesa_risposta_mappa = None
        self.mostra_mappa = False # Era specifico di MercatoState, ora generalizzato
        
        self.direzioni = {
            "nord": (0, -1),
            "sud": (0, 1),
            "est": (1, 0),
            "ovest": (-1, 0)
        }
        
        self._carica_dati_luogo() # Carica NPC, oggetti, configurazioni specifiche
        self._init_handlers()     # Inizializza UI, Menu handlers
        self._init_commands()     # Inizializza comandi specifici del luogo/generici
        self._register_event_handlers() # Registra handler eventi generici

        self.menu_handler = GenericLuogoMenuHandler(self)
        self.ui_handler = GenericLuogoUIHandler(self)
        
        # Prova a derivare il nome del modulo del luogo da self.nome_luogo
        nome_luogo_normalizzato = self.nome_luogo.lower().replace(" ", "_")
        nome_luogo_capitalized = self.nome_luogo.capitalize()

        try:
            # Importazione dinamica degli handler specifici del luogo
            module_path_prefix = f"states.{nome_luogo_normalizzato}" 
            
            menu_handler_class = None
            ui_handler_class = None

            # Carica Menu Handler
            try:
                menu_module_name = f"{module_path_prefix}.{nome_luogo_normalizzato}_menu_handler"
                menu_module = importlib.import_module(menu_module_name)
                menu_handler_class_name = f"{nome_luogo_capitalized}MenuHandler"
                if hasattr(menu_module, menu_handler_class_name):
                    menu_handler_class = getattr(menu_module, menu_handler_class_name)
                else:
                    logger.warning(f"Modulo Menu handler '{menu_module_name}' trovato per {nome_luogo_normalizzato}, ma classe '{menu_handler_class_name}' non presente.")
            except ImportError:
                 logger.info(f"Nessun Menu handler specifico trovato in '{module_path_prefix}.{nome_luogo_normalizzato}_menu_handler', userò il generico.")
            except Exception as e:
                logger.error(f"Errore durante il caricamento dinamico del Menu handler per {nome_luogo_normalizzato}: {e}")

            # Carica UI Handler (simile al menu handler)
            try:
                ui_module_name = f"{module_path_prefix}.{nome_luogo_normalizzato}_ui_handler"
                ui_module = importlib.import_module(ui_module_name)
                ui_handler_class_name = f"{nome_luogo_capitalized}UIHandler"
                if hasattr(ui_module, ui_handler_class_name):
                    ui_handler_class = getattr(ui_module, ui_handler_class_name)
                else:
                    logger.warning(f"Modulo UI handler '{ui_module_name}' trovato per {nome_luogo_normalizzato}, ma classe '{ui_handler_class_name}' non presente.")
            except ImportError:
                 logger.info(f"Nessun UI handler specifico trovato in '{module_path_prefix}.{nome_luogo_normalizzato}_ui_handler', userò il generico.")
            except Exception as e:
                logger.error(f"Errore durante il caricamento dinamico del UI handler per {nome_luogo_normalizzato}: {e}")

            # Istanzia gli handler (specifici o generici)
            self.menu_handler = menu_handler_class(self) if menu_handler_class else GenericLuogoMenuHandler(self)
            self.ui_handler = ui_handler_class(self) if ui_handler_class else GenericLuogoUIHandler(self)
            
            logger.info(f"Handler inizializzati per {nome_luogo_normalizzato} -> Menu: {type(self.menu_handler).__name__}, UI: {type(self.ui_handler).__name__}")

        except ImportError as e:
            logger.warning(f"Modulo specifico per il luogo '{nome_luogo_normalizzato}' non trovato ({e}). Usando handler generici.")
            self.menu_handler = GenericLuogoMenuHandler(self)
            self.ui_handler = GenericLuogoUIHandler(self)
        except Exception as e:
            logger.error(f"Errore generale durante l'inizializzazione degli handler specifici per {nome_luogo_normalizzato}: {e}")
            self.menu_handler = GenericLuogoMenuHandler(self)
            self.ui_handler = GenericLuogoUIHandler(self)

    def enter(self):
        # Imposta temporaneamente il livello di logging a DEBUG per questo logger specifico
        logger.setLevel(logging.DEBUG) # AGGIUNTA TEMPORANEA PER DEBUG

        # Chiamare super().enter() se EnhancedBaseState ha una logica importante in enter()
        if hasattr(super(), 'enter') and callable(getattr(super(), 'enter')):
            super().enter() 
        
        logger.info(f"***** MappaState.enter() chiamato per luogo: {self.nome_luogo} *****")
        
        # Il contesto self.gioco dovrebbe essere impostato da World._set_current_fsm_state_internal
        # prima di chiamare enter(). Verifichiamolo.
        if not self.gioco:
            logger.error(f"ERRORE CRITICO: self.gioco non è impostato in MappaState.enter() per {self.nome_luogo}. L'UI non si aggiornerà correttamente.")
            # Se self.game_state_manager (che è l'istanza di World passata opzionalmente o impostata) esiste,
            # potremmo tentare di impostare self.gioco qui, ma idealmente dovrebbe essere già fatto.
            if self.game_state_manager and not self.gioco:
                logger.info(f"Tentativo di impostare self.gioco da self.game_state_manager in MappaState.enter()")
                self.set_game_context(self.game_state_manager) # game_state_manager è l'istanza di World

        if self.gioco:
            logger.info(f"Contesto di gioco (self.gioco) disponibile in MappaState.enter() per {self.nome_luogo}. Procedo con l'aggiornamento delle entità locali.")
            
            # --- INIZIO MODIFICA SINCRONIZZAZIONE ENTITÀ ---
            self.npg_presenti.clear()
            self.oggetti_interattivi.clear()
            logger.info(f"Contenitori npg_presenti e oggetti_interattivi svuotati in MappaState per {self.nome_luogo} prima della sincronizzazione.")

            for entity_id, entity_obj in self.gioco.entities.items():
                entity_map_name = None
                entity_is_on_current_map = False
                actual_entity_type = type(entity_obj).__name__
                logger.debug(f"[SYNC_DEBUG] Controllo Entità ID: {entity_id}, Tipo Reale: {actual_entity_type}, Nome/Attributi: {vars(entity_obj) if hasattr(entity_obj, '__dict__') else 'N/A'}")

                # Determina la mappa dell'entità
                # Priorità al componente 'position' se esiste e ha 'map_name'
                if hasattr(entity_obj, 'has_component') and callable(getattr(entity_obj, 'has_component')) and entity_obj.has_component('position'): # MODIFICATO QUI: 'PositionComponent' -> 'position'
                    pos_comp = entity_obj.get_component('position') # MODIFICATO QUI: 'PositionComponent' -> 'position'
                    if pos_comp and hasattr(pos_comp, 'map_name'):
                        entity_map_name = pos_comp.map_name
                
                # Fallback all'attributo diretto 'mappa_corrente'
                if entity_map_name is None and hasattr(entity_obj, 'mappa_corrente'):
                    entity_map_name = entity_obj.mappa_corrente
                
                if entity_map_name == self.nome_luogo:
                    entity_is_on_current_map = True
                    logger.debug(f"[SYNC_DEBUG] Entità ID: {entity_id} È sulla mappa corrente '{self.nome_luogo}'.")
                else:
                    logger.debug(f"[SYNC_DEBUG] Entità ID: {entity_id} NON è sulla mappa corrente '{self.nome_luogo}' (mappa rilevata: '{entity_map_name}').")

                if entity_is_on_current_map:
                    is_npg = isinstance(entity_obj, NPG)
                    is_obj_int = isinstance(entity_obj, OggettoInterattivo)
                    logger.debug(f"[SYNC_DEBUG] Entità ID: {entity_id} - Check Tipi: is_npg={is_npg}, is_obj_int={is_obj_int}")

                    # Aggiungi a npg_presenti se è un NPG
                    if is_npg:
                        npc_key = getattr(entity_obj, 'nome', entity_obj.id)
                        self.npg_presenti[npc_key] = entity_obj
                        logger.debug(f"Sincronizzato NPG '{npc_key}' (ID: {entity_obj.id}) da World ECS in MappaState '{self.nome_luogo}'.")
                    # Aggiungi a oggetti_interattivi se è un OggettoInterattivo
                    elif is_obj_int:
                        obj_key = getattr(entity_obj, 'nome', entity_obj.id)
                        self.oggetti_interattivi[obj_key] = entity_obj
                        logger.debug(f"Sincronizzato OggettoInterattivo '{obj_key}' (ID: {entity_obj.id}) da World ECS in MappaState '{self.nome_luogo}'.")
            
            logger.info(f"MappaState '{self.nome_luogo}' sincronizzato con World ECS: {len(self.npg_presenti)} NPC, {len(self.oggetti_interattivi)} oggetti.")
            # --- FINE MODIFICA SINCRONIZZAZIONE ENTITÀ ---

            self.ui_aggiornata = False  # Forza un aggiornamento della UI al prossimo update
            
            # Chiamare update() per triggerare la logica di rendering e invio dati.
            # Assicurati che update() o metodi da esso chiamati (es. aggiorna_renderer)
            # emettano gli eventi WebSocket necessari al client.
            self.update(dt=0) # Passa un delta time, anche se 0 per l'inizializzazione iniziale
            
            # Esempio di emissione evento esplicito se necessario (da adattare):
            # if hasattr(self, 'get_map_render_data'): # Verifica se il metodo esiste
            #     map_render_data = self.get_map_render_data() 
            #     if map_render_data:
            #        self.emit_event(Events.MAP_DATA_READY, **map_render_data)
            #        logger.info(f"Evento MAP_DATA_READY emesso esplicitamente per {self.nome_luogo}")
            # else:
            #     logger.warning("Metodo get_map_render_data non trovato in MappaState.")

        else:
            logger.error(f"MappaState.enter(): self.gioco non è ancora disponibile per {self.nome_luogo} dopo il tentativo di set_game_context. L'UI potrebbe non aggiornarsi.")

    def _carica_dati_luogo(self):
        """Carica NPC, oggetti, menu, e altre configurazioni specifiche per il luogo.
        Questo metodo dovrà usare un data_manager per leggere dai file JSON.
        """
        nome_luogo_effettivo = self.nome_luogo # Usa una variabile locale per sicurezza
        if not isinstance(nome_luogo_effettivo, str):
            logger.error(f"[MappaState._carica_dati_luogo] ERRORE CRITICO: self.nome_luogo non è una stringa, ma {type(nome_luogo_effettivo)}. Valore: {nome_luogo_effettivo}. Non posso caricare i dati del luogo.")
            # Imposta valori di default per evitare crash ulteriori
            self.mappa_data = {}
            self.griglia = []
            self.descrizione_luogo = "Luogo sconosciuto (errore caricamento)"
            self.pos_iniziale_giocatore = (0,0)
            self.opzioni_menu_principale_luogo = []
            self.testi_ui_specifici_luogo = {}
            self.comandi_aggiuntivi_luogo_config = {}
            return

        logger.info(f"[MappaState._carica_dati_luogo] Inizio caricamento dati per il luogo: '{nome_luogo_effettivo}'")

        data_manager = get_data_manager()
        npg_manager = NPGManager() # Assumendo che NPGManager possa essere istanziato così

        # Resetta le strutture dati principali
        self.npg_presenti = {}
        self.oggetti_interattivi = {}
        self.mappa_data = {}

        # 1. Caricare dati di base della mappa (griglia, descrizione, etc.)
        # Questo metodo deve esistere in DataManager e leggere /data/mappe/{self.nome_luogo}.json
        raw_map_data = data_manager.get_map_data(nome_luogo_effettivo) 
        if raw_map_data:
            self.mappa_data = raw_map_data
            self.griglia = raw_map_data.get('griglia')
            self.descrizione_luogo = raw_map_data.get('descrizione', f"Ti trovi in {nome_luogo_effettivo.replace('_', ' ').title()}")
            self.pos_iniziale_giocatore = raw_map_data.get('pos_iniziale_giocatore')
            # Potresti voler caricare qui anche tileset, musiche di sottofondo specifiche, etc.
            logger.info(f"Dati mappa di base caricati per '{nome_luogo_effettivo}'. Descrizione: '{self.descrizione_luogo}'")
        else:
            logger.error(f"Impossibile caricare i dati di base per la mappa '{nome_luogo_effettivo}'. Il file potrebbe mancare o essere corrotto.")
            # Potrebbe essere utile avere una mappa di fallback o sollevare un'eccezione

        # 2. Caricare e istanziare NPG per questa mappa
        # mappe_npg.json contiene gli NPG per ogni mappa e la loro posizione
        map_specific_npcs_data = data_manager.load_data("npc", "mappe_npg.json")
        if map_specific_npcs_data:
            npcs_for_this_map = map_specific_npcs_data.get(nome_luogo_effettivo, [])
            logger.info(f"Trovati {len(npcs_for_this_map)} NPG configurati per '{nome_luogo_effettivo}' in mappe_npg.json.")
            for npc_info in npcs_for_this_map:
                nome_npg = npc_info.get("nome")
                posizione_npg = npc_info.get("posizione")
                npc_id_specifico = npc_info.get("id", nome_npg) # Usa 'id' se presente, altrimenti 'nome'

                if nome_npg and posizione_npg and isinstance(posizione_npg, list) and len(posizione_npg) == 2:
                    npg_instance = npg_manager.crea_npc(npc_id_specifico) # crea_npc usa l'ID/nome per caricare da npcs.json
                    if npg_instance:
                        npg_instance.x = posizione_npg[0]
                        npg_instance.y = posizione_npg[1]
                        npg_instance.mappa_corrente = nome_luogo_effettivo 
                        self.npg_presenti[nome_npg] = npg_instance # Usa il nome come chiave nel dizionario
                        if self.gioco and hasattr(self.gioco, 'add_entity'):
                            logger.debug(f"[SYNC_WORLD_ADD] Tentativo di aggiungere NPG '{npg_instance.nome}' (ID: {npg_instance.id}) al World ECS.")
                            self.gioco.add_entity(npg_instance)
                        logger.debug(f"NPG '{nome_npg}' (ID: {npc_id_specifico}) istanziato e posizionato a {posizione_npg}.")
                    else:
                        logger.warning(f"Impossibile creare istanza NPG per '{nome_npg}' (ID: {npc_id_specifico}) in '{nome_luogo_effettivo}'. Definizione mancante in npcs.json?")
                else:
                    logger.warning(f"Dati NPG malformati per '{nome_luogo_effettivo}': {npc_info}")
        else:
            logger.warning(f"File 'mappe_npg.json' non caricato o vuoto. Nessun NPG specifico per la mappa '{nome_luogo_effettivo}' verrà caricato.")

        # 3. Caricare e istanziare Oggetti Interattivi per questa mappa
        # mappe_oggetti.json contiene gli oggetti per ogni mappa e la loro posizione
        map_specific_objects_data = data_manager.load_data("items", "mappe_oggetti.json")
        if map_specific_objects_data:
            objects_for_this_map = map_specific_objects_data.get(nome_luogo_effettivo, [])
            logger.info(f"Trovati {len(objects_for_this_map)} oggetti configurati per '{nome_luogo_effettivo}' in mappe_oggetti.json.")
            for obj_info in objects_for_this_map:
                nome_oggetto = obj_info.get("nome")
                posizione_oggetto = obj_info.get("posizione")
                
                if nome_oggetto and posizione_oggetto and isinstance(posizione_oggetto, list) and len(posizione_oggetto) == 2:
                    # OggettoInterattivo.carica_da_json deve usare il DataManager per ottenere
                    # la definizione completa dell'oggetto da un file centrale (es. data/items/oggetti_interattivi_definizioni.json)
                    object_instance = OggettoInterattivo.carica_da_json(nome_oggetto)
                    if object_instance:
                        # La classe OggettoInterattivo ha self.posizione che può essere una lista [x,y]
                        object_instance.posizione = posizione_oggetto 
                        # Assicuriamoci che abbia anche mappa_corrente per coerenza, se non ce l'ha già
                        if not hasattr(object_instance, 'mappa_corrente') or not object_instance.mappa_corrente:
                            object_instance.mappa_corrente = nome_luogo_effettivo
                        self.oggetti_interattivi[nome_oggetto] = object_instance
                        if self.gioco and hasattr(self.gioco, 'add_entity'):
                            logger.debug(f"[SYNC_WORLD_ADD] Tentativo di aggiungere OggettoInterattivo '{object_instance.nome}' (ID: {object_instance.id}) al World ECS.")
                            self.gioco.add_entity(object_instance)
                        logger.debug(f"Oggetto Interattivo '{nome_oggetto}' istanziato e posizionato a {posizione_oggetto}.")
                    else:
                        logger.warning(f"Impossibile creare istanza OggettoInterattivo per '{nome_oggetto}' in '{nome_luogo_effettivo}'. Definizione mancante?")
                else:
                    logger.warning(f"Dati oggetto malformati per '{nome_luogo_effettivo}': {obj_info}")
        else:
            logger.warning(f"File 'mappe_oggetti.json' non caricato o vuoto. Nessun oggetto specifico per la mappa '{nome_luogo_effettivo}' verrà caricato.")
        
        # 4. Caricare configurazioni specifiche del luogo (menu, comandi, testi)
        if self.mappa_data: # Assicurati che i dati mappa base siano stati caricati
            config_luogo = self.mappa_data.get("config_luogo", {})
            self.opzioni_menu_principale_luogo = config_luogo.get("menu_principale_opzioni", [])
            self.testi_ui_specifici_luogo = config_luogo.get("ui_specific_texts", {})
            self.comandi_aggiuntivi_luogo_config = config_luogo.get("comandi_testuali_aggiuntivi", {})
            # Carica altre configurazioni se necessario (es. musica)
            logger.info(f"Caricate {len(self.opzioni_menu_principale_luogo)} opzioni menu principale, {len(self.comandi_aggiuntivi_luogo_config)} comandi aggiuntivi per '{nome_luogo_effettivo}'.")
        else:
            logger.warning(f"Nessuna configurazione specifica del luogo trovata o caricata per '{nome_luogo_effettivo}'.")
            self.opzioni_menu_principale_luogo = []
            self.testi_ui_specifici_luogo = {}
            self.comandi_aggiuntivi_luogo_config = {}

        logger.info(f"Caricamento dati per [LuogoState: {nome_luogo_effettivo}] completato.")
        logger.info(f"NPC presenti ({len(self.npg_presenti)}): {list(self.npg_presenti.keys())}")
        logger.info(f"Oggetti interattivi ({len(self.oggetti_interattivi)}): {list(self.oggetti_interattivi.keys())}")

    def _init_handlers(self):
        """Inizializza gli handler UI e Menu.
        Tenta di caricare handler specifici per il luogo, altrimenti usa i generici.
        """
        ui_handler_class = None
        menu_handler_class = None
        
        # Usa self.nome_luogo normalizzato per costruire i percorsi
        nome_luogo_normalizzato = self.nome_luogo.lower().replace(" ", "_")
        nome_luogo_capitalized = self.nome_luogo.capitalize() # Per convenzioni nomi classi

        module_path_prefix = f"states.{nome_luogo_normalizzato}"

        # Tenta di caricare UI Handler specifico
        try:
            ui_module_name = f"{module_path_prefix}.{nome_luogo_normalizzato}_ui_handler"
            ui_module = importlib.import_module(ui_module_name)
            ui_handler_class_name_convention = f"{nome_luogo_capitalized}UIHandler"
            if hasattr(ui_module, ui_handler_class_name_convention):
                 ui_handler_class = getattr(ui_module, ui_handler_class_name_convention)
            else:
                 logger.warning(f"Modulo UI handler '{ui_module_name}' trovato per {nome_luogo_normalizzato}, ma classe '{ui_handler_class_name_convention}' non presente. Verrà usato il generico.")
        except ImportError:
            logger.info(f"Nessun UI handler specifico trovato in '{ui_module_name}', userò il generico.")
        except Exception as e:
            logger.error(f"Errore durante il caricamento dinamico dell'UI handler per {nome_luogo_normalizzato}: {e}")

        # Tenta di caricare Menu Handler specifico
        try:
            menu_module_name = f"{module_path_prefix}.{nome_luogo_normalizzato}_menu_handler"
            menu_module = importlib.import_module(menu_module_name)
            menu_handler_class_name = f"{nome_luogo_capitalized}MenuHandler"
            if hasattr(menu_module, menu_handler_class_name):
                menu_handler_class = getattr(menu_module, menu_handler_class_name)
            else:
                logger.warning(f"Modulo Menu handler '{menu_module_name}' trovato per {nome_luogo_normalizzato}, ma classe '{menu_handler_class_name}' non presente.")
        except ImportError:
             logger.info(f"Nessun Menu handler specifico trovato in '{menu_module_name}', userò il generico.")
        except Exception as e:
            logger.error(f"Errore durante il caricamento dinamico del Menu handler per {nome_luogo_normalizzato}: {e}")

        # Istanzia gli handler (specifici o generici)
        self.ui_handler_instance = ui_handler_class(self) if ui_handler_class else GenericLuogoUIHandler(self)
        self.menu_handler_instance = menu_handler_class(self) if menu_handler_class else GenericLuogoMenuHandler(self)
            
        logger.info(f"Handler inizializzati per {nome_luogo_normalizzato} -> UI: {type(self.ui_handler_instance).__name__}, Menu: {type(self.menu_handler_instance).__name__}")

    def _register_event_handlers(self):
        """Registra gli handler per eventi relativi alla mappa"""
        logger.info(f"[MappaState] Registrazione handler eventi per {self.nome_luogo}")
        
        # Eventi di movimento
        unsubscribe_move = self.event_bus.on(Events.PLAYER_MOVE, self._handle_player_move_event)
        logger.info(f"[MappaState] Handler PLAYER_MOVE registrato: {unsubscribe_move is not None}")
        
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
        # Questi comandi potrebbero essere una base, e altri aggiunti da _carica_dati_luogo
        self.commands = {
            "guarda": self._cmd_guarda_ambiente, # Rinominiamo per chiarezza
            "muovi": self._sposta_giocatore, # Esistente
            "interagisci": self._mostra_opzioni_interazione, # Esistente
            "leggenda": self._toggle_leggenda, # Esistente
            "indietro": self._cmd_torna_indietro, # Rinominiamo per chiarezza
            # TODO: Aggiungere comandi comuni come "inventario", "menu", "salva", "carica"
        }
        
        # Aggiungi/sovrascrivi comandi specifici del luogo caricati da config
        if hasattr(self, 'comandi_aggiuntivi_luogo_config'):
            for comando, nome_metodo_str in self.comandi_aggiuntivi_luogo_config.items():
                if hasattr(self, nome_metodo_str):
                    self.commands[comando] = getattr(self, nome_metodo_str)
                    logger.debug(f"Comando specifico '{comando}' mappato a metodo '{nome_metodo_str}' per {self.nome_luogo}.")
                else:
                    # Se il metodo non è direttamente su MappaState (o sottoclasse), 
                    # potrebbe essere gestito altrove (es. process_azione_luogo o un handler)
                    # Per ora, logghiamo un warning.
                    logger.warning(f"Metodo comando '{nome_metodo_str}' per '{comando}' non trovato direttamente in {type(self).__name__} per {self.nome_luogo}. Sarà gestito genericamente?")
                    # Potremmo mappare a un handler generico se necessario:
                    # self.commands[comando] = lambda gioco, params=None, c=comando: self.process_azione_luogo(gioco.giocatore.id, c, params)
        
        logger.info(f"Comandi inizializzati per {self.nome_luogo}: {list(self.commands.keys())}")

    # Nuovi comandi o comandi rinominati/generalizzati
    def _cmd_guarda_ambiente(self, gioco):
        gioco.io.mostra_messaggio(f"Ti guardi intorno in: {self.nome_luogo.upper()}.")
        # TODO: Descrivere NPC e oggetti visibili basati su self.npg_presenti e self.oggetti_interattivi
        # ui.mostra_elementi_vicini(self, gioco) # Adattare questa funzione

    def _cmd_torna_indietro(self, gioco):
        # TODO: Logica per tornare allo stato/luogo precedente, se applicabile.
        # Potrebbe usare self.stato_origine se mantenuto, o una logica di stack di stati più robusta.
        # interazioni.torna_indietro(self, gioco) # Adattare questa funzione
        if hasattr(gioco, 'pop_stato'):
             gioco.pop_stato()
        else:
            gioco.io.mostra_messaggio("Non puoi tornare indietro da qui.")
    
    def update(self, dt):
        """
        Nuovo metodo di aggiornamento basato su EventBus.
        Sostituisce gradualmente esegui().
        
        Args:
            dt: Delta time, tempo trascorso dall'ultimo aggiornamento
        """
        gioco = self.gioco
        if not gioco:
            logger.warning(f"[MappaState.update][{self.nome_luogo}] self.gioco non è disponibile. Uscita.")
            return
        
        if not self.ui_aggiornata:
            logger.info(f"[MappaState.update][{self.nome_luogo}] UI non aggiornata, procedo con l'emissione dell'evento.")
            # self.aggiorna_renderer(gioco) # COMMENTATO - Causa AttributeError
            logger.info(f"[MappaState.update][{self.nome_luogo}] Chiamata a self.aggiorna_renderer commentata. Si fa affidamento sull'evento UI_UPDATE.")
            
            if self.mostra_leggenda:
                if hasattr(self.ui_handler_instance, 'mostra_leggenda') and callable(getattr(self.ui_handler_instance, 'mostra_leggenda')):
                    self.ui_handler_instance.mostra_leggenda(self, gioco)
                else:
                    logger.warning(f"[MappaState.update][{self.nome_luogo}] self.ui_handler_instance non ha il metodo 'mostra_leggenda' o non è callable.")
            
            # Prepara un payload specifico per l'aggiornamento della mappa
            payload_map_data = {
                "map_id": self.nome_luogo,
                "description": self.descrizione_luogo,
                "grid": self.griglia, # Assicurati che sia serializzabile (lista di liste di stringhe/numeri)
                "player_pos": (gioco.giocatore.x, gioco.giocatore.y) if gioco.giocatore else None,
                "entities_on_map": {name: npc.to_dict() for name, npc in self.npg_presenti.items() if hasattr(npc, 'to_dict')},
                "interactive_objects": {name: obj.to_dict() for name, obj in self.oggetti_interattivi.items() if hasattr(obj, 'to_dict')},
                # Aggiungi qui altri dati necessari, es. tileset_url, config_luogo se serve al client per la UI
            }
            try:
                # Logga il payload prima di inviarlo per debug
                # Usiamo default=str per gestire tipi non direttamente serializzabili in JSON per il logging
                logger.info(f"""[MappaState.update][{self.nome_luogo}] Payload per UI_UPDATE (o MAP_DATA_LOADED):
{json.dumps(payload_map_data, indent=2, default=str)}""")
            except Exception as e_log_payload:
                logger.error(f"[MappaState.update][{self.nome_luogo}] Errore durante il logging del payload: {e_log_payload}")

            # Considera di usare un evento più specifico come Events.MAP_DATA_LOADED
            # self.emit_event(Events.MAP_DATA_LOADED, **payload_map_data)
            # Per ora, modifichiamo l'evento UI_UPDATE per includere questi dati strutturati:
            self.emit_event(Events.UI_UPDATE, element="map_data", data=payload_map_data) 
            logger.info(f"[MappaState.update][{self.nome_luogo}] Evento UI_UPDATE emesso con element='map_data'.")
            self.ui_aggiornata = True
            
        if hasattr(self, 'mappa_aggiornata') and self.mappa_aggiornata:
            if gioco.giocatore:
                self.emit_event(Events.MAP_LOAD, 
                               map_name=gioco.giocatore.mappa_corrente,
                               player_pos=(gioco.giocatore.x, gioco.giocatore.y))
                logger.info(f"[MappaState.update][{self.nome_luogo}] Evento MAP_LOAD emesso per {gioco.giocatore.mappa_corrente}.")
            else:
                logger.warning(f"[MappaState.update][{self.nome_luogo}] Giocatore non disponibile, impossibile emettere MAP_LOAD.")
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
        mappa_corrente_obj = gioco.gestore_mappe.ottieni_mappa(gioco.giocatore.mappa_corrente) # Rinominato per chiarezza
        nome_mappa = gioco.giocatore.mappa_corrente.upper()
        
        gioco.io.mostra_messaggio(f"\n=== MAPPA DI {nome_mappa} ===")
        
        # Utilizziamo il renderer grafico invece della rappresentazione ASCII
        if not self.ui_aggiornata:
            # self.aggiorna_renderer(gioco) # COMMENTATO - Causa AttributeError
            logger.info(f"[MappaState.esegui][{self.nome_luogo}] Chiamata a self.aggiorna_renderer commentata.")
            self.ui_aggiornata = True # Assumiamo che l'evento UI_UPDATE gestisca il rendering
        
        if hasattr(self, 'ui_handler_instance') and hasattr(self.ui_handler_instance, 'mostra_leggenda') and self.mostra_leggenda:
            self.ui_handler_instance.mostra_leggenda(self, gioco)
        elif hasattr(self, 'mostra_leggenda') and self.mostra_leggenda and 'ui' in globals(): # Fallback se ui_handler_instance non c'è o non ha il metodo
            try:
                # Questo blocco è per la retrocompatibilità, 'ui' potrebbe non essere sempre definito
                # o potrebbe non avere mostra_leggenda
                if callable(ui.mostra_leggenda):
                    ui.mostra_leggenda(self, gioco)
            except NameError:
                logger.warning("[MappaState.esegui] Modulo 'ui' globale non trovato per mostra_leggenda.")
            except AttributeError:
                logger.warning("[MappaState.esegui] Funzione 'mostra_leggenda' non trovata nel modulo 'ui' globale.")

        # Mostra informazioni sulla posizione del giocatore
        gioco.io.mostra_messaggio(f"\nPosizione attuale: ({gioco.giocatore.x}, {gioco.giocatore.y})")
        
        # Mostra menù interattivo se non è già attivo
        if not self.menu_attivo:
            if hasattr(self.ui_handler_instance, 'mostra_menu_principale'):
                self.ui_handler_instance.mostra_menu_principale(self, gioco)
        
        # Aggiorna con EventBus, mantenendo retrocompatibilità
        # La chiamata a self.update() in MappaState.enter() dovrebbe già gestire questo per l'inizializzazione.
        # Potrebbe non essere necessario chiamarlo di nuovo qui in esegui() se esegui() è solo per retrocompatibilità testuale.
        # self.update(0.033) 
        
        # Processa gli eventi UI
        super().esegui(gioco)
    
    # Handler eventi
    def _handle_entity_moved(self, **kwargs):
        """Gestisce l'evento di movimento di un'entità"""
        entity_id = kwargs.get('entity_id')
        from_pos = kwargs.get('from_pos')
        to_pos = kwargs.get('to_pos')
        
        gioco = self.gioco
        if not gioco:
            return
            
        # Se l'entità è il giocatore, aggiorna UI
        if entity_id == gioco.giocatore.id:
            self.ui_aggiornata = False  # Forza aggiornamento UI
            
            # Logga movimento (può essere rimosso in produzione)
            gioco.io.mostra_messaggio(f"Ti sei spostato a ({to_pos[0]}, {to_pos[1]})")
            
            # Controlla oggetti e NPC vicini dopo il movimento
            # self._mostra_elementi_vicini(gioco) # DA ADATTARE o integrare in _cmd_guarda_ambiente
            if hasattr(self.ui_handler_instance, 'mostra_elementi_vicini'):
                self.ui_handler_instance.mostra_elementi_vicini(self, gioco)
    
    def _handle_movement_blocked(self, **kwargs):
        """Gestisce l'evento di movimento bloccato"""
        entity_id = kwargs.get('entity_id')
        from_pos = kwargs.get('from_pos')
        to_pos = kwargs.get('to_pos')
        reason = kwargs.get('reason')
        
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
    
    def _handle_map_change(self, **kwargs):
        """Gestisce l'evento di cambio mappa"""
        entity_id = kwargs.get('entity_id')
        from_map = kwargs.get('from_map')
        to_map = kwargs.get('to_map')
        target_pos = kwargs.get('target_pos')
        
        gioco = self.gioco
        if not gioco or entity_id != gioco.giocatore.id:
            return
            
        # Delega la gestione del cambio mappa al modulo movimento
        # movimento.gestisci_cambio_mappa(self, gioco, from_map, to_map, target_pos) # DA ADATTARE
        if hasattr(self.movimento_handler_instance, 'gestisci_cambio_mappa'): # Assumendo un self.movimento_handler_instance
            self.movimento_handler_instance.gestisci_cambio_mappa(self, gioco, from_map, to_map, target_pos)
        
        # Segnala che la mappa è stata aggiornata
        self.mappa_aggiornata = True
        self.ui_aggiornata = False
    
    def _handle_trigger_activated(self, **kwargs):
        """Gestisce l'attivazione di un trigger"""
        trigger_id = kwargs.get('trigger_id')
        trigger_type = kwargs.get('trigger_type')
        entity_id = kwargs.get('entity_id')
        position = kwargs.get('position')
        
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
    
    def _handle_treasure_found(self, **kwargs):
        """Gestisce l'evento di tesoro trovato"""
        entity_id = kwargs.get('entity_id')
        treasure_id = kwargs.get('treasure_id')
        contents = kwargs.get('contents')
        
        gioco = self.gioco
        if not gioco or entity_id != gioco.giocatore.id:
            return
            
        gioco.io.mostra_messaggio("Hai trovato un tesoro!")
        # Mostra contenuti e aggiungi all'inventario
        if contents:
            gioco.io.mostra_messaggio(f"Contenuto: {', '.join(item.get('name', 'Oggetto') for item in contents)}")
            # Aggiungi items all'inventario
    
    def _handle_ui_update(self, **kwargs):
        """Gestisce l'aggiornamento dell'interfaccia utente"""
        element = kwargs.get('element')
        
        # Aggiorna solo se l'elemento è relativo alla mappa
        if element in ["mappa", "luogo", "player_position", "all"]:
            self.ui_aggiornata = False
    
    # Wrapper per i metodi nei moduli (mantenuti per retrocompatibilità)
    # Questi wrapper dovranno essere rivisti. La logica dovrebbe essere 
    # negli handler istanziati (self.ui_handler_instance, self.menu_handler_instance) 
    # o nei moduli di logica (self.ui_logic, self.interazioni_logic, ecc.)

    def _handle_dialog_choice(self, event):
        # ui_handlers.handle_dialog_choice(self, event) # DA ADATTARE
        if hasattr(self.ui_handler_instance, 'handle_dialog_choice'):
            self.ui_handler_instance.handle_dialog_choice(self, event)
        
    def _handle_keypress(self, event):
        # ui_handlers.handle_keypress(self, event) # DA ADATTARE
        if hasattr(self.ui_handler_instance, 'handle_keypress'):
            self.ui_handler_instance.handle_keypress(self, event)
        
    def _handle_click_event(self, event):
        # ui_handlers.handle_click_event(self, event) # DA ADATTARE
        if hasattr(self.ui_handler_instance, 'handle_click_event'):
            self.ui_handler_instance.handle_click_event(self, event)
        
    def _handle_menu_action(self, event):
        # ui_handlers.handle_menu_action(self, event) # DA ADATTARE
        if hasattr(self.ui_handler_instance, 'handle_menu_action'): # o menu_handler_instance
            self.ui_handler_instance.handle_menu_action(self, event)
        
    def _sposta_giocatore(self, gioco, direzione):
        # Emetti evento di movimento
        self.emit_event(Events.PLAYER_MOVE, direction=direzione)
        
    def _mostra_opzioni_movimento(self, gioco):
        # ui.mostra_opzioni_movimento(self, gioco) # DA ADATTARE
        if hasattr(self.ui_handler_instance, 'mostra_opzioni_movimento'):
            self.ui_handler_instance.mostra_opzioni_movimento(self, gioco)
        
    def _mostra_opzioni_interazione(self, gioco):
        # ui.mostra_opzioni_interazione(self, gioco) # DA ADATTARE
        if hasattr(self.ui_handler_instance, 'mostra_opzioni_interazione'):
            self.ui_handler_instance.mostra_opzioni_interazione(self, gioco)
        
    def _interagisci_con_oggetto(self, gioco):
        # Emetti evento di interazione invece di chiamata diretta
        self.emit_event(Events.PLAYER_INTERACT, interaction_type="object")
        # interazioni.interagisci_con_oggetto(self, gioco) # DA ADATTARE
        # if hasattr(self.interazioni_logic, 'interagisci_con_oggetto'):
        #     self.interazioni_logic.interagisci_con_oggetto(self, gioco)
        
    def _interagisci_con_npg(self, gioco):
        # Emetti evento di interazione invece di chiamata diretta
        self.emit_event(Events.PLAYER_INTERACT, interaction_type="npc")
        # interazioni.interagisci_con_npg(self, gioco) # DA ADATTARE
        # if hasattr(self.interazioni_logic, 'interagisci_con_npg'):
        #     self.interazioni_logic.interagisci_con_npg(self, gioco)
        
    def _esamina_area(self, gioco):
        # interazioni.esamina_area(self, gioco) # DA ADATTARE
        # if hasattr(self.interazioni_logic, 'esamina_area'):
        #     self.interazioni_logic.esamina_area(self, gioco)
        pass # Implementare o collegare a un handler
        
    def _gestisci_cambio_mappa(self, gioco, mappa_origine, mappa_destinazione, target_pos=None):
        # movimento.gestisci_cambio_mappa(self, gioco, mappa_origine, mappa_destinazione) # DA ADATTARE
        # Il gestore eventi _handle_map_change già chiama una logica simile.
        # Questa funzione potrebbe diventare obsoleta o usata internamente dagli handler.
        pass
        
    def _mostra_elementi_vicini(self, gioco):
        # ui.mostra_elementi_vicini(self, gioco) # DA ADATTARE
        if hasattr(self.ui_handler_instance, 'mostra_elementi_vicini'):
            self.ui_handler_instance.mostra_elementi_vicini(self, gioco)
        
    def _mostra_menu_principale(self, gioco):
        # ui.mostra_menu_principale(self, gioco) # DA ADATTARE
        if hasattr(self.ui_handler_instance, 'mostra_menu_principale'):
            self.ui_handler_instance.mostra_menu_principale(self, gioco)
        
    def _toggle_leggenda(self, gioco):
        # ui.toggle_leggenda(self, gioco) # DA ADATTARE
        if hasattr(self.ui_handler_instance, 'toggle_leggenda'):
            self.ui_handler_instance.toggle_leggenda(self, gioco)
        else:
            self.mostra_leggenda = not self.mostra_leggenda
            self.ui_aggiornata = False
            gioco.io.mostra_messaggio(f"Leggenda: {'ON' if self.mostra_leggenda else 'OFF'}")

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
        game_state_manager = game.game_state_manager if game and hasattr(game, 'game_state_manager') else None

        nome_luogo = data.get("nome_luogo")
        if not nome_luogo:
            logger.error("Tentativo di deserializzare MappaState senza 'nome_luogo'. Impossibile procedere.")
            # Considerare di sollevare un'eccezione o ritornare None/un'istanza di errore
            raise ValueError("Impossibile deserializzare MappaState: 'nome_luogo' mancante nei dati.")

        # Crea l'istanza base. __init__ chiamerà _carica_dati_luogo e _init_handlers,
        # ma alcuni dati caricati da _carica_dati_luogo potrebbero essere sovrascritti
        # dai dati serializzati.
        # NOTA: game_state_manager viene passato qui.
        instance = cls(nome_luogo=nome_luogo, game_state_manager=game_state_manager) # Chiama __init__
        
        # Sovrascrivi gli attributi con quelli serializzati
        instance.nome_stato = data.get("nome_stato", f"luogo_{nome_luogo}")
        instance.fase_luogo = data.get("fase_luogo", "menu_principale")
        instance.dati_contestuali_luogo = data.get("dati_contestuali_luogo", {})
        
        # Deserializza NPG
        npg_data_dict = data.get("npg_presenti", {}) # Rinominato per chiarezza
        instance.npg_presenti = {} # Svuota quelli caricati da _carica_dati_luogo in __init__
        for nome_npg, npg_serial_data in npg_data_dict.items(): # npg_serial_data è il dict dell'NPG
            try:
                npg_instance = NPG.from_dict(npg_serial_data) # Chiamata al metodo corretto
                if npg_instance:
                    instance.npg_presenti[nome_npg] = npg_instance
                else:
                    logger.warning(f"NPG.from_dict ha restituito None per l'NPG '{nome_npg}' nel luogo '{instance.nome_luogo}'.")
            except Exception as e:
                logger.error(f"Errore durante la deserializzazione dell'NPG '{nome_npg}' per il luogo '{instance.nome_luogo}': {e}", exc_info=True)

        # Deserializza Oggetti Interattivi
        oggetti_data = data.get("oggetti_interattivi", {})
        instance.oggetti_interattivi = {} # Resetta prima di caricare
        for nome_oggetto, oggetto_data in oggetti_data.items():
            try:
                # Simile agli NPG, OggettoInterattivo dovrebbe avere from_dict
                obj_instance = OggettoInterattivo.from_dict(oggetto_data) # OggettoInterattivo deve essere importato e avere from_dict
                if obj_instance:
                    instance.oggetti_interattivi[nome_oggetto] = obj_instance
                else:
                    logger.warning(f"OggettoInterattivo.from_dict ha restituito None per '{nome_oggetto}'.")
            except Exception as e:
                logger.error(f"Errore durante la deserializzazione dell'oggetto interattivo '{nome_oggetto}': {e}")


        # Dati mappa grezzi - se decidiamo di serializzarli
        # Se non li serializziamo, _carica_dati_luogo (chiamato da __init__) dovrebbe averli già caricati
        # Se li serializziamo, sovrascriviamo qui.
        instance.mappa_data = data.get("mappa_data", instance.mappa_data) # Mantiene quello da __init__ se non serializzato
        instance.griglia = data.get("griglia", instance.griglia) # Mantiene quello da __init__ se non serializzato
        instance.descrizione_luogo = data.get("descrizione_luogo", instance.descrizione_luogo)
        instance.pos_iniziale_giocatore = data.get("pos_iniziale_giocatore", instance.pos_iniziale_giocatore)

        instance.menu_attivo = data.get("menu_attivo", "principale")
        instance.mostra_leggenda = data.get("mostra_leggenda", True)
        instance.nome_npg_attivo = data.get("nome_npg_attivo")
        instance.stato_conversazione = data.get("stato_conversazione", "inizio")
        
        # AGGIUNTO: Altri attributi importanti da serializzare/deserializzare
        instance.opzioni_menu_principale_luogo = data.get("opzioni_menu_principale_luogo", instance.opzioni_menu_principale_luogo)
        instance.testi_ui_specifici_luogo = data.get("testi_ui_specifici_luogo", instance.testi_ui_specifici_luogo)
        instance.comandi_aggiuntivi_luogo_config = data.get("comandi_aggiuntivi_luogo_config", instance.comandi_aggiuntivi_luogo_config)
        
        # NOTA IMPORTANTE: __init__ chiama _carica_dati_luogo(), _init_handlers(), _init_commands(), _register_event_handlers().
        # Quando from_dict sovrascrive i dati (es. npg_presenti, oggetti_interattivi, fase_luogo),
        # gli handler e i comandi inizializzati da __init__ potrebbero basarsi sui dati *prima* della sovrascrittura.
        # È FONDAMENTALE re-inizializzare handler e comandi DOPO che tutti i dati sono stati ripristinati
        # per assicurare che operino sullo stato corretto e completamente deserializzato.
        
        instance._init_handlers()  # Re-inizializza UI e Menu handlers con l'istanza aggiornata.
        instance._init_commands()  # Re-inizializza i comandi disponibili.
        # _register_event_handlers() è chiamato da __init__ e registra metodi dell'istanza MappaState
        # stessa sull'event_bus dell'istanza. Non è necessario richiamarlo qui, poiché
        # l'event bus e i metodi dell'istanza sono già correttamente configurati.

        logger.debug(f"MappaState deserializzato per il luogo '{instance.nome_luogo}'. Fase: '{instance.fase_luogo}'")
        return instance
        
    def get_base_dict(self):
        """
        Ottiene il dizionario base dallo stato genitore.
        
        Returns:
            dict: Dizionario base
        """
        return EnhancedBaseState.to_dict(self)

    # AGGIUNTO: Metodo helper per gestire azioni specifiche del luogo
    def _handle_azione_specifica_luogo(self, gioco, azione_id: str, context: dict):
        """Gestisce azioni specifiche del luogo che non sono comandi generici.
           Le sottoclassi possono sovrascrivere questo metodo."""
        logger.warning(f"Azione specifica '{azione_id}' non gestita da {type(self).__name__}. Contesto: {context}")
        if gioco and hasattr(gioco, 'io'):
            gioco.io.mostra_messaggio("Questa azione non è ancora implementata per questo luogo.")

    # AGGIUNTO: Metodo per processare azioni menu da handler generico
    def process_azione_menu(self, gioco, azione_id: str, context: dict = None):
        """Processa un'azione identificata da un ID proveniente da un menu."""
        logger.info(f"Processando azione menu '{azione_id}' per {self.nome_luogo}...")
        context = context or {}
        
        # Azioni Generiche
        if azione_id == "GUARDA_AMBIENTE":
            self._cmd_guarda_ambiente(gioco)
        elif azione_id == "TORNA_INDIETRO": # Spesso usato per uscire dal luogo corrente
             self._cmd_torna_indietro(gioco)
        
        # Navigazione tra Luoghi (MappaState)
        elif azione_id.startswith("VAI_A_"):
            destinazione_luogo = azione_id.replace("VAI_A_", "").lower()
            logger.info(f"Tentativo di navigazione da '{self.nome_luogo}' a '{destinazione_luogo}'")
            # Assumiamo che il gioco abbia un metodo per cambiare stato o pushare un nuovo stato
            if hasattr(gioco, 'push_stato'):
                # Qui creiamo una NUOVA istanza di MappaState per il luogo destinazione
                # NOTA: Potrebbe essere necessario passare più contesto o gestire il caricamento salvataggi
                try:
                    # Rimuovi import di MappaState da qui, usa cls=type(self) o nome diretto
                    nuovo_stato = MappaState(nome_luogo=destinazione_luogo)
                    gioco.push_stato(nuovo_stato)
                except Exception as e:
                     logger.error(f"Errore durante la creazione o il push del nuovo stato per {destinazione_luogo}: {e}")
                     gioco.io.mostra_messaggio(f"Errore nel tentativo di andare a {destinazione_luogo}.")
            else:
                 logger.error("Metodo 'push_stato' non trovato sull'oggetto gioco.")
                 gioco.io.mostra_messaggio("Errore: Impossibile cambiare luogo.")

        # Azioni di Dialogo Generiche (basate su ID NPG)
        elif azione_id.startswith("DIALOGO_"):
            nome_npg_target = azione_id.replace("DIALOGO_", "").replace("_", " ").title()
            # Cerca l'NPG nella lista di quelli presenti
            npg_trovato = self.npg_presenti.get(nome_npg_target)
            if npg_trovato:
                logger.info(f"Avvio dialogo con NPG: {nome_npg_target}")
                if hasattr(gioco, 'push_stato'):
                    stato_dialogo = DialogoState(npg=npg_trovato, stato_precedente=self)
                    gioco.push_stato(stato_dialogo)
                else:
                    logger.error("Metodo 'push_stato' non trovato sull'oggetto gioco.")
                    gioco.io.mostra_messaggio("Errore: Impossibile avviare dialogo.")
            else:
                logger.warning(f"NPG target '{nome_npg_target}' per azione dialogo non trovato in {self.nome_luogo}.")
                gioco.io.mostra_messaggio(f"Non trovi {nome_npg_target} qui.")

        # Azioni Specifiche del Luogo (delegate a helper method)
        elif azione_id in ["APRI_MENU_COMPRA", "APRI_MENU_VENDI", "ORDINA_BEVANDA", "GIOCO_DADI"]:
             self._handle_azione_specifica_luogo(gioco, azione_id, context)
        
        # TODO: Aggiungere gestione per altre azioni comuni (es. APRI_INVENTARIO, SALVA_GIOCO) 
        
        else:
            logger.warning(f"Azione menu non riconosciuta o non gestita: '{azione_id}' in {self.nome_luogo}")
            if gioco and hasattr(gioco, 'io'):
                gioco.io.mostra_messaggio("Opzione non ancora implementata.")
            
        # Aggiorna l'UI dopo aver processato l'azione
        self.ui_aggiornata = False 

    # AGGIUNTO: Metodo principale per processare azioni dal client (WebSocket/HTTP)
    def process_azione_luogo(self, user_id: str, azione: str, dati_azione: dict):
        """
        Processa un'azione specifica richiesta per questo luogo.

        Args:
            user_id (str): ID dell'utente che ha richiesto l'azione (per logging/validazione).
            azione (str): L'identificativo dell'azione (es. 'muovi', 'interagisci_oggetto').
            dati_azione (dict): Dati aggiuntivi necessari per l'azione.
        """
        logger.debug(f"[{self.nome_stato}] Ricevuta azione_luogo: user_id={user_id}, azione='{azione}', dati='{dati_azione}'")
        
        giocatore = self.gioco.get_giocatore_by_user_id(user_id)
        if not giocatore:
            logger.error(f"[{self.nome_stato}] Giocatore non trovato per user_id {user_id} durante process_azione_luogo.")
            # Considera di emettere una notifica di errore al client specifico
            return {"success": False, "error": "Giocatore non trovato"}

        if azione == "muovi":
            return self._handle_movimento_azione(giocatore, dati_azione)
        elif azione == "interagisci_oggetto":
            # Esempio: implementare _handle_interazione_oggetto_azione
            # return self._handle_interazione_oggetto_azione(giocatore, dati_azione)
            logger.info(f"[{self.nome_stato}] Azione '{azione}' ricevuta, ma non ancora implementata in process_azione_luogo.")
            pass # Implementare altre azioni
        elif azione == "dialoga_npg":
            # Esempio: implementare _handle_dialogo_npg_azione
            # return self._handle_dialogo_npg_azione(giocatore, dati_azione)
            logger.info(f"[{self.nome_stato}] Azione '{azione}' ricevuta, ma non ancora implementata in process_azione_luogo.")
            pass # Implementare altre azioni
        else:
            # Potrebbe trattarsi di un'azione specifica del luogo (es. compra, vendi)
            # che dovrebbe essere gestita da _handle_azione_specifica_luogo se esiste.
            if hasattr(self, '_handle_azione_specifica_luogo'):
                return self._handle_azione_specifica_luogo(giocatore, azione, dati_azione)
            else:
                logger.warning(f"[{self.nome_stato}] Azione '{azione}' non riconosciuta o gestore specifico non trovato.")
                return {"success": False, "error": f"Azione '{azione}' non riconosciuta"}
        
        return {"success": True, "message": "Azione processata (o in attesa di implementazione)"} # Ritorno generico

    def _handle_movimento_azione(self, giocatore, dati_azione):
        """
        Gestisce l'azione di movimento proveniente da process_azione_luogo.
        """
        direzione = dati_azione.get('direzione')
        if not direzione:
            logger.warning(f"[{self.nome_stato}] Direzione mancante per il movimento del giocatore {giocatore.id}.")
            self.event_bus.emit(Events.GAME_NOTIFICATION,
                                session_id=self.gioco.session_id,
                                player_id=giocatore.id,
                                message_type='error',
                                message='Direzione per il movimento non specificata.')
            return {"success": False, "error": "Direzione mancante"}

        # Normalizza la direzione
        direzione = direzione.lower()
        
        # Mappa per conversione direzioni inglesi->italiane
        direction_map = {
            'up': 'nord',
            'down': 'sud',
            'left': 'ovest',
            'right': 'est',
            'north': 'nord',
            'south': 'sud',
            'west': 'ovest',
            'east': 'est'
        }
        
        # Converti se necessario
        direzione_normalizzata = direction_map.get(direzione, direzione)

        dx, dy = 0, 0
        if direzione_normalizzata == 'nord': dy = -1
        elif direzione_normalizzata == 'sud': dy = 1
        elif direzione_normalizzata == 'ovest': dx = -1
        elif direzione_normalizzata == 'est': dx = 1
        # Aggiungere 'nord-est', 'nord-ovest', 'sud-est', 'sud-ovest' se necessario
        elif direzione_normalizzata == 'su': dy = -1 # Alias comune
        elif direzione_normalizzata == 'giu': dy = 1 # Alias comune
        elif direzione_normalizzata == 'sinistra': dx = -1 # Alias comune
        elif direzione_normalizzata == 'destra': dx = 1 # Alias comune
        else:
            logger.warning(f"[{self.nome_stato}] Direzione non valida '{direzione}' (normalizzata: '{direzione_normalizzata}') per il movimento del giocatore {giocatore.id}.")
            self.event_bus.emit(Events.GAME_NOTIFICATION,
                                session_id=self.gioco.session_id,
                                player_id=giocatore.id,
                                message_type='error',
                                message=f"Direzione '{direzione}' non valida.")
            return {"success": False, "error": f"Direzione '{direzione}' non valida"}

        if not hasattr(self.gioco, 'gestore_mappe') or not self.gioco.gestore_mappe:
             logger.error(f"[{self.nome_stato}] GestoreMappe non disponibile nel contesto di gioco per il movimento.")
             self.event_bus.emit(Events.GAME_NOTIFICATION,
                                session_id=self.gioco.session_id,
                                player_id=giocatore.id,
                                message_type='error',
                                message='Errore interno del server: Gestore mappe non trovato.')
             return {"success": False, "error": "Gestore mappe non trovato"}

        risultato_movimento = giocatore.muovi(dx, dy, self.gioco.gestore_mappe)

        if risultato_movimento and risultato_movimento.get('successo'):
            logger.info(f"[{self.nome_stato}] Movimento riuscito per giocatore {giocatore.id}: nuova posizione ({giocatore.x},{giocatore.y}) su mappa '{giocatore.mappa_corrente}'. Messaggio: {risultato_movimento.get('messaggio')}")
            
            cambio_mappa_info = risultato_movimento.get('cambio_mappa_richiesto')
            if cambio_mappa_info:
                # cambio_mappa_info può essere solo il nome della mappa o un dict più complesso
                # Entita.muovi restituisce una stringa per destinazione_porta
                # e un dict per trigger_transizione
                
                destinazione_mappa = None
                nuova_mappa_coords = None

                if isinstance(cambio_mappa_info, str): # Caso semplice: solo nome mappa (da porta)
                    destinazione_mappa = cambio_mappa_info
                    nuova_mappa_coords = risultato_movimento.get('nuova_mappa_coords') # Specifico per porta
                elif isinstance(cambio_mappa_info, dict): # Caso trigger_transizione
                    destinazione_mappa = cambio_mappa_info.get('destinazione_mappa')
                    nuova_mappa_coords = cambio_mappa_info.get('pos_destinazione')

                if destinazione_mappa:
                    logger.info(f"[{self.nome_stato}] Giocatore {giocatore.id} sta cambiando mappa verso '{destinazione_mappa}'. Coords target: {nuova_mappa_coords}")
                    
                    # Aggiorna la mappa corrente del giocatore PRIMA di emettere CHANGE_STATE
                    # e prima che il nuovo stato venga inizializzato.
                    giocatore.mappa_corrente = destinazione_mappa
                    if nuova_mappa_coords and isinstance(nuova_mappa_coords, (list, tuple)) and len(nuova_mappa_coords) == 2:
                        giocatore.x = nuova_mappa_coords[0]
                        giocatore.y = nuova_mappa_coords[1]
                    # Se nuova_mappa_coords non è fornito, il nuovo stato userà la pos_iniziale_giocatore della mappa.

                    self.event_bus.emit(Events.CHANGE_STATE,
                                        session_id=self.gioco.session_id,
                                        player_id=giocatore.id,
                                        nuovo_stato_nome=destinazione_mappa,
                                        payload={'target_coords': nuova_mappa_coords, 'previous_map': self.nome_luogo}
                                       )
                    logger.info(f"[{self.nome_stato}] Evento CHANGE_STATE emesso per {giocatore.id} verso {destinazione_mappa}.")
                    return {"success": True, "message": risultato_movimento.get('messaggio'), "cambio_mappa": destinazione_mappa}
                else:
                     logger.error(f"[{self.nome_stato}] 'cambio_mappa_richiesto' presente ma 'destinazione_mappa' non valida: {cambio_mappa_info}")
                     # Tratta come movimento normale se la destinazione non è chiara
                     self.event_bus.emit(Events.PLAYER_POSITION_UPDATED,
                                    session_id=self.gioco.session_id,
                                    player_id=giocatore.id,
                                    nuova_posizione=(giocatore.x, giocatore.y),
                                    mappa_corrente=giocatore.mappa_corrente)
                     return {"success": True, "message": "Movimento effettuato, ma transizione mappa fallita."}

            else:
                # Movimento avvenuto con successo all'interno della stessa mappa
                self.event_bus.emit(Events.PLAYER_POSITION_UPDATED,
                                    session_id=self.gioco.session_id,
                                    player_id=giocatore.id,
                                    nuova_posizione=(giocatore.x, giocatore.y),
                                    mappa_corrente=giocatore.mappa_corrente) # o self.nome_luogo
                logger.info(f"[{self.nome_stato}] Evento PLAYER_POSITION_UPDATED emesso per {giocatore.id} a ({giocatore.x},{giocatore.y}) su {giocatore.mappa_corrente}.")
                return {"success": True, "message": risultato_movimento.get('messaggio')}
        
        elif risultato_movimento: # Movimento fallito ma abbiamo un risultato
            logger.warning(f"[{self.nome_stato}] Movimento fallito per giocatore {giocatore.id}. Messaggio: {risultato_movimento.get('messaggio')}")
            self.event_bus.emit(Events.GAME_NOTIFICATION,
                                session_id=self.gioco.session_id,
                                player_id=giocatore.id,
                                message_type='error',
                                message=risultato_movimento.get('messaggio', 'Non puoi muoverti lì.'))
            return {"success": False, "error": risultato_movimento.get('messaggio', 'Movimento fallito')}
        else: # Nessun risultato dal movimento, errore imprevisto
            logger.error(f"[{self.nome_stato}] Errore imprevisto durante il movimento per giocatore {giocatore.id}. Il metodo muovi ha restituito None.")
            self.event_bus.emit(Events.GAME_NOTIFICATION,
                                session_id=self.gioco.session_id,
                                player_id=giocatore.id,
                                message_type='error',
                                message='Errore fatale durante il tentativo di movimento.')
            return {"success": False, "error": "Errore fatale nel movimento"}

    def to_dict_per_client(self):
        """
        Converte lo stato in un dizionario per la serializzazione.
        
        Returns:
            dict: Rappresentazione dello stato in formato dizionario
        """
        return serializzazione.to_dict(self)

    def _handle_player_move_event(self, **kwargs):
        """Gestisce l'evento PLAYER_MOVE, esegue il movimento e emette eventi di risultato."""
        logger.info(f"[MappaState._handle_player_move_event] Ricevuto evento PLAYER_MOVE con kwargs: {kwargs}")
        
        # Estrai i parametri dai kwargs
        direction = kwargs.get('direction')
        entity_id = kwargs.get('entity_id')
        session_id = kwargs.get('session_id')
        
        logger.info(f"[MappaState._handle_player_move_event] direction={direction}, entity_id={entity_id}, session_id={session_id}")
        
        gioco = self.gioco
        if not gioco or not hasattr(gioco, 'giocatore') or not gioco.giocatore:
            logger.error("Tentativo di gestire PLAYER_MOVE senza giocatore o contesto di gioco.")
            return

        if not hasattr(gioco, 'gestore_mappe'):
            logger.error("GestoreMappe non trovato nel contesto di gioco.")
            return

        # Mappa le direzioni inglesi a quelle italiane per retrocompatibilità
        direction_map = {
            'up': 'nord',
            'down': 'sud',
            'left': 'ovest',
            'right': 'est',
            'north': 'nord',
            'south': 'sud',
            'west': 'ovest',
            'east': 'est'
        }
        
        # Converti la direzione se necessario
        direction_normalized = direction_map.get(direction.lower(), direction.lower())
        
        dx, dy = self.direzioni.get(direction_normalized, (0,0))
        if dx == 0 and dy == 0:
            logger.warning(f"Direzione movimento non riconosciuta: {direction} (normalizzata: {direction_normalized})")
            self.emit_event(Events.MOVEMENT_BLOCKED, 
                            entity_id=gioco.giocatore.id, 
                            reason="Direzione non valida", 
                            details=f"Direzione fornita: {direction}",
                            from_pos=(gioco.giocatore.x, gioco.giocatore.y),
                            to_pos=(gioco.giocatore.x, gioco.giocatore.y) # to_pos non cambia
                            )
            return

        vecchia_x, vecchia_y = gioco.giocatore.x, gioco.giocatore.y
        mappa_corrente_iniziale = gioco.giocatore.mappa_corrente

        # Chiama il metodo muovi dell'entità Giocatore
        # Questo metodo ora contiene tutta la logica di validazione, collisione, e aggiornamento coordinate
        risultato_movimento = gioco.giocatore.muovi(dx, dy, gioco.gestore_mappe)

        if risultato_movimento.get("successo"):
            nuova_x, nuova_y = risultato_movimento.get("nuova_posizione", (vecchia_x, vecchia_y))
            messaggio = risultato_movimento.get("messaggio", "Movimento effettuato.")
            gioco.io.mostra_messaggio(messaggio) # Mostra il messaggio specifico dal metodo muovi

            # Emetti evento ENTITY_MOVED con le coordinate finali
            self.emit_event(Events.ENTITY_MOVED, 
                            entity_id=gioco.giocatore.id, 
                            from_pos=(vecchia_x, vecchia_y), 
                            to_pos=(nuova_x, nuova_y),
                            map_id=gioco.giocatore.mappa_corrente # La mappa potrebbe essere cambiata
                           )
            
            # Gestisci cambio mappa se richiesto dal risultato del movimento
            mappa_destinazione = risultato_movimento.get("cambio_mappa_richiesto")
            if mappa_destinazione:
                coords_nuova_mappa = risultato_movimento.get("nuova_mappa_coords") # Es. (x, y) o None
                self._gestisci_cambio_mappa_event(mappa_corrente_iniziale, mappa_destinazione, coords_nuova_mappa)
            else:
                # Se non c'è cambio mappa, la UI va aggiornata per la posizione
                self.ui_aggiornata = False
                # Controlla i trigger di posizione sulla nuova casella
                self._check_position_triggers_locale(nuova_x, nuova_y)

        else: # Movimento fallito
            messaggio_errore = risultato_movimento.get("messaggio", "Non puoi muoverti lì.")
            gioco.io.mostra_messaggio(messaggio_errore)
            self.emit_event(Events.MOVEMENT_BLOCKED, 
                            entity_id=gioco.giocatore.id, 
                            reason=risultato_movimento.get("reason", "ostacolo"), # Prendere un reason più specifico se muovi() lo fornisce 
                            details=messaggio_errore,
                            from_pos=(vecchia_x, vecchia_y),
                            # to_pos è la posizione che si è tentato di raggiungere
                            to_pos=(vecchia_x + dx, vecchia_y + dy) 
                           )

    def _check_position_triggers_locale(self, x, y):
        """
        Controlla se ci sono trigger sulla posizione attuale del giocatore.
        Questo metodo è adattato dalla funzione check_position_triggers in movimento.py
        """
        gioco = self.gioco
        if not gioco or not hasattr(gioco, 'giocatore') or not gioco.giocatore:
            return

        mappa_corrente_nome = gioco.giocatore.mappa_corrente
        mappa = gioco.gestore_mappe.ottieni_mappa(mappa_corrente_nome)
        
        if not mappa:
            logger.warning(f"_check_position_triggers_locale: Mappa '{mappa_corrente_nome}' non trovata.")
            return
        
        # Ottieni i trigger nella posizione
        # Assumiamo che mappa.get_triggers_at(x, y) esista e restituisca una lista di trigger.
        # Se non esiste, dobbiamo implementarlo in Mappa.py
        triggers = []
        if hasattr(mappa, 'get_triggers_at') and callable(mappa.get_triggers_at):
            triggers = mappa.get_triggers_at(x, y)
        else:
            logger.warning(f"Metodo 'get_triggers_at' non trovato sull'oggetto mappa '{mappa.nome}'. Nessun trigger di posizione verrà controllato.")

        if not triggers: # Se non ci sono triggers o il metodo non esiste/non restituisce nulla
            return

        for trigger_data in triggers: # Rinominato trigger in trigger_data per evitare conflitto con modulo trigger
            trigger_id = trigger_data.get('id', f"trigger_{x}_{y}")
            trigger_type = trigger_data.get('type', 'generic')
            
            logger.info(f"Trigger attivato a ({x},{y}): id={trigger_id}, tipo={trigger_type}")
            # Emetti evento di trigger attivato
            self.emit_event(
                Events.TRIGGER_ACTIVATED,
                trigger_id=trigger_id,
                trigger_type=trigger_type,
                entity_id=gioco.giocatore.id,
                position=(x, y),
                map_id=mappa_corrente_nome,
                trigger_data=trigger_data # Includi tutti i dati del trigger
            )
            
            # Gestisci tipi specifici di trigger (logica spostata da movimento.py)
            if trigger_type == 'trappola':
                damage = trigger_data.get('damage', 1)
                # Assumiamo che l'entità Giocatore abbia un metodo subisci_danno
                if hasattr(gioco.giocatore, 'subisci_danno'):
                    gioco.giocatore.subisci_danno(damage) # Potrebbe essere necessario passare il contesto 'gioco'
                    gioco.io.mostra_messaggio(f"Hai attivato una trappola! Hai subito {damage} danni.")
                    
                    self.emit_event(
                        Events.DAMAGE_TAKEN,
                        entity_id=gioco.giocatore.id,
                        damage=damage,
                        damage_type="trap", # dano da trappola
                        source_id=trigger_id
                    )
            
            elif trigger_type == 'tesoro':
                # Per evitare che il tesoro venga raccolto più volte, lo stato del trigger
                # dovrebbe essere gestito o nella mappa stessa (modificando i dati del trigger)
                # o in MappaState (es. self.trigger_raccolti).
                # Qui assumiamo una gestione semplice:
                if not trigger_data.get('raccolto', False): # Aggiungi un campo 'raccolto' ai dati del trigger
                    trigger_data['raccolto'] = True # Segna come raccolto (questo modifica il dict in memoria)
                    
                    contents = trigger_data.get('contents', [])
                    gioco.io.mostra_messaggio("Hai trovato un tesoro!")
                    if contents:
                        # TODO: Aggiungere items all'inventario del giocatore
                        # Per ora, mostriamo solo cosa c'è dentro
                        contenuto_str = []
                        for item_info in contents:
                            if isinstance(item_info, dict):
                                item_name = item_info.get('nome', item_info.get('id', 'Oggetto sconosciuto'))
                                item_qty = item_info.get('quantita', 1)
                                contenuto_str.append(f"{item_name} (x{item_qty})")
                            else: # Se è solo una stringa con l'ID/nome
                                contenuto_str.append(str(item_info))
                        gioco.io.mostra_messaggio(f"Contenuto: {', '.join(contenuto_str)}")
                    
                    self.emit_event(
                        Events.TREASURE_FOUND,
                        entity_id=gioco.giocatore.id,
                        treasure_id=trigger_id,
                        contents=contents # Contenuto del tesoro
                    )
                else:
                    gioco.io.mostra_messaggio("Hai già controllato questo punto.")
            
            elif trigger_type == 'evento':
                event_id_specifico = trigger_data.get('event_id') # event_id specifico del trigger
                if event_id_specifico:
                    gioco.io.mostra_messaggio("Si attiva un evento...")
                    # Emetti un evento più specifico che può essere gestito da sistemi dedicati
                    self.emit_event(
                        Events.CUSTOM_GAME_EVENT, # Un tipo di evento generico per eventi di gioco custom
                        event_name=event_id_specifico, # Nome specifico dell'evento dal trigger
                        entity_id=gioco.giocatore.id,
                        position=(x,y),
                        trigger_data=trigger_data
                    )
            # Altri tipi di trigger possono essere aggiunti qui

    def _gestisci_cambio_mappa_event(self, mappa_origine_nome, mappa_destinazione_nome, target_pos_nuova_mappa):
        """Gestisce la logica di cambio mappa quando richiesto da un evento di movimento."""
        gioco = self.gioco
        if not gioco:
            return

        logger.info(f"Richiesta cambio mappa da '{mappa_origine_nome}' a '{mappa_destinazione_nome}' con target_pos: {target_pos_nuova_mappa}")

        # Qui dobbiamo notificare il GameStateManager di cambiare lo stato.
        # Il GameStateManager dovrebbe poi gestire il pop dello stato corrente (MappaState)
        # e il push di un nuovo MappaState per mappa_destinazione_nome.
        
        # Prima di cambiare stato, assicuriamoci che il giocatore sia sulla nuova mappa
        # e alle coordinate corrette. Il metodo `muovi` dovrebbe aver già aggiornato x,y
        # sulla mappa di transizione, ma `giocatore.mappa_corrente` deve essere aggiornato.
        
        giocatore = gioco.giocatore
        
        # Ottieni la definizione della mappa di destinazione per trovare la posizione iniziale se target_pos non è fornito
        mappa_dest_data = gioco.gestore_mappe.ottieni_mappa(mappa_destinazione_nome)
        if not mappa_dest_data:
            logger.error(f"Impossibile caricare i dati per la mappa di destinazione '{mappa_destinazione_nome}'. Cambio mappa annullato.")
            gioco.io.mostra_messaggio(f"Errore: la mappa '{mappa_destinazione_nome}' non esiste.")
            return

        if target_pos_nuova_mappa and isinstance(target_pos_nuova_mappa, (list, tuple)) and len(target_pos_nuova_mappa) == 2:
            nuova_x_giocatore, nuova_y_giocatore = target_pos_nuova_mappa
        else:
            nuova_x_giocatore, nuova_y_giocatore = mappa_dest_data.pos_iniziale_giocatore
            logger.info(f"Nessuna coordinata specifica per '{mappa_destinazione_nome}', usando pos_iniziale_giocatore: ({nuova_x_giocatore},{nuova_y_giocatore})")

        # Aggiorna lo stato interno del giocatore PRIMA di notificare il cambio di stato FSM
        giocatore.mappa_corrente = mappa_destinazione_nome
        giocatore.x = nuova_x_giocatore
        giocatore.y = nuova_y_giocatore
        logger.info(f"Giocatore '{giocatore.id}' aggiornato: mappa='{giocatore.mappa_corrente}', pos=({giocatore.x},{giocatore.y})")

        # Notifica il GameStateManager
        if self.game_state_manager:
            # Creiamo una NUOVA istanza di MappaState per il luogo destinazione
            try:
                logger.info(f"Richiesta a GameStateManager di cambiare stato a un nuovo MappaState per '{mappa_destinazione_nome}'")
                # Usare cls=type(self) per creare una nuova istanza dello stesso tipo di stato (MappaState)
                # Questo assicura che se MappaState è sottoclassato (es. TavernaState che eredita da MappaState),
                # venga creata un'istanza della classe corretta.
                # Passiamo il game_state_manager all'init del nuovo stato.
                nuovo_stato_mappa = type(self)(nome_luogo=mappa_destinazione_nome, game_state_manager=self.game_state_manager)
                self.game_state_manager.change_state(nuovo_stato_mappa)
                logger.info(f"Cambio stato a MappaState per '{mappa_destinazione_nome}' richiesto a GameStateManager.")
            except Exception as e:
                logger.error(f"Errore durante la creazione o il push del nuovo stato MappaState per '{mappa_destinazione_nome}': {e}", exc_info=True)
                gioco.io.mostra_messaggio(f"Errore critico nel tentativo di viaggiare a {mappa_destinazione_nome}.")
        else:
            logger.error("GameStateManager non disponibile in MappaState per gestire il cambio di stato.")
            gioco.io.mostra_messaggio("Errore fatale: sistema di gestione stati non trovato.")

        # L'evento MAP_CHANGE originale potrebbe non essere più necessario qui se il cambio stato FSM gestisce la notifica
        # Tuttavia, per coerenza con la gestione eventi esistente, potremmo ancora emetterlo.
        self.emit_event(Events.MAP_CHANGE, 
                        entity_id=giocatore.id,
                        from_map=mappa_origine_nome, 
                        to_map=mappa_destinazione_nome,
                        target_pos=(nuova_x_giocatore, nuova_y_giocatore)
                       )
        # L'aggiornamento UI (self.ui_aggiornata = False) sarà gestito dal nuovo stato quando entra. 