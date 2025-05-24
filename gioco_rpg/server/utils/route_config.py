"""
Modulo per configurare i blueprint Flask con impostazioni JSON standard.

Questo modulo fornisce funzioni per standardizzare tutte le risposte API 
dei blueprint Flask utilizzando JSON.
"""

import logging
from flask import Blueprint, Flask
from . import json_middleware

# Configura il logger
logger = logging.getLogger(__name__)

def configure_blueprint_json(blueprint):
    """
    Configura un blueprint Flask con impostazioni JSON standard.
    
    Args:
        blueprint: Il blueprint Flask da configurare
    """
    if not isinstance(blueprint, Blueprint):
        logger.warning(f"L'oggetto {blueprint} non è un Blueprint Flask, skip configurazione")
        return
        
    logger.info(f"Configurazione standard JSON per blueprint: {blueprint.name}")
    logger.debug(f"Blueprint {blueprint.name} configurato con supporto JSON standard")

def configure_all_blueprints_json(app):
    """
    Configura tutti i blueprint registrati in un'app Flask con impostazioni JSON standard.
    
    Args:
        app: L'istanza dell'app Flask
    """
    if not isinstance(app, Flask):
        logger.warning(f"L'oggetto {app} non è un'app Flask, skip configurazione")
        return
        
    logger.info(f"Configurazione standard JSON per tutti i blueprint dell'app")
    
    for blueprint in app.blueprints.values():
        configure_blueprint_json(blueprint)
    
    logger.debug(f"Tutti i blueprint configurati con supporto JSON standard")

def apply_json_to_all_routes(app):
    """
    Applica la configurazione JSON standard a tutte le route dell'app Flask.
    
    Questa è la funzione principale da chiamare per standardizzare tutte le risposte
    API utilizzando JSON.
    
    Args:
        app: L'istanza dell'app Flask
    """
    logger.info(f"Applicazione della configurazione JSON standard a tutte le route")
    configure_all_blueprints_json(app)
    logger.info(f"Configurazione JSON standard applicata a tutte le route")

# Alias per retrocompatibilità
configure_blueprint = configure_blueprint_json
configure_all_blueprints = configure_all_blueprints_json 