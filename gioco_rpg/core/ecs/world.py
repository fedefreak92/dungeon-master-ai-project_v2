import uuid
import logging
from typing import Dict, List, Set, Type, Optional, Any, TYPE_CHECKING
from collections import defaultdict

# Import delle classi ECS
from .entity import Entity
from .component import Component
from .system import System
from world.gestore_mappe import GestitoreMappe
from entities.giocatore import Giocatore

if TYPE_CHECKING:
    from states.base.enhanced_base_state import EnhancedBaseState

logger = logging.getLogger(__name__)

class World:
    """
    Rappresenta il mondo di gioco, contenente tutte le entità e i sistemi.
    Coordina l'interazione tra i vari componenti del sistema ECS.
    """
    
    def __init__(self):
        """Inizializza un nuovo mondo"""
        self.entities: Dict[str, Entity] = {}  # Entità indicizzate per ID
        self.systems: List[System] = []  # Sistemi di gioco
        self.events: List[Dict[str, Any]] = []  # Eventi da processare
        self.pending_events: List[Dict[str, Any]] = []  # Eventi in attesa di processamento
        self.entities_by_tag: Dict[str, Set[Entity]] = defaultdict(set)  # Entità indicizzate per tag
        self.component_types: Dict[str, Type[Component]] = {}  # Tipi di componenti registrati
        self.temporary_states: Dict[str, Any] = {}  # Stati temporanei del gioco
        
        # Attributi aggiuntivi necessari per la compatibilità
        self.io = None  # Oggetto per input/output
        self.gestore_mappe = GestitoreMappe()  # Gestore delle mappe di gioco
        
        # Attributi per la FSM
        self.current_fsm_state: Optional['EnhancedBaseState'] = None
        self.fsm_stack: List['EnhancedBaseState'] = []
        self.session_id: Optional[str] = None

    @property
    def giocatore(self):
        """
        Ottiene l'entità giocatore
        
        Returns:
            Entity: L'entità giocatore
        """
        return self.get_player_entity()
        
    @giocatore.setter
    def giocatore(self, value: Any): # Cambiato tipo a Any per flessibilità
        """
        Imposta l'entità giocatore.
        Può essere un'istanza di gioco_rpg.entities.giocatore.Giocatore
        o un'istanza di core.ecs.entity.Entity (con i componenti necessari).
        """
        # Rimuove il tag player da tutte le entità che lo hanno precedentemente
        # Questo per assicurare che solo una entità sia il giocatore corrente.
        current_players = self.find_entities_by_tag("player")
        for p_entity in current_players:
            # Non rimuovere il tag se stiamo ri-settando la stessa entità o value è None
            if value is None or getattr(p_entity, 'id', None) != getattr(value, 'id', None):
                if hasattr(p_entity, 'remove_tag') and callable(getattr(p_entity, 'remove_tag')): # Per core.ecs.entity.Entity
                    p_entity.remove_tag("player")
                elif hasattr(p_entity, 'tags') and isinstance(getattr(p_entity, 'tags', None), set): # Per gioco_rpg.entities.Entita
                    getattr(p_entity, 'tags').discard("player")
                
                self._reindex_tags_for_entity(p_entity) # Assicura che entities_by_tag sia aggiornato
                display_name_p_entity = getattr(p_entity, 'nome', getattr(p_entity, 'name', getattr(p_entity, 'id', 'N/A')))
                logger.info(f"Rimosso tag 'player' dalla precedente entità giocatore: {display_name_p_entity}")


        if value is None:
            logger.warning("Tentativo di impostare world.giocatore a None. Le entità precedenti con tag 'player' sono state ripulite.")
            return

        entity_to_be_player = None

        try:
            from entities.giocatore import Giocatore as RPGGiocatore
            is_rpg_giocatore = isinstance(value, RPGGiocatore)
        except ImportError:
            is_rpg_giocatore = False

        if is_rpg_giocatore:
            logger.info(f"Impostazione di un'istanza di gioco_rpg.entities.giocatore.Giocatore come giocatore del mondo: {value.nome} (ID: {value.id})")
            entity_to_be_player = value
            if entity_to_be_player.id not in self.entities:
                self.add_entity(entity_to_be_player)
            
            # Assicura che abbia il tag 'player' (per gioco_rpg.entities.Entita/Giocatore)
            if not hasattr(entity_to_be_player, 'tags') or not isinstance(entity_to_be_player.tags, set):
                entity_to_be_player.tags = set() # Inizializza se mancante o tipo sbagliato
            if "player" not in entity_to_be_player.tags:
                entity_to_be_player.tags.add("player")
                self._reindex_tags_for_entity(entity_to_be_player)
            display_name_value_legacy = getattr(value, 'nome', getattr(value, 'name', value.id)) # value qui è RPGGiocatore, ha 'nome'
            logger.info(f"Giocatore legacy '{display_name_value_legacy}' (ID: {value.id}) impostato e taggato.")

        elif hasattr(value, 'components') and isinstance(getattr(value, 'components', None), dict) and hasattr(value, 'add_tag'):
            # È un'entità ECS (core.ecs.entity.Entity)
            display_name_value_ecs = getattr(value, 'name', value.id) # value qui è Entity, ha 'name'
            logger.info(f"Impostazione di un'istanza di core.ecs.entity.Entity come giocatore del mondo: {display_name_value_ecs} (ID: {value.id})")
            entity_to_be_player = value
            if entity_to_be_player.id not in self.entities:
                self.add_entity(entity_to_be_player)
            if not entity_to_be_player.has_tag("player"):
                 entity_to_be_player.add_tag("player")
                 self._reindex_tags_for_entity(entity_to_be_player) # add_entity già lo fa se il tag è nuovo
            logger.info(f"Entità ECS '{value.name}' (ID: {value.id}) impostata e taggata come giocatore.")
        else:
            logger.error(f"Tipo non supportato per world.giocatore: {type(value)}. Non è né un Giocatore legacy né un Entity ECS.")
            return

        # Log finale per confermare
        final_players = self.find_entities_by_tag("player")
        if entity_to_be_player and len(final_players) == 1 and final_players[0].id == entity_to_be_player.id:
            display_name_player = getattr(entity_to_be_player, 'nome', getattr(entity_to_be_player, 'name', entity_to_be_player.id))
            logger.info(f"world.giocatore impostato con successo. Entità giocatore attuale: {display_name_player}")
        elif entity_to_be_player and len(final_players) > 1:
            ids = [getattr(p, 'id', 'N/A') for p in final_players]
            logger.warning(f"ATTENZIONE: Più entità ({len(final_players)}, IDs: {ids}) sono taggate come 'player' dopo l'impostazione.")
        elif entity_to_be_player and not final_players:
            logger.warning(f"ATTENZIONE: Nessuna entità è taggata come 'player' dopo il tentativo di impostazione per {entity_to_be_player.id}.")
        elif not entity_to_be_player:
             logger.error("entity_to_be_player non è stato definito correttamente nel setter.")

    def _reindex_tags_for_entity(self, entity: Any):
        """Metodo helper per aggiornare gli indici dei tag per una specifica entità."""
        if not hasattr(entity, 'id'):
            logger.warning(f"Tentativo di reindicizzare tag per entità senza ID: {type(entity)}")
            return

        entity_id = entity.id
        
        # Rimuovi vecchi indici per questa entità basati sull'ID
        for tag_name, entities_in_tag in list(self.entities_by_tag.items()): # Itera su una copia per modifiche sicure
            to_remove_from_set = None
            for e_in_set in entities_in_tag:
                if hasattr(e_in_set, 'id') and e_in_set.id == entity_id:
                    to_remove_from_set = e_in_set
                    break
            if to_remove_from_set:
                entities_in_tag.remove(to_remove_from_set)
                if not entities_in_tag: # Se il set diventa vuoto, rimuovi la chiave del tag
                    del self.entities_by_tag[tag_name]

        current_tags_source = None
        if hasattr(entity, 'tags') and isinstance(entity.tags, set):
            current_tags_source = entity.tags
        elif hasattr(entity, 'tags') and isinstance(entity.tags, list): # Meno ideale, ma supportato
            current_tags_source = set(entity.tags)
        
        if current_tags_source:
            for tag in current_tags_source:
                self.entities_by_tag[tag].add(entity) # Aggiunge l'istanza corrente
            display_name_entity_reindex = getattr(entity, 'nome', getattr(entity, 'name', entity_id))
            logger.debug(f"Reindicizzati tag per l'entità '{display_name_entity_reindex}'. Tag attuali: {current_tags_source}")
        else:
            display_name_entity_reindex_fail = getattr(entity, 'nome', getattr(entity, 'name', entity_id))
            logger.debug(f"Nessun tag da reindicizzare per l'entità '{display_name_entity_reindex_fail}' (tags non trovati o formato non supportato).")

    def add_entity(self, entity: Entity) -> Entity:
        """
        Aggiunge un'entità al mondo
        
        Args:
            entity: Entità da aggiungere
            
        Returns:
            Entity: L'entità aggiunta
        """
        # Genera un ID se necessario
        if not entity.id:
            entity.id = str(uuid.uuid4())
            
        # Aggiungi l'entità alla mappa
        self.entities[entity.id] = entity
        
        # Aggiungi l'entità agli indici per tag
        for tag in entity.tags:
            self.entities_by_tag[tag].add(entity)
            logger.debug(f"Aggiunto tag '{tag}' all'entità '{entity.nome}' (ID: {entity.id})")
            
        # Aggiungi log per verificare i tag del giocatore
        if 'player' in entity.tags:
            logger.info(f"Aggiunta entità giocatore al mondo: {entity.nome} (ID: {entity.id}) con tag: {entity.tags}")
            logger.info(f"Numero di entità con tag 'player' dopo l'aggiunta: {len(self.entities_by_tag.get('player', set()))}")
            
        # Registra l'entità con i sistemi appropriati
        for system in self.systems:
            system.register_entity(entity)
            
        # Aggiorna l'indice dei tag dopo aver aggiunto l'entità e i suoi tag
        self._reindex_tags_for_entity(entity)

        display_name_add = getattr(entity, 'nome', getattr(entity, 'name', entity.id))
        logger.debug(f"Entità '{display_name_add}' (ID: {entity.id}) aggiunta al mondo")
        return entity
        
    def remove_entity(self, entity_id: str) -> bool:
        """
        Rimuove un'entità dal mondo
        
        Args:
            entity_id: ID dell'entità da rimuovere
            
        Returns:
            bool: True se l'entità è stata rimossa, False se non esisteva
        """
        if entity_id not in self.entities:
            return False
            
        entity = self.entities[entity_id]
        
        # Rimuovi l'entità dai sistemi
        for system in self.systems:
            system.unregister_entity(entity)
            
        # Rimuovi l'entità dagli indici per tag
        for tag in list(entity.tags): # Itera su una copia se entity.tags può cambiare
            if tag in self.entities_by_tag and entity in self.entities_by_tag[tag]:
                self.entities_by_tag[tag].remove(entity)
                if not self.entities_by_tag[tag]: # Rimuovi il tag dall'indice se il set è vuoto
                    del self.entities_by_tag[tag]
                
        # Rimuovi l'entità dalla mappa
        del self.entities[entity_id]
        
        display_name_remove = getattr(entity, 'nome', getattr(entity, 'name', entity_id))
        logger.debug(f"Entità '{display_name_remove}' (ID: {entity_id}) rimossa dal mondo")
        return True
        
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """
        Recupera un'entità dal suo ID
        
        Args:
            entity_id: ID dell'entità da recuperare
            
        Returns:
            Optional[Entity]: L'entità corrispondente o None se non esiste
        """
        return self.entities.get(entity_id)
        
    def find_entities_by_tag(self, tag: str) -> List[Entity]:
        """
        Trova tutte le entità con un determinato tag
        
        Args:
            tag: Tag da cercare
            
        Returns:
            List[Entity]: Lista delle entità con il tag specificato
        """
        return list(self.entities_by_tag.get(tag, set()))
        
    def find_entities_with_component(self, component_type: str) -> List[Entity]:
        """
        Trova tutte le entità con un determinato tipo di componente
        
        Args:
            component_type: Tipo di componente da cercare
            
        Returns:
            List[Entity]: Lista delle entità con il componente specificato
        """
        return [entity for entity in self.entities.values() if entity.has_component(component_type)]
        
    def add_system(self, system: System) -> System:
        """
        Aggiunge un sistema al mondo
        
        Args:
            system: Sistema da aggiungere
            
        Returns:
            System: Il sistema aggiunto
        """
        # Aggiungi il sistema alla lista
        self.systems.append(system)
        
        # Ordina i sistemi per priorità (priorità più alta = eseguito prima)
        self.systems.sort(key=lambda s: -s.priority)
        
        # Registra entità esistenti con il sistema
        for entity in self.entities.values():
            system.register_entity(entity)
            
        logger.debug(f"Sistema {system.__class__.__name__} aggiunto al mondo")
        return system
        
    def remove_system(self, system_type: Type[System]) -> bool:
        """
        Rimuove un sistema dal mondo
        
        Args:
            system_type: Tipo del sistema da rimuovere
            
        Returns:
            bool: True se il sistema è stato rimosso, False se non esisteva
        """
        for i, system in enumerate(self.systems):
            if isinstance(system, system_type):
                # Rimuovi il sistema dalla lista
                removed_system = self.systems.pop(i)
                
                # Pulisci le entità registrate
                removed_system.clear_entities()
                
                logger.debug(f"Sistema {system_type.__name__} rimosso dal mondo")
                return True
                
        return False
        
    def get_system(self, system_type: Type[System]) -> Optional[System]:
        """
        Recupera un sistema dal suo tipo
        
        Args:
            system_type: Tipo del sistema da recuperare
            
        Returns:
            Optional[System]: Il sistema corrispondente o None se non esiste
        """
        for system in self.systems:
            if isinstance(system, system_type):
                return system
                
        return None
        
    def create_entity(self, name: str = None) -> Entity:
        """
        Crea una nuova entità e la aggiunge al mondo
        
        Args:
            name: Nome dell'entità (opzionale)
            
        Returns:
            Entity: La nuova entità
        """
        entity = Entity(name=name)
        return self.add_entity(entity)
        
    def register_component_type(self, component_type: str, component_class: Type[Component]) -> None:
        """
        Registra un tipo di componente
        
        Args:
            component_type: Nome del tipo di componente
            component_class: Classe del componente
        """
        self.component_types[component_type] = component_class
        logger.debug(f"Tipo di componente '{component_type}' registrato")
        
    def create_component(self, component_type: str, entity: Entity, **kwargs) -> Optional[Component]:
        """
        Crea un nuovo componente di un tipo registrato
        
        Args:
            component_type: Tipo di componente da creare
            entity: Entità a cui associare il componente
            **kwargs: Parametri da passare al costruttore del componente
            
        Returns:
            Optional[Component]: Il nuovo componente o None se il tipo non è registrato
        """
        if component_type not in self.component_types:
            logger.warning(f"Tentativo di creare un componente di tipo '{component_type}' non registrato")
            return None
            
        component_class = self.component_types[component_type]
        component = component_class(entity, **kwargs)
        entity.add_component(component_type, component)
        
        # Aggiorna la registrazione dell'entità nei sistemi
        for system in self.systems:
            if system.should_process_entity(entity):
                system.register_entity(entity)
            else:
                system.unregister_entity(entity)
                
        return component
        
    def add_event(self, event: Dict[str, Any]) -> None:
        """
        Aggiunge un evento alla coda
        
        Args:
            event: Evento da aggiungere
        """
        self.events.append(event)
        
    def add_pending_event(self, event: Dict[str, Any]) -> None:
        """
        Aggiunge un evento alla coda degli eventi pendenti
        
        Args:
            event: Evento da aggiungere
        """
        self.pending_events.append(event)
        
    def update(self, delta_time: float) -> None:
        """
        Aggiorna tutti i sistemi attivi
        
        Args:
            delta_time: Tempo trascorso dall'ultimo aggiornamento
        """
        # Aggiungi gli eventi pendenti alla coda principale
        if self.pending_events:
            self.events.extend(self.pending_events)
            self.pending_events.clear()
            
        # Processa tutti i sistemi attivi
        for system in self.systems:
            if system.is_active():
                system.process(delta_time, self.events)
                
        # Svuota la coda degli eventi
        self.events.clear()
        
    def get_temporary_state(self, state_name: str) -> Optional[Any]:
        """
        Recupera uno stato temporaneo dal suo nome
        
        Args:
            state_name: Nome dello stato da recuperare
            
        Returns:
            Optional[Any]: Lo stato temporaneo o None se non esiste
        """
        return self.temporary_states.get(state_name)
        
    def has_state(self, state_name: str) -> bool:
        """
        Verifica se esiste uno stato con il nome specificato
        
        Args:
            state_name: Nome dello stato da verificare
            
        Returns:
            bool: True se lo stato esiste, False altrimenti
        """
        return state_name in self.temporary_states
        
    def get_state(self, state_name: str) -> Optional[Any]:
        """
        Recupera uno stato dal suo nome (alias di get_temporary_state)
        
        Args:
            state_name: Nome dello stato da recuperare
            
        Returns:
            Optional[Any]: Lo stato o None se non esiste
        """
        return self.get_temporary_state(state_name)
        
    def add_state(self, state_name: str, state_data: Any) -> None:
        """
        Aggiunge uno stato al mondo (alias di set_temporary_state)
        
        Args:
            state_name: Nome dello stato da aggiungere
            state_data: Dati dello stato
        """
        self.set_temporary_state(state_name, state_data)
        
    def set_temporary_state(self, state_name: str, state_data: Any) -> None:
        """
        Imposta uno stato temporaneo
        
        Args:
            state_name: Nome dello stato da impostare
            state_data: Dati dello stato
        """
        self.temporary_states[state_name] = state_data
        logger.debug(f"Stato temporaneo '{state_name}' impostato")
        
    def remove_temporary_state(self, state_name: str) -> bool:
        """
        Rimuove uno stato temporaneo
        
        Args:
            state_name: Nome dello stato da rimuovere
            
        Returns:
            bool: True se lo stato è stato rimosso, False se non esisteva
        """
        if state_name in self.temporary_states:
            del self.temporary_states[state_name]
            logger.debug(f"Stato temporaneo '{state_name}' rimosso")
            return True
        return False
        
    def get_all_temporary_states(self) -> Dict[str, Any]:
        """
        Recupera tutti gli stati temporanei
        
        Returns:
            Dict[str, Any]: Dizionario con tutti gli stati temporanei
        """
        return self.temporary_states.copy()
        
    def serialize(self) -> Dict[str, Any]:
        """
        Serializza il mondo in un dizionario
        
        Returns:
            Dict[str, Any]: Dizionario rappresentante lo stato del mondo
        """
        try:
            # Serializza entità
            entities_data = {}
            for entity_id, entity_obj in self.entities.items(): # Nome variabile cambiato per chiarezza
                try:
                    serialized_entity_data = None
                    if hasattr(entity_obj, 'to_dict') and callable(getattr(entity_obj, 'to_dict')):
                        serialized_entity_data = entity_obj.to_dict()
                    elif hasattr(entity_obj, 'serialize') and callable(getattr(entity_obj, 'serialize')):
                        # Questo è per core.ecs.entity.Entity
                        serialized_entity_data = entity_obj.serialize()
                    
                    if serialized_entity_data:
                        # Assicurati che il campo 'tipo' sia presente.
                        # Giocatore.to_dict() e Entita.to_dict() lo impostano.
                        # core.ecs.Entity.serialize() no.
                        if 'tipo' not in serialized_entity_data:
                            serialized_entity_data['tipo'] = type(entity_obj).__name__
                        entities_data[entity_id] = serialized_entity_data
                    else:
                        logger.warning(f"L'entità {entity_id} (tipo: {type(entity_obj).__name__}) non ha né to_dict né serialize "
                                       f"oppure hanno restituito None. Salvo info base.")
                        entities_data[entity_id] = {
                            "id": entity_id,
                            "name": getattr(entity_obj, 'nome', getattr(entity_obj, 'name', getattr(entity_obj, 'id', 'unknown_id'))),
                            "tipo": type(entity_obj).__name__
                        }
                except Exception as e:
                    logger.error(f"Errore nella serializzazione dell'entità {entity_id} (tipo: {type(entity_obj).__name__}): {e}", exc_info=True)
                    entities_data[entity_id] = {
                        "id": entity_id,
                        "name": getattr(entity_obj, 'nome', getattr(entity_obj, 'name', getattr(entity_obj, 'id', 'unknown_id'))),
                        "tipo": type(entity_obj).__name__,
                        "__serialization_error__": str(e)
                    }
            
            # Serializza eventi - assicura che non ci siano riferimenti circolari
            events_data = []
            for event in self.events:
                try:
                    if isinstance(event, dict):
                        # Crea una copia superficiale dell'evento
                        event_copy = {}
                        for k, v in event.items():
                            # Filtra solo i tipi base serializzabili
                            if isinstance(v, (str, int, float, bool)) or v is None:
                                event_copy[k] = v
                            elif isinstance(v, (list, tuple)):
                                # Converti in lista serializzabile
                                event_copy[k] = self._convert_to_serializable(v)
                            elif isinstance(v, dict):
                                # Converti in dizionario serializzabile
                                event_copy[k] = self._convert_to_serializable(v)
                            else:
                                # Per altri tipi, usa la rappresentazione stringa
                                event_copy[k] = str(v)
                        events_data.append(event_copy)
                    else:
                        # Se non è un dizionario, includi solo il tipo
                        events_data.append({"type": str(type(event).__name__)})
                except Exception as e:
                    logger.error(f"Errore serializzando un evento: {e}")
                    # Ignora questo evento
            
            # Serializza eventi in attesa con lo stesso approccio
            pending_events_data = []
            for event in self.pending_events:
                try:
                    if isinstance(event, dict):
                        event_copy = {}
                        for k, v in event.items():
                            # Filtra solo i tipi base serializzabili
                            if isinstance(v, (str, int, float, bool)) or v is None:
                                event_copy[k] = v
                            elif isinstance(v, (list, tuple)):
                                # Converti in lista serializzabile
                                event_copy[k] = self._convert_to_serializable(v)
                            elif isinstance(v, dict):
                                # Converti in dizionario serializzabile
                                event_copy[k] = self._convert_to_serializable(v)
                            else:
                                # Per altri tipi, usa la rappresentazione stringa
                                event_copy[k] = str(v)
                        pending_events_data.append(event_copy)
                    else:
                        pending_events_data.append({"type": str(type(event).__name__)})
                except Exception as e:
                    logger.error(f"Errore serializzando un evento in attesa: {e}")
                    # Ignora questo evento
            
            # Serializza stati temporanei
            temporary_states_data = {}
            for state_name, state_value in self.temporary_states.items():
                if state_name == "io":
                    logger.info("Saltato oggetto io durante la serializzazione")
                    continue
                
                logger.debug(f"[SERIALIZE_TEMP_STATE_DEBUG] Serializzo stato temporaneo: '{state_name}', Tipo: {type(state_value).__name__}, Ha to_dict: {hasattr(state_value, 'to_dict')}")
                try:
                    if hasattr(state_value, 'to_dict') and callable(getattr(state_value, 'to_dict')):
                        temporary_states_data[state_name] = state_value.to_dict()
                    elif hasattr(state_value, 'serialize') and callable(getattr(state_value, 'serialize')):
                        temporary_states_data[state_name] = state_value.serialize()
                    elif isinstance(state_value, dict):
                        # Creazione manuale di una copia sicura per evitare riferimenti circolari
                        temporary_states_data[state_name] = self._convert_to_serializable(state_value)
                    elif isinstance(state_value, (list, tuple)):
                        # Per liste e tuple, converti in lista serializzabile
                        temporary_states_data[state_name] = self._convert_to_serializable(state_value)
                    elif isinstance(state_value, (str, int, float, bool)) or state_value is None:
                        # I tipi di base sono già serializzabili
                        temporary_states_data[state_name] = state_value
                    else:
                        # Se non è serializzabile, tenta di convertirlo in stringa
                        try:
                            temporary_states_data[state_name] = {'__str__': str(state_value), '__type__': state_value.__class__.__name__}
                        except:
                            # In caso di errore, salta questo stato
                            logger.warning(f"Impossibile serializzare lo stato temporaneo {state_name}")
                except Exception as e:
                    logger.error(f"Errore nella serializzazione dello stato temporaneo {state_name}: {e}")
                    # Salva un segnaposto per indicare che lo stato esisteva ma non è stato serializzato
                    temporary_states_data[state_name] = {'__error__': 'Stato non serializzabile', '__type__': str(type(state_value))}
            
            # Gestione specifica dell'attributo io nella classe World
            if hasattr(self, 'io') and self.io is not None:
                logger.info("Attributo io presente nel World, escluso dalla serializzazione")
                # Non serializzare l'oggetto io, sarà ricreato alla deserializzazione
            
            # Verifica finale: assicurati che il dizionario sia effettivamente serializzabile
            import json
            try:
                # Prova a verificare che il dizionario sia JSON-compatibile
                # Questo può aiutare a identificare riferimenti circolari
                json.dumps({"entities": entities_data})
                json.dumps({"events": events_data})
                json.dumps({"pending_events": pending_events_data})
                json.dumps({"temporary_states": temporary_states_data})
            except (TypeError, OverflowError, ValueError) as je:
                logger.error(f"I dati non sono JSON-compatibili: {je}")
                # Se ci sono errori, rendi sicuro il dizionario finale
                # Elimina profondamente oggetti non serializzabili
                entities_data = {k: {"id": k, "name": v.get("name", "unknown")} for k, v in entities_data.items()}
                events_data = []
                pending_events_data = []
                temporary_states_data = {}
            
            return {
                "entities": entities_data,
                "events": events_data,
                "pending_events": pending_events_data,
                "temporary_states": temporary_states_data
            }
        except Exception as e:
            logger.error(f"Errore generale nella serializzazione del mondo: {e}")
            # Ritorna un dizionario minimo ma valido
            return {
                "entities": {},
                "events": [],
                "pending_events": [],
                "temporary_states": {}
            }
        
    def _convert_to_serializable(self, obj):
        """
        Converte un oggetto in un formato serializzabile per JSON.
        
        Args:
            obj: Oggetto da convertire
            
        Returns:
            Versione serializzabile dell'oggetto
        """
        if isinstance(obj, (str, int, float, bool)) or obj is None:
            # Tipi di base già serializzabili
            return obj
        elif isinstance(obj, (list, tuple)):
            # Per liste e tuple, converti ogni elemento
            return [self._convert_to_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            # Per dizionari, converti ogni chiave e valore
            result = {}
            for k, v in obj.items():
                # Assicurati che la chiave sia una stringa
                key = str(k)
                # Converti il valore
                result[key] = self._convert_to_serializable(v)
            return result
        elif hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
            # Usa il metodo to_dict se disponibile
            return self._convert_to_serializable(obj.to_dict())
        elif hasattr(obj, 'serialize') and callable(getattr(obj, 'serialize')):
            # Usa il metodo serialize se disponibile
            return self._convert_to_serializable(obj.serialize())
        else:
            # Per altri oggetti, converti in stringa
            try:
                return str(obj)
            except:
                return f"<<Oggetto non serializzabile: {type(obj).__name__}>>"
        
    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> 'World':
        """
        Deserializza un mondo da un dizionario
        
        Args:
            data: Dizionario contenente i dati del mondo
            
        Returns:
            World: Il mondo deserializzato
        """
        world = cls()
        world.session_id = data.get("session_id_persisted")
        
        if not isinstance(data, dict):
            logger.error(f"Dati non validi per la deserializzazione: {type(data)}")
                         
            return world
        
        try:
            # Deserializza entità
            entities_data = data.get("entities", {})
            for entity_id, entity_data_dict in entities_data.items():
                entity_to_add = None
                try:
                    entity_type_str = entity_data_dict.get("tipo")
                    has_player_tag = "player" in entity_data_dict.get("tags", [])
                    
                    # Logica migliorata per determinare la classe target
                    target_class = Entity # Default

                    if entity_type_str == "Giocatore":
                        from entities.giocatore import Giocatore
                        target_class = Giocatore
                    elif entity_type_str == "Nemico":
                        from entities.nemico import Nemico # Assumendo che esista
                        target_class = Nemico
                    elif entity_type_str == "NPG":
                        from entities.npg import NPG # Assumendo che esista
                        target_class = NPG
                    elif not entity_type_str and has_player_tag:
                        # Se il tipo è mancante MA ha il tag player, proviamo a deserializzarlo come Giocatore
                        # Questo è un tentativo di recupero per sessioni più vecchie/corrotte.
                        logger.warning(f"Campo 'tipo' mancante per entità {entity_id} ma ha il tag 'player'. "
                                       f"Tentativo di deserializzazione come Giocatore.")
                        try:
                            from entities.giocatore import Giocatore
                            target_class = Giocatore
                            entity_data_dict['tipo'] = 'Giocatore' # Forza il tipo per coerenza futura
                        except ImportError:
                            logger.error(f"Impossibile importare la classe Giocatore per il fallback dell'entità {entity_id}. Sarà Entity base.")
                            entity_type_str = "Entity" # Aggiorna per il logging successivo
                            target_class = Entity
                    elif not entity_type_str:
                        logger.warning(f"Campo 'tipo' mancante nei dati per entità {entity_id}. Deserializzo come Entity base.")
                        entity_type_str = "Entity" # Per i log e per evitare problemi dopo
                        target_class = Entity
                    # Aggiungi altri tipi qui se necessario

                    # MODIFICA CHIAVE: Seleziona il metodo di deserializzazione corretto
                    if hasattr(target_class, 'from_dict') and callable(getattr(target_class, 'from_dict')):
                        # Giocatore, Entita (da gioco_rpg.entities) usano from_dict
                        entity_to_add = target_class.from_dict(entity_data_dict)
                        logger.debug(f"Deserializzata entità {entity_id} (tipo: {target_class.__name__}) usando from_dict.")
                    elif hasattr(target_class, 'deserialize') and callable(getattr(target_class, 'deserialize')):
                        # core.ecs.entity.Entity usa deserialize
                        entity_to_add = target_class.deserialize(entity_data_dict)
                        logger.debug(f"Deserializzata entità {entity_id} (tipo: {target_class.__name__}) usando deserialize.")
                    else:
                        logger.warning(f"La classe {target_class.__name__} per entità {entity_id} non ha un metodo from_dict né deserialize. Impossibile istanziare.")
                        entity_to_add = None

                    if entity_to_add:
                        logger.info(f"[DESERIALIZE_DEBUG] Entità ID: {entity_id}, Tipo Dichiarato: {entity_type_str}, Tipo Istanziato: {type(entity_to_add).__name__}, Dati Entità: {entity_data_dict}")
                        world.add_entity(entity_to_add)
                    else:
                        logger.error(f"Deserializzazione ha restituito None per entità {entity_id} con tipo dichiarato {entity_type_str}. Dati Entità: {entity_data_dict}")

                except ImportError as ie:
                    logger.error(f"Errore di import per il tipo di entità '{entity_type_str}' durante deserializzazione di {entity_id}: {ie}. Deserializzo come Entity base.")
                    # Tentativo di fallback a Entity base
                    try:
                        fallback_entity = Entity.deserialize(entity_data_dict)
                        if fallback_entity:
                            world.add_entity(fallback_entity)
                        else:
                            logger.error(f"Anche il fallback a Entity.deserialize è fallito per {entity_id}.")
                    except Exception as fallback_e:
                        logger.error(f"Eccezione durante il fallback a Entity.deserialize per {entity_id}: {fallback_e}", exc_info=True)
                except Exception as e:
                    logger.error(f"Errore generale nella deserializzazione dell'entità specifica {entity_id} (tipo dichiarato: {entity_data_dict.get('tipo')}): {e}", exc_info=True)
                    # Non aggiungere questa entità se la deserializzazione fallisce gravemente
            
            # Deserializza eventi
            world.events = data.get("events", [])
            world.pending_events = data.get("pending_events", [])
            
            # Deserializza stati temporanei
            temporary_states_data = data.get("temporary_states", {})
            
            # Gestiamo la deserializzazione specializzata di stati noti
            for state_name, state_value in temporary_states_data.items():
                try:
                    # Ignora gli stati che erano segnalati come non serializzabili
                    if isinstance(state_value, dict) and '__error__' in state_value:
                        logger.warning(f"Saltato stato temporaneo non serializzabile: {state_name}")
                        continue

                    # Stati speciali che richiedono una conversione
                    if state_name == "combattimento" and isinstance(state_value, dict):
                        # Assicurati che lo stato combattimento abbia sempre gli attributi necessari
                        if "azioni" not in state_value:
                            state_value["azioni"] = {}
                        # Altre correzioni e normalizzazioni
                        if "dati_temporanei" not in state_value:
                            state_value["dati_temporanei"] = {}
                        if "fase" not in state_value:
                            state_value["fase"] = "scelta"
                    
                    # Memorizza lo stato nel mondo
                    world.temporary_states[state_name] = state_value
                except Exception as e:
                    logger.error(f"Errore durante la deserializzazione dello stato {state_name}: {e}")
            
            # Reinizializza l'oggetto IO per evitare problemi di serializzazione
            # Questo oggetto verrà impostato correttamente dalla sessione che carica il mondo
            world.io = None
            
            return world
            
        except Exception as e:
            logger.error(f"Errore generale nella deserializzazione del mondo: {e}")
            return world
        
    def clear(self) -> None:
        """Rimuove tutte le entità e gli eventi dal mondo"""
        # Svuota tutti i sistemi
        for system in self.systems:
            system.clear_entities()
            
        # Svuota le mappe e gli eventi
        self.entities.clear()
        self.entities_by_tag.clear()
        self.events.clear()
        self.pending_events.clear()
        
        logger.debug("Mondo svuotato completamente")
        
    def get_player_entity(self) -> Optional[Giocatore]:
        """
        Recupera l'entità del giocatore, assicurandosi che sia un'istanza di Giocatore.
        """
        player_entities_tagged = self.find_entities_by_tag("player") 
        logger.info(f"[get_player_entity] Ricerca entità con tag 'player': trovate {len(player_entities_tagged)} entità.")

        if not player_entities_tagged:
            logger.error("[get_player_entity] Nessuna entità con tag 'player' trovata.")
            # Tentativo di fallback: cercare un'istanza di Giocatore non taggata tra tutte le entità
            # Questo potrebbe essere lento se ci sono molte entità.
            try:
                from entities.giocatore import Giocatore as RPGGiocatore # Import specifico
                for entity_obj in self.entities.values():
                    if isinstance(entity_obj, RPGGiocatore):
                        logger.warning(f"[get_player_entity] FALLBACK: Trovato Giocatore (ID: {entity_obj.id}) non taggato. Tento di usarlo e aggiungo tag 'player'.")
                        # Aggiungi il tag e reindex
                        if not hasattr(entity_obj, 'tags') or not isinstance(entity_obj.tags, set):
                            entity_obj.tags = set()
                        if "player" not in entity_obj.tags:
                             entity_obj.tags.add("player")
                             self._reindex_tags_for_entity(entity_obj) # Reindex esplicitamente
                        return entity_obj # Restituisce la prima istanza di Giocatore trovata
            except ImportError:
                logger.error("[get_player_entity] Impossibile importare Giocatore per il fallback.")
            
            logger.error("[get_player_entity] Fallback fallito o Giocatore non importabile. Nessun Giocatore trovato.")
            return None

        # Abbiamo almeno un'entità con tag 'player'
        # Se ce n'è più di una, prendiamo la prima e logghiamo un warning.
        if len(player_entities_tagged) > 1:
            ids = [getattr(p, 'id', 'N/A') for p in player_entities_tagged]
            logger.warning(f"[get_player_entity] ATTENZIONE: Trovate {len(player_entities_tagged)} entità con tag 'player' (IDs: {ids}). Verrà usata la prima: {getattr(player_entities_tagged[0], 'id', 'N/A')}.")
        
        potential_player_entity = player_entities_tagged[0]
        entity_id = getattr(potential_player_entity, 'id', 'N/A')
        entity_name = getattr(potential_player_entity, 'nome', getattr(potential_player_entity, 'name', 'N/A'))
        entity_actual_type_name = type(potential_player_entity).__name__

        logger.info(f"[get_player_entity] Entità con tag 'player' selezionata: ID={entity_id}, Nome='{entity_name}', TipoAttuale='{entity_actual_type_name}'")

        try:
            from entities.giocatore import Giocatore as RPGGiocatore
            if isinstance(potential_player_entity, RPGGiocatore):
                logger.info(f"[get_player_entity] L'entità (ID: {entity_id}) è un'istanza di Giocatore. Perfetto.")
                return potential_player_entity
        except ImportError:
             logger.error(f"[get_player_entity] Impossibile importare Giocatore per controllo istanza su entità {entity_id}.")
             # Non possiamo confermare, ma se ha il tag player, la restituiamo con un warning.
             logger.warning(f"[get_player_entity] Restituisco entità {entity_id} come giocatore basandomi sul tag, ma non ho potuto verificare il tipo Giocatore.")
             return potential_player_entity # Restituisce l'oggetto così com'è

        # Se arriva qui, l'entità taggata come 'player' NON è un'istanza di Giocatore (o non abbiamo potuto verificarlo).
        logger.warning(f"[get_player_entity] ATTENZIONE: L'entità con tag 'player' (ID: {entity_id}) è di tipo '{entity_actual_type_name}' e non è (o non è stato possibile verificare come) 'Giocatore'.")
        
        # A questo punto, la deserializzazione dovrebbe aver già creato il tipo corretto se 'tipo: Giocatore' era nei dati.
        # Se è un core.ecs.entity.Entity, è probabile un problema nel file di salvataggio o nella logica di serializzazione precedente.
        # Non tentiamo una conversione qui, perché potrebbe portare a perdita di dati o stato inconsistente.
        # Il problema dovrebbe essere risolto a monte (corretta serializzazione o file di salvataggio).

        logger.error(f"[get_player_entity] L'entità con tag 'player' (ID: {entity_id}) non è un'istanza di Giocatore. Questo indica un problema nel salvataggio o nella deserializzazione. Impossibile restituire un Giocatore valido.")
        return None
        
    def inizializza_sistemi(self):
        """
        Inizializza e registra i sistemi di base per il mondo di gioco.
        Questo metodo carica i sistemi ECS principali come movimento, rendering, etc.
        """
        logger.info("Inizializzazione dei sistemi di base per il mondo di gioco...")
        
        # Importa e inizializza i sistemi necessari
        try:
            # Importazione dinamica per evitare dipendenze circolari
            from core.ecs.systems.movement_system import MovementSystem
            from core.ecs.systems.collision_system import CollisionSystem
            from core.ecs.systems.interaction_system import InteractionSystem
            
            # Crea e aggiungi i sistemi
            movement_system = MovementSystem()
            self.add_system(movement_system)
            logger.debug("Sistema di movimento aggiunto al mondo")
            
            collision_system = CollisionSystem()
            self.add_system(collision_system)
            logger.debug("Sistema di collisione aggiunto al mondo")
            
            interaction_system = InteractionSystem()
            self.add_system(interaction_system)
            logger.debug("Sistema di interazione aggiunto al mondo")
            
            # Aggiungi altri sistemi se necessario
            
            logger.info("Sistemi di base inizializzati con successo")
        except ImportError as e:
            logger.warning(f"Impossibile importare alcuni sistemi: {e}. Funzionalità limitate.")
        except Exception as e:
            logger.error(f"Errore durante l'inizializzazione dei sistemi: {e}")
        
    def cambia_mappa(self, id_mappa, x, y):
        """
        Cambia la mappa corrente del giocatore
        
        Args:
            id_mappa (str): ID della mappa di destinazione
            x (int): Coordinata X iniziale nella nuova mappa
            y (int): Coordinata Y iniziale nella nuova mappa
            
        Returns:
            bool: True se il cambio mappa è riuscito, False altrimenti
        """
        logger.info(f"Tentativo di cambio mappa verso {id_mappa} alle coordinate ({x}, {y})")
        
        try:
            # Ottieni l'entità giocatore
            player_entity = self.get_player_entity()
            if not player_entity:
                logger.error("Impossibile cambiare mappa: nessuna entità giocatore trovata")
                return False
            
            # Registra la mappa corrente prima del cambio per debug
            old_map = None
            
            # Verifica se stiamo usando un'entità ECS o un oggetto Giocatore
            if hasattr(player_entity, "get_component") and callable(getattr(player_entity, "get_component")):
                logger.info("Uso modalità entità ECS per il cambio mappa")
                # Caso entità ECS
                position_component = player_entity.get_component("position")
                if not position_component:
                    logger.error("Impossibile cambiare mappa: il giocatore non ha un componente posizione")
                    return False
                
                # Ottieni la mappa corrente
                try:
                    old_map = position_component.map_name
                    logger.info(f"Mappa attuale del giocatore: {old_map}")
                except Exception as e:
                    logger.warning(f"Impossibile leggere map_name: {e}")
                
                # Gestione per vari tipi di Position component
                try:
                    if hasattr(position_component, "__class__") and position_component.__class__.__name__ == "Position":
                        logger.info("Componente posizione di tipo namedtuple")
                        # È un namedtuple, dobbiamo sostituirlo con uno nuovo
                        if hasattr(player_entity, "mappa_corrente"):
                            # Se è un oggetto Giocatore, aggiorna direttamente gli attributi
                            player_entity.mappa_corrente = id_mappa
                            player_entity.x = x
                            player_entity.y = y
                            logger.info(f"Aggiornata posizione diretta: mappa={id_mappa}, x={x}, y={y}")
                        else:
                            # Crea un nuovo namedtuple e sostituisci il componente
                            from collections import namedtuple
                            Position = namedtuple('Position', ['x', 'y', 'map_name'])
                            # Verifica come è registrato il componente nell'entità
                            if hasattr(player_entity, "components") and isinstance(player_entity.components, dict):
                                player_entity.components["position"] = Position(x, y, id_mappa)
                                logger.info(f"Aggiornata posizione via components dict: mappa={id_mappa}, x={x}, y={y}")
                            elif hasattr(player_entity, "set_component") and callable(getattr(player_entity, "set_component")):
                                player_entity.set_component("position", Position(x, y, id_mappa))
                                logger.info(f"Aggiornata posizione via set_component: mappa={id_mappa}, x={x}, y={y}")
                            else:
                                logger.error("Impossibile aggiornare la posizione: struttura entità sconosciuta")
                                return False
                    else:
                        logger.info("Componente posizione standard")
                        # È un componente normale, prova ad aggiornare gli attributi
                        try:
                            position_component.map_name = id_mappa
                            position_component.x = x
                            position_component.y = y
                            logger.info(f"Aggiornati attributi del componente posizione: mappa={id_mappa}, x={x}, y={y}")
                        except AttributeError as e:
                            logger.error(f"Impossibile aggiornare gli attributi del componente posizione: {e}")
                            return False
                except Exception as e:
                    logger.error(f"Errore nella gestione del componente posizione: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    return False
            else:
                logger.info("Uso modalità oggetto Giocatore per il cambio mappa")
                # Caso oggetto Giocatore
                try:
                    old_map = getattr(player_entity, "mappa_corrente", None)
                    logger.info(f"Mappa attuale del giocatore: {old_map}")
                    player_entity.mappa_corrente = id_mappa
                    player_entity.x = x
                    player_entity.y = y
                    logger.info(f"Aggiornata posizione del giocatore: mappa={id_mappa}, x={x}, y={y}")
                except Exception as e:
                    logger.error(f"Errore nell'aggiornare la posizione dell'oggetto Giocatore: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    return False
            
            logger.info(f"Cambio mappa riuscito: da {old_map} a {id_mappa}, nuova posizione ({x}, {y})")
            
            # Genera un evento di cambio mappa
            try:
                map_change_event = {
                    "type": "map_change",
                    "player_id": player_entity.id,
                    "previous_map": old_map,
                    "new_map": id_mappa,
                    "position": {"x": x, "y": y}
                }
                self.add_event(map_change_event)
                logger.info(f"Evento cambio mappa generato: {map_change_event}")
            except Exception as e:
                logger.warning(f"Impossibile generare evento cambio mappa: {e}, ma proseguiamo comunque")
            
            return True
        except Exception as e:
            logger.error(f"Errore durante il cambio mappa: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False 

    # --- METODI FSM AGGIUNTI ---
    def get_current_fsm_state(self) -> Optional['EnhancedBaseState']:
        return self.current_fsm_state

    def _set_current_fsm_state_internal(self, new_state_instance: Optional['EnhancedBaseState']):
        """Metodo interno per cambiare lo stato ed eseguire enter/exit."""
        previous_state = self.current_fsm_state
        
        if previous_state and hasattr(previous_state, 'exit') and callable(getattr(previous_state, 'exit')):
            logger.debug(f"[World FSM - {self.session_id}] Eseguo exit per stato precedente: {type(previous_state).__name__}")
            previous_state.exit()
        
        self.current_fsm_state = new_state_instance
        logger.info(f"[World FSM - {self.session_id}] Stato FSM corrente impostato a: {type(new_state_instance).__name__ if new_state_instance else 'None'}")

        if new_state_instance:
            if hasattr(new_state_instance, 'set_game_context') and callable(getattr(new_state_instance, 'set_game_context')):
                new_state_instance.set_game_context(self) 
            elif hasattr(new_state_instance, 'gioco'): # Per compatibilità con stati più vecchi
                new_state_instance.gioco = self
            
            # Se gli stati necessitano di un game_state_manager e World ne ha uno:
            # if hasattr(new_state_instance, 'game_state_manager') and hasattr(self, 'game_state_manager'):
            #    new_state_instance.game_state_manager = self.game_state_manager

            if hasattr(new_state_instance, 'enter') and callable(getattr(new_state_instance, 'enter')):
                logger.debug(f"[World FSM - {self.session_id}] Eseguo enter per nuovo stato: {type(new_state_instance).__name__}")
                new_state_instance.enter()
        
        # Esempio di emissione evento EventBus per cambio stato globale
        # from core.event_bus import EventBus
        # import core.events as Events 
        # EventBus.get_instance().emit(Events.GAME_STATE_CHANGED, 
        #                             session_id=self.session_id,
        #                             new_state_name=type(new_state_instance).__name__ if new_state_instance else "None")

    def change_fsm_state(self, new_state_instance: 'EnhancedBaseState'):
        logger.info(f"[World FSM - {self.session_id}] Richiesta change_fsm_state a {type(new_state_instance).__name__}")
        self.fsm_stack.clear()
        self._set_current_fsm_state_internal(new_state_instance)

    def push_fsm_state(self, new_state_instance: 'EnhancedBaseState'):
        logger.info(f"[World FSM - {self.session_id}] Richiesta push_fsm_state con {type(new_state_instance).__name__}")
        if self.current_fsm_state:
            if hasattr(self.current_fsm_state, 'pause') and callable(getattr(self.current_fsm_state, 'pause')):
                 logger.debug(f"[World FSM - {self.session_id}] Eseguo pause per stato corrente: {type(self.current_fsm_state).__name__}")
                 self.current_fsm_state.pause()
            elif hasattr(self.current_fsm_state, 'exit') and callable(getattr(self.current_fsm_state, 'exit')): # Fallback se pause non esiste
                 logger.debug(f"[World FSM - {self.session_id}] Eseguo exit (come pause) per stato corrente: {type(self.current_fsm_state).__name__}")
                 self.current_fsm_state.exit() # Lo stato attuale esce prima di essere messo nello stack e rimpiazzato
            self.fsm_stack.append(self.current_fsm_state)
        self._set_current_fsm_state_internal(new_state_instance)

    def pop_fsm_state(self) -> Optional['EnhancedBaseState']:
        logger.info(f"[World FSM - {self.session_id}] Richiesta pop_fsm_state. Stack size attuale: {len(self.fsm_stack)}")
        # L'exit dello stato che viene poppato è già gestito da _set_current_fsm_state_internal
        # quando imposta il nuovo stato (che sarà quello precedente dallo stack, o None).
        
        if self.fsm_stack:
            previous_state_from_stack = self.fsm_stack.pop()
            self._set_current_fsm_state_internal(previous_state_from_stack) 
            # Se si vuole un comportamento di "resume" specifico per gli stati ripristinati:
            # if previous_state_from_stack and hasattr(previous_state_from_stack, 'resume') and callable(getattr(previous_state_from_stack, 'resume')):
            #    logger.debug(f"[World FSM - {self.session_id}] Eseguo resume per stato ripristinato: {type(previous_state_from_stack).__name__}")
            #    previous_state_from_stack.resume()
            # elif previous_state_from_stack and hasattr(previous_state_from_stack, 'enter'): # fallback a enter
            #    # L'enter è già chiamato da _set_current_fsm_state_internal
            #    pass
            return previous_state_from_stack
        else:
            logger.warning(f"[World FSM - {self.session_id}] Tentativo di pop da uno stack FSM vuoto.")
            self._set_current_fsm_state_internal(None)
            return None 