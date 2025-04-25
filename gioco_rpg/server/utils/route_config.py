"""
Configurazione per le routes con supporto MessagePack.

Questo modulo fornisce funzioni per configurare i blueprint Flask
per supportare MessagePack in tutte le routes.
"""

import logging
from flask import Blueprint, Flask
from functools import wraps

# Configura il logger
logger = logging.getLogger(__name__)

def configure_blueprint_for_msgpack(blueprint):
    """
    Configura un blueprint Flask per supportare MessagePack in tutte le sue routes.
    
    Args:
        blueprint: Il blueprint da configurare
        
    Returns:
        Blueprint: Il blueprint configurato
    """
    from .message_pack_middleware import supports_msgpack, accept_msgpack
    
    # Memorizza la funzione route originale
    original_route = blueprint.route
    
    # Sostituisci la funzione route con una versione che applica i decoratori MessagePack
    def route_with_msgpack(rule, **options):
        def decorator(f):
            # Applica i decoratori per MessagePack
            f = supports_msgpack(f)
            f = accept_msgpack(f)
            
            # Applica il decoratore route originale
            return original_route(rule, **options)(f)
        return decorator
    
    # Sostituisci il metodo route
    blueprint.route = route_with_msgpack
    
    logger.info(f"Blueprint {blueprint.name} configurato per supportare MessagePack")
    
    return blueprint

def configure_all_blueprints_for_msgpack(app):
    """
    Configura tutti i blueprint registrati in un'app Flask per supportare MessagePack.
    
    Args:
        app: L'applicazione Flask
        
    Returns:
        Flask: L'applicazione Flask con i blueprint configurati
    """
    for blueprint_name, blueprint in app.blueprints.items():
        configure_blueprint_for_msgpack(blueprint)
        
    logger.info(f"Tutti i {len(app.blueprints)} blueprint configurati per supportare MessagePack")
    
    return app

def apply_msgpack_to_all_routes(app):
    """
    Funzione da chiamare dopo la registrazione di tutte le routes per
    configurare il supporto MessagePack
    
    Args:
        app: L'applicazione Flask
    """
    # Configura tutti i blueprint
    configure_all_blueprints_for_msgpack(app)
    
    logger.info("Supporto MessagePack applicato a tutte le routes dell'applicazione") 