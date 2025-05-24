"""
Pacchetto routes per definire le route dell'applicazione Flask

Contiene moduli per le route suddivise per funzionalità.
"""

from flask import Blueprint
import logging

# Configura logger
logger = logging.getLogger(__name__)

# Importa i blueprint delle route con gestione degli errori

def _import_blueprint(module_name_str, blueprint_name_str, fallback_name_str):
    """Helper per importare un blueprint o crearne uno di fallback."""
    try:
        module = __import__(f"server.routes.{module_name_str}", fromlist=[blueprint_name_str])
        return getattr(module, blueprint_name_str)
    except ImportError:
        logger.warning(f"Modulo server.routes.{module_name_str} non trovato o errore di import per {blueprint_name_str}, creo un Blueprint di fallback '{fallback_name_str}'.")
        return Blueprint(fallback_name_str, __name__)
    except AttributeError:
        logger.error(f"ERRORE CRITICO: Modulo server.routes.{module_name_str} importato, MA non contiene un oggetto '{blueprint_name_str}'. Verificare {module_name_str}.py. Creo fallback.")
        return Blueprint(fallback_name_str, __name__)

base_routes = _import_blueprint("base_routes", "base_routes", "base_routes_fallback")
classes_routes = _import_blueprint("classes_routes", "classes_routes", "classes_routes_fallback")
entity_routes = _import_blueprint("entity_routes", "entity_routes", "entity_routes_fallback")
mappa_routes = _import_blueprint("mappa_routes", "mappa_routes", "mappa_routes_fallback")
scelta_mappa_routes = _import_blueprint("scelta_mappa_routes", "scelta_mappa_routes", "scelta_mappa_routes_fallback")
session_routes = _import_blueprint("session_routes", "session_routes", "session_routes_fallback")
combat_routes = _import_blueprint("combat_routes", "combat_routes", "combat_routes_fallback")
dialogo_routes = _import_blueprint("dialogo_routes", "dialogo_routes", "dialogo_routes_fallback")
inventory_routes = _import_blueprint("inventory_routes", "inventory_routes", "inventory_routes_fallback")
luogo_routes = _import_blueprint("luogo_routes", "luogo_routes", "luogo_routes_fallback")
save_routes = _import_blueprint("save_routes", "save_routes", "save_routes_fallback")
skill_challenge_routes = _import_blueprint("skill_challenge_routes", "skill_challenge_routes", "skill_challenge_routes_fallback")
entity_api = _import_blueprint("entity_api", "entity_api", "entity_api_fallback") # Potrebbe essere entity_api.entity_api
health_api = _import_blueprint("health_api", "health_api", "health_api_fallback")
assets_routes = _import_blueprint("assets_routes", "assets_routes", "assets_routes_fallback")
api_diagnostics = _import_blueprint("api_diagnostics", "api_diagnostics", "api_diagnostics_fallback")

# Importa la configurazione JSON standard
try:
    from server.utils.route_config import configure_blueprint_json
except ImportError:
    logger.error("Impossibile importare il supporto JSON standard, le routes utilizzeranno le impostazioni predefinite")
    configure_blueprint_json = lambda bp: bp  # Funzione nulla

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

# Applica JSON standard a tutti i blueprint
blueprint_list = [
    base_routes, classes_routes, entity_routes, mappa_routes, scelta_mappa_routes,
    session_routes, combat_routes, dialogo_routes, inventory_routes,
    save_routes,
    skill_challenge_routes, entity_api, health_api,
    assets_routes, api_diagnostics, api_routes, assets_api, maps_api, sessions_api,
    entities_api, diagnostics_api, main_routes, character_creation_routes, auth_routes,
    main_blueprint,
    luogo_routes
]

# Configura JSON standard per tutti i blueprint
for bp in blueprint_list:
    configure_blueprint_json(bp)

# Registra tutti i blueprint nel blueprint principale
main_blueprint.register_blueprint(main_routes)
main_blueprint.register_blueprint(combat_routes, url_prefix='/combat')
main_blueprint.register_blueprint(character_creation_routes, url_prefix='/character_creation')
main_blueprint.register_blueprint(auth_routes, url_prefix='/auth')
main_blueprint.register_blueprint(skill_challenge_routes, url_prefix='/skill_challenge')
main_blueprint.register_blueprint(api_diagnostics, url_prefix='/api/diagnostics')
main_blueprint.register_blueprint(health_api, url_prefix='/api')

