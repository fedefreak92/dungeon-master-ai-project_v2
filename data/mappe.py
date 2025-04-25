"""
Modulo per gestire le mappe del gioco.
Fornisce funzioni per caricare e manipolare i dati delle mappe.
"""

import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Percorso base per i dati delle mappe
MAPPE_DIR = Path(os.path.join(os.path.dirname(__file__), "mappe"))

def get_mappa(map_id):
    """
    Carica i dati di una mappa dal file corrispondente.
    
    Args:
        map_id (str): ID della mappa da caricare
        
    Returns:
        dict: Dati della mappa o dizionario vuoto se non trovata
    """
    try:
        # Assicurati che l'ID della mappa sia una stringa
        map_id = str(map_id)
        
        # Controlla se l'ID include già l'estensione .json
        if not map_id.endswith('.json'):
            map_id = f"{map_id}.json"
            
        # Percorso completo del file
        file_path = MAPPE_DIR / map_id
        
        # Verifica se il file esiste
        if not file_path.exists():
            logger.warning(f"File mappa non trovato: {file_path}")
            return {}
            
        # Carica il file JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        logger.debug(f"Mappa '{map_id}' caricata con successo")
        return data
        
    except Exception as e:
        logger.error(f"Errore nel caricamento della mappa '{map_id}': {str(e)}")
        return {}
        
def get_all_maps():
    """
    Ottiene la lista di tutte le mappe disponibili.
    
    Returns:
        list: Lista dei nomi dei file delle mappe (senza estensione)
    """
    try:
        if not MAPPE_DIR.exists():
            logger.warning(f"Directory mappe non trovata: {MAPPE_DIR}")
            return []
            
        # Trova tutti i file JSON nella directory delle mappe
        map_files = [f.stem for f in MAPPE_DIR.glob("*.json")]
        return map_files
        
    except Exception as e:
        logger.error(f"Errore nell'ottenere la lista delle mappe: {str(e)}")
        return []
        
def save_mappa(map_id, data):
    """
    Salva i dati di una mappa nel file corrispondente.
    
    Args:
        map_id (str): ID della mappa da salvare
        data (dict): Dati della mappa
        
    Returns:
        bool: True se il salvataggio è riuscito, False altrimenti
    """
    try:
        # Assicurati che l'ID della mappa sia una stringa
        map_id = str(map_id)
        
        # Controlla se l'ID include già l'estensione .json
        if not map_id.endswith('.json'):
            map_id = f"{map_id}.json"
            
        # Percorso completo del file
        file_path = MAPPE_DIR / map_id
        
        # Crea la directory se non esiste
        MAPPE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Salva i dati in formato JSON
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        logger.debug(f"Mappa '{map_id}' salvata con successo")
        return True
        
    except Exception as e:
        logger.error(f"Errore nel salvataggio della mappa '{map_id}': {str(e)}")
        return False 