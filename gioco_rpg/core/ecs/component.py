class Component:
    """
    Classe base per tutti i componenti nel sistema ECS.
    Un componente contiene solo dati, non logica.
    """
    
    def __init__(self):
        """Inizializza un nuovo componente"""
        self.entity = None  # Riferimento all'entità a cui appartiene
        
    def to_dict(self):
        """
        Converte il componente in un dizionario per la serializzazione.
        Da implementare nelle sottoclassi.
        
        Returns:
            dict: Rappresentazione del componente come dizionario
        """
        return {"type": self.__class__.__name__}
        
    @classmethod
    def from_dict(cls, data):
        """
        Crea un componente da un dizionario.
        Da implementare nelle sottoclassi.
        
        Args:
            data (dict): Dizionario con i dati del componente
            
        Returns:
            Component: Nuova istanza del componente
        """
        return cls()


class PositionComponent(Component):
    """Componente che rappresenta la posizione di un'entità nel mondo di gioco"""
    
    def __init__(self, x=0, y=0, z=0, map_name=None):
        """
        Inizializza un nuovo componente posizione
        
        Args:
            x (float): Coordinata X
            y (float): Coordinata Y
            z (float): Coordinata Z (profondità/livello)
            map_name (str): Nome della mappa in cui si trova l'entità
        """
        super().__init__()
        self.x = x
        self.y = y
        self.z = z
        self.map_name = map_name
        
    def to_dict(self):
        """
        Converte il componente in un dizionario
        
        Returns:
            dict: Rappresentazione del componente come dizionario
        """
        return {
            "type": "position",
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "map_name": self.map_name
        }
        
    @classmethod
    def from_dict(cls, data):
        """
        Crea un componente posizione da un dizionario
        
        Args:
            data (dict): Dizionario con i dati del componente
            
        Returns:
            PositionComponent: Nuova istanza del componente
        """
        return cls(
            x=data.get("x", 0),
            y=data.get("y", 0),
            z=data.get("z", 0),
            map_name=data.get("map_name")
        )


class RenderableComponent(Component):
    """Componente che rende un'entità visualizzabile"""
    
    def __init__(self, sprite=None, animation=None, layer=0, visible=True, scale=1.0):
        """
        Inizializza un nuovo componente renderable
        
        Args:
            sprite (str): Nome dello sprite da utilizzare
            animation (str): Nome dell'animazione da utilizzare
            layer (int): Livello di rendering (i livelli più alti vengono renderizzati sopra)
            visible (bool): Indica se l'entità è visibile
            scale (float): Fattore di scala
        """
        super().__init__()
        self.sprite = sprite
        self.animation = animation
        self.layer = layer
        self.visible = visible
        self.scale = scale
        self.flip_x = False
        self.flip_y = False
        self.rotation = 0.0
        self.tint = 0xFFFFFF  # Colore bianco per default
        self.alpha = 1.0      # Opacità piena per default
        
    def to_dict(self):
        """
        Converte il componente in un dizionario
        
        Returns:
            dict: Rappresentazione del componente come dizionario
        """
        return {
            "type": "renderable",
            "sprite": self.sprite,
            "animation": self.animation,
            "layer": self.layer,
            "visible": self.visible,
            "scale": self.scale,
            "flip_x": self.flip_x,
            "flip_y": self.flip_y,
            "rotation": self.rotation,
            "tint": self.tint,
            "alpha": self.alpha
        }
        
    @classmethod
    def from_dict(cls, data):
        """
        Crea un componente renderable da un dizionario
        
        Args:
            data (dict): Dizionario con i dati del componente
            
        Returns:
            RenderableComponent: Nuova istanza del componente
        """
        component = cls(
            sprite=data.get("sprite"),
            animation=data.get("animation"),
            layer=data.get("layer", 0),
            visible=data.get("visible", True),
            scale=data.get("scale", 1.0)
        )
        
        # Imposta le proprietà aggiuntive
        component.flip_x = data.get("flip_x", False)
        component.flip_y = data.get("flip_y", False)
        component.rotation = data.get("rotation", 0.0)
        component.tint = data.get("tint", 0xFFFFFF)
        component.alpha = data.get("alpha", 1.0)
        
        return component


