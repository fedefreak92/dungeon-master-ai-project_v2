#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script di utilità per la validazione e correzione automatica delle posizioni degli oggetti sulle mappe.
Questo script analizza i file mappe_oggetti.json e confronta le posizioni degli oggetti
con quelle già presenti nelle mappe, identificando e risolvendo eventuali conflitti.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Aggiungi la directory principale al path di sistema per importare i moduli del gioco
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from world.managers.oggetti_manager import OggettiManager
from util.data_manager import get_data_manager

# Configura il logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('valida_mappe')

def analizza_tutte_le_mappe(correggi=False):
    """
    Analizza tutte le mappe disponibili per trovare conflitti di posizionamento.
    
    Args:
        correggi: Se True, applica automaticamente le correzioni suggerite
        
    Returns:
        dict: Dizionario con i risultati dell'analisi per ogni mappa
    """
    # Inizializza il data manager
    data_manager = get_data_manager()
    
    # Ottieni il percorso delle mappe
    mappe_dir = data_manager._data_paths.get("mappe")
    if not mappe_dir or not mappe_dir.exists():
        logger.error("Directory delle mappe non trovata")
        return {}
    
    # Ottieni tutte le mappe disponibili
    mappe_files = [f.stem for f in mappe_dir.glob("*.json")]
    logger.info(f"Trovate {len(mappe_files)} mappe da analizzare")
    
    # Inizializza il manager degli oggetti
    oggetti_manager = OggettiManager()
    
    # Dizionario per i risultati
    risultati = {}
    
    # Analizza ogni mappa
    for nome_mappa in mappe_files:
        logger.info(f"Analisi della mappa: {nome_mappa}")
        
        # Esegui la convalida
        valido, problemi, correzioni = oggetti_manager.convalida_posizioni_oggetti_mappa(nome_mappa)
        
        risultati[nome_mappa] = {
            "valido": valido,
            "problemi": problemi,
            "correzioni": correzioni
        }
        
        # Mostra i risultati
        if valido:
            logger.info(f"✅ Mappa '{nome_mappa}' valida: nessun conflitto di posizionamento")
        else:
            logger.warning(f"❌ Mappa '{nome_mappa}' non valida: {len(problemi)} conflitti rilevati")
            
            for i, problema in enumerate(problemi):
                logger.warning(f"  Problema {i+1}: {problema}")
            
            if correzioni:
                logger.info(f"  Correzioni suggerite: {len(correzioni)}")
                for i, correzione in enumerate(correzioni):
                    oggetto = correzione["oggetto"]
                    pos_orig = correzione["posizione_originale"]
                    pos_nuova = correzione["posizione_suggerita"]
                    logger.info(f"  {i+1}. Sposta '{oggetto}' da {pos_orig} a {pos_nuova}")
            
            # Se richiesto, applica le correzioni
            if correggi and correzioni:
                applica_correzioni(nome_mappa, correzioni)
                logger.info(f"✅ Correzioni applicate alla mappa '{nome_mappa}'")
    
    # Restituisci i risultati
    return risultati

def applica_correzioni(nome_mappa, correzioni):
    """
    Applica le correzioni suggerite al file mappe_oggetti.json.
    
    Args:
        nome_mappa: Nome della mappa da correggere
        correzioni: Lista di correzioni da applicare
    """
    # Ottieni il data manager
    data_manager = get_data_manager()
    
    # Carica le configurazioni attuali
    oggetti_mappa = data_manager.get_map_objects(nome_mappa)
    
    if not oggetti_mappa:
        logger.error(f"Impossibile caricare gli oggetti per la mappa {nome_mappa}")
        return
    
    # Applica le correzioni
    modifiche = False
    for correzione in correzioni:
        nome_oggetto = correzione["oggetto"]
        pos_vecchia = correzione["posizione_originale"]
        pos_nuova = correzione["posizione_suggerita"]
        
        # Cerca l'oggetto da modificare
        for oggetto in oggetti_mappa:
            if oggetto.get("nome") == nome_oggetto:
                # Verifica che la posizione corrisponda a quella da correggere
                if oggetto.get("posizione") == pos_vecchia:
                    oggetto["posizione"] = pos_nuova
                    logger.info(f"Oggetto '{nome_oggetto}' spostato da {pos_vecchia} a {pos_nuova}")
                    modifiche = True
                    break
    
    # Se sono state apportate modifiche, salva il file
    if modifiche:
        try:
            # Salva le modifiche
            data_manager.save_map_objects(nome_mappa, oggetti_mappa)
            logger.info(f"File mappe_oggetti.json aggiornato per la mappa {nome_mappa}")
        except Exception as e:
            logger.error(f"Errore durante il salvataggio delle correzioni: {e}")
    else:
        logger.warning("Nessuna modifica effettuata")

