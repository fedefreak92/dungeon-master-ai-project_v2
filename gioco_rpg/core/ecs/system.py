from typing import Dict, Set, List, Any, Optional, Callable
from abc import ABC, abstractmethod

class System(ABC):
    """
    Classe base astratta per i sistemi nel framework ECS.
    I sistemi sono responsabili dell'elaborazione delle entità che possiedono
    componenti specifici o soddisfano determinati criteri.
    """

    def __init__(self, priority: int = 0):
        """
        Inizializza un nuovo sistema
        
        Args:
            priority: Priorità del sistema (valore più alto => aggiornamento anticipato)
        """
        self.priority = priority
        self.entities: Set[str] = set()  # Set di ID entità registrate con questo sistema
        self.world = None  # Riferimento al mondo (impostato quando il sistema viene aggiunto al mondo)
        self.active = True  # Indica se il sistema è attivo
        self.required_components: List[str] = []  # Componenti richiesti per le entità gestite dal sistema
        
    def is_interested_in(self, entity: Any) -> bool:
        """
        Determina se il sistema è interessato a gestire un'entità
        
        Args:
            entity: L'entità da valutare
            
        Returns:
            bool: True se l'entità dovrebbe essere gestita da questo sistema
        """
        # Per impostazione predefinita, un sistema è interessato a un'entità se
        # l'entità ha tutti i componenti richiesti dal sistema
        if not entity.is_active():
            return False
            
        if not self.required_components:
            return True
            
        return entity.has_components(self.required_components)
        
    def register_entity(self, entity_id: str) -> None:
        """
        Registra un'entità con questo sistema
        
        Args:
            entity_id: ID dell'entità da registrare
        """
        self.entities.add(entity_id)
        
    def unregister_entity(self, entity_id: str) -> None:
        """
        Rimuove la registrazione di un'entità da questo sistema
        
        Args:
            entity_id: ID dell'entità da rimuovere
        """
        if entity_id in self.entities:
            self.entities.remove(entity_id)
            
    def process_entity(self, entity: Any, dt: float) -> None:
        """
        Elabora una singola entità
        
        Args:
            entity: L'entità da elaborare
            dt: Delta time (tempo trascorso dall'ultimo aggiornamento)
        """
        # I sistemi concreti devono implementare questa logica
        pass
            
    @abstractmethod
    def update(self, dt: float) -> None:
        """
        Aggiorna il sistema, elaborando tutte le entità registrate
        
        Args:
            dt: Delta time (tempo trascorso dall'ultimo aggiornamento)
        """
        if not self.active or not self.world:
            return
            
        # Implementazione predefinita: elabora ogni entità registrata
        for entity_id in list(self.entities):
            entity = self.world.get_entity(entity_id)
            if entity and entity.is_active():
                try:
                    self.process_entity(entity, dt)
                except Exception as e:
                    print(f"Errore nell'elaborazione dell'entità {entity_id} nel sistema {self.__class__.__name__}: {e}")
                    
    def activate(self) -> None:
        """Attiva il sistema"""
        self.active = True
        
    def deactivate(self) -> None:
        """Disattiva il sistema"""
        self.active = False
        
    def is_active(self) -> bool:
        """
        Verifica se il sistema è attivo
        
        Returns:
            bool: True se il sistema è attivo, False altrimenti
        """
        return self.active
        
    def set_world(self, world) -> None:
        """
        Imposta il riferimento al mondo
        
        Args:
            world: Il mondo a cui appartiene questo sistema
        """
        self.world = world
        
    def get_entities(self) -> List[Any]:
        """
        Ottiene tutte le entità registrate con questo sistema
        
        Returns:
            List[Any]: Lista di entità
        """
        if not self.world:
            return []
            
        return [self.world.get_entity(entity_id) for entity_id in self.entities 
                if self.world.get_entity(entity_id) is not None]


