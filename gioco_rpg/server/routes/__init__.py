"""
Pacchetto routes per definire le route dell'applicazione Flask

Contiene moduli per le route suddivise per funzionalità.
"""

from flask import Blueprint
import logging

# Configura logger
logger = logging.getLogger(__name__)

# Importa i blueprint delle route con gestione degli errori

# Moduli esistenti con try-except per sicurezza
try:
    from .base_routes import base_routes
except ImportError:
    base_routes = Blueprint('base_routes', __name__)

try:
    from .classes_routes import classes_routes
except ImportError:
    classes_routes = Blueprint('classes_routes', __name__)

try:
    from .entity_routes import entity_routes
except ImportError:
    entity_routes = Blueprint('entity_routes', __name__)

try:
    from .mappa_routes import mappa_routes
except ImportError:
    mappa_routes = Blueprint('mappa_routes', __name__)

try:
    from .scelta_mappa_routes import scelta_mappa_routes
except ImportError:
    scelta_mappa_routes = Blueprint('scelta_mappa_routes', __name__)

try:
    from .session_routes import session_routes
except ImportError:
    session_routes = Blueprint('session_routes', __name__)

try:
    from .combat_routes import combat_routes
except ImportError:
    combat_routes = Blueprint('combat_routes', __name__)

try:
    from .dialogo_routes import dialogo_routes
except ImportError:
    dialogo_routes = Blueprint('dialogo_routes', __name__)

try:
    from .inventory_routes import inventory_routes
except ImportError:
    inventory_routes = Blueprint('inventory_routes', __name__)

try:
    from .mercato_routes import mercato_routes
except ImportError:
    mercato_routes = Blueprint('mercato_routes', __name__)

try:
    from .save_routes import save_routes
except ImportError:
    save_routes = Blueprint('save_routes', __name__)

try:
    from .taverna_routes import taverna_routes
except ImportError:
    taverna_routes = Blueprint('taverna_routes', __name__)

try:
    from .skill_challenge_routes import skill_challenge_routes
except ImportError:
    skill_challenge_routes = Blueprint('skill_challenge_routes', __name__)

try:
    from .entity_api import entity_api
except ImportError:
    entity_api = Blueprint('entity_api', __name__)

try:
    from .health_api import health_api
except ImportError:
    health_api = Blueprint('health_api', __name__)

try:
    from .assets_routes import assets_routes
except ImportError:
    assets_routes = Blueprint('assets_routes', __name__)

try:
    from .api_diagnostics import api_diagnostics
except ImportError:
    api_diagnostics = Blueprint('api_diagnostics', __name__)

# Importa il supporto MessagePack
try:
    from server.utils.route_config import configure_blueprint_for_msgpack
except ImportError:
    logger.error("Impossibile importare il supporto MessagePack, le routes non lo supporteranno")
    configure_blueprint_for_msgpack = lambda bp: bp  # Funzione nulla

# Moduli che non sono presenti nella directory ma vengono importati
# Creiamo blueprint vuoti come segnaposto
api_routes = Blueprint('api_routes', __name__)
assets_api = Blueprint('assets_api', __name__)
maps_api = Blueprint('maps_api', __name__)
sessions_api = Blueprint('sessions_api', __name__)
entities_api = Blueprint('entities_api', __name__)
diagnostics_api = Blueprint('diagnostics_api', __name__)
main_routes = Blueprint('main_routes', __name__)
character_creation_routes = Blueprint('character_creation_routes', __name__)
auth_routes = Blueprint('auth_routes', __name__)

# Blueprint principale che raccoglie tutte le route
main_blueprint = Blueprint('main_blueprint', __name__)

# Applica MessagePack a tutti i blueprint
blueprint_list = [
    base_routes, classes_routes, entity_routes, mappa_routes, scelta_mappa_routes,
    session_routes, combat_routes, dialogo_routes, inventory_routes, mercato_routes,
    save_routes, taverna_routes, skill_challenge_routes, entity_api, health_api,
    assets_routes, api_diagnostics, api_routes, assets_api, maps_api, sessions_api,
    entities_api, diagnostics_api, main_routes, character_creation_routes, auth_routes,
    main_blueprint
]

# Configura MessagePack per tutti i blueprint
for bp in blueprint_list:
    configure_blueprint_for_msgpack(bp)

# Registra tutti i blueprint nel blueprint principale
main_blueprint.register_blueprint(main_routes)
main_blueprint.register_blueprint(combat_routes, url_prefix='/combat')
main_blueprint.register_blueprint(character_creation_routes, url_prefix='/character_creation')
main_blueprint.register_blueprint(auth_routes, url_prefix='/auth')
main_blueprint.register_blueprint(taverna_routes, url_prefix='/tavern')
main_blueprint.register_blueprint(skill_challenge_routes, url_prefix='/skill_challenge')
main_blueprint.register_blueprint(api_diagnostics, url_prefix='/api/diagnostics')
main_blueprint.register_blueprint(health_api, url_prefix='/api')

