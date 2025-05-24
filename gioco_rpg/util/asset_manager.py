"""
Asset Manager per la gestione degli asset di gioco.
Fornisce funzionalità per caricare, registrare e gestire asset come sprite, tiles, animazioni, etc.
"""

import os
import json
import logging
import time
import traceback
import atexit
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

# Importa il gestore degli sprite sheet
from util.sprite_sheet_manager import get_sprite_sheet_manager

logger = logging.getLogger(__name__)

# Singleton globale
_global_asset_manager = None

def cleanup_assets():
    """
    Pulisce tutte le risorse degli asset.
    Chiude tutti gli AssetManager aperti.
    """
    global _global_asset_manager
    
    # Chiudi tutti gli AssetManager aperti
    AssetManager.close_all()
    
    # Reset dell'istanza globale
    _global_asset_manager = None
    
    logger.info("Pulizia asset completata")

def get_asset_manager(base_path=None):
    """
    Restituisce l'istanza singleton dell'AssetManager.
    
    Args:
        base_path (str, optional): Il percorso base per gli asset.
        
    Returns:
        AssetManager: L'istanza dell'AssetManager.
    """
    global _global_asset_manager
    if _global_asset_manager is None:
        _global_asset_manager = AssetManager(base_path)
    return _global_asset_manager

