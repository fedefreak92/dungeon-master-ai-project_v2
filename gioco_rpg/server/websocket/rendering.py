import logging
import time
from flask_socketio import emit
from flask import request

# Import moduli locali
from . import core, graphics_renderer

# Configura il logger
logger = logging.getLogger(__name__)

def handle_request_map_data(data):
    """
    Gestisce una richiesta di dati mappa dettagliati
    
    Args:
        data (dict): Contiene id_sessione ed eventualmente parametri per filtrare
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione']):
        return
        
    id_sessione = data['id_sessione']
    
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        return
    
    # Ottieni i dati della mappa dal mondo ECS
    try:
        player_entity = sessione.get_player_entity()
        if not player_entity:
            emit('error', {'message': 'Entità giocatore non trovata'})
            return
            
        # Ottieni il componente posizione del giocatore
        position_component = player_entity.get_component("position")
        if not position_component:
            emit('error', {'message': 'Componente posizione non trovato'})
            return
            
        # Ottieni la mappa corrente
        map_name = position_component.map_name
        map_entities = sessione.get_entities_in_map(map_name)
        
        # Costruisci i dati della mappa
        map_data = {
            'name': map_name,
            'player_position': {
                'x': position_component.x,
                'y': position_component.y
            },
            'entities': []
        }
        
        # Aggiungi tutte le entità presenti sulla mappa
        for entity in map_entities:
            entity_pos = entity.get_component("position")
            entity_render = entity.get_component("renderable")
            
            if entity_pos and entity_render:
                map_data['entities'].append({
                    'id': entity.id,
                    'name': entity.name,
                    'x': entity_pos.x,
                    'y': entity_pos.y,
                    'sprite': entity_render.sprite,
                    'layer': entity_render.layer,
                    'tags': entity.tags
                })
        
        emit('map_data', map_data)
    except Exception as e:
        logger.error(f"Errore nell'ottenere i dati mappa: {e}")
        emit('error', {'message': f'Errore nel caricamento mappa: {str(e)}'})

def handle_request_assets(data):
    """
    Gestisce una richiesta di asset grafici
    
    Args:
        data (dict): Contiene tipo_asset e parametri di filtro
    """
    tipo_asset = data.get('tipo_asset', 'all')
    
    from util.asset_manager import get_asset_manager
    asset_manager = get_asset_manager()
    
    if tipo_asset == 'sprites':
        assets = asset_manager.get_all_sprites()
    elif tipo_asset == 'tiles':
        assets = asset_manager.get_all_tiles()
    elif tipo_asset == 'animations':
        assets = asset_manager.get_all_animations()
    elif tipo_asset == 'tilesets':
        assets = asset_manager.get_all_tilesets()
    elif tipo_asset == 'ui':
        assets = asset_manager.get_all_ui_elements()
    else:
        # Restituisci tutti gli asset raggruppati per tipo
        assets = {
            'sprites': asset_manager.get_all_sprites(),
            'tiles': asset_manager.get_all_tiles(),
            'animations': asset_manager.get_all_animations(),
            'tilesets': asset_manager.get_all_tilesets(),
            'ui': asset_manager.get_all_ui_elements()
        }
    
    emit('assets_data', assets)

def handle_request_render_update(data):
    """
    Gestisce una richiesta di aggiornamento rendering dal client
    
    Args:
        data (dict): Dati della richiesta con id_sessione
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione']):
        return
        
    id_sessione = data['id_sessione']
    
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        return
    
    # Raccogli tutti gli eventi di rendering dal sistema ECS
    render_events = []
    
    # 1. Raccogli eventi dal RenderSystem
    render_system = sessione.get_system("render")
    if render_system:
        render_events.extend(render_system.get_render_events())
    
    # 2. Raccogli eventi dal GraphicsRenderer
    renderer_events = graphics_renderer.get_renderer_events()
    if renderer_events:
        render_events.extend(renderer_events)
        
    # 3. Raccogli eventi dalle entità con componenti di rendering
    for entity in sessione.get_entities_with_component("renderable"):
        if hasattr(entity, "get_render_events"):
            entity_events = entity.get_render_events()
            if entity_events:
                render_events.extend(entity_events)
    
    # 4. Sistema di particelle
    for entity in sessione.get_entities_with_component("particle"):
        if hasattr(entity, "get_render_events"):
            particle_events = entity.get_render_events()
            if particle_events:
                render_events.extend(particle_events)
    
    # Invia aggiornamenti al client
    if render_events:
        emit('render_update', {
            "events": render_events,
            "timestamp": time.time()
        })
    else:
        # Se non ci sono aggiornamenti, invia comunque una conferma
        emit('render_no_updates', {
            "timestamp": time.time()
        })

