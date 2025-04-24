import logging
from ..system import System

logger = logging.getLogger(__name__)

class MovementSystem(System):
    """
    Sistema responsabile per il movimento delle entità nel mondo di gioco.
    Gestisce le collisioni con la mappa e altre entità.
    """
    
    def __init__(self, priority=10):
        """
        Inizializza il sistema di movimento
        
        Args:
            priority (int): Priorità del sistema (valore più alto = aggiornato prima)
        """
        super().__init__(priority)
        self.required_components = ["position", "physics"]
        
    def should_process_entity(self, entity):
        """
        Determina se un'entità dovrebbe essere processata da questo sistema
        
        Args:
            entity: Entità da valutare
            
        Returns:
            bool: True se l'entità ha i componenti richiesti, False altrimenti
        """
        return (entity.is_active() and 
                entity.has_component("position") and 
                entity.has_component("physics"))
    
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
        # Ottieni tutte le entità registrate
        entities = self.get_entities()
        
        # Processa gli eventi di movimento
        move_events = [e for e in events if e.get("type") == "move"]
        
        for event in move_events:
            entity_id = event.get("entity_id")
            dx = event.get("dx", 0)
            dy = event.get("dy", 0)
            
            # Trova l'entità
            entity = self.world.get_entity(entity_id)
            if not entity:
                continue
                
            # Esegui il movimento
            self._move_entity(entity, dx, dy)
            
        # Aggiorna anche le entità che hanno velocità intrinseca
        for entity in entities:
            if not entity.has_component("physics"):
                continue
                
            physics = entity.get_component("physics")
            if not physics or not hasattr(physics, "velocity"):
                continue
                
            # Se l'entità ha una velocità, applicala
            vx = getattr(physics, "velocity_x", 0)
            vy = getattr(physics, "velocity_y", 0)
            
            if vx != 0 or vy != 0:
                # Scala la velocità per il delta time
                dx = vx * delta_time
                dy = vy * delta_time
                
                # Esegui il movimento
                self._move_entity(entity, dx, dy)
                
    def process_entity(self, entity, dt: float) -> None:
        """
        Elabora una singola entità
        
        Args:
            entity: L'entità da elaborare
            dt: Delta time (tempo trascorso dall'ultimo aggiornamento)
        """
        if not entity.has_component("physics"):
            return
            
        physics = entity.get_component("physics")
        if not physics or not hasattr(physics, "velocity_x") or not hasattr(physics, "velocity_y"):
            return
            
        # Se l'entità ha una velocità, applicala
        vx = physics.velocity_x
        vy = physics.velocity_y
        
        if vx != 0 or vy != 0:
            # Scala la velocità per il delta time
            dx = vx * dt
            dy = vy * dt
            
            # Esegui il movimento
            self._move_entity(entity, dx, dy)
    
    def _move_entity(self, entity, dx, dy):
        """
        Muove un'entità nel mondo di gioco
        
        Args:
            entity: Entità da muovere
            dx (float): Spostamento sull'asse X
            dy (float): Spostamento sull'asse Y
            
        Returns:
            bool: True se il movimento è stato completato, False se c'è stata una collisione
        """
        if not entity.has_component("position") or not entity.has_component("physics"):
            return False
            
        position = entity.get_component("position")
        physics = entity.get_component("physics")
        
        # Verifica se l'entità può muoversi
        if not getattr(physics, "movable", True):
            return False
            
        # Posizione attuale
        old_x, old_y = position.x, position.y
        map_name = position.map_name
        
        # Nuova posizione
        new_x, new_y = old_x + dx, old_y + dy
        
        # Verifica se c'è una collisione
        if self._check_collision(entity, new_x, new_y, map_name):
            return False
            
        # Aggiorna la posizione
        position.x, position.y = new_x, new_y
        
        # Notifica il sistema di eventi del movimento
        self.world.add_event({
            "type": "entity_moved",
            "entity_id": entity.id,
            "old_position": (old_x, old_y),
            "new_position": (new_x, new_y),
            "map_name": map_name
        })
        
        return True
    
    def _check_collision(self, entity, x, y, map_name):
        """
        Verifica se c'è una collisione alle coordinate specificate
        
        Args:
            entity: Entità da verificare
            x (float): Coordinata X
            y (float): Coordinata Y
            map_name (str): Nome della mappa
            
        Returns:
            bool: True se c'è una collisione, False altrimenti
        """
        # Per ora, implementazione di base
        # Verifica collisione con la mappa
        if self.world and self.world.gestore_mappe:
            mappa = self.world.gestore_mappe.ottieni_mappa(map_name)
            if mappa and hasattr(mappa, "è_occupata"):
                return mappa.è_occupata(int(x), int(y))
                
        # Se non abbiamo un gestore mappe, non ci sono collisioni
        return False 