#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script di diagnostica per verificare il caricamento dei dati JSON.
Utile per trovare rapidamente problemi con file e percorsi.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Aggiungi la directory principale al path
sys.path.append(str(Path(__file__).parent.parent))

# Configura logging con informazioni dettagliate
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

from util.data_manager import get_data_manager
from util.config import DATA_DIR, SAVE_DIR, MAPS_DIR

logger = logging.getLogger("diagnostica")

def main():
    """Funzione principale di diagnostica."""
    try:
        logger.info("Avvio diagnostica del sistema di dati JSON")
        
        # Verifica le directory principali
        logger.info(f"DATA_DIR: {DATA_DIR} (esiste: {DATA_DIR.exists()})")
        logger.info(f"SAVE_DIR: {SAVE_DIR} (esiste: {SAVE_DIR.exists()})")
        logger.info(f"MAPS_DIR: {MAPS_DIR} (esiste: {MAPS_DIR.exists()})")
        
        # Ottieni il data manager
        data_manager = get_data_manager()
        
        # Esegui diagnostica completa
        diagnostica = data_manager.diagnose_system_paths()
        
        # Visualizza il riepilogo
        riepilogo = diagnostica["_summary"]
        logger.info(f"Riepilogo diagnostica: {riepilogo['valid_paths']}/{riepilogo['total_paths']} percorsi validi, "
                   f"{riepilogo['json_files_found']} file JSON trovati, {riepilogo['errors_found']} errori rilevati")
        
        # Verifica ogni directory
        for data_type, info in diagnostica.items():
            if data_type == "_summary":
                continue
                
            logger.info(f"\nDiagnostica per {data_type}:")
            logger.info(f"  Percorso: {info['path']} (esiste: {info['exists']}, è directory: {info['is_dir']})")
            
            if info['exists'] and info['is_dir']:
                logger.info(f"  File JSON trovati: {', '.join(info['json_files']) if info['json_files'] else 'nessuno'}")
                
                if info['errors']:
                    logger.error(f"  Errori rilevati ({len(info['errors'])}):")
                    for errore in info['errors']:
                        logger.error(f"    - {errore}")
            
        # Verifica classi
        logger.info("\nVerifica delle classi di personaggio:")
        try:
            classi = data_manager.get_classes()
            if classi:
                logger.info(f"  Classi trovate ({len(classi)}): {', '.join(classi.keys())}")
            else:
                logger.error("  Nessuna classe trovata!")
        except Exception as e:
            logger.error(f"  Errore nel caricamento delle classi: {e}")
        
        logger.info("\nDiagnostica completata.")
        
    except Exception as e:
        logger.error(f"Errore durante la diagnostica: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main()) 