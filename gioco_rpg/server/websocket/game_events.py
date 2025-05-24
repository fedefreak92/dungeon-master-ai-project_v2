import logging
from flask_socketio import emit
from flask import request
import time

# Import moduli locali
from server.utils.session import salva_sessione, sessioni_attive
from . import core

# Configura il logger
logger = logging.getLogger(__name__)

def handle_game_event(data):
    """
    Gestisce un evento di gioco inviato dal client
    
    Args:
        data (dict): Contiene id_sessione, tipo_evento e dati_evento
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'tipo_evento']):
        return
        
    id_sessione = data['id_sessione']
    tipo_evento = data['tipo_evento']
    dati_evento = data.get('dati_evento', {})
    
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        return
    
    # Gestisci l'evento nel mondo ECS
    risultato = sessione.process_event(tipo_evento, dati_evento)
    
    # Salva la sessione aggiornata
    salva_sessione(id_sessione, sessione)
    
    # Comunica il risultato al client
    emit('event_result', {
        'success': True,
        'result': risultato,
        'world_state': sessione.get_player_view()
    })

def handle_player_input(data):
    """
    Gestisce l'input del giocatore dal frontend
    
    Args:
        data (dict): Contiene id_sessione, tipo_input e dati_input
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'tipo_input']):
        return
        
    id_sessione = data['id_sessione']
    tipo_input = data['tipo_input']
    dati_input = data.get('dati_input', {})
    
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        return
    
    # Trasforma l'input in un evento ECS appropriato
    if tipo_input == 'move':
        direzione = dati_input.get('direzione')
        if direzione:
            risultato = sessione.process_event('player_move', {'direction': direzione})
    elif tipo_input == 'action':
        azione = dati_input.get('azione')
        if azione:
            risultato = sessione.process_event('player_action', {'action': azione})
    elif tipo_input == 'interact':
        target_id = dati_input.get('target_id')
        if target_id:
            risultato = sessione.process_event('player_interact', {'target_id': target_id})
    elif tipo_input == 'save_game':
        # Gestione salvataggio
        nome_salvataggio = dati_input.get('name', f"Salvataggio_{int(time.time())}")
        logger.info(f"Richiesta salvataggio: {nome_salvataggio}")
        
        try:
            from flask import current_app
            import requests
            
            # Prepara i dati per la richiesta
            save_data = {
                "id_sessione": id_sessione,
                "nome_salvataggio": nome_salvataggio
            }
            
            # URL dell'endpoint di salvataggio
            api_url = f"http://localhost:{current_app.config.get('PORT', 5000)}/save/salva"
            logger.info(f"Chiamata REST a {api_url} con dati: {save_data}")
            
            # Effettua la richiesta POST
            response = requests.post(api_url, json=save_data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('successo'):
                    logger.info(f"Salvataggio completato: {nome_salvataggio}")
                    emit('game_notification', {
                        'type': 'success',
                        'message': f'Gioco salvato come "{nome_salvataggio}"'
                    })
                else:
                    logger.error(f"Errore nel salvataggio: {result.get('errore')}")
                    emit('game_notification', {
                        'type': 'error',
                        'message': f'Errore: {result.get("errore", "Errore sconosciuto")}'
                    })
            else:
                logger.error(f"Errore HTTP nel salvataggio: {response.status_code}, Risposta: {response.text}")
                emit('game_notification', {
                    'type': 'error',
                    'message': f'Errore nel salvataggio: codice {response.status_code}'
                })
                
        except Exception as e:
            logger.error(f"Eccezione durante il salvataggio: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            emit('game_notification', {
                'type': 'error',
                'message': f'Errore durante il salvataggio: {str(e)}'
            })
            
        # Comunica il risultato anche senza stato aggiornato
        emit('game_update', {
            'success': True
        })
        return
    else:
        emit('error', {'message': 'Tipo input non valido'})
        return
    
    # Salva la sessione aggiornata
    salva_sessione(id_sessione, sessione)
    
    # Comunica il risultato al client
    emit('game_update', {
        'success': True
    })

