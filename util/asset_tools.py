"""
Strumenti per la gestione degli asset del gioco.
Fornisce funzionalità per copiare e sincronizzare gli asset esterni nella directory interna del gioco.
"""

import os
import shutil
import json
import logging
from pathlib import Path

logger = logging.getLogger("gioco_rpg.assets")

def copy_assets(source_dir, dest_dir, overwrite=False):
    """
    Copia tutti gli asset dalla directory di origine alla directory di destinazione.
    
    Args:
        source_dir (str): Directory di origine degli asset
        dest_dir (str): Directory di destinazione
        overwrite (bool): Se sovrascrivere i file esistenti
        
    Returns:
        tuple: (numero di file copiati, elenco dei file copiati)
    """
    source_path = Path(source_dir)
    dest_path = Path(dest_dir)
    
    if not source_path.exists():
        logger.error(f"La directory di origine {source_dir} non esiste.")
        return 0, []
    
    # Assicurati che la directory di destinazione esista
    dest_path.mkdir(exist_ok=True, parents=True)
    
    copied_count = 0
    copied_files = []
    
    # Copia ricorsivamente tutti i file
    for src_file in source_path.glob("**/*"):
        if src_file.is_file():
            # Calcola il percorso di destinazione relativo
            rel_path = src_file.relative_to(source_path)
            dest_file = dest_path / rel_path
            
            # Assicurati che la directory di destinazione esista
            dest_file.parent.mkdir(exist_ok=True, parents=True)
            
            # Controlla se il file esiste già
            if not dest_file.exists() or overwrite:
                try:
                    shutil.copy2(src_file, dest_file)
                    copied_count += 1
                    copied_files.append(str(rel_path))
                    logger.info(f"Copiato asset: {rel_path}")
                except Exception as e:
                    logger.error(f"Errore nella copia di {src_file} in {dest_file}: {e}")
    
    logger.info(f"Copiati {copied_count} asset da {source_dir} a {dest_dir}")
    return copied_count, copied_files

def sync_assets(external_dir, game_dir, asset_types=None):
    """
    Sincronizza gli asset esterni con la directory di gioco.
    
    Args:
        external_dir (str): Directory esterna degli asset
        game_dir (str): Directory di gioco (interna)
        asset_types (list): Tipi di asset da sincronizzare, se None sincronizza tutti
        
    Returns:
        dict: Statistiche sulla sincronizzazione
    """
    external_path = Path(external_dir)
    game_path = Path(game_dir)
    
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
            copied, files = copy_assets(source_dir, dest_dir)
            stats["total_copied"] += copied
            stats["types"][asset_type] = {
                "copied": copied,
                "files": files
            }
    
    # Copia il manifest.json se esiste
    manifest_src = external_path / "manifest.json"
    if manifest_src.exists():
        try:
            # Carica i dati esistenti se presenti
            existing_data = {}
            manifest_dest = game_path / "manifest.json"
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
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento del manifest.json: {e}")
    
    return stats

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