import json
import os
import logging
import jsonschema
from typing import Dict, Any, List, Optional, Union, Set
from jsonschema import validate, ValidationError, SchemaError
from pathlib import Path

# Configura il logger
logger = logging.getLogger(__name__)

# Directory dove vengono memorizzati gli schemi JSON
SCHEMAS_DIR = Path(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "schemas"))

# Cache per gli schemi JSON
_schema_cache: Dict[str, Dict] = {}

# Mapping di file specifici a schemi personalizzati
FILE_TO_SCHEMA_MAPPING = {
    "mappe_npg.json": "mappa_npg",
    "mappe_oggetti.json": "mappa_oggetti"
}

def load_schema(entity_type: str) -> Dict:
    """
    Carica uno schema JSON per un tipo di entità.
    
    Args:
        entity_type: Tipo di entità (es. "mostro", "npc", "oggetto")
        
    Returns:
        Dict: Schema JSON per l'entità specificata
    """
    # Verifica cache
    if entity_type in _schema_cache:
        return _schema_cache[entity_type]
        
    # Costruisci il percorso dello schema
    schema_path = SCHEMAS_DIR / f"{entity_type}_schema.json"
    
    # Se lo schema non esiste, genera un errore
    if not schema_path.exists():
        logger.error(f"Schema JSON non trovato per il tipo di entità: {entity_type}")
        raise FileNotFoundError(f"Schema JSON non trovato: {schema_path}")
        
    # Carica lo schema
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
            _schema_cache[entity_type] = schema
            return schema
    except Exception as e:
        logger.error(f"Errore nel caricamento dello schema {schema_path}: {str(e)}")
        raise

def validate_data(data: Union[Dict, List], entity_type: str, file_name: Optional[str] = None) -> List[str]:
    """
    Valida i dati contro uno schema JSON.
    
    Args:
        data: Dati da validare (dizionario o lista)
        entity_type: Tipo di entità (es. "mostro", "npc", "oggetto")
        file_name: Nome del file, se disponibile, per schemi specifici
        
    Returns:
        List[str]: Lista di errori trovati durante la validazione
    """
    errors = []
    
    try:
        # Determina lo schema da utilizzare
        schema_type = entity_type
        
        # Se è fornito un nome file, verifica se esiste uno schema specifico
        if file_name and file_name in FILE_TO_SCHEMA_MAPPING:
            schema_type = FILE_TO_SCHEMA_MAPPING[file_name]
            logger.debug(f"Utilizzo schema specifico '{schema_type}' per il file {file_name}")
        
        schema = load_schema(schema_type)
        
        # Per le liste, valida ogni elemento
        if isinstance(data, list):
            for i, item in enumerate(data):
                try:
                    validate(item, schema)
                except ValidationError as e:
                    errors.append(f"Errore nell'elemento {i}: {e.message}")
        else:
            # Per i dizionari, valida l'intero dizionario
            try:
                validate(data, schema)
            except ValidationError as e:
                errors.append(f"Errore di validazione: {e.message}")
                
    except FileNotFoundError as e:
        errors.append(str(e))
    except SchemaError as e:
        errors.append(f"Errore nello schema: {str(e)}")
    except Exception as e:
        errors.append(f"Errore imprevisto: {str(e)}")
        
    return errors

def ensure_schema_directory() -> None:
    """
    Assicura che la directory degli schemi esista.
    """
    if not SCHEMAS_DIR.exists():
        try:
            SCHEMAS_DIR.mkdir(parents=True)
            logger.info(f"Creata directory degli schemi: {SCHEMAS_DIR}")
        except Exception as e:
            logger.error(f"Impossibile creare la directory degli schemi {SCHEMAS_DIR}: {str(e)}")

def generate_schema_from_data(data: Dict, entity_type: str, overwrite: bool = False) -> bool:
    """
    Genera uno schema JSON a partire dai dati esempio.
    Utile per creare schemi iniziali basati sui dati esistenti.
    
    Args:
        data: Dati da cui generare lo schema
        entity_type: Tipo di entità
        overwrite: Se sovrascrivere uno schema esistente
        
    Returns:
        bool: True se lo schema è stato creato con successo
    """
    ensure_schema_directory()
    
    schema_path = SCHEMAS_DIR / f"{entity_type}_schema.json"
    
    # Verifica se esiste già uno schema
    if schema_path.exists() and not overwrite:
        logger.info(f"Schema già esistente per {entity_type}. Usa overwrite=True per sovrascriverlo.")
        return False
        
    def _infer_type(value: Any) -> Dict:
        """Inferisce il tipo di un valore per lo schema JSON."""
        if value is None:
            return {"type": ["null", "string"]}
        elif isinstance(value, str):
            return {"type": "string"}
        elif isinstance(value, bool):
            return {"type": "boolean"}
        elif isinstance(value, int):
            return {"type": "integer"}
        elif isinstance(value, float):
            return {"type": "number"}
        elif isinstance(value, list):
            if value:
                # Cerca di determinare il tipo degli elementi
                item_types = set()
                for item in value:
                    if isinstance(item, dict):
                        item_types.add("object")
                    elif isinstance(item, (str, int, float, bool)):
                        item_types.add(type(item).__name__)
                        
                if len(item_types) == 1 and "object" in item_types:
                    # Genera schema per gli elementi oggetto
                    return {
                        "type": "array",
                        "items": _infer_schema_from_dict(value[0])
                    }
                else:
                    return {"type": "array"}
            else:
                return {"type": "array"}
        elif isinstance(value, dict):
            return _infer_schema_from_dict(value)
        else:
            return {"type": "string"}  # Fallback
    
    def _infer_schema_from_dict(obj: Dict) -> Dict:
        """Genera uno schema da un dizionario."""
        properties = {}
        required = []
        
        for key, value in obj.items():
            properties[key] = _infer_type(value)
            if value is not None:  # Considera obbligatori gli attributi non nulli
                required.append(key)
                
        result = {
            "type": "object",
            "properties": properties
        }
        
        if required:
            result["required"] = required
            
        return result
    
    # Crea lo schema
    if isinstance(data, dict):
        # Elemento singolo
        schema = _infer_schema_from_dict(data)
        schema["$schema"] = "http://json-schema.org/draft-07/schema#"
        schema["title"] = f"{entity_type.capitalize()} Schema"
        schema["description"] = f"Schema per la validazione di {entity_type}"
    elif isinstance(data, list) and data:
        # Lista di elementi
        # Prendi il primo elemento come esempio
        schema = _infer_type(data[0])
        schema["$schema"] = "http://json-schema.org/draft-07/schema#"
        schema["title"] = f"{entity_type.capitalize()} Schema"
        schema["description"] = f"Schema per la validazione di {entity_type}"
    else:
        logger.error(f"Dati non validi per generare schema: {type(data)}")
        return False
        
    try:
        with open(schema_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
            logger.info(f"Schema generato con successo per {entity_type}: {schema_path}")
            return True
    except Exception as e:
        logger.error(f"Errore durante la scrittura dello schema {schema_path}: {str(e)}")
        return False 