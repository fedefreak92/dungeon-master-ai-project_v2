from flask import Blueprint, request, jsonify
from server.utils.session import get_session
import logging
import os
import json

# Configura il logger
logger = logging.getLogger(__name__)

# Crea blueprint per le route della mappa
mappa_routes = Blueprint('mappa_routes', __name__)

@mappa_routes.route("/stato", methods=['GET'])
def get_stato_mappa():
    """
    Ottiene lo stato attuale della mappa (posizione del giocatore, NPC visibili, oggetti, ecc.)
    
    GET /mappa/stato?id_sessione=<id_sessione>
    
    Returns:
        json: Stato della mappa
    """
    id_sessione = request.args.get('id_sessione')
    if not id_sessione:
        return jsonify({"successo": False, "errore": "ID sessione mancante"}), 400
        
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"successo": False, "errore": "Sessione non trovata"}), 404
    
    try:
        # Ottieni il world dalla sessione
        world = sessione
        
        # Per sicurezza, verifichiamo che il giocatore esista
        if not hasattr(world, 'giocatore') or world.giocatore is None:
            # Se non c'è un giocatore, restituisci un risultato parziale
            return jsonify({
                "successo": True,
                "stato": {
                    "mappa_id": "sconosciuta",
                    "posizione_giocatore": {"x": 0, "y": 0},
                    "entita_visibili": []
                }
            })
        
        # Ottenere l'ID della mappa corrente del giocatore
        mappa_corrente = getattr(world.giocatore, 'mappa_corrente', "sconosciuta")
        
        # Ottenere la posizione del giocatore con controlli di sicurezza
        posizione_giocatore = {
            "x": getattr(world.giocatore, 'x', 0),
            "y": getattr(world.giocatore, 'y', 0)
        }
        
        # Trova entità visibili sulla mappa
        entita_visibili = []
        
        # Controllo di sicurezza prima di chiamare get_all_entities
        if hasattr(world, 'get_all_entities') and callable(world.get_all_entities):
            for entita in world.get_all_entities():
                # Verifica che l'entità abbia un attributo mappa_corrente
                entita_mappa = getattr(entita, 'mappa_corrente', None)
                
                # Includere solo entità nella stessa mappa del giocatore
                if entita_mappa == mappa_corrente:
                    # Aggiungere informazioni minime sull'entità
                    info_entita = {
                        "id": getattr(entita, 'id', None),
                        "tipo": getattr(entita, 'tipo', 'sconosciuto'),
                        "nome": getattr(entita, 'nome', getattr(entita, 'name', 'Entità sconosciuta')),
                        "x": getattr(entita, 'x', 0),
                        "y": getattr(entita, 'y', 0),
                        "è_giocatore": getattr(entita, 'è_giocatore', False),
                        "è_nemico": getattr(entita, 'è_nemico', False),
                        "è_npc": getattr(entita, 'è_npc', False),
                        "è_oggetto": getattr(entita, 'è_oggetto', False)
                    }
                    entita_visibili.append(info_entita)
        
        # Prepara la risposta
        stato_mappa = {
            "mappa_id": mappa_corrente,
            "posizione_giocatore": posizione_giocatore,
            "entita_visibili": entita_visibili
        }
        
        return jsonify({
            "successo": True,
            "stato": stato_mappa
        })
    except Exception as e:
        logger.error(f"Errore nel recupero dello stato della mappa: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"successo": False, "errore": str(e)}), 500 

@mappa_routes.route("/dati", methods=['GET'])
def get_dati_mappa():
    """
    Ottiene i dati di una mappa specifica
    
    GET /mappa/dati?id_sessione=<id_sessione>&id_mappa=<id_mappa>
    
    Returns:
        json: Dati della mappa
    """
    id_sessione = request.args.get('id_sessione')
    id_mappa = request.args.get('id_mappa')
    
    logger.info(f"Richiesta dati mappa: id_sessione={id_sessione}, id_mappa={id_mappa}")
    
    if not id_sessione:
        logger.warning("Richiesta dati mappa senza id_sessione")
        return jsonify({"successo": False, "errore": "ID sessione mancante"}), 400
        
    if not id_mappa:
        logger.warning(f"Richiesta dati mappa senza id_mappa (sessione: {id_sessione})")
        return jsonify({"successo": False, "errore": "ID mappa mancante"}), 400
    
    # Ottieni la sessione
    sessione = get_session(id_sessione)
    if not sessione:
        logger.warning(f"Sessione non trovata: {id_sessione}")
        return jsonify({"successo": False, "errore": "Sessione non trovata"}), 404
    
    try:
        # Percorso del file della mappa
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        maps_dir = os.path.join(base_dir, "data", "mappe")
        map_file = os.path.join(maps_dir, f"{id_mappa}.json")
        
        logger.info(f"Cerco file mappa: {map_file}")
        
        # Verifica se il file esiste
        if not os.path.exists(map_file):
            logger.warning(f"File mappa non trovato: {map_file}")
            
            # Log dei file disponibili per debug
            available_maps = os.listdir(maps_dir) if os.path.exists(maps_dir) else []
            logger.info(f"Mappe disponibili in {maps_dir}: {available_maps}")
            
            return jsonify({
                "successo": False,
                "errore": f"Mappa '{id_mappa}' non trovata",
                "mappe_disponibili": available_maps
            }), 404
        
        # Carica il file JSON
        with open(map_file, 'r', encoding='utf-8') as f:
            map_data = json.load(f)
        
        logger.info(f"Dati mappa '{id_mappa}' caricati con successo")
        
        # Verifica le autorizzazioni per accedere alla mappa
        # TODO: Implementare il controllo degli accessi basato sulla progressione del gioco
        
        return jsonify({
            "successo": True,
            "mappa": map_data
        })
    except Exception as e:
        logger.error(f"Errore nel recupero dei dati della mappa {id_mappa}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"successo": False, "errore": str(e)}), 500 