class MovementSystem(System):
    """Sistema responsabile del movimento delle entità"""
    
    def __init__(self):
        """Inizializza il sistema di movimento"""
        super().__init__(10)  # Eseguito con alta priorità
        
    def should_process_entity(self, entity):
        """
        Determina se un'entità dovrebbe essere processata dal sistema di movimento
        
        Args:
            entity: Entità da valutare
            
        Returns:
            bool: True se l'entità ha i componenti position e physics, False altrimenti
        """
        return entity.is_active() and entity.has_components("position", "physics") and entity.get_component("physics").movable
        
    def process_entity(self, entity: Any, dt: float) -> None:
        """
        Elabora una singola entità
        
        Args:
            entity: L'entità da elaborare
            dt: Delta time (tempo trascorso dall'ultimo aggiornamento)
        """
        position = entity.get_component("position")
        physics = entity.get_component("physics")
        
        if physics.velocity_x != 0 or physics.velocity_y != 0:
            # Calcola lo spostamento
            dx = physics.velocity_x * dt
            dy = physics.velocity_y * dt
            
            # Aggiorna la posizione
            position.x += dx
            position.y += dy
            
            # Aggiorna la direzione dell'entità (utile per animazioni)
            if abs(physics.velocity_x) > abs(physics.velocity_y):
                # Movimento prevalentemente orizzontale
                if physics.velocity_x > 0:
                    self._set_entity_direction(entity, "east")
                else:
                    self._set_entity_direction(entity, "west")
            else:
                # Movimento prevalentemente verticale
                if physics.velocity_y > 0:
                    self._set_entity_direction(entity, "south")
                else:
                    self._set_entity_direction(entity, "north")
                        
    def _set_entity_direction(self, entity, direction):
        """
        Imposta la direzione di un'entità
        
        Args:
            entity: Entità da aggiornare
            direction (str): Direzione ("north", "south", "east", "west")
        """
        # Verifica se l'entità ha un componente renderable
        if entity.has_component("renderable"):
            renderable = entity.get_component("renderable")
            
            # Imposta il flip orizzontale in base alla direzione
            if direction == "east":
                renderable.flip_x = False
            elif direction == "west":
                renderable.flip_x = True


