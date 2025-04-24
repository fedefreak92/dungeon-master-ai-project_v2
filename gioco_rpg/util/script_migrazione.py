#!/usr/bin/env python
"""
Script di migrazione per correggere i file di configurazione.
Questo script risolve i problemi identificati nei file JSON di dati e configurazione.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
import shutil

# Aggiungi la directory radice al percorso di importazione
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from util.validators import (
    valida_mappa, valida_npc, valida_oggetto,
    correggi_mappe_oggetti, correggi_mappe_npg
)
from util.logging_config import configurazione_logging
from util.safe_loader import SafeLoader

def backup_file(file_path):
    """
    Crea un backup del file specificato.
    
    Args:
        file_path (str or Path): Percorso del file da salvare
    
    Returns:
        Path: Percorso del file di backup
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return None
    
    # Crea una directory di backup se non esiste
    backup_dir = Path("backup")
    backup_dir.mkdir(exist_ok=True)
    
    # Nome del file di backup con timestamp
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    backup_file = backup_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"
    
    # Copia il file
    shutil.copy2(file_path, backup_file)
    logging.info(f"Creato backup del file {file_path} in {backup_file}")
    
    return backup_file

def carica_mappa(file_path):
    """
    Carica una mappa da un file JSON.
    
    Args:
        file_path (str or Path): Percorso del file JSON
    
    Returns:
        dict: Dati della mappa o None in caso di errore
    """
    try:
        return SafeLoader.safe_json_load(file_path)
    except Exception as e:
        logging.error(f"Errore durante il caricamento della mappa da {file_path}: {e}")
        return None

def salva_mappa(file_path, mappa_data):
    """
    Salva una mappa su un file JSON.
    
    Args:
        file_path (str or Path): Percorso del file JSON
        mappa_data (dict): Dati della mappa
    
    Returns:
        bool: True se il salvataggio è riuscito, False altrimenti
    """
    try:
        # Crea una copia di backup prima di sovrascrivere
        backup_file(file_path)
        
        # Salva il file
        return SafeLoader.safe_json_save(file_path, mappa_data)
    except Exception as e:
        logging.error(f"Errore durante il salvataggio della mappa in {file_path}: {e}")
        return False

def correggi_file_mappe():
    """
    Corregge tutti i file di mappa.
    
    Returns:
        int: Numero di file corretti
    """
    directory_mappe = Path("data/mappe")
    if not directory_mappe.exists():
        logging.error(f"Directory mappe non trovata: {directory_mappe}")
        return 0
    
    contatore = 0
    dati_mappe = {}  # Per memorizzare i dati delle mappe per correggi_mappe_oggetti
    
    # Processa ogni file mappa
    for file_path in directory_mappe.glob("*.json"):
        logging.info(f"Elaborazione mappa: {file_path}")
        
        # Carica i dati della mappa
        mappa_data = carica_mappa(file_path)
        if not mappa_data:
            continue
        
        # Valida e correggi i dati della mappa
        mappa_corretta = valida_mappa(mappa_data)
        
        # Salva i dati corretti
        if salva_mappa(file_path, mappa_corretta):
            logging.info(f"Mappa corretta e salvata: {file_path}")
            contatore += 1
        
        # Memorizza i dati della mappa per uso futuro
        nome_mappa = mappa_corretta.get("nome", file_path.stem)
        dati_mappe[nome_mappa] = mappa_corretta
    
    return contatore, dati_mappe

def correggi_file_npc(dati_mappe=None):
    """
    Corregge i file di configurazione degli NPC.
    
    Args:
        dati_mappe (dict, optional): Dati delle mappe per la correzione delle posizioni
    
    Returns:
        int: Numero di file corretti
    """
    directory_npc = Path("data/npc")
    if not directory_npc.exists():
        logging.error(f"Directory NPC non trovata: {directory_npc}")
        return 0
    
    contatore = 0
    
    # Correggi npcs.json
    npcs_file = directory_npc / "npcs.json"
    if npcs_file.exists():
        logging.info(f"Elaborazione file NPC: {npcs_file}")
        
        # Carica i dati NPC
        npcs_data = SafeLoader.safe_json_load(npcs_file)
        if npcs_data:
            # Correggi ogni NPC
            npcs_corretti = {}
            for nome, npc in npcs_data.items():
                npcs_corretti[nome] = valida_npc(npc, nome)
            
            # Salva i dati corretti
            if SafeLoader.safe_json_save(npcs_file, npcs_corretti):
                logging.info(f"File NPC corretto e salvato: {npcs_file}")
                contatore += 1
    
    # Correggi mappe_npg.json
    mappe_npg_file = directory_npc / "mappe_npg.json"
    if mappe_npg_file.exists():
        logging.info(f"Elaborazione file mappa NPC: {mappe_npg_file}")
        
        # Carica i dati mappa NPC
        mappe_npg_data = SafeLoader.safe_json_load(mappe_npg_file)
        
        if mappe_npg_data and dati_mappe:
            # Correggi posizioni NPC
            mappe_npg_corrette = correggi_mappe_npg(mappe_npg_data, dati_mappe)
            
            # Salva i dati corretti
            if SafeLoader.safe_json_save(mappe_npg_file, mappe_npg_corrette):
                logging.info(f"File mappa NPC corretto e salvato: {mappe_npg_file}")
                contatore += 1
        elif mappe_npg_data and not dati_mappe:
            logging.warning("Nessun dato mappa disponibile, impossibile correggere le posizioni degli NPC")
            # Backup del file senza correzioni
            backup_file(mappe_npg_file)
    
    return contatore

