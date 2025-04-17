from flask import Blueprint, request, jsonify
from server.utils.session import get_session, salva_sessione
import logging

# Configura il logger
logger = logging.getLogger(__name__)

# Crea blueprint per le route della taverna
taverna_routes = Blueprint('taverna_routes', __name__)

@taverna_routes.route("/stato", methods=['GET'])
def get_taverna_state():
    """Ottiene lo stato attuale della taverna"""
    id_sessione = request.args.get('id_sessione')
    if not id_sessione:
        return jsonify({"success": False, "error": "ID sessione mancante"}), 400
        
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni lo stato taverna dalla sessione
    taverna_state = sessione.get_state("taverna")
    if not taverna_state:
        return jsonify({"success": False, "error": "Stato taverna non disponibile"}), 404
    
    # Restituisci i dati della taverna
    return jsonify({
        "success": True, 
        "stato": taverna_state.to_dict()
    })

@taverna_routes.route("/interagisci", methods=['POST'])
def interagisci_oggetto():
    """Gestisce l'interazione con un oggetto nella taverna"""
    data = request.json
    if not data or 'id_sessione' not in data or 'oggetto_id' not in data:
        return jsonify({"success": False, "error": "Dati mancanti"}), 400
    
    id_sessione = data['id_sessione']
    oggetto_id = data['oggetto_id']
    
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni lo stato taverna dalla sessione
    taverna_state = sessione.get_state("taverna")
    if not taverna_state:
        return jsonify({"success": False, "error": "Stato taverna non disponibile"}), 404
    
    # Verifica se l'oggetto esiste
    if oggetto_id not in taverna_state.oggetti_interattivi:
        return jsonify({"success": False, "error": "Oggetto non trovato"}), 404
    
    # Esegui l'interazione con l'oggetto
    oggetto = taverna_state.oggetti_interattivi[oggetto_id]
    risultato = oggetto.interagisci()
    
    # Salva la sessione aggiornata
    salva_sessione(id_sessione, sessione)
    
    return jsonify({
        "success": True,
        "risultato": risultato
    })

@taverna_routes.route("/dialoga", methods=['POST'])
def dialoga_npg():
    """Gestisce il dialogo con un NPG nella taverna"""
    data = request.json
    if not data or 'id_sessione' not in data or 'npg_nome' not in data:
        return jsonify({"success": False, "error": "Dati mancanti"}), 400
    
    id_sessione = data['id_sessione']
    npg_nome = data['npg_nome']
    opzione_scelta = data.get('opzione_scelta')
    
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni lo stato taverna dalla sessione
    taverna_state = sessione.get_state("taverna")
    if not taverna_state:
        return jsonify({"success": False, "error": "Stato taverna non disponibile"}), 404
    
    # Verifica se l'NPG esiste
    if npg_nome not in taverna_state.npg_presenti:
        return jsonify({"success": False, "error": "NPG non trovato"}), 404
    
    # Accedi all'NPG e gestisci il dialogo
    npg = taverna_state.npg_presenti[npg_nome]
    
    # Se è una nuova conversazione
    if not opzione_scelta:
        taverna_state.nome_npg_attivo = npg_nome
        taverna_state.stato_conversazione = "inizio"
        dialogo = npg.avvia_dialogo()
    else:
        # Continua la conversazione con la scelta corrente
        dialogo = npg.continua_dialogo(opzione_scelta)
        taverna_state.ultimo_input = opzione_scelta
    
    # Salva la sessione aggiornata
    salva_sessione(id_sessione, sessione)
    
    return jsonify({
        "success": True,
        "dialogo": dialogo
    })

