from flask import request, jsonify, Blueprint
import datetime
import os
import pickle
import time
import logging
from uuid import uuid4
import json
import msgpack
from pathlib import Path

from util.config import SAVE_DIR, get_save_path, list_save_files, delete_save_file, normalize_save_data, USE_MSGPACK
from server.utils.session import sessioni_attive, salva_sessione, valida_input
from core.ecs.world import World

# Configura il logger
logger = logging.getLogger(__name__)

# Crea il blueprint per le route di salvataggio
save_routes = Blueprint('save_routes', __name__)

# Versione corrente del formato di salvataggio
SAVE_FORMAT_VERSION = "2.0.0"

def sanifica_salvataggio(save_data):
    """
    Sanifica i dati di salvataggio per evitare problemi con attributi mancanti o non previsti.
    Questo è un livello di protezione aggiuntivo al sistema di migrazione degli stati specifici.
    
    Args:
        save_data (dict): Dati del salvataggio deserializzati
        
    Returns:
        dict: Dati del salvataggio sanificati
    """
    try:
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
                is_msgpack_format = str(save_path).endswith('.msgpack')
                
                # Leggi il file in base al formato
                if is_json_format:
                    try:
                        with open(save_path, 'r', encoding='utf-8') as f:
                            save_data = json.load(f)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # Fallback a pickle se il file non è JSON valido
                        with open(save_path, 'rb') as f:
                            save_data = pickle.load(f)
                elif is_msgpack_format:
                    try:
                        with open(save_path, 'rb') as f:
                            save_data = msgpack.unpack(f, raw=False)
                    except Exception as msgpack_error:
                        logger.warning(f"Errore nella lettura MessagePack del salvataggio {nome_salvataggio}: {msgpack_error}")
                        with open(save_path, 'rb') as f:
                            save_data = pickle.load(f)
                else:
                    with open(save_path, 'rb') as f:
                        save_data = pickle.load(f)
                
                # Rimuovi l'estensione dal nome del salvataggio
                nome_senza_estensione = nome_salvataggio
                for ext in ['.json', '.msgpack', '.dat', '.pickle']:
                    nome_senza_estensione = nome_senza_estensione.replace(ext, '')
                
                metadata = save_data.get("metadata", {})
                risultati.append({
                    "nome": nome_senza_estensione,
                    "data": metadata.get("data", ""),
                    "versione": metadata.get("versione", ""),
                    "formato": "msgpack" if is_msgpack_format else "json" if is_json_format else "pickle"
                })
            except Exception as e:
                logger.warning(f"Errore nella lettura del salvataggio {nome_salvataggio}: {e}")
                # Se c'è un errore nel leggere un salvataggio, includi solo il nome
                # Rimuovi l'estensione dal nome del salvataggio
                nome_senza_estensione = nome_salvataggio
                for ext in ['.json', '.msgpack', '.dat', '.pickle']:
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
    use_msgpack = data.get("use_msgpack", USE_MSGPACK)  # Usa la configurazione predefinita se non specificato
    
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
        
        # Aggiungiamo l'estensione corretta se non presente
        if use_msgpack and not nome_salvataggio.endswith('.msgpack'):
            if nome_salvataggio.endswith('.json'):
                nome_salvataggio = nome_salvataggio[:-5] + '.msgpack'
            else:
                nome_salvataggio = nome_salvataggio + '.msgpack'
        elif not use_msgpack and not nome_salvataggio.endswith('.json'):
            if nome_salvataggio.endswith('.msgpack'):
                nome_salvataggio = nome_salvataggio[:-8] + '.json'
            else:
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
            "formato": "msgpack" if use_msgpack else "json"
        }
        
        # Salvataggio usando diversi metodi in caso di errore
        save_success = False
        error_messages = []
        
        if use_msgpack:
            try:
                # Serializza il mondo con MessagePack
                world_data_msgpack = world.serialize_msgpack()
                
                # Preparazione dati con metadati
                save_data_msgpack = {
                    "metadata": metadata,
                    "world": msgpack.unpackb(world_data_msgpack, raw=False)
                }
                
                # Scrittura su file
                with open(temp_save_path, 'wb') as f:
                    msgpack.pack(save_data_msgpack, f, use_bin_type=True)
                
                logger.info(f"File temporaneo MessagePack creato: {temp_save_path}")
                
                if temp_save_path.exists() and temp_save_path.stat().st_size > 0:
                    # Rinomina il file temporaneo per rendere l'operazione atomica
                    if save_path.exists():
                        save_path.unlink()
                    temp_save_path.rename(save_path)
                    save_success = True
                    logger.info(f"Salvataggio MessagePack completato: {save_path}")
                else:
                    error_messages.append("File temporaneo MessagePack creato ma non esiste o è vuoto")
            except Exception as e_msgpack:
                error_messages.append(f"Errore nel salvataggio MessagePack: {str(e_msgpack)}")
                logger.warning(f"Errore nel salvataggio MessagePack: {str(e_msgpack)}")
                # Fallback su JSON
                use_msgpack = False
        
        if not use_msgpack:
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
                temp_save_path = Path(get_save_path(nome_salvataggio.replace('.msgpack', '.json')))
                temp_save_path = temp_save_path.with_suffix(temp_save_path.suffix + ".tmp")
                
                temp_save_path.write_text(json_str, encoding='utf-8')
                logger.info(f"File temporaneo JSON creato: {temp_save_path}")
                
                if temp_save_path.exists() and temp_save_path.stat().st_size > 0:
                    # Rinomina il file temporaneo per rendere l'operazione atomica
                    save_path = Path(get_save_path(nome_salvataggio.replace('.msgpack', '.json')))
                    if save_path.exists():
                        save_path.unlink()
                    temp_save_path.rename(save_path)
                    save_success = True
                    logger.info(f"Salvataggio JSON completato: {save_path}")
                else:
                    error_messages.append("File temporaneo JSON creato ma non esiste o è vuoto")
            except Exception as e_json:
                error_messages.append(f"Errore nel salvataggio JSON: {str(e_json)}")
                logger.error(f"Errore nel salvataggio JSON: {str(e_json)}")

        # Verifica che il file temporaneo sia stato creato correttamente
        if not save_success:
            logger.error(f"File temporaneo {temp_save_path} non è stato creato correttamente. Errori: {'; '.join(error_messages)}")
            return jsonify({
                "successo": False,
                "errore": f"Errore nella creazione del file temporaneo: {'; '.join(error_messages)}"
            }), 500
            
        # Rinomina atomicamente il file temporaneo
        try:
            if os.name == 'nt':  # Windows
                # Windows richiede di rimuovere il file di destinazione prima
                if save_path.exists():
                    save_path.unlink()
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
                shutil.copy2(str(temp_save_path), str(save_path))
                logger.info(f"Copia diretta del file riuscita come fallback")
                
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
        
        # Verifica se è necessario provare diverse estensioni
        if not save_path.exists():
            # Prova con estensione .msgpack se non specificata
            if not (nome_salvataggio.endswith('.json') or nome_salvataggio.endswith('.msgpack')):
                msgpack_path = Path(get_save_path(nome_salvataggio + '.msgpack'))
                json_path = Path(get_save_path(nome_salvataggio + '.json'))
                
                if msgpack_path.exists():
                    save_path = msgpack_path
                    logger.info(f"Trovato file MessagePack: {save_path}")
                elif json_path.exists():
                    save_path = json_path
                    logger.info(f"Trovato file JSON: {save_path}")
                else:
                    return jsonify({
                        "successo": False,
                        "errore": f"Salvataggio '{nome_salvataggio}' non trovato"
                    }), 404
            else:
                return jsonify({
                    "successo": False,
                    "errore": f"Salvataggio '{nome_salvataggio}' non trovato"
                }), 404
        
        # Determina il formato del file
        is_msgpack = save_path.suffix.lower() == '.msgpack'
        
        # Carica i dati dal file
        if is_msgpack:
            with open(save_path, 'rb') as f:
                try:
                    save_data = msgpack.unpack(f, raw=False)
                except Exception as e:
                    logger.error(f"Errore nella decodifica MessagePack: {e}")
                    return jsonify({
                        "successo": False,
                        "errore": f"Errore nella decodifica MessagePack: {str(e)}"
                    }), 500
        else:
            with open(save_path, 'r', encoding='utf-8') as f:
                try:
                    save_data = json.load(f)
                except json.JSONDecodeError as e:
                    logger.error(f"Errore nella decodifica JSON: {e}")
                    return jsonify({
                        "successo": False,
                        "errore": f"Errore nella decodifica JSON: {str(e)}"
                    }), 500
        
        # Applica sanificazione ai dati caricati prima della deserializzazione
        save_data = sanifica_salvataggio(save_data)
        
        # Estrai i dati del mondo
        world_data = save_data.get("world", {})
        
        # Crea un nuovo mondo usando il deserializzatore appropriato
        if is_msgpack:
            world = World.deserialize_msgpack(msgpack.packb(world_data, use_bin_type=True))
        else:
            world = World.deserialize(world_data)
        
        # Se l'ID sessione non è fornito, generane uno nuovo
        if not id_sessione:
            id_sessione = str(uuid4())
        
        # Memorizza la sessione
        sessioni_attive[id_sessione] = world
        
        # Salva la sessione
        try:
            success = salva_sessione(id_sessione, world)
            if not success:
                logger.warning(f"Impossibile salvare la sessione {id_sessione}")
        except Exception as e:
            logger.warning(f"Errore durante il salvataggio della sessione: {e}")
        
        logger.info(f"Mondo '{nome_salvataggio}' caricato nella sessione {id_sessione}")
        
        return jsonify({
            "successo": True,
            "id_sessione": id_sessione,
            "nome_salvataggio": nome_salvataggio,
            "messaggio": "Mondo caricato con successo"
        })
    except Exception as e:
        logger.error(f"Errore generale durante il caricamento: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "successo": False,
            "errore": str(e)
        }), 500 