def handle_process_render_queue(data):
    """
    Elabora la coda di rendering e invia gli eventi al client
    
    Args:
        data (dict): Dati della richiesta con id_sessione e altre opzioni
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione']):
        return
        
    id_sessione = data['id_sessione']
    
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        return
    
    # Configura camera se fornita
    if "camera" in data:
        graphics_renderer.set_camera(data["camera"])
    
    # Esegui il rendering della scena
    graphics_renderer.clear_screen()
    
    # Ottieni tutte le entità con componente renderable
    entities = sessione.get_entities_with_component("renderable")
    
    # Renderizza prima la mappa se esiste
    map_entities = [e for e in entities if e.has_tag("map")]
    for entity in map_entities:
        render_comp = entity.get_component("renderable")
        if render_comp and hasattr(render_comp, "to_render_data"):
            tilemap_data = render_comp.to_render_data()
            graphics_renderer.render_tilemap(tilemap_data)
    
    # Renderizza le entità normali
    normal_entities = [e for e in entities if not e.has_tag("map") and not e.has_tag("ui")]
    
    # Ordina per layer (z-index)
    normal_entities.sort(key=lambda e: e.get_component("renderable").layer)
    
    for entity in normal_entities:
        render_comp = entity.get_component("renderable")
        if render_comp and hasattr(render_comp, "to_render_data"):
            entity_data = render_comp.to_render_data()
            graphics_renderer.draw_entity(entity_data)
    
    # Renderizza i sistemi di particelle
    particle_entities = sessione.get_entities_with_component("particle")
    for entity in particle_entities:
        particle_comp = entity.get_component("particle")
        if particle_comp and hasattr(particle_comp, "to_render_data"):
            particle_data = particle_comp.to_render_data()
            graphics_renderer.draw_particle_system(particle_data)
    
    # Renderizza infine elementi UI
    ui_entities = [e for e in entities if e.has_tag("ui")]
    for entity in ui_entities:
        render_comp = entity.get_component("renderable")
        if render_comp and hasattr(render_comp, "to_render_data"):
            ui_data = render_comp.to_render_data()
            graphics_renderer.draw_ui_element(ui_data)
    
    # Finalizza il rendering
    graphics_renderer.present()

def handle_set_camera(data):
    """
    Imposta i parametri della camera per il rendering
    
    Args:
        data (dict): Parametri della camera (x, y, zoom, viewport_width, viewport_height)
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione']):
        return
        
    id_sessione = data['id_sessione']
    
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        return
    
    # Estrai parametri camera
    camera_data = {}
    for param in ["x", "y", "zoom", "viewport_width", "viewport_height"]:
        if param in data:
            camera_data[param] = data[param]
    
    # Imposta la camera nel renderer
    graphics_renderer.set_camera(camera_data)
    
    # Se c'è un'entità camera, aggiorna anche quella
    camera_entities = sessione.get_entities_with_tag("camera")
    for entity in camera_entities:
        if entity.has_component("camera"):
            camera_comp = entity.get_component("camera")
            for param, value in camera_data.items():
                if hasattr(camera_comp, param):
                    setattr(camera_comp, param, value)
    
    # Conferma al client
    emit('camera_updated', {
        "camera": graphics_renderer.camera,
        "timestamp": time.time()
    })

def register_handlers(socketio_instance):
    """
    Registra gli handler di rendering
    
    Args:
        socketio_instance: Istanza SocketIO
    """
    socketio_instance.on_event('request_map_data', handle_request_map_data)
    socketio_instance.on_event('request_assets', handle_request_assets)
    socketio_instance.on_event('request_render_update', handle_request_render_update)
    socketio_instance.on_event('process_render_queue', handle_process_render_queue)
    socketio_instance.on_event('set_camera', handle_set_camera)
    
    logger.info("Handler di rendering registrati")