# Blueprint principale che conterrà tutti gli altri
game_api = Blueprint('game_api', __name__)
configure_blueprint_for_msgpack(game_api)

# Registra i blueprint per le varie API
game_api.register_blueprint(assets_api, url_prefix='/assets')
game_api.register_blueprint(maps_api, url_prefix='/maps')
game_api.register_blueprint(sessions_api, url_prefix='/sessions')
game_api.register_blueprint(entities_api, url_prefix='/entities')
game_api.register_blueprint(diagnostics_api, url_prefix='/diagnostics')

# Funzione per registrare tutte le route nell'app Flask
def register_game_routes(app):
    """
    Registra tutte le routes dell'applicazione
    
    Args:
        app: L'istanza dell'applicazione Flask
    """
    # Registra il blueprint principale con un prefisso
    app.register_blueprint(game_api, url_prefix='/api')
    app.register_blueprint(main_blueprint, url_prefix='/game')

# Funzione che registra tutte le route nell'app Flask
def register_routes(app):
    """
    Registra tutte le route API e Web dell'applicazione
    
    Args:
        app: L'istanza dell'applicazione Flask
    """
    logger.info("Registrazione delle route nell'applicazione")
    
    # Utilizziamo register_game_routes che già registra main_blueprint
    register_game_routes(app)
    
    # Registra i blueprint principali con nomi univoci
    app.register_blueprint(base_routes, url_prefix='/game', name='base_routes_direct')
    app.register_blueprint(session_routes, url_prefix='/game/session', name='session_routes_direct')
    app.register_blueprint(save_routes, url_prefix='/game/save', name='save_routes_direct')
    app.register_blueprint(skill_challenge_routes, url_prefix='/game/skill_challenge', name='skill_challenge_routes_direct')
    app.register_blueprint(combat_routes, url_prefix='/game/combat', name='combat_routes_direct')
    app.register_blueprint(taverna_routes, url_prefix='/game/taverna', name='taverna_routes_direct')
    app.register_blueprint(mercato_routes, url_prefix='/game/mercato', name='mercato_routes_direct')
    app.register_blueprint(scelta_mappa_routes, url_prefix='/game/scelta_mappa', name='scelta_mappa_routes_direct')
    app.register_blueprint(dialogo_routes, url_prefix='/game/dialogo', name='dialogo_routes_direct')
    app.register_blueprint(entity_routes, url_prefix='/game/entity', name='entity_routes_direct')
    app.register_blueprint(inventory_routes, url_prefix='/game/inventory', name='inventory_routes_direct')
    app.register_blueprint(mappa_routes, url_prefix='/mappa', name='mappa_routes_direct')
    app.register_blueprint(classes_routes, url_prefix='/game/classes', name='classes_routes_direct')
    
    # Registra i blueprint per le API con nomi univoci
    app.register_blueprint(entity_api, url_prefix='/api', name='entity_api_direct')
    try:
        from server.routes.api_map import api_map  # Importo il nome corretto 'api_map'
        app.register_blueprint(api_map, url_prefix='/api/map', name='api_map_direct')
    except (ImportError, AttributeError) as e:
        logger.warning(f"Blueprint 'api_map' non trovato o errore durante import/registrazione: {e}, saltato")
    
    app.register_blueprint(api_diagnostics, url_prefix='/api', name='api_diagnostics_direct')
    app.register_blueprint(health_api, url_prefix='/api', name='health_api_direct')
    
    # Registra il blueprint per gli assets
    app.register_blueprint(assets_routes, name='assets_routes_direct')
    
    # Applica il supporto MessagePack a tutti i blueprint dell'app
    try:
        from server.utils.route_config import apply_msgpack_to_all_routes
        # Esegui dopo la registrazione di tutti i blueprint
        apply_msgpack_to_all_routes(app)
        logger.info("Supporto MessagePack applicato a tutte le routes")
    except ImportError:
        logger.error("Impossibile importare il supporto MessagePack globale")
    
    logger.info("Route registrate con successo")

# Esponi tutti i blueprint per una facile importazione
__all__ = [
    'main_blueprint',
    'main_routes',
    'combat_routes',
    'character_creation_routes',
    'auth_routes',
    'taverna_routes',
    'skill_challenge_routes',
    'api_diagnostics',
    'health_api',
    'game_api',
    'api_routes',
    'entity_api',
    'register_routes'
] 