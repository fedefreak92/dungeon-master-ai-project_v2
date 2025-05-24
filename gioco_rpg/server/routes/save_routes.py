from flask import request, jsonify, Blueprint
import datetime
import os
import pickle
import time
import logging
from uuid import uuid4
import json
from pathlib import Path

from util.config import SAVE_DIR, get_save_path, list_save_files, delete_save_file, normalize_save_data
from server.utils.session import sessioni_attive, salva_sessione, valida_input
from core.ecs.world import World

# Configura il logger
logger = logging.getLogger(__name__)

# Crea il blueprint per le route di salvataggio
save_routes = Blueprint('save_routes', __name__)

# Versione corrente del formato di salvataggio
SAVE_FORMAT_VERSION = "2.0.0"

def migra_formato_salvataggio(save_data):
    """
    Migra un salvataggio dal vecchio formato al nuovo formato 2.0.0
    
    Args:
        save_data (dict): Dati di salvataggio in formato vecchio
        
    Returns:
        dict: Dati nel formato nuovo
    """
    # Verifica se è già nel nuovo formato
    if "metadata" in save_data and "world" in save_data:
        return save_data
        
    logger.info("Migrazione del salvataggio dal formato vecchio al formato 2.0.0")
    
    # Crea la struttura del nuovo formato
    nuovo_formato = {
        "metadata": {
            "nome": save_data.get("nome_salvataggio", "Salvataggio_migrato"),
            "data": datetime.datetime.now().isoformat(),
            "versione": "2.0.0",
            "formato": "json"
        },
        "world": {
            "entities": {},
            "events": [],
            "pending_events": [],
            "temporary_states": {}
        }
    }
    
    # Migra i dati del giocatore
    if "giocatore" in save_data:
        giocatore = save_data["giocatore"]
        player_id = str(uuid4())
        
        # Crea l'entità giocatore completa con tutti i dati
        player_entity = {
            "id": player_id,
            "name": giocatore.get("nome", "Giocatore"),
            "components": {},
            "tags": ["player"],
            "active": True,
            "marked_for_removal": False
        }
        
        # Copia tutti gli attributi rilevanti dal vecchio giocatore
        for attr in ["hp", "hp_max", "forza_base", "destrezza_base", "costituzione_base", 
                    "intelligenza_base", "saggezza_base", "carisma_base", "classe", 
                    "inventario", "oro", "esperienza", "livello", "arma", "armatura", 
                    "accessori", "abilita_competenze", "bonus_competenza", "difesa",
                    "progresso_missioni", "missioni_attive", "missioni_completate"]:
            if attr in giocatore:
                player_entity[attr] = giocatore[attr]
        
        # Gestisci la posizione
        if "x" in giocatore and "y" in giocatore:
            player_entity["x"] = giocatore["x"]
            player_entity["y"] = giocatore["y"]
        elif "posizione" in giocatore and isinstance(giocatore["posizione"], list) and len(giocatore["posizione"]) >= 2:
            player_entity["x"] = giocatore["posizione"][0]
            player_entity["y"] = giocatore["posizione"][1]
            
        # Mappa corrente
        if "mappa_corrente" in giocatore:
            player_entity["mappa_corrente"] = giocatore["mappa_corrente"]
        elif "mappa_corrente" in save_data:
            player_entity["mappa_corrente"] = save_data["mappa_corrente"]
            
        # Aggiungi l'entità giocatore al mondo
        nuovo_formato["world"]["entities"][player_id] = player_entity
        
        # Crea evento di cambio mappa
        nuovo_formato["world"]["events"].append({
            "type": "map_change",
            "player_id": player_id,
            "previous_map": None,
            "new_map": player_entity.get("mappa_corrente", "taverna"),
            "position": {
                "x": player_entity.get("x", 0),
                "y": player_entity.get("y", 0)
            }
        })
    
    # Migra gli stati
    if "stati" in save_data and isinstance(save_data["stati"], list):
        for stato in save_data["stati"]:
            if "type" in stato:
                # Estrai il nome dello stato (rimuovendo "State" dal tipo)
                nome_stato = stato["type"].lower().replace("state", "")
                nuovo_formato["world"]["temporary_states"][nome_stato] = stato
                
    # Migra mappa_corrente globale
    if "mappa_corrente" in save_data:
        if "mappe" not in nuovo_formato["world"]["temporary_states"]:
            nuovo_formato["world"]["temporary_states"]["mappe"] = {}
        nuovo_formato["world"]["temporary_states"]["mappe"]["mappa_attuale"] = save_data["mappa_corrente"]
    
    # Migra mappe e npg come stati temporanei
    if "mappe" in save_data:
        nuovo_formato["world"]["temporary_states"]["mappe"] = save_data["mappe"]
    
    if "npg" in save_data:
        nuovo_formato["world"]["temporary_states"]["npg"] = save_data["npg"]
        
    return nuovo_formato

