from flask import Blueprint, request, jsonify
from server.utils.session import get_session, salva_sessione
import logging

# Configura il logger
logger = logging.getLogger(__name__)

# Crea blueprint per le route della scelta mappa
scelta_mappa_routes = Blueprint('scelta_mappa_routes', __name__)

@scelta_mappa_routes.route("/liste_mappe", methods=['GET'])
def get_liste_mappe():
    """Ottiene la lista di tutte le mappe disponibili"""
    id_sessione = request.args.get('id_sessione')
    if not id_sessione:
        return jsonify({"success": False, "error": "ID sessione mancante"}), 400
        
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni la lista delle mappe dal gestore
    try:
        lista_mappe = sessione.gestore_mappe.ottieni_lista_mappe()
        
        # Aggiungi anche la mappa corrente del giocatore come informazione separata
        mappa_corrente = sessione.giocatore.mappa_corrente
        
        # Log dettagliato della risposta
        logger.info(f"Liste mappe per sessione {id_sessione}: {lista_mappe}")
        logger.info(f"Mappa corrente del giocatore: {mappa_corrente}")
        
        # Restituisci la lista delle mappe
        response = {
            "success": True, 
            "mappe": lista_mappe,
            "mappa_corrente": mappa_corrente
        }
        
        logger.info(f"Risposta completa: {response}")
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"Errore nel recupero delle mappe: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@scelta_mappa_routes.route("/cambia_mappa", methods=['POST'])
def cambia_mappa():
    """Cambia la mappa corrente del giocatore"""
    data = request.json
    if not data or 'id_sessione' not in data or 'id_mappa' not in data:
        return jsonify({"success": False, "error": "Dati mancanti"}), 400
    
    id_sessione = data['id_sessione']
    id_mappa = data['id_mappa']
    
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni la mappa e verifica i requisiti
    lista_mappe = sessione.gestore_mappe.ottieni_lista_mappe()
    if id_mappa not in lista_mappe:
        return jsonify({"success": False, "error": "Mappa non disponibile"}), 404
    
    # Verifica il livello minimo richiesto
    info_mappa = lista_mappe[id_mappa]
    livello_min = info_mappa.get("livello_min", 0)
    if sessione.giocatore.livello < livello_min:
        return jsonify({
            "success": False, 
            "error": f"Livello insufficiente! Devi essere almeno di livello {livello_min}."
        }), 403
    
    # Ottieni la mappa e le coordinate iniziali
    mappa = sessione.gestore_mappe.ottieni_mappa(id_mappa)
    if not mappa:
        return jsonify({"success": False, "error": "Impossibile caricare la mappa"}), 500
    
    x, y = mappa.pos_iniziale_giocatore
    
    # Cambia la mappa corrente
    try:
        success = sessione.cambia_mappa(id_mappa, x, y)
        
        if success:
            # Salva la sessione aggiornata
            salva_sessione(id_sessione, sessione)
            
            return jsonify({
                "success": True,
                "mappa": id_mappa,
                "posizione": {"x": x, "y": y}
            })
        else:
            return jsonify({
                "success": False, 
                "error": "Impossibile viaggiare verso questa destinazione."
            }), 500
    except Exception as e:
        logger.error(f"Errore nel cambio mappa: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@scelta_mappa_routes.route("/stato", methods=['GET'])
def get_stato_scelta_mappa():
    """Ottiene lo stato corrente di SceltaMappaState"""
    id_sessione = request.args.get('id_sessione')
    if not id_sessione:
        return jsonify({"success": False, "error": "ID sessione mancante"}), 400
        
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni lo stato scelta_mappa dalla sessione
    scelta_mappa_state = sessione.get_state("scelta_mappa")
    if not scelta_mappa_state:
        return jsonify({"success": False, "error": "Stato scelta_mappa non disponibile"}), 404
    
    # Restituisci lo stato
    return jsonify({
        "success": True, 
        "stato": scelta_mappa_state.to_dict()
    }) 