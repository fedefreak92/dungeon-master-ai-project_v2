from flask import Blueprint, request, jsonify
from server.utils.session import get_session, salva_sessione
import logging

# Configura il logger
logger = logging.getLogger(__name__)

# Crea blueprint per le route del dialogo
dialogo_routes = Blueprint('dialogo_routes', __name__)

@dialogo_routes.route("/stato", methods=['GET'])
def get_dialogo_state():
    """Ottiene lo stato attuale del dialogo"""
    id_sessione = request.args.get('id_sessione')
    if not id_sessione:
        return jsonify({"success": False, "error": "ID sessione mancante"}), 400
        
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni lo stato dialogo dalla sessione
    dialogo_state = sessione.get_state("dialogo")
    if not dialogo_state:
        return jsonify({"success": False, "error": "Stato dialogo non disponibile"}), 404
    
    # Restituisci i dati del dialogo
    return jsonify({
        "success": True, 
        "stato": dialogo_state.to_dict()
    })

@dialogo_routes.route("/interagisci", methods=['POST'])
def interagisci_dialogo():
    """Gestisce l'interazione con un NPG nel dialogo"""
    data = request.json
    if not data or 'id_sessione' not in data or 'npg_id' not in data:
        return jsonify({"success": False, "error": "Dati mancanti"}), 400
    
    id_sessione = data['id_sessione']
    npg_id = data['npg_id']
    
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni lo stato dialogo dalla sessione
    dialogo_state = sessione.get_state("dialogo")
    if not dialogo_state:
        return jsonify({"success": False, "error": "Stato dialogo non disponibile"}), 404
    
    # Verifica se l'NPG esiste
    if not dialogo_state.npg or dialogo_state.npg.id != npg_id:
        return jsonify({"success": False, "error": "NPG non trovato"}), 404
    
    # Avvia o continua il dialogo
    dialogo_corrente = dialogo_state.npg.ottieni_conversazione(dialogo_state.stato_corrente)
    
    # Salva la sessione aggiornata
    salva_sessione(id_sessione, sessione)
    
    return jsonify({
        "success": True,
        "dialogo": dialogo_corrente
    })

@dialogo_routes.route("/scelta", methods=['POST'])
def gestisci_scelta_dialogo():
    """Gestisce una scelta fatta durante il dialogo"""
    data = request.json
    if not data or 'id_sessione' not in data or 'scelta_indice' not in data:
        return jsonify({"success": False, "error": "Dati mancanti"}), 400
    
    id_sessione = data['id_sessione']
    scelta_indice = data['scelta_indice']
    
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni lo stato dialogo dalla sessione
    dialogo_state = sessione.get_state("dialogo")
    if not dialogo_state:
        return jsonify({"success": False, "error": "Stato dialogo non disponibile"}), 404
    
    # Ottieni i dati della conversazione
    dati_conversazione = dialogo_state.npg.ottieni_conversazione(dialogo_state.stato_corrente)
    
    # Verifica che l'opzione sia valida
    if not dati_conversazione or not dati_conversazione.get("opzioni") or scelta_indice >= len(dati_conversazione["opzioni"]):
        return jsonify({"success": False, "error": "Scelta non valida"}), 400
        
    # Ottieni la destinazione
    _, destinazione = dati_conversazione["opzioni"][scelta_indice]
    
    # Gestisci la destinazione
    if destinazione is None:
        # Termina il dialogo
        sessione.pop_stato()
        dialogo_corrente = None
    else:
        # Aggiorna lo stato del dialogo
        dialogo_state.stato_corrente = destinazione
        dialogo_state.dati_contestuali["mostrato_dialogo_corrente"] = False
        
        # Ottieni il nuovo dialogo
        dialogo_corrente = dialogo_state.npg.ottieni_conversazione(dialogo_state.stato_corrente)
    
    # Salva la sessione aggiornata
    salva_sessione(id_sessione, sessione)
    
    return jsonify({
        "success": True,
        "dialogo": dialogo_corrente,
        "terminato": destinazione is None
    })

@dialogo_routes.route("/effetto", methods=['POST'])
def gestisci_effetto_dialogo():
    """Gestisce un effetto durante il dialogo"""
    data = request.json
    if not data or 'id_sessione' not in data or 'effetto' not in data:
        return jsonify({"success": False, "error": "Dati mancanti"}), 400
    
    id_sessione = data['id_sessione']
    effetto = data['effetto']
    
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni lo stato dialogo dalla sessione
    dialogo_state = sessione.get_state("dialogo")
    if not dialogo_state:
        return jsonify({"success": False, "error": "Stato dialogo non disponibile"}), 404
    
    # Gestisci l'effetto
    dialogo_state._gestisci_effetto(effetto, sessione)
    
    # Salva la sessione aggiornata
    salva_sessione(id_sessione, sessione)
    
    return jsonify({
        "success": True
    }) 