class AssetManager:
    """
    Gestisce gli asset di gioco.
    Fornisce funzionalità per caricare, registrare e gestire asset come sprite, tiles, animazioni, etc.
    """
    
    # Registro di tutti gli AssetManager aperti per garantire la pulizia
    _open_managers = []
    
    # Tipi di asset supportati
    ASSET_TYPES = {
        "sprites": "sprite",
        "tiles": "tile",
        "animations": "animation",
        "tilesets": "tileset",
        "ui": "ui",
        "maps": "background"
    }
    
    @classmethod
    def close_all(cls):
        """Chiude tutti gli AssetManager aperti."""
        if not hasattr(cls, '_open_managers'):
            cls._open_managers = []
            return
        
        # Crea una copia della lista per evitare problemi durante l'iterazione
        managers_to_close = list(cls._open_managers)
        for manager in managers_to_close:
            try:
                # Chiudi esplicitamente le risorse
                if manager is not None:
                    manager._cleanup()
            except Exception as e:
                logger.error(f"Errore nella chiusura di un AssetManager: {e}")
        
        # Pulisci la lista
        cls._open_managers.clear()
    
    def __init__(self, base_path=None):
        """
        Inizializza l'AssetManager.
        
        Args:
            base_path (str, optional): Il percorso base per gli asset.
        """
        # Percorso base per gli asset
        self.base_path = base_path if base_path else os.path.join(os.getcwd(), "assets")
        
        # Normalizza il percorso per evitare problemi su Windows
        self.base_path = os.path.normpath(self.base_path)
        
        # Verifica se la directory esiste e creala se necessario
        if not os.path.exists(self.base_path):
            try:
                os.makedirs(self.base_path)
                logger.info(f"Creata directory degli asset: {self.base_path}")
            except Exception as e:
                logger.error(f"Errore nella creazione della directory degli asset {self.base_path}: {e}")
        
        # Inizializza i registri degli asset
        self.sprites = {}
        self.tiles = {}
        self.animations = {}
        self.tilesets = {}
        self.ui_elements = {}
        self.backgrounds = {}
        
        # Percorso del manifest
        self.manifest_path = os.path.join(self.base_path, "manifest.json")
        
        # Inizializza il manifest
        self.manifest = {
            "version": "1.0.0",
            "last_updated": time.time(),
            "sprites": self.sprites,
            "tiles": self.tiles,
            "animations": self.animations,
            "tilesets": self.tilesets,
            "ui_elements": self.ui_elements,
            "backgrounds": self.backgrounds
        }
        
        # Inizializza il gestore degli sprite sheet
        self.sprite_sheet_manager = get_sprite_sheet_manager(os.path.join(self.base_path, "spritesheets"))
        
        # Registra questo manager
        AssetManager._open_managers.append(self)
        
        # Carica il manifest se esiste o crea un manifest vuoto
        if not self.load_manifest():
            self.save_manifest()
        
        logger.info(f"AssetManager inizializzato con percorso {self.base_path}")
        
        # Registra la pulizia delle risorse all'uscita
        atexit.register(self._cleanup)
    
    def _cleanup(self):
        """Pulisce le risorse aperte."""
        try:
            # Salva il manifest prima di chiudere
            self.save_manifest()
            
            # Rimuovi questo manager dal registro in modo sicuro
            if hasattr(AssetManager, '_open_managers'):
                try:
                    if self in AssetManager._open_managers:
                        AssetManager._open_managers.remove(self)
                except (ValueError, TypeError):
                    # Ignora errori di rimozione, potrebbe essere già stato rimosso
                    pass
            
            logger.debug(f"AssetManager ripulito: {self.base_path}")
        except Exception as e:
            logger.error(f"Errore durante la pulizia dell'AssetManager: {e}")
    
    def __del__(self):
        """Distruttore per garantire la pulizia delle risorse."""
        try:
            self._cleanup()
        except:
            pass
    
    def load_manifest(self):
        """
        Carica il manifest degli asset.
        Il manifest contiene i metadati di tutti gli asset registrati.
        
        Returns:
            bool: True se il manifest è stato caricato con successo, False altrimenti.
        """
        if os.path.exists(self.manifest_path):
            try:
                logger.debug(f"Caricamento manifest da {self.manifest_path}")
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    self.manifest = json.load(f)
                
                # Aggiorna i registri
                self.sprites = self.manifest.get("sprites", {})
                self.tiles = self.manifest.get("tiles", {})
                self.animations = self.manifest.get("animations", {})
                self.tilesets = self.manifest.get("tilesets", {})
                self.ui_elements = self.manifest.get("ui_elements", {})
                self.backgrounds = self.manifest.get("backgrounds", {})
                
                logger.info(f"Manifest caricato con successo: {len(self.sprites)} sprites, {len(self.tiles)} tiles")
                return True
            except Exception as e:
                logger.error(f"Errore nel caricamento del manifest {self.manifest_path}: {e}")
                logger.debug(traceback.format_exc())
                return False
        else:
            logger.warning(f"Manifest non trovato in {self.manifest_path}")
            return False
    
    def save_manifest(self):
        """
        Salva il manifest degli asset.
        
        Returns:
            bool: True se il manifest è stato salvato con successo, False altrimenti.
        """
        try:
            # Crea le directory necessarie
            os.makedirs(os.path.dirname(self.manifest_path), exist_ok=True)
            
            # Aggiorna i dati del manifest
            self.manifest.update({
                "version": "1.0.0",
                "last_updated": time.time(),
                "sprites": self.sprites,
                "tiles": self.tiles,
                "animations": self.animations,
                "tilesets": self.tilesets,
                "ui_elements": self.ui_elements,
                "backgrounds": self.backgrounds
            })
            
            # Salva il manifest
            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump(self.manifest, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Manifest salvato con successo in {self.manifest_path}")
            return True
            
        except Exception as e:
            logger.error(f"Errore nel salvataggio del manifest: {e}")
            logger.debug(traceback.format_exc())
            return False
    
    def register_asset(self, asset_type: str, asset_id: str, name: str, file_path: str, 
                     **kwargs) -> bool:
        """
        Registra un asset nel registro appropriato.
        
        Args:
            asset_type (str): Tipo di asset (sprite, tile, ui, ecc.)
            asset_id (str): ID univoco per questo asset
            name (str): Nome descrittivo
            file_path (str): Percorso relativo al file dell'asset
            **kwargs: Attributi specifici per tipo di asset
            
        Returns:
            bool: True se l'asset è stato registrato con successo, False altrimenti
        """
        try:
            # Trova il registro appropriato
            registry = None
            if asset_type == "sprite":
                registry = self.sprites
            elif asset_type == "tile":
                registry = self.tiles
            elif asset_type == "ui":
                registry = self.ui_elements
            elif asset_type == "animation":
                registry = self.animations
            elif asset_type == "tileset":
                registry = self.tilesets
            elif asset_type == "background":
                registry = self.backgrounds
            else:
                logger.error(f"Tipo di asset non supportato: {asset_type}")
                return False
            
            # Verifica che il file esista
            abs_path = os.path.join(self.base_path, file_path)
            if not os.path.exists(abs_path):
                logger.warning(f"File asset {asset_id} non trovato: {file_path}")
                return False
                
            # Crea l'asset base
            asset_data = {
                "id": asset_id,
                "name": name,
                "file": file_path,
                "tags": kwargs.get("tags", []),
                "last_updated": time.time()
            }
            
            # Aggiungi attributi specifici per tipo
            if asset_type == "sprite":
                asset_data.update({
                    "dimensions": kwargs.get("dimensions"),
                    "offset": kwargs.get("offset")
                })
            elif asset_type == "tile":
                asset_data.update({
                    "dimensions": kwargs.get("dimensions"),
                    "properties": kwargs.get("properties", {})
                })
            elif asset_type == "ui":
                asset_data.update({
                    "dimensions": kwargs.get("dimensions", {"width": 64, "height": 32}),
                    "type": "ui"
                })
                # Aggiungi anche il percorso normalizzato
                if os.path.isabs(file_path):
                    asset_data["path"] = os.path.relpath(file_path, self.base_path).replace("\\", "/")
                else:
                    asset_data["path"] = file_path.replace("\\", "/")
            elif asset_type == "background":
                asset_data.update({
                    "dimensions": kwargs.get("dimensions"),
                    "map_id": kwargs.get("map_id")
                })
                # Aggiungi anche il percorso normalizzato
                if os.path.isabs(file_path):
                    asset_data["path"] = os.path.relpath(file_path, self.base_path).replace("\\", "/")
                else:
                    asset_data["path"] = file_path.replace("\\", "/")
            
            # Registra l'asset
            registry[asset_id] = asset_data
            
            logger.debug(f"{asset_type.capitalize()} registrato: {asset_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Errore nella registrazione dell'asset {asset_type}/{asset_id}: {e}")
            logger.debug(traceback.format_exc())
            return False
    
    def register_sprite(self, sprite_id, name, file_path, dimensions=None, offset=None, tags=None):
        """
        Registra uno sprite nel registro degli asset.
        
        Args:
            sprite_id (str): ID univoco per questo sprite
            name (str): Nome descrittivo
            file_path (str): Percorso relativo al file dell'asset
            dimensions (tuple, optional): Dimensioni (larghezza, altezza)
            offset (tuple, optional): Offset di disegno (x, y)
            tags (list, optional): Tag per categorizzare lo sprite
            
        Returns:
            bool: True se lo sprite è stato registrato con successo, False altrimenti
        """
        return self.register_asset(
            asset_type="sprite",
            asset_id=sprite_id,
            name=name,
            file_path=file_path,
            dimensions=dimensions,
            offset=offset,
            tags=tags or []
        )
    
    def register_tile(self, tile_id, name, file_path, dimensions=None, properties=None, tags=None):
        """
        Registra un tile nel registro degli asset.
        
        Args:
            tile_id (str): ID univoco per questo tile
            name (str): Nome descrittivo
            file_path (str): Percorso relativo al file dell'asset
            dimensions (tuple, optional): Dimensioni (larghezza, altezza)
            properties (dict, optional): Proprietà del tile (es. walkable, transparent)
            tags (list, optional): Tag per categorizzare il tile
            
        Returns:
            bool: True se il tile è stato registrato con successo, False altrimenti
        """
        return self.register_asset(
            asset_type="tile", 
            asset_id=tile_id,
            name=name,
            file_path=file_path,
            dimensions=dimensions,
            properties=properties,
            tags=tags or []
        )
    
    def register_ui_element(self, ui_id, name, file_path, dimensions=None, tags=None):
        """
        Registra un elemento UI.
        
        Args:
            ui_id (str): ID univoco dell'elemento UI.
            name (str): Nome leggibile dell'elemento UI.
            file_path (str): Percorso del file relativo alla directory degli asset.
            dimensions (dict, optional): Dimensioni dell'elemento {"width": w, "height": h}.
            tags (list, optional): Tag associati all'elemento UI.
        
        Returns:
            bool: True se l'elemento UI è stato registrato con successo, False altrimenti.
        """
        return self.register_asset(
            asset_type="ui",
            asset_id=ui_id,
            name=name,
            file_path=file_path,
            dimensions=dimensions,
            tags=tags or []
        )
    
    def register_background(self, background_id, name, file_path, map_id=None, dimensions=None, tags=None):
        """
        Registra un'immagine di sfondo per una mappa.
        
        Args:
            background_id (str): ID univoco dell'immagine di sfondo.
            name (str): Nome leggibile dell'immagine di sfondo.
            file_path (str): Percorso del file relativo alla directory degli asset.
            map_id (str, optional): ID della mappa associata.
            dimensions (dict, optional): Dimensioni dell'immagine {"width": w, "height": h}.
            tags (list, optional): Tag associati all'immagine di sfondo.
        
        Returns:
            bool: True se l'immagine di sfondo è stata registrata con successo, False altrimenti.
        """
        return self.register_asset(
            asset_type="background",
            asset_id=background_id,
            name=name,
            file_path=file_path,
            map_id=map_id,
            dimensions=dimensions,
            tags=tags or []
        )
    
    def scan_sprites(self, directory=None):
        """
        Scansiona i file degli sprite e li registra.
        
        Args:
            directory (str, optional): Directory specifica da scansionare.
                                     Se non specificata, usa 'sprites' nella directory di base.
        
        Returns:
            int: Il numero di sprite scansionati e registrati.
        """
        if directory is None:
            directory = os.path.join(self.base_path, "sprites")
        
        count = self._scan_assets_in_directory(directory, "sprite")
        
        logger.info(f"Scansione sprite completata: {count} sprite registrati da {directory}")
        
        return count
    
    def scan_tiles(self, directory=None):
        """
        Scansiona i file dei tile e li registra.
        
        Args:
            directory (str, optional): Directory specifica da scansionare.
                                     Se non specificata, usa 'tiles' nella directory di base.
        
        Returns:
            int: Il numero di tile scansionati e registrati.
        """
        if directory is None:
            directory = os.path.join(self.base_path, "tiles")
        
        count = self._scan_assets_in_directory(directory, "tile")
        
        logger.info(f"Scansione tile completata: {count} tile registrati da {directory}")
        
        return count
    
    def scan_ui_elements(self, directory=None):
        """
        Scansiona i file degli elementi UI e li registra.
        
        Args:
            directory (str, optional): Directory specifica da scansionare.
                                     Se non specificata, usa 'ui' nella directory di base.
        
        Returns:
            int: Il numero di elementi UI scansionati e registrati.
        """
        if directory is None:
            directory = os.path.join(self.base_path, "ui")
        
        count = self._scan_assets_in_directory(directory, "ui")
        
        logger.info(f"Scansione elementi UI completata: {count} elementi registrati da {directory}")
        
        return count
    
    def scan_backgrounds(self, directory=None):
        """
        Scansiona i file delle immagini di sfondo e li registra.
        
        Args:
            directory (str, optional): Directory specifica da scansionare.
                                     Se non specificata, usa 'maps' nella directory di base.
        
        Returns:
            int: Il numero di immagini di sfondo scansionate e registrate.
        """
        if directory is None:
            directory = os.path.join(self.base_path, "maps")
        
        count = self._scan_assets_in_directory(directory, "background")
        
        logger.info(f"Scansione immagini di sfondo completata: {count} immagini registrate da {directory}")
        
        return count
    
    def _scan_assets_in_directory(self, directory, asset_type):
        """
        Scansiona una singola directory per un tipo specifico di asset.
        
        Args:
            directory (str): Percorso della directory da scansionare.
            asset_type (str): Tipo di asset atteso ('sprite', 'tile', ecc.).
            
        Returns:
            dict: Dizionario degli asset trovati nel formato {asset_id: info}.
        """
        assets_found = {}
        if not os.path.isdir(directory):
            logger.warning(f"Directory non trovata per la scansione: {directory}")
            return assets_found

        logger.debug(f"Scansione directory: {directory} per tipo: {asset_type}")
        for filename in os.listdir(directory):
            full_file_path = os.path.join(directory, filename)
            if os.path.isfile(full_file_path):
                # Qui potresti aggiungere controlli sull'estensione del file se necessario
                # es: if filename.lower().endswith(('.png', '.jpg')):

                asset_id = Path(filename).stem # Usa nome file senza estensione come ID
                name = asset_id # Default name è l'ID
                # Calcola il percorso relativo rispetto a self.base_path
                try:
                    relative_path = os.path.relpath(full_file_path, self.base_path).replace("\\", "/")
                except ValueError:
                    # Se i percorsi sono su drive diversi, usa il percorso completo
                    relative_path = full_file_path.replace("\\", "/")

                # Determina quale funzione di registrazione chiamare
                registered_successfully = False
                if asset_type == "sprite":
                    registered_successfully = self.register_sprite(sprite_id=asset_id, name=name, file_path=relative_path)
                elif asset_type == "tile":
                    registered_successfully = self.register_tile(tile_id=asset_id, name=name, file_path=relative_path)
                elif asset_type == "ui": # Assumendo che 'ui' sia il tipo corretto per ui_elements
                    registered_successfully = self.register_ui_element(ui_id=asset_id, name=name, file_path=relative_path)
                elif asset_type == "background":
                    registered_successfully = self.register_background(background_id=asset_id, name=name, file_path=relative_path)
                elif asset_type == "animation":
                    # Assumiamo esista un metodo register_animation
                    registered_successfully = self.register_animation(animation_id=asset_id, name=name, file_path=relative_path)
                elif asset_type == "tileset":
                    # Assumiamo esista un metodo register_tileset
                    registered_successfully = self.register_tileset(tileset_id=asset_id, name=name, file_path=relative_path)
                else:
                    logger.warning(f"Tipo asset '{asset_type}' non gestito durante scansione specifica per file {filename}")

                if registered_successfully:
                    assets_found[asset_id] = {"name": name, "path": relative_path}
                # else: # Log opzionale se la registrazione fallisce
                    # logger.warning(f"Registrazione fallita per asset {asset_id} ({asset_type}) in {relative_path}")

        return assets_found
    
    def update_all(self):
        """
        Scansiona tutte le directory degli asset e aggiorna il manifest.
        """
        logger.info(f"Avvio scansione di tutti gli asset da {self.base_path}")
        all_assets_found = {}
        has_changes = False
        
        # Scansiona le directory specifiche per ogni tipo di asset
        asset_directories = {
            "sprites": os.path.join(self.base_path, "sprites"),
            "tiles": os.path.join(self.base_path, "tiles"),
            "animations": os.path.join(self.base_path, "animations"),
            "tilesets": os.path.join(self.base_path, "tilesets"),
            "ui_elements": os.path.join(self.base_path, "ui"),
            "backgrounds": os.path.join(self.base_path, "maps") # Sfondo mappe in /maps ? verificare
        }
        
        for asset_folder_name, asset_type in self.ASSET_TYPES.items():
             directory_to_scan = os.path.join(self.base_path, asset_folder_name)
             if os.path.isdir(directory_to_scan):
                 try:
                     logger.debug(f"Scansione directory {directory_to_scan} per tipo {asset_type}")
                     found_in_dir = self._scan_assets_in_directory(directory_to_scan, asset_type)
                     # Unisci i risultati (questo sovrascriverà eventuali ID duplicati tra tipi diversi, 
                     # ma gli ID dovrebbero essere univoci globalmente o per tipo a seconda del design)
                     all_assets_found.update(found_in_dir) 
                     # Verifica se ci sono stati cambiamenti reali (più complesso, per ora salva sempre)
                     has_changes = True # Semplificato: assume sempre cambiamenti se la scansione avviene
                 except Exception as e:
                      logger.error(f"Errore durante la scansione di {directory_to_scan} per {asset_type}: {e}", exc_info=True)
             else:
                 logger.warning(f"Directory non trovata per tipo {asset_type}: {directory_to_scan}")

        # Se sono stati trovati cambiamenti (semplificato a sempre vero se scansione eseguita)
        if has_changes:
             logger.info("Rilevati cambiamenti negli asset, salvataggio manifest...")
             self.save_manifest()
        else:
             logger.info("Nessun cambiamento rilevato negli asset.")

    def get_asset_info(self, asset_type: str, asset_id: str) -> Optional[Dict]:
        """
        Ottiene le informazioni su un asset specifico.
        
        Args:
            asset_type (str): Tipo di asset ('sprite', 'tile', 'ui', ecc.)
            asset_id (str): L'ID dell'asset.
            
        Returns:
            dict: Le informazioni sull'asset o None se non trovato.
        """
        if asset_type == "sprite":
            return self.get_sprite_info(asset_id)
        elif asset_type == "tile":
            return self.get_tile_info(asset_id)
        elif asset_type == "ui":
            return self.get_ui_element_info(asset_id)
        elif asset_type == "animation":
            return self.animations.get(asset_id)
        elif asset_type == "tileset":
            return self.tilesets.get(asset_id)
        elif asset_type == "background":
            return self.backgrounds.get(asset_id)
        else:
            logger.warning(f"Tipo di asset non supportato: {asset_type}")
            return None

    def get_sprite_info(self, sprite_id):
        """
        Ottiene le informazioni su uno sprite specifico.
        
        Args:
            sprite_id (str): L'ID dello sprite.
            
        Returns:
            dict: Le informazioni sullo sprite o None se non trovato.
        """
        # Prima verifica se è nel registro standard degli sprite
        sprite_info = self.sprites.get(sprite_id)
        if sprite_info:
            return sprite_info
            
        # Se non trovato, verifica se è in uno sprite sheet
        return self.sprite_sheet_manager.get_sprite_info(sprite_id)
    
    def get_sprite_path(self, sprite_id):
        """
        Ottiene il percorso completo di uno sprite.
        
        Args:
            sprite_id (str): L'ID dello sprite.
            
        Returns:
            str or dict: Il percorso completo dello sprite o un dizionario con le informazioni dello sprite sheet
        """
        # Prima verifica se è nel registro standard degli sprite
        sprite_info = self.sprites.get(sprite_id)
        if sprite_info:
            return os.path.join(self.base_path, sprite_info.get("file", ""))
            
        # Se non trovato, verifica se è in uno sprite sheet
        sprite_data = self.sprite_sheet_manager.get_sprite_data_url(sprite_id)
        if sprite_data:
            return sprite_data
            
        return None
    
    def get_tile_info(self, tile_id):
        """
        Ottiene le informazioni su un tile specifico.
        
        Args:
            tile_id (str): L'ID del tile.
            
        Returns:
            dict: Le informazioni sul tile o None se non trovato.
        """
        return self.tiles.get(tile_id)
    
    def get_ui_element_info(self, ui_id):
        """
        Ottiene le informazioni su un elemento UI specifico.
        
        Args:
            ui_id (str): L'ID dell'elemento UI.
            
        Returns:
            dict: Le informazioni sull'elemento UI o None se non trovato.
        """
        return self.ui_elements.get(ui_id)
    
    def get_background_info(self, background_id):
        """
        Ottiene le informazioni su un'immagine di sfondo specifica.
        
        Args:
            background_id (str): L'ID dell'immagine di sfondo.
            
        Returns:
            dict: Le informazioni sull'immagine di sfondo o None se non trovata.
        """
        return self.backgrounds.get(background_id)
    
    def get_map_data(self, map_id):
        """
        Ottiene i dati di una mappa dal file JSON corrispondente.
        
        Args:
            map_id (str): L'ID della mappa.
            
        Returns:
            dict: I dati della mappa o None se non trovata.
        """
        try:
            # Percorso del file JSON della mappa
            map_path = os.path.join(os.getcwd(), "gioco_rpg", "data", "mappe", f"{map_id}.json")
            
            # Verifica se il file esiste
            if not os.path.exists(map_path):
                logger.warning(f"File mappa non trovato: {map_path}")
                return None
            
            # Carica il file JSON
            with open(map_path, "r", encoding="utf-8") as f:
                map_data = json.load(f)
            
            # Verifica che esista un'immagine di sfondo per questa mappa
            background_id = f"{map_id}_background"
            
            # Verifica se l'immagine di sfondo è registrata
            background_info = self.get_background_info(background_id)
            
            # Se non è registrata, controlla se esiste il file e registralo
            if not background_info:
                # Verifico se esiste un'immagine di sfondo nel percorso standard
                background_path = os.path.join(self.base_path, "maps", f"{background_id}.png")
                if os.path.exists(background_path):
                    # Registra l'immagine di sfondo
                    self.register_background(
                        background_id=background_id,
                        name=f"Sfondo {map_id}",
                        file_path=os.path.relpath(background_path, self.base_path),
                        map_id=map_id
                    )
                    background_info = self.get_background_info(background_id)
            
            # Se abbiamo trovato un'immagine di sfondo, aggiungila ai dati della mappa
            if background_info:
                map_data["backgroundImage"] = background_info.get("path", f"assets/maps/{background_id}.png")
            else:
                # Usa un percorso predefinito se non è stata trovata un'immagine specifica
                map_data["backgroundImage"] = f"assets/maps/{map_id}_background.png"
            
            return map_data
            
        except Exception as e:
            logger.error(f"Errore nel caricamento dei dati della mappa {map_id}: {e}")
            logger.debug(traceback.format_exc())
            return None
    
    def get_all_sprites(self):
        """Restituisce tutti gli sprite registrati"""
        return self.sprites
    
    def get_all_tiles(self):
        """Restituisce tutti i tiles registrati"""
        return self.tiles
    
    def get_all_animations(self):
        """Restituisce tutte le animazioni registrate"""
        return self.animations
    
    def get_all_tilesets(self):
        """Restituisce tutti i tilesets registrati"""
        return self.tilesets
    
    def get_all_ui_elements(self):
        """Restituisce tutti gli elementi UI registrati"""
        return self.ui_elements
    
    def get_all_backgrounds(self):
        """Restituisce tutte le immagini di sfondo registrate"""
        return self.backgrounds
    
    def get_all_assets(self, asset_type=None):
        """
        Restituisce tutti gli asset di un tipo specifico o tutti gli asset.
        
        Args:
            asset_type (str, optional): Tipo di asset. Se None, restituisce tutti gli asset.
            
        Returns:
            dict: Dizionario di asset.
        """
        if asset_type == "sprite":
            return self.sprites
        elif asset_type == "tile":
            return self.tiles
        elif asset_type == "ui":
            return self.ui_elements
        elif asset_type == "animation":
            return self.animations
        elif asset_type == "tileset":
            return self.tilesets
        elif asset_type == "background":
            return self.backgrounds
        else:
            # Restituisce tutti gli asset
            return {
                "sprites": self.sprites,
                "tiles": self.tiles,
                "animations": self.animations,
                "tilesets": self.tilesets,
                "ui_elements": self.ui_elements,
                "backgrounds": self.backgrounds
            }
    
    def get_asset_path(self, asset_type, asset_id):
        """
        Ottiene il percorso completo di un asset.
        
        Args:
            asset_type (str): Il tipo di asset (sprites, tiles, ui, ecc.).
            asset_id (str): L'ID dell'asset.
            
        Returns:
            str: Il percorso completo dell'asset o None se non trovato.
        """
        asset_info = self.get_asset_info(asset_type, asset_id)
        
        # Se l'asset è trovato, restituisci il percorso completo
        if asset_info:
            return os.path.join(self.base_path, asset_info.get("path", asset_info.get("file", "")))
        
        return None

    def generate_sprite_sheets(self):
        """
        Genera sprite sheet da varie directory di asset.
        Questo metodo analizza la directory degli asset e crea sprite sheet
        per ottimizzare il caricamento.
        
        Returns:
            bool: True se almeno uno sprite sheet è stato creato, False altrimenti
        """
        success = False
        
        # Directory da includere negli sprite sheet
        sprite_directories = [
            os.path.join(self.base_path, "sprites"),
            os.path.join(self.base_path, "tiles"),
            os.path.join(self.base_path, "ui"),
            os.path.join(self.base_path, "entities")
        ]
        
        # Crea sprite sheet per ciascuna directory
        for directory in sprite_directories:
            if os.path.exists(directory) and os.path.isdir(directory):
                # Genera uno sprite sheet per la directory principale
                sheet_id = os.path.basename(directory)
                if self.sprite_sheet_manager.generate_sprite_sheet_from_directory(directory, sheet_id):
                    success = True
                
                # Controlla le sottodirectory
                for subdir in os.listdir(directory):
                    subdir_path = os.path.join(directory, subdir)
                    if os.path.isdir(subdir_path):
                        subsheet_id = f"{sheet_id}_{subdir}"
                        if self.sprite_sheet_manager.generate_sprite_sheet_from_directory(subdir_path, subsheet_id):
                            success = True
        
        return success

    def check_for_missing_directories(self):
        # Implementa la logica per controllare la presenza di directory mancanti
        # Questo metodo può essere implementato in base alle esigenze specifiche del tuo progetto
        pass

    def scan_all_assets(self, force_rescan=False):
        # Implementa la logica per scansionare tutti gli asset
        # Questo metodo può essere implementato in base alle esigenze specifiche del tuo progetto
        pass

    def register_animation(self, animation_id: str, name: str, file_path: str, **kwargs) -> bool:
        """
        Registra un'animazione (placeholder).
        Le animazioni potrebbero essere definiti principalmente tramite file JSON che
        aggregano frame individuali, piuttosto che essere singoli file immagine da registrare qui.

        Args:
            animation_id (str): ID univoco dell'animazione.
            name (str): Nome descrittivo.
            file_path (str): Percorso relativo al file dell'asset.
            kwargs (dict, optional): Dati aggiuntivi per l'animazione (es. frame_rate, loop).
            
        Returns:
            bool: True se l'animazione è stata registrata/gestita, False altrimenti.
        """
        # Placeholder - l'utente ha indicato che file specifici di animazione potrebbero non esistere
        # o essere gestiti diversamente (es. definiti in JSON).
        # Questa implementazione evita l'AttributeError e permette la scansione.
        logger.info(f"Placeholder: Tentativo di registrare animazione '{animation_id}' da '{file_path}'. Questa funzionalità non è completamente implementata per la registrazione di file individuali.")
        # Potresti voler aggiungere l'asset al dizionario self.animations se necessario,
        # anche senza una logica di caricamento file complessa.
        # self.animations[animation_id] = {"id": animation_id, "name": name, "file": file_path, "path": file_path, **kwargs}
        return self.register_asset(
            asset_type="animation",
            asset_id=animation_id,
            name=name,
            file_path=file_path,
            **kwargs
        )

    def register_tileset(self, tileset_id: str, name: str, file_path: str, **kwargs) -> bool:
        """
        Registra un tileset (placeholder).
        I tileset potrebbero essere definiti principalmente tramite file JSON che
        aggregano tile individuali, piuttosto che essere singoli file immagine da registrare qui.

        Args:
            tileset_id (str): ID univoco del tileset.
            name (str): Nome descrittivo.
            file_path (str): Percorso relativo al file dell'asset.
            kwargs (dict, optional): Dati aggiuntivi per il tileset.

        Returns:
            bool: True se il tileset è stato registrato/gestito, False altrimenti.
        """
        # Placeholder - i tileset sono spesso definiti da JSON.
        logger.info(f"Placeholder: Tentativo di registrare tileset '{tileset_id}' da '{file_path}'. I tileset sono tipicamente definiti da file JSON.")
        # self.tilesets[tileset_id] = {"id": tileset_id, "name": name, "file": file_path, "path": file_path, **kwargs}
        return self.register_asset(
            asset_type="tileset",
            asset_id=tileset_id,
            name=name,
            file_path=file_path,
            **kwargs
        )

# Registra la pulizia globale all'uscita
atexit.register(AssetManager.close_all) 