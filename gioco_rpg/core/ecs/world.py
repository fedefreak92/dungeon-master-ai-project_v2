import uuid
import logging
from typing import Dict, List, Set, Type, Optional, Any
from collections import defaultdict

# Import delle classi ECS
from .entity import Entity
from .component import Component
from .system import System
from world.gestore_mappe import GestitoreMappe

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
        
    @property
    def giocatore(self):
        """
        Ottiene l'entità giocatore
        
        Returns:
            Entity: L'entità giocatore
        """
        return self.get_player_entity()
        
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
            logger.debug(f"Aggiunto tag '{tag}' all'entità '{entity.name}' (ID: {entity.id})")
            
        # Aggiungi log per verificare i tag del giocatore
        if 'player' in entity.tags:
            logger.info(f"Aggiunta entità giocatore al mondo: {entity.name} (ID: {entity.id}) con tag: {entity.tags}")
            logger.info(f"Numero di entità con tag 'player' dopo l'aggiunta: {len(self.entities_by_tag.get('player', set()))}")
            
        # Registra l'entità con i sistemi appropriati
        for system in self.systems:
            system.register_entity(entity)
            
        logger.debug(f"Entità '{entity.name}' (ID: {entity.id}) aggiunta al mondo")
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
        for tag in entity.tags:
            if entity in self.entities_by_tag[tag]:
                self.entities_by_tag[tag].remove(entity)
                
        # Rimuovi l'entità dalla mappa
        del self.entities[entity_id]
        
        logger.debug(f"Entità '{entity.name}' (ID: {entity_id}) rimossa dal mondo")
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
            for entity_id, entity in self.entities.items():
                try:
                    entities_data[entity_id] = entity.serialize()
                except Exception as e:
                    # Log dell'errore e continua con la prossima entità
                    logger.error(f"Errore nella serializzazione dell'entità {entity_id}: {e}")
                    # Crea un record minimo per l'entità con informazioni base
                    entities_data[entity_id] = {"id": entity_id, "name": getattr(entity, 'name', 'unknown')}
                
            # Serializza eventi - assicura che non ci siano riferimenti circolari
            events_data = []
            for event in self.events:
                try:
                    if isinstance(event, dict):
                        # Crea una copia superficiale dell'evento
                        event_copy = {}
                        for k, v in event.items():
                            # Filtra solo i tipi base serializzabili
                            if isinstance(v, (str, int, float, bool, list, tuple, dict)) or v is None:
                                event_copy[k] = v
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
                            if isinstance(v, (str, int, float, bool, list, tuple, dict)) or v is None:
                                event_copy[k] = v
                        pending_events_data.append(event_copy)
                    else:
                        pending_events_data.append({"type": str(type(event).__name__)})
                except Exception as e:
                    logger.error(f"Errore serializzando un evento in attesa: {e}")
                    # Ignora questo evento
            
            # Serializza stati temporanei
            temporary_states_data = {}
            for state_name, state_value in self.temporary_states.items():
                # Salta l'oggetto io che non è serializzabile
                if state_name == "io":
                    logger.info("Saltato oggetto io durante la serializzazione")
                    continue
                    
                try:
                    # Gestisci la serializzazione degli stati
                    if hasattr(state_value, 'to_dict') and callable(getattr(state_value, 'to_dict')):
                        temporary_states_data[state_name] = state_value.to_dict()
                    elif hasattr(state_value, 'serialize') and callable(getattr(state_value, 'serialize')):
                        temporary_states_data[state_name] = state_value.serialize()
                    elif isinstance(state_value, dict):
                        # Creazione manuale di una copia sicura per evitare riferimenti circolari
                        temp_dict = {}
                        for k, v in state_value.items():
                            if isinstance(v, (str, int, float, bool)) or v is None:
                                # I tipi di base sono sicuri
                                temp_dict[k] = v
                            elif isinstance(v, (list, tuple)):
                                # Per liste e tuple, includi solo elementi di tipo base
                                safe_list = []
                                for item in v:
                                    if isinstance(item, (str, int, float, bool)) or item is None:
                                        safe_list.append(item)
                                    elif isinstance(item, dict):
                                        # Per dizionari innestati, includi solo le chiavi come stringhe
                                        safe_list.append(str(item))
                                    else:
                                        # Per altri oggetti, converti in stringa
                                        safe_list.append(str(item))
                                temp_dict[k] = safe_list
                            elif isinstance(v, dict):
                                # Per dizionari innestati, includi solo coppie chiave-valore di tipo base
                                safe_dict = {}
                                for sub_k, sub_v in v.items():
                                    if isinstance(sub_v, (str, int, float, bool)) or sub_v is None:
                                        safe_dict[str(sub_k)] = sub_v
                                    else:
                                        # Per valori complessi, converti in stringa
                                        safe_dict[str(sub_k)] = str(sub_v)
                                temp_dict[k] = safe_dict
                            else:
                                # Per qualsiasi altro tipo, converti in stringa
                                temp_dict[k] = str(v)
                        temporary_states_data[state_name] = temp_dict
                    elif isinstance(state_value, (str, int, float, bool)) or state_value is None:
                        temporary_states_data[state_name] = state_value
                    elif isinstance(state_value, (list, tuple)):
                        # Per liste e tuple, includi solo elementi di tipo base
                        safe_list = []
                        for item in state_value:
                            if isinstance(item, (str, int, float, bool)) or item is None:
                                safe_list.append(item)
                            else:
                                # Per altri oggetti, converti in stringa
                                safe_list.append(str(item))
                        temporary_states_data[state_name] = safe_list
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
        
        # Verifica che data sia un dizionario valido
        if not isinstance(data, dict):
            logger.error(f"Dati non validi per la deserializzazione: {type(data)}")
            return world
        
        try:
            # Deserializza entità
            entities_data = data.get("entities", {})
            for entity_id, entity_data in entities_data.items():
                try:
                    entity = Entity.deserialize(entity_data)
                    world.add_entity(entity)
                except Exception as e:
                    logger.error(f"Errore nella deserializzazione dell'entità {entity_id}: {e}")
                    # Continua con la prossima entità
            
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
        
    def get_player_entity(self) -> Optional['Entity']:
        """
        Recupera l'entità del giocatore
        
        Returns:
            Optional[Entity]: L'entità del giocatore o None se non esiste
        """
        # Cerca le entità con il tag "player"
        player_entities = self.find_entities_by_tag("player")
        logger.info(f"Ricerca entità con tag 'player': trovate {len(player_entities)} entità")
        
        if player_entities:
            logger.info(f"Trovata entità giocatore con tag: {player_entities[0].id} con nome {player_entities[0].name}")
            return player_entities[0]  # Restituisci la prima entità giocatore trovata
        
        # Piano B: Cerca entità basandoci sul nome
        logger.warning("Nessuna entità con tag 'player' trovata. Tentativo con nome entità...")
        for entity in self.entities.values():
            if entity.name.lower() in ["player", "testplayer"]:
                logger.info(f"Trovata entità giocatore dal nome: {entity.id} con nome {entity.name}")
                # Aggiunge automaticamente il tag
                entity.add_tag("player")
                return entity
        
        # Piano C: Cerca entità con attributo "è_giocatore"
        logger.warning("Nessuna entità con nome 'Player' trovata. Tentativo con attributo...")
        for entity in self.entities.values():
            if hasattr(entity, "è_giocatore") and entity.è_giocatore:
                logger.info(f"Trovata entità giocatore con attributo: {entity.id} con nome {entity.name}")
                # Aggiunge automaticamente il tag
                entity.add_tag("player")
                return entity
        
        logger.error("Nessuna entità giocatore trovata!")
        return None
        
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
            
            # Verifica se stiamo usando un'entità ECS o un oggetto Giocatore
            if hasattr(player_entity, "get_component") and callable(getattr(player_entity, "get_component")):
                # Caso entità ECS
                position_component = player_entity.get_component("position")
                if not position_component:
                    logger.error("Impossibile cambiare mappa: il giocatore non ha un componente posizione")
                    return False
                
                # Aggiorna la mappa e la posizione
                old_map = position_component.map_name
                position_component.map_name = id_mappa
                position_component.x = x
                position_component.y = y
            else:
                # Caso oggetto Giocatore
                old_map = getattr(player_entity, "mappa_corrente", None)
                player_entity.mappa_corrente = id_mappa
                player_entity.x = x
                player_entity.y = y
            
            logger.info(f"Cambio mappa riuscito: da {old_map} a {id_mappa}, nuova posizione ({x}, {y})")
            
            # Genera un evento di cambio mappa
            map_change_event = {
                "type": "map_change",
                "player_id": player_entity.id,
                "previous_map": old_map,
                "new_map": id_mappa,
                "position": {"x": x, "y": y}
            }
            self.add_event(map_change_event)
            
            return True
        except Exception as e:
            logger.error(f"Errore durante il cambio mappa: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False 