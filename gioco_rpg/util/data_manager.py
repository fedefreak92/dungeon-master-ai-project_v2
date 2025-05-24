import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable, Set
import hashlib

# Import dei nuovi moduli di validazione
from util.json_validator import validate_data, generate_schema_from_data

# Configura il logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Percorso base per i dati
DATA_DIR = Path(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))

# Versione attuale del formato dati
CURRENT_DATA_VERSION = "1.0.0"

# Hook personalizzabili
class DataHooks:
    """Hooks per la personalizzazione del comportamento del DataManager."""
    
    pre_load: Dict[str, List[Callable]] = {}
    post_load: Dict[str, List[Callable]] = {}
    pre_save: Dict[str, List[Callable]] = {}
    post_save: Dict[str, List[Callable]] = {}
    
    @classmethod
    def register_pre_load(cls, data_type: str, callback: Callable) -> None:
        """Registra una callback da eseguire prima del caricamento di dati."""
        if data_type not in cls.pre_load:
            cls.pre_load[data_type] = []
        cls.pre_load[data_type].append(callback)
    
    @classmethod
    def register_post_load(cls, data_type: str, callback: Callable) -> None:
        """Registra una callback da eseguire dopo il caricamento di dati."""
        if data_type not in cls.post_load:
            cls.post_load[data_type] = []
        cls.post_load[data_type].append(callback)
    
    @classmethod
    def register_pre_save(cls, data_type: str, callback: Callable) -> None:
        """Registra una callback da eseguire prima del salvataggio di dati."""
        if data_type not in cls.pre_save:
            cls.pre_save[data_type] = []
        cls.pre_save[data_type].append(callback)
    
    @classmethod
    def register_post_save(cls, data_type: str, callback: Callable) -> None:
        """Registra una callback da eseguire dopo il salvataggio di dati."""
        if data_type not in cls.post_save:
            cls.post_save[data_type] = []
        cls.post_save[data_type].append(callback)

