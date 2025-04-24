import os
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Set

# Importa i moduli necessari
from util.data_manager import get_data_manager, DataManager, CURRENT_DATA_VERSION
from util.json_validator import validate_data, generate_schema_from_data, ensure_schema_directory

# Configura il logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Directory di dati
DATA_DIR = Path(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))

def migrate_all_data() -> Dict[str, int]:
    """
    Migra tutti i dati al nuovo formato standardizzato.
    
    Returns:
        Dict[str, int]: Dizionario con il numero di file migrati per tipo di dati
    """
    logger.info("Avvio migrazione di tutti i dati al formato standard...")
    
    # Statistiche sulla migrazione
    stats = {}
    
    # Ottieni il data manager
    data_manager = get_data_manager()
    
    # Per ogni tipo di dati supportato
    for data_type, entity_type in data_manager._entity_mapping.items():
        logger.info(f"Migrazione tipo di dati: {data_type} (entità: {entity_type})")
        
        # Genera schema se non esiste
        schema_path = DATA_DIR / "schemas" / f"{entity_type}_schema.json"
        if not schema_path.exists():
            logger.info(f"Schema non trovato per {entity_type}, generazione automatica...")
            _generate_schema_for_type(data_type, entity_type, data_manager)
        
        # Ottieni tutti i file di questo tipo
        files = data_manager.get_all_data_files(data_type)
        if not files:
            logger.info(f"Nessun file trovato per il tipo {data_type}")
            stats[data_type] = 0
            continue
        
        # Migra ciascun file
        migrated = 0
        for file_name in files:
            result = migrate_data_file(data_type, file_name, data_manager)
            if result:
                migrated += 1
                
        stats[data_type] = migrated
        logger.info(f"Migrati {migrated} file di tipo {data_type}")
    
    logger.info("Migrazione completata.")
    return stats

def _generate_schema_for_type(data_type: str, entity_type: str, data_manager: DataManager) -> bool:
    """
    Genera uno schema JSON per un tipo di entità basandosi sui dati esistenti.
    
    Args:
        data_type: Tipo di dati
        entity_type: Tipo di entità
        data_manager: Istanza del DataManager
        
    Returns:
        bool: True se lo schema è stato generato con successo
    """
    # Assicura che la directory degli schemi esista
    ensure_schema_directory()
    
    # Trova un file di esempio per questo tipo
    files = data_manager.get_all_data_files(data_type)
    if not files:
        logger.warning(f"Nessun file di esempio trovato per {data_type}")
        return False
    
    # Carica il primo file come esempio
    sample_file = files[0]
    sample_data = data_manager.load_data(data_type, sample_file, validate=False)
    
    if not sample_data:
        logger.warning(f"File di esempio vuoto: {sample_file}")
        return False
    
    # Estrai un elemento di esempio per la generazione dello schema
    sample_item = None
    
    if isinstance(sample_data, dict) and sample_data:
        # Prendi il primo valore dal dizionario
        sample_item = next(iter(sample_data.values()))
    elif isinstance(sample_data, list) and sample_data:
        # Prendi il primo elemento della lista
        sample_item = sample_data[0]
    
    if not sample_item:
        logger.warning(f"Nessun elemento di esempio trovato in {sample_file}")
        return False
    
    # Genera lo schema
    result = generate_schema_from_data(sample_item, entity_type)
    logger.info(f"Schema generato per {entity_type}: {result}")
    return result

def migrate_data_file(data_type: str, file_name: str, data_manager: Optional[DataManager] = None) -> bool:
    """
    Migra un singolo file dati al nuovo formato standardizzato.
    
    Args:
        data_type: Tipo di dati
        file_name: Nome del file
        data_manager: Istanza del DataManager (opzionale)
        
    Returns:
        bool: True se la migrazione è riuscita
    """
    if data_manager is None:
        data_manager = get_data_manager()
    
    # Verifica che il tipo di dati sia valido
    if data_type not in data_manager._data_paths:
        logger.error(f"Tipo di dati non valido: {data_type}")
        return False
    
    # Percorso completo del file
    file_path = data_manager._data_paths[data_type] / file_name
    if not file_path.exists():
        logger.error(f"File non trovato: {file_path}")
        return False
    
    logger.info(f"Migrazione file {file_path}...")
    
    # Carica i dati dal file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Errore nel caricamento del file {file_path}: {str(e)}")
        return False
    
    # Determina se abbiamo già la versione corrente
    data_version = None
    if isinstance(data, dict) and "_version" in data:
        data_version = data["_version"]
    
    if data_version == CURRENT_DATA_VERSION:
        logger.info(f"File già alla versione corrente {CURRENT_DATA_VERSION}, migrazione non necessaria")
        return True
    
    # Aggiungi la versione ai dati
    if isinstance(data, dict):
        data["_version"] = CURRENT_DATA_VERSION
    
    # Se il file è un dizionario, migra ogni elemento
    if isinstance(data, dict):
        # Migrazione specifica per ogni tipo di dati
        if data_type == "mostri":
            _migrate_monsters(data)
        elif data_type == "npc":
            _migrate_npcs(data)
        elif data_type == "oggetti":
            _migrate_items(data)
        elif data_type == "mappe":
            _migrate_maps(data)
    
    # Se il file è una lista, migra ogni elemento
    elif isinstance(data, list):
        # Migrazione specifica per ogni tipo di dati
        if data_type == "oggetti":
            data = _migrate_item_list(data)
    
    # Salva i dati migrati
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"File migrato con successo: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Errore nel salvataggio del file migrato {file_path}: {str(e)}")
        return False

