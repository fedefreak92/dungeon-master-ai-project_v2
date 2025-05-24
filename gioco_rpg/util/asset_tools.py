"""
Strumenti per la gestione degli asset del gioco.
Fornisce funzionalità per copiare e sincronizzare gli asset esterni nella directory interna del gioco.
"""

import os
import shutil
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union, Any

logger = logging.getLogger("gioco_rpg.assets")

def copy_assets(source_dir: str, dest_dir: str, overwrite: bool = False, 
               file_types: Optional[List[str]] = None) -> Tuple[int, List[str]]:
    """
    Copia tutti gli asset dalla directory di origine alla directory di destinazione.
    
    Args:
        source_dir (str): Directory di origine degli asset
        dest_dir (str): Directory di destinazione
        overwrite (bool): Se sovrascrivere i file esistenti
        file_types (list, optional): Lista di estensioni di file da copiare (es. ['.png', '.jpg'])
        
    Returns:
        tuple: (numero di file copiati, elenco dei file copiati)
    """
    source_path = Path(source_dir)
    dest_path = Path(dest_dir)
    
    if not source_path.exists():
        raise FileNotFoundError(f"La directory di origine {source_dir} non esiste.")
    
    # Assicurati che la directory di destinazione esista
    dest_path.mkdir(exist_ok=True, parents=True)
    
    copied_count = 0
    copied_files = []
    
    # Se sono specificati i tipi di file, normalizza le estensioni
    if file_types:
        file_types = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in file_types]
    
    # Copia ricorsivamente tutti i file
    for src_file in source_path.glob("**/*"):
        if src_file.is_file():
            # Se sono specificati i tipi di file, filtra in base all'estensione
            if file_types and src_file.suffix.lower() not in file_types:
                continue
                
            # Calcola il percorso di destinazione relativo
            rel_path = src_file.relative_to(source_path)
            dest_file = dest_path / rel_path
            
            # Assicurati che la directory di destinazione esista
            dest_file.parent.mkdir(exist_ok=True, parents=True)
            
            # Controlla se il file esiste già
            if not dest_file.exists() or overwrite:
                # Calcola hash solo se il file esiste e non vogliamo sovrascrivere sempre
                if dest_file.exists() and not overwrite:
                    # Verifica se il file è cambiato usando hash MD5
                    src_hash = calculate_file_hash(src_file)
                    dest_hash = calculate_file_hash(dest_file)
                    if src_hash == dest_hash:
                        logger.debug(f"File identico, skip: {rel_path}")
                        continue
                
                # Copia il file
                shutil.copy2(src_file, dest_file)
                copied_count += 1
                copied_files.append(str(rel_path))
                logger.info(f"Copiato asset: {rel_path}")
    
    logger.info(f"Copiati {copied_count} asset da {source_dir} a {dest_dir}")
    return copied_count, copied_files

def calculate_file_hash(file_path: Union[str, Path]) -> str:
    """
    Calcola l'hash MD5 di un file.
    
    Args:
        file_path (str or Path): Percorso del file
        
    Returns:
        str: Hash MD5 del file
    """
    with open(file_path, 'rb') as f:
        file_hash = hashlib.md5()
        # Leggi il file a blocchi per gestire file di grandi dimensioni
        for chunk in iter(lambda: f.read(4096), b''):
            file_hash.update(chunk)
    return file_hash.hexdigest()

def sync_assets(external_dir: str, game_dir: str, asset_types: Optional[List[str]] = None,
               overwrite: bool = False) -> Dict[str, Any]:
    """
    Sincronizza gli asset esterni con la directory di gioco.
    
    Args:
        external_dir (str): Directory esterna degli asset
        game_dir (str): Directory di gioco (interna)
        asset_types (list): Tipi di asset da sincronizzare, se None sincronizza tutti
        overwrite (bool): Se sovrascrivere i file esistenti
        
    Returns:
        dict: Statistiche sulla sincronizzazione
    """
    external_path = Path(external_dir)
    game_path = Path(game_dir)
    
    if not external_path.exists():
        raise FileNotFoundError(f"La directory esterna {external_dir} non esiste.")
    
    stats = {
        "total_copied": 0,
        "types": {}
    }
    
    # Tipi di asset da sincronizzare
    if asset_types is None:
        asset_types = ["sprites", "tiles", "animations", "tilesets", "ui"]
    
    # Per ogni tipo di asset
    for asset_type in asset_types:
        source_dir = external_path / asset_type
        dest_dir = game_path / asset_type
        
        # Se la directory esiste, copia gli asset
        if source_dir.exists():
            copied, files = copy_assets(source_dir, dest_dir, overwrite)
            stats["total_copied"] += copied
            stats["types"][asset_type] = {
                "copied": copied,
                "files": files
            }
    
    # Sincronizza il manifest
    sync_manifest(external_path, game_path)
    
    return stats

