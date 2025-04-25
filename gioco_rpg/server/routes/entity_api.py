from flask import Blueprint, jsonify
import os
import json
import logging

# Configura il logger
logger = logging.getLogger(__name__)

# Crea il blueprint
entity_api = Blueprint('entity_api', __name__)

@entity_api.route('/entities', methods=['GET'])
def get_entities():
    """
    Recupera le entità disponibili nel sistema.
    
    Returns:
        json: Entità disponibili
    """
    try:
        # Calcola il percorso delle directory delle entità
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        entity_dirs = {
            "monsters": os.path.join(base_dir, "data", "monsters"),
            "npcs": os.path.join(base_dir, "data", "npcs"),
            "items": os.path.join(base_dir, "data", "items")
        }
        
        # Raccogli le entità
        entities = {}
        
        # Per ogni tipo di entità
        for entity_type, directory in entity_dirs.items():
            entities[entity_type] = []
            
            # Verifica se la directory esiste
            if os.path.exists(directory) and os.path.isdir(directory):
                # Elenca i file nella directory
                for filename in os.listdir(directory):
                    if filename.endswith('.json'):
                        entity_id = os.path.splitext(filename)[0]
                        entity_path = os.path.join(directory, filename)
                        
                        # Carica i metadati dell'entità
                        try:
                            with open(entity_path, 'r', encoding='utf-8') as f:
                                entity_data = json.load(f)
                                entities[entity_type].append({
                                    "id": entity_id,
                                    "name": entity_data.get("name", entity_id),
                                    **{k: v for k, v in entity_data.items() if k not in ["id", "name"]}
                                })
                        except Exception as e:
                            logger.error(f"Errore nel caricamento dell'entità {filename}: {e}")
                            entities[entity_type].append({
                                "id": entity_id,
                                "error": str(e)
                            })
            else:
                logger.warning(f"Directory {entity_type} non trovata: {directory}")
                # Aggiungi entità di esempio se la directory non esiste
                if entity_type == "monsters":
                    entities[entity_type] = [
                        {"id": "goblin", "name": "Goblin", "hp": 20, "attack": 5, "defense": 2},
                        {"id": "troll", "name": "Troll", "hp": 50, "attack": 10, "defense": 5}
                    ]
                elif entity_type == "npcs":
                    entities[entity_type] = [
                        {"id": "villager", "name": "Villager", "type": "friendly", "dialog": ["Hello!", "Nice day!"]},
                        {"id": "merchant", "name": "Merchant", "type": "vendor", "wares": ["potion", "sword"]}
                    ]
                elif entity_type == "items":
                    entities[entity_type] = [
                        {"id": "potion", "name": "Health Potion", "type": "consumable", "effect": "heal", "value": 20},
                        {"id": "sword", "name": "Iron Sword", "type": "weapon", "damage": 10, "value": 100}
                    ]
        
        # Restituisci anche una lista di entità per il rendering
        active_entities = []
        for entity_type in ["npcs", "monsters"]:
            for entity in entities.get(entity_type, []):
                # Creiamo un oggetto entità per il rendering
                active_entities.append({
                    "id": entity.get("id", "unknown"),
                    "tipo": entity_type[:-1],  # rimuovi 's' finale
                    "type": entity_type[:-1],  # campo aggiuntivo per compatibilità test
                    "nome": entity.get("name", entity.get("id", "Unknown")),
                    "x": 5,  # posizione di default
                    "y": 5,  # posizione di default
                    "position": {"x": 5, "y": 5},  # posizione formattata per compatibilità test
                    "spriteId": entity.get("id", "unknown")
                })
        
        # Aggiungi il giocatore
        active_entities.insert(0, {
            "id": "player_1",
            "tipo": "player",
            "type": "player",
            "nome": "Giocatore",
            "x": 5,
            "y": 5,
            "position": {"x": 5, "y": 5},
            "spriteId": "player"
        })
        
        return jsonify({
            "entities": active_entities,
            "entity_database": entities
        })
    except Exception as e:
        error_msg = f"Errore durante il recupero delle entità: {str(e)}"
        logger.error(error_msg)
        
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500 