class PhysicsComponent(Component):
    """Componente che permette ad un'entità di interagire fisicamente con il mondo"""
    
    def __init__(self, solid=True, movable=True, weight=1.0, 
                velocity_x=0.0, velocity_y=0.0, collision_mask=None):
        """
        Inizializza un nuovo componente physics
        
        Args:
            solid (bool): Indica se l'entità è solida (può collidere)
            movable (bool): Indica se l'entità può essere mossa
            weight (float): Peso dell'entità
            velocity_x (float): Velocità orizzontale
            velocity_y (float): Velocità verticale
            collision_mask (list): Tipi di entità con cui può collidere
        """
        super().__init__()
        self.solid = solid
        self.movable = movable
        self.weight = weight
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.collision_mask = collision_mask or ["solid"]
        self.hitbox = {"width": 1, "height": 1, "offset_x": 0, "offset_y": 0}
        
    def to_dict(self):
        """
        Converte il componente in un dizionario
        
        Returns:
            dict: Rappresentazione del componente come dizionario
        """
        return {
            "type": "physics",
            "solid": self.solid,
            "movable": self.movable,
            "weight": self.weight,
            "velocity_x": self.velocity_x,
            "velocity_y": self.velocity_y,
            "collision_mask": self.collision_mask,
            "hitbox": self.hitbox
        }
        
    @classmethod
    def from_dict(cls, data):
        """
        Crea un componente physics da un dizionario
        
        Args:
            data (dict): Dizionario con i dati del componente
            
        Returns:
            PhysicsComponent: Nuova istanza del componente
        """
        component = cls(
            solid=data.get("solid", True),
            movable=data.get("movable", True),
            weight=data.get("weight", 1.0),
            velocity_x=data.get("velocity_x", 0.0),
            velocity_y=data.get("velocity_y", 0.0),
            collision_mask=data.get("collision_mask")
        )
        
        # Imposta l'hitbox
        if "hitbox" in data:
            component.hitbox = data["hitbox"]
            
        return component


class InventoryComponent(Component):
    """Componente che permette ad un'entità di avere un inventario"""
    
    def __init__(self, capacity=10, items=None):
        """
        Inizializza un nuovo componente inventario
        
        Args:
            capacity (int): Capacità massima dell'inventario
            items (list): Lista iniziale di item nell'inventario
        """
        super().__init__()
        self.capacity = capacity
        self.items = items or []
        
    def to_dict(self):
        """
        Converte il componente in un dizionario
        
        Returns:
            dict: Rappresentazione del componente come dizionario
        """
        # Serializziamo solo gli ID degli item per evitare cicli
        item_ids = []
        for item in self.items:
            if hasattr(item, 'id'):
                item_ids.append(item.id)
            elif isinstance(item, dict) and 'id' in item:
                item_ids.append(item['id'])
                
        return {
            "type": "inventory",
            "capacity": self.capacity,
            "item_ids": item_ids
        }
        
    @classmethod
    def from_dict(cls, data):
        """
        Crea un componente inventario da un dizionario
        
        Args:
            data (dict): Dizionario con i dati del componente
            
        Returns:
            InventoryComponent: Nuova istanza del componente
        """
        # Nota: gli item verranno aggiunti in seguito dal manager o dal sistema
        return cls(
            capacity=data.get("capacity", 10)
        )
        
    def add_item(self, item):
        """
        Aggiunge un item all'inventario
        
        Args:
            item: Item da aggiungere
            
        Returns:
            bool: True se l'item è stato aggiunto, False altrimenti
        """
        if len(self.items) < self.capacity:
            self.items.append(item)
            return True
        return False
        
    def remove_item(self, item):
        """
        Rimuove un item dall'inventario
        
        Args:
            item: Item da rimuovere
            
        Returns:
            bool: True se l'item è stato rimosso, False altrimenti
        """
        if item in self.items:
            self.items.remove(item)
            return True
        return False
        
    def has_item(self, item_id):
        """
        Verifica se l'inventario contiene un item con l'ID specificato
        
        Args:
            item_id (str): ID dell'item da cercare
            
        Returns:
            bool: True se l'item è presente, False altrimenti
        """
        for item in self.items:
            if hasattr(item, 'id') and item.id == item_id:
                return True
            elif isinstance(item, dict) and item.get('id') == item_id:
                return True
        return False