def render_taverna(taverna_state, sessione):
    """
    Renderizza la taverna e i suoi elementi
    
    Args:
        taverna_state: Lo stato della taverna
        sessione: Sessione di gioco attuale
    """
    logger.info("Rendering state: taverna")
    
    # Ottieni il giocatore
    giocatore = sessione.giocatore
    
    # Ottieni informazioni sulla mappa
    mappa = sessione.gestore_mappe.ottieni_mappa("taverna")
    if not mappa:
        logger.error("Mappa della taverna non trovata")
        return
    
    # Ottieni la posizione del giocatore
    pos_x, pos_y = giocatore.get_posizione("taverna")
    
    # Prepara i dati per il rendering
    render_data = {
        "tipo": "taverna",
        "mappa": mappa.to_dict() if hasattr(mappa, "to_dict") else {},
        "giocatore": {
            "posizione": {"x": pos_x, "y": pos_y},
            "nome": giocatore.nome
        },
        "npg": [npg.to_dict() for nome, npg in taverna_state.npg_presenti.items() if hasattr(npg, "to_dict")],
        "oggetti": [obj.to_dict() for id_obj, obj in taverna_state.oggetti_interattivi.items() if hasattr(obj, "to_dict")],
        "fase": taverna_state.fase
    }
    
    # Emetti evento di rendering
    room_id = f"session_{sessione.sessione_id}"
    socketio.emit('render_update', render_data, room=room_id)
    socketio.emit('rendering_completed', {}, room=room_id)

def render_mercato(mercato_state, sessione):
    """
    Renderizza il mercato e i suoi elementi
    
    Args:
        mercato_state: Lo stato del mercato
        sessione: Sessione di gioco attuale
    """
    logger.info("Rendering state: mercato")
    
    # Ottieni il giocatore
    giocatore = sessione.giocatore
    
    # Ottieni informazioni sulla mappa
    mappa = sessione.gestore_mappe.ottieni_mappa("mercato")
    if not mappa:
        logger.error("Mappa del mercato non trovata")
        return
    
    # Ottieni la posizione del giocatore
    pos_x, pos_y = giocatore.get_posizione("mercato")
    
    # Prepara i dati per il rendering
    render_data = {
        "tipo": "mercato",
        "mappa": mappa.to_dict() if hasattr(mappa, "to_dict") else {},
        "giocatore": {
            "posizione": {"x": pos_x, "y": pos_y},
            "nome": giocatore.nome
        },
        "npg": [npg.to_dict() for nome, npg in mercato_state.npg_presenti.items() if hasattr(npg, "to_dict")],
        "oggetti": [obj.to_dict() for id_obj, obj in mercato_state.oggetti_interattivi.items() if hasattr(obj, "to_dict")],
        "fase": mercato_state.fase
    }
    
    # Emetti evento di rendering
    room_id = f"session_{sessione.sessione_id}"
    socketio.emit('render_update', render_data, room=room_id)
    socketio.emit('rendering_completed', {}, room=room_id)

def render_scelta_mappa(scelta_mappa_state, sessione):
    """
    Renderizza l'interfaccia di scelta mappa e i suoi elementi
    
    Args:
        scelta_mappa_state: Lo stato della scelta mappa
        sessione: Sessione di gioco attuale
    """
    logger.info("Rendering state: scelta_mappa")
    
    # Ottieni il giocatore
    giocatore = sessione.giocatore
    
    # Ottieni la lista delle mappe disponibili
    lista_mappe = sessione.gestore_mappe.ottieni_lista_mappe()
    if not lista_mappe:
        logger.error("Nessuna mappa disponibile per il rendering")
        return
    
    # Ottieni la mappa corrente del giocatore
    mappa_corrente = giocatore.mappa_corrente
    
    # Prepara i dati di rendering per ciascuna mappa
    mappe_render = []
    for id_mappa, info_mappa in lista_mappe.items():
        # Evidenzia la mappa corrente
        is_corrente = (id_mappa == mappa_corrente)
        
        # Estrai informazioni sulla mappa
        nome_mappa = info_mappa.get("nome", id_mappa)
        descrizione = info_mappa.get("descrizione", "")
        livello_min = info_mappa.get("livello_min", 0)
        
        # Verifica accessibilità in base al livello
        accessibile = giocatore.livello >= livello_min
        
        mappe_render.append({
            "id": id_mappa,
            "nome": nome_mappa,
            "descrizione": descrizione,
            "livello_min": livello_min,
            "corrente": is_corrente,
            "accessibile": accessibile
        })
    
    # Prepara i dati per il rendering
    render_data = {
        "tipo": "scelta_mappa",
        "mappe": mappe_render,
        "mappa_corrente": mappa_corrente,
        "giocatore": {
            "nome": giocatore.nome,
            "livello": giocatore.livello
        },
        "prima_esecuzione": getattr(scelta_mappa_state, 'prima_esecuzione', False),
        "ui_aggiornata": getattr(scelta_mappa_state, 'ui_aggiornata', False)
    }
    
    # Emetti evento di rendering
    room_id = f"session_{sessione.sessione_id}"
    socketio.emit('render_update', render_data, room=room_id)
    socketio.emit('rendering_completed', {}, room=room_id)

