"""
Sprite Sheet Manager
Gestisce il caricamento e l'utilizzo di sprite sheet per ottimizzare le richieste HTTP e la performance.
"""

import os
import json
import logging
from pathlib import Path
import msgpack

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
        
        # Carica tutti gli sprite sheet esistenti
        self.load_all_sprite_sheets()
        
        logger.info(f"SpriteSheetManager inizializzato con percorso {self.base_path}")
    
    def load_all_sprite_sheets(self):
        """
        Carica tutti gli sprite sheet disponibili nella directory base.
        """
        try:
            # Trova tutti i file di metadati JSON/MSGPACK degli sprite sheet
            for file_path in Path(self.base_path).glob("**/*.json"):
                self.load_sprite_sheet_metadata(file_path)
                
            for file_path in Path(self.base_path).glob("**/*.msgpack"):
                self.load_sprite_sheet_metadata(file_path, is_msgpack=True)
                
            logger.info(f"Caricati {len(self.sprite_sheets)} sprite sheet con {len(self.sprite_to_sheet)} sprite mappati")
        except Exception as e:
            logger.error(f"Errore nel caricamento degli sprite sheet: {e}")
    
    def load_sprite_sheet_metadata(self, metadata_path, is_msgpack=False):
        """
        Carica i metadati di uno sprite sheet.
        
        Args:
            metadata_path (str): Percorso al file dei metadati.
            is_msgpack (bool): True se il file è in formato MessagePack, False se JSON.
            
        Returns:
            bool: True se il caricamento è riuscito, False altrimenti.
        """
        try:
            # Carica i metadati
            if is_msgpack:
                with open(metadata_path, "rb") as f:
                    metadata = msgpack.unpackb(f.read(), raw=False)
            else:
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
    
    def get_sprite_info(self, sprite_id):
        """
        Ottiene le informazioni su uno sprite specifico.
        
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
            msgpack_path = f"{output_path}.msgpack"
            
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
            
            # Posiziona gli sprite sull'immagine
            x, y = 0, 0
            max_height = 0
            
            for i, sprite_path in enumerate(sprites):
                try:
                    # Apri l'immagine dello sprite
                    sprite_image = Image.open(sprite_path)
                    sprite_width, sprite_height = sprite_image.size
                    
                    # Se l'immagine è troppo grande per la riga corrente, vai alla riga successiva
                    if x + sprite_width > size[0]:
                        x = 0
                        y += max_height
                        max_height = 0
                    
                    # Se l'immagine è troppo grande per lo sheet, salta
                    if y + sprite_height > size[1]:
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
            sheet_image.save(image_path)
            
            # Salva i metadati in formato JSON
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
            
            # Salva i metadati in formato MessagePack
            with open(msgpack_path, "wb") as f:
                f.write(msgpack.packb(metadata, use_bin_type=True))
            
            # Aggiorna il dizionario degli sprite sheet
            self.sprite_sheets[sheet_id] = metadata
            
            # Aggiorna la mappatura degli sprite
            for frame_id, frame_data in metadata["frames"].items():
                self.sprite_to_sheet[frame_id] = {
                    "sheet_id": sheet_id,
                    "frame": frame_data
                }
            
            logger.info(f"Sprite sheet creato con successo: {sheet_id} ({len(metadata['frames'])} sprites)")
            return True
        
        except Exception as e:
            logger.error(f"Errore nella creazione dello sprite sheet {sheet_id}: {e}")
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
            
            # Prepara il percorso di output
            output_path = os.path.join(self.base_path, sheet_id)
            
            # Crea lo sprite sheet
            return self.create_sprite_sheet(sheet_id, sprite_paths, output_path)
        
        except Exception as e:
            logger.error(f"Errore nella generazione dello sprite sheet dalla directory {directory}: {e}")
            return False
            
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
            sheet_info = self.get_sprite_sheet_info(sheet_id)
            
            if sheet_info:
                return {
                    "type": "spritesheet",
                    "sheet_url": sheet_info["image"],
                    "frame": sprite_info["frame"]["frame"]
                }
        
        # Altrimenti, potrebbe essere uno sprite singolo
        # Questo dipende dall'implementazione specifica
        return None

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