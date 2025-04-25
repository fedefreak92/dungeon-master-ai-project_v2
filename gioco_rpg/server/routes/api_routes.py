"""
Definizione delle rotte API per il server.
Gestisce tutte le richieste HTTP API.
"""

from flask import Blueprint, jsonify, request, current_app
import logging
import time
from datetime import datetime

# Configura logger
logger = logging.getLogger(__name__)

# Crea il blueprint per le API
api_blueprint = Blueprint('api', __name__, url_prefix='/api')

# Timestamp di avvio per calcolare l'uptime
start_time = time.time()

# ---- Rotte di base ----

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """Ritorna lo stato di salute del server."""
    logger.debug("Richiesta health check ricevuta")
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    })

@api_blueprint.route('/entities', methods=['GET'])
def get_entities():
    """Ritorna tutte le entità nel gioco."""
    logger.debug("Richiesta entities ricevuta")
    
    # Ottieni il game manager (o mock se in modalità test)
    game_manager = getattr(current_app, 'game_manager', None)
    
    # Se non c'è un game manager, ritorna dati di esempio
    if not game_manager:
        logger.warning("Game manager non disponibile, ritorno dati di esempio")
        return jsonify({
            "entities": [
                {
                    "id": "player_1",
                    "type": "player",
                    "position": {"x": 5, "y": 5},
                    "state": "idle"
                },
                {
                    "id": "npc_1",
                    "type": "npc",
                    "position": {"x": 10, "y": 8},
                    "state": "patrol"
                }
            ]
        })
    
    # Se c'è un game manager, ottieni le entità reali
    try:
        entities = game_manager.get_all_entities()
        return jsonify({"entities": entities})
    except Exception as e:
        logger.error(f"Errore nel recupero delle entità: {e}")
        return jsonify({
            "status": "error",
            "message": "Impossibile recuperare le entità",
            "entities": []
        }), 500

@api_blueprint.route('/current_map', methods=['GET'])
def get_current_map():
    """Ritorna i dati della mappa corrente."""
    logger.debug("Richiesta current_map ricevuta")
    
    # Ottieni il game manager (o mock se in modalità test)
    game_manager = getattr(current_app, 'game_manager', None)
    
    # Se non c'è un game manager, ritorna dati di esempio
    if not game_manager:
        logger.warning("Game manager non disponibile, ritorno dati mappa di esempio")
        return jsonify({
            "map": {
                "id": "starting_village",
                "name": "Villaggio Iniziale",
                "width": 20,
                "height": 15,
                "tileset": "village",
                "layers": [
                    {
                        "name": "ground",
                        "visible": True,
                        "data": [[0] * 20 for _ in range(15)]
                    },
                    {
                        "name": "objects",
                        "visible": True,
                        "data": [[0] * 20 for _ in range(15)]
                    }
                ]
            }
        })
    
    # Se c'è un game manager, ottieni i dati reali della mappa
    try:
        current_map = game_manager.get_current_map()
        return jsonify({"map": current_map})
    except Exception as e:
        logger.error(f"Errore nel recupero della mappa corrente: {e}")
        return jsonify({
            "status": "error",
            "message": "Impossibile recuperare la mappa corrente",
            "map": None
        }), 500

@api_blueprint.route('/diagnostics/frontend', methods=['GET'])
def get_frontend_diagnostics():
    """Ritorna i dati diagnostici per il frontend."""
    logger.debug("Richiesta diagnostics/frontend ricevuta")
    
    # Calcola l'uptime
    uptime_seconds = time.time() - start_time
    
    # Raccogli le statistiche
    stats = {
        "status": "ok",
        "version": "0.1.0",
        "uptime": uptime_seconds,
        "memory_usage": {
            "unit": "MB",
            "value": 128.5  # Valore di esempio
        },
        "connections": {
            "websocket": getattr(current_app, 'websocket_connections', 0),
            "http": getattr(current_app, 'http_connections', 0)
        },
        "timestamp": datetime.now().isoformat()
    }
    
    return jsonify(stats)

# ---- Altre rotte API ----

@api_blueprint.route('/player/move', methods=['POST'])
def player_move():
    """Gestisce il movimento del giocatore."""
    data = request.json
    logger.debug(f"Richiesta di movimento del giocatore: {data}")
    
    # Validazione dell'input
    if not data or 'direction' not in data:
        return jsonify({
            "status": "error",
            "message": "Manca il parametro direction"
        }), 400
    
    direction = data['direction']
    valid_directions = ['up', 'down', 'left', 'right']
    
    if direction not in valid_directions:
        return jsonify({
            "status": "error",
            "message": f"Direzione non valida. Usare uno di: {', '.join(valid_directions)}"
        }), 400
    
    # Ottieni il game manager
    game_manager = getattr(current_app, 'game_manager', None)
    
    # Se non c'è un game manager, ritorna errore
    if not game_manager:
        logger.warning("Game manager non disponibile per il movimento del giocatore")
        return jsonify({
            "status": "error",
            "message": "Sistema di gioco non disponibile"
        }), 503
    
    # Movimento effettivo
    try:
        result = game_manager.move_player(direction)
        return jsonify({
            "status": "success",
            "direction": direction,
            "position": result["position"]
        })
    except Exception as e:
        logger.error(f"Errore nel movimento del giocatore: {e}")
        return jsonify({
            "status": "error",
            "message": f"Impossibile muovere il giocatore: {str(e)}"
        }), 500

@api_blueprint.route('/assets/list', methods=['GET'])
def list_assets():
    """Ritorna l'elenco degli asset disponibili."""
    logger.debug("Richiesta di elenco asset ricevuta")
    
    # Ottieni il gestore degli asset
    asset_manager = getattr(current_app, 'asset_manager', None)
    
    # Se non c'è un asset manager, ritorna dati di esempio
    if not asset_manager:
        logger.warning("Asset manager non disponibile, ritorno dati di esempio")
        return jsonify({
            "assets": {
                "sprites": ["player.png", "npc.png", "objects.png"],
                "tilemaps": ["village.png", "dungeon.png", "forest.png"],
                "audio": ["background.mp3", "effects.mp3"]
            }
        })
    
    # Se c'è un asset manager, ottieni i dati reali
    try:
        assets = asset_manager.get_all_assets()
        return jsonify({"assets": assets})
    except Exception as e:
        logger.error(f"Errore nel recupero degli asset: {e}")
        return jsonify({
            "status": "error",
            "message": "Impossibile recuperare l'elenco degli asset",
            "assets": {}
        }), 500

# Altre rotte possono essere aggiunte qui