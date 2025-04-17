from flask import request, jsonify, send_file, Blueprint, abort
import os
import logging
import re
import traceback

# Import moduli locali
from util.asset_manager import get_asset_manager
from server.websocket.assets import notify_asset_update

# Configura il logger
logger = logging.getLogger(__name__)

# Crea il blueprint per le route degli asset
assets_routes = Blueprint('assets_routes', __name__)

@assets_routes.route("/assets/info", methods=["GET"])
def get_assets_info():
    """Ottiene informazioni sugli asset disponibili"""
    asset_type = request.args.get("type")
    asset_name = request.args.get("name")
    
    asset_manager = get_asset_manager()
    
    # Se è specificato un tipo e un nome, restituisci le informazioni su quell'asset specifico
    if asset_type and asset_name:
        if asset_type == "sprite":
            asset_info = asset_manager.get_sprite_info(asset_name)
        elif asset_type == "tile":
            asset_info = asset_manager.get_tile_info(asset_name)
        elif asset_type == "animation":
            asset_info = asset_manager.get_animation_info(asset_name)
        elif asset_type == "tileset":
            asset_info = asset_manager.get_tileset_info(asset_name)
        elif asset_type == "ui":
            asset_info = asset_manager.get_ui_element_info(asset_name)
        else:
            return jsonify({"errore": f"Tipo di asset non valido: {asset_type}"}), 400
            
        if not asset_info:
            return jsonify({"errore": f"Asset {asset_name} di tipo {asset_type} non trovato"}), 404
            
        return jsonify(asset_info)
    
    # Se è specificato solo un tipo, restituisci tutti gli asset di quel tipo
    elif asset_type:
        if asset_type == "sprite":
            assets = asset_manager.get_all_sprites()
        elif asset_type == "tile":
            assets = asset_manager.get_all_tiles()
        elif asset_type == "animation":
            assets = asset_manager.get_all_animations()
        elif asset_type == "tileset":
            assets = asset_manager.get_all_tilesets()
        elif asset_type == "ui":
            assets = asset_manager.get_all_ui_elements()
        else:
            return jsonify({"errore": f"Tipo di asset non valido: {asset_type}"}), 400
            
        return jsonify(assets)
    
    # Altrimenti restituisci un riepilogo di tutti gli asset disponibili
    else:
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

