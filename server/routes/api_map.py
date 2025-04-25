from flask import Blueprint, jsonify, request
import os
import json
import logging

# Configura il logger
logger = logging.getLogger(__name__)

# Crea il blueprint
api_map = Blueprint('api_map', __name__)

@api_map.route('/current', methods=['GET'])
def get_current_map():
    """
    Restituisce la mappa corrente caricata dal server.
    
    Returns:
        json: Dati della mappa corrente
    """
    logger.info("API current map chiamata")
    try:
        # Ottieni l'ID della mappa dai parametri di query (opzionale)
        map_id = request.args.get('id', 'default_map')
        
        # Calcola il percorso della directory delle mappe
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        maps_dir = os.path.join(base_dir, 'data', 'maps')
        
        # Verifica se la mappa esiste
        map_file = os.path.join(maps_dir, f"{map_id}.json")
        
        if os.path.exists(map_file):
            # Se la mappa esiste, caricala
            with open(map_file, 'r', encoding='utf-8') as f:
                map_data = json.load(f)
                
                # Assicura compatibilità con più formati di test
                # Restituisci sia il formato map.layers che layers
                response = {
                    "map": map_data,
                    "id": map_data.get("id", map_id),
                    "name": map_data.get("name", map_id),
                    "layers": map_data.get("layers", {})
                }
                
                return jsonify(response)
        else:
            logger.warning(f"File mappa non trovato: {map_file}. Uso mappa di esempio.")
            # Restituisci una mappa di esempio se quella richiesta non esiste
            example_map = {
                "id": map_id,
                "name": "Mappa di Esempio",
                "width": 20,
                "height": 15,
                "layers": {
                    "ground": [
                        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                        [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
                        [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
                        [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
                        [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
                        [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
                        [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
                        [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
                        [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
                        [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
                        [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
                        [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
                        [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
                        [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
                        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
                    ],
                    "walls": [
                        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                        [1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1],
                        [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
                        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                        [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
                        [1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1],
                        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
                    ],
                    "objects": [
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    ]
                },
                "spawn_points": {
                    "player": {"x": 5, "y": 5},
                    "npcs": [
                        {"id": "npc_1", "x": 8, "y": 3, "type": "villager"},
                        {"id": "npc_2", "x": 15, "y": 8, "type": "merchant"}
                    ]
                },
                "tile_types": {
                    "ground": {
                        "1": {"name": "stone", "walkable": True, "sprite": "stone_floor"},
                        "2": {"name": "grass", "walkable": True, "sprite": "grass_floor"}
                    },
                    "walls": {
                        "1": {"name": "wall", "walkable": False, "sprite": "stone_wall"}
                    },
                    "objects": {
                        "3": {"name": "chest", "walkable": False, "sprite": "chest", "interactive": True}
                    }
                }
            }
            
            # Formato compatibile con i test
            response = {
                "map": example_map,
                "id": example_map["id"],
                "name": example_map["name"],
                "layers": example_map["layers"]
            }
            
            return jsonify(response)
    except Exception as e:
        logger.error(f"Errore durante il recupero della mappa corrente: {e}")
        return jsonify({
            "successo": False,
            "errore": str(e)
        }), 500

@api_map.route('/list', methods=['GET'])
def list_maps():
    """
    Elenca tutte le mappe disponibili nel sistema.
    
    Returns:
        json: Lista delle mappe disponibili
    """
    logger.info("API list maps chiamata")
    try:
        # Calcola il percorso della directory delle mappe
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        maps_dir = os.path.join(base_dir, 'data', 'maps')
        
        # Verifica se la directory delle mappe esiste
        if not os.path.exists(maps_dir) or not os.path.isdir(maps_dir):
            logger.warning(f"Directory delle mappe non trovata: {maps_dir}")
            return jsonify({
                "maps": []
            })
        
        # Elenca le mappe disponibili
        maps = []
        for filename in os.listdir(maps_dir):
            if filename.endswith('.json'):
                map_id = os.path.splitext(filename)[0]
                map_path = os.path.join(maps_dir, filename)
                
                # Carica i metadati della mappa
                try:
                    with open(map_path, 'r', encoding='utf-8') as f:
                        map_data = json.load(f)
                        maps.append({
                            "id": map_id,
                            "name": map_data.get("name", map_id),
                            "width": map_data.get("width", 0),
                            "height": map_data.get("height", 0)
                        })
                except Exception as e:
                    logger.error(f"Errore nel caricamento della mappa {filename}: {e}")
                    maps.append({
                        "id": map_id,
                        "name": map_id,
                        "error": str(e)
                    })
        
        return jsonify({
            "maps": maps
        })
    except Exception as e:
        logger.error(f"Errore durante l'elenco delle mappe: {e}")
        return jsonify({
            "successo": False,
            "errore": str(e)
        }), 500 