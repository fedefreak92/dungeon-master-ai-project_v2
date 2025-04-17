from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from flask_socketio import SocketIO
import os
import logging
import json
import sys
from werkzeug.exceptions import BadRequest
import datetime

# Aggiungi il percorso della directory principale al sys.path per assicurarsi che tutti i moduli siano importabili
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
    print(f"Aggiunto {current_dir} al sys.path")

# Import moduli locali
from server.routes.base_routes import base_routes
from server.routes import register_game_routes
from server.routes.assets_routes import assets_routes
from server.websocket import init_websocket_handlers
from server.utils.session import set_socketio
from util.config import SESSIONS_DIR, SAVE_DIR, BACKUPS_DIR
from util.asset_manager import get_asset_manager
from core.graphics_renderer import GraphicsRenderer

# Configura il logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Crea e configura l'app Flask"""
    app = Flask(__name__)
    
    # Configurazione CORS più dettagliata
    cors_config = {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": [
            "Content-Type", 
            "Authorization", 
            "X-Requested-With", 
            "Cache-Control",
            "Accept",
            "Origin",
            "Pragma",
            "Expires",
            "If-Modified-Since"
        ],
        "supports_credentials": True,
        "max_age": 86400  # Cache preflight per 24 ore
    }
    
    CORS(app, resources={r"/*": cors_config})
    
    # Aggiungi route statica per gli asset
    @app.route('/assets/<path:path>', methods=['GET'])
    def serve_assets(path):
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets')
        logger.info(f"Richiesta asset: {path}, cercando in {assets_dir}")
        
        # Controllo di sicurezza per evitare path traversal
        full_path = os.path.join(assets_dir, path)
        if not os.path.normpath(full_path).startswith(os.path.normpath(assets_dir)):
            logger.warning(f"Tentativo di path traversal bloccato: {path}")
            return jsonify({"successo": False, "errore": "Accesso non autorizzato"}), 403
            
        # Verifica che il file esista
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            logger.warning(f"Asset non trovato: {full_path}")
            return jsonify({"successo": False, "errore": "File non trovato"}), 404
            
        # Serve il file
        return send_file(full_path)
    
    # Aggiungi route per servire i file statici della webapp
    @app.route('/<path:path>', methods=['GET'])
    def serve_static_files(path):
        frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend', 'public')
        logger.info(f"Richiesta file statico: {path}, cercando in {frontend_dir}")
        
        # Controllo di sicurezza per evitare path traversal
        full_path = os.path.join(frontend_dir, path)
        if not os.path.normpath(full_path).startswith(os.path.normpath(frontend_dir)):
            logger.warning(f"Tentativo di path traversal bloccato: {path}")
            return jsonify({"successo": False, "errore": "Accesso non autorizzato"}), 403
            
        # Verifica che il file esista
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            logger.warning(f"File statico non trovato: {full_path}")
            # Se il file richiesto è una favicon o un'immagine mancante, servi un'immagine placeholder
            if path.endswith('.ico') or path.endswith('.png'):
                placeholder_path = os.path.join(frontend_dir, 'assets', 'fallback', 'placeholder.png')
                if os.path.exists(placeholder_path):
                    return send_file(placeholder_path)
            return jsonify({"successo": False, "errore": "File non trovato"}), 404
            
        # Serve il file
        return send_file(full_path)
    
    # Aggiungi route esplicita per API REST
    @app.route('/api/maps', methods=['GET'])
    def get_maps_api():
        logger.info("Richiesta API per le mappe")
        try:
            # Ottieni directory delle mappe
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            maps_dir = os.path.join(base_dir, "data", "mappe")
            
            # Verifica se la directory esiste
            if not os.path.exists(maps_dir):
                logger.warning(f"Directory mappe non trovata: {maps_dir}")
                return jsonify({"successo": False, "errore": "Directory mappe non trovata"}), 404
                
            # Lista i file delle mappe
            map_files = [f.replace('.json', '') for f in os.listdir(maps_dir) if f.endswith('.json')]
            logger.info(f"Mappe trovate: {map_files}")
            
            return jsonify({
                "successo": True,
                "mappe": map_files
            })
        except Exception as e:
            logger.error(f"Errore nell'API mappe: {e}")
            return jsonify({"successo": False, "errore": str(e)}), 500
    
    # Aggiungi route per API sessions
    @app.route('/api/sessions', methods=['GET'])
    def get_sessions_api():
        logger.info("Richiesta API per le sessioni")
        try:
            # Ottieni directory delle sessioni
            sessions_dir = SESSIONS_DIR
            
            # Verifica se la directory esiste
            if not os.path.exists(sessions_dir):
                logger.warning(f"Directory sessioni non trovata: {sessions_dir}")
                return jsonify({"successo": False, "errore": "Directory sessioni non trovata"}), 404
                
            # Lista i file delle sessioni
            session_files = [f.replace('.json', '') for f in os.listdir(sessions_dir) if f.endswith('.json')]
            logger.info(f"Sessioni trovate: {session_files}")
            
            return jsonify({
                "successo": True,
                "sessioni": session_files
            })
        except Exception as e:
            logger.error(f"Errore nell'API sessioni: {e}")
            return jsonify({"successo": False, "errore": str(e)}), 500
    
    # Aggiungi route per API assets/info
    @app.route('/api/assets/info', methods=['GET'])
    def get_assets_info_api():
        logger.info("Richiesta API per le informazioni sugli asset")
        try:
            asset_manager = get_asset_manager()
            
            # Ottieni informazioni sugli asset
            assets_summary = {
                "sprites": {
                    "count": len(asset_manager.get_all_sprites()),
                    "items": list(asset_manager.get_all_sprites().keys())
                },
                "tiles": {
                    "count": len(asset_manager.get_all_tiles()),
                    "items": list(asset_manager.get_all_tiles().keys())
                },
                "animations": {
                    "count": len(asset_manager.get_all_animations()),
                    "items": list(asset_manager.get_all_animations().keys())
                },
                "tilesets": {
                    "count": len(asset_manager.get_all_tilesets()),
                    "items": list(asset_manager.get_all_tilesets().keys())
                },
                "ui_elements": {
                    "count": len(asset_manager.get_all_ui_elements()),
                    "items": list(asset_manager.get_all_ui_elements().keys())
                }
            }
            
            return jsonify(assets_summary)
        except Exception as e:
            logger.error(f"Errore nell'API assets/info: {e}")
            return jsonify({"successo": False, "errore": str(e)}), 500
    
    # Gestione esplicita delle richieste OPTIONS per CORS preflight
    @app.route('/', methods=['OPTIONS'])
    @app.route('/<path:path>', methods=['OPTIONS'])
    def options_handler(path=None):
        return '', 204
    
    # Aggiungi una route esplicita per la root che restituisca uno stato OK
    @app.route('/', methods=['GET'])
    def root_handler():
        return jsonify({
            "status": "online",
            "message": "Server del gioco RPG funzionante"
        }), 200
    
    # Registra middleware per la validazione del JSON
    @app.before_request
    def validate_json():
        if request.method == 'POST' and request.is_json:
            try:
                # Verifica che il JSON sia valido
                _ = request.get_json(force=True)
            except BadRequest:
                return jsonify({
                    "successo": False,
                    "errore": "Il formato JSON fornito non è valido"
                }), 400
    
    # Registra error handler specifico per BadRequest
    @app.errorhandler(BadRequest)
    def handle_bad_request(e):
        logger.warning(f"Richiesta non valida: {str(e)}")
        return jsonify({
            "successo": False,
            "errore": "Richiesta non valida o malformata"
        }), 400
    
    # Gestore specifico per gli errori 404 (Not Found)
    @app.errorhandler(404)
    def handle_not_found(e):
        logger.warning(f"Risorsa non trovata: {request.path}")
        
        # Controlla se sembra un tentativo di path traversal
        if '..' in request.path or '../' in request.path or '/..' in request.path:
            logger.warning(f"Possibile tentativo di path traversal bloccato: {request.path}")
            return jsonify({
                "successo": False,
                "errore": "Accesso non autorizzato"
            }), 403
            
        return jsonify({
            "successo": False,
            "errore": "La risorsa richiesta non è stata trovata"
        }), 404
    
    # Registra error handler per le eccezioni generiche
    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error(f"Errore non gestito: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Controlla se è un tentativo di path traversal
        if request and hasattr(request, 'path'):
            if '..' in request.path or '../' in request.path or '/..' in request.path:
                logger.warning(f"Possibile tentativo di path traversal bloccato: {request.path}")
                return jsonify({
                    "successo": False,
                    "errore": "Accesso non autorizzato"
                }), 403
                
        return jsonify({
            "successo": False,
            "errore": "Si è verificato un errore interno"
        }), 500
    
    # Registra i blueprint delle route
    app.register_blueprint(base_routes, url_prefix='/game')
    
    # NOTA: Sembra che registrare sia tramite game_routes che direttamente stia causando problemi
    # Non utilizziamo register_game_routes, ma registriamo direttamente i blueprint necessari
    
    # Import esplicito dei blueprint necessari
    from server.routes.session_routes import session_routes
    from server.routes.save_routes import save_routes
    from server.routes.skill_challenge_routes import skill_challenge_routes
    from server.routes.combat_routes import combat_routes
    from server.routes.taverna_routes import taverna_routes
    from server.routes.mercato_routes import mercato_routes
    from server.routes.scelta_mappa_routes import scelta_mappa_routes
    from server.routes.dialogo_routes import dialogo_routes
    from server.routes.entity_routes import entity_routes
    from server.routes.mappa_routes import mappa_routes
    from server.routes.inventory_routes import inventory_routes
    from server.routes.classes_routes import classes_routes

    # Registrazione diretta dei blueprint
    app.register_blueprint(session_routes, url_prefix='/game/session')
    app.register_blueprint(save_routes, url_prefix='/game/save')
    app.register_blueprint(skill_challenge_routes, url_prefix='/game/skill_challenge')
    app.register_blueprint(combat_routes, url_prefix='/game/combat')
    app.register_blueprint(taverna_routes, url_prefix='/game/taverna')
    app.register_blueprint(mercato_routes, url_prefix='/game/mercato')
    app.register_blueprint(scelta_mappa_routes, url_prefix='/game/scelta_mappa')
    app.register_blueprint(dialogo_routes, url_prefix='/game/dialogo')
    app.register_blueprint(entity_routes, url_prefix='/game/entity')
    app.register_blueprint(inventory_routes, url_prefix='/game/inventory')
    app.register_blueprint(mappa_routes, url_prefix='/mappa')
    app.register_blueprint(assets_routes)
    app.register_blueprint(classes_routes, url_prefix='/game/classes')
    
    # Supporto per le URL legacy (combattimento)
    try:
        # Invece di riutilizzare lo stesso blueprint, creiamo una copia con le stesse route
        # Questo evita l'errore di riutilizzo dello stesso blueprint
        from flask import Blueprint
        legacy_combat_routes = Blueprint('combat_routes_legacy', __name__)
        
        # Copiamo tutte le funzioni delle route da combat_routes
        for rule in combat_routes.deferred_functions:
            legacy_combat_routes.deferred_functions.append(rule)
            
        # Registriamo il blueprint legacy
        app.register_blueprint(legacy_combat_routes, url_prefix='/combattimento')
        logger.info("Blueprint legacy combat_routes_legacy registrato con successo su /combattimento")
    except Exception as e:
        logger.error(f"Errore nella registrazione del blueprint legacy: {e}")
        logger.exception("Dettaglio eccezione:")
    
    # Route diretta nell'app per il test
    @app.route("/test_direct", methods=["GET"])
    def test_direct():
        logger.info("Route di test diretta chiamata")
        return jsonify({
            "successo": True,
            "messaggio": "Test diretto funziona correttamente"
        })
    
    # Route diretta per le classi
    @app.route("/classes", methods=["GET"])
    def get_classes_direct():
        logger.info("Route diretta /classes chiamata")
        try:
            # Percorso del file delle classi
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            classes_file = os.path.join(base_dir, "data", "classes", "classes.json")
            
            # Verifica se esiste classes.json
            if not os.path.exists(classes_file):
                logger.warning(f"File classes.json non trovato, provo con classi.json")
                classes_file = os.path.join(base_dir, "data", "classes", "classi.json")
                
                # Verifica se esiste classi.json
                if not os.path.exists(classes_file):
                    logger.error(f"Nessun file delle classi trovato in: {os.path.dirname(classes_file)}")
                    return jsonify({
                        "success": False,
                        "error": "File delle classi non trovato"
                    }), 404
            
            # Carica il file JSON
            with open(classes_file, 'r', encoding='utf-8') as f:
                classes_data = json.load(f)
            
            # Formatta i dati per il frontend
            classes_list = []
            for class_id, class_info in classes_data.items():
                classes_list.append({
                    "id": class_id,
                    "nome": class_id.capitalize(),
                    "descrizione": class_info.get("descrizione", "")
                })
            
            return jsonify({
                "success": True,
                "classi": classes_list
            })
        except Exception as e:
            logger.error(f"Errore nel caricamento delle classi: {str(e)}")
            return jsonify({
                "success": False,
                "error": f"Impossibile caricare le classi: {str(e)}"
            }), 500
    
    # Route diretta per le classi (con prefisso game)
    @app.route("/game/classes", methods=["GET"])
    def get_game_classes_direct():
        logger.info("Route diretta /game/classes chiamata")
        return get_classes_direct()
    
    # Route diretta per il test di combat
    @app.route("/game/combat/test_direct", methods=["GET"])
    def test_combat_direct():
        logger.info("Route di test combat diretta chiamata")
        return jsonify({
            "successo": True,
            "messaggio": "Test combat diretto funziona correttamente"
        })
    
    # Debug delle route
    logger.info("Route registrate nell'applicazione:")
    for rule in app.url_map.iter_rules():
        logger.info(f"Route: {rule.rule} [metodi: {', '.join(rule.methods)}]")
    
    # Stampa dettagliata delle route di combattimento
    logger.info("=== ROUTE DI COMBATTIMENTO ===")
    for rule in app.url_map.iter_rules():
        if 'combat' in rule.rule or 'combattimento' in rule.rule:
            logger.info(f"Combat route: {rule.rule} [endpoint: {rule.endpoint}] [metodi: {', '.join(rule.methods)}]")
    
    # Sovrascrivi la route /status esistente con una versione più robusta
    @app.route('/status', methods=['GET', 'OPTIONS'])
    def check_status():
        """
        Endpoint semplice per verificare lo stato del server
        Usato dal frontend per controllare la disponibilità
        """
        if request.method == 'OPTIONS':
            # Gestisci le richieste CORS OPTIONS
            response = app.make_default_options_response()
        else:
            # Restituisci lo stato del server come JSON
            response = jsonify({
                'status': 'online',
                'version': '1.0.0',
                'message': 'Server disponibile',
                'timestamp': str(datetime.datetime.now())
            })
            
        # Configura gli header CORS per consentire richieste da qualsiasi origine
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        
        return response, 200
    
    return app

def init_directories():
    """Crea le directory necessarie se non esistono"""
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    os.makedirs(SAVE_DIR, exist_ok=True)
    os.makedirs(BACKUPS_DIR, exist_ok=True)

def create_socketio(app):
    """Crea e configura l'istanza SocketIO"""
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    return socketio

def setup():
    """Configurazione iniziale del server"""
    # Crea le directory necessarie
    init_directories()
    
    # Crea l'app Flask
    app = create_app()
    
    # Crea l'istanza SocketIO
    socketio = create_socketio(app)
    
    # Imposta il riferimento socketio nel modulo session
    set_socketio(socketio)
    
    # Crea il renderer grafico
    graphics_renderer = GraphicsRenderer(socketio)
    
    # Inizializza gli handler WebSocket
    init_websocket_handlers(socketio, graphics_renderer)
    
    # Inizializza il gestore degli asset
    asset_manager = get_asset_manager()
    asset_manager.update_all()
    
    # Importa e chiama la funzione di inizializzazione degli asset esterni
    from server.utils.asset_loader import init_assets
    init_assets()
    
    # Configura il renderer grafico
    graphics_renderer.set_socket_io(socketio)
    
    return app, socketio

# Crea l'app e l'istanza SocketIO
app, socketio = setup()

def run_server(debug=True, host="0.0.0.0", port=5000):
    """Avvia il server"""
    socketio.run(app, debug=debug, host=host, port=port)

if __name__ == "__main__":
    run_server()