class DataManager:
    """
    Gestore per i dati statici del gioco.
    Carica i dati dai file JSON nella directory 'data'.
    
    Caratteristiche:
    - Cache intelligente con gestione TTL (time-to-live)
    - Caricamento lazy per ottimizzare le prestazioni
    - Versionamento dei file dati
    - Sistema di hook per eventi pre/post caricamento/salvataggio
    - Validazione automatica tramite schemi JSON
    """
    
    _instance = None
    _data_cache = {}  # Cache dati
    _cache_metadata = {}  # Metadati cache (timestamp, hash, ecc.)
    
    # Configurazione TTL predefinito della cache (in secondi)
    DEFAULT_CACHE_TTL = 300  # 5 minuti
    
    # Modalità di caricamento
    LAZY_LOADING = True  # Se True, carica solo quando richiesto
    
    def __new__(cls):
        """Implementazione singleton per avere una sola istanza del gestore dati."""
        if cls._instance is None:
            cls._instance = super(DataManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Inizializza le directory per i dati."""
        # Configura i percorsi per i diversi tipi di dati
        self._data_paths = {
            "classi": DATA_DIR / "classes",  # Aggiornato per puntare alla directory 'classes'
            "classes": DATA_DIR / "classes",  # Aggiungo il supporto esplicito per 'classes'
            "tutorials": DATA_DIR / "tutorials",
            "achievements": DATA_DIR / "achievements",
            "oggetti": DATA_DIR / "items",
            "npc": DATA_DIR / "npc",
            "mostri": DATA_DIR / "monsters",
            "mappe": DATA_DIR / "mappe",
            "assets_info": DATA_DIR / "assets_info",
            "world_state": DATA_DIR / "world_state",
            "schemas": DATA_DIR / "schemas",
        }
        
        # Mapping tra tipi di dati e entità per la validazione
        self._entity_mapping = {
            "classi": "classe",
            "classes": "classe",  # Aggiungo mapping anche per 'classes'
            "tutorials": "tutorial",
            "achievements": "achievement",
            "oggetti": "oggetto",
            "npc": "npc",
            "mostri": "mostro",
            "mappe": "mappa",
        }
        
        # Assicurati che tutte le directory esistano
        for path in self._data_paths.values():
            if not path.exists():
                logger.warning(f"Directory dati non trovata: {path}")
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Creata directory: {path}")
                except Exception as e:
                    logger.error(f"Impossibile creare directory {path}: {str(e)}")
        
        # Assicurati esplicitamente che la directory schemas esista
        schemas_path = self._data_paths["schemas"]
        if not schemas_path.exists():
            try:
                schemas_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Creata directory schemas: {schemas_path}")
            except Exception as e:
                logger.error(f"Impossibile creare directory schemas {schemas_path}: {str(e)}")
        
        # Configurazione TTL specifici per tipo di dati
        self._cache_ttl = {
            # Dati che cambiano raramente (TTL più lungo)
            "classi": 3600,            # 1 ora
            "tutorials": 3600,         # 1 ora
            "achievements": 1800,      # 30 minuti
            
            # Dati che cambiano più frequentemente
            "oggetti": 300,            # 5 minuti
            "npc": 300,                # 5 minuti
            "mostri": 300,             # 5 minuti
            "mappe": 300,              # 5 minuti
            
            # Dati che cambiano molto frequentemente
            "world_state": 60,         # 1 minuto
            
            # TTL per gli schemi
            "schemas": 3600,           # 1 ora
        }
    
    def load_data(self, data_type: str, file_name: Optional[str] = None, 
                 reload: bool = False, validate: bool = True) -> Union[Dict, List]:
        """
        Carica i dati da un file JSON.
        
        Args:
            data_type: Tipo di dati da caricare (classi, tutorials, ecc.)
            file_name: Nome del file specifico. Se None, usa il valore predefinito.
            reload: Se True, ricarica i dati anche se già in cache.
            validate: Se True, valida i dati contro lo schema
            
        Returns:
            dict/list: I dati caricati dal file.
        """
        if data_type not in self._data_paths:
            logger.error(f"Tipo di dati non valido: {data_type}")
            # Verifichiamo se è possibile aggiungere questo tipo di dati dinamicamente
            if isinstance(data_type, str) and data_type:
                logger.warning(f"Tentativo di aggiungere dinamicamente il tipo di dati: {data_type}")
                try:
                    nuovo_percorso = DATA_DIR / data_type
                    nuovo_percorso.mkdir(parents=True, exist_ok=True)
                    self._data_paths[data_type] = nuovo_percorso
                    logger.info(f"Aggiunto nuovo tipo di dati: {data_type} con percorso {nuovo_percorso}")
                except Exception as e:
                    logger.error(f"Impossibile creare directory per il nuovo tipo di dati {data_type}: {str(e)}")
                    return {}
            else:
                return {}
        
        # Determina il nome del file predefinito se non specificato
        if file_name is None:
            file_name = f"{data_type}.json"
            
        # Assicurati che il nome del file abbia l'estensione .json
        if not file_name.lower().endswith('.json'):
            file_name = f"{file_name}.json"
        
        # Chiave per la cache
        cache_key = f"{data_type}/{file_name}"
        
        # Verifica se i dati sono in cache e se sono ancora validi
        if not reload and self._is_cache_valid(cache_key):
            logger.debug(f"Utilizzo dati dalla cache: {cache_key}")
            return self._data_cache[cache_key]
        
        # Esegui hooks pre-caricamento
        if data_type in DataHooks.pre_load:
            for hook in DataHooks.pre_load[data_type]:
                try:
                    hook(file_name)
                except Exception as e:
                    logger.error(f"Errore nell'esecuzione del hook pre-caricamento per {data_type}: {str(e)}")
        
        # Percorso completo del file JSON
        file_path = self._data_paths[data_type] / file_name
        
        # Se il file non esiste, prova con diverse varianti
        if not file_path.exists():
            logger.warning(f"File non trovato: {file_path}, tentativo con varianti...")
            
            # Prova con file_name senza estensione + .json
            if '.' in file_name:
                nome_base = file_name.rsplit('.', 1)[0]
                file_path_alt = self._data_paths[data_type] / f"{nome_base}.json"
                if file_path_alt.exists():
                    logger.info(f"Trovata alternativa: {file_path_alt}")
                    file_path = file_path_alt
                
            # Prova con il file default del tipo di dati
            if not file_path.exists():
                file_path_default = self._data_paths[data_type] / f"{data_type}.json"
                if file_path_default.exists():
                    logger.info(f"Utilizzando file default: {file_path_default}")
                    file_path = file_path_default
        
        # Se ancora non esiste, log e exit
        if not file_path.exists():
            logger.error(f"File non trovato dopo tentativi alternativi: {file_path}")
            return {}
        
        # Carica i dati dal file JSON
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Dati caricati da JSON: {file_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Errore nella decodifica JSON del file {file_path}: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Errore nel caricamento del file JSON {file_path}: {str(e)}")
            return {}
        
        # Gestione del versionamento
        data_version = self._get_data_version(data)
        if data_version is not None and data_version != CURRENT_DATA_VERSION:
            data = self._migrate_data(data, data_version, data_type)
        
        # Validazione (se richiesta)
        if validate and data_type in self._entity_mapping:
            entity_type = self._entity_mapping[data_type]
            errors = validate_data(data, entity_type, file_name)
            if errors:
                for error in errors:
                    logger.warning(f"Errore di validazione in {file_name}: {error}")
                
                # Genera schema automaticamente se non esiste
                self._auto_generate_schema(data, entity_type)
        
        # Aggiorna la cache
        self._update_cache(cache_key, data, file_path)
        
        # Esegui hooks post-caricamento
        if data_type in DataHooks.post_load:
            for hook in DataHooks.post_load[data_type]:
                try:
                    data = hook(data)
                except Exception as e:
                    logger.error(f"Errore nell'esecuzione del hook post-caricamento per {data_type}: {str(e)}")
        
        return data
    
    def _get_data_version(self, data: Union[Dict, List]) -> Optional[str]:
        """Estrae la versione dai dati se presente."""
        if isinstance(data, dict) and "_version" in data:
            return data["_version"]
        return None
    
    def _migrate_data(self, data: Union[Dict, List], from_version: str, data_type: str) -> Union[Dict, List]:
        """
        Migra i dati da una versione precedente a quella attuale.
        
        Args:
            data: Dati da migrare
            from_version: Versione attuale dei dati
            data_type: Tipo di dati
            
        Returns:
            Union[Dict, List]: Dati migrati
        """
        logger.info(f"Migrazione dati {data_type} dalla versione {from_version} alla {CURRENT_DATA_VERSION}")
        
        # Implementazione delle migrazioni specifiche
        # Esempio: from_version "0.9.0" -> CURRENT_DATA_VERSION "1.0.0"
        if from_version == "0.9.0" and CURRENT_DATA_VERSION == "1.0.0":
            if data_type == "mostri" and isinstance(data, dict):
                # Esempio: aggiunta campo difesa a tutti i mostri
                for mostro in data.values():
                    if "difesa" not in mostro:
                        mostro["difesa"] = mostro.get("armatura", 0)
            
            # Aggiungi altre migrazioni specifiche qui
        
        # Aggiorna la versione nei dati
        if isinstance(data, dict):
            data["_version"] = CURRENT_DATA_VERSION
        
        return data
    
    def _auto_generate_schema(self, data: Union[Dict, List], entity_type: str) -> None:
        """Genera automaticamente uno schema se non esiste."""
        try:
            # Assicuriamoci che il percorso schemas sia sempre definito nel dizionario _data_paths
            # Questa voce dovrebbe essere sempre presente dall'inizializzazione
            schema_path = self._data_paths["schemas"] / f"{entity_type}_schema.json"
            
            if not schema_path.exists():
                logger.info(f"Generazione automatica schema per {entity_type}")
                if isinstance(data, dict) and len(data) > 0:
                    # Prendi il primo elemento del dizionario come esempio
                    sample = next(iter(data.values()))
                    generate_schema_from_data(sample, entity_type)
                elif isinstance(data, list) and len(data) > 0:
                    # Usa il primo elemento della lista come esempio
                    generate_schema_from_data(data[0], entity_type)
        except Exception as e:
            logger.error(f"Errore durante la generazione automatica dello schema per {entity_type}: {e}")
            # Non solleviamo eccezioni per non bloccare il caricamento dei dati
            
    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Verifica se i dati in cache sono ancora validi.
        
        Args:
            cache_key: Chiave della cache da verificare
            
        Returns:
            bool: True se i dati sono validi, False altrimenti
        """
        # Se la chiave non è in cache, non è valida
        if cache_key not in self._data_cache:
            return False
            
        # Se non ci sono metadati, considera la cache non valida
        if cache_key not in self._cache_metadata:
            return False
            
        metadata = self._cache_metadata[cache_key]
        
        # Verifica TTL
        current_time = time.time()
        ttl = self._get_ttl_for_key(cache_key)
        if current_time - metadata.get("timestamp", 0) > ttl:
            logger.debug(f"Cache scaduta per {cache_key}")
            return False
            
        # Verifica se il file è stato modificato
        file_path = metadata.get("file_path")
        if file_path and os.path.exists(file_path):
            if os.path.getmtime(file_path) > metadata.get("timestamp", 0):
                logger.debug(f"File modificato dopo l'ultimo caricamento: {file_path}")
                return False
                
        return True
    
    def _get_ttl_for_key(self, cache_key: str) -> int:
        """Ottiene il TTL appropriato per una chiave cache."""
        # Estrai il tipo di dati dalla chiave cache
        parts = cache_key.split('/')
        data_type = parts[0] if parts else ""
        
        # Usa il TTL specifico o quello predefinito
        return self._cache_ttl.get(data_type, self.DEFAULT_CACHE_TTL)
    
    def _update_cache(self, cache_key: str, data: Union[Dict, List], file_path: Path) -> None:
        """
        Aggiorna la cache con nuovi dati.
        
        Args:
            cache_key: Chiave della cache
            data: Dati da memorizzare
            file_path: Percorso del file di origine
        """
        # Aggiorna i dati in cache
        self._data_cache[cache_key] = data
        
        # Aggiorna i metadati
        self._cache_metadata[cache_key] = {
            "timestamp": time.time(),
            "file_path": str(file_path),
            "hash": self._calculate_hash(data),
        }
        
        logger.debug(f"Cache aggiornata per {cache_key}")
    
    def _calculate_hash(self, data: Union[Dict, List]) -> str:
        """Calcola un hash dei dati per rilevare cambiamenti."""
        try:
            data_str = json.dumps(data, sort_keys=True)
            return hashlib.md5(data_str.encode()).hexdigest()
        except Exception:
            return str(time.time())  # Fallback
    
    def invalidate_cache(self, data_type: Optional[str] = None, file_name: Optional[str] = None) -> None:
        """
        Invalida la cache per uno specifico tipo di dati o file.
        
        Args:
            data_type: Tipo di dati (se None, invalida tutta la cache)
            file_name: Nome del file (se None, invalida tutti i file del tipo)
        """
        if data_type is None:
            # Invalida tutta la cache
            self._data_cache.clear()
            self._cache_metadata.clear()
            logger.debug("Cache completamente invalidata")
            return
            
        # Costruisci il prefisso della chiave cache
        key_prefix = f"{data_type}/"
        if file_name:
            key_prefix = f"{data_type}/{file_name}"
            
        # Rimuovi le chiavi che corrispondono al prefisso
        keys_to_remove = [k for k in self._data_cache.keys() if k.startswith(key_prefix)]
        for key in keys_to_remove:
            self._data_cache.pop(key, None)
            self._cache_metadata.pop(key, None)
            
        logger.debug(f"Cache invalidata per {key_prefix}")
    
    def get_all_data_files(self, data_type: str) -> List[str]:
        """
        Restituisce tutti i file di dati di un certo tipo.
        
        Args:
            data_type: Tipo di dati da cercare
            
        Returns:
            list: Lista di nomi dei file disponibili
        """
        if data_type not in self._data_paths:
            logger.error(f"Tipo di dati non valido: {data_type}")
            return []
        
        path = self._data_paths[data_type]
        if not path.exists():
            return []
        
        # Cerca solo file JSON
        json_files = [f.name for f in path.glob("*.json")]
        return json_files
    
    def save_data(self, data_type: str, data: Union[Dict, List], file_name: Optional[str] = None) -> bool:
        """
        Salva i dati in file JSON.
        
        Args:
            data_type: Tipo di dati
            data: Dati da salvare
            file_name: Nome del file (se None, usa il tipo)
            
        Returns:
            bool: True se il salvataggio è riuscito
        """
        if data_type not in self._data_paths:
            logger.error(f"Tipo di dati non valido: {data_type}")
            return False
            
        # Determina il nome del file
        if file_name is None:
            file_name = f"{data_type}.json"
            
        # Percorso completo del file JSON
        file_path_json = self._data_paths[data_type] / file_name
        
        # Esegui hooks pre-salvataggio
        if data_type in DataHooks.pre_save:
            for hook in DataHooks.pre_save[data_type]:
                try:
                    data = hook(data)
                except Exception as e:
                    logger.error(f"Errore nell'esecuzione del hook pre-salvataggio per {data_type}: {str(e)}")
        
        try:
            # Aggiungi informazioni di versione
            if isinstance(data, dict):
                data["_version"] = CURRENT_DATA_VERSION
                data["_last_modified"] = time.time()
                
            # Valida i dati prima del salvataggio
            if data_type in self._entity_mapping:
                entity_type = self._entity_mapping[data_type]
                errors = validate_data(data, entity_type)
                if errors:
                    for error in errors:
                        logger.warning(f"Errore di validazione prima del salvataggio in {file_path_json}: {error}")
            
            # Crea la directory padre se non esiste
            os.makedirs(os.path.dirname(file_path_json), exist_ok=True)
            
            # Salva i dati in JSON
            with open(file_path_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.debug(f"Dati salvati in formato JSON: {file_path_json}")
                
            # Invalida la cache per questo file
            self.invalidate_cache(data_type, file_name)
            
            # Esegui hooks post-salvataggio
            if data_type in DataHooks.post_save:
                for hook in DataHooks.post_save[data_type]:
                    try:
                        hook(data)
                    except Exception as e:
                        logger.error(f"Errore nell'esecuzione del hook post-salvataggio per {data_type}: {str(e)}")
                        
            logger.info(f"Dati salvati con successo: {file_path_json}")
            return True
            
        except Exception as e:
            logger.error(f"Errore durante il salvataggio del file {file_path_json}: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
            return False
    
    def get_classes(self) -> Dict:
        """Ottieni informazioni sulle classi di personaggio."""
        try:
            # Tenta di caricare da classi/classes.json (percorso corretto)
            classi = self.load_data("classes", "classes.json", validate=False)
            if classi and isinstance(classi, dict) and len(classi) > 0:
                logger.info(f"Classi caricate correttamente da classes/classes.json: {len(classi)} classi trovate")
                return classi
            
            # Se fallisce, prova con il percorso alternativo
            classi = self.load_data("classi", "classes.json", validate=False)
            if classi and isinstance(classi, dict) and len(classi) > 0:
                logger.info(f"Classi caricate correttamente da classi/classes.json: {len(classi)} classi trovate")
                return classi
            
            # Ultimo tentativo: prova a caricare direttamente
            file_path = DATA_DIR / "classes" / "classes.json"
            if file_path.exists():
                logger.info(f"Tentativo di caricamento diretto da {file_path}")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        classi = json.load(f)
                        if classi and isinstance(classi, dict):
                            logger.info(f"Classi caricate direttamente: {len(classi)} classi trovate")
                            return classi
                except Exception as e:
                    logger.error(f"Errore nel caricamento diretto delle classi: {str(e)}")
            
            # Se siamo qui, non è stato possibile caricare le classi
            logger.error("Impossibile caricare le classi da nessun percorso. Verificare i file e i percorsi.")
            return {}
        except Exception as e:
            logger.error(f"Errore nel caricamento delle classi: {str(e)}")
            return {}
    
    def get_classe(self, classe_id: str) -> Dict:
        """
        Ottieni informazioni su una specifica classe di personaggio.
        
        Args:
            classe_id: ID della classe da recuperare
            
        Returns:
            dict: Informazioni sulla classe o None se non trovata
        """
        try:
            # Normalizza l'ID della classe (minuscolo)
            classe_id = classe_id.lower()
            
            # Prima ottiene tutte le classi
            classi = self.get_classes()
            
            # Se non ci sono classi, log esplicito
            if not classi:
                logger.error(f"Impossibile trovare classi nel sistema. Il file classes.json esiste?")
                return {}
                
            # Verifica se classe_id è una chiave valida nel dizionario
            if classe_id in classi:
                classe_info = classi[classe_id]
                # Aggiungi l'id alla classe se non presente
                if "id" not in classe_info:
                    classe_info = classe_info.copy()
                    classe_info["id"] = classe_id
                    
                # Aggiungi il nome formattato se non presente
                if "nome" not in classe_info:
                    classe_info["nome"] = classe_id.capitalize()
                    
                logger.info(f"Classe {classe_id} trovata e caricata correttamente")
                return classe_info
                
            # Log dettagliato se la classe non è stata trovata
            logger.warning(f"Classe {classe_id} non trovata. Classi disponibili: {list(classi.keys())}")
            
            # Altrimenti cerca tra gli oggetti di una lista
            if isinstance(classi, list):
                for classe in classi:
                    if classe.get("id") == classe_id:
                        logger.info(f"Classe {classe_id} trovata in formato lista")
                        return classe
                        
            # Se non troviamo la classe, restituiamo un dizionario base
            logger.error(f"Classe {classe_id} non trovata in nessun formato")
            return {
                "id": classe_id,
                "nome": classe_id.capitalize(),
                "descrizione": f"Classe {classe_id.capitalize()} (non trovata)",
                "statistiche_base": {
                    "forza": 10, "destrezza": 10, "costituzione": 10,
                    "intelligenza": 10, "saggezza": 10, "carisma": 10
                },
                "hp_base": 10,
                "mana_base": 5
            }
        except Exception as e:
            logger.error(f"Errore durante il recupero della classe {classe_id}: {str(e)}")
            return {
                "id": classe_id,
                "nome": classe_id.capitalize(),
                "descrizione": f"Classe {classe_id.capitalize()} (errore di caricamento)"
            }
    
    def get_tutorials(self) -> Dict:
        """Ottieni i tutorial del gioco."""
        return self.load_data("tutorials")
    
    def get_achievements(self) -> Dict:
        """Ottieni gli achievement del gioco."""
        return self.load_data("achievements")
    
    def get_items(self, category: Optional[str] = None) -> List:
        """
        Ottieni gli oggetti del gioco, opzionalmente filtrati per categoria.
        
        Args:
            category: Categoria di oggetti (armi, armature, ecc.)
            
        Returns:
            list: Lista di oggetti
        """
        if category:
            file_name = f"{category}.json"
            return self.load_data("oggetti", file_name)
        else:
            # Carica tutti gli oggetti da tutti i file
            items = []
            for file_name in self.get_all_data_files("oggetti"):
                items_data = self.load_data("oggetti", file_name)
                if isinstance(items_data, list):
                    items.extend(items_data)
                elif isinstance(items_data, dict):
                    # Se è un dizionario, aggiungi gli oggetti con la categoria
                    category = file_name.replace(".json", "")
                    for item_id, item in items_data.items():
                        item_copy = item.copy()
                        item_copy["id"] = item_id
                        item_copy["categoria"] = category
                        items.append(item_copy)
            return items
    
    def get_asset_info(self, asset_type: Optional[str] = None) -> Dict:
        """
        Ottieni informazioni sugli asset grafici.
        
        Args:
            asset_type: Tipo di asset (personaggio, ambiente, ecc.)
            
        Returns:
            dict: Informazioni sugli asset
        """
        file_name = f"{asset_type}.json" if asset_type else "assets.json"
        return self.load_data("assets_info", file_name)
    
    def get_npc_data(self, nome_npc: Optional[str] = None) -> Dict:
        """
        Ottieni dati di uno o tutti gli NPC.
        
        Args:
            nome_npc: Nome dello specifico NPC richiesto
            
        Returns:
            dict: Dati dell'NPC o di tutti gli NPC
        """
        npcs = self.load_data("npc", "npcs.json")
        if nome_npc:
            return npcs.get(nome_npc, {})
        return npcs
    
    def get_npc_conversation(self, nome_npc: str, stato: str = "inizio") -> Dict:
        """
        Ottieni la conversazione di un NPC per lo stato specificato.
        
        Args:
            nome_npc: Nome dell'NPC
            stato: Stato della conversazione
            
        Returns:
            dict: Dati della conversazione per lo stato specificato
        """
        conversations = self.load_data("npc", "conversations.json")
        npc_conversations = conversations.get(nome_npc)
        
        # Se non ci sono conversazioni specifiche per questo NPC, usa quelle di default
        if not npc_conversations:
            npc_conversations = conversations.get("default", {})
            
        # Restituisci la conversazione per lo stato specificato o quella iniziale
        return npc_conversations.get(stato, npc_conversations.get("inizio", {}))
    
    def get_all_npc_conversations(self, nome_npc: str) -> Dict:
        """
        Ottieni tutte le conversazioni di un NPC.
        
        Args:
            nome_npc: Nome dell'NPC
            
        Returns:
            dict: Tutte le conversazioni dell'NPC
        """
        conversations = self.load_data("npc", "conversations.json")
        return conversations.get(nome_npc, conversations.get("default", {}))
    
    def get_interactive_objects(self, nome_oggetto: Optional[str] = None) -> Union[Dict, List]:
        """
        Ottieni dati su uno o tutti gli oggetti interattivi.
        
        Args:
            nome_oggetto: Nome dell'oggetto specifico o None per tutti
            
        Returns:
            dict/list: Dati dell'oggetto o di tutti gli oggetti
        """
        oggetti = self.load_data("oggetti", "oggetti_interattivi.json")
        if nome_oggetto:
            if isinstance(oggetti, dict):
                return oggetti.get(nome_oggetto, {})
            else:
                for oggetto in oggetti:
                    if oggetto.get("nome") == nome_oggetto:
                        return oggetto
                return {}
        return oggetti
    
    def save_interactive_objects(self, oggetti: Union[Dict, List]) -> bool:
        """
        Salva i dati degli oggetti interattivi.
        
        Args:
            oggetti: Dati degli oggetti da salvare
            
        Returns:
            bool: True se il salvataggio è riuscito
        """
        return self.save_data("oggetti", oggetti, "oggetti_interattivi.json")
    
    def get_map_objects(self, nome_mappa: str) -> List:
        """
        Ottieni gli oggetti posizionati su una specifica mappa.
        
        Args:
            nome_mappa: Nome della mappa
            
        Returns:
            list: Lista di oggetti sulla mappa
        """
        mappe_oggetti = self.load_data("oggetti", "mappe_oggetti.json")
        
        # Verifica la coerenza delle posizioni (ma solo in modalità debug)
        if logging.getLogger().level == logging.DEBUG:
            self.verifica_posizioni_oggetti(nome_mappa, mappe_oggetti.get(nome_mappa, []))
        
        return mappe_oggetti.get(nome_mappa, [])
    
    def save_map_objects(self, nome_mappa: str, oggetti_posizioni: List) -> bool:
        """
        Salva le posizioni degli oggetti su una mappa.
        
        Args:
            nome_mappa: Nome della mappa
            oggetti_posizioni: Lista di oggetti con le loro posizioni
            
        Returns:
            bool: True se il salvataggio è riuscito
        """
        # Carica l'intero file
        mappe_oggetti = self.load_data("oggetti", "mappe_oggetti.json")
        
        # Aggiorna solo la mappa specifica
        mappe_oggetti[nome_mappa] = oggetti_posizioni
        
        # Verifica la validità delle posizioni prima del salvataggio
        oggetti_validi = self.verifica_posizioni_oggetti(nome_mappa, oggetti_posizioni)
        
        # Salva il file aggiornato
        return self.save_data("oggetti", mappe_oggetti, "mappe_oggetti.json")
    
    def verifica_posizioni_oggetti(self, nome_mappa: str, oggetti_posizioni: List) -> bool:
        """
        Verifica che le posizioni degli oggetti siano valide e non ci siano conflitti
        tra oggetti definiti in mappe_oggetti.json e quelli già presenti nella mappa.
        
        Args:
            nome_mappa: Nome della mappa da verificare
            oggetti_posizioni: Lista di oggetti con posizioni (opzionale, se None carica da mappe_oggetti.json)
            
        Returns:
            bool: True se tutte le posizioni sono valide
        """
        try:
            # Importa OggettiManager solo quando necessario per evitare dipendenze circolari
            from world.managers.oggetti_manager import OggettiManager
            oggetti_manager = OggettiManager()
            
            # Esegui la convalida
            valido, problemi, correzioni = oggetti_manager.convalida_posizioni_oggetti_mappa(nome_mappa)
            
            # Logga eventuali problemi
            if not valido:
                logging.warning(f"Rilevati {len(problemi)} conflitti di posizionamento sulla mappa {nome_mappa}:")
                for problema in problemi:
                    logging.warning(f"  - {problema}")
                    
                if correzioni:
                    logging.info("Correzioni suggerite:")
                    for correzione in correzioni:
                        oggetto = correzione["oggetto"]
                        pos_orig = correzione["posizione_originale"]
                        pos_nuova = correzione["posizione_suggerita"]
                        logging.info(f"  - Sposta '{oggetto}' da {pos_orig} a {pos_nuova}")
                        
                logging.info("Esegui 'python tools/valida_mappe_oggetti.py -c' per applicare automaticamente le correzioni")
            
            return valido
        except Exception as e:
            logging.error(f"Errore durante la verifica delle posizioni oggetti: {e}")
            return False
    
    def get_monsters(self, monster_id: Optional[str] = None) -> Union[Dict, List]:
        """
        Ottieni dati sui mostri.
        
        Args:
            monster_id: ID del mostro specifico o None per tutti
            
        Returns:
            dict/list: Dati del mostro o di tutti i mostri
        """
        monsters = self.load_data("mostri", "monsters.json")
        if monster_id:
            return monsters.get(monster_id, {})
        return monsters
        
    def get_map_data(self, map_id: str) -> Dict:
        """
        Ottieni dati su una mappa.
        
        Args:
            map_id: ID della mappa
            
        Returns:
            dict: Dati della mappa
        """
        file_name = f"{map_id}.json"
        return self.load_data("mappe", file_name)

    def verifica_directory_essenziali(self) -> Dict[str, bool]:
        """
        Verifica la presenza di tutte le directory essenziali per il funzionamento del gioco.
        
        Returns:
            Dict[str, bool]: Dizionario con chiave=nome directory e valore=True se esiste
        """
        stato_directory = {}
        
        for nome, percorso in self._data_paths.items():
            stato_directory[nome] = percorso.exists()
            if not percorso.exists():
                logger.warning(f"Directory essenziale mancante: {nome} ({percorso})")
                try:
                    percorso.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Creata directory mancante: {percorso}")
                    stato_directory[nome] = True
                except Exception as e:
                    logger.error(f"Impossibile creare directory {percorso}: {str(e)}")
        
        return stato_directory

    def diagnose_system_paths(self) -> Dict:
        """
        Diagnostica i problemi di percorso nel sistema.
        Verifica ogni percorso configurato e fornisce dettagli sullo stato.
        
        Returns:
            Dict: Dizionario con risultati della diagnostica per ogni percorso
        """
        result = {}
        
        # Controlla ogni percorso configurato
        for data_type, path in self._data_paths.items():
            # Costruisci un rapporto per questo tipo di dati
            report = {
                "path": str(path),
                "exists": path.exists(),
                "is_dir": path.is_dir() if path.exists() else False,
                "files": [],
                "json_files": [],
                "errors": []
            }
            
            # Se il percorso esiste, elenca i file
            if path.exists() and path.is_dir():
                try:
                    all_files = list(path.glob("*"))
                    report["files"] = [f.name for f in all_files]
                    report["json_files"] = [f.name for f in all_files if f.name.lower().endswith('.json')]
                    
                    # Verifica i file JSON
                    for json_file in [f for f in all_files if f.name.lower().endswith('.json')]:
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                json.load(f)
                        except Exception as e:
                            report["errors"].append(f"Errore nel file {json_file.name}: {str(e)}")
                except Exception as e:
                    report["errors"].append(f"Errore nell'elenco dei file: {str(e)}")
            
            result[data_type] = report
            
        # Aggiungi risultato globale
        result["_summary"] = {
            "valid_paths": sum(1 for r in result.values() if r.get("exists", False)),
            "total_paths": len(self._data_paths),
            "json_files_found": sum(len(r.get("json_files", [])) for r in result.values()),
            "errors_found": sum(len(r.get("errors", [])) for r in result.values())
        }
        
        return result

# Funzione helper per ottenere l'istanza del DataManager
def get_data_manager() -> DataManager:
    """
    Ottieni l'istanza singleton del DataManager.
    
    Returns:
        DataManager: Istanza del gestore dati
    """
    return DataManager() 