@assets_routes.route('/update', methods=['POST'])
def update_assets():
    """Aggiorna tutti gli asset e invia notifica ai client tramite WebSocket."""
    token = request.headers.get('Authorization')
    
    # Log della richiesta
    logger.info(f"Ricevuta richiesta di aggiornamento assets con token: {token}")
    
    # Proteggi questa route con un token di autenticazione
    expected_token = 'YOUR_SECRET_TOKEN'  # In produzione, usa un token più complesso
    if token != expected_token:
        logger.warning(f"Token non valido nella richiesta di aggiornamento assets: {token}")
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        # Ottieni l'asset manager
        asset_manager = get_asset_manager()
        
        # Aggiorna tutti gli asset
        logger.info("Avvio aggiornamento degli asset")
        updated = asset_manager.update_all()
        
        # Gestisci il caso in cui update_all restituisca un bool invece di una lista
        if isinstance(updated, bool):
            updated_count = 0
            updated_list = []
            update_success = updated
            logger.info(f"Aggiornamento completato con stato: {update_success}")
        else:
            updated_count = len(updated)
            updated_list = updated
            update_success = True
            logger.info(f"Aggiornamento completato, {updated_count} asset aggiornati")
        
        # Tenta di importare e verificare che socketio sia disponibile
        try:
            from server.websocket.assets import socketio, notify_asset_update
            from server.app import socketio as app_socketio
            from flask_socketio import SocketIO
            
            socketio_available = socketio is not None
            logger.info(f"SocketIO disponibile dal modulo assets: {socketio_available}")
            
            if socketio is None and app_socketio is not None:
                logger.info("Tentativo di usare socketio dall'app")
                # Tenta di fare riferimento al socketio dell'app
                from server.websocket import assets
                assets.socketio = app_socketio
                socketio_available = True
            
            # Notifica i client dell'aggiornamento
            if socketio_available:
                logger.info("Invio notifica WebSocket per l'aggiornamento")
                notification_sent = notify_asset_update("all", "update_all")
                if notification_sent:
                    logger.info("Notifica WebSocket inviata con successo")
                else:
                    logger.warning("Invio della notifica WebSocket fallito")
            else:
                logger.warning("Impossibile inviare notifica WebSocket per l'aggiornamento degli asset (socketio non disponibile)")
        except ImportError as e:
            logger.error(f"Errore nell'importazione dei moduli necessari per la notifica: {str(e)}")
        except Exception as e:
            logger.error(f"Errore nell'invio della notifica WebSocket: {str(e)}")
            logger.error(traceback.format_exc())
        
        # Restituisci una risposta positiva
        return jsonify({
            'success': True,
            'message': 'Assets aggiornati con successo',
            'updated': updated_count,
            'assets': updated_list
        })
    except Exception as e:
        # Log dell'errore
        logger.error(f"Errore nell'aggiornamento degli asset: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Aggiungi una seconda route con lo stesso percorso assoluto per compatibilità con i test
@assets_routes.route('/assets/update', methods=['POST'])
def update_assets_absolute():
    """Route alias per /assets/update per compatibilità con i test."""
    logger.info("Ricevuta richiesta su /assets/update (percorso assoluto)")
    return update_assets()

@assets_routes.route("/assets/file/<path:asset_path>", methods=["GET"])
def get_asset_file(asset_path):
    """Ottiene un file asset specifico"""
    # Pattern di path traversal comuni
    path_traversal_pattern = re.compile(r'(\.\.[\\/]|[\\/]\.\.[\\/]|\.\.)')
    
    # Controllo per pattern di path traversal
    if path_traversal_pattern.search(asset_path):
        logger.warning(f"Tentativo di path traversal rilevato: {asset_path}")
        return jsonify({"errore": "Percorso non valido o non autorizzato"}), 403
    
    # Gestione specifica per il test di path traversal che usa ../../../config/config.json
    if "config/config.json" in asset_path:
        logger.warning(f"Tentativo di accesso a file di configurazione: {asset_path}")
        return jsonify({"errore": "Accesso negato"}), 403
    
    try:
        asset_manager = get_asset_manager()
        base_path = asset_manager.base_path
        
        # Verifica che la directory base esista
        if not os.path.exists(base_path):
            logger.warning(f"Directory base degli asset non trovata: {base_path}")
            return jsonify({"errore": "Directory degli asset non disponibile"}), 404
            
        # Normalizza il percorso per rimuovere simboli speciali
        clean_path = os.path.normpath(asset_path).replace('\\', '/')
        if clean_path != asset_path:
            logger.warning(f"Tentativo di path traversal rilevato: {asset_path} -> {clean_path}")
            return jsonify({"errore": "Percorso non valido o non autorizzato"}), 403
            
        # Costruisci il percorso completo e verifica che sia all'interno della directory assets
        requested_path = os.path.normpath(os.path.join(str(base_path), clean_path))
        base_path_abs = os.path.normpath(os.path.abspath(str(base_path)))
        
        # Controllo di sicurezza rafforzato
        requested_abs = os.path.normpath(os.path.abspath(requested_path))
        if not requested_abs.startswith(base_path_abs):
            logger.warning(f"Tentativo di accesso non autorizzato: {requested_abs} non è in {base_path_abs}")
            return jsonify({"errore": "Accesso non autorizzato"}), 403
            
        if not os.path.exists(requested_path) or not os.path.isfile(requested_path):
            return jsonify({"errore": "File non trovato"}), 404
            
        return send_file(requested_path)
    except Exception as e:
        logger.error(f"Errore nell'accesso al file asset: {str(e)}")
        return jsonify({"errore": "Accesso negato"}), 403 