def sync_manifest(external_path: Path, game_path: Path) -> bool:
    """
    Sincronizza il file manifest.json tra due directory.
    
    Args:
        external_path (Path): Percorso esterno contenente il manifest
        game_path (Path): Percorso di gioco dove sincronizzare il manifest
        
    Returns:
        bool: True se l'operazione è riuscita, False altrimenti
    """
    # Verifica che il manifest esterno esista
    manifest_src = external_path / "manifest.json"
    if not manifest_src.exists():
        logger.warning(f"Manifest non trovato in {manifest_src}")
        return False

    # Prepara il percorso di destinazione
    manifest_dest = game_path / "manifest.json"
    
    # Carica i dati esistenti se presenti
    existing_data = {}
    if manifest_dest.exists():
        with open(manifest_dest, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    
    # Carica i nuovi dati
    with open(manifest_src, 'r', encoding='utf-8') as f:
        new_data = json.load(f)
    
    # Unisci i dati
    for key, value in new_data.items():
        if key in existing_data and isinstance(value, dict) and isinstance(existing_data[key], dict):
            existing_data[key].update(value)
        else:
            existing_data[key] = value
    
    # Salva il manifest unito
    with open(manifest_dest, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2)
    
    logger.info("Manifest.json aggiornato con nuovi asset")
    return True

def verify_asset_integrity(base_dir: str, asset_type: str = None) -> Dict[str, Any]:
    """
    Verifica l'integrità degli asset controllando che i file esistano.
    
    Args:
        base_dir (str): Directory di base degli asset
        asset_type (str, optional): Tipo di asset da verificare, se None verifica tutti
        
    Returns:
        dict: Statistiche sulla verifica
    """
    base_path = Path(base_dir)
    
    if not base_path.exists():
        raise FileNotFoundError(f"La directory degli asset {base_dir} non esiste.")
    
    # Carica il manifest per ottenere l'elenco degli asset
    manifest_path = base_path / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest non trovato in {manifest_path}")
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    # Tipi di asset da verificare
    asset_types = ["sprites", "tiles", "animations", "tilesets", "ui_elements"]
    if asset_type and asset_type in asset_types:
        asset_types = [asset_type]
    
    results = {
        "status": "success",
        "total_assets": 0,
        "missing_assets": 0,
        "asset_types": {}
    }
    
    # Verifica ogni tipo di asset
    for tipo in asset_types:
        assets = manifest.get(tipo, {})
        missing = []
        
        for asset_id, asset_data in assets.items():
            results["total_assets"] += 1
            
            # Ottieni il percorso del file
            file_path = None
            if "file" in asset_data:
                file_path = base_path / asset_data["file"]
            elif "path" in asset_data:
                file_path = base_path / asset_data["path"]
            
            # Verifica che il file esista
            if file_path and not file_path.exists():
                missing.append({
                    "id": asset_id,
                    "file": str(file_path.relative_to(base_path))
                })
                results["missing_assets"] += 1
        
        # Aggiungi i risultati per questo tipo
        results["asset_types"][tipo] = {
            "total": len(assets),
            "missing": len(missing),
            "missing_assets": missing
        }
    
    return results

def optimize_image_asset(file_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None,
                       quality: int = 85, max_size: Optional[int] = None) -> bool:
    """
    Ottimizza un'immagine riducendone la dimensione.
    
    Args:
        file_path (str or Path): Percorso del file immagine
        output_path (str or Path, optional): Percorso output (se None sovrascrive l'originale)
        quality (int): Qualità dell'immagine (0-100)
        max_size (int, optional): Dimensione massima del lato più lungo
        
    Returns:
        bool: True se l'ottimizzazione è riuscita, False altrimenti
    """
    # Importa PIL
    from PIL import Image
    
    # Converti i percorsi in Path
    file_path = Path(file_path)
    if not output_path:
        output_path = file_path
    else:
        output_path = Path(output_path)
    
    # Verifica che il file esista
    if not file_path.exists():
        raise FileNotFoundError(f"File immagine non trovato: {file_path}")
    
    # Apri l'immagine
    img = Image.open(file_path)
    
    # Ridimensiona se necessario
    if max_size and (img.width > max_size or img.height > max_size):
        # Mantiene le proporzioni
        if img.width >= img.height:
            new_width = max_size
            new_height = int(img.height * (max_size / img.width))
        else:
            new_height = max_size
            new_width = int(img.width * (max_size / img.height))
        
        img = img.resize((new_width, new_height), Image.LANCZOS)
    
    # Salva con ottimizzazione
    if file_path.suffix.lower() in ['.jpg', '.jpeg']:
        img.save(output_path, 'JPEG', quality=quality, optimize=True)
    elif file_path.suffix.lower() == '.png':
        img.save(output_path, 'PNG', optimize=True)
    else:
        # Per altri formati, salva nel formato originale
        img.save(output_path, quality=quality, optimize=True)
    
    logger.info(f"Immagine ottimizzata: {file_path}")
    return True

if __name__ == "__main__":
    # Configurazione del logger
    logging.basicConfig(level=logging.INFO)
    
    # Directory di esempio
    external_dir = "../assets"
    game_dir = "assets"
    
    # Sincronizza gli asset
    stats = sync_assets(external_dir, game_dir)
    
    print(f"Sincronizzazione completata: {stats['total_copied']} file copiati")
    for asset_type, data in stats["types"].items():
        print(f"  {asset_type}: {data['copied']} file") 