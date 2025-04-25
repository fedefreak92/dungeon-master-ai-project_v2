# Assicurati che eventlet sia configurato correttamente
# Se eventlet è già stato patched in main.py, non farà nulla qui
try:
    import eventlet
    # Applica il monkey patching di Eventlet
    print("Applicazione monkey patching di Eventlet...")
    eventlet.monkey_patch(socket=True, select=True)
    print("Eventlet configurato correttamente per WebSocket")
except ImportError:
    print("ATTENZIONE: Eventlet non disponibile, le prestazioni WebSocket potrebbero essere ridotte")
    pass

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
import os
import logging
import json
import sys
from werkzeug.exceptions import BadRequest
import datetime
import time
from server.routes import register_routes
from server.websocket.websocket_manager import WebSocketManager
from server.websocket.session_auth import SessionAuthManager
from server.utils.session import get_session_manager

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
# Importa i moduli di diagnostica
from server.routes.api_diagnostics import api_diagnostics
# Importa il nostro nuovo WebSocketManager
from server.websocket.websocket_manager import WebSocketManager

# Importa i blueprint API con gestione degli errori
try:
    from server.routes.entity_api import entity_api
except ImportError:
    # Crea un blueprint vuoto se il modulo non esiste
    from flask import Blueprint
    entity_api = Blueprint('entity_api', __name__)
    logger.warning("Impossibile importare entity_api, utilizzando un blueprint vuoto")

try:  
    from server.routes.api_map import api_map
except ImportError:
    # Crea un blueprint vuoto se il modulo non esiste
    from flask import Blueprint
    api_map = Blueprint('api_map', __name__)
    logger.warning("Impossibile importare api_map, utilizzando un blueprint vuoto")

try:
    from server.routes.health_api import health_api
except ImportError:
    # Crea un blueprint vuoto se il modulo non esiste
    from flask import Blueprint
    health_api = Blueprint('health_api', __name__)
    logger.warning("Impossibile importare health_api, utilizzando un blueprint vuoto")

