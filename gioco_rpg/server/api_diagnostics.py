"""
API di diagnostica per il gioco RPG.

Questo modulo fornisce API specifiche per il debug e la diagnostica
del frontend, del rendering della mappa e delle connessioni WebSocket.
"""
import os
import json
import logging
from flask import Blueprint, request, jsonify
from flask_cors import CORS

# Setup logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Crea il blueprint per le API di diagnostica
bp_diagnostics = Blueprint('diagnostics', __name__, url_prefix='/api/diagnostics')
CORS(bp_diagnostics)

# Cache delle texture per tracciamento
texture_cache = {
    'cached_textures': []
}

# Informazioni sul viewport
viewport_info = {
    'width': 800,
    'height': 600,
    'scale': 1.0,
    'center_x': 400,
    'center_y': 300
}

# Diagnostica WebSocket
socket_stats = {
    'connections': 0,
    'active_sessions': {},
    'events_received': 0,
    'events_sent': 0
}

@bp_diagnostics.route('/frontend', methods=['GET'])
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
            viewport_info.update(new_viewport)
            logger.info(f"Viewport info aggiornate: {viewport_info}")
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento del viewport: {e}")
    
    # Restituisci i dati diagnostici
    return jsonify({
        'viewport': viewport_info,
        'browser': request.user_agent.string,
        'timestamp': request.args.get('timestamp', 0)
    })

@bp_diagnostics.route('/frontend', methods=['POST'])
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
            viewport_info.update(data['viewport'])
            
        return jsonify({
            'success': True,
            'message': 'Dati diagnostici frontend ricevuti correttamente'
        })
    except Exception as e:
        logger.error(f"Errore nella ricezione dati diagnostici frontend: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@bp_diagnostics.route('/textures', methods=['GET', 'POST'])
def textures_diagnostics():
    """
    Gestisce la diagnostica delle texture.
    GET: Restituisce informazioni sulle texture caricate.
    POST: Aggiorna le informazioni sulle texture.
    
    Returns:
        JSON: Dati sulle texture
    """
    if request.method == 'POST':
        try:
            texture_data = request.json
            texture_cache['cached_textures'] = texture_data.get('textures', [])
            return jsonify({'success': True, 'message': 'Texture cache aggiornata'})
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento della cache texture: {e}")
            return jsonify({'success': False, 'error': str(e)}), 400
    else:
        return jsonify(texture_cache)

@bp_diagnostics.route('/websocket', methods=['GET', 'POST'])
def websocket_diagnostics():
    """
    Gestisce la diagnostica delle connessioni WebSocket.
    GET: Restituisce statistiche sulle connessioni WebSocket.
    POST: Aggiorna le statistiche WebSocket.
    
    Returns:
        JSON: Statistiche WebSocket
    """
    if request.method == 'POST':
        try:
            stats_data = request.json
            
            # Aggiorna statistiche
            if 'connections' in stats_data:
                socket_stats['connections'] = stats_data['connections']
            if 'events_received' in stats_data:
                socket_stats['events_received'] = stats_data['events_received']
            if 'events_sent' in stats_data:
                socket_stats['events_sent'] = stats_data['events_sent']
            if 'sessions' in stats_data:
                socket_stats['active_sessions'] = stats_data['sessions']
                
            return jsonify({'success': True, 'message': 'Statistiche WebSocket aggiornate'})
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento delle statistiche WebSocket: {e}")
            return jsonify({'success': False, 'error': str(e)}), 400
    else:
        return jsonify(socket_stats)

@bp_diagnostics.route('/render-test', methods=['GET'])
def render_test():
    """
    Genera una piccola mappa di test per verificare il rendering.
    
    Returns:
        JSON: Mappa di test
    """
    test_map = {
        'id': 'test_map',
        'name': 'Test Map',
        'width': 10,
        'height': 10,
        'layers': [
            {
                'name': 'ground',
                'data': [1] * 100  # 10x10 mappa di pavimenti
            },
            {
                'name': 'walls',
                'data': [0] * 100  # Layer vuoto inizialmente
            }
        ]
    }
    
    # Aggiungi muri ai bordi
    for i in range(10):  # Prima riga
        test_map['layers'][1]['data'][i] = 2
    for i in range(10):  # Ultima riga
        test_map['layers'][1]['data'][90 + i] = 2
    for i in range(1, 9):  # Prima colonna (escludendo angoli)
        test_map['layers'][1]['data'][i * 10] = 2
    for i in range(1, 9):  # Ultima colonna (escludendo angoli)
        test_map['layers'][1]['data'][i * 10 + 9] = 2
    
    # Aggiungi una porta
    test_map['layers'][1]['data'][45] = 3  # Centro della mappa
    
    # Entità di test
    test_entities = {
        'entities': [
            {
                'id': 'player_test',
                'tipo': 'player',
                'nome': 'Giocatore Test',
                'x': 5,
                'y': 5,
                'spriteId': 'player'
            },
            {
                'id': 'npc_test',
                'tipo': 'npc',
                'nome': 'NPC Test',
                'x': 3,
                'y': 3,
                'spriteId': 'npc'
            }
        ]
    }
    
    return jsonify({
        'map': test_map,
        'entities': test_entities
    })

@bp_diagnostics.route('/assets-check', methods=['GET'])
def assets_check():
    """
    Verifica la disponibilità degli asset della mappa.
    
    Returns:
        JSON: Stato degli asset
    """
    assets_base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')
    
    # Definisci gli asset da verificare
    asset_paths = {
        'tiles': ['floor.png', 'wall.png', 'door.png', 'grass.png', 'water.png'],
        'entities': ['player.png', 'npc.png', 'enemy.png'],
        'objects': ['chest.png', 'furniture.png']
    }
    
    # Verifica esistenza degli asset
    results = {}
    for category, files in asset_paths.items():
        category_path = os.path.join(assets_base_dir, category)
        results[category] = {}
        for file in files:
            file_path = os.path.join(category_path, file)
            results[category][file] = os.path.exists(file_path)
    
    return jsonify({
        'assets_dir': assets_base_dir,
        'results': results
    })

# Aggiornamenti WebSocket per diagnostica
def register_socket_connection(socket_id, session_id=None):
    """Registra una nuova connessione WebSocket nelle statistiche."""
    socket_stats['connections'] += 1
    if session_id:
        socket_stats['active_sessions'][socket_id] = {
            'session_id': session_id, 
            'connected_at': import_time().strftime('%Y-%m-%d %H:%M:%S'),
            'events_count': 0
        }

def unregister_socket_connection(socket_id):
    """Rimuove una connessione WebSocket dalle statistiche."""
    if socket_stats['connections'] > 0:
        socket_stats['connections'] -= 1
    if socket_id in socket_stats['active_sessions']:
        del socket_stats['active_sessions'][socket_id]

def track_socket_event(direction, event_name=None):
    """Traccia eventi WebSocket in entrata o uscita."""
    if direction == 'received':
        socket_stats['events_received'] += 1
    elif direction == 'sent':
        socket_stats['events_sent'] += 1

def import_time():
    """Importa datetime solo quando necessario."""
    from datetime import datetime
    return datetime

# Integrazione con il server principale
def register_diagnostics_bp(app):
    """Registra il blueprint diagnostics nell'app Flask."""
    app.register_blueprint(bp_diagnostics)
    logger.info("API di diagnostica registrate") 