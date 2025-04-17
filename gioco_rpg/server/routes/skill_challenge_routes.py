from flask import request, jsonify, Blueprint
import logging
import random

from server.utils.session import sessioni_attive, salva_sessione

# Configura il logger
logger = logging.getLogger(__name__)

# Crea il blueprint per le route delle prove di abilità
skill_challenge_routes = Blueprint('skill_challenge_routes', __name__)

@skill_challenge_routes.route("/inizia", methods=["POST"])
def inizia_prova_abilita():
    """Inizia una prova di abilità"""
    data = request.json or {}
    id_sessione = data.get("id_sessione")
    tipo_prova = data.get("tipo_prova")  # "giocatore", "npg", "confronto"
    
    if not id_sessione or tipo_prova not in ["giocatore", "npg", "confronto"]:
        return jsonify({
            "successo": False,
            "errore": "Parametri mancanti o non validi"
        }), 400
    
    # Verifica che la sessione esista
    if id_sessione not in sessioni_attive:
        return jsonify({
            "successo": False,
            "errore": "Sessione non trovata"
        }), 404
    
    try:
        # Ottieni il mondo dalla sessione
        world = sessioni_attive[id_sessione]
        
        # Crea un nuovo stato ProvaAbilitaState
        from states.prova_abilita import ProvaAbilitaState
        
        # Prepara il contesto per il nuovo stato
        contesto = {
            "world": world,
            "tipo_prova": tipo_prova
        }
        
        # Crea la nuova istanza di stato
        state = ProvaAbilitaState(contesto)
        
        # Memorizza lo stato nella sessione
        world.set_temporary_state("prova_abilita", state.to_dict())
        
        return jsonify({
            "successo": True,
            "stato": "iniziato",
            "tipo_prova": tipo_prova,
            "fase": state.fase
        })
    except Exception as e:
        logger.error(f"Errore durante l'inizializzazione della prova: {e}")
        return jsonify({
            "successo": False,
            "errore": str(e)
        }), 500

@skill_challenge_routes.route("/abilita_disponibili", methods=["GET"])
def elenca_abilita():
    """Ottieni la lista delle abilità disponibili per una prova"""
    id_sessione = request.args.get("id_sessione")
    entita_id = request.args.get("entita_id")  # Opzionale, se non fornito usa il giocatore
    
    if not id_sessione:
        return jsonify({
            "successo": False,
            "errore": "ID sessione richiesto"
        }), 400
    
    # Verifica che la sessione esista
    if id_sessione not in sessioni_attive:
        return jsonify({
            "successo": False,
            "errore": "Sessione non trovata"
        }), 404
    
    try:
        # Ottieni il mondo dalla sessione
        world = sessioni_attive[id_sessione]
        
        # Ottieni l'entità target
        if entita_id:
            entita = world.get_entity(entita_id)
        else:
            # Usa il giocatore se non specificato
            entita = world.get_player_entity()
            
        if not entita:
            return jsonify({
                "successo": False,
                "errore": "Entità non trovata"
            }), 404
            
        # Ottieni le abilità dell'entità
        abilita = []
        if hasattr(entita, "get_abilita") and callable(entita.get_abilita):
            abilita = entita.get_abilita()
        else:
            # Fallback per entità senza metodo get_abilita
            for componente in entita.get_all_components():
                if hasattr(componente, "abilita"):
                    abilita.extend(componente.abilita)
        
        return jsonify({
            "successo": True,
            "abilita": abilita
        })
    except Exception as e:
        logger.error(f"Errore durante l'ottenimento delle abilità: {e}")
        return jsonify({
            "successo": False,
            "errore": str(e)
        }), 500

