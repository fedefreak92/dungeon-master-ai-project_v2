import logging
from typing import Dict, Type, Any, Optional
import os
import json

# Configura il logger
logger = logging.getLogger(__name__)

# Registro globale delle classi
_class_registry: Dict[str, Type] = {}
# Cache delle classi caricate dal file JSON
_classi_personaggio_cache: Dict[str, Dict] = {}

def register_class(cls: Type, name: Optional[str] = None) -> None:
    """
    Registra una classe nel registry globale.
    
    Args:
        cls: Classe da registrare
        name: Nome con cui registrare la classe (default: nome della classe)
    """
    class_name = name or cls.__name__
    _class_registry[class_name] = cls
    logger.debug(f"Classe registrata: {class_name}")

def get_class(class_name: str) -> Optional[Type]:
    """
    Ottiene una classe dal registro.
    
    Args:
        class_name: Nome della classe
        
    Returns:
        Type: Classe richiesta o None se non trovata
    """
    if class_name in _class_registry:
        return _class_registry[class_name]
    
    # Cerca in tutti i moduli caricati
    import sys
    for module_name, module in sys.modules.items():
        if module_name.startswith('gioco_rpg'):
            for attr_name in dir(module):
                if attr_name == class_name:
                    try:
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type):
                            logger.debug(f"Classe {class_name} trovata in {module_name}")
                            register_class(attr)
                            return attr
                    except Exception as e:
                        logger.debug(f"Errore durante il caricamento della classe {class_name} da {module_name}: {e}")
                        
    logger.warning(f"Classe non trovata: {class_name}")
    return None

def auto_register_decoratore(cls: Type) -> Type:
    """
    Decoratore per registrare automaticamente una classe.
    
    Args:
        cls: Classe da registrare
        
    Returns:
        Type: La stessa classe, per permettere l'uso come decoratore
    """
    register_class(cls)
    return cls

def get_player_class(class_name: str) -> Dict:
    """
    Ottiene la definizione di una classe personaggio dal file classes.json.
    
    Args:
        class_name: Nome della classe personaggio (es. 'guerriero', 'mago', ecc.)
        
    Returns:
        Dict: Definizione della classe o dizionario vuoto se non trovata
    """
    # Controlla se la classe è già in cache
    class_name = class_name.lower()
    if class_name in _classi_personaggio_cache:
        return _classi_personaggio_cache[class_name]
    
    # Percorso del file delle classi
    try:
        from util.data_manager import get_data_manager
        data_manager = get_data_manager()
        classi = data_manager.load_data("classes", "classes.json")
        
        if classi and class_name in classi:
            # Aggiungi l'id alla definizione della classe
            classe_def = classi[class_name].copy()
            classe_def["id"] = class_name
            classe_def["nome"] = class_name.capitalize()
            
            # Salva in cache
            _classi_personaggio_cache[class_name] = classe_def
            return classe_def
    except Exception as e:
        logger.error(f"Errore nel caricamento della classe {class_name} da classes.json: {e}")
    
    # Se non trovata, restituisci una definizione base
    return {
        "id": class_name,
        "nome": class_name.capitalize(),
        "descrizione": f"Classe {class_name.capitalize()}"
    }

def load_all_player_classes() -> Dict[str, Dict]:
    """
    Carica tutte le definizioni delle classi personaggio.
    
    Returns:
        Dict[str, Dict]: Mappatura delle classi personaggio
    """
    try:
        from util.data_manager import get_data_manager
        data_manager = get_data_manager()
        classi = data_manager.load_data("classes", "classes.json")
        
        # Aggiungi l'id a ogni definizione
        for nome, definizione in classi.items():
            definizione_copia = definizione.copy()
            definizione_copia["id"] = nome
            definizione_copia["nome"] = nome.capitalize()
            _classi_personaggio_cache[nome] = definizione_copia
        
        return _classi_personaggio_cache
    except Exception as e:
        logger.error(f"Errore nel caricamento di tutte le classi personaggio: {e}")
        return {} 