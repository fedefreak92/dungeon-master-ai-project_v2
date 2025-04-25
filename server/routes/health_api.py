import os
import sys
import platform
import psutil
import json
import datetime
import logging
from flask import Blueprint, jsonify, current_app

# Configura il logger
logger = logging.getLogger(__name__)

# Crea il blueprint per le API di health
health_api = Blueprint('health_api', __name__)

@health_api.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint di health check che fornisce informazioni dettagliate sullo stato del sistema
    """
    logger.info("Richiesta API health check dettagliato")
    
    try:
        # Informazioni di sistema
        system_info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": sys.version,
        }
        
        # Informazioni sul processo
        process = psutil.Process(os.getpid())
        process_info = {
            "pid": process.pid,
            "memory_percent": process.memory_percent(),
            "cpu_percent": process.cpu_percent(interval=0.1),
            "threads": len(process.threads()),
            "create_time": datetime.datetime.fromtimestamp(process.create_time()).isoformat(),
            "status": process.status(),
        }
        
        # Informazioni sull'app Flask
        flask_info = {
            "debug": current_app.debug,
            "testing": current_app.testing,
            "secret_key_set": current_app.secret_key is not None,
            "registered_blueprints": list(current_app.blueprints.keys()),
        }
        
        # Informazioni sul sistema (non Windows)
        system_load = {}
        if platform.system() != "Windows":
            load1, load5, load15 = os.getloadavg()
            system_load = {
                "load1": load1,
                "load5": load5,
                "load15": load15,
            }
        
        # Informazioni sul disco
        disk_usage = {}
        try:
            disk = psutil.disk_usage('/')
            disk_usage = {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent,
            }
        except Exception as e:
            logger.warning(f"Impossibile ottenere informazioni sul disco: {e}")
            disk_usage = {"error": str(e)}
        
        # Restituisci il risultato
        return jsonify({
            "status": "ok",
            "timestamp": datetime.datetime.now().isoformat(),
            "system": system_info,
            "process": process_info,
            "flask": flask_info,
            "system_load": system_load,
            "disk_usage": disk_usage,
        })
    except Exception as e:
        logger.error(f"Errore durante health check: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat()
        }), 500

@health_api.route('/ping', methods=['GET'])
def ping():
    """
    Semplice endpoint di ping per verificare che il server sia attivo
    """
    logger.info("Richiesta ping")
    
    # Formato compatibile con i test
    return jsonify({
        "status": "ok",
        "message": "pong",
        "timestamp": datetime.datetime.now().isoformat()
    }) 