def correggi_file_oggetti(dati_mappe=None):
    """
    Corregge i file di configurazione degli oggetti.
    
    Args:
        dati_mappe (dict, optional): Dati delle mappe per la correzione delle posizioni
    
    Returns:
        int: Numero di file corretti
    """
    directory_oggetti = Path("data/items")
    if not directory_oggetti.exists():
        logging.error(f"Directory oggetti non trovata: {directory_oggetti}")
        return 0
    
    contatore = 0
    
    # Correggi oggetti_interattivi.json
    oggetti_file = directory_oggetti / "oggetti_interattivi.json"
    if oggetti_file.exists():
        logging.info(f"Elaborazione file oggetti: {oggetti_file}")
        
        # Carica i dati oggetti
        oggetti_data = SafeLoader.safe_json_load(oggetti_file)
        if oggetti_data:
            # Correggi ogni oggetto
            oggetti_corretti = []
            for oggetto in oggetti_data:
                oggetti_corretti.append(valida_oggetto(oggetto))
            
            # Salva i dati corretti
            if SafeLoader.safe_json_save(oggetti_file, oggetti_corretti):
                logging.info(f"File oggetti corretto e salvato: {oggetti_file}")
                contatore += 1
    
    # Correggi mappe_oggetti.json
    mappe_oggetti_file = directory_oggetti / "mappe_oggetti.json"
    if mappe_oggetti_file.exists():
        logging.info(f"Elaborazione file mappa oggetti: {mappe_oggetti_file}")
        
        # Carica i dati mappa oggetti
        mappe_oggetti_data = SafeLoader.safe_json_load(mappe_oggetti_file)
        
        if mappe_oggetti_data and dati_mappe:
            # Correggi posizioni oggetti
            mappe_oggetti_corrette = correggi_mappe_oggetti(mappe_oggetti_data, dati_mappe)
            
            # Salva i dati corretti
            if SafeLoader.safe_json_save(mappe_oggetti_file, mappe_oggetti_corrette):
                logging.info(f"File mappa oggetti corretto e salvato: {mappe_oggetti_file}")
                contatore += 1
        elif mappe_oggetti_data and not dati_mappe:
            logging.warning("Nessun dato mappa disponibile, impossibile correggere le posizioni degli oggetti")
            # Backup del file senza correzioni
            backup_file(mappe_oggetti_file)
    
    return contatore

def crea_file_mancanti():
    """
    Crea i file di configurazione mancanti con contenuti minimi.
    
    Returns:
        int: Numero di file creati
    """
    contatore = 0
    
    # Assicurati che le directory esistano
    directories = [
        Path("data/mappe"),
        Path("data/npc"),
        Path("data/items"),
        Path("data/classes"),
        Path("logs")
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Crea mappe_npg.json se mancante
    mappe_npg_file = Path("data/npc/mappe_npg.json")
    if not mappe_npg_file.exists():
        contenuto_minimo = {
            "taverna": []
        }
        if SafeLoader.safe_json_save(mappe_npg_file, contenuto_minimo):
            logging.info(f"Creato file mancante: {mappe_npg_file}")
            contatore += 1
    
    # Crea mappe_oggetti.json se mancante
    mappe_oggetti_file = Path("data/items/mappe_oggetti.json")
    if not mappe_oggetti_file.exists():
        contenuto_minimo = {
            "taverna": []
        }
        if SafeLoader.safe_json_save(mappe_oggetti_file, contenuto_minimo):
            logging.info(f"Creato file mancante: {mappe_oggetti_file}")
            contatore += 1
    
    # Crea npcs.json se mancante
    npcs_file = Path("data/npc/npcs.json")
    if not npcs_file.exists():
        contenuto_minimo = {
            "Oste": {
                "nome": "Oste",
                "descrizione": "Un oste cordiale con un sorriso accogliente.",
                "token": "O",
                "livello": 1,
                "hp": 10,
                "hp_max": 10,
                "inventario": []
            }
        }
        if SafeLoader.safe_json_save(npcs_file, contenuto_minimo):
            logging.info(f"Creato file mancante: {npcs_file}")
            contatore += 1
    
    return contatore

def main():
    """
    Funzione principale del script di migrazione.
    """
    configurazione_logging(livello=logging.INFO)
    logging.info("Avvio script di migrazione")
    
    # Crea directory di backup
    Path("backup").mkdir(exist_ok=True)
    
    # Crea file mancanti
    logging.info("Creazione file mancanti")
    n_file_creati = crea_file_mancanti()
    logging.info(f"Creati {n_file_creati} file mancanti")
    
    # Correggi file mappe
    logging.info("Correzione file mappe")
    n_file_mappe, dati_mappe = correggi_file_mappe()
    logging.info(f"Corretti {n_file_mappe} file mappe")
    
    # Correggi file NPC
    logging.info("Correzione file NPC")
    n_file_npc = correggi_file_npc(dati_mappe)
    logging.info(f"Corretti {n_file_npc} file NPC")
    
    # Correggi file oggetti
    logging.info("Correzione file oggetti")
    n_file_oggetti = correggi_file_oggetti(dati_mappe)
    logging.info(f"Corretti {n_file_oggetti} file oggetti")
    
    logging.info(f"Migrazione completata. Totale file elaborati: {n_file_mappe + n_file_npc + n_file_oggetti + n_file_creati}")
    
if __name__ == "__main__":
    main() 