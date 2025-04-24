import logging
from ..system import System

logger = logging.getLogger(__name__)

class InteractionSystem(System):
    """
    Sistema responsabile per le interazioni tra entità e tra entità e ambiente di gioco.
    Gestisce interazioni come dialoghi, raccolta oggetti, attivazione di meccanismi, etc.
    """
    
    def __init__(self, priority=8):
        """
        Inizializza il sistema di interazione
        
        Args:
            priority (int): Priorità del sistema (valore più alto = aggiornato prima)
        """
        super().__init__(priority)
        self.required_components = ["interactable"]
        
    def should_process_entity(self, entity):
        """
        Determina se un'entità dovrebbe essere processata da questo sistema
        
        Args:
            entity: Entità da valutare
            
        Returns:
            bool: True se l'entità ha i componenti richiesti, False altrimenti
        """
        return (entity.is_active() and 
                (entity.has_component("interactable") or entity.has_tag("player")))
    
    def update(self, dt: float) -> None:
        """
        Aggiorna il sistema, elaborando tutte le entità registrate
        
        Args:
            dt: Delta time (tempo trascorso dall'ultimo aggiornamento)
        """
        if not self.active or not self.world:
            return
            
        # Implementazione: elabora ogni entità registrata
        for entity_id in list(self.entities):
            entity = self.world.get_entity(entity_id)
            if entity and entity.is_active() and self.should_process_entity(entity):
                try:
                    self.process_entity(entity, dt)
                except Exception as e:
                    logger.error(f"Errore nell'elaborazione dell'entità {entity_id} nel sistema {self.__class__.__name__}: {e}")
    
    def process(self, delta_time, events):
        """
        Elabora tutte le entità registrate
        
        Args:
            delta_time (float): Tempo trascorso dall'ultimo aggiornamento
            events (list): Lista di eventi da processare
        """
        # Processa eventi di interazione
        interaction_events = [e for e in events if e.get("type") == "interaction"]
        
        for event in interaction_events:
            initiator_id = event.get("initiator_id")
            target_id = event.get("target_id")
            interaction_type = event.get("interaction_type", "default")
            
            # Trova le entità coinvolte
            initiator = self.world.get_entity(initiator_id)
            target = self.world.get_entity(target_id)
            
            if not initiator or not target:
                continue
                
            # Esegui l'interazione
            self._perform_interaction(initiator, target, interaction_type)
            
        # Processa eventi di interazione con l'ambiente
        env_interaction_events = [e for e in events if e.get("type") == "environment_interaction"]
        
        for event in env_interaction_events:
            entity_id = event.get("entity_id")
            x = event.get("x", 0)
            y = event.get("y", 0)
            map_name = event.get("map_name", "")
            
            # Trova l'entità
            entity = self.world.get_entity(entity_id)
            if not entity:
                continue
                
            # Trova l'oggetto interattivo alle coordinate specificate
            interactable = self._find_interactable_at(x, y, map_name)
            if interactable:
                self._perform_interaction(entity, interactable, "environment")
    
    def process_entity(self, entity, dt: float) -> None:
        """
        Elabora una singola entità
        
        Args:
            entity: L'entità da elaborare
            dt: Delta time (tempo trascorso dall'ultimo aggiornamento)
        """
        # In questa implementazione base non ci sono aggiornamenti costanti per 
        # le entità nel sistema di interazione, poiché le interazioni sono principalmente
        # guidate dagli eventi
        pass
    
    def _perform_interaction(self, initiator, target, interaction_type):
        """
        Esegue un'interazione tra due entità
        
        Args:
            initiator: Entità che inizia l'interazione
            target: Entità obiettivo dell'interazione
            interaction_type (str): Tipo di interazione
        """
        # Se il target ha un componente interactable, usa la sua logica
        if target.has_component("interactable"):
            interactable = target.get_component("interactable")
            if hasattr(interactable, "on_interact"):
                interactable.on_interact(initiator)
                return
        
        # Implementazione di base per vari tipi di interazione
        if interaction_type == "talk":
            self._handle_talk_interaction(initiator, target)
        elif interaction_type == "examine":
            self._handle_examine_interaction(initiator, target)
        elif interaction_type == "pickup":
            self._handle_pickup_interaction(initiator, target)
        elif interaction_type == "use":
            self._handle_use_interaction(initiator, target)
        elif interaction_type == "environment":
            self._handle_environment_interaction(initiator, target)
        else:
            # Interazione generica
            self._handle_generic_interaction(initiator, target)
            
        # Notifica il sistema di eventi dell'interazione
        self.world.add_event({
            "type": "interaction_completed",
            "initiator_id": initiator.id,
            "target_id": target.id,
            "interaction_type": interaction_type
        })
    
    def _find_interactable_at(self, x, y, map_name):
        """
        Trova un oggetto interattivo alle coordinate specificate
        
        Args:
            x (float): Coordinata X
            y (float): Coordinata Y
            map_name (str): Nome della mappa
            
        Returns:
            Entity: Entità interattiva trovata, o None se non ce ne sono
        """
        # Ottieni tutte le entità registrate
        entities = self.get_entities()
        
        for entity in entities:
            if not entity.has_component("position") or not entity.has_component("interactable"):
                continue
                
            position = entity.get_component("position")
            
            # Verifica se l'entità è nella posizione specificata
            if (position.map_name == map_name and 
                int(position.x) == int(x) and 
                int(position.y) == int(y)):
                return entity
                
        # Verifica se c'è un oggetto interattivo nella mappa
        if self.world and self.world.gestore_mappe:
            mappa = self.world.gestore_mappe.ottieni_mappa(map_name)
            if mappa and hasattr(mappa, "ottieni_oggetto_a"):
                oggetto = mappa.ottieni_oggetto_a(int(x), int(y))
                if oggetto and hasattr(oggetto, "interagisci"):
                    return oggetto
                    
        return None
    
    def _handle_talk_interaction(self, initiator, target):
        """
        Gestisce un'interazione di dialogo
        
        Args:
            initiator: Entità che inizia l'interazione
            target: Entità obiettivo dell'interazione
        """
        # Verifica se il target è un NPC
        if target.has_tag("npc"):
            # Avvia un dialogo
            self.world.add_event({
                "type": "start_dialogue",
                "player_id": initiator.id,
                "npc_id": target.id
            })
    
    def _handle_examine_interaction(self, initiator, target):
        """
        Gestisce un'interazione di esame
        
        Args:
            initiator: Entità che inizia l'interazione
            target: Entità obiettivo dell'interazione
        """
        # Ottieni la descrizione dell'oggetto
        description = getattr(target, "description", f"Un {target.name}")
        
        # Invia un messaggio all'interfaccia IO
        if self.world and self.world.io:
            self.world.io.mostra_messaggio(description)
    
    def _handle_pickup_interaction(self, initiator, target):
        """
        Gestisce un'interazione di raccolta oggetto
        
        Args:
            initiator: Entità che inizia l'interazione
            target: Entità obiettivo dell'interazione
        """
        # Verifica se l'initiator ha un inventario
        if not initiator.has_component("inventory"):
            return
            
        # Verifica se il target è raccoglibile
        if not hasattr(target, "is_pickable") or not target.is_pickable:
            return
            
        # Aggiungi l'oggetto all'inventario
        inventory = initiator.get_component("inventory")
        
        # Gestione inventario integrata con il sistema esistente
        if hasattr(initiator, "inventario") and hasattr(target, "to_item"):
            # Usa il sistema di inventario esistente se disponibile
            item = target.to_item()
            initiator.inventario.append(item)
            
            # Rimuovi l'oggetto dal mondo
            self.world.remove_entity(target.id)
            
            # Invia messaggio
            if self.world and self.world.io:
                self.world.io.mostra_messaggio(f"Hai raccolto: {target.name}")
        elif hasattr(inventory, "add_item"):
            # Usa il componente ECS inventory
            inventory.add_item(target)
            
            # Rimuovi l'oggetto dal mondo
            self.world.remove_entity(target.id)
            
            # Invia messaggio
            if self.world and self.world.io:
                self.world.io.mostra_messaggio(f"Hai raccolto: {target.name}")
    
    def _handle_use_interaction(self, initiator, target):
        """
        Gestisce un'interazione di utilizzo
        
        Args:
            initiator: Entità che inizia l'interazione
            target: Entità obiettivo dell'interazione
        """
        # Verifica se il target ha un metodo use
        if hasattr(target, "use"):
            target.use(initiator)
    
    def _handle_environment_interaction(self, initiator, target):
        """
        Gestisce un'interazione con l'ambiente
        
        Args:
            initiator: Entità che inizia l'interazione
            target: Oggetto dell'ambiente
        """
        # Verifica se il target ha un metodo interagisci
        if hasattr(target, "interagisci"):
            target.interagisci(initiator)
    
    def _handle_generic_interaction(self, initiator, target):
        """
        Gestisce un'interazione generica
        
        Args:
            initiator: Entità che inizia l'interazione
            target: Entità obiettivo dell'interazione
        """
        # Invia un messaggio generico
        if self.world and self.world.io:
            self.world.io.mostra_messaggio(f"{initiator.name} interagisce con {target.name}") 