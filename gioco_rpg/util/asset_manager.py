"""
Asset Manager per la gestione degli asset di gioco.
Fornisce funzionalità per caricare, registrare e gestire asset come sprite, tiles, animazioni, etc.
"""

import os
import json
import logging
import tempfile
import shutil
import time
import traceback
import atexit
from pathlib import Path

logger = logging.getLogger(__name__)

# Singleton globale
_global_asset_manager = None

# Classe per limitare il number di messaggi di log ripetitivi
class LogThrottler:
    def __init__(self, max_occurrences=3, reset_interval=300):
        self.log_counts = {}
        self.max_occurrences = max_occurrences
        self.reset_interval = reset_interval  # secondi
        self.last_reset = time.time()
    
    def should_log(self, message):
        # Reset periodico
        current_time = time.time()
        if current_time - self.last_reset > self.reset_interval:
            self.log_counts.clear()
            self.last_reset = current_time
            
        # Incrementa contatore per questo messaggio
        count = self.log_counts.get(message, 0) + 1
        self.log_counts[message] = count
        
        # Log solo se sotto la soglia o un multiplo della soglia
        # (permette di loggare "logged N times" periodicamente)
        return count <= self.max_occurrences or count % (self.max_occurrences * 5) == 0

# Inizializza il throttler
log_throttler = LogThrottler()