def sanifica_salvataggio(save_data):
    """
    Sanifica i dati di salvataggio e applica migrazione se necessario
    
    Args:
        save_data (dict): Dati del salvataggio deserializzati
        
    Returns:
        dict: Dati del salvataggio sanificati e migrati se necessario
    """
    try:
        # Verifica se è necessaria una migrazione (formato vecchio)
        if "giocatore" in save_data and "world" not in save_data:
            logger.info("Rilevato formato salvataggio vecchio, avvio migrazione")
            return migra_formato_salvataggio(save_data)
            
        # Ottieni i metadati o crea un dizionario vuoto
        metadata = save_data.get("metadata", {})
        
        # Controlla la versione del salvataggio
        save_version = metadata.get("versione", "1.0.0")
        
        # Se il salvataggio ha una versione precedente, aggiorna la versione
        if save_version < SAVE_FORMAT_VERSION:
            logger.info(f"Aggiornamento versione salvataggio da {save_version} a {SAVE_FORMAT_VERSION}")
            metadata["versione"] = SAVE_FORMAT_VERSION
            save_data["metadata"] = metadata
            
        # Controlla la presenza di world
        if "world" not in save_data:
            logger.warning("Salvataggio senza dati 'world', creazione di un oggetto world vuoto")
            save_data["world"] = {}
            
        # Controlla e sanifica gli stati del gioco
        if "world" in save_data and isinstance(save_data["world"], dict):
            world_data = save_data["world"]
            
            # Controlla se ci sono stati salvati
            if "states" in world_data and isinstance(world_data["states"], dict):
                states_data = world_data["states"]
                
                # Itera su ogni stato e applica sanificazioni specifiche
                for state_name, state_data in states_data.items():
                    if state_name == "taverna" and isinstance(state_data, dict):
                        # Rimuovi esplicitamente _handle_click_event se presente
                        if "_handle_click_event" in state_data:
                            logger.info(f"Rimozione attributo obsoleto '_handle_click_event' dallo stato {state_name}")
                            del state_data["_handle_click_event"]
        
        return save_data
    except Exception as e:
        logger.warning(f"Errore durante la sanificazione del salvataggio: {e}")
        # In caso di errore, restituisci i dati originali
        return save_data

@save_routes.route("/elenco", methods=["GET"])
def elenca_salvataggi():
    """Ottieni lista dei salvataggi disponibili"""
    try:
        # Ottieni la lista dei file di salvataggio
        salvataggi = list_save_files()
        
        # Recupera i metadati di ogni salvataggio
        risultati = []
        for nome_salvataggio in salvataggi:
            try:
                save_path = get_save_path(nome_salvataggio)
                
                # Determina il formato del file
                is_json_format = str(save_path).endswith('.json')
                
                # Leggi il file in base al formato
                if is_json_format:
                    try:
                        with open(save_path, 'r', encoding='utf-8') as f:
                            save_data = json.load(f)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # Fallback a pickle se il file non è JSON valido
                        with open(save_path, 'rb') as f:
                            save_data = pickle.load(f)
                else:
                    with open(save_path, 'rb') as f:
                        save_data = pickle.load(f)
                
                # Rimuovi l'estensione dal nome del salvataggio
                nome_senza_estensione = nome_salvataggio
                for ext in ['.json', '.dat', '.pickle']:
                    nome_senza_estensione = nome_senza_estensione.replace(ext, '')
                
                metadata = save_data.get("metadata", {})
                risultati.append({
                    "nome": nome_senza_estensione,
                    "data": metadata.get("data", ""),
                    "versione": metadata.get("versione", ""),
                    "formato": "json" if is_json_format else "pickle"
                })
            except Exception as e:
                logger.warning(f"Errore nella lettura del salvataggio {nome_salvataggio}: {e}")
                # Se c'è un errore nel leggere un salvataggio, includi solo il nome
                # Rimuovi l'estensione dal nome del salvataggio
                nome_senza_estensione = nome_salvataggio
                for ext in ['.json', '.dat', '.pickle']:
                    nome_senza_estensione = nome_senza_estensione.replace(ext, '')
                    
                risultati.append({
                    "nome": nome_senza_estensione,
                    "data": "",
                    "versione": "",
                    "formato": "sconosciuto"
                })
        
        return jsonify({
            "successo": True,
            "salvataggi": risultati
        })
    except Exception as e:
        logger.error(f"Errore nell'elenco dei salvataggi: {e}")
        return jsonify({
            "successo": False,
            "errore": str(e)
        }), 500

