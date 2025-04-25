from flask import request, jsonify, Blueprint, Response
from uuid import uuid4
import time
import logging
import os
from pathlib import Path

from core.ecs.world import World
from core.ecs.component import PositionComponent, RenderableComponent, PhysicsComponent, InventoryComponent, InteractableComponent
from server.utils.session import sessioni_attive, salva_sessione, get_session
from server.init.taverna_init import inizializza_taverna_per_sessione
from util.data_manager import get_data_manager
from core.event_bus import EventBus
from core.events import EventType

# Aggiungi il supporto per MessagePack
from server.utils.message_pack_middleware import supports_msgpack, accept_msgpack
import msgpack

# Configura il logger
logger = logging.getLogger(__name__)

# Crea il blueprint per le route di sessione
session_routes = Blueprint('session_routes', __name__)

@session_routes.route("/inizia", methods=["POST"])
@accept_msgpack  # Aggiungi supporto per ricevere dati MessagePack
@supports_msgpack  # Aggiungi supporto per rispondere con MessagePack
def inizia_sessione():
    """Inizia una nuova sessione di gioco"""
    # Gestisci sia richieste JSON che MessagePack
    if hasattr(request, 'msgpack_data'):
        data = request.msgpack_data
    else:
        data = request.json
    
    # Validazione dei dati
    if not data:
        return jsonify({"success": False, "error": "Dati mancanti"}), 400
        
    # Gestione compatibilità tra nome_giocatore e nome_personaggio
    nome_giocatore = data.get("nome_giocatore")
    if not nome_giocatore:
        nome_giocatore = data.get("nome_personaggio")
    
    if not nome_giocatore:
        return jsonify({"success": False, "error": "Nome giocatore mancante"}), 400
        
    # Gestione compatibilità tra classe_id e classe
    classe_id = data.get("classe_id")
    if not classe_id:
        classe_id = data.get("classe")
    
    if not classe_id:
        return jsonify({"success": False, "error": "ID classe mancante"}), 400
    
    # Controlla se è richiesta la verifica forzata delle mappe
    force_check_mappe = data.get("force_check_mappe", False)
    if force_check_mappe:
        logger.info("Verifica forzata delle mappe richiesta")
        # Verifica la presenza dei file delle mappe
        base_dir = Path(os.getcwd())
        possible_paths = [
            base_dir / "gioco_rpg" / "data" / "mappe",
            base_dir / "data" / "mappe",
            Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "data" / "mappe"
        ]
        
        found_maps = False
        for path in possible_paths:
            if path.exists():
                map_files = list(path.glob("*.json"))
                logger.info(f"Trovate {len(map_files)} mappe in {path}")
                if map_files:
                    found_maps = True
                    for map_file in map_files:
                        logger.info(f"  - {map_file.name}")
                    break
        
        if not found_maps:
            logger.error("ERRORE: Nessuna mappa trovata nei percorsi controllati!")
            return jsonify({
                "success": False, 
                "error": "Nessuna mappa trovata. Verifica che i file JSON delle mappe esistano."
            }), 500
    
    try:
        # Ottieni EventBus
        event_bus = EventBus.get_instance()
        
        # Ottieni le informazioni sulla classe
        data_manager = get_data_manager()
        
        # Log di debug per verificare l'accesso alle classi
        logger.info(f"Ricevuta richiesta per classe_id: {classe_id}")
        classi_disponibili = data_manager.get_classes()
        logger.info(f"Classi disponibili: {list(classi_disponibili.keys()) if isinstance(classi_disponibili, dict) else 'Non è un dizionario'}")
        
        classe = data_manager.get_classe(classe_id)
        logger.info(f"Informazioni classe ottenute: {classe != None}")
        
        if not classe:
            return jsonify({"success": False, "error": f"Classe non valida: {classe_id}"}), 400
            
        # Emetti evento di inizio creazione sessione
        event_bus.emit(EventType.SESSION_CREATE_START, 
                      player_name=nome_giocatore,
                      class_id=classe_id)
            
        # Crea un nuova sessione con un ID unico
        id_sessione = str(uuid4())
        logger.info(f"Inizializzazione nuova sessione {id_sessione}")
        
        # Crea il mondo di gioco
        world = World()
        
        # Inizializza la grafica se richiesto
        modalita_grafica = data.get("modalita_grafica", True)
        world.modalita_grafica = modalita_grafica
        
        # Crea il giocatore e aggiungilo al mondo
        from entities.giocatore import Giocatore
        giocatore = Giocatore(nome_giocatore, classe)
        world.giocatore = giocatore
        
        # Imposta la classe del giocatore
        giocatore.imposta_classe(classe)
        
        # Inizializza l'interfaccia IO subito dopo la creazione di world
        from core.io_interface import IOInterface
        world.io = IOInterface(world)
        logger.info(f"IO Interface inizializzata per sessione {id_sessione}")
        
        # Inizializza i manager dei sistemi di gioco
        world.inizializza_sistemi()
        
        # Inizializza le mappe di gioco con gestione degli errori migliorata
        logger.info("Inizializzazione delle mappe di gioco...")
        try:
            from world.gestore_mappe import GestitoreMappe
            gestore_mappe = GestitoreMappe()
            world.gestore_mappe = gestore_mappe
            gestore_mappe.inizializza_mappe()
            logger.info("Mappe inizializzate con successo")
            
            # Verifica che le mappe siano state caricate
            mappe_disponibili = list(gestore_mappe.mappe.keys())
            logger.info(f"Mappe disponibili: {mappe_disponibili}")
            if not mappe_disponibili:
                raise ValueError("Nessuna mappa caricata. Controlla i file delle mappe.")
        except Exception as map_error:
            logger.error(f"Errore nell'inizializzazione delle mappe: {str(map_error)}")
            return jsonify({
                "success": False, 
                "error": f"Errore nell'inizializzazione delle mappe: {str(map_error)}"
            }), 500
        
        # Emetti evento di creazione giocatore
        event_bus.emit(EventType.PLAYER_CREATED, 
                      session_id=id_sessione,
                      player_id=giocatore.id,
                      player_name=nome_giocatore,
                      class_id=classe_id)
        
        # Salva la sessione
        if salva_sessione(id_sessione, world):
            logger.info(f"Nuova sessione {id_sessione} salvata con successo")
        else:
            logger.error(f"Errore nel salvataggio della sessione {id_sessione}")
            return jsonify({"success": False, "error": "Errore nel salvataggio della sessione"}), 500
            
        # Aggiungi la sessione al dizionario delle sessioni attive
        sessioni_attive[id_sessione] = world
        
        # Inizializza la taverna
        from server.init import taverna_init
        taverna_init.inizializza_taverna(id_sessione)
        
        # Inizializza lo stato di scelta mappa
        from states.scelta_mappa_state import SceltaMappaState
        scelta_mappa_state = SceltaMappaState(gioco=world)
        world.add_state("scelta_mappa", scelta_mappa_state)
        logger.info(f"Stato scelta_mappa aggiunto alla sessione {id_sessione}")
        
        # Emetti evento di sessione creata
        event_bus.emit(EventType.SESSION_CREATED, 
                      session_id=id_sessione,
                      player_id=giocatore.id,
                      player_name=nome_giocatore,
                      class_id=classe_id)
        
        # Controlla se la classe è un dizionario e gestisci di conseguenza l'accesso a id
        classe_id = classe.get('id') if isinstance(classe, dict) else classe.id
        classe_nome = classe.get('nome') if isinstance(classe, dict) else classe.nome
        classe_descrizione = classe.get('descrizione') if isinstance(classe, dict) else classe.descrizione
        
        return jsonify({
            "success": True,
            "message": "Sessione avviata con successo",
            "session_id": id_sessione,
            "player_name": nome_giocatore,
            "player_class": {
                "id": classe_id,
                "nome": classe_nome,
                "descrizione": classe_descrizione
            }
        })
    except Exception as e:
        import traceback
        logger.error(f"Errore nell'avvio della sessione: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": f"Errore interno: {str(e)}"}), 500

