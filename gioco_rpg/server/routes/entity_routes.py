from flask import Blueprint, request, jsonify
from server.utils.session import sessioni_attive, salva_sessione, get_session
import logging

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
    
    # Per compatibilità frontend, estraiamo il nome della classe come stringa
    classe_nome = ""
    classe_info = {}
    
    if hasattr(giocatore, "classe"):
        if isinstance(giocatore.classe, dict):
            classe_nome = giocatore.classe.get('id', giocatore.classe.get('nome', 'Guerriero'))
            classe_info = giocatore.classe
        elif isinstance(giocatore.classe, str):
            classe_nome = giocatore.classe.capitalize()
            classe_info = {"id": giocatore.classe, "nome": classe_nome}
        elif giocatore.classe and hasattr(giocatore.classe, "id"):
            classe_nome = giocatore.classe.id if hasattr(giocatore.classe, "id") else "Guerriero"
            classe_info = {
                "id": getattr(giocatore.classe, "id", ""),
                "nome": getattr(giocatore.classe, "nome", classe_nome),
                "descrizione": getattr(giocatore.classe, "descrizione", "")
            }
    else:
        classe_nome = "Guerriero"
        classe_info = {"id": "guerriero", "nome": "Guerriero"}
    
    # Log per debugging classe
    logger = logging.getLogger(__name__)
    logger.info(f"Classe del giocatore: {classe_nome} (tipo: {type(giocatore.classe).__name__ if hasattr(giocatore, 'classe') else 'Non impostata'})")
        
    # Assicuriamoci che i valori vitali siano corretti chiamando verifica_valori_vitali
    if hasattr(giocatore, "verifica_valori_vitali") and callable(getattr(giocatore, "verifica_valori_vitali")):
        giocatore.verifica_valori_vitali()
        
    # Verifica che i valori di hp e hp_max siano validi e corretti dopo la verifica
    hp_max = None  # Non imposta un valore predefinito, lo determineremo in base alla classe
    
    if hasattr(giocatore, "hp_max") and giocatore.hp_max is not None and giocatore.hp_max > 0:
        hp_max = giocatore.hp_max
        logger.info(f"HP_MAX dal giocatore: {hp_max}")
    else:
        # Impostiamo un valore basato sulla classe utilizzando il class_registry
        try:
            from util.class_registry import get_player_class
            classe_def = get_player_class(classe_nome.lower())
            hp_base = classe_def.get("hp_base", 10)  # Usa 10 come fallback
            # Calcola il modificatore di costituzione se possibile
            mod_costituzione = 0
            if hasattr(giocatore, "modificatore_costituzione"):
                mod_costituzione = giocatore.modificatore_costituzione
            hp_max = hp_base + mod_costituzione
            logger.info(f"HP_MAX calcolato da classe {classe_nome}: {hp_max} (hp_base: {hp_base}, mod_costituzione: {mod_costituzione})")
        except Exception as e:
            logger.warning(f"Errore nel caricamento hp_base per la classe {classe_nome}: {e}")
            # Fallback ai valori di classe predefiniti solo se necessario
            if classe_nome.lower() == "guerriero":
                hp_max = 12  # In linea con classes.json
            elif classe_nome.lower() == "mago":
                hp_max = 6  # In linea con classes.json
            elif classe_nome.lower() == "ladro":
                hp_max = 8  # In linea con classes.json
            elif classe_nome.lower() == "chierico":
                hp_max = 10  # In linea con classes.json
            else:
                hp_max = 10  # Valore predefinito di base
            logger.info(f"HP_MAX impostato da fallback per {classe_nome}: {hp_max}")
            
        # Imposta hp_max sul giocatore
        if hasattr(giocatore, "hp_max"):
            giocatore.hp_max = hp_max
            # Richiama verifica_valori_vitali per assicurarsi che tutto sia coerente
            if hasattr(giocatore, "verifica_valori_vitali") and callable(getattr(giocatore, "verifica_valori_vitali")):
                giocatore.verifica_valori_vitali()
                hp_max = giocatore.hp_max
                logger.info(f"HP_MAX dopo verifica_valori_vitali: {hp_max}")
    
    # Impostiamo hp uguale a hp_max per un giocatore nuovo o se hp è 0 o non impostato
    hp = None  # Default a None per forzare la verifica
    
    if hasattr(giocatore, "hp") and giocatore.hp is not None and giocatore.hp > 0:
        hp = giocatore.hp
        logger.info(f"HP dal giocatore: {hp}")
    else:
        # Se hp è 0 o non impostato, lo impostiamo a hp_max
        hp = hp_max
        logger.info(f"HP impostato a hp_max: {hp}")
        # Aggiorniamo anche il valore sul giocatore
        if hasattr(giocatore, "hp"):
            giocatore.hp = hp
    
    # Raccogli le informazioni sul giocatore
    info_giocatore = {
        "nome": giocatore.nome if hasattr(giocatore, "nome") else (giocatore.name if hasattr(giocatore, "name") else "Sconosciuto"),
        "livello": giocatore.livello if hasattr(giocatore, "livello") else (giocatore.level if hasattr(giocatore, "level") else 1),
        # Aggiungiamo sia classe come stringa che classe_info come oggetto per compatibilità
        "classe": classe_nome,
        "classe_info": classe_info,
        "hp": hp,
        "hp_max": hp_max,
        "currentHP": hp,  # Aggiungiamo anche i campi in formato camelCase per compatibilità
        "maxHP": hp_max,
        "mana": giocatore.mana if hasattr(giocatore, "mana") else 0,
        "mana_max": giocatore.mana_max if hasattr(giocatore, "mana_max") else 0,
        "oro": giocatore.oro if hasattr(giocatore, "oro") else (giocatore.gold if hasattr(giocatore, "gold") else 0),
        "exp": giocatore.esperienza if hasattr(giocatore, "esperienza") else (giocatore.experience if hasattr(giocatore, "experience") else 0),
        "exp_next_level": giocatore.esperienza_prossimo_livello if hasattr(giocatore, "esperienza_prossimo_livello") else 100,
        "abilita": giocatore.abilita.to_dict() if hasattr(giocatore, "abilita") and hasattr(giocatore.abilita, "to_dict") else (giocatore.abilities.to_dict() if hasattr(giocatore, "abilities") and hasattr(giocatore.abilities, "to_dict") else {}),
        "mappa_corrente": giocatore.mappa_corrente if hasattr(giocatore, "mappa_corrente") else (giocatore.current_map if hasattr(giocatore, "current_map") else None),
        "posizione": {
            "x": giocatore.x if hasattr(giocatore, "x") else 0,
            "y": giocatore.y if hasattr(giocatore, "y") else 0
        },
        "statistiche": {
            "forza": giocatore.forza_base if hasattr(giocatore, "forza_base") else 10,
            "destrezza": giocatore.destrezza_base if hasattr(giocatore, "destrezza_base") else 10,
            "costituzione": giocatore.costituzione_base if hasattr(giocatore, "costituzione_base") else 10,
            "intelligenza": giocatore.intelligenza_base if hasattr(giocatore, "intelligenza_base") else 10,
            "saggezza": giocatore.saggezza_base if hasattr(giocatore, "saggezza_base") else 10,
            "carisma": giocatore.carisma_base if hasattr(giocatore, "carisma_base") else 10
        }
    }
    
    logger.info(f"Invio dati giocatore con HP: {info_giocatore['hp']}/{info_giocatore['hp_max']}")
    
    return jsonify({"success": True, "player": info_giocatore}) 