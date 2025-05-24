from flask import Blueprint, jsonify, request, current_app
from util.logging_config import get_logger

logger = get_logger(__name__)
mercato_routes = Blueprint('mercato_routes', __name__)

# Nessuna route definita qui ora, sono state spostate in luogo_routes.py
logger.info("mercato_routes.py caricato (ma le route sono ora in luogo_routes.py)") 