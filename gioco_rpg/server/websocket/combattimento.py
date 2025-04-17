import logging
import time
import requests
from flask_socketio import emit
from flask import request

# Import moduli locali
from server.utils.session import salva_sessione, sessioni_attive
from . import core, socketio

# Configura il logger
logger = logging.getLogger(__name__)

def handle_combattimento_inizia(data):
    """
    Gestisce l'inizializzazione di un combattimento
    
    Args:
        data (dict): Contiene id_sessione e opzionalmente nemici_ids
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione']):
        emit('error', {'message': 'Dati mancanti o non validi'})
        return
        
    id_sessione = data['id_sessione']
    nemici = data.get('nemici', [])
    nemici_ids = data.get('nemici_ids', nemici)
    tipo_incontro = data.get('tipo_incontro', 'casuale')
    
    logger.info(f"Inizializzazione combattimento: {id_sessione}, nemici: {nemici_ids}")
    
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        emit('error', {'message': 'Sessione non trovata'})
        return
    
    try:
        # Usa un approccio diverso e più semplice per il combattimento
        giocatore = None
        # Cerca l'entità con il tag 'player'
        for entity_id, entity in sessione.entities.items():
            if entity.has_tag("player"):
                giocatore = entity
                break
        
        # Se non troviamo un'entità con il tag 'player', cerchiamo un'entità con name 'Player'
        if not giocatore:
            for entity_id, entity in sessione.entities.items():
                if entity.name == "Player":
                    giocatore = entity
                    # Aggiungi il tag player per renderlo identificabile come giocatore
                    entity.add_tag("player")
                    break
        
        if not giocatore:
            logger.error(f"Giocatore non trovato nella sessione {id_sessione}. Entità presenti: {list(sessione.entities.keys())}")
            emit('error', {'message': 'Giocatore non trovato'})
            return
            
        logger.info(f"Giocatore trovato: {giocatore.id}, {giocatore.name}")
        
        # Crea i nemici
        nemici_entita = []
        for nemico_tipo in nemici_ids:
            # Crea un nemico basato sul tipo
            nemico = sessione.create_entity(name=nemico_tipo.capitalize())
            nemico.add_tag("nemico")
            nemico.aggiungi_abilita("forza", 2)
            nemico.aggiungi_abilita("destrezza", 3)
            nemico.aggiungi_abilita("costituzione", 1)
            nemici_entita.append(nemico)
            
        logger.info(f"Nemici creati: {[n.id for n in nemici_entita]}")
        
        # Prepara i partecipanti al combattimento
        partecipanti = [giocatore] + nemici_entita
        
        # Crea una struttura dati semplice per il combattimento
        combat_data = {
            "partecipanti": [p.id for p in partecipanti],
            "tipo_incontro": tipo_incontro,
            "turno_corrente": giocatore.id,  # Inizia dal giocatore
            "round_corrente": 1,
            "in_corso": True,
            "azioni": {},  # Dizionario vuoto per le azioni
            "messaggi": []
        }
        
        # Memorizza lo stato nella sessione
        sessione.set_temporary_state("combattimento", combat_data)
        
        # Prepara i dati di risposta
        partecipanti_info = []
        for p in partecipanti:
            partecipanti_info.append({
                "id": p.id,
                "nome": p.name,
                "è_giocatore": p.has_tag("player"),
                "è_nemico": p.has_tag("nemico"),
                "iniziativa": 10  # Valore predefinito
            })
        
        result_data = {
            "successo": True,
            "stato": "iniziato",
            "tipo_incontro": tipo_incontro,
            "partecipanti": partecipanti_info,
            "turno_di": giocatore.id
        }
        
        logger.info(f"Emissione dell'evento combattimento_inizializzato per la sessione {id_sessione}")
        
        # Emetti evento per aggiornare l'interfaccia del client
        emit('combattimento_inizializzato', result_data, namespace='/')
        
        # Emetti anche un evento per tutti i client nella stessa sessione
        room_id = f"session_{id_sessione}"
        socketio.emit('combattimento_inizializzato', result_data, room=room_id, namespace='/')
        
        # Salva la sessione per persistere lo stato del combattimento
        salva_sessione(id_sessione, sessione)
        
        logger.info(f"Combattimento inizializzato con successo per la sessione {id_sessione}")
        
        # Avvia aggiornamenti periodici per il combattimento
        socketio.start_background_task(
            task_aggiornamenti_combattimento,
            id_sessione=id_sessione,
            room_id=room_id
        )
    except Exception as e:
        logger.error(f"Errore nella gestione del combattimento: {e}")
        emit('error', {'message': f'Errore interno: {str(e)}'})

def handle_combattimento_azione(data):
    """
    Handler per l'azione di combattimento
    
    Args:
        data (dict): Dati dell'evento
    """
    id_sessione = data.get('id_sessione')
    tipo_azione = data.get('tipo_azione')
    parametri = data.get('parametri', {})
    
    logger.info(f"Richiesta combattimento_azione: sessione={id_sessione}, tipo={tipo_azione}, parametri={parametri}")
    
    if not id_sessione or not tipo_azione:
        logger.error(f"Parametri mancanti: {data}")
        emit('error', {'message': 'Parametri mancanti'})
        return
        
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        logger.error(f"Sessione non trovata: {id_sessione}")
        emit('error', {'message': 'Sessione non trovata'})
        return
        
    try:
        # Ottieni lo stato del combattimento
        stato_combattimento = sessione.get_temporary_state("combattimento")
        if not stato_combattimento:
            logger.error(f"Nessun combattimento in corso per la sessione: {id_sessione}")
            emit('error', {'message': 'Nessun combattimento in corso'})
            return
            
        logger.info(f"Stato combattimento trovato: {stato_combattimento}")
            
        # Deserializza lo stato
        from states.combattimento.combattimento_state import CombattimentoState
        state = CombattimentoState.from_dict(stato_combattimento, sessione)
        
        # Esegui l'azione in base al tipo
        risultato = None
        
        if tipo_azione == "attacca" or tipo_azione == "attacco":
            attaccante_id = parametri.get("attaccante_id")
            target_id = parametri.get("target_id")
            arma = parametri.get("arma")
            
            logger.info(f"Attacco: attaccante={attaccante_id}, target={target_id}, arma={arma}")
            
            # Verifica che sia il turno dell'attaccante
            if state.turno_corrente != attaccante_id:
                logger.warning(f"Non è il turno dell'attaccante: turno corrente={state.turno_corrente}, attaccante={attaccante_id}")
                emit('error', {
                    'message': 'Non è il turno di questa entità'
                })
                return
                
            # Esegui l'attacco
            risultato = state.azioni.esegui_attacco(attaccante_id, target_id, arma)
            logger.info(f"Risultato attacco: {risultato}")
            
        elif tipo_azione == "passa":
            entita_id = parametri.get("entita_id")
            
            # Verifica che sia il turno dell'entità
            if state.turno_corrente != entita_id:
                logger.warning(f"Non è il turno dell'entità: turno corrente={state.turno_corrente}, entità={entita_id}")
                emit('error', {
                    'message': 'Non è il turno di questa entità'
                })
                return
                
            # Passa il turno
            risultato = state.azioni.passa_turno(entita_id)
            logger.info(f"Risultato passa turno: {risultato}")
            
        else:
            logger.error(f"Tipo di azione non supportato: {tipo_azione}")
            emit('error', {
                'message': f'Tipo di azione non supportato: {tipo_azione}'
            })
            return
            
        # Controlla se il combattimento è terminato
        combat_terminato = False
        if hasattr(state, 'gestore_turni') and state.gestore_turni:
            combat_terminato = state.gestore_turni.controlla_fine_combattimento()
            logger.info(f"Combattimento terminato: {combat_terminato}")
        
        if combat_terminato:
            # Determina il vincitore
            vincitore = state.gestore_turni.determina_vincitore()
            
            # Aggiorna lo stato
            sessione.set_temporary_state("combattimento", state.to_dict())
            
            # Invia l'evento di azione eseguita
            room_id = f"session_{id_sessione}"
            logger.info(f"Emissione combattimento_azione_eseguita (terminato): {risultato}")
            emit('combattimento_azione_eseguita', {
                'risultato': risultato,
                'stato': {
                    'in_corso': False,
                    'vincitore': vincitore,
                    'messaggi': state.messaggi[-5:] if hasattr(state, "messaggi") else []
                }
            })
            
            # Invia l'evento di combattimento terminato
            emit('combattimento_terminato', {
                'vincitore': vincitore
            })
            
            return
            
        # Se è il turno di un'entità controllata dal computer, esegui la sua azione
        if state.turno_corrente:
            entita = sessione.get_entity(state.turno_corrente)
            if entita and not entita.has_tag("player"):
                logger.info(f"Turno dell'IA: {entita.id} - {entita.name}")
                try:
                    # Ottieni l'azione dell'IA
                    azione_ia = state.azioni.determina_azione_ia(state.turno_corrente)
                    
                    # Esegui l'azione dell'IA
                    risultato_ia = state.azioni.esegui_azione_ia(azione_ia)
                    logger.info(f"Risultato azione IA: {risultato_ia}")
                    
                    # Controlla di nuovo se il combattimento è terminato
                    combat_terminato = state.gestore_turni.controlla_fine_combattimento()
                    
                    if combat_terminato:
                        vincitore = state.gestore_turni.determina_vincitore()
                        
                        # Aggiorna lo stato
                        sessione.set_temporary_state("combattimento", state.to_dict())
                        
                        # Invia l'evento di azione eseguita
                        logger.info(f"Emissione combattimento_azione_eseguita (IA, terminato): {risultato}")
                        emit('combattimento_azione_eseguita', {
                            'risultato': risultato,
                            'risultato_ia': risultato_ia,
                            'stato': {
                                'in_corso': False,
                                'vincitore': vincitore,
                                'messaggi': state.messaggi[-5:] if hasattr(state, "messaggi") else []
                            }
                        })
                        
                        # Invia l'evento di combattimento terminato
                        emit('combattimento_terminato', {
                            'vincitore': vincitore
                        })
                        
                        return
                        
                    # Preparati a inviare anche il risultato dell'IA
                    risultato = {
                        'giocatore': risultato,
                        'ia': risultato_ia
                    }
                except Exception as e:
                    logger.error(f"Errore durante l'esecuzione dell'azione IA: {e}")
                    risultato = {
                        'giocatore': risultato,
                        'ia_errore': str(e)
                    }
                
        # Aggiorna lo stato
        sessione.set_temporary_state("combattimento", state.to_dict())
        
        # Prepara lo stato aggiornato per la risposta
        stato_aggiornato = {
            'in_corso': state.in_corso,
            'turno_di': state.turno_corrente,
            'round': state.round_corrente,
            'messaggi': state.messaggi[-5:] if hasattr(state, "messaggi") else []
        }
        
        # Invia l'evento di azione eseguita
        logger.info(f"Emissione combattimento_azione_eseguita: {risultato}")
        emit('combattimento_azione_eseguita', {
            'risultato': risultato,
            'stato': stato_aggiornato
        })
        
        # Emetti anche un evento per tutti i client nella stessa sessione
        room_id = f"session_{id_sessione}"
        socketio.emit('combattimento_azione_eseguita', {
            'risultato': risultato,
            'stato': stato_aggiornato
        }, room=room_id)
        
    except Exception as e:
        logger.error(f"Errore durante l'esecuzione dell'azione: {e}")
        import traceback
        logger.error(traceback.format_exc())
        emit('error', {'message': f'Errore interno: {str(e)}'})

def handle_combattimento_seleziona_bersaglio(data):
    """
    Gestisce la selezione di un bersaglio durante il combattimento
    
    Args:
        data (dict): Contiene id_sessione, attaccante_id e target_id
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'attaccante_id', 'target_id']):
        return
        
    id_sessione = data['id_sessione']
    attaccante_id = data['attaccante_id']
    target_id = data['target_id']
    
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        return
    
    try:
        # Ottieni lo stato del combattimento
        stato_combattimento = sessione.get_temporary_state("combattimento")
        if not stato_combattimento:
            emit('error', {'message': 'Nessun combattimento in corso'})
            return
            
        # Deserializza lo stato
        from states.combattimento.combattimento_state import CombattimentoState
        state = CombattimentoState.from_dict(stato_combattimento, sessione)
        
        # Verifica se l'attaccante può agire in questo turno
        if state.turno_corrente != attaccante_id:
            emit('error', {'message': 'Non è il turno di questa entità'})
            return
        
        # Verifica se il target è valido
        if target_id not in state.partecipanti:
            emit('error', {'message': 'Bersaglio non valido'})
            return
        
        # Memorizza la selezione
        state.target_selezionato = target_id
        
        # Emetti evento per aggiornare l'interfaccia
        emit('combattimento_bersaglio_selezionato', {
            'attaccante_id': attaccante_id,
            'target_id': target_id,
            'azioni_disponibili': state.get_azioni_disponibili(attaccante_id, target_id)
        })
        
        # Aggiorna lo stato
        sessione.set_temporary_state("combattimento", state.to_dict())
        
    except Exception as e:
        logger.error(f"Errore nella selezione del bersaglio: {e}")
        import traceback
        logger.error(traceback.format_exc())
        emit('error', {'message': f'Errore interno: {str(e)}'})