class InteractableComponent(Component):
    """Componente che permette ad un'entità di essere interattiva"""
    
    def __init__(self, interaction_type=None, interaction_radius=1.0, 
                interaction_message=None, interaction_data=None):
        """
        Inizializza un nuovo componente interactable
        
        Args:
            interaction_type (str): Tipo di interazione (es. "dialog", "pickup", "use")
            interaction_radius (float): Raggio di interazione
            interaction_message (str): Messaggio mostrato quando l'entità è interattiva
            interaction_data (dict): Dati aggiuntivi per l'interazione
        """
        super().__init__()
        self.interaction_type = interaction_type
        self.interaction_radius = interaction_radius
        self.interaction_message = interaction_message
        self.interaction_data = interaction_data or {}
        self.interaction_enabled = True
        
    def to_dict(self):
        """
        Converte il componente in un dizionario
        
        Returns:
            dict: Rappresentazione del componente come dizionario
        """
        return {
            "type": "interactable",
            "interaction_type": self.interaction_type,
            "interaction_radius": self.interaction_radius,
            "interaction_message": self.interaction_message,
            "interaction_data": self.interaction_data,
            "interaction_enabled": self.interaction_enabled
        }
        
    @classmethod
    def from_dict(cls, data):
        """
        Crea un componente interactable da un dizionario
        
        Args:
            data (dict): Dizionario con i dati del componente
            
        Returns:
            InteractableComponent: Nuova istanza del componente
        """
        component = cls(
            interaction_type=data.get("interaction_type"),
            interaction_radius=data.get("interaction_radius", 1.0),
            interaction_message=data.get("interaction_message"),
            interaction_data=data.get("interaction_data", {})
        )
        
        component.interaction_enabled = data.get("interaction_enabled", True)
        
        return component


class ParticleComponent(Component):
    """Componente che gestisce effetti particellari per un'entità"""
    
    def __init__(self, effect_type=None, max_particles=50, lifetime=1.0, 
                 color=0xFFFFFF, size=1.0, active=False):
        """
        Inizializza un nuovo componente particellare
        
        Args:
            effect_type (str): Tipo di effetto particellare (fuoco, fumo, pioggia, ecc.)
            max_particles (int): Numero massimo di particelle
            lifetime (float): Durata di vita delle particelle in secondi
            color (int): Colore delle particelle in formato esadecimale
            size (float): Dimensione delle particelle
            active (bool): Indica se l'emettitore è attivo
        """
        super().__init__()
        self.effect_type = effect_type
        self.max_particles = max_particles
        self.lifetime = lifetime
        self.color = color
        self.size = size
        self.active = active
        self.velocity = {"min_x": -1, "max_x": 1, "min_y": -1, "max_y": 1}
        self.acceleration = {"x": 0, "y": 0}
        self.spawn_rate = 10  # particelle al secondo
        self.last_spawn_time = 0
        self.particles = []  # lista di particelle attive
        
    def to_dict(self):
        """
        Converte il componente in un dizionario
        
        Returns:
            dict: Rappresentazione del componente come dizionario
        """
        return {
            "type": "particle",
            "effect_type": self.effect_type,
            "max_particles": self.max_particles,
            "lifetime": self.lifetime,
            "color": self.color,
            "size": self.size,
            "active": self.active,
            "velocity": self.velocity,
            "acceleration": self.acceleration,
            "spawn_rate": self.spawn_rate
        }
        
    @classmethod
    def from_dict(cls, data):
        """
        Crea un componente particellare da un dizionario
        
        Args:
            data (dict): Dizionario con i dati del componente
            
        Returns:
            ParticleComponent: Nuova istanza del componente
        """
        component = cls(
            effect_type=data.get("effect_type"),
            max_particles=data.get("max_particles", 50),
            lifetime=data.get("lifetime", 1.0),
            color=data.get("color", 0xFFFFFF),
            size=data.get("size", 1.0),
            active=data.get("active", False)
        )
        
        if "velocity" in data:
            component.velocity = data["velocity"]
            
        if "acceleration" in data:
            component.acceleration = data["acceleration"]
            
        if "spawn_rate" in data:
            component.spawn_rate = data["spawn_rate"]
            
        return component


