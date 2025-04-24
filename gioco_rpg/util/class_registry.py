import logging
from typing import Dict, Type, Any, Optional

# Configura il logger
logger = logging.getLogger(__name__)

# Registro globale delle classi
_class_registry: Dict[str, Type] = {}

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