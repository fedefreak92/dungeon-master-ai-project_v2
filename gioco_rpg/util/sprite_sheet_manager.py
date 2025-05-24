"""
Sprite Sheet Manager
Gestisce il caricamento e l'utilizzo di sprite sheet per ottimizzare le richieste HTTP e la performance.
"""

import os
import json
import logging
from pathlib import Path
import weakref
from typing import Dict, List, Optional, Tuple, Union, Any
from functools import lru_cache

logger = logging.getLogger(__name__)

class SpriteSheetManager:
    """
    Gestisce il caricamento e l'utilizzo di sprite sheet.
    Un sprite sheet è un'unica immagine contenente più sprite, riducendo le richieste HTTP.
    """
    
    def __init__(self, base_path=None):
        """
        Inizializza il gestore di sprite sheet.
        
        Args:
            base_path (str, optional): Il percorso base per gli sprite sheet.
        """
        # Percorso base per gli sprite sheet
        self.base_path = base_path if base_path else os.path.join(os.getcwd(), "assets", "spritesheets")
        
        # Normalizza il percorso per evitare problemi su Windows
        self.base_path = os.path.normpath(self.base_path)
        
        # Verifica se la directory esiste e creala se necessario
        if not os.path.exists(self.base_path):
            try:
                os.makedirs(self.base_path)
                logger.info(f"Creata directory degli sprite sheet: {self.base_path}")
            except Exception as e:
                logger.error(f"Errore nella creazione della directory degli sprite sheet {self.base_path}: {e}")
        
        # Dizionario degli sprite sheet caricati
        self.sprite_sheets = {}
        
        # Dizionario per la mappatura degli sprite singoli ai loro sprite sheet
        self.sprite_to_sheet = {}
        
        # Cache per sprite sheet (utilizza riferimenti deboli per consentire il garbage collection)
        self._sprite_sheet_cache = weakref.WeakValueDictionary()
        
        # Carica tutti gli sprite sheet esistenti
        self.load_all_sprite_sheets()
        
        logger.info(f"SpriteSheetManager inizializzato con percorso {self.base_path}")
    
    def load_all_sprite_sheets(self):
        """
        Carica tutti gli sprite sheet disponibili nella directory base.
        """
        try:
            # Contatori per logging
            total_sheets = 0
            total_sprites = 0
            
            # Trova tutti i file di metadati JSON degli sprite sheet
            for file_path in Path(self.base_path).glob("**/*.json"):
                if self.load_sprite_sheet_metadata(file_path):
                    total_sheets += 1
                    
            # Conta il numero totale di sprite mappati
            total_sprites = len(self.sprite_to_sheet)
                
            logger.info(f"Caricati {total_sheets} sprite sheet con {total_sprites} sprite mappati")
        except Exception as e:
            logger.error(f"Errore nel caricamento degli sprite sheet: {e}")
            raise
    
    def load_sprite_sheet_metadata(self, metadata_path):
        """
        Carica i metadati di uno sprite sheet.
        
        Args:
            metadata_path (str): Percorso al file dei metadati JSON.
            
        Returns:
            bool: True se il caricamento è riuscito, False altrimenti.
        """
        try:
            # Carica i metadati JSON
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            # Ottieni l'ID dello sprite sheet
            sheet_id = metadata.get("id")
            if not sheet_id:
                logger.warning(f"Sprite sheet senza ID: {metadata_path}")
                return False
            
            # Verifica che il file dell'immagine esista
            image_path = metadata.get("image")
            if not image_path:
                logger.warning(f"Sprite sheet senza immagine: {metadata_path}")
                return False
            
            # Normalizza il percorso dell'immagine
            if not os.path.isabs(image_path):
                image_path = os.path.join(os.path.dirname(metadata_path), image_path)
            
            # Verifica che il file esista
            if not os.path.exists(image_path):
                logger.warning(f"Immagine dello sprite sheet non trovata: {image_path}")
                return False
            
            # Registra lo sprite sheet
            self.sprite_sheets[sheet_id] = {
                "id": sheet_id,
                "image": image_path,
                "frames": metadata.get("frames", {}),
                "animations": metadata.get("animations", {}),
                "meta": metadata.get("meta", {})
            }
            
            # Aggiorna la mappatura degli sprite
            frames = metadata.get("frames", {})
            for frame_id, frame_data in frames.items():
                self.sprite_to_sheet[frame_id] = {
                    "sheet_id": sheet_id,
                    "frame": frame_data
                }
            
            logger.info(f"Sprite sheet caricato: {sheet_id} con {len(frames)} frame")
            return True
        
        except Exception as e:
            logger.error(f"Errore nel caricamento dei metadati dello sprite sheet {metadata_path}: {e}")
            return False
    
    @lru_cache(maxsize=128)
    def get_sprite_info(self, sprite_id):
        """
        Ottiene le informazioni su uno sprite specifico.
        Utilizza caching LRU per migliorare le prestazioni sugli sprite più utilizzati.
        
        Args:
            sprite_id (str): L'ID dello sprite.
            
        Returns:
            dict: Le informazioni sullo sprite o None se non trovato.
        """
        return self.sprite_to_sheet.get(sprite_id)
    
    def get_sprite_sheet_info(self, sheet_id):
        """
        Ottiene le informazioni su uno sprite sheet specifico.
        
        Args:
            sheet_id (str): L'ID dello sprite sheet.
            
        Returns:
            dict: Le informazioni sullo sprite sheet o None se non trovato.
        """
        return self.sprite_sheets.get(sheet_id)
    
    def get_or_load_sprite_sheet(self, sheet_id):
        """
        Ottiene uno sprite sheet dalla cache o lo carica se non è presente.
        
        Args:
            sheet_id (str): ID dello sprite sheet.
            
        Returns:
            dict: Informazioni sullo sprite sheet o None se non trovato.
        """
        # Verifica se è già nella cache
        if sheet_id in self._sprite_sheet_cache:
            return self._sprite_sheet_cache[sheet_id]
        
        # Carica le informazioni dello sprite sheet
        sheet_info = self.get_sprite_sheet_info(sheet_id)
        if sheet_info:
            # Memorizza nella cache
            self._sprite_sheet_cache[sheet_id] = sheet_info
            return sheet_info
        
        return None
    
    def create_sprite_sheet(self, sheet_id, sprites, output_path=None, size=(2048, 2048)):
        """
        Crea un nuovo sprite sheet combinando più sprite.
        
        Args:
            sheet_id (str): ID del nuovo sprite sheet.
            sprites (list): Lista di percorsi agli sprite da combinare.
            output_path (str, optional): Percorso di output per l'immagine e i metadati.
            size (tuple, optional): Dimensioni dello sprite sheet (larghezza, altezza).
            
        Returns:
            bool: True se la creazione è riuscita, False altrimenti.
        """
        try:
            # Se non è specificato un percorso di output, usa la directory base
            if not output_path:
                output_path = os.path.join(self.base_path, f"{sheet_id}")
            
            # Normalizza il percorso
            output_path = os.path.normpath(output_path)
            
            # Verifica che la directory esista e creala se necessario
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Ottieni i percorsi completi per l'immagine e i metadati
            image_path = f"{output_path}.png"
            json_path = f"{output_path}.json"
            
            # Importa Pillow per la manipolazione delle immagini
            try:
                from PIL import Image
            except ImportError:
                logger.error("Pillow non installato. Impossibile creare sprite sheet.")
                return False
            
            # Crea una nuova immagine vuota
            sheet_image = Image.new("RGBA", size, (0, 0, 0, 0))
            
            # Prepara i metadati
            metadata = {
                "id": sheet_id,
                "image": os.path.basename(image_path),
                "frames": {},
                "meta": {
                    "size": {"w": size[0], "h": size[1]},
                    "scale": 1
                }
            }
            
            # Posiziona gli sprite sull'immagine utilizzando algoritmo di packing
            return self._pack_sprites_in_sheet(sprites, sheet_image, metadata, image_path, json_path)
        
        except Exception as e:
            logger.error(f"Errore nella creazione dello sprite sheet {sheet_id}: {e}")
            return False
    
    def _pack_sprites_in_sheet(self, sprites, sheet_image, metadata, image_path, json_path):
        """
        Posiziona gli sprite su uno sheet utilizzando un algoritmo di packing semplice.
        
        Args:
            sprites (list): Lista di percorsi agli sprite.
            sheet_image (PIL.Image): Immagine dello sheet.
            metadata (dict): Metadati dello sheet.
            image_path (str): Percorso output immagine.
            json_path (str): Percorso output JSON.
            
        Returns:
            bool: True se l'operazione è riuscita, False altrimenti.
        """
        try:
            from PIL import Image
            
            # Larghezza e altezza totali dello sheet
            sheet_width, sheet_height = sheet_image.size
            
            # Posiziona gli sprite sull'immagine
            x, y = 0, 0
            max_height = 0
            
            for sprite_path in sprites:
                try:
                    # Apri l'immagine dello sprite
                    sprite_image = Image.open(sprite_path)
                    sprite_width, sprite_height = sprite_image.size
                    
                    # Se l'immagine è troppo grande per la riga corrente, vai alla riga successiva
                    if x + sprite_width > sheet_width:
                        x = 0
                        y += max_height
                        max_height = 0
                    
                    # Se l'immagine è troppo grande per lo sheet, salta
                    if y + sprite_height > sheet_height:
                        logger.warning(f"Sprite {sprite_path} troppo grande per lo sheet, saltato.")
                        continue
                    
                    # Incolla lo sprite nello sheet
                    sheet_image.paste(sprite_image, (x, y))
                    
                    # Aggiorna l'altezza massima per questa riga
                    max_height = max(max_height, sprite_height)
                    
                    # Aggiungi le informazioni dello sprite ai metadati
                    sprite_name = os.path.splitext(os.path.basename(sprite_path))[0]
                    frame_id = f"{sprite_name}"
                    
                    metadata["frames"][frame_id] = {
                        "frame": {"x": x, "y": y, "w": sprite_width, "h": sprite_height},
                        "spriteSourceSize": {"x": 0, "y": 0, "w": sprite_width, "h": sprite_height},
                        "sourceSize": {"w": sprite_width, "h": sprite_height},
                        "rotated": False,
                        "trimmed": False
                    }
                    
                    # Aggiorna la posizione per il prossimo sprite
                    x += sprite_width
                    
                except Exception as e:
                    logger.error(f"Errore nell'aggiunta dello sprite {sprite_path}: {e}")
                    continue
            
            # Salva l'immagine dello sprite sheet
            sheet_image.save(image_path, optimize=True)
            
            # Salva i metadati in formato JSON
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
            
            # Aggiorna il dizionario degli sprite sheet
            sheet_id = metadata["id"]
            self.sprite_sheets[sheet_id] = {
                "id": sheet_id,
                "image": image_path,
                "frames": metadata["frames"],
                "animations": metadata.get("animations", {}),
                "meta": metadata.get("meta", {})
            }
            
            # Aggiorna la mappatura degli sprite
            for frame_id, frame_data in metadata["frames"].items():
                self.sprite_to_sheet[frame_id] = {
                    "sheet_id": sheet_id,
                    "frame": frame_data
                }
            
            # Pulisci la cache lru
            self.get_sprite_info.cache_clear()
            
            logger.info(f"Sprite sheet creato con successo: {sheet_id} ({len(metadata['frames'])} sprites)")
            return True
        
        except Exception as e:
            logger.error(f"Errore nel packing degli sprite: {e}")
            return False
            
    def generate_sprite_sheet_from_directory(self, directory, sheet_id=None, recursive=False):
        """
        Genera uno sprite sheet da tutti gli sprite in una directory.
        
        Args:
            directory (str): Directory contenente gli sprite.
            sheet_id (str, optional): ID dello sprite sheet. Se non specificato, usa il nome della directory.
            recursive (bool, optional): Se True, cerca anche nelle sottodirectory.
            
        Returns:
            bool: True se la generazione è riuscita, False altrimenti.
        """
        try:
            # Normalizza il percorso
            directory = os.path.normpath(directory)
            
            # Se non è specificato un ID, usa il nome della directory
            if not sheet_id:
                sheet_id = os.path.basename(directory)
            
            # Trova tutti i file immagine
            sprite_paths = []
            
            if recursive:
                for root, _, files in os.walk(directory):
                    for file in files:
                        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                            sprite_paths.append(os.path.join(root, file))
            else:
                for file in os.listdir(directory):
                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        sprite_paths.append(os.path.join(directory, file))
            
            # Se non ci sono sprite, restituisci False
            if not sprite_paths:
                logger.warning(f"Nessuno sprite trovato nella directory {directory}")
                return False
            
            # Calcola dimensioni ottimali per lo sprite sheet
            size = self._calculate_optimal_sheet_size(sprite_paths)
            
            # Prepara il percorso di output
            output_path = os.path.join(self.base_path, sheet_id)
            
            # Crea lo sprite sheet
            return self.create_sprite_sheet(sheet_id, sprite_paths, output_path, size)
        
        except Exception as e:
            logger.error(f"Errore nella generazione dello sprite sheet dalla directory {directory}: {e}")
            return False
    
    def _calculate_optimal_sheet_size(self, sprite_paths, max_size=4096):
        """
        Calcola le dimensioni ottimali per uno sprite sheet in base agli sprite da inserire.
        
        Args:
            sprite_paths (list): Lista di percorsi agli sprite.
            max_size (int): Dimensione massima consentita per lo sprite sheet.
            
        Returns:
            tuple: Dimensioni (larghezza, altezza) ottimali.
        """
        from PIL import Image
        
        # Calcola l'area totale necessaria
        total_area = 0
        max_width = 0
        max_height = 0
        
        for path in sprite_paths:
            try:
                img = Image.open(path)
                w, h = img.size
                total_area += w * h
                max_width = max(max_width, w)
                max_height = max(max_height, h)
            except Exception as e:
                logger.error(f"Errore nell'apertura dello sprite {path}: {e}")
        
        # Aggiungi un margine del 10% per evitare di riempire troppo lo sheet
        total_area *= 1.1
        
        # Calcola il lato di un quadrato che potrebbe contenere tutti gli sprite
        side = int(total_area ** 0.5)
        
        # Arrotonda al multiplo di 128 superiore per ottimizzare la texture
        side = ((side + 127) // 128) * 128
        
        # Limita le dimensioni massime
        side = min(side, max_size)
        
        # Assicurati che possa contenere almeno lo sprite più grande
        side = max(side, max(max_width, max_height))
        
        return (side, side)
            
    def get_sprite_data_url(self, sprite_id):
        """
        Restituisce i dati per l'URL dello sprite, che può essere un'immagine singola
        o un riferimento a uno sprite all'interno di uno sprite sheet.
        
        Args:
            sprite_id (str): ID dello sprite.
            
        Returns:
            dict: Dati per l'URL, o None se non trovato.
        """
        # Verifica se lo sprite è mappato a uno sprite sheet
        sprite_info = self.get_sprite_info(sprite_id)
        if sprite_info:
            # Lo sprite è in uno sprite sheet
            sheet_id = sprite_info["sheet_id"]
            sheet_info = self.get_or_load_sprite_sheet(sheet_id)
            
            if sheet_info:
                return {
                    "type": "spritesheet",
                    "sheet_url": sheet_info["image"],
                    "frame": sprite_info["frame"]["frame"]
                }
        
        # Sprite non trovato
        logger.warning(f"Sprite non trovato: {sprite_id}")
        return None
    
    def clear_cache(self):
        """
        Pulisce la cache degli sprite sheet.
        """
        self._sprite_sheet_cache.clear()
        self.get_sprite_info.cache_clear()
        logger.debug("Cache degli sprite sheet pulita")

# Singleton globale
_sprite_sheet_manager = None

def get_sprite_sheet_manager(base_path=None):
    """
    Restituisce l'istanza singleton del SpriteSheetManager.
    
    Args:
        base_path (str, optional): Il percorso base per gli sprite sheet.
        
    Returns:
        SpriteSheetManager: L'istanza del SpriteSheetManager.
    """
    global _sprite_sheet_manager
    if _sprite_sheet_manager is None:
        _sprite_sheet_manager = SpriteSheetManager(base_path)
    return _sprite_sheet_manager 