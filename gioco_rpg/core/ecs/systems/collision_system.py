import logging
from ..system import System

logger = logging.getLogger(__name__)

class CollisionSystem(System):
    """
    Sistema responsabile per il rilevamento e la risoluzione delle collisioni tra entità
    e tra entità e ambiente di gioco.
    """
    
    def __init__(self, priority=9):
        """
        Inizializza il sistema di collisione
        
        Args:
            priority (int): Priorità del sistema (valore più alto = aggiornato prima)
        """
        super().__init__(priority)
        self.required_components = ["position", "physics"]
        self.collision_grid = {}  # Struttura dati per ottimizzare il rilevamento delle collisioni
        
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
            
        # Aggiorna la griglia di collisione
        self._update_collision_grid()
        
        # Cerca collisioni tra entità
        collisions = self._detect_collisions()
        
        # Risolvi collisioni
        for entity1, entity2 in collisions:
            self._resolve_collision(entity1, entity2)
            
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
        # Aggiorna la griglia di collisione
        self._update_collision_grid()
        
        # Cerca collisioni tra entità
        collisions = self._detect_collisions()
        
        # Risolvi collisioni
        for entity1, entity2 in collisions:
            self._resolve_collision(entity1, entity2)
            
        # Processa eventi di collisione
        collision_events = [e for e in events if e.get("type") == "check_collision"]
        
        for event in collision_events:
            entity_id = event.get("entity_id")
            x = event.get("x", 0)
            y = event.get("y", 0)
            map_name = event.get("map_name", "")
            
            # Trova l'entità
            entity = self.world.get_entity(entity_id)
            if not entity:
                continue
                
            # Controlla se c'è una collisione e invia un evento di risposta
            collision = self._check_collision_at(entity, x, y, map_name)
            
            self.world.add_event({
                "type": "collision_result",
                "entity_id": entity_id,
                "collision": collision,
                "x": x,
                "y": y,
                "map_name": map_name
            })
    
    def process_entity(self, entity, dt: float) -> None:
        """
        Elabora una singola entità
        
        Args:
            entity: L'entità da elaborare
            dt: Delta time (tempo trascorso dall'ultimo aggiornamento)
        """
        # In questa implementazione base, le collisioni vengono gestite a livello globale
        # tramite la griglia di collisione, quindi non c'è molto da fare per entità singole
        # ma potremmo implementare controlli specifici per entità
        pass
        
    def _update_collision_grid(self):
        """
        Aggiorna la griglia di collisione con le posizioni attuali delle entità
        """
        # Reimpostazione della griglia
        self.collision_grid = {}
        
        # Ottieni tutte le entità registrate
        entities = self.get_entities()
        
        # Aggiungi le entità alla griglia
        for entity in entities:
            if not entity.has_component("position") or not entity.has_component("physics"):
                continue
                
            position = entity.get_component("position")
            physics = entity.get_component("physics")
            
            # Salta le entità non solide
            if not getattr(physics, "solid", True):
                continue
                
            # Posizione attuale
            x, y = position.x, position.y
            map_name = position.map_name
            
            # Chiave della cella nella griglia
            cell_key = (int(x), int(y), map_name)
            
            # Aggiungi l'entità alla cella
            if cell_key not in self.collision_grid:
                self.collision_grid[cell_key] = []
                
            self.collision_grid[cell_key].append(entity)
    
    def _detect_collisions(self):
        """
        Rileva le collisioni tra entità
        
        Returns:
            list: Lista di coppie di entità in collisione
        """
        collisions = []
        
        # Cerca collisioni in ogni cella della griglia
        for cell_key, entities in self.collision_grid.items():
            # Se c'è più di un'entità nella stessa cella, c'è una collisione
            if len(entities) > 1:
                for i in range(len(entities)):
                    for j in range(i + 1, len(entities)):
                        collisions.append((entities[i], entities[j]))
        
        return collisions
    
    def _resolve_collision(self, entity1, entity2):
        """
        Risolve una collisione tra due entità
        
        Args:
            entity1: Prima entità coinvolta nella collisione
            entity2: Seconda entità coinvolta nella collisione
        """
        # Ottieni i componenti necessari
        position1 = entity1.get_component("position")
        position2 = entity2.get_component("position")
        physics1 = entity1.get_component("physics")
        physics2 = entity2.get_component("physics")
        
        # Notifica il sistema di eventi della collisione
        self.world.add_event({
            "type": "entity_collision",
            "entity1_id": entity1.id,
            "entity2_id": entity2.id,
            "position1": (position1.x, position1.y),
            "position2": (position2.x, position2.y),
            "map_name": position1.map_name
        })
        
        # Implementazione di base della risoluzione delle collisioni
        # In una versione più avanzata, si potrebbero implementare
        # algoritmi di risposta alle collisioni più sofisticati
        
        # Se una delle entità è statica, l'altra deve spostarsi
        if not getattr(physics1, "movable", True):
            # entity1 è statica, entity2 deve spostarsi
            self._push_away(entity2, entity1)
        elif not getattr(physics2, "movable", True):
            # entity2 è statica, entity1 deve spostarsi
            self._push_away(entity1, entity2)
        else:
            # Entrambe le entità possono muoversi
            # Si muovono entrambe in direzioni opposte
            self._push_away(entity1, entity2, 0.5)
            self._push_away(entity2, entity1, 0.5)
    
    def _push_away(self, entity_to_move, entity_static, factor=1.0):
        """
        Sposta un'entità lontano da un'altra
        
        Args:
            entity_to_move: Entità da spostare
            entity_static: Entità statica
            factor (float): Fattore di spostamento
        """
        # Ottieni i componenti necessari
        position_move = entity_to_move.get_component("position")
        position_static = entity_static.get_component("position")
        
        # Calcola la direzione di allontanamento
        dx = position_move.x - position_static.x
        dy = position_move.y - position_static.y
        
        # Normalizza il vettore direzione
        length = (dx * dx + dy * dy) ** 0.5
        if length == 0:
            # Se le entità sono esattamente sovrapposte, scegli una direzione casuale
            dx, dy = 1, 0
        else:
            dx /= length
            dy /= length
        
        # Sposta l'entità
        position_move.x += dx * factor
        position_move.y += dy * factor
    
    def _check_collision_at(self, entity, x, y, map_name):
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
        # Chiave della cella nella griglia
        cell_key = (int(x), int(y), map_name)
        
        # Verifica collisione con la mappa
        if self.world and self.world.gestore_mappe:
            mappa = self.world.gestore_mappe.ottieni_mappa(map_name)
            if mappa and hasattr(mappa, "è_occupata") and mappa.è_occupata(int(x), int(y)):
                return True
        
        # Verifica collisione con altre entità
        if cell_key in self.collision_grid:
            entities_in_cell = self.collision_grid[cell_key]
            for other_entity in entities_in_cell:
                if other_entity.id != entity.id:  # Escludi l'entità stessa
                    return True
        
        return False 