@session_routes.route('/create', methods=['POST'])
@accept_msgpack  # Aggiungi supporto per ricevere dati MessagePack
@supports_msgpack  # Aggiungi supporto per rispondere con MessagePack
def create_session():
    """Crea una nuova sessione di gioco (endpoint alternativo)"""
    # Gestisci sia richieste JSON che MessagePack
    if hasattr(request, 'msgpack_data'):
        data = request.msgpack_data
        logger.info("Ricevuti dati MessagePack per create_session")
    else:
        # Ottieni i dati dalla richiesta con gestione sicura del content-type
        try:
            data = request.get_json(force=True, silent=True) or {}
        except Exception as e:
            logger.warning(f"Errore nell'elaborazione del JSON: {e}")
            data = {}
    
    nome_personaggio = data.get("nome_personaggio", "Player")
    classe = data.get("classe", "guerriero")
    
    # Ottieni EventBus
    event_bus = EventBus.get_instance()
    
    # Emetti evento di inizio creazione sessione
    event_bus.emit(EventType.SESSION_CREATE_START, 
                  player_name=nome_personaggio,
                  class_id=classe)
    
    # Utilizziamo la stessa logica di inizia_sessione
    id_sessione = str(uuid4())
    
    # Crea un nuovo mondo ECS
    world = World()
    
    # Registra i tipi di componenti
    world.register_component_type("position", PositionComponent)
    world.register_component_type("renderable", RenderableComponent)
    world.register_component_type("physics", PhysicsComponent)
    world.register_component_type("inventory", InventoryComponent)
    world.register_component_type("interactable", InteractableComponent)
    
    # Crea l'entità giocatore con il nome fornito
    player = world.create_entity(name=nome_personaggio)
    player.add_tag("player")
    
    # Aggiungi componenti base al giocatore
    position = PositionComponent(x=0, y=0, map_name="start")
    player.add_component("position", position)
    
    renderable = RenderableComponent(sprite="player", layer=10)
    player.add_component("renderable", renderable)
    
    physics = PhysicsComponent(solid=True, movable=True)
    player.add_component("physics", physics)
    
    inventory = InventoryComponent(capacity=20)
    player.add_component("inventory", inventory)
    
    # Se vogliamo gestire la classe del personaggio
    if hasattr(player, "add_tag"):
        player.add_tag(classe)  # Aggiungiamo la classe come tag
    
    # Aggiungiamo attributi base per combattimento
    if not hasattr(player, "hp"):
        setattr(player, "hp", 20)
    if not hasattr(player, "hp_max"):
        setattr(player, "hp_max", 20)
    
    # Emetti evento di creazione giocatore
    event_bus.emit(EventType.PLAYER_CREATED, 
                  session_id=id_sessione,
                  player_id=player.id,
                  player_name=nome_personaggio,
                  class_id=classe)
    
    # Stampa di debug per verificare che il giocatore sia stato creato correttamente
    logger.info(f"Creato giocatore '{nome_personaggio}' con id: {player.id}, tag: {player.tags}")
    
    # Memorizza la sessione
    sessioni_attive[id_sessione] = world
    
    # Salva la sessione
    salva_sessione(id_sessione, world)
    
    # Inizializza lo stato taverna
    inizializza_taverna_per_sessione(id_sessione)
    
    # Inizializza lo stato di scelta mappa
    from states.scelta_mappa_state import SceltaMappaState
    scelta_mappa_state = SceltaMappaState(gioco=world)
    world.add_state("scelta_mappa", scelta_mappa_state)
    logger.info(f"Stato scelta_mappa aggiunto alla sessione {id_sessione}")
    
    # Emetti evento di sessione creata
    event_bus.emit(EventType.SESSION_CREATED, 
                  session_id=id_sessione,
                  player_id=player.id,
                  player_name=nome_personaggio,
                  class_id=classe)
    
    return jsonify({
        'success': True,
        'message': 'Sessione creata con successo',
        'session_id': id_sessione
    })

