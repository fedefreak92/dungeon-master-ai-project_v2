import logging
from typing import Dict, Any, List, Set, Optional, Union

# Configura il logger
logger = logging.getLogger(__name__)

class Serializable:
    """
    Classe base per tutti gli oggetti serializzabili nel gioco.
    Fornisce metodi standardizzati per la conversione tra oggetti Python e formati JSON.
    """
    
    # Attributi da ignorare durante la serializzazione 
    # (ogni classe può estendere questa lista)
    _non_serializable_attrs: Set[str] = {"_non_serializable_attrs"}
    
    def to_dict(self, already_serialized: Optional[Set[int]] = None) -> Dict[str, Any]:
        """
        Converte l'oggetto in un dizionario serializzabile.
        
        Args:
            already_serialized: Set di id di oggetti già serializzati, per evitare riferimenti ciclici
            
        Returns:
            Dict[str, Any]: Dizionario contenente i dati dell'oggetto
        """
        # Inizializza il set per tracciare oggetti già serializzati (per evitare ricorsione infinita)
        if already_serialized is None:
            already_serialized = set()
            
        # Se questo oggetto è già stato serializzato, ritorna solo l'ID
        obj_id = id(self)
        if obj_id in already_serialized:
            return {"_ref_id": obj_id, "_class": self.__class__.__name__}
            
        # Aggiungi questo oggetto al set degli oggetti già serializzati
        already_serialized.add(obj_id)
        
        # Dizionario risultato
        result = {"_class": self.__class__.__name__}
        
        # Serializza gli attributi
        for key, value in self.__dict__.items():
            # Salta attributi privati e quelli nella lista di esclusione
            if key.startswith('_') or key in self._non_serializable_attrs:
                continue
                
            result[key] = self._serialize_value(value, already_serialized)
                
        return result
    
    def _serialize_value(self, value: Any, already_serialized: Set[int]) -> Any:
        """
        Serializza un singolo valore in modo appropriato in base al suo tipo.
        
        Args:
            value: Valore da serializzare
            already_serialized: Set di oggetti già serializzati
            
        Returns:
            Any: Valore serializzato
        """
        # Gestisci tipi primitivi che sono già serializzabili
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
            
        # Gestisci oggetti Serializable
        if isinstance(value, Serializable):
            return value.to_dict(already_serialized)
            
        # Gestisci oggetti con metodo to_dict personalizzato
        if hasattr(value, 'to_dict') and callable(getattr(value, 'to_dict')):
            try:
                # Prova prima con il parametro already_serialized
                return value.to_dict(already_serialized)
            except TypeError:
                # Se fallisce, prova senza parametri
                return value.to_dict()
        
        # Gestisci liste e tuple
        if isinstance(value, (list, tuple)):
            return [self._serialize_value(item, already_serialized) for item in value]
            
        # Gestisci dizionari
        if isinstance(value, dict):
            return {
                str(k): self._serialize_value(v, already_serialized) 
                for k, v in value.items()
            }
            
        # Per altri tipi complessi, usa la rappresentazione come stringa
        try:
            # Se esiste un attributo 'nome', usalo come rappresentazione semplificata
            if hasattr(value, 'nome'):
                return str(value.nome)
            # Altrimenti usa la rappresentazione standard come stringa
            return str(value)
        except Exception as e:
            logger.warning(f"Impossibile serializzare {type(value)}: {e}")
            return None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], object_registry: Optional[Dict[int, Any]] = None) -> 'Serializable':
        """
        Crea un'istanza della classe a partire da un dizionario.
        
        Args:
            data: Dizionario con i dati dell'oggetto
            object_registry: Registro di oggetti già deserializzati
            
        Returns:
            Serializable: Istanza della classe
        """
        if object_registry is None:
            object_registry = {}
            
        # Se è un riferimento a un oggetto già creato, restituiscilo
        if "_ref_id" in data:
            ref_id = data["_ref_id"]
            if ref_id in object_registry:
                return object_registry[ref_id]
            # Se non troviamo l'oggetto, ritorna None
            logger.warning(f"Riferimento a oggetto non trovato: {ref_id}")
            return None
            
        # Crea una nuova istanza
        instance = cls()
        
        # Salva l'istanza nel registro
        if "_id" in data:
            object_registry[data["_id"]] = instance
            
        # Popola gli attributi
        for key, value in data.items():
            # Salta i campi speciali
            if key in ("_class", "_id", "_ref_id"):
                continue
                
            # Deserializza il valore
            setattr(instance, key, cls._deserialize_value(value, object_registry))
            
        return instance
    
    @classmethod
    def _deserialize_value(cls, value: Any, object_registry: Dict[int, Any]) -> Any:
        """
        Deserializza un singolo valore.
        
        Args:
            value: Valore da deserializzare
            object_registry: Registro di oggetti già deserializzati
            
        Returns:
            Any: Valore deserializzato
        """
        # Gestisci valori primitivi
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
            
        # Gestisci liste
        if isinstance(value, list):
            return [cls._deserialize_value(item, object_registry) for item in value]
            
        # Gestisci dizionari
        if isinstance(value, dict):
            # Se il dizionario rappresenta un oggetto serializzato
            if "_class" in value:
                # Verifica se l'oggetto è già stato creato
                if "_ref_id" in value and value["_ref_id"] in object_registry:
                    return object_registry[value["_ref_id"]]
                    
                # Altrimenti crea una nuova istanza
                # Questo richiede che le classi siano registrate in un registry globale
                from util.class_registry import get_class
                cls_name = value["_class"]
                obj_class = get_class(cls_name)
                
                if obj_class and hasattr(obj_class, 'from_dict'):
                    return obj_class.from_dict(value, object_registry)
                    
                # Se la classe non è trovata, ritorna il dizionario originale
                logger.warning(f"Classe non trovata durante la deserializzazione: {cls_name}")
                return value
                
            # Dizionario normale
            return {
                k: cls._deserialize_value(v, object_registry)
                for k, v in value.items()
            }
            
        # Per altri tipi di valore, ritorna il valore originale
        return value 