def _migrate_monsters(monsters: Dict[str, Any]) -> None:
    """Migra i dati dei mostri."""
    for monster_id, monster in monsters.items():
        # Aggiungi il campo ID se non presente
        if "id" not in monster:
            monster["id"] = monster_id
        
        # Aggiungi il campo difesa se non presente
        if "difesa" not in monster:
            # Deriva la difesa dall'armatura o usa un valore predefinito
            monster["difesa"] = 0
            if "armatura" in monster:
                # Logica semplificata: il valore dipende dal tipo di armatura
                armature_valori = {
                    "Armatura di cuoio": 2,
                    "Armatura a scaglie": 4,
                    "Pelliccia spessa": 1,
                    "Resti di armatura": 3,
                    "Pelle coriacea": 5,
                    "Scaglie spesse": 7,
                    "Esoscheletro": 3,
                    "Vestiti logori": 1,
                    "Tunica del culto": 2
                }
                monster["difesa"] = armature_valori.get(monster["armatura"], 0)
        
        # Aggiungi il campo zone se non presente
        if "zone" not in monster:
            monster["zone"] = []
        
        # Aggiungi il campo abilita_speciali se non presente
        if "abilita_speciali" not in monster:
            monster["abilita_speciali"] = []
        
        # Aggiungi il campo loot se non presente
        if "loot" not in monster:
            monster["loot"] = []

def _migrate_npcs(npcs: Dict[str, Any]) -> None:
    """Migra i dati degli NPC."""
    for npc_id, npc in npcs.items():
        # Aggiungi il campo ID se non presente
        if "id" not in npc:
            npc["id"] = npc_id
        
        # Aggiungi campi standard se mancanti
        if "ruolo" not in npc:
            npc["ruolo"] = "cittadino"  # ruolo predefinito
        
        if "posizione" not in npc:
            npc["posizione"] = {"mappa": "default", "x": 0, "y": 0}

def _migrate_items(items: Dict[str, Any]) -> None:
    """Migra i dati degli oggetti (formato dizionario)."""
    for item_id, item in items.items():
        # Aggiungi il campo ID se non presente
        if "id" not in item:
            item["id"] = item_id
        
        # Aggiungi campi standard se mancanti
        if "tipo" not in item and "categoria" not in item:
            # Cerca di determinare il tipo dall'ID o dal nome del file
            item["tipo"] = "oggetto"  # tipo predefinito
        
        if "valore" not in item:
            item["valore"] = 0  # valore predefinito

def _migrate_item_list(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Migra i dati degli oggetti (formato lista)."""
    for item in items:
        # Assicura che ogni oggetto abbia un ID
        if "id" not in item and "nome" in item:
            # Genera ID dal nome se mancante
            item["id"] = item["nome"].lower().replace(" ", "_")
        
        # Aggiungi campi standard se mancanti
        if "tipo" not in item and "categoria" not in item:
            item["tipo"] = "oggetto"  # tipo predefinito
        
        if "valore" not in item:
            item["valore"] = 0  # valore predefinito
            
    return items

def _migrate_maps(maps: Dict[str, Any]) -> None:
    """Migra i dati delle mappe."""
    for map_id, map_data in maps.items():
        # Aggiungi il campo ID se non presente
        if "id" not in map_data:
            map_data["id"] = map_id
        
        # Aggiungi campi standard se mancanti
        if "connessioni" not in map_data:
            map_data["connessioni"] = []

def main():
    """Funzione principale per l'esecuzione da linea di comando."""
    parser = argparse.ArgumentParser(description="Migra i dati di gioco al formato standardizzato.")
    parser.add_argument("--all", action="store_true", help="Migra tutti i tipi di dati")
    parser.add_argument("--type", type=str, help="Tipo di dati da migrare (es. mostri, oggetti)")
    parser.add_argument("--file", type=str, help="Nome del file da migrare (opzionale)")
    
    args = parser.parse_args()
    
    if args.all:
        # Migra tutti i dati
        stats = migrate_all_data()
        print("Migrazione completata:")
        for data_type, count in stats.items():
            print(f"  - {data_type}: {count} file migrati")
    elif args.type:
        # Migra un tipo specifico
        data_manager = get_data_manager()
        if args.file:
            # Migra un file specifico
            if migrate_data_file(args.type, args.file, data_manager):
                print(f"Migrazione completata per {args.file}")
            else:
                print(f"Errore nella migrazione di {args.file}")
        else:
            # Migra tutti i file di questo tipo
            count = 0
            for file_name in data_manager.get_all_data_files(args.type):
                if migrate_data_file(args.type, file_name, data_manager):
                    count += 1
            print(f"Migrazione completata: {count} file migrati per il tipo {args.type}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 