@save_routes.route("/elimina", methods=["POST"])
def elimina_salvataggio():
    """Elimina un salvataggio"""
    data = request.json or {}
    nome_salvataggio = data.get("nome_salvataggio")
    
    if not nome_salvataggio:
        return jsonify({
            "successo": False,
            "errore": "Nome salvataggio non fornito"
        }), 400
    
    try:
        # Elimina il file di salvataggio
        if delete_save_file(nome_salvataggio):
            return jsonify({
                "successo": True,
                "messaggio": f"Salvataggio '{nome_salvataggio}' eliminato"
            })
        else:
            return jsonify({
                "successo": False,
                "errore": f"Salvataggio '{nome_salvataggio}' non trovato"
            }), 404
    except Exception as e:
        logger.error(f"Errore nell'eliminazione del salvataggio: {e}")
        return jsonify({
            "successo": False,
            "errore": str(e)
        }), 500

@save_routes.route("/salva", methods=["POST"])
def salva_mondo_ecs():
    """Salva il mondo ECS come file di salvataggio"""
    data = request.json or {}
    id_sessione = data.get("id_sessione")
    nome_salvataggio = data.get("nome_salvataggio", f"Salvataggio_{int(time.time())}")
    
    # Validazione dei parametri
    nome_salvataggio = valida_input(nome_salvataggio, str, "nome_salvataggio", 200)
    
    # Verifica che la sessione esista
    if id_sessione not in sessioni_attive:
        return jsonify({
            "successo": False,
            "errore": "Sessione non trovata"
        }), 404
    
    try:
        # Ottieni il mondo dalla sessione
        world = sessioni_attive[id_sessione]
        
        # Assicuriamo che il file abbia estensione .json
        if not nome_salvataggio.endswith('.json'):
            nome_salvataggio = nome_salvataggio + '.json'
        
        # Salva su file usando pathlib
        save_path = Path(get_save_path(nome_salvataggio))
        
        # Assicurati che la directory esista
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Definisci il percorso temporaneo
        temp_save_path = save_path.with_suffix(save_path.suffix + ".tmp")
        
        # Crea un backup se il file esiste già
        if save_path.exists():
            backup_path = save_path.with_suffix(save_path.suffix + ".bak")
            try:
                import shutil
                shutil.copy2(str(save_path), str(backup_path))
                logger.info(f"Creato backup del salvataggio in {backup_path}")
            except Exception as e:
                logger.warning(f"Impossibile creare backup del salvataggio: {e}")
        
        # Aggiungi metadati
        metadata = {
            "nome": nome_salvataggio,
            "data": datetime.datetime.now().isoformat(),
            "versione": "2.0.0",
            "formato": "json"
        }
        
        # Salvataggio usando formato JSON
        save_success = False
        error_messages = []
        
        try:
            # Serializza il mondo con JSON
            world_data = world.serialize()
            
            # Aggiungi metadati
            save_data = {
                "metadata": metadata,
                "world": world_data
            }
            
            # Scrivi su file JSON
            json_str = json.dumps(save_data, indent=2, ensure_ascii=False)
            temp_save_path.write_text(json_str, encoding='utf-8')
            logger.info(f"File temporaneo JSON creato: {temp_save_path}")
            
            # Verifica che il file temporaneo sia stato creato correttamente
            if not temp_save_path.exists() or temp_save_path.stat().st_size == 0:
                error_messages.append("File temporaneo JSON creato ma non esiste o è vuoto")
                save_success = False
            else:
                save_success = True
                
        except Exception as e_json:
            error_messages.append(f"Errore nel salvataggio JSON: {str(e_json)}")
            logger.error(f"Errore nel salvataggio JSON: {str(e_json)}")
            save_success = False

        # Verifica che il file temporaneo sia stato creato correttamente
        if not save_success:
            logger.error(f"File temporaneo {temp_save_path} non è stato creato correttamente. Errori: {'; '.join(error_messages)}")
            return jsonify({
                "successo": False,
                "errore": f"Errore nella creazione del file temporaneo: {'; '.join(error_messages)}"
            }), 500
            
        # Rinomina atomicamente il file temporaneo
        try:
            # Controlla nuovamente che il file temporaneo esista prima di rinominarlo
            if not temp_save_path.exists():
                logger.error(f"File temporaneo {temp_save_path} non trovato per la rinomina finale")
                return jsonify({
                    "successo": False,
                    "errore": "Il file temporaneo è stato creato ma non è più presente"
                }), 500

            logger.info(f"Tentativo di rinomina del file temporaneo: {temp_save_path} -> {save_path}")
            
            if os.name == 'nt':  # Windows
                # Windows richiede di rimuovere il file di destinazione prima
                if save_path.exists():
                    save_path.unlink()
                    logger.info(f"File di destinazione esistente rimosso: {save_path}")
                os.rename(str(temp_save_path), str(save_path))
            else:  # Unix/Linux/Mac
                os.rename(str(temp_save_path), str(save_path))
                
            logger.info(f"Mondo salvato come '{nome_salvataggio}'")
            
            return jsonify({
                "successo": True,
                "nome_salvataggio": nome_salvataggio,
                "messaggio": "Mondo salvato con successo"
            })
        except Exception as e:
            logger.error(f"Errore durante la rinomina del file temporaneo: {e}")
            # Tentativo di copia diretta come fallback
            try:
                import shutil
                
                # Verifica che il file temporaneo esista ancora
                if not temp_save_path.exists():
                    logger.error(f"File temporaneo {temp_save_path} non trovato per il metodo fallback")
                    return jsonify({
                        "successo": False,
                        "errore": "File temporaneo non disponibile per il fallback"
                    }), 500
                
                # Usa copyfile che è più semplice di copy2 e ha meno requisiti
                logger.info(f"Tentativo di copia diretta come fallback: {temp_save_path} -> {save_path}")
                shutil.copyfile(str(temp_save_path), str(save_path))
                logger.info(f"Copia diretta del file riuscita come fallback")
                
                # Prova a eliminare il file temporaneo
                try:
                    temp_save_path.unlink()
                    logger.info(f"File temporaneo eliminato dopo copia di fallback")
                except Exception as del_err:
                    logger.warning(f"Impossibile eliminare file temporaneo dopo fallback: {del_err}")
                
                return jsonify({
                    "successo": True,
                    "nome_salvataggio": nome_salvataggio,
                    "messaggio": "Mondo salvato con successo (metodo fallback)"
                })
            except Exception as copy_error:
                logger.error(f"Anche la copia diretta è fallita: {copy_error}")
                import traceback
                logger.error(traceback.format_exc())
                return jsonify({
                    "successo": False,
                    "errore": f"Impossibile scrivere il file di salvataggio: {str(e)}, Fallback: {str(copy_error)}"
                }), 500
                
    except Exception as e:
        logger.error(f"Errore generale durante il salvataggio: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "successo": False,
            "errore": str(e)
        }), 500