def handle_player_action(data):
    """
    Gestisce le azioni del giocatore
    
    Args:
        data (dict): Contiene action e data dell'azione
    """
    sid = request.sid
    client_id = sid
    
    # Log dettagliato per debug
    logger.info(f"=== PLAYER ACTION RICEVUTA ===")
    logger.info(f"Client ID: {client_id}")
    logger.info(f"Dati ricevuti: {data}")
    logger.info(f"Timestamp: {time.time()}")
    
    # Verifica se abbiamo un ID sessione
    from server.utils.session import socket_sessioni
    
    id_sessione = socket_sessioni.get(client_id)
    if not id_sessione:
        logger.error(f"Client {client_id} non associato ad alcuna sessione")
        logger.info(f"Socket sessioni attive: {list(socket_sessioni.keys())}")
        emit('error', {'message': 'Sessione non trovata - ricarica la pagina'})
        return
    
    logger.info(f"Client {client_id} associato alla sessione {id_sessione}")
    
    # Controlla che i dati siano in formato corretto
    if not isinstance(data, dict):
        emit('error', {'message': 'Formato dati non valido'})
        return
    
    # Estrai i dati dell'azione
    action = data.get('action')
    action_data = data.get('data', {}) or data.get('params', {})
    
    logger.info(f"Ricevuta azione {action} dal client {client_id} con dati: {action_data}")
    
    # DEBUG: Log di tutte le azioni ricevute
    logger.info(f"🔍 TIPO AZIONE: '{action}' | DATI: {action_data}")
    
    # Gestisci le diverse azioni
    if action == 'save_game':
        # Gestione salvataggio
        nome_salvataggio = action_data.get('name', f"Salvataggio_{int(time.time())}")
        logger.info(f"Richiesta salvataggio: {nome_salvataggio}")
        
        try:
            from flask import current_app
            import requests
            
            # Prepara i dati per la richiesta
            save_data = {
                "id_sessione": id_sessione,
                "nome_salvataggio": nome_salvataggio
            }
            
            # URL dell'endpoint di salvataggio
            api_url = f"http://localhost:{current_app.config.get('PORT', 5000)}/save/salva"
            logger.info(f"Chiamata REST a {api_url} con dati: {save_data}")
            
            # Effettua la richiesta POST
            response = requests.post(api_url, json=save_data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('successo'):
                    logger.info(f"Salvataggio completato: {nome_salvataggio}")
                    emit('game_notification', {
                        'type': 'success',
                        'message': f'Gioco salvato come "{nome_salvataggio}"'
                    })
                else:
                    logger.error(f"Errore nel salvataggio: {result.get('errore')}")
                    emit('game_notification', {
                        'type': 'error',
                        'message': f'Errore: {result.get("errore", "Errore sconosciuto")}'
                    })
            else:
                logger.error(f"Errore HTTP nel salvataggio: {response.status_code}, Risposta: {response.text}")
                emit('game_notification', {
                    'type': 'error',
                    'message': f'Errore nel salvataggio: codice {response.status_code}'
                })
                
        except Exception as e:
            logger.error(f"Eccezione durante il salvataggio: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            emit('game_notification', {
                'type': 'error',
                'message': f'Errore durante il salvataggio: {str(e)}'
            })
    
    else:
        # Per le altre azioni, trasforma in input appropriato
        session = core.get_session(id_sessione)
        if not session:
            emit('error', {'message': 'Sessione non trovata'})
            return
            
        # DEBUG: Verifica stato del mondo ECS
        logger.info(f"[DEBUG MOVIMENTO] Stato del mondo ECS:")
        logger.info(f"[DEBUG MOVIMENTO] - Entità totali: {len(session.entities)}")
        logger.info(f"[DEBUG MOVIMENTO] - Entità per ID: {list(session.entities.keys())}")
        
        # DEBUG: Verifica entità con tag player
        try:
            player_entities = session.find_entities_by_tag("player") if hasattr(session, "find_entities_by_tag") else []
            logger.info(f"[DEBUG MOVIMENTO] - Entità con tag 'player': {len(player_entities)}")
            if player_entities:
                for i, p in enumerate(player_entities):
                    logger.info(f"[DEBUG MOVIMENTO] - Player {i}: ID={getattr(p, 'id', 'N/A')}, Nome={getattr(p, 'nome', getattr(p, 'name', 'N/A'))}, Tipo={type(p).__name__}")
        except Exception as e:
            logger.error(f"[DEBUG MOVIMENTO] Errore nella verifica delle entità player: {e}")
        
        # DEBUG: Verifica se il giocatore esiste nel sistema legacy
        try:
            if hasattr(session, 'giocatore') and session.giocatore:
                logger.info(f"[DEBUG MOVIMENTO] - Giocatore legacy presente: ID={getattr(session.giocatore, 'id', 'N/A')}, Nome={getattr(session.giocatore, 'nome', 'N/A')}")
            else:
                logger.warning(f"[DEBUG MOVIMENTO] - Nessun giocatore legacy trovato")
        except Exception as e:
            logger.error(f"[DEBUG MOVIMENTO] Errore nella verifica del giocatore legacy: {e}")
            
        # SOLUZIONE TEMPORANEA: Se il giocatore non è nel mondo ECS, tenta di aggiungerlo
        try:
            player_entities = session.find_entities_by_tag("player") if hasattr(session, "find_entities_by_tag") else []
            if not player_entities:
                logger.warning(f"[RIPRISTINO GIOCATORE] Nessuna entità giocatore nel mondo ECS, tento il ripristino")
                
                # Metodo 1: Cerca nel sistema legacy
                if hasattr(session, 'giocatore') and session.giocatore:
                    logger.info(f"[RIPRISTINO GIOCATORE] Trovato giocatore legacy, lo aggiungo al mondo ECS")
                    session.giocatore = session.giocatore  # Usa il setter che dovrebbe aggiungerlo al mondo
                    logger.info(f"[RIPRISTINO GIOCATORE] Giocatore aggiunto tramite setter")
                    
                    # Verifica che sia stato aggiunto
                    player_entities_after = session.find_entities_by_tag("player") if hasattr(session, "find_entities_by_tag") else []
                    logger.info(f"[RIPRISTINO GIOCATORE] Entità giocatore dopo ripristino: {len(player_entities_after)}")
                    
                # Metodo 2: Carica da file salvataggio se esiste
                elif session_id:
                    logger.info(f"[RIPRISTINO GIOCATORE] Nessun giocatore legacy, tento caricamento da file salvataggio")
                    from server.utils.session import carica_sessione
                    original_world = carica_sessione(session_id)
                    if original_world:
                        original_players = original_world.find_entities_by_tag("player") if hasattr(original_world, "find_entities_by_tag") else []
                        if original_players:
                            player_to_restore = original_players[0]
                            logger.info(f"[RIPRISTINO GIOCATORE] Trovato giocatore nel file: {getattr(player_to_restore, 'nome', 'N/A')}")
                            session.add_entity(player_to_restore)
                            logger.info(f"[RIPRISTINO GIOCATORE] Giocatore ripristinato da file")
                        else:
                            logger.error(f"[RIPRISTINO GIOCATORE] Nessun giocatore nel file di salvataggio originale")
                    else:
                        logger.error(f"[RIPRISTINO GIOCATORE] Impossibile caricare il file di salvataggio originale")
                        
                # Metodo 3: Crea un giocatore di emergenza
                else:
                    logger.warning(f"[RIPRISTINO GIOCATORE] Creo un giocatore di emergenza")
                    from entities.giocatore import Giocatore
                    emergency_player = Giocatore(
                        nome="Giocatore",
                        classe="guerriero",
                        razza="umano",
                        livello=1,
                        hp=10
                    )
                    emergency_player.x = 7  # Posizione default taverna
                    emergency_player.y = 8
                    emergency_player.mappa_corrente = "taverna"
                    session.add_entity(emergency_player)
                    logger.info(f"[RIPRISTINO GIOCATORE] Giocatore di emergenza creato: {emergency_player.nome}")
            else:
                logger.info(f"[RIPRISTINO GIOCATORE] Giocatore già presente nel mondo ECS")
                
        except Exception as e:
            logger.error(f"[RIPRISTINO GIOCATORE] Errore durante il ripristino del giocatore: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
        # Trasforma player_action nel formato atteso dal sistema ECS
        try:
            if action == 'move_player':
                logger.info(f"🎮 ACTION MOVE_PLAYER RICEVUTA! Direction: {action_data.get('direction')}")
                logger.info(f"🎮 Tutti i dati action: {action_data}")
                
                direction = action_data.get('direction')
                logger.info(f"Movimento richiesto: direzione={direction}")
                
                if direction:
                    # Ottieni il giocatore
                    player = session.get_player_entity()
                    if not player:
                        logger.error("Giocatore non trovato nella sessione")
                        emit('error', {'message': 'Giocatore non trovato'}, room=sid)
                        return
                    
                    logger.info(f"Giocatore trovato: {getattr(player, 'nome', player.id)} a posizione ({getattr(player, 'x', 'N/A')}, {getattr(player, 'y', 'N/A')})")

                    # Ottieni il gestore mappe dalla sessione/mondo
                    # Assicurati che session.mondo e session.mondo.gestore_mappe esistano e siano corretti
                    gestore_mappe = None
                    if hasattr(session, 'mondo') and hasattr(session.mondo, 'gestore_mappe'):
                        gestore_mappe = session.mondo.gestore_mappe
                    elif hasattr(session, 'gestore_mappe'): # Fallback se gestore_mappe è direttamente nella sessione
                        gestore_mappe = session.gestore_mappe
                    
                    if not gestore_mappe:
                        logger.error("GestoreMappe non trovato nella sessione.")
                        emit('error', {'message': 'Errore interno del server (GestoreMappe mancante).'}, room=sid)
                        return

                    dx, dy = 0, 0
                    if direction == 'nord': dy = -1
                    elif direction == 'sud': dy = 1
                    elif direction == 'ovest': dx = -1
                    elif direction == 'est': dx = 1
                    else:
                        logger.warning(f"Direzione non valida: {direction}")
                        emit('error', {'message': f"Direzione '{direction}' non valida."}, room=sid)
                        return
                    
                    logger.info(f"Tentativo movimento giocatore {player.id} ({getattr(player, 'nome', player.id)}) da ({player.x},{player.y}) in direzione {direction} (dx:{dx}, dy:{dy}) sulla mappa {player.mappa_corrente}")

                    risultato_movimento = player.muovi(dx, dy, gestore_mappe)
                    
                    logger.info(f"Risultato movimento per {player.id}: {risultato_movimento}")

                    if risultato_movimento and risultato_movimento.get("successo"):
                        logger.info(f"Movimento riuscito per {player.id}. Nuova posizione: ({player.x},{player.y}) sulla mappa {player.mappa_corrente}")
                        
                        # CRITICAL FIX: Forza l'aggiornamento dell'entità nel mondo ECS
                        # Trova l'entità nel mondo ECS e aggiorna la sua posizione
                        world_entities = session.entities if hasattr(session, 'entities') else {}
                        if player.id in world_entities:
                            world_player = world_entities[player.id]
                            world_player.x = player.x
                            world_player.y = player.y
                            world_player.mappa_corrente = player.mappa_corrente
                            logger.info(f"AGGIORNAMENTO FORZATO: Entità {player.id} nel mondo ECS aggiornata a posizione ({world_player.x},{world_player.y})")
                        else:
                            logger.warning(f"Entità {player.id} non trovata in session.entities per aggiornamento posizione")
                            # Aggiungi l'entità al mondo se non presente
                            session.entities[player.id] = player
                            logger.info(f"Entità {player.id} aggiunta al mondo ECS con posizione ({player.x},{player.y})")
                        
                        # MIGLIORAMENTO: Salvataggio immediato e verificato
                        logger.info(f"SALVATAGGIO IMMEDIATO: Inizio salvataggio sessione {id_sessione} dopo movimento")
                        try:
                            # Verifica che la posizione sia corretta prima del salvataggio
                            final_x, final_y = player.x, player.y
                            final_mappa = player.mappa_corrente
                            logger.info(f"POSIZIONE FINALE PRIMA DEL SALVATAGGIO: x={final_x}, y={final_y}, mappa={final_mappa}")
                            
                            # Forza aggiornamento della sessione in memoria
                            sessioni_attive[id_sessione] = session
                            
                            if salva_sessione(id_sessione, session):
                                logger.info(f"✓ SUCCESSO: Sessione {id_sessione} salvata correttamente dopo movimento")
                                logger.info(f"✓ POSIZIONE SALVATA: x={final_x}, y={final_y}, mappa={final_mappa}")
                            else:
                                logger.error(f"✗ FALLIMENTO nel salvataggio della sessione {id_sessione} dopo movimento")
                        except Exception as save_error:
                            logger.error(f"✗ ECCEZIONE durante il salvataggio della sessione {id_sessione}: {save_error}")
                            import traceback
                            logger.error(traceback.format_exc())

                        # Emetti l'aggiornamento della posizione al client
                        emit('player_position_updated', {
                            'player_id': player.id,
                            'x': player.x,
                            'y': player.y,
                            'map_id': player.mappa_corrente,
                            'message': risultato_movimento.get("messaggio", "Movimento effettuato.")
                        }, room=sid)
                        
                        if "cambio_mappa_richiesto" in risultato_movimento:
                            logger.info(f"Cambio mappa richiesto a {risultato_movimento['cambio_mappa_richiesto']} per {player.id}")
                            # Qui la logica di cambio mappa (FSM, ecc.)
                            # Ad esempio: session.mondo.gestore_stati.cambia_stato('MappaState', {'nome_luogo': risultato_movimento['cambio_mappa_richiesto']})
                            # E poi emettere un evento di cambio mappa al client.
                            emit('map_changed', {
                                'new_map_id': risultato_movimento['cambio_mappa_richiesto'],
                                'player_new_coords': risultato_movimento.get('nuova_mappa_coords'),
                                'message': f"Transizione alla mappa: {risultato_movimento['cambio_mappa_richiesto']}"
                            }, room=sid)
                    else:
                        logger.warning(f"Movimento fallito per {player.id}: {risultato_movimento.get('messaggio', 'Motivo sconosciuto')}")
                        emit('player_move_failed', {
                            'player_id': player.id,
                            'message': risultato_movimento.get("messaggio", "Impossibile muoversi lì.")
                        }, room=sid)
                    # Non è più necessario l'EventBus per il movimento diretto qui
                    # L'event bus può essere usato per side effect o da altri sistemi che reagiscono al movimento.
                else:
                    logger.warning("Direzione mancante nella richiesta di movimento")
                    emit('error', {'message': 'Direzione non specificata'}, room=sid)
                    
            elif action == 'interact':
                # Assicurati che il giocatore e la sessione siano validi
                player = session.get_player_entity()
                if not player:
                    logger.error(f"Tentativo di interazione senza giocatore valido per sessione {id_sessione}")
                    emit('error', {'message': 'Giocatore non trovato'}, room=sid)
                    return

                logger.info(f"Azione 'interact' ricevuta per giocatore {player.id} ({getattr(player, 'nome', '')})")
                # La logica di interazione dovrebbe essere gestita dallo stato corrente della FSM
                # o da un sistema dedicato, non direttamente qui.
                # Qui potremmo emettere un evento sull'EventBus o chiamare un metodo del mondo/stato.
                
                # Esempio: session.mondo.fsm.current_state.handle_interaction(player, action_data)
                # Oppure: EventBus.get_instance().emit(EventType.PLAYER_INTERACT_REQUEST, player_id=player.id, target_data=action_data, session_id=id_sessione)

                # Per ora, logghiamo e inviamo un placeholder di successo
                # Dovrai implementare la logica di interazione effettiva.
                emit('interaction_result', {'success': True, 'message': 'Interazione ricevuta (logica da implementare).'}, room=sid)
                salva_sessione(id_sessione, session) # Salva se l'interazione potesse modificare lo stato

            elif action == 'dialog_response':
                option_index = action_data.get('option_index')
                if option_index is not None:
                    # La logica di risposta al dialogo dovrebbe essere gestita dallo stato DialogoState
                    # session.mondo.fsm.current_state.process_input({'type': 'select_option', 'option_index': option_index})
                    logger.info(f"Risposta al dialogo (opzione {option_index}) ricevuta per sessione {id_sessione}")
                    emit('dialog_update', {'success': True, 'message': f"Opzione {option_index} elaborata (logica da implementare)."}, room=sid)
                    salva_sessione(id_sessione, session)
            elif action == 'exit_to_menu':
                logger.info(f"Richiesta uscita al menu per sessione {id_sessione}")
                # session.mondo.fsm.change_state('MenuPrincipaleState') o simile
                emit('game_event_response', {'event': 'exit_to_menu', 'success': True, 'message': 'Ritorno al menu (da implementare).'}, room=sid)
                # Potrebbe essere necessario pulire/salvare la sessione qui
            else:
                emit('error', {'message': f'Azione non supportata: {action}'}, room=sid)
                return
            
        except Exception as e:
            logger.error(f"Errore nell'elaborazione dell'azione {action}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            emit('error', {'message': f'Errore: {str(e)}'})

def handle_request_game_state(data):
    """
    Gestisce una richiesta di stato completo del gioco
    
    Args:
        data (dict): Contiene id_sessione
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione']):
        return
        
    id_sessione = data['id_sessione']
    
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        return
    
    # Ottieni la vista completa del gioco
    try:
        game_state = {
            'player': sessione.get_player_entity().serialize(),
            'entities': [e.serialize() for e in sessione.get_entities()],
            'world': sessione.serialize()
        }
        
        emit('full_game_state', game_state)
    except Exception as e:
        logger.error(f"Errore nell'ottenere lo stato del gioco: {e}")
        emit('error', {'message': f'Errore nel caricamento dello stato: {str(e)}'})

def register_handlers(socketio_instance):
    """
    Registra gli handler degli eventi di gioco
    
    Args:
        socketio_instance: Istanza SocketIO
    """
    socketio_instance.on_event('game_event', handle_game_event)
    socketio_instance.on_event('player_input', handle_player_input)
    socketio_instance.on_event('player_action', handle_player_action)
    socketio_instance.on_event('request_game_state', handle_request_game_state)
    
    logger.info("Handler degli eventi di gioco registrati") 