# Configura il logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config=None):
    """
    Crea e configura l'applicazione Flask
    
    Args:
        config (dict, optional): Configurazione personalizzata
        
    Returns:
        Flask: Istanza dell'applicazione configurata
    """
    app = Flask(__name__, static_folder=None)
    
    # Configurazione di base
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chiave_segreta_per_dev')
    app.config['CORS_HEADERS'] = 'Content-Type'
    app.config['JSON_AS_ASCII'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
    
    # Applica configurazione personalizzata
    if config:
        app.config.update(config)
    
    # Configurazione CORS più dettagliata
    cors_config = {
        "origins": ["http://localhost:3000", "http://localhost:5000", "*"],
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
        logger.info("Richiesta route root")
        return jsonify({
            "status": "ok",
            "message": "Server del gioco RPG in esecuzione",
            "versione": "1.0.0"
        })
    
    # Validazione JSON per le richieste POST/PUT
    @app.before_request
    def validate_json():
        if request.method in ('POST', 'PUT') and request.content_type == 'application/json':
            try:
                _ = request.json
            except BadRequest:
                logger.warning(f"Ricevuti dati JSON non validi nella richiesta: {request.data}")
                return jsonify({"successo": False, "errore": "JSON non valido"}), 400
    
    # Gestione degli errori
    @app.errorhandler(BadRequest)
    def handle_bad_request(e):
        logger.warning(f"Bad request: {e}")
        return jsonify({
            "successo": False,
            "errore": "Richiesta non valida"
        }), 400
    
    # Gestione errore 404
    @app.errorhandler(404)
    def handle_not_found(e):
        # Ottieni il percorso richiesto
        path = request.path if request else "Unknown"
        logger.warning(f"Risorsa non trovata: {path}")
        
        return jsonify({
            "successo": False,
            "errore": "File non trovato"
        }), 404
    
    # Gestione generica degli errori
    @app.errorhandler(Exception)
    def handle_exception(e):
        """
        Gestisce le eccezioni generiche in modo centralizzato
        """
        logger.error(f"Errore non gestito: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f"Si è verificato un errore: {str(e)}"
        }), 500
    
    # Registra i blueprint delle route
    app.register_blueprint(base_routes, url_prefix='/game')
    
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
    
    # Registra i blueprint per le API
    app.register_blueprint(api_diagnostics, url_prefix='/api')
    
    # Registra i blueprint per le API REST che falliscono nei test
    app.register_blueprint(entity_api, url_prefix='/api')
    app.register_blueprint(api_map, url_prefix='/api/map')
    app.register_blueprint(health_api, url_prefix='/api')
    
    # Aggiungi route per ping - ridefiniamo per avere consistenza
    @app.route('/ping', methods=['GET'])
    def ping():
        logger.info("Richiesta ping")
        return jsonify({
            "status": "ok",
            "message": "pong",
            "timestamp": datetime.datetime.now().isoformat()
        })
    
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
            
            # Leggi il file
            with open(classes_file, 'r', encoding='utf-8') as f:
                classi_data = json.load(f)
            
            # Trasforma i dati nel formato atteso dal frontend
            classi_formattate = []
            for classe_id, classe_info in classi_data.items():
                classe_info["id"] = classe_id
                classi_formattate.append(classe_info)
                
            return jsonify({
                "success": True,
                "classi": classi_formattate
            })
        except Exception as e:
            logger.error(f"Errore nel recupero delle classi: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route("/game/classes", methods=["GET"])
    def get_game_classes_direct():
        logger.info("Route diretta /game/classes chiamata")
        return get_classes_direct()
    
    # Route per verifica status
    @app.route('/status', methods=['GET', 'OPTIONS'])
    def check_status():
        """
        Verifica lo stato del server e restituisce info sul sistema
        """
        try:
            # Ottieni informazioni base sul sistema
            import platform
            import psutil
            
            system_info = {
                "platform": platform.platform(),
                "python_version": sys.version,
                "memory_usage": psutil.virtual_memory().percent,
                "cpu_usage": psutil.cpu_percent(interval=0.1)
            }
            
            # Verifica presenza asset manager
            asset_manager = get_asset_manager()
            assets_count = 0
            if asset_manager:
                try:
                    assets_count = len(asset_manager.get_all_sprites()) + len(asset_manager.get_all_tiles()) + len(asset_manager.get_all_ui_elements())
                except:
                    pass
            
            status_info = {
                "status": "ok",
                "uptime": time.time() - SERVER_START_TIME if 'SERVER_START_TIME' in globals() else 0,
                "system": system_info,
                "assets_loaded": assets_count,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            return jsonify(status_info)
        except Exception as e:
            logger.error(f"Errore durante check_status: {e}")
            return jsonify({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }), 500
    
    # Aggiunta del socket manager per WebSocket
    socket_manager = WebSocketManager(app)
    # Flask-SocketIO non ha un metodo middleware ma integra automaticamente con Flask
    # Salva il riferimento al socket_manager per usarlo altrove
    app.socket_manager = socket_manager
    
    # Registra le route
    register_routes(app)
    
    # Stato di salute
    @app.route('/health')
    def health():
        """
        Endpoint di health check
        """
        session_manager = get_session_manager()
        active_sessions = len(session_manager.get_active_sessions()) if session_manager else 0
        
        return jsonify({
            'status': 'ok',
            'websocket_connections': app.websocket_connections,
            'active_sessions': active_sessions,
            'authenticated_sessions': app.session_auth_manager.get_active_sessions_count()
        })
    
    # Esegui pulizia sessioni scadute periodicamente
    @app.before_request
    def cleanup_expired_sessions():
        """
        Pulisce le sessioni JWT scadute prima di ogni richiesta
        """
        if hasattr(app, 'session_auth_manager') and app.session_auth_manager:
            # Esegui pulizia solo ogni 100 richieste (valore approssimativo)
            import random
            if random.random() < 0.01:  # 1% delle richieste
                app.session_auth_manager.cleanup_expired_sessions()
    
    logger.info("Applicazione Flask inizializzata")
    return app

# Memorizza il tempo di avvio del server
SERVER_START_TIME = time.time()

# Funzione per inizializzare le directory necessarie
def init_directories():
    """Crea le directory necessarie se non esistono"""
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    os.makedirs(SAVE_DIR, exist_ok=True)
    os.makedirs(BACKUPS_DIR, exist_ok=True)

def create_socketio(app):
    """
    Crea e configura l'oggetto SocketIO per le comunicazioni WebSocket
    """
    try:
        # Configurazione ottimizzata per WebSocket con Eventlet
        # I valori ping_timeout e ping_interval sono cruciali per evitare disconnessioni premature
        ping_timeout = 60000  # Aumentato a 60 secondi
        ping_interval = 25000 # Mantenuto a 25 secondi
        
        # Configura CORS per supportare completamente WebSocket
        cors_allowed = ["http://localhost:3000", "http://localhost:5000", "http://127.0.0.1:3000", "http://127.0.0.1:5000"]
        
        socketio = SocketIO(
            app, 
            cors_allowed_origins=cors_allowed, 
            async_mode='eventlet',  # Usa eventlet per supportare WebSocket nativo
            ping_timeout=ping_timeout,       # 60 secondi di timeout per evitare disconnessioni premature
            ping_interval=ping_interval,     # 25 secondi tra ping per un bilanciamento ottimale
            always_connect=True,    # Tentativo di connessione immediato
            manage_session=False,   # Gestisci le sessioni manualmente per maggior controllo
            transports=['websocket', 'polling'],  # Preferisci WebSocket, fallback su polling
            engineio_logger=True if app.debug else False,  # Log dettagliati solo in debug
            logger=True if app.debug else False  # Logging di Flask-SocketIO
        )
        
        # Configura il websocket_manager nell'app per accesso futuro
        websocket_manager = WebSocketManager(app, socketio)
        app.websocket_manager = websocket_manager
        
        # NON inizializzare gli handler websocket qui
        # Gli handler verranno inizializzati nella funzione setup() dove è disponibile il renderer
        
        # Configura il socketio nel modulo di sessione
        set_socketio(socketio)
        
        # Registra CORS per supportare WebSocket
        app.config['CORS_HEADERS'] = 'Content-Type, Authorization'
        logger.info(f"SocketIO configurato con successo utilizzando async_mode='eventlet', ping_interval={ping_interval/1000}s, ping_timeout={ping_timeout/1000}s")
        logger.info(f"CORS configurato per: {cors_allowed}")
        return socketio
    except Exception as e:
        logger.error(f"Errore nella configurazione di SocketIO: {str(e)}")
        raise e

def setup():
    """
    Configurazione completa dell'applicazione e del server WebSocket
    
    Returns:
        tuple: (app, socketio)
    """
    # Crea app Flask
    app = create_app()
    
    # Verifica e crea directory richieste
    init_directories()
    
    # Crea istanza SocketIO
    socketio = create_socketio(app)
    
    # Configura SessionAuthManager se supporta set_socketio
    try:
        from server.websocket.session_auth import SessionAuthManager
        session_auth_manager = SessionAuthManager()
        if hasattr(session_auth_manager, 'set_socketio'):
            session_auth_manager.set_socketio(socketio)
            logger.info("SessionAuthManager configurato con socketio")
    except Exception as e:
        logger.warning(f"Impossibile configurare SessionAuthManager: {e}")
    
    # Imposta l'istanza socketio nel modulo utils.session
    from server.utils.session import set_socketio
    set_socketio(socketio)
    
    # Configura il renderer grafico
    from core.graphics_renderer import GraphicsRenderer
    graphics_renderer = GraphicsRenderer()
    
    # Importa WebSocketEventBridge dopo aver creato socketio
    try:
        from server.websocket.websocket_event_bridge import WebSocketEventBridge
        # Ottieni l'istanza esistente o creane una nuova
        websocket_bridge = WebSocketEventBridge.get_instance()
        # Imposta l'istanza SocketIO solo se non è stata già impostata
        if websocket_bridge.socketio is None:
            websocket_bridge.set_socketio(socketio)
        logger.info("WebSocketEventBridge inizializzato correttamente")
    except Exception as e:
        logger.error(f"Errore durante inizializzazione WebSocketEventBridge: {e}")
    
    # Inizializza gli handler WebSocket
    from server.websocket import init_websocket_handlers
    init_websocket_handlers(socketio, graphics_renderer)
    
    # Inizializza l'asset manager
    try:
        from util.asset_manager import get_asset_manager
        asset_manager = get_asset_manager()
        asset_manager.update_all()
    except Exception as e:
        logger.warning(f"Impossibile inizializzare asset manager: {e}")
    
    return app, socketio

# Crea l'app e l'istanza SocketIO
app, socketio = setup()

def run_server(debug=True, host="0.0.0.0", port=5000):
    """Avvia il server"""
    logger.info(f"Avvio server su {host}:{port} (debug: {debug})")
    
    # Ottieni la modalità asincrona in uso
    async_mode = socketio.async_mode
    logger.info(f"Utilizzando modalità asincrona: {async_mode}")
    
    # Verifica se la porta è già in uso e prova porte alternative
    original_port = port
    max_port_attempts = 10
    port_attempts = 0
    
    while port_attempts < max_port_attempts:
        try:
            import socket
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.bind((host, port))
            test_socket.close()
            logger.info(f"Porta {port} disponibile per l'uso")
            break
        except OSError:
            port_attempts += 1
            port = original_port + port_attempts
            logger.warning(f"Porta {port-1} già in uso, provo con la porta {port}")
            if port_attempts >= max_port_attempts:
                logger.error(f"Impossibile trovare una porta disponibile dopo {max_port_attempts} tentativi")
                raise RuntimeError(f"Tutte le porte da {original_port} a {port-1} sono occupate")
    
    try:
        # Con Flask-SocketIO, usare sempre socketio.run() che gestisce autonomamente
        # l'integrazione con i vari backends come eventlet o gevent
        socketio.run(app, host=host, port=port, debug=debug)
    except Exception as e:
        logger.error(f"Errore durante l'avvio del server: {e}")
        raise e

if __name__ == "__main__":
    run_server()

def setup_diagnostics_routes(app):
    """
    Configura le route per la diagnostica dopo che il blueprint è stato registrato
    
    Args:
        app: L'istanza dell'applicazione Flask
    """
    from flask import jsonify, request
    import json
    
    # Definisci variabili globali per viewport_info
    app.viewport_info = {}
    
    # Aggiungi la funzione di gestione per /api/diagnostics/frontend
    @app.route('/api/diagnostics/frontend', methods=['GET'])
    def get_frontend_diagnostics():
        """
        Restituisce dati diagnostici sul frontend, incluso il viewport.
        
        Returns:
            JSON: Dati diagnostici frontend
        """
        # Ottieni i dati dal frontend se presenti nella richiesta
        if request.args.get('update') and request.args.get('viewport_data'):
            try:
                new_viewport = json.loads(request.args.get('viewport_data'))
                app.viewport_info.update(new_viewport)
                logger.info(f"Viewport info aggiornate: {app.viewport_info}")
            except Exception as e:
                logger.error(f"Errore nell'aggiornamento del viewport: {e}")
        
        # Restituisci i dati diagnostici
        return jsonify({
            'viewport': app.viewport_info,
            'browser': request.user_agent.string,
            'timestamp': request.args.get('timestamp', 0)
        })

    # Aggiungi una route POST per frontend diagnostics
    @app.route('/api/diagnostics/frontend', methods=['POST'])
    def post_frontend_diagnostics():
        """
        Riceve dati diagnostici dal frontend.
        
        Returns:
            JSON: Conferma ricezione
        """
        try:
            data = request.json
            logger.info(f"Ricevuti dati diagnostici dal frontend: {data}")
            
            # Aggiorna info viewport se presenti
            if 'viewport' in data:
                app.viewport_info.update(data['viewport'])
                
            return jsonify({
                'success': True,
                'message': 'Dati diagnostici frontend ricevuti correttamente'
            })
        except Exception as e:
            logger.error(f"Errore nell'elaborazione dei dati diagnostici: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500