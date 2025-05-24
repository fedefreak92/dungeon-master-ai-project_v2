# gioco_rpg/server/routes/luogo_routes.py

from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from util.logging_config import get_logger
from states.mappa.mappa_state import MappaState
from server.websocket.websocket_manager import WebSocketManager
import functools

logger = get_logger(__name__)
luogo_routes = Blueprint('luogo_routes', __name__, url_prefix='/luogo') # Aggiunto prefisso URL

def luogo_context_required(nome_luogo_atteso_route: str = None):
    """
    Decorator generico per route HTTP relative ai luoghi.
    Richiede che l'utente sia loggato, attivo in una sessione di gioco
    e si trovi nello stato MappaState corretto.
    Se nome_luogo_atteso_route è fornito, valida anche che corrisponda
    al nome_luogo estratto dall'URL.
    Inietta stato_luogo e player_instance nella funzione decorata.
    """
    def decorator(f):
        @login_required
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Estrai nome_luogo dai parametri della route URL se presente
            nome_luogo_url = kwargs.get('nome_luogo')

            # Controllo di coerenza opzionale se fornito nome_luogo_atteso_route
            if nome_luogo_atteso_route and nome_luogo_atteso_route != nome_luogo_url:
                 logger.error(f"Incoerenza nel decorator luogo_context_required: atteso '{nome_luogo_atteso_route}', ricevuto '{nome_luogo_url}' dalla route URL.")
                 return jsonify({"errore": "Errore di configurazione del server."}), 500
            
            # Se nome_luogo_atteso_route non è fornito, usiamo quello dall'URL per la validazione
            nome_luogo_validazione = nome_luogo_url if nome_luogo_url else nome_luogo_atteso_route
            if not nome_luogo_validazione:
                 logger.error("Nome luogo per validazione mancante in luogo_context_required.")
                 return jsonify({"errore": "Errore di configurazione del server (nome luogo mancante)."}), 500

            websocket_manager = WebSocketManager.get_instance()
            if not websocket_manager:
                 logger.error("WebSocketManager non disponibile in luogo_context_required.")
                 return jsonify({"errore": "Errore interno del server (WS Manager)"}), 500

            player_instance = None
            if current_user and hasattr(current_user, 'id'):
                if hasattr(websocket_manager, 'get_player_instance_by_user_id'):
                    player_instance = websocket_manager.get_player_instance_by_user_id(current_user.id)
            
            if not player_instance:
                logger.warning(f"Istanza giocatore attiva non trovata per user {getattr(current_user, 'id', 'N/A')} in luogo_context_required.")
                return jsonify({"errore": "Sessione di gioco attiva non trovata."}), 403 

            stato_corrente = player_instance.stato_corrente
            if not stato_corrente:
                 logger.warning(f"Stato corrente non trovato per user {current_user.id} in luogo_context_required.")
                 return jsonify({"errore": "Stato di gioco non valido."}), 404
                 
            # Validazione tipo stato E nome luogo (usando nome_luogo_validazione)
            if not (isinstance(stato_corrente, MappaState) and stato_corrente.nome_luogo == nome_luogo_validazione):
                logger.warning(f"Accesso API a /luogo/{nome_luogo_validazione} fallito. User: {current_user.id}, Stato attuale: {type(stato_corrente).__name__}, Luogo attuale: {getattr(stato_corrente, 'nome_luogo', 'N/A')}")
                return jsonify({"errore": f"Non sei attualmente nel luogo richiesto ({nome_luogo_validazione})."}), 403
                
            # Verifica contesto gioco nello stato
            game_context_ok = False
            if hasattr(stato_corrente, 'gioco') and stato_corrente.gioco and \
               hasattr(stato_corrente.gioco, 'giocatore') and stato_corrente.gioco.giocatore == player_instance:
                game_context_ok = True
            
            if not game_context_ok:
                logger.error(f"Contesto gioco non valido nello stato {stato_corrente.nome_stato} per user {current_user.id}")
                return jsonify({"errore": "Errore interno: stato non sincronizzato."}), 500

            # Inietta stato e giocatore
            # Passa anche nome_luogo_url se la funzione decorata lo necessita
            kwargs_to_pass = kwargs.copy()
            if nome_luogo_url:
                 kwargs_to_pass['nome_luogo_url'] = nome_luogo_url # Usa nome diverso per evitare conflitti

            return f(stato_luogo=stato_corrente, player_instance=player_instance, *args, **kwargs_to_pass)
        return decorated_function
    return decorator

# --- Route Generiche ---

@luogo_routes.route("/<string:nome_luogo>/stato", methods=['GET'])
@luogo_context_required() # nome_luogo viene preso dall'URL
def get_luogo_state(stato_luogo, player_instance, nome_luogo_url):
    """Ottiene lo stato attuale del luogo specificato."""
    logger.info(f"API Luogo: Richiesta GET /{nome_luogo_url}/stato da user {player_instance.user_id}")
    try:
        serializer = getattr(stato_luogo, 'to_dict_per_client', getattr(stato_luogo, 'to_dict', None))
        if serializer:
            dati_stato = serializer()
            return jsonify(dati_stato), 200
        else:
             logger.error(f"Stato {stato_luogo.nome_stato} per user {player_instance.user_id} non ha un metodo di serializzazione.")
             return jsonify({"errore": "Errore interno nel recupero dello stato."}), 500
    except Exception as e:
        logger.error(f"Errore serializzazione stato {stato_luogo.nome_stato} per user {player_instance.user_id}: {e}", exc_info=True)
        return jsonify({"errore": "Errore interno nel formato dello stato."}), 500

