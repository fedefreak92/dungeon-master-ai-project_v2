from flask import Blueprint, jsonify, request
from core.ecs.component import InventoryComponent
from server.utils.session import sessioni_attive, salva_sessione
from flask_cors import cross_origin

# Crea un blueprint per le route dell'inventario
inventory_routes = Blueprint('inventory_routes', __name__)

@inventory_routes.route('/list', methods=['POST'])
@cross_origin()
def list_inventory():
    """
    Ottiene l'inventario di un'entità
    """
    # Verifica che il JSON sia valido
    if not request.is_json:
        return jsonify({
            "successo": False,
            "errore": "La richiesta deve contenere dati in formato JSON"
        }), 400
    
    # Ottieni i dati dalla richiesta
    data = request.get_json()
    
    # Verifica i parametri obbligatori
    if 'id_sessione' not in data:
        return jsonify({
            "successo": False,
            "errore": "Il parametro 'id_sessione' è obbligatorio"
        }), 400
        
    if 'entity_id' not in data:
        return jsonify({
            "successo": False,
            "errore": "Il parametro 'entity_id' è obbligatorio"
        }), 400
    
    # Ottieni la sessione
    sessione = sessioni_attive.get(data['id_sessione'])
    if not sessione:
        return jsonify({
            "successo": False,
            "errore": "Sessione non valida o scaduta"
        }), 403
    
    # La sessione stessa è il world
    world = sessione
    if not world:
        return jsonify({
            "successo": False,
            "errore": "Mondo di gioco non trovato"
        }), 404
    
    # Ottieni l'entità
    entity = world.get_entity(data['entity_id'])
    if not entity:
        return jsonify({
            "successo": False,
            "errore": f"Entità con ID {data['entity_id']} non trovata"
        }), 404
    
    # Ottieni il componente inventario
    inventory_component = entity.get_component("inventory")
    if not inventory_component:
        return jsonify({
            "successo": False,
            "errore": f"L'entità non ha un componente inventario"
        }), 404
    
    # Prepara i dati dell'inventario per la risposta
    items = []
    for item in inventory_component.items:
        if hasattr(item, 'to_dict') and callable(getattr(item, 'to_dict')):
            items.append(item.to_dict())
        elif isinstance(item, dict):
            items.append(item)
        else:
            # Fallback se l'item non ha un metodo to_dict
            items.append({"id": getattr(item, "id", "unknown"), "name": str(item)})
    
    # Restituisci l'inventario
    return jsonify({
        "successo": True,
        "items": items,
        "capacity": inventory_component.capacity
    })

@inventory_routes.route('/add', methods=['POST'])
@cross_origin()
def add_item():
    """
    Aggiunge un item all'inventario di un'entità
    """
    # Verifica che il JSON sia valido
    if not request.is_json:
        return jsonify({
            "successo": False,
            "errore": "La richiesta deve contenere dati in formato JSON"
        }), 400
    
    # Ottieni i dati dalla richiesta
    data = request.get_json()
    
    # Verifica i parametri obbligatori
    if 'id_sessione' not in data:
        return jsonify({
            "successo": False,
            "errore": "Il parametro 'id_sessione' è obbligatorio"
        }), 400
        
    if 'entity_id' not in data:
        return jsonify({
            "successo": False,
            "errore": "Il parametro 'entity_id' è obbligatorio"
        }), 400
        
    if 'item_data' not in data:
        return jsonify({
            "successo": False,
            "errore": "Il parametro 'item_data' è obbligatorio"
        }), 400
    
    # Ottieni la sessione
    sessione = sessioni_attive.get(data['id_sessione'])
    if not sessione:
        return jsonify({
            "successo": False,
            "errore": "Sessione non valida o scaduta"
        }), 403
    
    # La sessione stessa è il world
    world = sessione
    if not world:
        return jsonify({
            "successo": False,
            "errore": "Mondo di gioco non trovato"
        }), 404
    
    # Ottieni l'entità
    entity = world.get_entity(data['entity_id'])
    if not entity:
        return jsonify({
            "successo": False,
            "errore": f"Entità con ID {data['entity_id']} non trovata"
        }), 404
    
    # Ottieni il componente inventario
    inventory_component = entity.get_component("inventory")
    if not inventory_component:
        # Se l'entità non ha un inventario, crealo
        inventory_component = InventoryComponent()
        entity.add_component("inventory", inventory_component)
    
    # Crea un item dal dizionario fornito
    # Nota: questa è una implementazione semplificata. Un'implementazione più completa
    # dovrebbe gestire la creazione di oggetti specifici in base al tipo.
    item_data = data['item_data']
    
    # Aggiungi l'item all'inventario
    success = inventory_component.add_item(item_data)
    
    # Salva la sessione
    salva_sessione(data['id_sessione'], sessione)
    
    if success:
        return jsonify({
            "successo": True,
            "messaggio": "Item aggiunto all'inventario"
        })
    else:
        return jsonify({
            "successo": False,
            "errore": "Impossibile aggiungere l'item all'inventario (capacità massima raggiunta)"
        }), 400

