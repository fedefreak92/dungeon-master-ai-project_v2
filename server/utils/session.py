import os
import pickle
import logging
import time
from core.ecs.world import World
from uuid import uuid4
import json
from datetime import datetime
from pathlib import Path
from data.mappe import get_mappa

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
                # Rimuovo la chiamata a risolvi_problemi_sessione per evitare la ricorsione infinita
                # Implemento direttamente la logica di riparazione qui
                riparazione_diretta(world)
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
                # Rimuovo la chiamata a risolvi_problemi_sessione per evitare la ricorsione infinita
                # Implemento direttamente la logica di riparazione qui
                riparazione_diretta(world)
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
        
        # Ottieni percorsi come oggetti Path
        session_path = Path(get_session_path(id_sessione))
        msgpack_session_path = session_path.with_suffix('.msgpack')
        temp_session_path = session_path.with_suffix(session_path.suffix + ".tmp")
        temp_msgpack_session_path = msgpack_session_path.with_suffix(msgpack_session_path.suffix + ".tmp")
        
        # Crea la directory delle sessioni se non esiste
        session_dir = session_path.parent
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Salvataggio usando MessagePack (più veloce)
        try:
            # Serializza il mondo ECS con MessagePack
            world_data_msgpack = world.serialize_msgpack()
            
            # Scrivi i dati serializzati nel file temporaneo
            with open(temp_msgpack_session_path, 'wb') as f:
                f.write(world_data_msgpack)
            
            # Rinomina il file temporaneo per rendere l'operazione atomica
            if os.path.exists(msgpack_session_path):
                os.remove(msgpack_session_path)
            os.rename(temp_msgpack_session_path, msgpack_session_path)
            
            logger.info(f"Sessione {id_sessione} salvata con MessagePack in {msgpack_session_path}")
            return True
        except Exception as e:
            logger.error(f"Errore nel salvataggio MessagePack della sessione {id_sessione}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Fallback su JSON in caso di errore con MessagePack
            logger.warning(f"Tentativo di fallback su JSON per la sessione {id_sessione}")
            
        # Serializza il mondo ECS
        world_data = world.serialize()
        
        # Verifica se ci sono entità player nei dati serializzati
        if "entities" in world_data:
            player_ids = []
            for entity_id, entity_data in world_data["entities"].items():
                if "tags" in entity_data and "player" in entity_data["tags"]:
                    player_ids.append(entity_id)
            logger.info(f"Giocatori nei dati serializzati: {len(player_ids)}")
        
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
        
        # Scrivi i dati serializzati nel file temporaneo
        with open(temp_session_path, 'w') as f:
            json.dump(world_data, f)
        
        # Rinomina il file temporaneo per rendere l'operazione atomica
        if os.path.exists(session_path):
            os.remove(session_path)
        os.rename(temp_session_path, session_path)
        
        logger.info(f"Sessione {id_sessione} salvata con successo")
        return True
        
    except Exception as e:
        logger.error(f"Errore generale nel salvataggio della sessione {id_sessione}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def carica_sessione(id_sessione):
    """Carica lo stato del mondo ECS"""
    try:
        session_path = Path(get_session_path(id_sessione))
        msgpack_session_path = session_path.with_suffix('.msgpack')
        
        # Tenta prima di caricare da MessagePack (più veloce)
        if msgpack_session_path.exists():
            try:
                # Leggi il file MessagePack
                with open(msgpack_session_path, 'rb') as f:
                    data_bytes = f.read()
                
                # Deserializza il mondo ECS da MessagePack
                world = World.deserialize_msgpack(data_bytes)
                logger.info(f"Sessione {id_sessione} caricata da MessagePack con successo")
                return world
            except Exception as e:
                logger.error(f"Errore nel caricamento MessagePack della sessione {id_sessione}: {e}")
                logger.warning(f"Tentativo fallback su JSON per la sessione {id_sessione}")
                # Continua con il caricamento da JSON in caso di errore
        
        # Caricamento tradizionale da JSON
        if not session_path.exists():
            logger.warning(f"File di sessione {session_path} non trovato")
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

def riparazione_diretta(world):
    """
    Implementa direttamente la logica di riparazione per evitare la ricorsione
    
    Args:
        world: Il mondo ECS da riparare
    
    Returns:
        bool: True se la riparazione ha avuto successo, False altrimenti
    """
    giocatore_trovato = False
    
    # Cerca per nome
    for entity in world.entities.values():
        if entity.name.lower() in ["player", "giocatore"]:
            logger.info(f"Trovata potenziale entità giocatore dal nome: {entity.name} (ID: {entity.id})")
            entity.add_tag("player")
            # Aggiorna anche il dizionario entities_by_tag
            if "player" not in world.entities_by_tag:
                world.entities_by_tag["player"] = set()
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
                if "player" not in world.entities_by_tag:
                    world.entities_by_tag["player"] = set()
                world.entities_by_tag["player"].add(entity)
                giocatore_trovato = True
                break
    
    if giocatore_trovato:
        logger.info("Riparazione diretta completata: entità giocatore recuperata e tag aggiunto")
        return True
    else:
        logger.error("Riparazione diretta fallita: nessuna entità giocatore identificabile trovata")
        return False

def risolvi_problemi_sessione(id_sessione):
    """
    Analizza e risolve problemi comuni nelle sessioni, come l'entità giocatore mancante
    
    Args:
        id_sessione (str): ID della sessione da riparare
        
    Returns:
        bool: True se la riparazione ha avuto successo, False altrimenti
    """
    logger.info(f"Analisi e riparazione della sessione {id_sessione}")
    
    # Ottieni la sessione SENZA utilizzare get_session per evitare ricorsione
    world = sessioni_attive.get(id_sessione)
    if not world:
        world = carica_sessione(id_sessione)
        if world:
            sessioni_attive[id_sessione] = world
    
    if not world:
        logger.error(f"Impossibile trovare la sessione {id_sessione}")
        return False
    
    # Verifica se world contiene un giocatore
    player_entities = world.find_entities_by_tag("player") if hasattr(world, "find_entities_by_tag") else []
    logger.info(f"Analisi sessione {id_sessione}, giocatori trovati con tag: {len(player_entities)}")
    
    if not player_entities:
        logger.warning(f"Nessuna entità con tag 'player' trovata nella sessione {id_sessione}, avvio procedura di riparazione")
        
        # Utilizza la funzione di riparazione diretta
        giocatore_trovato = riparazione_diretta(world)
        
        # Se la riparazione automatica ha avuto successo
        if giocatore_trovato:
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
    logger.info(f"Nessuna riparazione necessaria per la sessione {id_sessione}")
    return True 

class SessionManager:
    """
    Manager centralizzato per le sessioni di gioco.
    Supporta le richieste asincrone con ID univoci.
    """
    def __init__(self):
        # Riferimento alle sessioni attive esistenti
        self._sessioni = sessioni_attive
    
    def get_session(self, id_sessione):
        """
        Ottiene una sessione di gioco identificata dall'ID.
        
        Args:
            id_sessione (str): ID della sessione
            
        Returns:
            SessionWrapper: Wrapper della sessione o None se non trovata
        """
        world = get_session(id_sessione)
        if world:
            return SessionWrapper(id_sessione, world)
        return None
    
    def create_session(self):
        """
        Crea una nuova sessione di gioco.
        
        Returns:
            SessionWrapper: Wrapper della nuova sessione
        """
        id_sessione = str(uuid4())
        world = World()
        sessioni_attive[id_sessione] = world
        return SessionWrapper(id_sessione, world)
    
    def delete_session(self, id_sessione):
        """
        Elimina una sessione di gioco.
        
        Args:
            id_sessione (str): ID della sessione da eliminare
            
        Returns:
            bool: True se l'eliminazione è riuscita, False altrimenti
        """
        if id_sessione in sessioni_attive:
            del sessioni_attive[id_sessione]
            try:
                # Elimina anche il file su disco
                session_path = Path(get_session_path(id_sessione))
                if session_path.exists():
                    session_path.unlink()
                return True
            except Exception as e:
                logger.error(f"Errore nell'eliminazione del file di sessione: {e}")
                return False
        return False
    
    def get_active_sessions(self):
        """
        Ottiene la lista delle sessioni attive.
        
        Returns:
            list: Lista degli ID delle sessioni attive
        """
        return list(sessioni_attive.keys())


class SessionWrapper:
    """
    Wrapper per una sessione di gioco che fornisce metodi di alto livello
    per interagire con il mondo ECS e supportare le richieste asincrone.
    """
    def __init__(self, id_sessione, world):
        self.id_sessione = id_sessione
        self.world = world
    
    def get_map_data(self, map_id=None):
        """
        Ottiene i dati di una mappa.
        
        Args:
            map_id (str, optional): ID della mappa. Se None, restituisce la mappa corrente.
            
        Returns:
            dict: Dati della mappa
        """
        try:
            # Se map_id è None, cerca la mappa corrente
            if map_id is None:
                # Cerca nel FSM lo stato corrente
                if hasattr(self.world, "fsm") and self.world.fsm:
                    current_state = self.world.fsm.current_state
                    if hasattr(current_state, "map_id"):
                        map_id = current_state.map_id
                
                # Se ancora non abbiamo un ID, prova a cercarlo nel giocatore
                if not map_id:
                    player_entities = self.world.find_entities_by_tag("player")
                    if player_entities and hasattr(player_entities[0], "current_map"):
                        map_id = player_entities[0].current_map
            
            # Se ancora non abbiamo trovato un ID, usa la mappa di default
            if not map_id:
                map_id = "taverna"  # Mappa predefinita
            
            # Carica i dati della mappa (adatta questo alla tua implementazione)
            if hasattr(self.world, "get_map_data"):
                # Usa il metodo del mondo se esiste
                return self.world.get_map_data(map_id)
            else:
                # Implementazione di fallback
                map_data = get_mappa(map_id)
                
                # Aggiungi le entità presenti sulla mappa
                if map_data:
                    map_data["entities"] = self._get_entities_for_map(map_id)
                
                return map_data
                
        except Exception as e:
            logger.error(f"Errore nell'ottenimento dei dati della mappa {map_id}: {e}")
            return {
                "error": True,
                "message": f"Errore nel caricamento della mappa: {str(e)}"
            }
    
    def get_game_state(self):
        """
        Ottiene lo stato completo del gioco.
        
        Returns:
            dict: Stato del gioco
        """
        try:
            # Ottieni il giocatore
            player_entities = self.world.find_entities_by_tag("player")
            if not player_entities:
                raise ValueError("Nessuna entità giocatore trovata nella sessione")
            
            player = player_entities[0]
            
            # Costruisci lo stato di gioco
            game_state = {
                "sessionId": self.id_sessione,
                "player": {
                    "id": str(player.id),
                    "name": player.name if hasattr(player, "name") else "Giocatore",
                    "level": player.level if hasattr(player, "level") else 1,
                    "hp": player.hp if hasattr(player, "hp") else 100,
                    "max_hp": player.max_hp if hasattr(player, "max_hp") else 100,
                    "exp": player.exp if hasattr(player, "exp") else 0
                },
                "currentMap": player.current_map if hasattr(player, "current_map") else None,
                "player_position": {
                    "x": player.x if hasattr(player, "x") else 0,
                    "y": player.y if hasattr(player, "y") else 0
                },
                "inventory": self._get_player_inventory(player),
                "quests": self._get_player_quests(player),
                "stats": self._get_player_stats(player),
                "entities": self._get_visible_entities(player)
            }
            
            # Aggiungi info sullo stato corrente FSM
            if hasattr(self.world, "fsm") and self.world.fsm:
                current_state = self.world.fsm.current_state
                game_state["fsm"] = {
                    "current_state": current_state.__class__.__name__ if current_state else None,
                    "previous_state": self.world.fsm.previous_state.__class__.__name__ if self.world.fsm.previous_state else None,
                    "state_stack": [s.__class__.__name__ for s in self.world.fsm.state_stack] if self.world.fsm.state_stack else []
                }
            
            return game_state
            
        except Exception as e:
            logger.error(f"Errore nell'ottenimento dello stato di gioco: {e}")
            return {
                "error": True,
                "message": f"Errore nell'ottenimento dello stato di gioco: {str(e)}"
            }
    
    def get_entities(self, map_id=None):
        """
        Ottiene le entità presenti nella sessione, opzionalmente filtrate per mappa.
        
        Args:
            map_id (str, optional): ID della mappa. Se None, restituisce tutte le entità.
            
        Returns:
            dict: Dizionario delle entità
        """
        try:
            if map_id:
                return self._get_entities_for_map(map_id)
            else:
                return self._get_all_entities()
        except Exception as e:
            logger.error(f"Errore nell'ottenimento delle entità: {e}")
            return {
                "error": True,
                "message": f"Errore nell'ottenimento delle entità: {str(e)}"
            }
    
    def _get_entities_for_map(self, map_id):
        """
        Ottiene le entità presenti su una specifica mappa.
        
        Args:
            map_id (str): ID della mappa
            
        Returns:
            dict: Dizionario delle entità sulla mappa
        """
        entities = {}
        
        # Cerca tutte le entità con il componente position e map_id corrispondente
        for entity_id, entity in self.world.entities.items():
            # Verifica se l'entità ha un componente di posizione e mappa
            if (hasattr(entity, "current_map") and entity.current_map == map_id) or \
               (hasattr(entity, "map_id") and entity.map_id == map_id):
                # Serializza l'entità
                entity_data = self._serialize_entity(entity)
                entities[str(entity_id)] = entity_data
        
        return entities
    
    def _get_all_entities(self):
        """
        Ottiene tutte le entità presenti nella sessione.
        
        Returns:
            dict: Dizionario di tutte le entità
        """
        entities = {}
        
        for entity_id, entity in self.world.entities.items():
            # Serializza l'entità
            entity_data = self._serialize_entity(entity)
            entities[str(entity_id)] = entity_data
        
        return entities
    
    def _get_visible_entities(self, player):
        """
        Ottiene le entità visibili al giocatore (sulla stessa mappa).
        
        Args:
            player: Entità giocatore
            
        Returns:
            dict: Dizionario delle entità visibili
        """
        if not hasattr(player, "current_map"):
            return {}
        
        return self._get_entities_for_map(player.current_map)
    
    def _serialize_entity(self, entity):
        """
        Serializza un'entità nel formato appropriato per il client.
        
        Args:
            entity: Entità da serializzare
            
        Returns:
            dict: Dati serializzati dell'entità
        """
        # Implementazione base, da estendere in base alle tue esigenze
        entity_data = {
            "id": str(entity.id),
            "type": getattr(entity, "type", "generic"),
            "tags": list(entity.tags) if hasattr(entity, "tags") else []
        }
        
        # Aggiungi posizione se disponibile
        if hasattr(entity, "x") and hasattr(entity, "y"):
            entity_data["position"] = {
                "x": entity.x,
                "y": entity.y
            }
        
        # Aggiungi nome se disponibile
        if hasattr(entity, "name"):
            entity_data["name"] = entity.name
        
        # Aggiungi sprite se disponibile
        if hasattr(entity, "sprite"):
            entity_data["sprite"] = entity.sprite
        
        # Aggiungi stato interattivo se disponibile
        if hasattr(entity, "interactive") and entity.interactive:
            entity_data["interactive"] = True
        
        return entity_data
    
    def _get_player_inventory(self, player):
        """
        Ottiene l'inventario del giocatore.
        
        Args:
            player: Entità giocatore
            
        Returns:
            list: Lista degli oggetti nell'inventario
        """
        if not hasattr(player, "inventory"):
            return []
        
        inventory = []
        for item in player.inventory:
            item_data = {
                "id": str(item.id) if hasattr(item, "id") else None,
                "name": item.name if hasattr(item, "name") else "Oggetto",
                "quantity": item.quantity if hasattr(item, "quantity") else 1,
                "type": item.type if hasattr(item, "type") else "generic",
                "icon": item.icon if hasattr(item, "icon") else None
            }
            inventory.append(item_data)
        
        return inventory
    
    def _get_player_quests(self, player):
        """
        Ottiene le missioni del giocatore.
        
        Args:
            player: Entità giocatore
            
        Returns:
            list: Lista delle missioni
        """
        if not hasattr(player, "quests"):
            return []
        
        quests = []
        for quest in player.quests:
            quest_data = {
                "id": str(quest.id) if hasattr(quest, "id") else None,
                "title": quest.title if hasattr(quest, "title") else "Missione",
                "description": quest.description if hasattr(quest, "description") else "",
                "completed": quest.completed if hasattr(quest, "completed") else False,
                "progress": quest.progress if hasattr(quest, "progress") else 0
            }
            quests.append(quest_data)
        
        return quests
    
    def _get_player_stats(self, player):
        """
        Ottiene le statistiche del giocatore.
        
        Args:
            player: Entità giocatore
            
        Returns:
            dict: Statistiche del giocatore
        """
        stats = {
            "strength": getattr(player, "strength", 0),
            "dexterity": getattr(player, "dexterity", 0),
            "intelligence": getattr(player, "intelligence", 0),
            "constitution": getattr(player, "constitution", 0),
            "luck": getattr(player, "luck", 0)
        }
        
        return stats


# Singleton per il SessionManager
_session_manager_instance = None

def get_session_manager():
    """
    Ottiene l'istanza singleton del SessionManager.
    
    Returns:
        SessionManager: Istanza del manager
    """
    global _session_manager_instance
    if _session_manager_instance is None:
        _session_manager_instance = SessionManager()
    return _session_manager_instance 