@skill_challenge_routes.route("/esegui", methods=["POST"])
def esegui_prova_abilita():
    """Esegui una prova di abilità"""
    data = request.json or {}
    id_sessione = data.get("id_sessione")
    modalita = data.get("modalita", "semplice")  # semplice o avanzata
    abilita = data.get("abilita")
    entita_id = data.get("entita_id")  # Entità che esegue la prova
    target_id = data.get("target_id")  # Entità o oggetto target (per confronto)
    difficolta = data.get("difficolta", 10)  # Difficoltà della prova
    
    if not id_sessione or not abilita:
        return jsonify({
            "successo": False,
            "errore": "Parametri mancanti o non validi"
        }), 400
    
    # Verifica che la sessione esista
    if id_sessione not in sessioni_attive:
        return jsonify({
            "successo": False,
            "errore": "Sessione non trovata"
        }), 404
    
    try:
        # Ottieni il mondo dalla sessione
        world = sessioni_attive[id_sessione]
        
        # Ottieni lo stato della prova
        stato_prova = world.get_temporary_state("prova_abilita")
        if not stato_prova:
            return jsonify({
                "successo": False,
                "errore": "Nessuna prova di abilità in corso"
            }), 400
            
        # Deserializza lo stato
        from states.prova_abilita import ProvaAbilitaState
        state = ProvaAbilitaState.from_dict(stato_prova)
        
        # Ottieni l'entità che esegue la prova
        if entita_id:
            entita = world.get_entity(entita_id)
        else:
            # Usa il giocatore se non specificato
            entita = world.get_player_entity()
            
        if not entita:
            return jsonify({
                "successo": False,
                "errore": "Entità non trovata"
            }), 404
        
        # Ottieni il target (se esiste)
        target = None
        if target_id:
            target = world.get_entity(target_id)
            
        # Imposta i parametri nella state
        state.abilita_scelta = abilita
        state.dati_contestuali = {
            "modalita": modalita,
            "difficolta": difficolta,
            "entita_id": entita_id or entita.id,
            "target_id": target_id
        }
        
        # Esegui la prova in base alla modalità
        if modalita == "semplice":
            # Prova semplice
            risultato = random.randint(1, 20)
            
            # Aggiungi bonus dall'abilità dell'entità
            for componente in entita.get_all_components():
                if hasattr(componente, "get_bonus_abilita") and callable(componente.get_bonus_abilita):
                    risultato += componente.get_bonus_abilita(abilita)
            
            # Determina successo/fallimento
            successo = risultato >= difficolta
            
            # Gestisci conseguenze
            if target:
                # Caso confronto
                target_risultato = random.randint(1, 20)
                for componente in target.get_all_components():
                    if hasattr(componente, "get_bonus_abilita") and callable(componente.get_bonus_abilita):
                        target_risultato += componente.get_bonus_abilita(abilita)
                
                # Determina vincitore del confronto
                confronto_successo = risultato >= target_risultato
                
                response_data = {
                    "successo": True,
                    "tipo": "confronto",
                    "entita": entita.nome if hasattr(entita, "nome") else str(entita.id),
                    "entita_risultato": risultato,
                    "target": target.nome if hasattr(target, "nome") else str(target.id),
                    "target_risultato": target_risultato,
                    "vincitore": entita.nome if confronto_successo else target.nome
                }
            else:
                # Caso prova normale
                response_data = {
                    "successo": True,
                    "tipo": "normale",
                    "entita": entita.nome if hasattr(entita, "nome") else str(entita.id),
                    "risultato": risultato,
                    "difficolta": difficolta,
                    "esito": "successo" if successo else "fallimento"
                }
        else:
            # Prova avanzata (più dettagli)
            # Qui implementiamo una versione più complessa che considera più fattori
            
            # Tiro di base
            tiro_base = random.randint(1, 20)
            
            # Calcola bonus e modificatori
            bonus_abilita = 0
            bonus_situazionali = 0
            
            # Ottieni bonus dall'abilità
            for componente in entita.get_all_components():
                if hasattr(componente, "get_bonus_abilita") and callable(componente.get_bonus_abilita):
                    bonus_abilita += componente.get_bonus_abilita(abilita)
                    
                # Ottieni eventuali bonus situazionali
                if hasattr(componente, "get_bonus_situazionali") and callable(componente.get_bonus_situazionali):
                    bonus_situazionali += componente.get_bonus_situazionali(abilita)
            
            # Calcola il risultato finale
            risultato_finale = tiro_base + bonus_abilita + bonus_situazionali
            
            # Determina il successo
            successo = risultato_finale >= difficolta
            
            # Gestisci conseguenze (possibilmente diverse per successo/fallimento)
            if target:
                # Caso confronto
                target_tiro_base = random.randint(1, 20)
                target_bonus_abilita = 0
                target_bonus_situazionali = 0
                
                # Calcola bonus per il target
                for componente in target.get_all_components():
                    if hasattr(componente, "get_bonus_abilita") and callable(componente.get_bonus_abilita):
                        target_bonus_abilita += componente.get_bonus_abilita(abilita)
                    
                    # Bonus situazionali del target
                    if hasattr(componente, "get_bonus_situazionali") and callable(componente.get_bonus_situazionali):
                        target_bonus_situazionali += componente.get_bonus_situazionali(abilita)
                
                target_risultato_finale = target_tiro_base + target_bonus_abilita + target_bonus_situazionali
                
                # Determina vincitore del confronto
                confronto_successo = risultato_finale >= target_risultato_finale
                
                response_data = {
                    "successo": True,
                    "tipo": "confronto_avanzato",
                    "entita": entita.nome if hasattr(entita, "nome") else str(entita.id),
                    "tiro_base": tiro_base,
                    "bonus_abilita": bonus_abilita,
                    "bonus_situazionali": bonus_situazionali,
                    "risultato_finale": risultato_finale,
                    "target": target.nome if hasattr(target, "nome") else str(target.id),
                    "target_tiro_base": target_tiro_base,
                    "target_bonus_abilita": target_bonus_abilita,
                    "target_bonus_situazionali": target_bonus_situazionali,
                    "target_risultato_finale": target_risultato_finale,
                    "vincitore": entita.nome if confronto_successo else target.nome
                }
            else:
                # Caso prova normale avanzata
                response_data = {
                    "successo": True,
                    "tipo": "avanzata",
                    "entita": entita.nome if hasattr(entita, "nome") else str(entita.id),
                    "tiro_base": tiro_base,
                    "bonus_abilita": bonus_abilita,
                    "bonus_situazionali": bonus_situazionali,
                    "risultato_finale": risultato_finale,
                    "difficolta": difficolta,
                    "esito": "successo" if successo else "fallimento"
                }
        
        # Aggiorna lo stato e salvalo
        state.fase = "conclusione"
        world.set_temporary_state("prova_abilita", state.to_dict())
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Errore durante l'esecuzione della prova: {e}")
        return jsonify({
            "successo": False,
            "errore": str(e)
        }), 500