@session_routes.route('/get/<id_sessione>', methods=['GET'])
@supports_msgpack
def get_session_data(id_sessione):
    """
    Ottiene i dati di una sessione esistente, supportando sia JSON che MessagePack
    in base all'header Accept del client.
    """
    # Controlla se la sessione esiste
    world = get_session(id_sessione)
    if not world:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Determina il formato preferito
    accept_header = request.headers.get('Accept', '')
    use_msgpack = 'application/msgpack' in accept_header
    
    # Crea la risposta
    try:
        # Ottieni i dati serializzati
        if use_msgpack:
            # Usa direttamente il metodo serialize_msgpack del mondo
            data_bytes = world.serialize_msgpack()
            logger.info(f"Inviando dati sessione {id_sessione} in formato MessagePack, dimensione: {len(data_bytes)} bytes")
            return Response(data_bytes, mimetype='application/msgpack')
        else:
            # Usa la serializzazione JSON standard
            data = world.serialize()
            return jsonify({
                "success": True,
                "session_id": id_sessione,
                "data": data
            })
    except Exception as e:
        logger.error(f"Errore nel recupero della sessione {id_sessione}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": f"Errore nel recupero della sessione: {str(e)}"
        }), 500

@session_routes.route('/state/<id_sessione>', methods=['GET'])
@supports_msgpack
def get_session_state(id_sessione):
    """
    Ottiene lo stato corrente di una sessione di gioco, supportando sia JSON che MessagePack.
    Fornisce una risposta più compatta rispetto all'endpoint get_session_data.
    """
    # Controlla se la sessione esiste
    world = get_session(id_sessione)
    if not world:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    try:
        # Ottieni informazioni di base sulla sessione
        state_data = {
            "success": True,
            "session_id": id_sessione,
            "active": True,
            "current_state": None,
            "player": {}
        }
        
        # Ottieni lo stato corrente se presente
        if hasattr(world, "state_stack") and world.state_stack:
            current_state = world.state_stack[-1]
            state_data["current_state"] = {
                "name": current_state.__class__.__name__,
                "type": getattr(current_state, "type", "unknown")
            }
        
        # Ottieni informazioni sul giocatore
        player_entities = world.find_entities_by_tag("player") if hasattr(world, "find_entities_by_tag") else []
        if player_entities:
            player = player_entities[0]
            state_data["player"] = {
                "id": player.id,
                "name": player.name,
                "hp": getattr(player, "hp", 0),
                "hp_max": getattr(player, "hp_max", 0),
                "position": {}
            }
            
            # Ottieni la posizione del giocatore
            if hasattr(player, "get_component") and player.get_component("position"):
                position = player.get_component("position")
                state_data["player"]["position"] = {
                    "x": position.x,
                    "y": position.y,
                    "map": position.map_name
                }
        
        # Determina il formato preferito
        accept_header = request.headers.get('Accept', '')
        use_msgpack = 'application/msgpack' in accept_header
        
        if use_msgpack:
            # Serializza in MessagePack
            data_bytes = msgpack.packb(state_data, use_bin_type=True)
            logger.info(f"Inviando stato sessione {id_sessione} in formato MessagePack, dimensione: {len(data_bytes)} bytes")
            return Response(data_bytes, mimetype='application/msgpack')
        else:
            # Serializza in JSON
            return jsonify(state_data)
            
    except Exception as e:
        logger.error(f"Errore nel recupero dello stato della sessione {id_sessione}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": f"Errore nel recupero dello stato: {str(e)}"
        }), 500

# ... existing code ... 