def throttled_log(level, message, logger=logger):
    """Logga un messaggio solo se non è stato loggato troppe volte."""
    if log_throttler.should_log(message):
        count = log_throttler.log_counts.get(message, 1)
        if count > log_throttler.max_occurrences:
            message = f"{message} (ripetuto {count} volte)"
        
        if level == logging.DEBUG:
            logger.debug(message)
        elif level == logging.INFO:
            logger.info(message)
        elif level == logging.WARNING:
            logger.warning(message)
        elif level == logging.ERROR:
            logger.error(message)
        elif level == logging.CRITICAL:
            logger.critical(message)

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
            "ui_elements": self.ui_elements
        }
        
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
        Salva il manifest degli asset con meccanismi di resilienza.
        Utilizza tre metodi diversi per assicurare che il file venga creato:
        1. Usa un file temporaneo e lo sposta (il più sicuro)
        2. Scrittura diretta se il primo metodo fallisce
        3. Scrittura tramite Path se le prime due falliscono
        
        Returns:
            bool: True se il manifest è stato salvato con successo, False altrimenti.
        """
        try:
            # Aggiungi le directory necessarie
            os.makedirs(os.path.dirname(self.manifest_path), exist_ok=True)
            
            # Aggiorna i dati del manifest
            self.manifest.update({
                "version": "1.0.0",
                "last_updated": time.time(),
                "sprites": self.sprites,
                "tiles": self.tiles,
                "animations": self.animations,
                "tilesets": self.tilesets,
                "ui_elements": self.ui_elements
            })
            
            # METODO 1: Usa un file temporaneo per la scrittura sicura
            success = self._save_manifest_temp_method(self.manifest)
            
            # METODO 2: Scrittura diretta (fallback)
            if not success:
                logger.warning("Usando metodo fallback per salvataggio manifest")
                success = self._save_manifest_direct_method(self.manifest)
            
            # METODO 3: Usa Path (ultimo tentativo)
            if not success:
                logger.warning("Usando metodo Path per salvataggio manifest (ultimo tentativo)")
                success = self._save_manifest_path_method(self.manifest)
            
            # Verifica finale
            if os.path.exists(self.manifest_path):
                logger.info(f"Manifest salvato con successo in {self.manifest_path}")
                return True
            else:
                logger.error(f"Impossibile creare il manifest nonostante multipli tentativi")
                return False
        
        except Exception as e:
            logger.error(f"Errore generale nel salvataggio del manifest: {e}")
            logger.debug(traceback.format_exc())
            return False
    
    def _save_manifest_temp_method(self, manifest_data):
        """Salva il manifest usando un file temporaneo."""
        try:
            # Crea un file temporaneo nella stessa directory
            fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(self.manifest_path), suffix=".json")
            try:
                # Chiudi il file descriptor
                os.close(fd)
                
                # Scrivi nel file temporaneo
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(manifest_data, f, indent=2, ensure_ascii=False)
                
                # Su Windows, assicurati che il file di destinazione non esista
                if os.path.exists(self.manifest_path):
                    try:
                        os.unlink(self.manifest_path)
                    except Exception as e:
                        logger.warning(f"Impossibile rimuovere manifest esistente: {e}")
                
                # Sposta il file temporaneo nella posizione finale
                shutil.move(temp_path, self.manifest_path)
                
                # Verifica
                if os.path.exists(self.manifest_path):
                    logger.debug(f"Manifest salvato con metodo file temporaneo")
                    return True
            finally:
                # Rimuovi il file temporaneo se esiste ancora
                if os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
        except Exception as e:
            logger.error(f"Errore con metodo file temporaneo: {e}")
        
        return False
    
    def _save_manifest_direct_method(self, manifest_data):
        """Salva il manifest con scrittura diretta."""
        try:
            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest_data, f, indent=2, ensure_ascii=False)
            
            if os.path.exists(self.manifest_path):
                logger.debug("Manifest salvato con metodo diretto")
                return True
        except Exception as e:
            logger.error(f"Errore con metodo diretto: {e}")
        
        return False
    
    def _save_manifest_path_method(self, manifest_data):
        """Salva il manifest usando pathlib.Path."""
        try:
            # Usa Path per la scrittura
            manifest_path = Path(self.manifest_path)
            manifest_path.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8")
            
            if os.path.exists(self.manifest_path):
                logger.debug("Manifest salvato con metodo Path")
                return True
        except Exception as e:
            logger.error(f"Errore con metodo Path: {e}")
        
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
        try:
            # Verifica se il file esiste
            abs_path = os.path.join(self.base_path, file_path)
            if not os.path.exists(abs_path):
                fallback_path = os.path.join(self.base_path, "fallback", file_path)
                if os.path.exists(fallback_path):
                    throttled_log(logging.WARNING, f"Sprite {sprite_id} non trovato, uso fallback: {fallback_path}")
                    file_path = os.path.join("fallback", file_path)
                    abs_path = fallback_path
                else:
                    throttled_log(logging.WARNING, f"Sprite {sprite_id} non trovato e nessun fallback disponibile: {file_path}")
                    return False
            
            # Registrazione sprite
            self.sprites[sprite_id] = {
                "id": sprite_id,
                "name": name,
                "file": file_path,
                "dimensions": dimensions,
                "offset": offset,
                "tags": tags or []
            }
            
            throttled_log(logging.DEBUG, f"Sprite registrato: {sprite_id}")
            
            # Aggiorna il manifest
            self.manifest["sprites"] = self.sprites
            
            return True
        except Exception as e:
            logger.error(f"Errore nella registrazione dello sprite {sprite_id}: {e}")
            logger.debug(traceback.format_exc())
            return False
    
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
        try:
            # Verifica se il file esiste
            abs_path = os.path.join(self.base_path, file_path)
            if not os.path.exists(abs_path):
                fallback_path = os.path.join(self.base_path, "fallback", file_path)
                if os.path.exists(fallback_path):
                    throttled_log(logging.WARNING, f"Tile {tile_id} non trovato, uso fallback: {fallback_path}")
                    file_path = os.path.join("fallback", file_path)
                    abs_path = fallback_path
                else:
                    throttled_log(logging.WARNING, f"Tile {tile_id} non trovato e nessun fallback disponibile: {file_path}")
                    return False
            
            # Registrazione tile
            self.tiles[tile_id] = {
                "id": tile_id,
                "name": name,
                "file": file_path,
                "dimensions": dimensions,
                "properties": properties or {},
                "tags": tags or []
            }
            
            throttled_log(logging.DEBUG, f"Tile registrato: {tile_id}")
            
            # Aggiorna il manifest
            self.manifest["tiles"] = self.tiles
            
            return True
        except Exception as e:
            logger.error(f"Errore nella registrazione del tile {tile_id}: {e}")
            logger.debug(traceback.format_exc())
            return False
    
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
        try:
            # Normalizza il percorso del file
            if os.path.isabs(file_path):
                # Se è un percorso assoluto, rendilo relativo alla directory di base
                rel_path = os.path.relpath(file_path, self.base_path)
            else:
                # Altrimenti, lo consideriamo già relativo
                rel_path = file_path.replace("\\", "/")
            
            # Ottieni solo il nome del file
            file_name = os.path.basename(file_path)
            
            # Crea il dizionario dell'elemento UI
            ui_data = {
                "id": ui_id,
                "name": name,
                "file": file_name,
                "path": rel_path,
                "type": "ui",
                "dimensions": dimensions if dimensions else {"width": 64, "height": 32},
                "tags": tags if tags else []
            }
            
            # Registra l'elemento UI
            self.ui_elements[ui_id] = ui_data
            
            logger.debug(f"Elemento UI registrato: {ui_id} ({rel_path})")
            
            # Salva il manifest
            self.save_manifest()
            
            return True
        
        except Exception as e:
            logger.error(f"Errore nella registrazione dell'elemento UI {ui_id}: {e}")
            return False
    
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
        
        count = 0
        
        if os.path.exists(directory):
            for file_name in os.listdir(directory):
                file_path = os.path.join(directory, file_name)
                
                # Verifica che sia un file e un'immagine
                if os.path.isfile(file_path) and file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                    # Estrai l'ID dal nome del file (senza estensione)
                    sprite_id = os.path.splitext(file_name)[0]
                    
                    # Registra lo sprite
                    self.register_sprite(
                        sprite_id=sprite_id,
                        name=sprite_id.capitalize(),
                        file_path=os.path.relpath(file_path, self.base_path)
                    )
                    
                    count += 1
        
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
        
        count = 0
        
        if os.path.exists(directory):
            for file_name in os.listdir(directory):
                file_path = os.path.join(directory, file_name)
                
                # Verifica che sia un file e un'immagine
                if os.path.isfile(file_path) and file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                    # Estrai l'ID dal nome del file (senza estensione)
                    tile_id = os.path.splitext(file_name)[0]
                    
                    # Registra il tile
                    self.register_tile(
                        tile_id=tile_id,
                        name=tile_id.capitalize(),
                        file_path=os.path.relpath(file_path, self.base_path)
                    )
                    
                    count += 1
        
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
        
        count = 0
        
        if os.path.exists(directory):
            for file_name in os.listdir(directory):
                file_path = os.path.join(directory, file_name)
                
                # Verifica che sia un file e un'immagine
                if os.path.isfile(file_path) and file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                    # Estrai l'ID dal nome del file (senza estensione)
                    ui_id = os.path.splitext(file_name)[0]
                    
                    # Registra l'elemento UI
                    self.register_ui_element(
                        ui_id=ui_id,
                        name=ui_id.capitalize(),
                        file_path=os.path.relpath(file_path, self.base_path)
                    )
                    
                    count += 1
        
        logger.info(f"Scansione elementi UI completata: {count} elementi registrati da {directory}")
        
        return count
    
    def update_all(self):
        """
        Aggiorna tutti gli asset scansionando tutte le directory.
        
        Returns:
            bool: True se l'aggiornamento è stato completato con successo, False altrimenti.
        """
        try:
            # Scansiona tutti i tipi di asset
            logger.info(f"Avvio scansione di tutti gli asset da {self.base_path}")
            logger.debug(f"Directory sprites: {os.path.join(self.base_path, 'sprites')}, esiste: {os.path.exists(os.path.join(self.base_path, 'sprites'))}")
            logger.debug(f"Directory tiles: {os.path.join(self.base_path, 'tiles')}, esiste: {os.path.exists(os.path.join(self.base_path, 'tiles'))}")
            logger.debug(f"Directory ui: {os.path.join(self.base_path, 'ui')}, esiste: {os.path.exists(os.path.join(self.base_path, 'ui'))}")
            
            # Verifica i contenuti delle directory
            self._log_directory_contents(os.path.join(self.base_path, 'sprites'), "sprites")
            self._log_directory_contents(os.path.join(self.base_path, 'tiles'), "tiles")
            self._log_directory_contents(os.path.join(self.base_path, 'ui'), "ui")
            
            # Prima della scansione, registra cosa c'è nei dizionari
            logger.debug(f"Sprite prima della scansione: {list(self.sprites.keys())}")
            logger.debug(f"Tiles prima della scansione: {list(self.tiles.keys())}")
            logger.debug(f"UI prima della scansione: {list(self.ui_elements.keys())}")
            
            sprites_count = self.scan_sprites()
            tiles_count = self.scan_tiles()
            ui_count = self.scan_ui_elements()
            
            # Dopo la scansione, verifica cosa è stato registrato
            logger.debug(f"Sprite dopo la scansione: {list(self.sprites.keys())}")
            logger.debug(f"Tiles dopo la scansione: {list(self.tiles.keys())}")
            logger.debug(f"UI dopo la scansione: {list(self.ui_elements.keys())}")
            
            # Salva il manifest aggiornato
            result = self.save_manifest()
            
            # Verifica che il manifest esista dopo il salvataggio
            manifest_exists = os.path.exists(self.manifest_path)
            logger.debug(f"Manifest dopo salvataggio: {self.manifest_path}, esiste: {manifest_exists}")
            
            if manifest_exists:
                try:
                    with open(self.manifest_path, "r", encoding="utf-8") as f:
                        manifest_data = json.load(f)
                    logger.debug(f"Contenuto manifest - sprite: {list(manifest_data.get('sprites', {}).keys())}")
                    logger.debug(f"Contenuto manifest - tiles: {list(manifest_data.get('tiles', {}).keys())}")
                except Exception as e:
                    logger.error(f"Errore nella lettura del manifest dopo salvataggio: {e}")
            
            # Log dei risultati
            total = sprites_count + tiles_count + ui_count
            logger.info(f"Aggiornamento completato: {total} asset totali registrati")
            logger.debug(f"Asset registrati: {sprites_count} sprites, {tiles_count} tiles, {ui_count} elementi UI")
            
            return result
        
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento di tutti gli asset: {e}")
            logger.debug(traceback.format_exc())
            return False
            
    def _log_directory_contents(self, directory, dir_type):
        """
        Registra il contenuto di una directory per debugging.
        
        Args:
            directory (str): Il percorso della directory da verificare.
            dir_type (str): Il tipo di directory (per il logging).
        """
        try:
            if os.path.exists(directory):
                files = os.listdir(directory)
                logger.debug(f"Contenuto directory {dir_type}: {files}")
                
                # Verifica se i file possono essere letti
                for file_name in files:
                    file_path = os.path.join(directory, file_name)
                    if os.path.isfile(file_path):
                        readable = os.access(file_path, os.R_OK)
                        logger.debug(f"File {file_path} leggibile: {readable}")
            else:
                logger.debug(f"Directory {dir_type} non esiste: {directory}")
        except Exception as e:
            logger.error(f"Errore nella verifica della directory {dir_type}: {e}")

    def get_sprite_info(self, sprite_id):
        """
        Ottiene le informazioni su uno sprite specifico.
        
        Args:
            sprite_id (str): L'ID dello sprite.
            
        Returns:
            dict: Le informazioni sullo sprite o None se non trovato.
        """
        return self.sprites.get(sprite_id)
    
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
    
    def get_asset_path(self, asset_type, asset_id):
        """
        Ottiene il percorso completo di un asset.
        
        Args:
            asset_type (str): Il tipo di asset (sprites, tiles, ui, ecc.).
            asset_id (str): L'ID dell'asset.
            
        Returns:
            str: Il percorso completo dell'asset o None se non trovato.
        """
        asset_info = None
        
        # Seleziona il tipo di asset
        if asset_type == "sprites":
            asset_info = self.get_sprite_info(asset_id)
        elif asset_type == "tiles":
            asset_info = self.get_tile_info(asset_id)
        elif asset_type == "ui":
            asset_info = self.get_ui_element_info(asset_id)
        
        # Se l'asset è trovato, restituisci il percorso completo
        if asset_info:
            return os.path.join(self.base_path, asset_info["path"])
        
        return None

# Registra la pulizia globale all'uscita
atexit.register(AssetManager.close_all) 