@skill_challenge_routes.route("/npg_vicini", methods=["GET"])
def elenca_npg_vicini():
    """Ottieni la lista degli NPG vicini al giocatore"""
    id_sessione = request.args.get("id_sessione")
    
    if not id_sessione:
        return jsonify({
            "successo": False,
            "errore": "ID sessione richiesto"
        }), 400
    
    # Verifica che la sessione esista
    if id_sessione not in sessioni_attive:
        return jsonify({
            "successo": False,
            "errore": "Sessione non trovata"
        }), 404
    
    try:
        # Ottieni il mondo dalla sessione
        world = sessioni_attive[id_sessione]
        
        # Ottieni l'entità del giocatore
        player = world.get_player_entity()
        if not player:
            return jsonify({
                "successo": False,
                "errore": "Giocatore non trovato"
            }), 404
            
        # Ottieni il componente posizione del giocatore
        position_component = player.get_component("position")
        if not position_component:
            return jsonify({
                "successo": False,
                "errore": "Componente posizione non trovato"
            }), 404
            
        # Ottieni la mappa corrente
        map_name = position_component.map_name
        
        # Trova NPG vicini (entità con tag "npc" sulla stessa mappa)
        npg_vicini = []
        for entity in world.get_entities():
            if entity.has_tag("npc"):
                entity_pos = entity.get_component("position")
                if entity_pos and entity_pos.map_name == map_name:
                    # Calcola distanza
                    dx = entity_pos.x - position_component.x
                    dy = entity_pos.y - position_component.y
                    distanza = (dx**2 + dy**2)**0.5
                    
                    # Considera vicini se a distanza <= 5
                    if distanza <= 5:
                        npg_vicini.append({
                            "id": entity.id,
                            "nome": entity.nome if hasattr(entity, "nome") else f"NPG {entity.id}",
                            "distanza": round(distanza, 2)
                        })
        
        return jsonify({
            "successo": True,
            "npg_vicini": npg_vicini
        })
    except Exception as e:
        logger.error(f"Errore durante la ricerca di NPG vicini: {e}")
        return jsonify({
            "successo": False,
            "errore": str(e)
        }), 500