def handle_combattimento_usa_abilita(data):
    """
    Handler per l'uso di un'abilità durante il combattimento
    
    Args:
        data (dict): Dati dell'evento
    """
    id_sessione = data.get('id_sessione')
    entita_id = data.get('entita_id')
    abilita = data.get('abilita')
    target_ids = data.get('target_ids', [])
    
    logger.info(f"Richiesta combattimento_usa_abilita: sessione={id_sessione}, entita={entita_id}, abilita={abilita}, targets={target_ids}")
    
    if not id_sessione or not entita_id or not abilita:
        logger.error(f"Parametri mancanti: {data}")
        emit('error', {'message': 'Parametri mancanti'})
        return
        
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        logger.error(f"Sessione non trovata: {id_sessione}")
        emit('error', {'message': 'Sessione non trovata'})
        return
        
    try:
        # Ottieni lo stato del combattimento
        stato_combattimento = sessione.get_temporary_state("combattimento")
        if not stato_combattimento:
            logger.error(f"Nessun combattimento in corso per la sessione: {id_sessione}")
            emit('error', {'message': 'Nessun combattimento in corso'})
            return
            
        logger.info(f"Stato combattimento trovato: {stato_combattimento}")
            
        # Deserializza lo stato
        from states.combattimento.combattimento_state import CombattimentoState
        state = CombattimentoState.from_dict(stato_combattimento, sessione)
        
        # Verifica che sia il turno dell'entità
        if state.turno_corrente != entita_id:
            logger.warning(f"Non è il turno dell'entità: turno corrente={state.turno_corrente}, entità={entita_id}")
            emit('error', {
                'message': 'Non è il turno di questa entità'
            })
            return
            
        # Usa l'abilità
        logger.info(f"Tentativo di usare abilità: {abilita} da parte di {entita_id} su {target_ids}")
        risultato = state.azioni.usa_abilita(entita_id, abilita, target_ids)
        logger.info(f"Risultato uso abilità: {risultato}")
        
        if not risultato or not risultato.get('successo', False):
            # Invia l'errore ma emetti anche l'evento di abilità usata con successo=false
            # per permettere ai client di gestire l'errore
            emit('error', {
                'message': risultato.get('messaggio', 'Errore nell\'uso dell\'abilità')
            })
            
            # Emetti anche l'evento di abilità usata con successo=false
            socketio.emit('combattimento_abilita_usata', {
                'risultato': risultato,
                'stato': {
                    'in_corso': state.in_corso,
                    'turno_di': state.turno_corrente,
                    'round': state.round_corrente,
                    'messaggi': state.messaggi[-5:] if hasattr(state, "messaggi") else []
                }
            }, room=f"session_{id_sessione}")
            
            return
            
        # Controlla se il combattimento è terminato
        combat_terminato = False
        if hasattr(state, 'gestore_turni') and state.gestore_turni:
            combat_terminato = state.gestore_turni.controlla_fine_combattimento()
            logger.info(f"Combattimento terminato: {combat_terminato}")
        
        if combat_terminato:
            # Determina il vincitore
            vincitore = state.gestore_turni.determina_vincitore()
            
            # Aggiorna lo stato
            sessione.set_temporary_state("combattimento", state.to_dict())
            
            # Invia l'evento di abilità usata
            room_id = f"session_{id_sessione}"
            logger.info(f"Emissione combattimento_abilita_usata (terminato): {risultato}")
            emit('combattimento_abilita_usata', {
                'risultato': risultato,
                'stato': {
                    'in_corso': False,
                    'vincitore': vincitore,
                    'messaggi': state.messaggi[-5:] if hasattr(state, "messaggi") else []
                }
            })
            
            # Invia l'evento di combattimento terminato
            emit('combattimento_terminato', {
                'vincitore': vincitore
            })
            
            return
            
        # Passa al turno successivo
        if hasattr(state, 'gestore_turni') and state.gestore_turni:
            state.gestore_turni.passa_al_turno_successivo()
        
        # Se è il turno di un'entità controllata dal computer, esegui la sua azione
        if state.turno_corrente:
            entita = sessione.get_entity(state.turno_corrente)
            if entita and not entita.has_tag("player"):
                logger.info(f"Turno dell'IA: {entita.id} - {entita.name}")
                try:
                    # Ottieni l'azione dell'IA
                    azione_ia = state.azioni.determina_azione_ia(state.turno_corrente)
                    
                    # Esegui l'azione dell'IA
                    risultato_ia = state.azioni.esegui_azione_ia(azione_ia)
                    logger.info(f"Risultato azione IA: {risultato_ia}")
                    
                    # Controlla di nuovo se il combattimento è terminato
                    if hasattr(state, 'gestore_turni') and state.gestore_turni:
                        combat_terminato = state.gestore_turni.controlla_fine_combattimento()
                    
                    if combat_terminato:
                        vincitore = state.gestore_turni.determina_vincitore()
                        
                        # Aggiorna lo stato
                        sessione.set_temporary_state("combattimento", state.to_dict())
                        
                        # Invia l'evento di abilità usata
                        logger.info(f"Emissione combattimento_abilita_usata (IA, terminato): {risultato}")
                        emit('combattimento_abilita_usata', {
                            'risultato': risultato,
                            'risultato_ia': risultato_ia,
                            'stato': {
                                'in_corso': False,
                                'vincitore': vincitore,
                                'messaggi': state.messaggi[-5:] if hasattr(state, "messaggi") else []
                            }
                        })
                        
                        # Invia l'evento di combattimento terminato
                        emit('combattimento_terminato', {
                            'vincitore': vincitore
                        })
                        
                        return
                        
                    # Preparati a inviare anche il risultato dell'IA
                    risultato = {
                        'giocatore': risultato,
                        'ia': risultato_ia
                    }
                except Exception as e:
                    logger.error(f"Errore durante l'esecuzione dell'azione IA: {e}")
                    risultato = {
                        'giocatore': risultato,
                        'ia_errore': str(e)
                    }
                
        # Aggiorna lo stato
        sessione.set_temporary_state("combattimento", state.to_dict())
        
        # Prepara lo stato aggiornato per la risposta
        stato_aggiornato = {
            'in_corso': state.in_corso,
            'turno_di': state.turno_corrente,
            'round': state.round_corrente,
            'messaggi': state.messaggi[-5:] if hasattr(state, "messaggi") else []
        }
        
        # Invia l'evento di abilità usata
        logger.info(f"Emissione combattimento_abilita_usata: {risultato}")
        emit('combattimento_abilita_usata', {
            'risultato': risultato,
            'stato': stato_aggiornato
        })
        
        # Emetti anche un evento per tutti i client nella stessa sessione
        room_id = f"session_{id_sessione}"
        socketio.emit('combattimento_abilita_usata', {
            'risultato': risultato,
            'stato': stato_aggiornato
        }, room=room_id)
        
    except Exception as e:
        logger.error(f"Errore durante l'uso dell'abilità: {e}")
        import traceback
        logger.error(traceback.format_exc())
        emit('error', {'message': f'Errore interno: {str(e)}'})

