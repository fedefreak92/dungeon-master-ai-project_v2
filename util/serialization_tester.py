import logging
import json
import argparse
from typing import Dict, Any, List, Optional, Union, Set

# Importa il sistema di serializzazione
from util.serializable import Serializable
from util.class_registry import register_class, get_class, auto_register_decoratore

# Configura il logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@auto_register_decoratore
class TestEntity(Serializable):
    """
    Classe di test per verificare il sistema di serializzazione.
    """
    
    def __init__(self, name: str = "", value: int = 0):
        self.name = name
        self.value = value
        self.children = []
        self._private_attr = "questo non deve essere serializzato"

@auto_register_decoratore
class ChildEntity(Serializable):
    """
    Classe figlio per test annidati.
    """
    
    def __init__(self, id: str = "", description: str = ""):
        self.id = id
        self.description = description
        self.parent = None  # Riferimento al genitore (potenziale riferimento circolare)

def create_test_entities() -> List[TestEntity]:
    """
    Crea entità di test con varie configurazioni per verificare la serializzazione.
    
    Returns:
        List[TestEntity]: Lista di entità di test
    """
    # Entità semplice
    entity1 = TestEntity("Test Entity 1", 100)
    
    # Entità con figli
    entity2 = TestEntity("Test Entity 2", 200)
    
    # Aggiungi figli a entity2
    child1 = ChildEntity("child1", "First child")
    child1.parent = entity2  # Crea un riferimento circolare
    
    child2 = ChildEntity("child2", "Second child")
    child2.parent = entity2  # Crea un riferimento circolare
    
    entity2.children = [child1, child2]
    
    # Entità con strutture dati complesse
    entity3 = TestEntity("Test Entity 3", 300)
    entity3.data = {
        "list": [1, 2, 3, 4],
        "dict": {"a": 1, "b": 2},
        "nested": {
            "x": [{"y": 10}]
        }
    }
    entity3.tuple_data = (1, 2, 3)  # Test conversione tuple
    
    # Entità che fa riferimento ad altre entità
    entity4 = TestEntity("Test Entity 4", 400)
    entity4.reference = entity1  # Riferimento a un'altra entità
    entity4.references = [entity2, entity3]  # Lista di riferimenti
    
    return [entity1, entity2, entity3, entity4]

def test_serialization(verbose: bool = False):
    """
    Esegue un test completo del sistema di serializzazione.
    
    Args:
        verbose: Se True, mostra output dettagliato
    """
    logger.info("Avvio test di serializzazione...")
    
    # Crea entità di test
    entities = create_test_entities()
    
    # Serializza le entità
    serialized = []
    for i, entity in enumerate(entities):
        serialized_data = entity.to_dict()
        serialized.append(serialized_data)
        
        if verbose:
            logger.info(f"Entità {i+1} serializzata:")
            logger.info(json.dumps(serialized_data, indent=2))
    
    # Verifica che tutte le entità siano state serializzate
    logger.info(f"Serializzate {len(serialized)} entità")
    
    # Deserializza le entità
    deserialized = []
    for i, data in enumerate(serialized):
        try:
            # Ottieni la classe dal campo _class
            class_name = data.get("_class", "TestEntity")
            cls = get_class(class_name)
            
            if cls:
                entity = cls.from_dict(data)
                deserialized.append(entity)
                logger.info(f"Entità {i+1} deserializzata con successo")
            else:
                logger.error(f"Classe non trovata: {class_name}")
        except Exception as e:
            logger.error(f"Errore nella deserializzazione dell'entità {i+1}: {str(e)}")
    
    # Verifica che tutte le entità siano state deserializzate
    logger.info(f"Deserializzate {len(deserialized)} entità")
    
    # Verifica la correttezza dei dati dopo la deserializzazione
    for i, (original, deserialized_entity) in enumerate(zip(entities, deserialized)):
        # Confronta i valori principali
        if original.name != deserialized_entity.name or original.value != deserialized_entity.value:
            logger.error(f"I dati dell'entità {i+1} non corrispondono dopo la deserializzazione")
        else:
            logger.info(f"I dati principali dell'entità {i+1} sono stati preservati")
    
    # Verifica dei riferimenti ciclici in entity2
    if len(entities) > 1 and len(deserialized) > 1:
        entity2 = entities[1]
        deserialized_entity2 = deserialized[1]
        
        if hasattr(deserialized_entity2, 'children') and deserialized_entity2.children:
            child = deserialized_entity2.children[0]
            if hasattr(child, 'parent') and child.parent is deserialized_entity2:
                logger.info("I riferimenti ciclici sono stati preservati correttamente")
            else:
                logger.warning("I riferimenti ciclici potrebbero non essere stati preservati")
    
    logger.info("Test di serializzazione completato")

def main():
    """Funzione principale per l'esecuzione da linea di comando."""
    parser = argparse.ArgumentParser(description="Testa il sistema di serializzazione.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Mostra output dettagliato")
    
    args = parser.parse_args()
    
    # Esegui il test
    test_serialization(args.verbose)

if __name__ == "__main__":
    main() 