class RenderSystem(System):
    """Sistema responsabile del rendering delle entità"""
    
    def __init__(self, renderer):
        """
        Inizializza il sistema di rendering
        
        Args:
            renderer: Oggetto che si occupa del rendering effettivo
        """
        super().__init__(1)  # Priorità bassa, eseguito dopo altri sistemi
        self.renderer = renderer
        self.camera_entity = None
        self.render_queue = {}  # layer -> lista di entità
        self.animation_time = 0
        self.particle_time = 0
        
    def should_process_entity(self, entity):
        """
        Determina se un'entità dovrebbe essere processata dal sistema di rendering
        
        Args:
            entity: Entità da valutare
            
        Returns:
            bool: True se l'entità ha il componente renderable, False altrimenti
        """
        return entity.is_active() and entity.has_component("renderable")
        
    def process_entity(self, entity: Any, dt: float) -> None:
        """
        Elabora una singola entità
        
        Args:
            entity: L'entità da elaborare
            dt: Delta time (tempo trascorso dall'ultimo aggiornamento)
        """
        renderable = entity.get_component("renderable")
        
        # Salta entità non visibili
        if not renderable.visible:
            return
            
        # Ottieni la posizione dell'entità (se presente)
        position = entity.get_component("position") if entity.has_component("position") else None
        
        # Prepara i dati per il rendering
        render_data = {
            "id": entity.id,
            "sprite": renderable.sprite,
            "x": position.x if position else 0,
            "y": position.y if position else 0,
            "z": position.z if position else 0,
            "layer": renderable.layer,
            "scale": renderable.scale,
            "rotation": renderable.rotation,
            "flip_x": renderable.flip_x,
            "flip_y": renderable.flip_y,
            "tint": renderable.tint,
            "alpha": renderable.alpha,
            "tags": entity.tags
        }
        
        # Gestione delle animazioni se presente il componente
        if entity.has_component("animation"):
            animation = entity.get_component("animation")
            if animation.playing and animation.current_animation:
                # Aggiorna il frame dell'animazione
                self._update_animation(animation, dt)
                
                # Se l'animazione è in corso, usa il frame corrente come sprite
                if animation.current_animation in animation.animations:
                    current_anim = animation.animations[animation.current_animation]
                    if "frames" in current_anim and current_anim["frames"]:
                        # Usa il frame corrente per aggiornare lo sprite
                        frame_index = min(animation.current_frame, len(current_anim["frames"]) - 1)
                        render_data["sprite"] = current_anim["frames"][frame_index]
        
        # Aggiungi alla coda di rendering nel layer appropriato
        if renderable.layer not in self.render_queue:
            self.render_queue[renderable.layer] = []
            
        self.render_queue[renderable.layer].append(render_data)
            
    def update(self, dt: float) -> None:
        """
        Aggiorna il sistema, elaborando tutte le entità registrate e eseguendo il rendering
        
        Args:
            dt: Delta time (tempo trascorso dall'ultimo aggiornamento)
        """
        if not self.active or not self.world:
            return
            
        # Aggiorna il tempo per le animazioni e particelle
        self.animation_time += dt
        self.particle_time += dt
            
        # Pulisci la coda di rendering
        self.render_queue = {}
        
        # Elabora le entità per preparare i dati di rendering
        for entity_id in list(self.entities):
            entity = self.world.get_entity(entity_id)
            if entity:
                if self.should_process_entity(entity):
                    try:
                        self.process_entity(entity, dt)
                    except Exception as e:
                        print(f"Errore nel sistema di rendering per l'entità {entity_id}: {e}")
                        
                # Gestisci sistemi di particelle indipendentemente dal rendering
                if entity.has_component("particle"):
                    try:
                        self._update_particles(entity, dt)
                    except Exception as e:
                        print(f"Errore nel sistema di particelle per l'entità {entity_id}: {e}")
        
        # Aggiorna la camera se esiste
        self._update_camera(dt)
        
        # Esegui il rendering effettivo
        self._render_entities()
        
    def _update_animation(self, animation_component, dt):
        """
        Aggiorna lo stato di un componente animazione
        
        Args:
            animation_component: Componente animazione da aggiornare
            dt: Delta time
        """
        if not animation_component.playing or not animation_component.current_animation:
            return
            
        # Ottieni i dati dell'animazione corrente
        current_anim = animation_component.animations.get(animation_component.current_animation)
        if not current_anim:
            return
            
        # Aggiorna il tempo del frame
        animation_component.frame_time += dt * animation_component.speed
        
        # Verifica se è necessario passare al frame successivo
        frame_duration = current_anim.get("frame_duration", 0.1)
        while animation_component.frame_time >= frame_duration:
            animation_component.frame_time -= frame_duration
            animation_component.current_frame += 1
            
            # Gestione della fine dell'animazione
            frames = current_anim.get("frames", [])
            if not frames:
                animation_component.playing = False
                animation_component.finished = True
                break
                
            if animation_component.current_frame >= len(frames):
                # Se è impostato il loop, riavvia l'animazione
                if animation_component.loop:
                    animation_component.current_frame = 0
                else:
                    # Altrimenti ferma l'animazione all'ultimo frame
                    animation_component.current_frame = len(frames) - 1
                    animation_component.playing = False
                    animation_component.finished = True
                    break
    
    def _update_particles(self, entity, dt):
        """
        Aggiorna il sistema di particelle di un'entità
        
        Args:
            entity: Entità con componente particellare
            dt: Delta time
        """
        particle = entity.get_component("particle")
        if not particle.active:
            return
            
        # Posizione per emettere particelle
        position = None
        if entity.has_component("position"):
            position = entity.get_component("position")
        
        # Aggiorna le particelle esistenti
        i = 0
        while i < len(particle.particles):
            p = particle.particles[i]
            p["life"] -= dt
            
            if p["life"] <= 0:
                # Rimuovi particelle morte
                particle.particles.pop(i)
            else:
                # Aggiorna posizione in base a velocità e accelerazione
                p["x"] += p["vx"] * dt
                p["y"] += p["vy"] * dt
                p["vx"] += particle.acceleration["x"] * dt
                p["vy"] += particle.acceleration["y"] * dt
                p["alpha"] = min(1.0, p["life"] / particle.lifetime)  # Svanisci verso la fine
                i += 1
        
        # Genera nuove particelle se necessario
        if position and particle.active:
            spawn_count = int(particle.spawn_rate * dt)
            for _ in range(spawn_count):
                if len(particle.particles) < particle.max_particles:
                    # Velocità casuale entro i limiti
                    vx = (particle.velocity["max_x"] - particle.velocity["min_x"]) * (0.5 - self._random()) + particle.velocity["min_x"]
                    vy = (particle.velocity["max_y"] - particle.velocity["min_y"]) * (0.5 - self._random()) + particle.velocity["min_y"]
                    
                    # Crea una nuova particella
                    new_particle = {
                        "x": position.x,
                        "y": position.y,
                        "vx": vx,
                        "vy": vy,
                        "size": particle.size * (0.8 + 0.4 * self._random()),
                        "life": particle.lifetime * (0.8 + 0.4 * self._random()),
                        "color": particle.color,
                        "alpha": 1.0
                    }
                    
                    particle.particles.append(new_particle)
                    
        # Aggiungi le particelle alla coda di rendering
        for p in particle.particles:
            render_data = {
                "id": f"{entity.id}_particle_{id(p)}",
                "sprite": "particle",  # Sprite dedicato o generato
                "x": p["x"],
                "y": p["y"],
                "z": 0.5,  # Sopra la maggior parte degli elementi
                "layer": 15,  # Layer alto per le particelle
                "scale": p["size"],
                "rotation": 0,
                "tint": p["color"],
                "alpha": p["alpha"],
                "is_particle": True
            }
            
            # Aggiungi alla coda di rendering
            if 15 not in self.render_queue:
                self.render_queue[15] = []
                
            self.render_queue[15].append(render_data)
    
    def _update_camera(self, dt):
        """
        Aggiorna la posizione della camera
        
        Args:
            dt: Delta time
        """
        if not self.camera_entity:
            # Cerca un'entità con componente camera
            for entity_id in self.entities:
                entity = self.world.get_entity(entity_id)
                if entity and entity.has_component("camera"):
                    self.camera_entity = entity
                    break
        
        if not self.camera_entity:
            return
            
        camera = self.camera_entity.get_component("camera")
        
        # Se abbiamo un target, segui quella entità
        if camera.target_id:
            target_entity = self.world.get_entity(camera.target_id)
            if target_entity and target_entity.has_component("position"):
                target_pos = target_entity.get_component("position")
                camera.target_x = target_pos.x + camera.offset_x
                camera.target_y = target_pos.y + camera.offset_y
                
                # Applica smoothing
                if camera.smoothing > 0:
                    camera.position_x += (camera.target_x - camera.position_x) * camera.smoothing * dt * 10
                    camera.position_y += (camera.target_y - camera.position_y) * camera.smoothing * dt * 10
                else:
                    camera.position_x = camera.target_x
                    camera.position_y = camera.target_y
                    
                # Limiti della camera
                if camera.bounds:
                    half_width = (camera.viewport_width / 2) / camera.zoom
                    half_height = (camera.viewport_height / 2) / camera.zoom
                    
                    # Limita la camera all'interno dei bounds
                    camera.position_x = max(camera.bounds["x"] + half_width, 
                                         min(camera.bounds["x"] + camera.bounds["width"] - half_width, 
                                             camera.position_x))
                    camera.position_y = max(camera.bounds["y"] + half_height, 
                                         min(camera.bounds["y"] + camera.bounds["height"] - half_height, 
                                             camera.position_y))
    
    def _render_entities(self):
        """Esegue il rendering effettivo delle entità nella coda"""
        if not self.renderer:
            return
            
        # Imposta la camera
        camera_data = None
        if self.camera_entity and self.camera_entity.has_component("camera"):
            camera = self.camera_entity.get_component("camera")
            camera_data = {
                "x": camera.position_x,
                "y": camera.position_y,
                "zoom": camera.zoom,
                "viewport_width": camera.viewport_width,
                "viewport_height": camera.viewport_height
            }
            
        # Applica la trasformazione della camera
        self.renderer.set_camera(camera_data)
        
        # Pulisci lo schermo
        self.renderer.clear_screen()
        
        # Ottieni i layer in ordine crescente (dal più basso al più alto)
        sorted_layers = sorted(self.render_queue.keys())
        
        # Rendering per ogni layer
        for layer in sorted_layers:
            for render_data in self.render_queue[layer]:
                self.renderer.draw_entity(render_data)
                
        # Completa il rendering
        self.renderer.present()
    
    def _random(self):
        """Restituisce un numero casuale tra 0 e 1"""
        import random
        return random.random()

    def set_renderer(self, renderer):
        """
        Imposta il renderer da utilizzare
        
        Args:
            renderer: Oggetto renderer
        """
        self.renderer = renderer