# Blueprint principale che conterrà tutti gli altri
game_api = Blueprint('game_api', __name__)
configure_blueprint_json(game_api)

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
    
    # Nota: register_game_routes è chiamato da app.py/setup, quindi non è necessario chiamarlo di nuovo qui
    # a meno che la logica di setup non sia cambiata.
    # Per sicurezza e pulizia, assicuriamoci che sia chiamato una sola volta o che la logica sia chiara.
    # Se create_app() in app.py chiama register_routes(app), allora register_game_routes va bene qui.
    # Se app.py chiama register_game_routes separatamente, allora commenta la riga sotto.
    # register_game_routes(app) # Assumiamo che sia già gestito o da chiamare qui a seconda del flusso di app.py

    # Elenco dei blueprint da registrare direttamente sull'app principale
    # con i loro prefissi e nomi univoci per evitare conflitti.
    direct_blueprints_to_register = [
        (base_routes, {"url_prefix": '/game', "name": 'base_routes_direct'}),
        (session_routes, {"url_prefix": '/game/session', "name": 'session_routes_direct'}),
        (save_routes, {"url_prefix": '/game/save', "name": 'save_routes_direct'}),
        (skill_challenge_routes, {"url_prefix": '/game/skill_challenge', "name": 'skill_challenge_routes_direct'}),
        (combat_routes, {"url_prefix": '/game/combat', "name": 'combat_routes_direct'}), # Verificare se già in main_blueprint
        (scelta_mappa_routes, {"url_prefix": '/game/scelta_mappa', "name": 'scelta_mappa_routes_direct'}),
        (dialogo_routes, {"url_prefix": '/game/dialogo', "name": 'dialogo_routes_direct'}),
        (entity_routes, {"url_prefix": '/game/entity', "name": 'entity_routes_direct'}),
        (inventory_routes, {"url_prefix": '/game/inventory', "name": 'inventory_routes_direct'}),
        (mappa_routes, {"url_prefix": '/mappa', "name": 'mappa_routes_direct'}),
        (classes_routes, {"url_prefix": '/game/classes', "name": 'classes_routes_direct'}),
        (luogo_routes, {"url_prefix": '/luogo', "name": 'luogo_routes_direct'}), # Prefisso cambiato a /luogo
        
        # API blueprints (se non già registrati tramite game_api)
        # Se game_api è registrato su /api, questi potrebbero essere registrati su game_api o direttamente sull'app
        # con prefisso /api.
        # Per ora, li registro direttamente sull'app per coerenza con la vecchia struttura, ma potrebbe essere meglio
        # annidarli sotto game_api.
        (entity_api, {"url_prefix": '/api', "name": 'entity_api_direct'}), 
        (api_diagnostics, {"url_prefix": '/api', "name": 'api_diagnostics_direct'}), 
        (health_api, {"url_prefix": '/api', "name": 'health_api_direct'}), 
        
        (assets_routes, {"name": 'assets_routes_direct'}) # Assets di solito non ha prefisso /game o /api
    ]

    # Registra i blueprint definiti sopra
    for bp_object, bp_config in direct_blueprints_to_register:
        bp_name_for_log = bp_config.get('name', getattr(bp_object, 'name', 'unknown_blueprint'))
        if isinstance(bp_object, Blueprint):
            logger.info(f"[ROUTES INIT] Registrazione blueprint: {bp_name_for_log} con tipo {type(bp_object)} e config {bp_config}")
            app.register_blueprint(bp_object, **bp_config) # Uso **bp_config per passare tutti gli argomenti
        else:
            logger.error(f"[ROUTES INIT] ERRORE: Oggetto per '{bp_name_for_log}' NON è un Blueprint. Tipo: {type(bp_object)}. SALTO REGISTRAZIONE.")

    # Registrazione speciale per api_map (se esiste)
    try:
        from server.routes.api_map import api_map 
        if isinstance(api_map, Blueprint):
            logger.info(f"[ROUTES INIT] Registrazione blueprint api_map con tipo {type(api_map)}")
            app.register_blueprint(api_map, url_prefix='/api/map', name='api_map_direct')
        else:
            logger.error(f"[ROUTES INIT] ERRORE: server.routes.api_map.api_map NON è un Blueprint. Tipo: {type(api_map)}. SALTO REGISTRAZIONE.")
    except (ImportError, AttributeError) as e:
        logger.warning(f"Blueprint 'api_map' non trovato o errore durante import/registrazione: {e}, saltato")
    
    # La registrazione di game_api e main_blueprint (che annidano altri blueprint) 
    # dovrebbe avvenire preferibilmente in app.py o in una funzione di setup specifica 
    # per evitare registrazioni multiple o confusione.
    # Se register_game_routes() è il modo corretto, assicurati che venga chiamata una sola volta.
    # Per ora, commento la chiamata a register_game_routes() qui, assumendo che create_app la gestisca.
    # register_game_routes(app)

    # Applica il supporto JSON standard a tutti i blueprint dell'app
    try:
        from server.utils.route_config import apply_json_to_all_routes
        apply_json_to_all_routes(app)
        logger.info("Supporto JSON standard applicato a tutte le routes")
    except ImportError:
        logger.error("Impossibile importare il supporto JSON standard globale")
    
    logger.info("Route registrate con successo")

# Esponi tutti i blueprint per una facile importazione
__all__ = [
    'main_blueprint',
    'main_routes',
    'combat_routes',
    'character_creation_routes',
    'auth_routes',
    'skill_challenge_routes',
    'api_diagnostics',
    'health_api',
    'game_api',
    'api_routes',
    'entity_api',
    'luogo_routes',
    'register_routes'
] 