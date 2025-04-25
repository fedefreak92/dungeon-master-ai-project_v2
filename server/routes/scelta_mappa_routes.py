from flask import Blueprint, request, jsonify
from server.utils.session import get_session, salva_sessione
import logging
from core.event_bus import EventBus
from core.events import EventType

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
    
    # Ottieni EventBus
    event_bus = EventBus.get_instance()
    
    # Emetti evento di richiesta liste mappe
    event_bus.emit(EventType.MAP_LIST_REQUEST, 
                  session_id=id_sessione,
                  player_id=sessione.giocatore.id if hasattr(sessione, 'giocatore') else None)
    
    # Ottieni la lista delle mappe dal gestore
    try:
        lista_mappe = sessione.gestore_mappe.ottieni_lista_mappe()
        
        # Aggiungi anche la mappa corrente del giocatore come informazione separata
        mappa_corrente = sessione.giocatore.mappa_corrente
        
        # Emetti evento di risposta liste mappe
        event_bus.emit(EventType.UI_UPDATE, 
                      ui_element="map_list",
                      map_list=lista_mappe,
                      current_map=mappa_corrente,
                      player_id=sessione.giocatore.id)
        
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
    try:
        data = request.json
        logger.info(f"Richiesta cambio mappa ricevuta: {data}")
        
        if not data or 'id_sessione' not in data or 'id_mappa' not in data:
            logger.warning("Richiesta cambio mappa incompleta: dati mancanti")
            return jsonify({"success": False, "error": "Dati mancanti"}), 400
        
        id_sessione = data['id_sessione']
        id_mappa = data['id_mappa']
        
        logger.info(f"Tentativo cambio mappa: sessione={id_sessione}, mappa={id_mappa}")
        
        # Ottieni la sessione con gestione errori migliorata
        sessione = get_session(id_sessione)
        if not sessione:
            logger.error(f"Cambio mappa fallito: sessione {id_sessione} non trovata")
            return jsonify({"success": False, "error": "Sessione non trovata"}), 404
        
        # Ottieni EventBus
        event_bus = EventBus.get_instance()
        
        # Verifica che il gestore_mappe esista
        if not hasattr(sessione, 'gestore_mappe'):
            logger.error(f"Cambio mappa fallito: gestore_mappe non presente nella sessione {id_sessione}")
            return jsonify({"success": False, "error": "Gestore mappe non disponibile"}), 500
        
        # Ottieni la mappa e verifica i requisiti
        try:
            lista_mappe = sessione.gestore_mappe.ottieni_lista_mappe()
            logger.info(f"Liste mappe disponibili: {lista_mappe.keys()}")
        except Exception as e:
            logger.error(f"Errore nell'ottenere la lista delle mappe: {e}")
            return jsonify({"success": False, "error": f"Errore nel recupero delle mappe: {str(e)}"}), 500
        
        if id_mappa not in lista_mappe:
            logger.warning(f"Mappa {id_mappa} non disponibile tra le mappe: {list(lista_mappe.keys())}")
            return jsonify({"success": False, "error": f"Mappa '{id_mappa}' non disponibile"}), 404
        
        # Verifica il livello minimo richiesto
        info_mappa = lista_mappe[id_mappa]
        livello_min = info_mappa.get("livello_min", 0)
        
        # Verifica che il giocatore esista
        if not hasattr(sessione, 'giocatore'):
            logger.error(f"Cambio mappa fallito: giocatore non presente nella sessione {id_sessione}")
            return jsonify({"success": False, "error": "Giocatore non disponibile"}), 500
        
        # Verifica che il giocatore abbia l'attributo livello
        if not hasattr(sessione.giocatore, 'livello'):
            logger.error(f"Cambio mappa fallito: attributo livello mancante nel giocatore")
            return jsonify({"success": False, "error": "Attributo livello mancante nel giocatore"}), 500
            
        if sessione.giocatore.livello < livello_min:
            # Emetti evento di requisiti non soddisfatti
            event_bus.emit(EventType.MAP_CHANGE_DENIED, 
                          player_id=sessione.giocatore.id,
                          map_id=id_mappa,
                          reason="low_level",
                          required_level=livello_min,
                          current_level=sessione.giocatore.livello)
            
            logger.warning(f"Livello insufficiente: richiesto={livello_min}, attuale={sessione.giocatore.livello}")
            return jsonify({
                "success": False, 
                "error": f"Livello insufficiente! Devi essere almeno di livello {livello_min}."
            }), 403
        
        # Ottieni la mappa e le coordinate iniziali con gestione errori migliorata
        try:
            mappa = sessione.gestore_mappe.ottieni_mappa(id_mappa)
            if not mappa:
                logger.error(f"Mappa {id_mappa} non può essere caricata")
                return jsonify({"success": False, "error": "Impossibile caricare la mappa"}), 500
                
            # Verifica che la mappa abbia le coordinate iniziali
            if not hasattr(mappa, 'pos_iniziale_giocatore'):
                logger.error(f"Mappa {id_mappa} non ha posizione iniziale definita")
                # Impostiamo una posizione predefinita
                x, y = 0, 0
                logger.info(f"Utilizzo posizione predefinita: ({x}, {y})")
            else:
                x, y = mappa.pos_iniziale_giocatore
                logger.info(f"Posizione iniziale della mappa: ({x}, {y})")
        except Exception as e:
            logger.error(f"Errore nel caricamento della mappa {id_mappa}: {e}")
            return jsonify({"success": False, "error": f"Errore nel caricamento della mappa: {str(e)}"}), 500
        
        # Emetti evento di richiesta cambio mappa
        event_bus.emit(EventType.MAP_CHANGE_REQUEST, 
                      session_id=id_sessione,
                      player_id=sessione.giocatore.id,
                      from_map=sessione.giocatore.mappa_corrente,
                      to_map=id_mappa,
                      position=(x, y))
        
        # Cambia la mappa corrente
        try:
            # Verifica che il metodo cambia_mappa esista
            if not hasattr(sessione, 'cambia_mappa'):
                logger.error(f"Metodo cambia_mappa non presente nella sessione {id_sessione}")
                return jsonify({"success": False, "error": "Funzionalità cambio mappa non disponibile"}), 500
                
            logger.info(f"Esecuzione cambio mappa: {id_mappa}, posizione: ({x}, {y})")
            success = sessione.cambia_mappa(id_mappa, x, y)
            
            if success:
                # Emetti evento di cambio mappa completato
                event_bus.emit(EventType.MAP_CHANGED, 
                              session_id=id_sessione,
                              player_id=sessione.giocatore.id,
                              map_id=id_mappa,
                              position=(x, y))
                
                # Salva la sessione aggiornata
                salva_sessione(id_sessione, sessione)
                logger.info(f"Cambio mappa completato con successo: {id_mappa}")
                
                return jsonify({
                    "success": True,
                    "mappa": id_mappa,
                    "posizione": {"x": x, "y": y}
                })
            else:
                # Emetti evento di cambio mappa fallito
                event_bus.emit(EventType.MAP_CHANGE_FAILED, 
                              session_id=id_sessione,
                              player_id=sessione.giocatore.id,
                              map_id=id_mappa,
                              reason="game_logic")
                
                logger.error(f"Cambio mappa fallito: metodo cambia_mappa ha restituito False")
                return jsonify({
                    "success": False, 
                    "error": "Impossibile viaggiare verso questa destinazione."
                }), 500
        except Exception as e:
            logger.error(f"Errore nell'esecuzione del cambio mappa: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({"success": False, "error": f"Errore nel cambio mappa: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Errore generale nel cambio mappa: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": f"Errore interno: {str(e)}"}), 500

@scelta_mappa_routes.route("/stato", methods=['GET'])
def get_stato_scelta_mappa():
    """Ottiene lo stato corrente di SceltaMappaState"""
    id_sessione = request.args.get('id_sessione')
    if not id_sessione:
        return jsonify({"success": False, "error": "ID sessione mancante"}), 400
        
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni EventBus
    event_bus = EventBus.get_instance()
    
    # Ottieni lo stato scelta_mappa dalla sessione
    scelta_mappa_state = sessione.get_state("scelta_mappa")
    if not scelta_mappa_state:
        return jsonify({"success": False, "error": "Stato scelta_mappa non disponibile"}), 404
    
    # Emetti evento di richiesta stato
    event_bus.emit(EventType.STATE_INFO_REQUEST, 
                  session_id=id_sessione,
                  player_id=sessione.giocatore.id if hasattr(sessione, 'giocatore') else None,
                  state_type="scelta_mappa")
    
    # Restituisci lo stato
    return jsonify({
        "success": True, 
        "stato": scelta_mappa_state.to_dict()
    }) 