@skill_challenge_routes.route("/oggetti_vicini", methods=["GET"])
def elenca_oggetti_vicini():
    """Ottieni la lista degli oggetti interagibili vicini al giocatore"""
    id_sessione = request.args.get("id_sessione")
    
    if not id_sessione:
        return jsonify({
            "successo": False,
            "errore": "ID sessione richiesto"
        }), 400
    
    # Verifica che la sessione esista
    if id_sessione not in sessioni_attive:
        return jsonify({
            "successo": False,
            "errore": "Sessione non trovata"
        }), 404
    
    try:
        # Ottieni il mondo dalla sessione
        world = sessioni_attive[id_sessione]
        
        # Ottieni l'entità del giocatore
        player = world.get_player_entity()
        if not player:
            return jsonify({
                "successo": False,
                "errore": "Giocatore non trovato"
            }), 404
            
        # Ottieni il componente posizione del giocatore
        position_component = player.get_component("position")
        if not position_component:
            return jsonify({
                "successo": False,
                "errore": "Componente posizione non trovato"
            }), 404
            
        # Ottieni la mappa corrente
        map_name = position_component.map_name
        
        # Trova oggetti vicini (entità con componente "interactable" sulla stessa mappa)
        oggetti_vicini = []
        for entity in world.get_entities():
            if entity.has_component("interactable"):
                entity_pos = entity.get_component("position")
                if entity_pos and entity_pos.map_name == map_name:
                    # Calcola distanza
                    dx = entity_pos.x - position_component.x
                    dy = entity_pos.y - position_component.y
                    distanza = (dx**2 + dy**2)**0.5
                    
                    # Considera vicini se a distanza <= 3
                    if distanza <= 3:
                        oggetti_vicini.append({
                            "id": entity.id,
                            "nome": entity.nome if hasattr(entity, "nome") else f"Oggetto {entity.id}",
                            "distanza": round(distanza, 2)
                        })
        
        return jsonify({
            "successo": True,
            "oggetti_vicini": oggetti_vicini
        })
    except Exception as e:
        logger.error(f"Errore durante la ricerca di oggetti vicini: {e}")
        return jsonify({
            "successo": False,
            "errore": str(e)
        }), 500

@skill_challenge_routes.route("/termina", methods=["POST"])
def termina_prova_abilita():
    """Termina una prova di abilità e applica conseguenze"""
    data = request.json or {}
    id_sessione = data.get("id_sessione")
    
    if not id_sessione:
        return jsonify({
            "successo": False,
            "errore": "ID sessione richiesto"
        }), 400
    
    # Verifica che la sessione esista
    if id_sessione not in sessioni_attive:
        return jsonify({
            "successo": False,
            "errore": "Sessione non trovata"
        }), 404
    
    try:
        # Ottieni il mondo dalla sessione
        world = sessioni_attive[id_sessione]
        
        # Ottieni lo stato della prova
        stato_prova = world.get_temporary_state("prova_abilita")
        if not stato_prova:
            return jsonify({
                "successo": False,
                "errore": "Nessuna prova di abilità in corso"
            }), 400
            
        # Rimuovi lo stato della prova
        world.remove_temporary_state("prova_abilita")
        
        # Salva le modifiche alla sessione
        salva_sessione(id_sessione, world)
        
        return jsonify({
            "successo": True,
            "messaggio": "Prova di abilità terminata"
        })
    except Exception as e:
        logger.error(f"Errore durante la terminazione della prova: {e}")
        return jsonify({
            "successo": False,
            "errore": str(e)
        }), 500 