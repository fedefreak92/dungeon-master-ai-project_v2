#!/usr/bin/env python
"""
Script per la standardizzazione e ottimizzazione dei formati dati del gioco RPG.

Questo script esegue:
1. Generazione di schemi JSON per tutti i tipi di entità
2. Validazione dei dati esistenti contro gli schemi
3. Migrazione dei dati al nuovo formato standardizzato
4. Test del sistema di serializzazione
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Configura il logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data_standardization.log')
    ]
)
logger = logging.getLogger(__name__)

# Aggiungi la directory corrente al path per l'import dei moduli
sys.path.insert(0, os.path.abspath('.'))

def setup_environment():
    """Configura l'ambiente e crea le directory necessarie."""
    # Percorso directory schemas
    schemas_dir = Path("gioco_rpg/data/schemas")
    
    # Crea la directory degli schemi se non esiste
    if not schemas_dir.exists():
        try:
            schemas_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Creata directory degli schemi: {schemas_dir}")
        except Exception as e:
            logger.error(f"Impossibile creare directory {schemas_dir}: {str(e)}")
            return False
            
    return True

def generate_schemas(force=False):
    """
    Genera schemi JSON per tutti i tipi di entità.
    
    Args:
        force: Se True, sovrascrive gli schemi esistenti
        
    Returns:
        bool: True se la generazione è riuscita
    """
    logger.info("Generazione schemi JSON...")
    
    from util.data_manager import get_data_manager
    from util.json_validator import generate_schema_from_data
    
    # Ottieni il data manager
    data_manager = get_data_manager()
    
    # Per ogni tipo di entità
    for data_type, entity_type in data_manager._entity_mapping.items():
        logger.info(f"Generazione schema per {entity_type} (tipo dati: {data_type})...")
        
        # Carica un esempio di dati
        files = data_manager.get_all_data_files(data_type)
        if not files:
            logger.warning(f"Nessun file trovato per {data_type}, impossibile generare schema")
            continue
            
        # Usa il primo file come esempio
        sample_file = files[0]
        sample_data = data_manager.load_data(data_type, sample_file, validate=False)
        
        if not sample_data:
            logger.warning(f"File di esempio vuoto: {sample_file}")
            continue
            
        # Estrai un elemento da usare come modello
        sample_item = None
        if isinstance(sample_data, dict) and sample_data:
            # Prendi il primo valore dal dizionario
            sample_item = next(iter(sample_data.values()))
        elif isinstance(sample_data, list) and sample_data:
            # Prendi il primo elemento della lista
            sample_item = sample_data[0]
            
        if not sample_item:
            logger.warning(f"Nessun elemento di esempio trovato in {sample_file}")
            continue
            
        # Genera lo schema
        result = generate_schema_from_data(sample_item, entity_type, overwrite=force)
        if result:
            logger.info(f"Schema generato per {entity_type}")
        else:
            logger.warning(f"Schema non generato per {entity_type}")
    
    logger.info("Generazione schemi completata")
    return True

def validate_all_data():
    """
    Valida tutti i dati contro gli schemi.
    
    Returns:
        bool: True se la validazione è riuscita
    """
    logger.info("Validazione dati contro gli schemi...")
    
    from util.data_manager import get_data_manager
    from util.json_validator import validate_data
    
    # Ottieni il data manager
    data_manager = get_data_manager()
    
    # Flag per il successo complessivo
    success = True
    
    # Per ogni tipo di entità
    for data_type, entity_type in data_manager._entity_mapping.items():
        logger.info(f"Validazione {data_type}...")
        
        # Carica tutti i file di questo tipo
        files = data_manager.get_all_data_files(data_type)
        if not files:
            logger.warning(f"Nessun file trovato per {data_type}")
            continue
            
        # Valida ciascun file
        for file_name in files:
            logger.info(f"Validazione file {file_name}...")
            
            # Carica i dati senza validazione
            data = data_manager.load_data(data_type, file_name, validate=False)
            
            # Valida i dati
            errors = validate_data(data, entity_type)
            
            if errors:
                logger.error(f"Validazione fallita per {file_name}: {len(errors)} errori")
                for error in errors:
                    logger.error(f"  - {error}")
                success = False
            else:
                logger.info(f"Validazione superata per {file_name}")
    
    logger.info("Validazione completata")
    return success

def migrate_all_data():
    """
    Migra tutti i dati al nuovo formato standardizzato.
    
    Returns:
        bool: True se la migrazione è riuscita
    """
    logger.info("Migrazione dati al formato standardizzato...")
    
    from util.data_migrator import migrate_all_data
    
    # Esegui la migrazione
    stats = migrate_all_data()
    
    # Verifica i risultati
    success = True
    for data_type, count in stats.items():
        if count == 0:
            logger.warning(f"Nessun file migrato per {data_type}")
        else:
            logger.info(f"{count} file migrati per {data_type}")
            
    logger.info("Migrazione completata")
    return success

def test_serialization():
    """
    Testa il sistema di serializzazione.
    
    Returns:
        bool: True se i test sono riusciti
    """
    logger.info("Test del sistema di serializzazione...")
    
    from util.serialization_tester import test_serialization
    
    # Esegui i test
    try:
        test_serialization(verbose=True)
        logger.info("Test di serializzazione completati con successo")
        return True
    except Exception as e:
        logger.error(f"Test di serializzazione falliti: {str(e)}")
        return False

def main():
    """Funzione principale per l'esecuzione dello script."""
    parser = argparse.ArgumentParser(description="Standardizza e ottimizza i formati dati del gioco RPG.")
    parser.add_argument("--setup", action="store_true", help="Configura solo l'ambiente")
    parser.add_argument("--schemas", action="store_true", help="Genera solo gli schemi JSON")
    parser.add_argument("--force-schemas", action="store_true", help="Forza la rigenerazione degli schemi")
    parser.add_argument("--validate", action="store_true", help="Valida solo i dati")
    parser.add_argument("--migrate", action="store_true", help="Migra solo i dati")
    parser.add_argument("--test", action="store_true", help="Testa solo il sistema di serializzazione")
    parser.add_argument("--all", action="store_true", help="Esegui tutte le operazioni")
    
    args = parser.parse_args()
    
    # Se nessuna opzione è specificata, mostra l'help
    if not any([args.setup, args.schemas, args.force_schemas, args.validate, args.migrate, args.test, args.all]):
        parser.print_help()
        return
    
    # Configura l'ambiente
    if args.setup or args.all:
        if not setup_environment():
            logger.error("Configurazione ambiente fallita")
            return
    
    # Genera schemi
    if args.schemas or args.force_schemas or args.all:
        if not generate_schemas(force=args.force_schemas):
            logger.error("Generazione schemi fallita")
            if not args.all:
                return
    
    # Valida dati
    if args.validate or args.all:
        if not validate_all_data():
            logger.warning("Validazione fallita per alcuni file")
            # Continua comunque
    
    # Migra dati
    if args.migrate or args.all:
        if not migrate_all_data():
            logger.error("Migrazione dati fallita")
            if not args.all:
                return
    
    # Test serializzazione
    if args.test or args.all:
        if not test_serialization():
            logger.error("Test serializzazione falliti")
            return
    
    logger.info("Operazioni completate con successo")

if __name__ == "__main__":
    main() 