# Esempio per /articoli (generalizzazione di /articoli_disponibili del mercato)
@luogo_routes.route("/<string:nome_luogo>/articoli", methods=['GET'])
@luogo_context_required()
def get_luogo_items(stato_luogo, player_instance, nome_luogo_url):
    """Ottiene la lista degli articoli disponibili nel luogo specificato (se applicabile)."""
    logger.info(f"API Luogo: Richiesta GET /{nome_luogo_url}/articoli da user {player_instance.user_id}")
    try:
        if hasattr(stato_luogo, 'get_articoli_disponibili'): # Metodo ipotetico
            # Passa l'istanza del giocatore per eventuali modificatori di prezzo/disponibilità
            articoli = stato_luogo.get_articoli_disponibili(player_instance)
            return jsonify({"success": True, "articoli": articoli}), 200
        else:
            # Se il luogo non ha articoli (non è un negozio, ecc.)
            logger.info(f"Il luogo '{nome_luogo_url}' non supporta la visualizzazione di articoli.")
            return jsonify({"success": True, "articoli": {}, "messaggio": "Nessun articolo disponibile in questo luogo."}), 200
    except Exception as e:
        logger.error(f"Errore API /{nome_luogo_url}/articoli per user {player_instance.user_id}: {e}", exc_info=True)
        return jsonify({"success": False, "errore": "Errore nel recupero articoli."}), 500

# Esempio per /compra (generalizzazione di /compra del mercato)
@luogo_routes.route("/<string:nome_luogo>/compra", methods=['POST'])
@luogo_context_required()
def post_luogo_compra(stato_luogo, player_instance, nome_luogo_url):
    """Gestisce l'acquisto di un oggetto nel luogo specificato via HTTP."""
    data = request.json
    item_id = data.get('item_id')
    quantita = data.get('quantita', 1)
    
    if not item_id: return jsonify({"success": False, "errore": "ID oggetto mancante"}), 400
    if not isinstance(quantita, int) or quantita <= 0: return jsonify({"success": False, "errore": "Quantità non valida"}), 400

    logger.info(f"API Luogo: Richiesta POST /{nome_luogo_url}/compra da user {player_instance.user_id}. Item: {item_id}, Qty: {quantita}")
    try:
        # Delega l'azione allo stato MappaState, usando l'azione "compra"
        azione_data = {"item_id": item_id, "quantita": quantita}
        # MappaState/MercatoState._handle_azione_specifica_luogo deve gestire "compra"
        stato_luogo.process_azione_luogo(user_id=player_instance.user_id, azione="compra", dati_azione=azione_data)
        return jsonify({"success": True, "messaggio": f"Richiesta di acquisto per {item_id} inviata."}), 202 # Accepted
    except Exception as e: # TODO: Gestire eccezioni specifiche (DenaroInsufficiente, OggettoNonDisponibile, AzioneNonSupportata)
        logger.error(f"Errore API /{nome_luogo_url}/compra per user {player_instance.user_id}: {e}", exc_info=True)
        return jsonify({"success": False, "errore": f"Errore durante l'acquisto: {str(e)}"}), 500

# Esempio per /vendi (generalizzazione di /vendi del mercato)
@luogo_routes.route("/<string:nome_luogo>/vendi", methods=['POST'])
@luogo_context_required()
def post_luogo_vendi(stato_luogo, player_instance, nome_luogo_url):
    """Gestisce la vendita di un oggetto nel luogo specificato via HTTP."""
    data = request.json
    item_id = data.get('item_id')
    quantita = data.get('quantita', 1)
    
    if not item_id: return jsonify({"success": False, "errore": "ID oggetto mancante"}), 400
    if not isinstance(quantita, int) or quantita <= 0: return jsonify({"success": False, "errore": "Quantità non valida"}), 400

    logger.info(f"API Luogo: Richiesta POST /{nome_luogo_url}/vendi da user {player_instance.user_id}. Item: {item_id}, Qty: {quantita}")
    try:
        # Delega l'azione allo stato MappaState, usando l'azione "vendi"
        azione_data = {"item_id": item_id, "quantita": quantita}
        # MappaState/MercatoState._handle_azione_specifica_luogo deve gestire "vendi"
        stato_luogo.process_azione_luogo(user_id=player_instance.user_id, azione="vendi", dati_azione=azione_data)
        return jsonify({"success": True, "messaggio": f"Richiesta di vendita per {item_id} inviata."}), 202 # Accepted
    except Exception as e: # TODO: Gestire eccezioni specifiche (OggettoNonInInventario, AzioneNonSupportata)
        logger.error(f"Errore API /{nome_luogo_url}/vendi per user {player_instance.user_id}: {e}", exc_info=True)
        return jsonify({"success": False, "errore": f"Errore durante la vendita: {str(e)}"}), 500

# Nota: Le azioni che modificano lo stato sono spesso gestite meglio via WebSocket per feedback real-time.
# Le route POST qui sono mantenute per possibile compatibilità o usi specifici, ma la loro
# utilità a lungo termine va valutata rispetto all'approccio WebSocket. 