class CollisionSystem(System):
    """Sistema responsabile della rilevazione e gestione delle collisioni"""
    
    def __init__(self):
        """Inizializza il sistema di collisione"""
        super().__init__(20)  # Eseguito con priorità medio-alta
        self.collision_handlers = {}  # Gestori di collisione per diversi tipi di entità
        
    def should_process_entity(self, entity):
        """
        Determina se un'entità dovrebbe essere processata dal sistema di collisione
        
        Args:
            entity: Entità da valutare
            
        Returns:
            bool: True se l'entità ha i componenti position e physics con solid=True, False altrimenti
        """
        return (entity.is_active() and 
                entity.has_components("position", "physics") and 
                entity.get_component("physics").solid)
        
    def process_entity(self, entity: Any, dt: float) -> None:
        """
        Elabora una singola entità
        
        Args:
            entity: L'entità da elaborare
            dt: Delta time (tempo trascorso dall'ultimo aggiornamento)
        """
        position = entity.get_component("position")
        physics = entity.get_component("physics")
        
        # Verifica la collisione con altre entità
        for other_entity in self.get_entities():
            if other_entity == entity:
                continue
                
            other_pos = other_entity.get_component("position")
            other_phys = other_entity.get_component("physics")
            
            # Verifica se le entità sono nella stessa mappa
            if position.map_name != other_pos.map_name:
                continue
                
            # Calcola hitbox effettive
            hitbox1 = self._get_effective_hitbox(entity)
            hitbox2 = self._get_effective_hitbox(other_entity)
            
            # Verifica la collisione tra le hitbox
            if self._check_collision(position, hitbox1, other_pos, hitbox2):
                # Gestisci la collisione
                self._handle_collision(entity, other_entity)
                    
    def _get_effective_hitbox(self, entity):
        """
        Calcola l'hitbox effettiva di un'entità
        
        Args:
            entity: Entità di cui calcolare l'hitbox
            
        Returns:
            dict: Hitbox effettiva
        """
        physics = entity.get_component("physics")
        return physics.hitbox
        
    def _check_collision(self, pos1, hitbox1, pos2, hitbox2):
        """
        Verifica se due entità collidono
        
        Args:
            pos1: Componente position della prima entità
            hitbox1: Hitbox della prima entità
            pos2: Componente position della seconda entità
            hitbox2: Hitbox della seconda entità
            
        Returns:
            bool: True se le entità collidono, False altrimenti
        """
        # Calcola le coordinate dei bordi dei rettangoli di collisione
        left1 = pos1.x + hitbox1.get("offset_x", 0)
        top1 = pos1.y + hitbox1.get("offset_y", 0)
        right1 = left1 + hitbox1.get("width", 1)
        bottom1 = top1 + hitbox1.get("height", 1)
        
        left2 = pos2.x + hitbox2.get("offset_x", 0)
        top2 = pos2.y + hitbox2.get("offset_y", 0)
        right2 = left2 + hitbox2.get("width", 1)
        bottom2 = top2 + hitbox2.get("height", 1)
        
        # Verifica se i rettangoli si sovrappongono
        return not (right1 <= left2 or left1 >= right2 or bottom1 <= top2 or top1 >= bottom2)
        
    def _handle_collision(self, entity1, entity2):
        """
        Gestisce la collisione tra due entità
        
        Args:
            entity1: Prima entità coinvolta nella collisione
            entity2: Seconda entità coinvolta nella collisione
        """
        # Determina i tipi delle entità
        type1 = self._get_entity_type(entity1)
        type2 = self._get_entity_type(entity2)
        
        # Cerca un gestore di collisione specifico
        handler_key = (type1, type2)
        if handler_key in self.collision_handlers:
            self.collision_handlers[handler_key](entity1, entity2)
        elif (type2, type1) in self.collision_handlers:
            self.collision_handlers[(type2, type1)](entity2, entity1)
        else:
            # Gestione di default: respingi le entità mobili
            self._default_collision_handler(entity1, entity2)
            
    def _get_entity_type(self, entity):
        """
        Determina il tipo di un'entità
        
        Args:
            entity: Entità di cui determinare il tipo
            
        Returns:
            str: Tipo dell'entità
        """
        # Usa il primo tag dell'entità come tipo, o "generic" se non ha tag
        return next(iter(entity.tags), "generic")
        
    def _default_collision_handler(self, entity1, entity2):
        """
        Gestore di collisione predefinito
        
        Args:
            entity1: Prima entità coinvolta nella collisione
            entity2: Seconda entità coinvolta nella collisione
        """
        # Verifica quali entità possono essere spostate
        phys1 = entity1.get_component("physics")
        phys2 = entity2.get_component("physics")
        
        if phys1.movable and not phys2.movable:
            # Solo entity1 può essere spostata
            self._push_back_entity(entity1)
        elif phys2.movable and not phys1.movable:
            # Solo entity2 può essere spostata
            self._push_back_entity(entity2)
        elif phys1.movable and phys2.movable:
            # Entrambe le entità possono essere spostate
            self._push_back_entity(entity1, 0.5)
            self._push_back_entity(entity2, 0.5)
            
    def _push_back_entity(self, entity, factor=1.0):
        """
        Respinge un'entità indietro in base alla sua velocità
        
        Args:
            entity: Entità da respingere
            factor (float): Fattore di respinta (1.0 = completa)
        """
        position = entity.get_component("position")
        physics = entity.get_component("physics")
        
        # Calcola lo spostamento inverso
        dx = -physics.velocity_x * factor
        dy = -physics.velocity_y * factor
        
        # Applica lo spostamento
        position.x += dx
        position.y += dy
        
        # Annulla la velocità
        physics.velocity_x = 0
        physics.velocity_y = 0
        
    def register_collision_handler(self, type1, type2, handler):
        """
        Registra un gestore di collisione per due tipi di entità
        
        Args:
            type1 (str): Tipo della prima entità
            type2 (str): Tipo della seconda entità
            handler (callable): Funzione che gestisce la collisione
        """
        self.collision_handlers[(type1, type2)] = handler


