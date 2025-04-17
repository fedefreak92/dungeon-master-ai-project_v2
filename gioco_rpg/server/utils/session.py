import os
import pickle
import logging
import time
from core.ecs.world import World
from uuid import uuid4
import json
from datetime import datetime
from pathlib import Path

# Configura il logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dizionario delle sessioni attive: id_sessione -> world
sessioni_attive = {}

# Mappatura socket_id -> id_sessione per le connessioni WebSocket
socket_sessioni = {}

# Riferimento al SocketIO (sarà impostato dall'app)
socketio = None

def set_socketio(socket_io):
    """Imposta il riferimento all'istanza SocketIO"""
    global socketio
    socketio = socket_io

def get_session_path(id_sessione):
    """Restituisce il percorso completo per un file di sessione"""
    from util.config import SESSIONS_DIR
    return os.path.join(SESSIONS_DIR, f"{id_sessione}.session")

def get_session(id_sessione):
    """
    Ottiene una sessione di gioco attiva o la carica da disco se non è in memoria
    
    Args:
        id_sessione (str): ID della sessione da ottenere
        
    Returns:
        World: Mondo ECS della sessione richiesta o None se non trovata
    """
    logger.info(f"Richiesta sessione con ID: {id_sessione}")
    
    # Controlla se la sessione è già in memoria
    if id_sessione in sessioni_attive:
        logger.info(f"Sessione {id_sessione} trovata in memoria")
        world = sessioni_attive[id_sessione]
        # Verifica integrità della sessione
        if hasattr(world, "entities"):
            logger.info(f"Sessione {id_sessione} valida, contiene {len(world.entities)} entità")
            # Verifica entità giocatore
            player_entities = world.find_entities_by_tag("player") if hasattr(world, "find_entities_by_tag") else []
            logger.info(f"Entità con tag 'player' nella sessione: {len(player_entities)}")
            
            # Tentativo di riparazione automatica se non ci sono giocatori
            if len(player_entities) == 0:
                logger.warning(f"Sessione {id_sessione} senza entità giocatore, tentativo di riparazione automatica")
                risolvi_problemi_sessione(id_sessione)
                # Verifica di nuovo
                player_entities = world.find_entities_by_tag("player") if hasattr(world, "find_entities_by_tag") else []
                logger.info(f"Entità con tag 'player' dopo riparazione: {len(player_entities)}")
                
        return world
    
    logger.info(f"Sessione {id_sessione} non trovata in memoria, tentativo di caricamento da disco")
    
    # Altrimenti prova a caricarla dal disco
    world = carica_sessione(id_sessione)
    
    # Se è stata caricata con successo, memorizzala nel dizionario delle sessioni attive
    if world:
        logger.info(f"Sessione {id_sessione} caricata con successo da disco")
        sessioni_attive[id_sessione] = world
        # Verifica integrità della sessione caricata
        if hasattr(world, "entities"):
            logger.info(f"Sessione caricata valida, contiene {len(world.entities)} entità")
            # Verifica entità giocatore
            player_entities = world.find_entities_by_tag("player") if hasattr(world, "find_entities_by_tag") else []
            logger.info(f"Entità con tag 'player' nella sessione caricata: {len(player_entities)}")
            
            # Tentativo di riparazione automatica se non ci sono giocatori
            if len(player_entities) == 0:
                logger.warning(f"Sessione caricata {id_sessione} senza entità giocatore, tentativo di riparazione automatica")
                risolvi_problemi_sessione(id_sessione)
                # Verifica di nuovo
                player_entities = world.find_entities_by_tag("player") if hasattr(world, "find_entities_by_tag") else []
                logger.info(f"Entità con tag 'player' dopo riparazione: {len(player_entities)}")
    else:
        logger.warning(f"Impossibile caricare la sessione {id_sessione} da disco")
    
    return world