@save_routes.route("/carica", methods=["POST"])
def carica_mondo_ecs():
    """Carica un mondo ECS da un file di salvataggio"""
    data = request.json or {}
    id_sessione = data.get("id_sessione")
    nome_salvataggio = data.get("nome_salvataggio")
    
    # Validazione dei parametri
    nome_salvataggio = valida_input(nome_salvataggio, str, "nome_salvataggio", 200, is_required=True)
    
    if nome_salvataggio is None:
        return jsonify({
            "successo": False,
            "errore": "Nome salvataggio non fornito"
        }), 400
    
    # Verifica che la sessione esista
    if id_sessione not in sessioni_attive:
        return jsonify({
            "successo": False,
            "errore": "Sessione non trovata"
        }), 404
    
    try:
        # Ottieni il percorso del file
        save_path = Path(get_save_path(nome_salvataggio))
        logger.info(f"Tentativo di caricamento del salvataggio: {nome_salvataggio}, percorso completo: {save_path}")
        
        # Verifica se è necessario provare diverse estensioni
        salvataggio_trovato = False
        if not save_path.exists():
            # Prova con estensione .json se non specificata
            if not nome_salvataggio.endswith('.json'):
                json_path = Path(get_save_path(nome_salvataggio + '.json'))
                
                if json_path.exists():
                    save_path = json_path
                    logger.info(f"Trovato file JSON: {save_path}")
                    salvataggio_trovato = True
            else:
                # Controlla semplicemente se esiste un file con il nome esatto fornito
                if save_path.exists():
                    salvataggio_trovato = True
                else:
                    logger.error(f"Salvataggio non trovato: {save_path}")
        else:
            salvataggio_trovato = True
            
        if not salvataggio_trovato:
            return jsonify({
                "successo": False,
                "errore": f"Salvataggio '{nome_salvataggio}' non trovato"
            }), 404
        
        # Carica i dati dal file
        logger.info(f"Caricamento salvataggio da file: {save_path}")
        try:
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
                logger.info(f"Formato file: JSON")
        except json.JSONDecodeError as e:
            logger.error(f"Errore nella decodifica JSON: {e}")
            return jsonify({
                "successo": False,
                "errore": f"Errore nella decodifica JSON: {str(e)}"
            }), 500
        
        # Verifica se è necessaria una migrazione
        if "giocatore" in save_data and "world" not in save_data:
            logger.info(f"Migrazione del salvataggio {nome_salvataggio} dal formato vecchio a 2.0.0")
            save_data = migra_formato_salvataggio(save_data)
            
            # Opzionalmente salva il file migrato per uso futuro
            migrated_path = save_path.with_name(f"{save_path.stem}_migrated.json")
            try:
                with open(migrated_path, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, indent=2, ensure_ascii=False)
                logger.info(f"Salvataggio migrato salvato in {migrated_path}")
            except Exception as write_err:
                logger.warning(f"Impossibile salvare il file migrato: {write_err}")
        else:
            # Applica sanificazione ai dati caricati prima della deserializzazione
            save_data = sanifica_salvataggio(save_data)
        
        # Estrai i dati del mondo
        world_data = save_data.get("world", {})
        if not world_data:
            logger.error("Dati 'world' mancanti o vuoti nel salvataggio")
            return jsonify({
                "successo": False,
                "errore": "Dati di mondo mancanti nel salvataggio"
            }), 400
            
        # Deserializza il mondo ECS
        try:
            world = World.deserialize(world_data)
            
            # AGGIUNTA: Inizializza il GestoreMappe se necessario
            if hasattr(world, 'gestore_mappe') and world.gestore_mappe:
                # Verifica se le mappe sono caricate
                if not world.gestore_mappe.mappe or len(world.gestore_mappe.mappe) == 0:
                    logger.info(f"GestoreMappe trovato ma senza mappe caricate, procedo con l'inizializzazione")
                    try:
                        world.gestore_mappe.inizializza_mappe(world)
                        logger.info(f"GestoreMappe reinizializzato con {len(world.gestore_mappe.mappe)} mappe")
                    except Exception as init_error:
                        logger.error(f"Errore nell'inizializzazione del GestoreMappe: {init_error}")
                else:
                    logger.info(f"GestoreMappe già inizializzato con {len(world.gestore_mappe.mappe)} mappe")
            else:
                # Se il GestoreMappe non esiste, crealo e inizializzalo
                logger.warning(f"GestoreMappe non trovato nel mondo deserializzato, ne creo uno nuovo")
                from world.gestore_mappe import GestitoreMappe
                world.gestore_mappe = GestitoreMappe()
                try:
                    world.gestore_mappe.inizializza_mappe(world)
                    logger.info(f"Nuovo GestoreMappe creato e inizializzato con {len(world.gestore_mappe.mappe)} mappe")
                except Exception as init_error:
                    logger.error(f"Errore nella creazione del nuovo GestoreMappe: {init_error}")
            
            # Verifica player e imposta stato FSM
            player_entities = world.find_entities_by_tag("player") if hasattr(world, "find_entities_by_tag") else []
            if not player_entities:
                logger.warning("Nessuna entità giocatore trovata nel mondo caricato. Verifica il salvataggio.")
            else:
                logger.info(f"Trovato giocatore: {player_entities[0].nome} (ID: {player_entities[0].id})")
            
            # Inizializza lo stato FSM del mondo
            player_entity = world.get_player_entity()
            if player_entity and hasattr(player_entity, 'mappa_corrente') and player_entity.mappa_corrente:
                nome_mappa_corrente = player_entity.mappa_corrente
                try:
                    from gioco_rpg.states.mappa import MappaState
                    map_state_instance = MappaState(nome_luogo=nome_mappa_corrente)
                    world.change_fsm_state(map_state_instance)
                    logger.info(f"FSM del mondo inizializzata a MappaState con la mappa: {nome_mappa_corrente}")
                except ModuleNotFoundError as e_mod:
                    logger.error(f"ERRORE MODULO durante l'importazione di MappaState: {e_mod}. Controlla sys.path e la struttura del progetto.")
                    import traceback
                    logger.error(traceback.format_exc())
                except Exception as e_fsm:
                    logger.error(f"ERRORE FSM durante l'inizializzazione di MappaState o il cambio FSM (post-import): {e_fsm}")
                    import traceback
                    logger.error(traceback.format_exc())
            elif player_entity and (not hasattr(player_entity, 'mappa_corrente') or not player_entity.mappa_corrente):
                logger.warning(f"Giocatore {player_entity.nome} (ID: {player_entity.id}) non ha una mappa_corrente definita. Stato FSM non inizializzato a MappaState.")
                # Potrebbe essere necessario un fallback a SceltaMappaState o uno stato di default
                # from gioco_rpg.states.scelta_mappa_state import SceltaMappaState
                # default_state = SceltaMappaState()
                # world.change_fsm_state(default_state)
                # logger.info("FSM del mondo inizializzata a SceltaMappaState come fallback.")
            else:
                logger.error("Nessuna entità giocatore trovata dopo la deserializzazione. Impossibile inizializzare lo stato FSM della mappa.")

        except Exception as deserialize_err:
            logger.error(f"Errore nella deserializzazione del mondo: {deserialize_err}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({
                "successo": False,
                "errore": f"Errore nella deserializzazione del mondo: {str(deserialize_err)}"
            }), 500
            
        # Se l'ID sessione non è fornito, generane uno nuovo
        if not id_sessione:
            id_sessione = str(uuid4())
        
        # Memorizza la sessione
        logger.info(f"Associazione del mondo caricato alla sessione {id_sessione}")
        sessioni_attive[id_sessione] = world
        
        # Salva la sessione
        try:
            success = salva_sessione(id_sessione, world)
            if not success:
                logger.warning(f"Impossibile salvare la sessione {id_sessione}")
        except Exception as e:
            logger.warning(f"Errore durante il salvataggio della sessione: {e}")
        
        # Comunica tramite EventBus che è stato effettuato un caricamento
        try:
            from core.event_bus import EventBus
            from core.events import EventType
            event_bus = EventBus.get_instance()
            
            # Ottieni il nome del giocatore se possibile
            player_name = player_entities[0].nome if player_entities else "Sconosciuto"
            
            # Emetti evento di caricamento completato
            event_bus.emit(EventType.GAME_LOADED, 
                          session_id=id_sessione,
                          save_name=nome_salvataggio,
                          player_name=player_name)
            
            logger.info(f"Evento GAME_LOADED emesso per la sessione {id_sessione}")
        except Exception as event_err:
            logger.warning(f"Impossibile emettere evento di caricamento: {event_err}")
        
        logger.info(f"Mondo '{nome_salvataggio}' caricato nella sessione {id_sessione}")
        
        return jsonify({
            "successo": True,
            "id_sessione": id_sessione,
            "nome_salvataggio": nome_salvataggio,
            "messaggio": "Mondo caricato con successo",
            "player_info": {
                "name": player_entities[0].nome if player_entities else None,
                "id": str(player_entities[0].id) if player_entities else None
            } if player_entities else {}
        })
    except Exception as e:
        logger.error(f"Errore generale durante il caricamento: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "successo": False,
            "errore": str(e)
        }), 500 