def render_dialogo(dialogo_state, sessione):
    """
    Renderizza l'interfaccia di dialogo e i suoi elementi
    
    Args:
        dialogo_state: Lo stato del dialogo
        sessione: Sessione di gioco attuale
    """
    logger.info("Rendering state: dialogo")
    
    # Ottieni l'NPG con cui si sta dialogando
    npg = dialogo_state.npg
    if not npg:
        logger.error("NPG per il dialogo non trovato")
        return
    
    # Ottieni informazioni sul dialogo corrente
    stato_corrente = dialogo_state.stato_corrente
    dati_conversazione = npg.ottieni_conversazione(stato_corrente)
    if not dati_conversazione:
        logger.error(f"Dati conversazione per stato '{stato_corrente}' non trovati")
        return
    
    # Prepara il rendering dell'interfaccia di dialogo
    render_data = {
        "tipo": "dialogo",
        "npg": {
            "nome": npg.nome,
            "descrizione": getattr(npg, "descrizione", ""),
            "immagine": getattr(npg, "immagine", "npc_default"),
            "professione": getattr(npg, "professione", "")
        },
        "dialogo": {
            "stato": stato_corrente,
            "testo": dati_conversazione.get("testo", ""),
            "opzioni": dati_conversazione.get("opzioni", []),
            "effetto": dati_conversazione.get("effetto", None)
        },
        "fase": dialogo_state.fase,
        "ui_aggiornata": dialogo_state.ui_aggiornata,
        "dati_contestuali": dialogo_state.dati_contestuali
    }
    
    # Emetti evento di rendering
    room_id = f"session_{sessione.sessione_id}"
    socketio.emit('render_update', render_data, room=room_id)
    socketio.emit('rendering_completed', {}, room=room_id)

def render_prova_abilita(prova_state, sessione):
    """
    Renderizza l'interfaccia per le prove di abilità
    
    Args:
        prova_state: Lo stato della prova di abilità
        sessione: Sessione di gioco attuale
    """
    logger.info("Rendering state: prova_abilita")
    
    # Ottieni il giocatore
    giocatore = sessione.get_player_entity()
    
    # Deserializza lo stato se necessario
    from states.prova_abilita import ProvaAbilitaState
    state = prova_state if isinstance(prova_state, ProvaAbilitaState) else ProvaAbilitaState.from_dict(prova_state)
    
    # Prepara le informazioni sulle abilità disponibili
    abilita_disponibili = []
    if hasattr(giocatore, "get_abilita") and callable(giocatore.get_abilita):
        abilita_disponibili = giocatore.get_abilita()
    else:
        # Fallback per entità senza metodo get_abilita
        for componente in giocatore.get_all_components():
            if hasattr(componente, "abilita"):
                abilita_disponibili.extend(componente.abilita)
    
    # Ottieni informazioni sul target (se presente)
    target_info = None
    target_id = state.dati_contestuali.get("target_id")
    if target_id:
        target = sessione.get_entity(target_id)
        if target:
            target_info = {
                "id": target.id,
                "nome": target.name if hasattr(target, "name") else str(target.id),
                "tipo": "npg" if target.has_tag("npg") or target.has_tag("npc") else "oggetto"
            }
    
    # Prepara i dati per il rendering
    render_data = {
        "tipo": "prova_abilita",
        "fase": state.fase,
        "abilita_scelta": state.abilita_scelta,
        "abilita_disponibili": abilita_disponibili,
        "difficolta": state.dati_contestuali.get("difficolta", 10),
        "modalita": state.dati_contestuali.get("modalita", "semplice"),
        "giocatore": {
            "id": giocatore.id,
            "nome": giocatore.name if hasattr(giocatore, "name") else str(giocatore.id)
        },
        "target": target_info,
        "risultato": state.dati_contestuali.get("risultato"),
        "ui_aggiornata": state.ui_aggiornata
    }
    
    # Emetti evento di rendering
    room_id = f"session_{sessione.sessione_id}"
    socketio.emit('render_update', render_data, room=room_id)
    socketio.emit('rendering_completed', {}, room=room_id) 