def esporta_report(risultati, percorso_file):
    """
    Esporta un report dell'analisi in formato JSON.
    
    Args:
        risultati: Dizionario con i risultati dell'analisi
        percorso_file: Percorso del file in cui salvare il report
    """
    try:
        with open(percorso_file, 'w', encoding='utf-8') as f:
            json.dump(risultati, f, indent=2, ensure_ascii=False)
        logger.info(f"Report salvato in: {percorso_file}")
    except Exception as e:
        logger.error(f"Errore durante il salvataggio del report: {e}")

def main():
    """Funzione principale dello script."""
    # Configura il parser degli argomenti
    parser = argparse.ArgumentParser(
        description="Strumento per la validazione e correzione delle posizioni degli oggetti sulle mappe"
    )
    parser.add_argument(
        "-c", "--correggi", 
        action="store_true", 
        help="Applica automaticamente le correzioni suggerite"
    )
    parser.add_argument(
        "-r", "--report", 
        type=str, 
        help="Esporta un report dell'analisi in formato JSON nel file specificato"
    )
    parser.add_argument(
        "-m", "--mappa", 
        type=str, 
        help="Analizza solo la mappa specificata"
    )
    
    # Analizza gli argomenti
    args = parser.parse_args()
    
    # Esegui l'analisi
    if args.mappa:
        logger.info(f"Analisi della mappa: {args.mappa}")
        
        # Inizializza il manager degli oggetti
        oggetti_manager = OggettiManager()
        
        # Esegui la convalida
        valido, problemi, correzioni = oggetti_manager.convalida_posizioni_oggetti_mappa(args.mappa)
        
        risultati = {
            args.mappa: {
                "valido": valido,
                "problemi": problemi,
                "correzioni": correzioni
            }
        }
        
        # Mostra i risultati
        if valido:
            logger.info(f"✅ Mappa '{args.mappa}' valida: nessun conflitto di posizionamento")
        else:
            logger.warning(f"❌ Mappa '{args.mappa}' non valida: {len(problemi)} conflitti rilevati")
            
            for i, problema in enumerate(problemi):
                logger.warning(f"  Problema {i+1}: {problema}")
            
            if correzioni:
                logger.info(f"  Correzioni suggerite: {len(correzioni)}")
                for i, correzione in enumerate(correzioni):
                    oggetto = correzione["oggetto"]
                    pos_orig = correzione["posizione_originale"]
                    pos_nuova = correzione["posizione_suggerita"]
                    logger.info(f"  {i+1}. Sposta '{oggetto}' da {pos_orig} a {pos_nuova}")
            
            # Se richiesto, applica le correzioni
            if args.correggi and correzioni:
                applica_correzioni(args.mappa, correzioni)
                logger.info(f"✅ Correzioni applicate alla mappa '{args.mappa}'")
    else:
        # Analizza tutte le mappe
        risultati = analizza_tutte_le_mappe(args.correggi)
    
    # Esporta il report se richiesto
    if args.report:
        esporta_report(risultati, args.report)

if __name__ == "__main__":
    main() 