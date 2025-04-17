from flask import Blueprint, request, jsonify
from server.utils.session import sessioni_attive, salva_sessione, get_session

# Crea il Blueprint per le route delle entità
entity_routes = Blueprint('entity_routes', __name__)

@entity_routes.route("/add_ability", methods=["POST"])
def add_ability():
    """
    Aggiunge un'abilità a un'entità specificata
    
    POST /game/entity/add_ability
    {
        "id_sessione": "id della sessione",
        "entity_id": "id dell'entità",
        "ability_name": "nome dell'abilità",
        "ability_value": valore numerico dell'abilità (opzionale, default=1)
    }
    
    Returns:
        json: Risultato dell'operazione
    """
    # Ottieni i dati dalla richiesta
    data = request.json
    if not data:
        return jsonify({"successo": False, "errore": "Dati mancanti"}), 400
        
    id_sessione = data.get("id_sessione")
    entity_id = data.get("entity_id")
    ability_name = data.get("ability_name")
    ability_value = data.get("ability_value", 1)
    
    # Verifica parametri obbligatori
    if not all([id_sessione, entity_id, ability_name]):
        return jsonify({
            "successo": False, 
            "errore": "Parametri obbligatori mancanti (id_sessione, entity_id, ability_name)"
        }), 400
    
    # Carica la sessione
    sessione = sessioni_attive.get(id_sessione)
    if not sessione:
        return jsonify({"successo": False, "errore": "Sessione non trovata"}), 404
    
    # Recupera l'entità dal mondo di gioco
    # La sessione stessa è il world
    world = sessione
    if not world:
        return jsonify({"successo": False, "errore": "Mondo di gioco non trovato nella sessione"}), 404
    
    entity = world.get_entity(entity_id)
    if not entity:
        return jsonify({"successo": False, "errore": f"Entità {entity_id} non trovata"}), 404
    
    # Aggiungi l'abilità all'entità
    # Prima controlla se l'entità ha già un attributo per le abilità speciali
    if not hasattr(entity, "abilita_speciali"):
        entity.abilita_speciali = {}
    
    # Aggiungi l'abilità al dizionario
    entity.abilita_speciali[ability_name] = ability_value
    
    # Salva la sessione
    salva_sessione(id_sessione, sessione)
    
    return jsonify({
        "successo": True,
        "messaggio": f"Abilità {ability_name} aggiunta con successo all'entità {entity.nome if hasattr(entity, 'nome') else entity_id}"
    })

@entity_routes.route("/player", methods=["GET"])
def get_player():
    """
    Ottiene le informazioni del giocatore
    
    GET /game/entity/player?id_sessione=ID_SESSIONE
    
    Returns:
        json: Informazioni sul giocatore
    """
    id_sessione = request.args.get("id_sessione")
    
    if not id_sessione:
        return jsonify({"success": False, "error": "ID sessione mancante"}), 400
    
    # Carica la sessione
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni il giocatore dalla sessione
    giocatore = sessione.giocatore
    if not giocatore:
        return jsonify({"success": False, "error": "Giocatore non trovato nella sessione"}), 404
    
    # Raccogli le informazioni sul giocatore
    info_giocatore = {
        "nome": giocatore.nome,
        "livello": giocatore.livello,
        "classe": {
            "id": giocatore.classe.get('id') if hasattr(giocatore, "classe") and isinstance(giocatore.classe, dict) else (giocatore.classe.id if hasattr(giocatore, "classe") and giocatore.classe and hasattr(giocatore.classe, "id") else None),
            "nome": giocatore.classe.get('nome') if hasattr(giocatore, "classe") and isinstance(giocatore.classe, dict) else (giocatore.classe.nome if hasattr(giocatore, "classe") and giocatore.classe and hasattr(giocatore.classe, "nome") else None),
            "descrizione": giocatore.classe.get('descrizione') if hasattr(giocatore, "classe") and isinstance(giocatore.classe, dict) else (giocatore.classe.descrizione if hasattr(giocatore, "classe") and giocatore.classe and hasattr(giocatore.classe, "descrizione") else None)
        },
        "hp": giocatore.hp,
        "hp_max": giocatore.hp_max,
        "mana": giocatore.mana if hasattr(giocatore, "mana") else 0,
        "mana_max": giocatore.mana_max if hasattr(giocatore, "mana_max") else 0,
        "oro": giocatore.oro,
        "exp": giocatore.esperienza if hasattr(giocatore, "esperienza") else 0,
        "exp_next_level": giocatore.exp_next_level if hasattr(giocatore, "exp_next_level") else 100,
        "abilita": giocatore.abilita.to_dict() if hasattr(giocatore, "abilita") else {},
        "mappa_corrente": giocatore.mappa_corrente,
        "posizione": {
            "x": giocatore.x,
            "y": giocatore.y
        }
    }
    
    return jsonify({"success": True, "player": info_giocatore}) 