def handle_combattimento_usa_oggetto(data):
    """
    Gestisce l'uso di un oggetto durante il combattimento
    
    Args:
        data (dict): Contiene id_sessione, entita_id, oggetto e target_ids
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'entita_id', 'oggetto']):
        return
        
    id_sessione = data['id_sessione']
    entita_id = data['entita_id']
    oggetto = data['oggetto']
    target_ids = data.get('target_ids', [])
    
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        return
    
    try:
        # Usa l'endpoint per eseguire l'azione
        response = requests.post(
            "http://localhost:5000/game/combat/azione",
            json={
                "id_sessione": id_sessione,
                "tipo_azione": "oggetto",
                "parametri": {
                    "utilizzatore_id": entita_id,
                    "oggetto": oggetto,
                    "target_ids": target_ids
                }
            }
        )
        
        if response.status_code == 200:
            result_data = response.json()
            
            # Emetti evento per aggiornare l'interfaccia
            emit('combattimento_oggetto_usato', {
                'entita_id': entita_id,
                'oggetto': oggetto,
                'target_ids': target_ids,
                'risultato': result_data.get('risultato')
            })
            
            # Emetti anche un evento per tutti i client nella stessa sessione
            room_id = f"session_{id_sessione}"
            socketio.emit('combattimento_oggetto_usato', {
                'entita_id': entita_id,
                'oggetto': oggetto,
                'target_ids': target_ids,
                'risultato': result_data.get('risultato')
            }, room=room_id)
        else:
            emit('error', {'message': 'Errore nell\'uso dell\'oggetto'})
    except Exception as e:
        logger.error(f"Errore nell'uso dell'oggetto: {e}")
        emit('error', {'message': f'Errore interno: {str(e)}'})

def handle_combattimento_passa_turno(data):
    """
    Gestisce il passaggio di turno durante il combattimento
    
    Args:
        data (dict): Contiene id_sessione e entita_id
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'entita_id']):
        return
        
    id_sessione = data['id_sessione']
    entita_id = data['entita_id']
    
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        return
    
    try:
        # Usa l'endpoint per eseguire l'azione
        response = requests.post(
            "http://localhost:5000/game/combat/azione",
            json={
                "id_sessione": id_sessione,
                "tipo_azione": "passa",
                "parametri": {
                    "entita_id": entita_id
                }
            }
        )
        
        if response.status_code == 200:
            result_data = response.json()
            
            # Emetti evento per aggiornare l'interfaccia
            emit('combattimento_turno_passato', {
                'entita_id': entita_id,
                'prossimo_turno': result_data.get('prossimo_turno'),
                'round': result_data.get('round')
            })
            
            # Emetti anche un evento per tutti i client nella stessa sessione
            room_id = f"session_{id_sessione}"
            socketio.emit('combattimento_turno_passato', {
                'entita_id': entita_id,
                'prossimo_turno': result_data.get('prossimo_turno'),
                'round': result_data.get('round')
            }, room=room_id)
        else:
            emit('error', {'message': 'Errore nel passaggio di turno'})
    except Exception as e:
        logger.error(f"Errore nel passaggio di turno: {e}")
        emit('error', {'message': f'Errore interno: {str(e)}'})

