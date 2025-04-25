"""
Utility per il caricamento e la gestione degli asset.
"""

import os
import logging
import sys
from util.asset_manager import cleanup_assets

# Aggiungi il percorso necessario per importare i moduli di util
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
    
from util.asset_manager import AssetManager, get_asset_manager
from util.asset_tools import sync_assets

# Configura il logger
logger = logging.getLogger(__name__)

def init_assets():
    """Inizializza gli asset del gioco."""
    # Path della directory corrente del server
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cleanup_assets()
    
    # Path degli asset esterni (nella directory principale) e interni (dentro gioco_rpg)
    external_assets = os.path.join(os.path.dirname(base_dir), "assets")
    internal_assets = os.path.join(base_dir, "assets")
    
    # Inizializza il gestore degli asset 
    asset_manager = get_asset_manager()
    
    # Se la directory degli asset esterni esiste
    if os.path.exists(external_assets):
        logger.info(f"Rilevata directory asset esterni: {external_assets}")
        logger.info(f"Sincronizzazione con directory interna: {internal_assets}")
        
        # Sincronizza gli asset
        stats = sync_assets(external_assets, internal_assets)
        
        logger.info(f"Sincronizzazione completata: {stats['total_copied']} file copiati")
        for asset_type, data in stats["types"].items():
            logger.info(f"  {asset_type}: {data['copied']} file")
        
        # Aggiorna il gestore degli asset
        asset_manager.update_all()
    else:
        logger.info(f"Directory asset esterni non trovata: {external_assets}")
        logger.info(f"Utilizzo solo gli asset interni: {internal_assets}")
    
    # Riporta un log con gli asset caricati
    logger.info(f"Asset manager configurato: {len(asset_manager.sprites)} sprites, "
               f"{len(asset_manager.tiles)} tiles, {len(asset_manager.animations)} animazioni, "
               f"{len(asset_manager.tilesets)} tilesets, {len(asset_manager.ui_elements)} elementi UI")
    
    return asset_manager 