@taverna_routes.route("/menu", methods=['POST'])
def gestisci_menu():
    """Gestisce le interazioni con i menu della taverna"""
    data = request.json
    if not data or 'id_sessione' not in data or 'menu_id' not in data:
        return jsonify({"success": False, "error": "Dati mancanti"}), 400
    
    id_sessione = data['id_sessione']
    menu_id = data['menu_id']
    scelta = data.get('scelta')
    
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni lo stato taverna dalla sessione
    taverna_state = sessione.get_state("taverna")
    if not taverna_state:
        return jsonify({"success": False, "error": "Stato taverna non disponibile"}), 404
    
    # Gestisci l'interazione con il menu
    taverna_state.fase = menu_id
    
    if scelta:
        # Memorizza l'ultima scelta dell'utente
        taverna_state.ultima_scelta = scelta
        taverna_state.ultimo_input = scelta
    
    # Esegui la logica del menu appropriato
    if hasattr(taverna_state.menu_handler, f"gestisci_{menu_id}"):
        risultato = getattr(taverna_state.menu_handler, f"gestisci_{menu_id}")(sessione)
    else:
        risultato = {"error": "Menu non implementato"}
    
    # Salva la sessione aggiornata
    salva_sessione(id_sessione, sessione)
    
    return jsonify({
        "success": True,
        "risultato": risultato
    })

@taverna_routes.route("/movimento", methods=['POST'])
def gestisci_movimento():
    """Gestisce il movimento nella taverna"""
    data = request.json
    if not data or 'id_sessione' not in data or 'direzione' not in data:
        return jsonify({"success": False, "error": "Dati mancanti"}), 400
    
    id_sessione = data['id_sessione']
    direzione = data['direzione']
    
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni lo stato taverna dalla sessione
    taverna_state = sessione.get_state("taverna")
    if not taverna_state:
        return jsonify({"success": False, "error": "Stato taverna non disponibile"}), 404
    
    # Verifica se la direzione è valida
    if direzione not in taverna_state.direzioni:
        return jsonify({"success": False, "error": "Direzione non valida"}), 400
    
    # Ottieni la mappa della taverna e il giocatore
    mappa = sessione.gestore_mappe.ottieni_mappa("taverna")
    giocatore = sessione.giocatore
    
    # Calcola la nuova posizione
    x, y = giocatore.get_posizione("taverna")
    dx, dy = taverna_state.direzioni[direzione]
    nuova_x, nuova_y = x + dx, y + dy
    
    # Verifica se il movimento è valido
    if mappa.is_valid_position(nuova_x, nuova_y):
        giocatore.imposta_posizione("taverna", nuova_x, nuova_y)
        
        # Verifica se ci sono eventi nella nuova posizione
        evento = mappa.get_event_at(nuova_x, nuova_y)
        
        # Salva la sessione aggiornata
        salva_sessione(id_sessione, sessione)
        
        return jsonify({
            "success": True,
            "posizione": {"x": nuova_x, "y": nuova_y},
            "evento": evento
        })
    else:
        return jsonify({
            "success": False, 
            "error": "Movimento non valido"
        }), 400

@taverna_routes.route("/transizione", methods=['POST'])
def transizione_stato():
    """Gestisce le transizioni tra la taverna e altri stati"""
    data = request.json
    if not data or 'id_sessione' not in data or 'stato_destinazione' not in data:
        return jsonify({"success": False, "error": "Dati mancanti"}), 400
    
    id_sessione = data['id_sessione']
    stato_destinazione = data['stato_destinazione']
    parametri = data.get('parametri', {})
    
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni lo stato taverna dalla sessione
    taverna_state = sessione.get_state("taverna")
    if not taverna_state:
        return jsonify({"success": False, "error": "Stato taverna non disponibile"}), 404
    
    # Esegui la transizione verso il nuovo stato
    try:
        sessione.change_state(stato_destinazione, parametri)
        
        # Salva la sessione aggiornata
        salva_sessione(id_sessione, sessione)
        
        return jsonify({
            "success": True,
            "nuovo_stato": stato_destinazione
        })
    except Exception as e:
        logger.error(f"Errore nella transizione: {e}")
        return jsonify({
            "success": False,
            "error": f"Errore nella transizione: {str(e)}"
        }), 500 