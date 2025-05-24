from flask import Blueprint, jsonify, request
import os
import json
import logging
import time
import platform
import psutil
import sys
from datetime import datetime
from collections import deque
import threading
from util.asset_manager import get_asset_manager
from util.data_manager import get_data_manager
from util.config import DATA_DIR, SAVE_DIR, MAPS_DIR

# Configura il logger
logger = logging.getLogger(__name__)

# Crea il blueprint
api_diagnostics = Blueprint('api_diagnostics', __name__)

# Memorizza il tempo di avvio del server
SERVER_START_TIME = time.time()

# Coda per memorizzare i log (massimo 100 voci)
log_entries = deque(maxlen=100)

@api_diagnostics.route('/health', methods=['GET'])
def health_check():
    """
    Controlla lo stato di salute del server e fornisce informazioni di base.
    
    Returns:
        json: Stato di salute del server e informazioni di sistema
    """
    logger.info("Richiesta di health check ricevuta")
    try:
        # Calcola l'uptime del server
        uptime_seconds = time.time() - SERVER_START_TIME
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        uptime_str = f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"
        
        # Ottieni informazioni di sistema
        system_info = {
            "platform": platform.platform(),
            "python_version": sys.version,
            "processor": platform.processor(),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent_used": psutil.virtual_memory().percent
            },
            "cpu_usage": psutil.cpu_percent(interval=0.1)
        }
        
        # Costruisci la risposta
        response = {
            "status": "online",
            "version": "1.0.0",  # Aggiorna con la versione effettiva
            "uptime": uptime_str,
            "system_info": system_info,
            "timestamp": datetime.now().isoformat()
        }
        
        # Aggiungi l'informazione alla coda dei log
        log_entries.append({
            "timestamp": datetime.now().isoformat(),
            "type": "health_check",
            "message": "Health check completato con successo"
        })
        
        return jsonify(response)
    except Exception as e:
        error_msg = f"Errore durante il health check: {str(e)}"
        logger.error(error_msg)
        
        # Aggiungi l'errore alla coda dei log
        log_entries.append({
            "timestamp": datetime.now().isoformat(),
            "type": "error",
            "message": error_msg
        })
        
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@api_diagnostics.route('/frontend', methods=['POST'])
def frontend_diagnostics():
    """
    Riceve e registra dati diagnostici dal frontend.
    
    Returns:
        json: Conferma di ricezione
    """
    try:
        # Ottieni dati JSON dalla richiesta
        data = request.json
        if not data:
            logger.warning("Dati diagnostici frontend non validi o vuoti")
            return jsonify({
                "success": False,
                "error": "Dati non validi o vuoti"
            }), 400
        
        # Registra i dati diagnostici
        logger.info(f"Dati diagnostici frontend ricevuti: {data}")
        
        # Aggiungi i dati alla coda dei log
        log_entries.append({
            "timestamp": datetime.now().isoformat(),
            "type": "frontend_diagnostics",
            "data": data
        })
        
        return jsonify({
            "success": True,
            "message": "Dati diagnostici ricevuti correttamente"
        })
    except Exception as e:
        error_msg = f"Errore nell'elaborazione dei dati diagnostici frontend: {str(e)}"
        logger.error(error_msg)
        
        # Aggiungi l'errore alla coda dei log
        log_entries.append({
            "timestamp": datetime.now().isoformat(),
            "type": "error",
            "message": error_msg
        })
        
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_diagnostics.route('/entities', methods=['GET'])
def get_entities():
    """
    Recupera le entità disponibili nel sistema per scopi diagnostici.
    
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
        
        return jsonify(entities)
    except Exception as e:
        error_msg = f"Errore durante il recupero delle entità: {str(e)}"
        logger.error(error_msg)
        
        # Aggiungi l'errore alla coda dei log
        log_entries.append({
            "timestamp": datetime.now().isoformat(),
            "type": "error",
            "message": error_msg
        })
        
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_diagnostics.route('/server', methods=['GET'])
def server_diagnostics():
    """
    Fornisce diagnostica dettagliata sul server e le risorse di sistema.
    
    Returns:
        json: Informazioni diagnostiche del server
    """
    try:
        # Raccogli informazioni di sistema dettagliate
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Ottieni informazioni sul processo corrente
        process = psutil.Process()
        process_memory = process.memory_info()
        
        # Costruisci la risposta
        diagnostics = {
            "server": {
                "uptime": time.time() - SERVER_START_TIME,
                "start_time": datetime.fromtimestamp(SERVER_START_TIME).isoformat(),
                "process_id": process.pid,
                "process_memory": {
                    "rss": process_memory.rss,  # Resident Set Size
                    "vms": process_memory.vms,  # Virtual Memory Size
                    "shared": getattr(process_memory, 'shared', 0),  # Shared memory
                    "percent": process.memory_percent()
                },
                "threads": process.num_threads(),
                "cpu_percent": process.cpu_percent(interval=0.1)
            },
            "system": {
                "platform": platform.platform(),
                "python_version": sys.version,
                "processor": platform.processor(),
                "cpu_count": {
                    "physical": psutil.cpu_count(logical=False),
                    "logical": psutil.cpu_count(logical=True)
                },
                "cpu_usage": {
                    "system": psutil.cpu_percent(interval=0.1),
                    "per_cpu": psutil.cpu_percent(interval=0.1, percpu=True)
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent
                },
                "network": {
                    "connections": len(psutil.net_connections())
                }
            },
            "logs": {
                "recent": list(log_entries)[-10:] if log_entries else []  # Ultimi 10 log
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Aggiungi informazione alla coda dei log
        log_entries.append({
            "timestamp": datetime.now().isoformat(),
            "type": "server_diagnostics",
            "message": "Diagnostica server richiesta"
        })
        
        return jsonify(diagnostics)
    except Exception as e:
        error_msg = f"Errore durante la raccolta di diagnostica server: {str(e)}"
        logger.error(error_msg)
        
        # Aggiungi l'errore alla coda dei log
        log_entries.append({
            "timestamp": datetime.now().isoformat(),
            "type": "error",
            "message": error_msg
        })
        
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api_diagnostics.route('/diagnostics/resources', methods=['GET'])
def get_resources():
    """
    Restituisce informazioni sulle risorse del sistema.
    """
    try:
        # Ottieni le informazioni su CPU e memoria
        cpu_usage = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Restituisci un oggetto JSON con le informazioni
        return jsonify({
            'cpu': {
                'usage': cpu_usage,
                'cores': psutil.cpu_count(logical=False),
                'threads': psutil.cpu_count(logical=True)
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent
            },
            'disk': {
                'total': disk.total,
                'free': disk.free,
                'percent': disk.percent
            },
            'process': {
                'memory': psutil.Process().memory_info().rss,
                'threads': len(psutil.Process().threads())
            }
        })
    except ImportError:
        return jsonify({
            'error': 'psutil non installato, impossibile ottenere informazioni sulle risorse'
        }), 500
    except Exception as e:
        logger.error(f"Errore nell'API resources: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@api_diagnostics.route('/diagnostics/assets', methods=['GET'])
def get_assets_info():
    """
    Restituisce informazioni sugli asset caricati.
    """
    try:
        asset_manager = get_asset_manager()
        
        # Ottieni le informazioni sugli asset
        assets_info = {
            'sprites': len(asset_manager.get_all_sprites()),
            'tiles': len(asset_manager.get_all_tiles()),
            'animations': len(asset_manager.get_all_animations()),
            'tilesets': len(asset_manager.get_all_tilesets()),
            'ui_elements': len(asset_manager.get_all_ui_elements())
        }
        
        # Ottieni informazioni sugli sprite sheet
        try:
            sprite_sheet_manager = asset_manager.sprite_sheet_manager
            sprite_sheets_info = {
                'sheets': len(sprite_sheet_manager.sprite_sheets),
                'sprite_mappings': len(sprite_sheet_manager.sprite_to_sheet)
            }
            assets_info['sprite_sheets'] = sprite_sheets_info
        except Exception as e:
            logger.warning(f"Errore nell'ottenimento delle informazioni sugli sprite sheet: {e}")
            assets_info['sprite_sheets'] = {'error': str(e)}
        
        return jsonify(assets_info)
    except Exception as e:
        logger.error(f"Errore nell'API assets: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@api_diagnostics.route('/diagnostics/generate-sprite-sheets', methods=['POST'])
def generate_sprite_sheets():
    """
    Genera sprite sheet da varie directory di asset.
    """
    try:
        # Ottieni il flag per l'esecuzione asincrona
        async_execution = request.json.get('async', False) if request.is_json else False
        
        if async_execution:
            # Esegui la generazione in un thread separato
            thread = threading.Thread(target=_generate_sprite_sheets_async)
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'status': 'started',
                'message': 'Generazione sprite sheet avviata in background'
            })
        else:
            # Esegui la generazione in modo sincrono
            start_time = time.time()
            asset_manager = get_asset_manager()
            result = asset_manager.generate_sprite_sheets()
            duration = time.time() - start_time
            
            return jsonify({
                'status': 'completed',
                'success': result,
                'duration': duration
            })
    except Exception as e:
        logger.error(f"Errore nell'API generate-sprite-sheets: {e}")
        return jsonify({
            'error': str(e)
        }), 500

def _generate_sprite_sheets_async():
    """
    Funzione eseguita in un thread separato per generare sprite sheet in modo asincrono.
    """
    try:
        logger.info("Avvio generazione sprite sheet in background")
        start_time = time.time()
        asset_manager = get_asset_manager()
        result = asset_manager.generate_sprite_sheets()
        duration = time.time() - start_time
        logger.info(f"Generazione sprite sheet completata in {duration:.2f} secondi (success: {result})")
    except Exception as e:
        logger.error(f"Errore nella generazione asincrona degli sprite sheet: {e}")

@api_diagnostics.route('/diagnostics/data_paths', methods=['GET'])
def diagnostica_percorsi_dati():
    """Endpoint per ottenere informazioni diagnostiche sui percorsi dati."""
    try:
        # Ottieni il data manager
        data_manager = get_data_manager()
        
        # Esegui diagnostica completa
        diagnostica = data_manager.diagnose_system_paths()
        
        # Aggiungi informazioni sulle directory principali
        diagnostica["_directories"] = {
            "DATA_DIR": str(DATA_DIR),
            "DATA_DIR_exists": DATA_DIR.exists(),
            "SAVE_DIR": str(SAVE_DIR),
            "SAVE_DIR_exists": SAVE_DIR.exists(),
            "MAPS_DIR": str(MAPS_DIR),
            "MAPS_DIR_exists": MAPS_DIR.exists(),
        }
        
        return jsonify({
            "success": True,
            "message": "Diagnostica completata",
            "data": diagnostica
        })
    except Exception as e:
        logger.error(f"Errore durante la diagnostica: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Errore durante la diagnostica: {str(e)}",
            "error": str(e)
        }), 500

@api_diagnostics.route('/diagnostics/classi', methods=['GET'])
def diagnostica_classi():
    """Endpoint per verificare le classi di personaggio."""
    try:
        # Ottieni il data manager
        data_manager = get_data_manager()
        
        # Carica le classi
        classi = data_manager.get_classes()
        
        # Raccogli informazioni sulle classi
        info_classi = {
            "numero_classi": len(classi) if isinstance(classi, dict) else 0,
            "nomi_classi": list(classi.keys()) if isinstance(classi, dict) else [],
            "data_type": type(classi).__name__,
            "classi_complete": classi if isinstance(classi, dict) else None
        }
        
        return jsonify({
            "success": True,
            "message": f"Trovate {info_classi['numero_classi']} classi",
            "data": info_classi
        })
    except Exception as e:
        logger.error(f"Errore durante la diagnostica delle classi: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Errore durante la diagnostica delle classi: {str(e)}",
            "error": str(e)
        }), 500

@api_diagnostics.route('/diagnostics/all_data', methods=['GET'])
def diagnostica_tutti_i_dati():
    """Endpoint per verificare tutti i tipi di dati disponibili."""
    try:
        # Ottieni il data manager
        data_manager = get_data_manager()
        
        # Verifica tutti i tipi di dati
        dati = {}
        for data_type in data_manager._data_paths.keys():
            try:
                dati[data_type] = {
                    "caricati": True,
                    "tipo": None,
                    "dimensione": 0,
                    "errore": None
                }
                
                # Tenta di caricare i dati
                data = data_manager.load_data(data_type)
                
                # Raccogli informazioni
                if isinstance(data, dict):
                    dati[data_type]["tipo"] = "dict"
                    dati[data_type]["dimensione"] = len(data)
                    dati[data_type]["chiavi"] = list(data.keys())[:10]  # Limita a 10 chiavi
                elif isinstance(data, list):
                    dati[data_type]["tipo"] = "list"
                    dati[data_type]["dimensione"] = len(data)
                else:
                    dati[data_type]["tipo"] = type(data).__name__
                    dati[data_type]["dimensione"] = -1
            except Exception as e:
                dati[data_type]["caricati"] = False
                dati[data_type]["errore"] = str(e)
        
        return jsonify({
            "success": True,
            "message": f"Diagnostica completata per {len(dati)} tipi di dati",
            "data": dati
        })
    except Exception as e:
        logger.error(f"Errore durante la diagnostica di tutti i dati: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Errore durante la diagnostica di tutti i dati: {str(e)}",
            "error": str(e)
        }), 500 