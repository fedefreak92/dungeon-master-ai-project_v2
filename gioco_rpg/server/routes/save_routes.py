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
                is_json_format = str(save_path).endswith('.json') or not (str(save_path).endswith('.dat') or str(save_path).endswith('.pickle'))
                
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
                
                # Rimuovi l'estensione .json dal nome del salvataggio
                nome_senza_estensione = nome_salvataggio.replace('.json', '')
                
                metadata = save_data.get("metadata", {})
                risultati.append({
                    "nome": nome_senza_estensione,
                    "data": metadata.get("data", ""),
                    "versione": metadata.get("versione", "")
                })
            except Exception as e:
                logger.warning(f"Errore nella lettura del salvataggio {nome_salvataggio}: {e}")
                # Se c'è un errore nel leggere un salvataggio, includi solo il nome
                # Rimuovi l'estensione .json dal nome del salvataggio
                nome_senza_estensione = nome_salvataggio.replace('.json', '')
                risultati.append({
                    "nome": nome_senza_estensione,
                    "data": "",
                    "versione": ""
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
        
        # Serializza il mondo
        try:
            world_data = world.serialize()
            
            # Prova a verificare che il dizionario sia JSON-compatibile
            try:
                # Questo test è per verificare la compatibilità
                json.dumps(world_data)
            except (TypeError, OverflowError, ValueError) as je:
                logger.error(f"I dati del mondo non sono JSON-compatibili: {je}")
                return jsonify({
                    "successo": False, 
                    "errore": f"Errore nella serializzazione: il mondo contiene dati non serializzabili"
                }), 500
        except Exception as e:
            logger.error(f"Errore nella serializzazione del mondo: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({
                "successo": False, 
                "errore": f"Errore nella serializzazione del mondo: {str(e)}"
            }), 500
        
        # Aggiungi metadati
        save_data = {
            "metadata": {
                "nome": nome_salvataggio,
                "data": datetime.datetime.now().isoformat(),
                "versione": "2.0.0"
            },
            "world": world_data
        }
        
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
        
        # Salvataggio usando diversi metodi in caso di errore
        save_success = False
        error_messages = []
        
        # Metodo 1: Usando pathlib.write_text direttamente
        try:
            json_str = json.dumps(save_data, indent=2, ensure_ascii=False)
            temp_save_path.write_text(json_str, encoding='utf-8')
            logger.info(f"File temporaneo creato con metodo Path.write_text: {temp_save_path}")
            if temp_save_path.exists() and temp_save_path.stat().st_size > 0:
                save_success = True
            else:
                error_messages.append("File creato con write_text ma non esiste o è vuoto")
        except Exception as e1:
            error_messages.append(f"Errore con metodo file temporaneo: {str(e1)}")
            logger.warning(f"Errore con metodo file temporaneo: {str(e1)}")
            
            # Metodo 2: Usando open tradizionale
            if not save_success:
                try:
                    with open(str(temp_save_path), 'w', encoding='utf-8') as f:
                        json.dump(save_data, f, indent=2, ensure_ascii=False)
                        f.flush()  # Forza la scrittura su disco
                    logger.info(f"File temporaneo creato con metodo open tradizionale: {temp_save_path}")
                    if os.path.exists(str(temp_save_path)) and os.path.getsize(str(temp_save_path)) > 0:
                        save_success = True
                    else:
                        error_messages.append("File creato con open ma non esiste o è vuoto")
                except Exception as e2:
                    error_messages.append(f"Errore con metodo diretto: {str(e2)}")
                    logger.warning(f"Errore con metodo diretto: {str(e2)}")
                    
                    # Metodo 3: Salvataggio diretto senza file temporaneo
                    if not save_success:
                        try:
                            save_path.write_text(json.dumps(save_data, indent=2, ensure_ascii=False), encoding='utf-8')
                            logger.info(f"File salvato direttamente con Path (ultimo tentativo): {save_path}")
                            if save_path.exists() and save_path.stat().st_size > 0:
                                save_success = True
                                # In questo caso abbiamo già salvato direttamente, quindi usciamo
                                logger.info(f"Mondo salvato come '{nome_salvataggio}' (metodo diretto)")
                                return jsonify({
                                    "successo": True,
                                    "nome_salvataggio": nome_salvataggio,
                                    "messaggio": "Mondo salvato con successo (metodo diretto)"
                                })
                            else:
                                error_messages.append("File salvato direttamente ma non esiste o è vuoto")
                        except Exception as e3:
                            error_messages.append(f"Errore con metodo Path per salvataggio manifest (ultimo tentativo): {str(e3)}")
                            logger.warning(f"Usando metodo Path per salvataggio manifest (ultimo tentativo)")
                            
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
    
    # Verifica che il nome del salvataggio sia fornito
    if not nome_salvataggio:
        return jsonify({
            "successo": False,
            "errore": "Nome salvataggio non fornito"
        }), 400
    
    try:
        # Verifica che il file di salvataggio esista
        save_path = get_save_path(nome_salvataggio)
        if not os.path.exists(save_path):
            # Prova a controllare se esiste un file con estensione .json, .dat o nessuna estensione
            alternative_paths = [
                f"{save_path}.json",
                f"{save_path}.dat"
            ]
            found = False
            for alt_path in alternative_paths:
                if os.path.exists(alt_path):
                    save_path = alt_path
                    found = True
                    break
            
            if not found:
                return jsonify({
                    "successo": False,
                    "errore": "Salvataggio non trovato"
                }), 404
        
        # Determina il formato del file in base all'estensione
        is_json_format = str(save_path).endswith('.json') or not (str(save_path).endswith('.dat') or str(save_path).endswith('.pickle'))
        
        # Carica i dati del salvataggio
        try:
            if is_json_format:
                with open(save_path, 'r', encoding='utf-8') as f:
                    try:
                        save_data = json.load(f)
                    except json.JSONDecodeError as e:
                        logger.error(f"Errore nella decodifica JSON: {e}")
                        return jsonify({
                            "successo": False,
                            "errore": f"File di salvataggio JSON non valido: {str(e)}"
                        }), 500
            else:
                # Fallback a pickle per vecchi file
                with open(save_path, 'rb') as f:
                    try:
                        save_data = pickle.load(f)
                    except Exception as e:
                        logger.error(f"Errore durante la deserializzazione pickle: {e}")
                        return jsonify({
                            "successo": False,
                            "errore": f"File di salvataggio corrotto: {str(e)}"
                        }), 500
        except Exception as e:
            logger.error(f"Errore durante l'apertura del file di salvataggio: {e}")
            return jsonify({
                "successo": False,
                "errore": f"Impossibile aprire il file di salvataggio: {str(e)}"
            }), 500
        
        # Normalizza il formato dei dati del salvataggio
        try:
            normalized_save_data = normalize_save_data(save_data)
            logger.info(f"Dati del salvataggio normalizzati")
        except Exception as e:
            logger.error(f"Errore durante la normalizzazione dei dati: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({
                "successo": False,
                "errore": f"Errore durante la normalizzazione dei dati: {str(e)}"
            }), 500
            
        # Estrai i dati del mondo normalizzati
        world_data = normalized_save_data.get("world", {})
        
        # Deserializza il mondo
        try:
            world = World.deserialize(world_data)
        except Exception as e:
            logger.error(f"Errore durante la deserializzazione del mondo: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({
                "successo": False,
                "errore": f"Errore durante la deserializzazione del mondo: {str(e)}"
            }), 500
        
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