def task_aggiornamenti_combattimento(id_sessione, room_id):
    """
    Task in background per inviare aggiornamenti periodici sullo stato del combattimento
    
    Args:
        id_sessione: ID della sessione di gioco
        room_id: ID della room SocketIO
    """
    try:
        logger = logging.getLogger(__name__)
        logger.info(f"Avvio task aggiornamenti combattimento per sessione {id_sessione}")
        
        # Memorizza l'ultimo stato per confronto
        ultimo_stato_hash = None
        ultimo_stato = None
        
        # Esegui aggiornamenti ogni 2 secondi per 5 minuti
        for ciclo in range(150):  # 5 minuti = 300 secondi = 150 cicli di 2 secondi
            # Verifica se la sessione esiste ancora
            from server.utils.session import sessioni_attive
            sessione = sessioni_attive.get(id_sessione)
            if not sessione:
                logger.info(f"Sessione {id_sessione} non più attiva, interruzione aggiornamenti")
                break
                
            # Verifica se il combattimento è ancora in corso
            stato_combattimento = sessione.get_temporary_state("combattimento")
            if not stato_combattimento:
                logger.info(f"Nessun combattimento attivo nella sessione {id_sessione}, interruzione aggiornamenti")
                break
                
            # Calcola un hash semplice dello stato per verificare se è cambiato
            # Utilizziamo solo i campi principali per evitare falsi cambiamenti dovuti a timestamp o altri campi volatili
            try:
                import hashlib
                import json
                # Estrai solo i campi rilevanti per il confronto
                stato_rilevante = {
                    "turno": stato_combattimento.get("turno_corrente"),
                    "round": stato_combattimento.get("round_corrente"),
                    "in_corso": stato_combattimento.get("in_corso"),
                    "fase": stato_combattimento.get("fase_corrente"),
                    # Non includiamo messaggi che cambiano frequentemente
                }
                
                # Aggiungiamo HP dei partecipanti per identificare cambiamenti significativi
                for p_id in stato_combattimento.get("partecipanti", []):
                    p = sessione.get_entity(p_id)
                    if p:
                        stato_rilevante[f"hp_{p_id}"] = getattr(p, "hp", 0)
                
                # Calcoliamo hash dello stato rilevante
                stato_json = json.dumps(stato_rilevante, sort_keys=True)
                stato_hash = hashlib.md5(stato_json.encode()).hexdigest()
                
                # Se lo stato non è cambiato, riutilizziamo l'ultimo stato deserializzato
                if stato_hash == ultimo_stato_hash and ultimo_stato is not None:
                    logger.debug(f"Stato combattimento non cambiato (ciclo {ciclo}), riutilizzo stato precedente")
                    state = ultimo_stato
                else:
                    # Stato cambiato o primo ciclo, deserializziamo
                    from states.combattimento.combattimento_state import CombattimentoState
                    state = CombattimentoState.from_dict(stato_combattimento, sessione)
                    ultimo_stato = state
                    ultimo_stato_hash = stato_hash
                    logger.debug(f"Stato combattimento cambiato, deserializzazione completa (ciclo {ciclo})")
            except Exception as e:
                # In caso di errore nel calcolo dell'hash, deserializziamo sempre
                logger.warning(f"Errore nel calcolo hash stato: {e}, deserializzazione completa")
                from states.combattimento.combattimento_state import CombattimentoState
                state = CombattimentoState.from_dict(stato_combattimento, sessione)
            
            # Verifica che azioni sia inizializzato
            if not hasattr(state, 'azioni') or state.azioni is None:
                from states.combattimento.azioni import AzioniCombattimento
                from states.combattimento.turni import GestoreTurni
                from states.combattimento.ui import UICombattimento
                
                # Inizializza i moduli separati
                state.azioni = AzioniCombattimento(state)
                state.gestore_turni = GestoreTurni(state)
                state.ui = UICombattimento(state)
                
                # Aggiungi anche gli altri attributi necessari
                state.fase = getattr(state, 'fase', "scelta")
                state.dati_temporanei = getattr(state, 'dati_temporanei', {})
            
            # Se il combattimento è terminato, interrompi gli aggiornamenti
            if not state.in_corso:
                logger.info(f"Combattimento terminato nella sessione {id_sessione}, interruzione aggiornamenti")
                break
                
            # Ottieni informazioni sui partecipanti
            partecipanti_info = []
            for p_id in state.partecipanti:
                p = sessione.get_entity(p_id)
                if p:
                    partecipanti_info.append({
                        "id": p.id,
                        "nome": p.name,
                        "è_giocatore": p.has_tag("player"),
                        "è_nemico": p.has_tag("nemico"),
                        "iniziativa": getattr(p, "iniziativa", 0),
                        "hp": getattr(p, "hp", 10),
                        "max_hp": getattr(p, "max_hp", 10),
                        "azioni_disponibili": state.get_azioni_disponibili(p_id)
                    })
            
            # Invia aggiornamento a tutti i client nella stessa room
            socketio.emit('combattimento_aggiornamento', {
                'in_corso': state.in_corso,
                'round': state.round_corrente,
                'turno_di': state.turno_corrente,
                'fase': state.fase_corrente,
                'partecipanti': partecipanti_info,
                'messaggi': state.messaggi[-5:] if hasattr(state, "messaggi") else []
            }, room=room_id)
            
            # Attendi prima del prossimo aggiornamento
            time.sleep(2)
    except Exception as e:
        logger.error(f"Errore nel task di aggiornamento del combattimento: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Invia un errore ai client
        socketio.emit('error', {'message': f'Errore interno negli aggiornamenti: {str(e)}'}, room=room_id)

def register_handlers(socketio_instance):
    """
    Registra gli handler del combattimento
    
    Args:
        socketio_instance: Istanza SocketIO
    """
    # Supporta sia "combattimento_inizia" che "combattimento_inizializza" per retrocompatibilità
    socketio_instance.on_event('combattimento_inizia', handle_combattimento_inizia)
    socketio_instance.on_event('combattimento_inizializza', handle_combattimento_inizia)
    
    socketio_instance.on_event('combattimento_azione', handle_combattimento_azione)
    socketio_instance.on_event('combattimento_seleziona_bersaglio', handle_combattimento_seleziona_bersaglio)
    socketio_instance.on_event('combattimento_usa_abilita', handle_combattimento_usa_abilita)
    socketio_instance.on_event('combattimento_usa_oggetto', handle_combattimento_usa_oggetto)
    socketio_instance.on_event('combattimento_passa_turno', handle_combattimento_passa_turno)
    
    logger.info("Handler del combattimento registrati")
    
# Registra gli handler quando il modulo viene importato
register_handlers(socketio) 