from flask import request, jsonify, Blueprint
from uuid import uuid4
import time
import logging

from core.ecs.world import World
from core.ecs.component import PositionComponent, RenderableComponent, PhysicsComponent, InventoryComponent, InteractableComponent
from server.utils.session import sessioni_attive, salva_sessione, get_session
from server.init.taverna_init import inizializza_taverna_per_sessione
from util.data_manager import get_data_manager

# Configura il logger
logger = logging.getLogger(__name__)

# Crea il blueprint per le route di sessione
session_routes = Blueprint('session_routes', __name__)

@session_routes.route("/inizia", methods=["POST"])
def inizia_sessione():
    """Inizia una nuova sessione di gioco"""
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
    
    try:
        # Crea una nuova sessione (world)
        id_sessione = str(uuid4())
        world = World()
        
        # Ottieni la classe dal database
        dm = get_data_manager()
        classe = dm.get_classe(classe_id)
        if not classe:
            return jsonify({"success": False, "error": "Classe non trovata"}), 404
            
        # Crea il giocatore
        from entities.giocatore import Giocatore
        giocatore = Giocatore(nome_giocatore, classe=classe)
        
        # Assicurati che il giocatore abbia il tag 'player'
        if not hasattr(giocatore, 'tags'):
            giocatore.tags = set(['player'])
        elif 'player' not in giocatore.tags:
            giocatore.tags.add('player')
        
        # Aggiungi anche il tag della classe
        classe_tag = classe.get('id', '').lower() if isinstance(classe, dict) else classe.id.lower() if hasattr(classe, 'id') else 'classe_generica'
        giocatore.tags.add(classe_tag)
        
        # Aggiungi il giocatore al world
        world.add_entity(giocatore)
        
        # Log per verificare la corretta creazione
        logger.info(f"Creato giocatore '{nome_giocatore}' con id: {giocatore.id}, tag: {giocatore.tags}")
        
        # Verifica che il giocatore sia stato aggiunto correttamente
        player_entities = world.find_entities_by_tag("player")
        logger.info(f"Entità con tag 'player' dopo la creazione: {len(player_entities)}")
        
        if len(player_entities) == 0:
            logger.warning("Giocatore non trovato tramite tag 'player', verifica i tags")
            # Aggiunta manuale al dizionario
            world.entities_by_tag["player"].add(giocatore)
            logger.info(f"Aggiunto manualmente il giocatore al dizionario entities_by_tag")
        
        # Imposta la mappa iniziale
        world.gestore_mappe.inizializza_mappe()
        world.gestore_mappe.cambia_mappa_giocatore(giocatore, "taverna")
        
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
def create_session():
    """Crea una nuova sessione di gioco (endpoint alternativo)"""
    # Ottieni i dati dalla richiesta con gestione sicura del content-type
    try:
        data = request.get_json(force=True, silent=True) or {}
    except Exception as e:
        logger.warning(f"Errore nell'elaborazione del JSON: {e}")
        data = {}
    
    nome_personaggio = data.get("nome_personaggio", "Player")
    classe = data.get("classe", "guerriero")
    
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
    
    return jsonify({
        'success': True,
        'message': 'Sessione creata con successo',
        'session_id': id_sessione
    })

# ... existing code ... 