@inventory_routes.route('/remove', methods=['POST'])
@cross_origin()
def remove_item():
    """
    Rimuove un item dall'inventario di un'entità
    """
    # Verifica che il JSON sia valido
    if not request.is_json:
        return jsonify({
            "successo": False,
            "errore": "La richiesta deve contenere dati in formato JSON"
        }), 400
    
    # Ottieni i dati dalla richiesta
    data = request.get_json()
    
    # Verifica i parametri obbligatori
    if 'id_sessione' not in data:
        return jsonify({
            "successo": False,
            "errore": "Il parametro 'id_sessione' è obbligatorio"
        }), 400
        
    if 'entity_id' not in data:
        return jsonify({
            "successo": False,
            "errore": "Il parametro 'entity_id' è obbligatorio"
        }), 400
        
    if 'item_id' not in data:
        return jsonify({
            "successo": False,
            "errore": "Il parametro 'item_id' è obbligatorio"
        }), 400
    
    # Ottieni la sessione
    sessione = sessioni_attive.get(data['id_sessione'])
    if not sessione:
        return jsonify({
            "successo": False,
            "errore": "Sessione non valida o scaduta"
        }), 403
    
    # La sessione stessa è il world
    world = sessione
    if not world:
        return jsonify({
            "successo": False,
            "errore": "Mondo di gioco non trovato"
        }), 404
    
    # Ottieni l'entità
    entity = world.get_entity(data['entity_id'])
    if not entity:
        return jsonify({
            "successo": False,
            "errore": f"Entità con ID {data['entity_id']} non trovata"
        }), 404
    
    # Ottieni il componente inventario
    inventory_component = entity.get_component("inventory")
    if not inventory_component:
        return jsonify({
            "successo": False,
            "errore": f"L'entità non ha un componente inventario"
        }), 404
    
    # Cerca l'item da rimuovere
    found = False
    for item in inventory_component.items:
        item_id = None
        if hasattr(item, 'id'):
            item_id = item.id
        elif isinstance(item, dict) and 'id' in item:
            item_id = item['id']
        
        if item_id == data['item_id']:
            # Rimuovi l'item
            inventory_component.remove_item(item)
            found = True
            break
    
    # Salva la sessione
    salva_sessione(data['id_sessione'], sessione)
    
    if found:
        return jsonify({
            "successo": True,
            "messaggio": "Item rimosso dall'inventario"
        })
    else:
        return jsonify({
            "successo": False,
            "errore": f"Item con ID {data['item_id']} non trovato nell'inventario"
        }), 404

@inventory_routes.route('/update_capacity', methods=['POST'])
@cross_origin()
def update_inventory_capacity():
    """
    Aggiorna la capacità dell'inventario di un'entità
    """
    # Verifica che il JSON sia valido
    if not request.is_json:
        return jsonify({
            "successo": False,
            "errore": "La richiesta deve contenere dati in formato JSON"
        }), 400
    
    # Ottieni i dati dalla richiesta
    data = request.get_json()
    
    # Verifica i parametri obbligatori
    if 'id_sessione' not in data:
        return jsonify({
            "successo": False,
            "errore": "Il parametro 'id_sessione' è obbligatorio"
        }), 400
        
    if 'entity_id' not in data:
        return jsonify({
            "successo": False,
            "errore": "Il parametro 'entity_id' è obbligatorio"
        }), 400
        
    if 'capacity' not in data:
        return jsonify({
            "successo": False,
            "errore": "Il parametro 'capacity' è obbligatorio"
        }), 400
    
    # Ottieni la sessione
    sessione = sessioni_attive.get(data['id_sessione'])
    if not sessione:
        return jsonify({
            "successo": False,
            "errore": "Sessione non valida o scaduta"
        }), 403
    
    # La sessione stessa è il world
    world = sessione
    if not world:
        return jsonify({
            "successo": False,
            "errore": "Mondo di gioco non trovato"
        }), 404
    
    # Ottieni l'entità
    entity = world.get_entity(data['entity_id'])
    if not entity:
        return jsonify({
            "successo": False,
            "errore": f"Entità con ID {data['entity_id']} non trovata"
        }), 404
    
    # Ottieni il componente inventario
    inventory_component = entity.get_component("inventory")
    if not inventory_component:
        # Se l'entità non ha un inventario, crealo
        inventory_component = InventoryComponent(capacity=data['capacity'])
        entity.add_component("inventory", inventory_component)
    else:
        # Aggiorna la capacità
        inventory_component.capacity = data['capacity']
    
    # Salva la sessione
    salva_sessione(data['id_sessione'], sessione)
    
    return jsonify({
        "successo": True,
        "messaggio": f"Capacità dell'inventario aggiornata a {data['capacity']}"
    }) 