def salva_sessione(id_sessione, world):
    """Salva lo stato del mondo ECS"""
    try:
        # Verifica se world contiene un giocatore
        player_entities = world.find_entities_by_tag("player") if hasattr(world, "find_entities_by_tag") else []
        logger.info(f"Salvataggio sessione {id_sessione}, giocatori presenti: {len(player_entities)}")
        if player_entities:
            logger.info(f"Giocatore presente con ID: {player_entities[0].id}, nome: {player_entities[0].name}")
        
        # Serializza il mondo ECS
        world_data = world.serialize()
        
        # Verifica se ci sono entità player nei dati serializzati
        if "entities" in world_data:
            player_ids = []
            for entity_id, entity_data in world_data["entities"].items():
                if "tags" in entity_data and "player" in entity_data["tags"]:
                    player_ids.append(entity_id)
            logger.info(f"Giocatori nei dati serializzati: {len(player_ids)}")
        
        # Ottieni percorsi come oggetti Path
        session_path = Path(get_session_path(id_sessione))
        temp_session_path = session_path.with_suffix(session_path.suffix + ".tmp")
        
        # Crea la directory delle sessioni se non esiste
        session_dir = session_path.parent
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Verifica che il dizionario sia JSON-serializzabile
        try:
            # Test per la compatibilità JSON
            json.dumps(world_data)
        except (TypeError, OverflowError, ValueError) as je:
            logger.error(f"I dati non sono JSON-compatibili: {je}")
            # Tenta di rendere i dati compatibili con JSON
            world_data = {
                "entities": {},  # Dati minimi
                "events": [],
                "pending_events": [],
                "temporary_states": {}
            }
        
        # Salva come JSON (più robusto di pickle)
        try:
            # Approccio diretto con Path
            temp_session_path.write_text(json.dumps(world_data, indent=2, ensure_ascii=False), encoding='utf-8')
        except Exception as write_error:
            # Fallback all'approccio tradizionale
            logger.warning(f"Errore con approccio Path: {write_error}, utilizzo metodo tradizionale")
            with open(str(temp_session_path), 'w', encoding='utf-8') as f:
                json.dump(world_data, f, indent=2, ensure_ascii=False)
                f.flush()  # Assicura che i dati vengano scritti sul disco
        
        logger.info(f"Dati serializzati salvati in {temp_session_path}")
        
        # Verifica che il file temporaneo esista
        if not temp_session_path.exists():
            logger.error(f"File temporaneo {temp_session_path} non esiste dopo il salvataggio")
            # Tenta un approccio alternativo
            try:
                with open(str(temp_session_path), 'w', encoding='utf-8') as f:
                    json.dump(world_data, f, indent=2, ensure_ascii=False)
                    f.flush()
                logger.info(f"Secondo tentativo di salvataggio completato")
            except Exception as e2:
                logger.error(f"Anche il secondo tentativo di salvataggio è fallito: {e2}")
                return False
            
            # Verifica di nuovo
            if not os.path.exists(str(temp_session_path)):
                logger.error(f"Impossibile creare il file temporaneo anche al secondo tentativo")
                return False
        
        # Se il file principale esiste, creane un backup
        if session_path.exists():
            backup_path = session_path.with_suffix(session_path.suffix + ".bak")
            try:
                import shutil
                shutil.copy2(str(session_path), str(backup_path))
            except Exception as e:
                logger.warning(f"Impossibile creare backup della sessione {id_sessione}: {e}")
        
        # Rinomina il file temporaneo nel file principale (operazione atomica)
        try:
            if os.name == 'nt':  # Windows
                # Windows richiede di rimuovere il file di destinazione prima
                if session_path.exists():
                    session_path.unlink()
                os.rename(str(temp_session_path), str(session_path))
            else:  # Unix/Linux/Mac
                os.rename(str(temp_session_path), str(session_path))
            
            logger.info(f"Sessione {id_sessione} salvata con successo")
            return True
        except Exception as rename_error:
            logger.error(f"Errore nella rinomina del file temporaneo: {rename_error}")
            # Tentativo di copia diretta se la rinomina fallisce
            try:
                import shutil
                shutil.copy2(str(temp_session_path), str(session_path))
                logger.info(f"Copia diretta del file riuscita come fallback")
                return True
            except Exception as copy_error:
                logger.error(f"Anche la copia diretta è fallita: {copy_error}")
                return False
    except Exception as e:
        logger.error(f"Errore nel salvataggio della sessione {id_sessione}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def carica_sessione(id_sessione):
    """Carica lo stato del mondo ECS"""
    try:
        session_path = get_session_path(id_sessione)
        if not os.path.exists(session_path):
            # Verifica se esiste un backup
            backup_path = f"{session_path}.bak"
            if os.path.exists(backup_path):
                logger.warning(f"Sessione {id_sessione} non trovata, uso il backup")
                session_path = backup_path
            else:
                logger.warning(f"Sessione {id_sessione} non trovata")
                return None
        
        # Prova prima con JSON (nuovo formato preferito)
        try:
            with open(session_path, 'r', encoding='utf-8') as f:
                try:
                    world_data = json.load(f)
                    logger.info(f"Sessione {id_sessione} caricata in formato JSON")
                except json.JSONDecodeError:
                    # Se il file non è JSON valido, potrebbe essere in formato pickle
                    logger.warning(f"File della sessione {id_sessione} non è in formato JSON valido")
                    raise ValueError("Non è un file JSON valido")
        except (ValueError, UnicodeDecodeError):
            # Fallback a pickle per la retrocompatibilità
            try:
                with open(session_path, 'rb') as f:
                    try:
                        world_data = pickle.load(f)
                        logger.info(f"Sessione {id_sessione} caricata in formato pickle")
                    except Exception as e:
                        logger.error(f"Errore nella deserializzazione pickle della sessione {id_sessione}: {e}")
                        
                        # Prova a caricare il backup se esiste
                        backup_path = f"{session_path}.bak"
                        if os.path.exists(backup_path) and backup_path != session_path:
                            logger.warning(f"Tentativo di caricamento dal backup per la sessione {id_sessione}")
                            with open(backup_path, 'rb') as bf:
                                try:
                                    world_data = pickle.load(bf)
                                    logger.info(f"Backup della sessione {id_sessione} caricato correttamente")
                                except Exception as be:
                                    logger.error(f"Anche il backup è corrotto per la sessione {id_sessione}: {be}")
                                    return None
                        else:
                            return None
            except FileNotFoundError:
                logger.error(f"File della sessione {id_sessione} non trovato")
                return None
        except Exception as e:
            logger.error(f"Errore nell'apertura del file di sessione {id_sessione}: {e}")
            return None
        
        # Verifica che i dati siano validi
        if not isinstance(world_data, dict):
            logger.error(f"Formato della sessione {id_sessione} non valido: {type(world_data)}")
            return None
        
        # Deserializza il mondo ECS
        try:
            world = World.deserialize(world_data)
            logger.info(f"Sessione {id_sessione} deserializzata con successo")
            return world
        except Exception as e:
            logger.error(f"Errore nella deserializzazione del mondo della sessione {id_sessione}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    except Exception as e:
        logger.error(f"Errore generale nel caricamento della sessione {id_sessione}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def aggiungi_notifica(id_sessione, tipo, messaggio, data=None):
    """Aggiunge una notifica alla sessione"""
    if id_sessione not in sessioni_attive:
        logger.warning(f"Impossibile aggiungere notifica: sessione {id_sessione} non trovata")
        return False
    
    world = sessioni_attive[id_sessione]
    
    # Crea un evento nel mondo ECS
    notifica = {
        "id": str(uuid4()),
        "tipo": tipo,
        "messaggio": messaggio,
        "data": data or {},
        "timestamp": time.time(),
        "letta": False
    }
    
    # Aggiungi l'evento al mondo
    world.add_event({
        "type": "notification",
        "data": notifica
    })
    
    # Emetti un evento WebSocket per la notifica se socketio è disponibile
    if socketio:
        room = f"session_{id_sessione}"
        socketio.emit('new_notification', notifica, room=room)
    
    return True

def transizione_stato(id_sessione, stato_origine, stato_destinazione, parametri=None):
    """
    Gestisce la transizione da uno stato all'altro
    
    Args:
        id_sessione (str): ID della sessione
        stato_origine (str): Stato corrente
        stato_destinazione (str): Stato di destinazione
        parametri (dict, optional): Parametri per lo stato di destinazione
    
    Returns:
        bool: True se la transizione è riuscita, False altrimenti
    """
    try:
        # Ottieni la sessione
        sessione = get_session(id_sessione)
        if not sessione:
            return False
        
        # Verifica che lo stato corrente sia quello di origine
        stato_corrente = sessione.stato_corrente
        if stato_corrente.nome_stato != stato_origine:
            logger.warning(f"Transizione fallita: stato corrente {stato_corrente.nome_stato} non corrisponde a stato origine {stato_origine}")
            return False
        
        # Esegui la transizione
        sessione.change_state(stato_destinazione, parametri or {})
        
        # Salva la sessione aggiornata
        salva_sessione(id_sessione, sessione)
        
        return True
    except Exception as e:
        logger.error(f"Errore nella transizione da {stato_origine} a {stato_destinazione}: {e}")
        return False 

# Aggiungi funzione di validazione degli input
def valida_input(valore, tipo_atteso, nome_campo=None, lunghezza_max=None, valore_default=None, is_required=False):
    """
    Valida e normalizza un input in base al tipo atteso e ad altri vincoli.
    
    Args:
        valore: Il valore da validare
        tipo_atteso: Il tipo atteso (str, int, list, dict, ecc.)
        nome_campo: Nome del campo per i log (opzionale)
        lunghezza_max: Lunghezza massima per stringhe e liste (opzionale)
        valore_default: Valore di default se la conversione fallisce (opzionale)
        is_required: Se True, restituisce None se il valore è None
        
    Returns:
        Il valore convertito nel tipo corretto o None se non valido e is_required=False
    """
    campo_log = f" per il campo '{nome_campo}'" if nome_campo else ""
    
    # Gestione valore None
    if valore is None:
        if is_required:
            logger.warning(f"Valore richiesto{campo_log} non fornito")
        return valore_default
    
    # Conversione di tipo
    try:
        # Per le stringhe
        if tipo_atteso == str:
            if not isinstance(valore, str):
                valore_orig = valore
                valore = str(valore)
                logger.warning(f"Convertito valore{campo_log} da {type(valore_orig).__name__} a stringa: {valore}")
        
        # Per gli interi
        elif tipo_atteso == int:
            if not isinstance(valore, int):
                valore_orig = valore
                valore = int(valore)
                logger.warning(f"Convertito valore{campo_log} da {type(valore_orig).__name__} a intero: {valore}")
        
        # Per le liste
        elif tipo_atteso == list:
            if not isinstance(valore, list):
                if isinstance(valore, (str, tuple, set)):
                    valore_orig = valore
                    valore = list(valore)
                    logger.warning(f"Convertito valore{campo_log} da {type(valore_orig).__name__} a lista: {valore}")
                else:
                    valore = [valore]
                    logger.warning(f"Incapsulato valore{campo_log} in una lista: {valore}")
        
        # Per i dizionari
        elif tipo_atteso == dict:
            if not isinstance(valore, dict):
                logger.warning(f"Impossibile convertire valore{campo_log} in dizionario, uso default")
                return valore_default if valore_default is not None else {}
    
    except (ValueError, TypeError) as e:
        logger.warning(f"Errore di conversione{campo_log}: {str(e)}")
        return valore_default
    
    # Controllo lunghezza
    if lunghezza_max is not None:
        if isinstance(valore, (str, list, tuple, dict)) and len(valore) > lunghezza_max:
            valore_orig = valore
            if isinstance(valore, str):
                valore = valore[:lunghezza_max]
                logger.warning(f"Troncata stringa{campo_log} da {len(valore_orig)} a {len(valore)} caratteri")
            elif isinstance(valore, (list, tuple)):
                valore = valore[:lunghezza_max]
                logger.warning(f"Troncata lista/tupla{campo_log} da {len(valore_orig)} a {len(valore)} elementi")
            elif isinstance(valore, dict) and len(valore) > lunghezza_max:
                # Prendi solo le prime N chiavi
                chiavi = list(valore.keys())[:lunghezza_max]
                valore = {k: valore[k] for k in chiavi}
                logger.warning(f"Troncato dizionario{campo_log} da {len(valore_orig)} a {len(valore)} elementi")
    
    return valore 

def risolvi_problemi_sessione(id_sessione):
    """
    Analizza e risolve problemi comuni nelle sessioni, come l'entità giocatore mancante
    
    Args:
        id_sessione (str): ID della sessione da riparare
        
    Returns:
        bool: True se la riparazione ha avuto successo, False altrimenti
    """
    logger.info(f"Analisi e riparazione della sessione {id_sessione}")
    
    # Ottieni la sessione
    world = get_session(id_sessione)
    if not world:
        logger.error(f"Impossibile trovare la sessione {id_sessione}")
        return False
    
    riparazione_necessaria = False
    
    # Verifica se world contiene un giocatore
    player_entities = world.find_entities_by_tag("player") if hasattr(world, "find_entities_by_tag") else []
    logger.info(f"Analisi sessione {id_sessione}, giocatori trovati con tag: {len(player_entities)}")
    
    if not player_entities:
        logger.warning(f"Nessuna entità con tag 'player' trovata nella sessione {id_sessione}, avvio procedura di riparazione")
        riparazione_necessaria = True
        
        # Cerca entità che potrebbero essere il giocatore ma senza tag
        giocatore_trovato = False
        
        # Cerca per nome
        for entity in world.entities.values():
            if entity.name.lower() in ["player", "giocatore"]:
                logger.info(f"Trovata potenziale entità giocatore dal nome: {entity.name} (ID: {entity.id})")
                entity.add_tag("player")
                # Aggiorna anche il dizionario entities_by_tag
                world.entities_by_tag["player"].add(entity)
                giocatore_trovato = True
                break
        
        # Cerca per attributi se non ancora trovato
        if not giocatore_trovato:
            for entity in world.entities.values():
                # Controlla se ha attributi tipici del giocatore
                if (hasattr(entity, "livello") or 
                    hasattr(entity, "classe") or 
                    hasattr(entity, "hp") or 
                    hasattr(entity, "mappa_corrente")):
                    logger.info(f"Trovata potenziale entità giocatore dagli attributi: {entity.name} (ID: {entity.id})")
                    entity.add_tag("player")
                    # Aggiorna anche il dizionario entities_by_tag
                    world.entities_by_tag["player"].add(entity)
                    giocatore_trovato = True
                    break
        
        # Se la riparazione automatica ha avuto successo
        if giocatore_trovato:
            logger.info("Riparazione automatica completata: entità giocatore recuperata e tag aggiunto")
            
            # Verifica il risultato della riparazione
            player_entities_after = world.find_entities_by_tag("player")
            logger.info(f"Entità con tag 'player' dopo la riparazione: {len(player_entities_after)}")
            
            # Salva la sessione riparata
            if salva_sessione(id_sessione, world):
                logger.info(f"Sessione {id_sessione} riparata e salvata con successo")
                return True
            else:
                logger.error(f"Impossibile salvare la sessione {id_sessione} dopo la riparazione")
                return False
        else:
            logger.error("Riparazione automatica fallita: nessuna entità giocatore identificabile trovata")
            return False
    
    # Se non era necessaria alcuna riparazione
    if not riparazione_necessaria:
        logger.info(f"Nessuna riparazione necessaria per la sessione {id_sessione}")
        return True
        
    return False 