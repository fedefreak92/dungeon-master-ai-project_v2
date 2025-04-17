from flask import Blueprint, jsonify
import os
import json
import logging

# Configura il logger
logger = logging.getLogger(__name__)

# Crea blueprint per le route delle classi
classes_routes = Blueprint('classes_routes', __name__)

@classes_routes.route("/", methods=['GET'])
def get_available_classes():
    """Ottiene la lista di tutte le classi disponibili"""
    try:
        # Percorso del file delle classi
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        classes_path = os.path.join(base_dir, "data", "classes", "classes.json")
        
        # Verifica se il file esiste
        if not os.path.exists(classes_path):
            logger.error(f"File classes.json non trovato in: {classes_path}")
            
            # Prova con classi.json come fallback
            classes_path = os.path.join(base_dir, "data", "classes", "classi.json")
            if not os.path.exists(classes_path):
                logger.error(f"Nemmeno classi.json trovato in: {os.path.dirname(classes_path)}")
                return jsonify({
                    "success": False,
                    "error": "File delle classi non trovato"
                }), 404
        
        # Leggi il file delle classi
        with open(classes_path, 'r', encoding='utf-8') as f:
            classes_data = json.load(f)
        
        # Trasforma i dati in un formato più utilizzabile
        classi_formattate = []
        for classe_id, classe_info in classes_data.items():
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
            "error": f"Errore interno: {str(e)}"
        }), 500
        
@classes_routes.route("/<classe_id>", methods=['GET'])
def get_class_by_id(classe_id):
    """Ottiene le informazioni di una specifica classe"""
    try:
        # Percorso del file delle classi
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        classes_path = os.path.join(base_dir, "data", "classes", "classes.json")
        
        # Verifica se il file esiste
        if not os.path.exists(classes_path):
            logger.error(f"File classes.json non trovato in: {classes_path}")
            
            # Prova con classi.json come fallback
            classes_path = os.path.join(base_dir, "data", "classes", "classi.json")
            if not os.path.exists(classes_path):
                logger.error(f"Nemmeno classi.json trovato in: {os.path.dirname(classes_path)}")
                return jsonify({
                    "success": False,
                    "error": "File delle classi non trovato"
                }), 404
        
        # Leggi il file delle classi
        with open(classes_path, 'r', encoding='utf-8') as f:
            classes_data = json.load(f)
        
        # Verifica se la classe richiesta esiste
        if classe_id not in classes_data:
            return jsonify({
                "success": False,
                "error": f"Classe '{classe_id}' non trovata"
            }), 404
            
        # Ottieni i dati della classe
        classe_info = classes_data[classe_id]
        classe_info["id"] = classe_id
            
        return jsonify({
            "success": True,
            "classe": classe_info
        })
    except Exception as e:
        logger.error(f"Errore nel recupero della classe: {e}")
        return jsonify({
            "success": False,
            "error": f"Errore interno: {str(e)}"
        }), 500 