class AnimationComponent(Component):
    """Componente che gestisce le animazioni di un'entità"""
    
    def __init__(self, animations=None, current_animation=None, speed=1.0, 
                loop=True, auto_play=True):
        """
        Inizializza un nuovo componente animazione
        
        Args:
            animations (dict): Dizionario con le animazioni disponibili
            current_animation (str): Nome dell'animazione corrente
            speed (float): Velocità di riproduzione
            loop (bool): Indica se l'animazione deve essere ripetuta in loop
            auto_play (bool): Indica se l'animazione deve iniziare automaticamente
        """
        super().__init__()
        self.animations = animations or {}  # nome -> dati animazione
        self.current_animation = current_animation
        self.speed = speed
        self.loop = loop
        self.auto_play = auto_play
        self.current_frame = 0
        self.frame_time = 0
        self.playing = auto_play
        self.finished = False
        
    def to_dict(self):
        """
        Converte il componente in un dizionario
        
        Returns:
            dict: Rappresentazione del componente come dizionario
        """
        return {
            "type": "animation",
            "animations": self.animations,
            "current_animation": self.current_animation,
            "speed": self.speed,
            "loop": self.loop,
            "auto_play": self.auto_play,
            "current_frame": self.current_frame,
            "playing": self.playing
        }
        
    @classmethod
    def from_dict(cls, data):
        """
        Crea un componente animazione da un dizionario
        
        Args:
            data (dict): Dizionario con i dati del componente
            
        Returns:
            AnimationComponent: Nuova istanza del componente
        """
        component = cls(
            animations=data.get("animations", {}),
            current_animation=data.get("current_animation"),
            speed=data.get("speed", 1.0),
            loop=data.get("loop", True),
            auto_play=data.get("auto_play", True)
        )
        
        component.current_frame = data.get("current_frame", 0)
        component.playing = data.get("playing", component.auto_play)
        
        return component
        
    def add_animation(self, name, frames, frame_duration=0.1):
        """
        Aggiunge una nuova animazione
        
        Args:
            name (str): Nome dell'animazione
            frames (list): Lista di frame (nomi sprite)
            frame_duration (float): Durata di ogni frame in secondi
        """
        self.animations[name] = {
            "frames": frames,
            "frame_duration": frame_duration
        }
        
    def play(self, animation_name=None, reset=True):
        """
        Avvia la riproduzione di un'animazione
        
        Args:
            animation_name (str, optional): Nome dell'animazione da riprodurre
            reset (bool): Se True, resetta l'animazione dall'inizio
        """
        if animation_name:
            self.current_animation = animation_name
            
        if self.current_animation in self.animations:
            self.playing = True
            self.finished = False
            
            if reset:
                self.current_frame = 0
                self.frame_time = 0
                
    def stop(self):
        """Interrompe la riproduzione dell'animazione corrente"""
        self.playing = False
    
    def pause(self):
        """Mette in pausa l'animazione corrente"""
        self.playing = False
        
    def resume(self):
        """Riprende un'animazione in pausa"""
        self.playing = True


class CameraComponent(Component):
    """Componente che rappresenta una camera che segue un'entità o un punto"""
    
    def __init__(self, target_id=None, offset_x=0, offset_y=0, zoom=1.0,
                smoothing=0.1, viewport_width=800, viewport_height=600,
                bounds=None):
        """
        Inizializza un nuovo componente camera
        
        Args:
            target_id (str): ID dell'entità da seguire
            offset_x (float): Offset orizzontale dalla posizione target
            offset_y (float): Offset verticale dalla posizione target
            zoom (float): Livello di zoom
            smoothing (float): Fattore di smoothing per il movimento
            viewport_width (int): Larghezza del viewport in pixel
            viewport_height (int): Altezza del viewport in pixel
            bounds (dict): Limiti della camera (x, y, width, height)
        """
        super().__init__()
        self.target_id = target_id
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.zoom = zoom
        self.smoothing = smoothing
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.bounds = bounds or {"x": 0, "y": 0, "width": 10000, "height": 10000}
        self.position_x = 0
        self.position_y = 0
        self.target_x = 0
        self.target_y = 0
        
    def to_dict(self):
        """
        Converte il componente in un dizionario
        
        Returns:
            dict: Rappresentazione del componente come dizionario
        """
        return {
            "type": "camera",
            "target_id": self.target_id,
            "offset_x": self.offset_x,
            "offset_y": self.offset_y,
            "zoom": self.zoom,
            "smoothing": self.smoothing,
            "viewport_width": self.viewport_width,
            "viewport_height": self.viewport_height,
            "bounds": self.bounds,
            "position_x": self.position_x,
            "position_y": self.position_y
        }
        
    @classmethod
    def from_dict(cls, data):
        """
        Crea un componente camera da un dizionario
        
        Args:
            data (dict): Dizionario con i dati del componente
            
        Returns:
            CameraComponent: Nuova istanza del componente
        """
        component = cls(
            target_id=data.get("target_id"),
            offset_x=data.get("offset_x", 0),
            offset_y=data.get("offset_y", 0),
            zoom=data.get("zoom", 1.0),
            smoothing=data.get("smoothing", 0.1),
            viewport_width=data.get("viewport_width", 800),
            viewport_height=data.get("viewport_height", 600),
            bounds=data.get("bounds")
        )
        
        component.position_x = data.get("position_x", 0)
        component.position_y = data.get("position_y", 0)
        
        return component 