class InteractionSystem(System):
    """Sistema responsabile della gestione delle interazioni tra entità"""
    
    def __init__(self):
        """Inizializza il sistema di interazione"""
        super().__init__(30)  # Eseguito con priorità media
        self.player_entity = None  # Riferimento all'entità del giocatore
        
    def should_process_entity(self, entity):
        """
        Determina se un'entità dovrebbe essere processata dal sistema di interazione
        
        Args:
            entity: Entità da valutare
            
        Returns:
            bool: True se l'entità ha i componenti position e interactable, False altrimenti
        """
        return (entity.is_active() and 
                entity.has_components("position", "interactable") and 
                entity.get_component("interactable").interaction_enabled)
        
    def set_player_entity(self, player_entity):
        """
        Imposta l'entità del giocatore
        
        Args:
            player_entity: Entità del giocatore
        """
        self.player_entity = player_entity
        
    def process_entity(self, entity: Any, dt: float) -> None:
        """
        Elabora una singola entità
        
        Args:
            entity: L'entità da elaborare
            dt: Delta time (tempo trascorso dall'ultimo aggiornamento)
        """
        if not self.active or not self.player_entity:
            return
            
        # Ottieni la posizione del giocatore
        player_pos = self.player_entity.get_component("position")
        if not player_pos:
            return
            
        # Processa gli eventi di interazione
        interact_event = None
        if events:
            for event in events:
                if event.get("type") == "interaction":
                    interact_event = event
                    break
                    
        # Trova le entità interattive nelle vicinanze
        nearby_interactables = []
        for other_entity in self.get_entities():
            if other_entity == self.player_entity:
                continue
                
            pos = other_entity.get_component("position")
            interactable = other_entity.get_component("interactable")
            
            # Verifica se l'entità è nella stessa mappa
            if pos.map_name != player_pos.map_name:
                continue
                
            # Calcola la distanza
            distance = ((pos.x - player_pos.x) ** 2 + (pos.y - player_pos.y) ** 2) ** 0.5
            
            # Verifica se l'entità è abbastanza vicina
            if distance <= interactable.interaction_radius:
                nearby_interactables.append({
                    "entity": other_entity,
                    "distance": distance
                })
                
        # Ordina le entità interattive per distanza
        nearby_interactables.sort(key=lambda e: e["distance"])
        
        # Se c'è un evento di interazione, interagisci con l'entità più vicina
        if interact_event and nearby_interactables:
            target_entity = nearby_interactables[0]["entity"]
            self._handle_interaction(self.player_entity, target_entity, interact_event)
            
    def _handle_interaction(self, player_entity, target_entity, event):
        """
        Gestisce l'interazione tra due entità
        
        Args:
            player_entity: Entità del giocatore
            target_entity: Entità con cui interagire
            event: Evento di interazione
        """
        interactable = target_entity.get_component("interactable")
        
        # Gestisci l'interazione in base al tipo
        interaction_type = interactable.interaction_type
        if interaction_type == "dialog":
            self._handle_dialog_interaction(player_entity, target_entity, event)
        elif interaction_type == "pickup":
            self._handle_pickup_interaction(player_entity, target_entity, event)
        elif interaction_type == "use":
            self._handle_use_interaction(player_entity, target_entity, event)
        elif interaction_type == "door":
            self._handle_door_interaction(player_entity, target_entity, event)
        elif interaction_type == "container":
            self._handle_container_interaction(player_entity, target_entity, event)
            
    def _handle_dialog_interaction(self, player_entity, target_entity, event):
        """
        Gestisce l'interazione di dialogo
        
        Args:
            player_entity: Entità del giocatore
            target_entity: Entità con cui interagire
            event: Evento di interazione
        """
        interactable = target_entity.get_component("interactable")
        
        # Ottieni i dati di dialogo
        dialog_data = interactable.interaction_data.get("dialog", {})
        
        # Crea un evento di dialogo
        dialog_event = {
            "type": "dialog_start",
            "source": player_entity.id,
            "target": target_entity.id,
            "dialog_data": dialog_data
        }
        
        # Aggiungi l'evento agli eventi pendenti
        if hasattr(event, "add_pending_event"):
            event.add_pending_event(dialog_event)
            
    def _handle_pickup_interaction(self, player_entity, target_entity, event):
        """
        Gestisce l'interazione di raccolta
        
        Args:
            player_entity: Entità del giocatore
            target_entity: Entità con cui interagire
            event: Evento di interazione
        """
        # Verifica se il giocatore ha un inventario
        if not player_entity.has_component("inventory"):
            return
            
        inventory = player_entity.get_component("inventory")
        
        # Crea un item in base ai dati dell'entità
        item_data = target_entity.to_dict()
        
        # Aggiungi l'item all'inventario
        if inventory.add_item(item_data):
            # Disattiva l'entità raccolta
            target_entity.deactivate()
            
            # Crea un evento di raccolta
            pickup_event = {
                "type": "item_pickup",
                "source": player_entity.id,
                "target": target_entity.id,
                "item": item_data
            }
            
            # Aggiungi l'evento agli eventi pendenti
            if hasattr(event, "add_pending_event"):
                event.add_pending_event(pickup_event)
                
    def _handle_use_interaction(self, player_entity, target_entity, event):
        """
        Gestisce l'interazione di utilizzo
        
        Args:
            player_entity: Entità del giocatore
            target_entity: Entità con cui interagire
            event: Evento di interazione
        """
        interactable = target_entity.get_component("interactable")
        
        # Ottieni i dati di utilizzo
        use_data = interactable.interaction_data.get("use", {})
        
        # Crea un evento di utilizzo
        use_event = {
            "type": "entity_use",
            "source": player_entity.id,
            "target": target_entity.id,
            "use_data": use_data
        }
        
        # Aggiungi l'evento agli eventi pendenti
        if hasattr(event, "add_pending_event"):
            event.add_pending_event(use_event)
            
    def _handle_door_interaction(self, player_entity, target_entity, event):
        """
        Gestisce l'interazione con una porta
        
        Args:
            player_entity: Entità del giocatore
            target_entity: Entità con cui interagire
            event: Evento di interazione
        """
        interactable = target_entity.get_component("interactable")
        
        # Ottieni i dati della porta
        door_data = interactable.interaction_data.get("door", {})
        
        # Ottieni le informazioni sulla destinazione
        target_map = door_data.get("target_map")
        target_x = door_data.get("target_x")
        target_y = door_data.get("target_y")
        
        if target_map and target_x is not None and target_y is not None:
            # Aggiorna la posizione del giocatore
            player_pos = player_entity.get_component("position")
            player_pos.map_name = target_map
            player_pos.x = target_x
            player_pos.y = target_y
            
            # Crea un evento di cambio mappa
            door_event = {
                "type": "map_change",
                "source": player_entity.id,
                "target": target_entity.id,
                "previous_map": player_pos.map_name,
                "new_map": target_map,
                "position": {"x": target_x, "y": target_y}
            }
            
            # Aggiungi l'evento agli eventi pendenti
            if hasattr(event, "add_pending_event"):
                event.add_pending_event(door_event)
                
    def _handle_container_interaction(self, player_entity, target_entity, event):
        """
        Gestisce l'interazione con un contenitore
        
        Args:
            player_entity: Entità del giocatore
            target_entity: Entità con cui interagire
            event: Evento di interazione
        """
        interactable = target_entity.get_component("interactable")
        
        # Verifica se il contenitore ha un inventario
        if not target_entity.has_component("inventory"):
            return
            
        container_inventory = target_entity.get_component("inventory")
        
        # Crea un evento di apertura contenitore
        container_event = {
            "type": "container_open",
            "source": player_entity.id,
            "target": target_entity.id,
            "items": [item.to_dict() if hasattr(item, 'to_dict') else item for item in container_inventory.items]
        }
        
        # Aggiungi l'evento agli eventi pendenti
        if hasattr(event, "add_pending_event"):
            event.add_pending_event(container_event) 