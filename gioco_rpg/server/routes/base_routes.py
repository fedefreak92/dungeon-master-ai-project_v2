from flask import jsonify, Blueprint
import time
import json
import os

# Crea il blueprint per le route di base
base_routes = Blueprint('base_routes', __name__)

@base_routes.route("/")
def home():
    """Pagina principale dell'API"""
    return jsonify({
        "nome": "API Gioco RPG",
        "versione": "2.0.0",
        "descrizione": "API per il gioco RPG con architettura ECS",
        "endpoints": {
            "GET /": "Informazioni sull'API",
            "GET /ping": "Verifica connessione",
            "GET /game/classes": "Ottieni classi disponibili",
            "GET /game/save/elenco": "Ottieni lista salvataggi",
            "POST /game/save/elimina": "Elimina un salvataggio",
            "POST /game/save/salva": "Salva il mondo di gioco",
            "POST /game/save/carica": "Carica un salvataggio",
            "POST /game/session/inizia": "Inizia una nuova sessione",
            "POST /game/skill_challenge/inizia": "Inizia una prova di abilità",
            "GET /game/skill_challenge/abilita_disponibili": "Ottieni abilità disponibili",
            "POST /game/skill_challenge/esegui": "Esegui una prova di abilità",
            "POST /game/skill_challenge/termina": "Termina una prova di abilità",
            "POST /game/combat/inizia": "Inizia un combattimento",
            "GET /game/combat/stato": "Ottieni stato del combattimento",
            "POST /game/combat/azione": "Esegui un'azione in combattimento",
            "POST /game/combat/termina": "Termina un combattimento",
            "GET /assets/info": "Ottieni informazioni sugli asset disponibili",
            "POST /assets/update": "Aggiorna le informazioni sugli asset",
            "GET /assets/file/<path:asset_path>": "Ottiene un file asset specifico"
        },
        "websocket": {
            "eventi": {
                "connect": "Connessione WebSocket",
                "disconnect": "Disconnessione WebSocket",
                "join_game": "Partecipa a una sessione di gioco",
                "game_event": "Invia un evento di gioco",
                "request_map_data": "Richiedi dati mappa"
            }
        }
    })

@base_routes.route("/ping")
def ping():
    """Verifica che il server sia attivo"""
    return jsonify({
        "stato": "online",
        "timestamp": time.time()
    })

@base_routes.route("/game/classes")
def get_classes():
    """Restituisce le classi disponibili"""
    try:
        # Percorso del file delle classi
        classes_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                    "data", "classes", "classes.json")
        
        # Carica il file JSON
        with open(classes_file, 'r', encoding='utf-8') as f:
            classes_data = json.load(f)
        
        # Formatta i dati per il frontend
        classes_list = []
        for class_id, class_info in classes_data.items():
            classes_list.append({
                "id": class_id,
                "nome": class_id.capitalize(),  # Capitalizza il nome come workaround
                "descrizione": class_info.get("descrizione", "")
            })
        
        return jsonify({
            "successo": True,
            "classi": classes_list
        })
    except Exception as e:
        return jsonify({
            "successo": False,
            "errore": f"Impossibile caricare le classi: {str(e)}"
        }), 500 