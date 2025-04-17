"""
Pacchetto routes per definire le route dell'applicazione Flask

Contiene moduli per le route suddivise per funzionalità.
"""

from flask import Blueprint

# Importa i blueprint dalle route specifiche
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

# Crea un blueprint principale per aggregare tutte le route di gioco
game_routes = Blueprint('game_routes', __name__)

# Registra tutti i blueprint sotto la route principale
game_routes.register_blueprint(session_routes, url_prefix='/session')
game_routes.register_blueprint(save_routes, url_prefix='/save')
game_routes.register_blueprint(skill_challenge_routes, url_prefix='/skill_challenge')
game_routes.register_blueprint(combat_routes, url_prefix='/combat')
game_routes.register_blueprint(taverna_routes, url_prefix='/taverna')
game_routes.register_blueprint(mercato_routes, url_prefix='/mercato')
game_routes.register_blueprint(scelta_mappa_routes, url_prefix='/scelta_mappa')
game_routes.register_blueprint(dialogo_routes, url_prefix='/dialogo')
game_routes.register_blueprint(entity_routes, url_prefix='/entity')
game_routes.register_blueprint(inventory_routes, url_prefix='/inventory')
# Nota: mappa_routes viene registrato direttamente nell'app con prefisso /mappa
# e non sotto /game/mappa per mantenere la compatibilità con i test esistenti

# Funzione per registrare tutte le route nell'app Flask
def register_game_routes(app):
    app.register_blueprint(game_routes, url_prefix='/game') 