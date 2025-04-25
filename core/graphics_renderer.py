import json
import time
import uuid
from typing import Dict, List, Any, Optional

class GraphicsRenderer:
    """
    Classe che fornisce un'interfaccia per il rendering grafico.
    Questa classe funge da ponte tra il sistema ECS e il frontend grafico.
    """
    
    def __init__(self, socket_io=None):
        """
        Inizializza il renderer grafico
        
        Args:
            socket_io: Oggetto SocketIO per la comunicazione con il client
        """
        self.socket_io = socket_io
        self.camera = {
            "x": 0,
            "y": 0,
            "zoom": 1.0,
            "viewport_width": 800,
            "viewport_height": 600
        }
        self.render_id = str(uuid.uuid4())  # ID univoco per questo ciclo di rendering
        self.frame_count = 0
        self.last_frame_time = time.time()
        self.fps = 0
        self.draw_calls = 0
        self.entity_cache = {}  # Cache degli oggetti già renderizzati
        self.debug_mode = False
        # Aggiungiamo un buffer per gli eventi di rendering
        self.render_events = []
        
    def set_socket_io(self, socket_io):
        """
        Imposta l'oggetto SocketIO per la comunicazione con il client
        
        Args:
            socket_io: Oggetto SocketIO
        """
        self.socket_io = socket_io
        
    def set_camera(self, camera_data):
        """
        Imposta i parametri della camera
        
        Args:
            camera_data (dict): Dati della camera (x, y, zoom, viewport_width, viewport_height)
        """
        if camera_data:
            self.camera.update(camera_data)
        
    def clear_screen(self):
        """Pulisce lo schermo"""
        self.render_id = str(uuid.uuid4())
        self.draw_calls = 0
        
        # Invia evento di pulizia schermo al client
        if self.socket_io:
            render_data = {
                "render_id": self.render_id,
                "timestamp": time.time()
            }
            self.socket_io.emit('render_clear', render_data)
            # Aggiungi anche all'elenco eventi
            self.push_render_event('render_clear', render_data)
        
    def draw_entity(self, entity_data):
        """
        Disegna un'entità o un elemento visivo
        
        Args:
            entity_data (dict): Dati dell'entità da renderizzare
        """
        self.draw_calls += 1
        
        # Crea una copia dei dati per evitare modifiche indesiderate
        render_data = entity_data.copy()
        
        # Applica trasformazione camera per convertire coordinate mondo in coordinate schermo
        render_data["screen_x"] = (render_data["x"] - self.camera["x"]) * self.camera["zoom"] + self.camera["viewport_width"] / 2
        render_data["screen_y"] = (render_data["y"] - self.camera["y"]) * self.camera["zoom"] + self.camera["viewport_height"] / 2
        render_data["screen_scale"] = render_data.get("scale", 1.0) * self.camera["zoom"]
        
        # Aggiungi info rendering
        render_data["render_id"] = self.render_id
        render_data["draw_call"] = self.draw_calls
        
        # Ottimizzazione: controlla se l'entità è visibile sullo schermo
        viewport_margin = 100  # pixel extra oltre il viewport per evitare pop-in
        if (render_data["screen_x"] < -viewport_margin or 
            render_data["screen_x"] > self.camera["viewport_width"] + viewport_margin or
            render_data["screen_y"] < -viewport_margin or
            render_data["screen_y"] > self.camera["viewport_height"] + viewport_margin):
            # Entità fuori schermo, salta il rendering
            return
        
        # Invia comando di rendering al client
        if self.socket_io:
            self.socket_io.emit('render_entity', render_data)
            # Aggiungi anche all'elenco eventi
            self.push_render_event('render_entity', render_data)
        
    def draw_particle_system(self, particle_data):
        """
        Disegna un sistema di particelle
        
        Args:
            particle_data (dict): Dati del sistema di particelle
        """
        # Simile a draw_entity, ma ottimizzato per i sistemi di particelle
        self.draw_calls += 1
        
        # Applica trasformazione camera
        screen_x = (particle_data["x"] - self.camera["x"]) * self.camera["zoom"] + self.camera["viewport_width"] / 2
        screen_y = (particle_data["y"] - self.camera["y"]) * self.camera["zoom"] + self.camera["viewport_height"] / 2
        
        # Controlla se il sistema di particelle è visibile
        if (screen_x < -200 or screen_x > self.camera["viewport_width"] + 200 or
            screen_y < -200 or screen_y > self.camera["viewport_height"] + 200):
            # Sistema di particelle fuori schermo, salta il rendering
            return
        
        # Dati rendering
        render_data = {
            "type": "particle_system",
            "id": particle_data["id"],
            "effect_type": particle_data.get("effect_type", "default"),
            "x": particle_data["x"],
            "y": particle_data["y"],
            "screen_x": screen_x,
            "screen_y": screen_y,
            "particles": particle_data.get("particles", []),
            "render_id": self.render_id,
            "draw_call": self.draw_calls
        }
        
        # Invia comando di rendering al client
        if self.socket_io:
            self.socket_io.emit('render_particles', render_data)
            # Aggiungi anche all'elenco eventi
            self.push_render_event('render_particles', render_data)
    
    def draw_ui_element(self, ui_data):
        """
        Disegna un elemento dell'interfaccia utente
        
        Args:
            ui_data (dict): Dati dell'elemento UI da renderizzare
        """
        self.draw_calls += 1
        
        # Gli elementi UI in genere usano coordinate schermo dirette
        render_data = ui_data.copy()
        render_data["render_id"] = self.render_id
        render_data["draw_call"] = self.draw_calls
        
        # Invia comando di rendering al client
        if self.socket_io:
            self.socket_io.emit('render_ui', render_data)
            # Aggiungi anche all'elenco eventi
            self.push_render_event('render_ui', render_data)
    
    def present(self):
        """Finalizza il rendering e presenta il frame"""
        # Calcola FPS
        current_time = time.time()
        delta_time = current_time - self.last_frame_time
        self.last_frame_time = current_time
        
        if delta_time > 0:
            self.fps = 1.0 / delta_time
        
        self.frame_count += 1
        
        # Dati completamento frame
        render_data = {
            "render_id": self.render_id,
            "frame": self.frame_count,
            "draw_calls": self.draw_calls,
            "fps": round(self.fps, 1),
            "timestamp": current_time
        }
        
        # Invia segnale di completamento frame al client
        if self.socket_io:
            self.socket_io.emit('render_complete', render_data)
            # Aggiungi anche all'elenco eventi
            self.push_render_event('render_complete', render_data)
    
    def toggle_debug_mode(self):
        """Attiva/disattiva la modalità debug"""
        self.debug_mode = not self.debug_mode
        debug_data = {"enabled": self.debug_mode}
        if self.socket_io:
            self.socket_io.emit('debug_mode', debug_data)
            # Aggiungi anche all'elenco eventi
            self.push_render_event('debug_mode', debug_data)
    
    def set_environment(self, env_data):
        """
        Imposta parametri ambientali (luce, meteo, ecc.)
        
        Args:
            env_data (dict): Parametri ambientali
        """
        if self.socket_io:
            self.socket_io.emit('set_environment', env_data)
            # Aggiungi anche all'elenco eventi
            self.push_render_event('set_environment', env_data)
    
    def play_sound(self, sound_data):
        """
        Riproduce un suono
        
        Args:
            sound_data (dict): Dati del suono da riprodurre
        """
        if self.socket_io:
            self.socket_io.emit('play_sound', sound_data)
            # Aggiungi anche all'elenco eventi
            self.push_render_event('play_sound', sound_data)
    
    def play_music(self, music_data):
        """
        Riproduce una traccia musicale di sottofondo
        
        Args:
            music_data (dict): Dati della musica da riprodurre
        """
        if self.socket_io:
            self.socket_io.emit('play_music', music_data)
            # Aggiungi anche all'elenco eventi
            self.push_render_event('play_music', music_data)
            
    def stop_music(self, fade_out=1.0):
        """
        Interrompe la riproduzione musicale
        
        Args:
            fade_out (float): Tempo di fade out in secondi
        """
        stop_data = {"fade_out": fade_out}
        if self.socket_io:
            self.socket_io.emit('stop_music', stop_data)
            # Aggiungi anche all'elenco eventi
            self.push_render_event('stop_music', stop_data)
    
    def render_tilemap(self, tilemap_data):
        """
        Renderizza una mappa di tile
        
        Args:
            tilemap_data (dict): Dati della mappa di tile
        """
        # Ottimizza il rendering della mappa inviando solo i tile visibili
        if not tilemap_data or not self.socket_io:
            return
            
        # Calcola i tile visibili in base alla posizione della camera
        tile_size = tilemap_data.get("tile_size", 32)
        map_width = tilemap_data.get("width", 0)
        map_height = tilemap_data.get("height", 0)
        layers = tilemap_data.get("layers", [])
        
        # Calcola il range di tile visibili
        scaled_tile_size = tile_size * self.camera["zoom"]
        start_x = max(0, int((self.camera["x"] - self.camera["viewport_width"] / 2 / self.camera["zoom"]) / tile_size))
        start_y = max(0, int((self.camera["y"] - self.camera["viewport_height"] / 2 / self.camera["zoom"]) / tile_size))
        end_x = min(map_width, int((self.camera["x"] + self.camera["viewport_width"] / 2 / self.camera["zoom"]) / tile_size) + 2)
        end_y = min(map_height, int((self.camera["y"] + self.camera["viewport_height"] / 2 / self.camera["zoom"]) / tile_size) + 2)
        
        # Prepara dati della mappa visibile
        visible_tilemap = {
            "tile_size": tile_size,
            "width": map_width,
            "height": map_height,
            "start_x": start_x,
            "start_y": start_y,
            "end_x": end_x,
            "end_y": end_y,
            "camera": {
                "x": self.camera["x"],
                "y": self.camera["y"],
                "zoom": self.camera["zoom"]
            },
            "render_id": self.render_id,
            "visible_layers": []
        }
        
        # Estrai solo i tile visibili per ogni layer
        for layer in layers:
            layer_id = layer.get("id", 0)
            layer_name = layer.get("name", f"layer_{layer_id}")
            layer_data = layer.get("data", [])
            
            visible_layer = {
                "id": layer_id,
                "name": layer_name,
                "visible_tiles": []
            }
            
            # Estrai solo i tile visibili
            for y in range(start_y, end_y):
                for x in range(start_x, end_x):
                    if 0 <= y < map_height and 0 <= x < map_width:
                        tile_idx = y * map_width + x
                        if tile_idx < len(layer_data) and layer_data[tile_idx] > 0:
                            visible_layer["visible_tiles"].append({
                                "x": x,
                                "y": y,
                                "tile_id": layer_data[tile_idx]
                            })
            
            visible_tilemap["visible_layers"].append(visible_layer)
        
        # Invia i dati della mappa visibile al client
        self.socket_io.emit('render_tilemap', visible_tilemap)
        # Aggiungi anche all'elenco eventi
        self.push_render_event('render_tilemap', visible_tilemap)
        
    def get_renderer_info(self):
        """
        Restituisce informazioni sul renderer
        
        Returns:
            dict: Informazioni sul renderer
        """
        return {
            "camera": self.camera,
            "fps": round(self.fps, 1),
            "frame_count": self.frame_count,
            "draw_calls": self.draw_calls,
            "debug_mode": self.debug_mode
        }
    
    def get_renderer_events(self):
        """
        Restituisce tutti gli eventi di rendering accumulati e pulisce il buffer
        
        Returns:
            list: Lista degli eventi di rendering in attesa
        """
        events = self.render_events.copy()
        self.render_events = []
        return events
        
    def push_render_event(self, event_type: str, event_data: dict = None):
        """
        Aggiunge un evento di rendering alla coda eventi
        
        Args:
            event_type (str): Tipo di evento di rendering
            event_data (dict): Dati associati all'evento
        """
        event = {
            "id": str(uuid.uuid4()),
            "type": event_type,
            "data": event_data or {},
            "timestamp": time.time()
        }
        self.render_events.append(event) 