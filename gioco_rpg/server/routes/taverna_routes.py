from flask import Blueprint, jsonify, request, current_app
from util.logging_config import get_logger

logger = get_logger(__name__)
taverna_routes = Blueprint('taverna_routes', __name__)

# Nessuna route definita qui ora, sono state spostate in luogo_routes.py
logger.info("taverna_routes.py caricato (ma le route sono ora in luogo_routes.py)") 