import logging
import requests
from flask_socketio import emit, join_room
from flask import request

# Import moduli locali
from server.utils.session import get_session, salva_sessione
from . import socketio, graphics_renderer
from . import core
import core.events as Events

# Configura il logger
logger = logging.getLogger(__name__)

def handle_prova_abilita_inizializza(data):
    """
    Inizializza lo stato prova_abilita e invia i dati iniziali al client
    
    Args:
        data (dict): Contiene id_sessione e eventuali parametri aggiuntivi
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione']):
        return
        
    id_sessione = data['id_sessione']
    
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        return
    
    # Ottieni o crea lo stato prova_abilita
    prova_state = sessione.get_temporary_state("prova_abilita")
    if not prova_state:
        # Crea un nuovo stato
        from states.prova_abilita import ProvaAbilitaState
        state = ProvaAbilitaState()
        
        # Inizializza lo stato utilizzando EventBus
        if hasattr(state, 'event_bus'):
            state.set_game_context(sessione)
            # Emetti evento per inizializzare la prova di abilità
            state.emit_event(Events.PROVA_ABILITA_INIZIA)
        
        prova_state = state.to_dict()
        sessione.set_temporary_state("prova_abilita", prova_state)
    else:
        # Deserializza lo stato esistente
        from states.prova_abilita import ProvaAbilitaState
        state = ProvaAbilitaState.from_dict(prova_state)
        state.set_game_context(sessione)
    
    # Crea il room_id per questa sessione
    room_id = f"session_{id_sessione}"
    join_room(room_id)
    
    # Preparazione dati iniziali
    dati_prova = {
        "stato": prova_state,
        "abilita_disponibili": _ottieni_abilita_disponibili(sessione.get_player_entity())
    }
    
    # Invia i dati al client
    emit('prova_abilita_stato', dati_prova)
    
    # Esegui il rendering dell'interfaccia
    from server.websocket.rendering import render_prova_abilita
    render_prova_abilita(state, sessione)
    
    # Salva la sessione aggiornata
    salva_sessione(id_sessione, sessione)

def handle_prova_abilita_scelta(data):
    """
    Gestisce la scelta di un'abilità da parte del giocatore
    
    Args:
        data (dict): Contiene id_sessione e abilita_scelta
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'abilita']):
        return
        
    id_sessione = data['id_sessione']
    abilita = data['abilita']
    
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        return
    
    # Ottieni lo stato prova_abilita
    prova_state = sessione.get_temporary_state("prova_abilita")
    if not prova_state:
        emit('error', {'message': 'Stato prova abilità non disponibile'})
        return
    
    # Deserializza lo stato
    from states.prova_abilita import ProvaAbilitaState
    state = ProvaAbilitaState.from_dict(prova_state)
    state.set_game_context(sessione)
    
    # Utilizza il sistema EventBus se disponibile
    if hasattr(state, 'event_bus'):
        # Emetti evento di abilità scelta
        state.emit_event(Events.ABILITA_SCELTA, abilita=abilita)
    else:
        # Fallback al vecchio sistema
        state.abilita_scelta = abilita
        state.fase = "esecuzione"
    
    # Aggiorna lo stato serializzato
    sessione.set_temporary_state("prova_abilita", state.to_dict())
    
    # Aggiorna il client
    emit('prova_abilita_aggiornamento', {
        'fase': state.fase,
        'abilita_scelta': abilita
    })
    
    # Esegui il rendering dell'interfaccia aggiornata
    from server.websocket.rendering import render_prova_abilita
    render_prova_abilita(state, sessione)
    
    # Salva la sessione aggiornata
    salva_sessione(id_sessione, sessione)

def handle_prova_abilita_esegui(data):
    """
    Esegue la prova di abilità con i parametri specificati
    
    Args:
        data (dict): Contiene id_sessione, difficolta e opzionalmente target_id
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'difficolta']):
        return
        
    id_sessione = data['id_sessione']
    difficolta = data['difficolta']
    target_id = data.get('target_id')
    
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        return
    
    # Ottieni lo stato prova_abilita
    prova_state = sessione.get_temporary_state("prova_abilita")
    if not prova_state:
        emit('error', {'message': 'Stato prova abilità non disponibile'})
        return
    
    # Deserializza lo stato
    from states.prova_abilita import ProvaAbilitaState
    state = ProvaAbilitaState.from_dict(prova_state)
    state.set_game_context(sessione)
    
    # Controlla se è stata scelta un'abilità
    if not state.abilita_scelta:
        emit('error', {'message': 'Nessuna abilità selezionata'})
        return
    
    try:
        # Utilizza il sistema EventBus se disponibile
        if hasattr(state, 'event_bus'):
            # Emetti evento di esecuzione prova
            state.emit_event(Events.PROVA_ABILITA_ESEGUI, 
                           difficolta=difficolta, 
                           target_id=target_id)
        else:
            # Fallback al vecchio sistema
            from states.prova_abilita.esecuzione import esegui_prova
            giocatore = sessione.get_player_entity()
            target = None
            if target_id:
                target = sessione.get_entity(target_id)
                
            risultato = esegui_prova(state, sessione, giocatore, state.abilita_scelta, 
                                    difficolta, target)
            
            state.fase = "risultato"
            state.dati_contestuali['risultato'] = risultato
        
        # Aggiorna lo stato serializzato
        sessione.set_temporary_state("prova_abilita", state.to_dict())
        
        # Aggiorna il client con il risultato (compatibile con entrambi i sistemi)
        emit('prova_abilita_risultato', {
            'risultato': state.dati_contestuali.get('risultato', {}),
            'fase': state.fase
        })
        
        # Esegui il rendering dell'interfaccia con i risultati
        from server.websocket.rendering import render_prova_abilita
        render_prova_abilita(state, sessione)
        
        # Salva la sessione aggiornata
        salva_sessione(id_sessione, sessione)
    except Exception as e:
        logger.error(f"Errore durante l'esecuzione della prova: {e}")
        emit('error', {'message': f'Errore durante la prova: {str(e)}'})

def handle_prova_abilita_termina(data):
    """
    Termina la prova di abilità e pulisce lo stato temporaneo
    
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
        
    # Ottieni lo stato prova_abilita
    prova_state = sessione.get_temporary_state("prova_abilita")
    if not prova_state:
        emit('error', {'message': 'Stato prova abilità non disponibile'})
        return
    
    # Deserializza lo stato
    from states.prova_abilita import ProvaAbilitaState
    state = ProvaAbilitaState.from_dict(prova_state)
    state.set_game_context(sessione)
    
    # Utilizza il sistema EventBus se disponibile
    if hasattr(state, 'event_bus'):
        # Emetti evento di terminazione
        state.emit_event(Events.PROVA_ABILITA_TERMINA)
    
    # Rimuovi lo stato temporaneo
    sessione.remove_temporary_state("prova_abilita")
    
    # Aggiorna il client
    emit('prova_abilita_terminata', {
        'terminata': True
    })
    
    # Salva la sessione aggiornata
    salva_sessione(id_sessione, sessione)

def _ottieni_abilita_disponibili(entita):
    """Helper per ottenere le abilità disponibili di un'entità"""
    abilita = []
    
    if not entita:
        return abilita
        
    # Ottieni le abilità dell'entità
    if hasattr(entita, "get_abilita") and callable(entita.get_abilita):
        abilita = entita.get_abilita()
    else:
        # Fallback per entità senza metodo get_abilita
        for componente in entita.get_all_components():
            if hasattr(componente, "abilita"):
                abilita.extend(componente.abilita)
                
    return abilita

def handle_prova_abilita_input(data):
    """
    Gestisce l'input dell'utente durante una prova di abilità
    
    Args:
        data (dict): Contiene id_sessione, tipo_input e dati_input
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'tipo_input']):
        return
        
    id_sessione = data['id_sessione']
    tipo_input = data['tipo_input']  # "seleziona_abilita", "seleziona_modalita", ecc.
    dati_input = data.get('dati_input', {})
    
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        return
    
    # Ottieni lo stato della prova di abilità
    stato_prova = sessione.get_temporary_state("prova_abilita")
    if not stato_prova:
        emit('error', {'message': 'Nessuna prova di abilità in corso'})
        return
        
    # Deserializza lo stato
    from states.prova_abilita import ProvaAbilitaState
    state = ProvaAbilitaState.from_dict(stato_prova)
    state.set_game_context(sessione)
    
    # Imposta l'ultimo input
    state.ultimo_input = dati_input.get('input')
    
    # Utilizza il sistema EventBus se disponibile
    if hasattr(state, 'event_bus'):
        # Gestisci l'input usando il sistema di eventi
        if tipo_input == "seleziona_abilita" and 'abilita' in dati_input:
            state.emit_event(Events.ABILITA_SCELTA, abilita=dati_input['abilita'])
        elif tipo_input == "seleziona_modalita" and 'modalita' in dati_input:
            state.dati_contestuali["modalita"] = dati_input['modalita']
            if dati_input['modalita'] == "avanzata":
                state.fase = "imposta_difficolta"
                emit('prova_abilita_update', {
                    'fase': state.fase,
                    'messaggio': "Seleziona il livello di difficoltà:",
                    'opzioni_disponibili': [5, 10, 15, 20, 25]
                })
            else:
                # Per modalità semplice, usa difficoltà predefinita
                state.emit_event(Events.PROVA_ABILITA_DIFFICOLTA_IMPOSTATA, difficolta=10)
        elif tipo_input == "seleziona_npg" and 'npg_id' in dati_input:
            state.emit_event(Events.PROVA_ABILITA_NPC_SELEZIONATO, npg_id=dati_input['npg_id'])
    else:
        # Fallback al vecchio sistema
        if tipo_input == "seleziona_abilita":
            abilita = dati_input.get('abilita')
            if abilita:
                state.abilita_scelta = abilita
                state.fase = "scegli_modalita"
                
                # Emetti evento per aggiornare l'interfaccia
                emit('prova_abilita_update', {
                    'fase': state.fase,
                    'messaggio': f"Abilità selezionata: {abilita}",
                    'opzioni_disponibili': ["semplice", "avanzata"]
                })
        
        elif tipo_input == "seleziona_modalita":
            modalita = dati_input.get('modalita')
            if modalita in ["semplice", "avanzata"]:
                state.dati_contestuali["modalita"] = modalita
                
                # Se modalità avanzata, chiedi la difficoltà
                if modalita == "avanzata":
                    state.fase = "imposta_difficolta"
                    emit('prova_abilita_update', {
                        'fase': state.fase,
                        'messaggio': "Seleziona il livello di difficoltà:",
                        'opzioni_disponibili': [5, 10, 15, 20, 25]
                    })
                else:
                    # Per la modalità semplice, procedi direttamente all'esecuzione
                    state.fase = "esegui_prova"
                    emit('prova_abilita_update', {
                        'fase': state.fase,
                        'messaggio': "Esecuzione prova in corso...",
                        'in_corso': True
                    })
                    
                    # Chiama l'endpoint per eseguire la prova
                    response = requests.post(
                        "http://localhost:5000/prova_abilita/esegui",
                        json={
                            "id_sessione": id_sessione,
                            "modalita": "semplice",
                            "abilita": state.abilita_scelta,
                            "difficolta": 10
                        }
                    )
                    
                    if response.status_code == 200:
                        result_data = response.json()
                        emit('prova_abilita_risultato', result_data)
                    else:
                        emit('error', {'message': 'Errore nell\'esecuzione della prova'})
        
        elif tipo_input == "seleziona_npg":
            npg_id = dati_input.get('npg_id')
            if npg_id:
                state.dati_contestuali["target_id"] = npg_id
                state.fase = "scegli_abilita"
                
                # Ottieni le abilità disponibili per l'NPG
                response = requests.get(
                    f"http://localhost:5000/prova_abilita/abilita_disponibili?id_sessione={id_sessione}&entita_id={npg_id}"
                )
                
                if response.status_code == 200:
                    abilita_data = response.json()
                    emit('prova_abilita_update', {
                        'fase': state.fase,
                        'messaggio': "Seleziona un'abilità per la prova:",
                        'abilita_disponibili': abilita_data.get('abilita', [])
                    })
                else:
                    emit('error', {'message': 'Errore nell\'ottenimento delle abilità'})
    
    # Aggiorna lo stato della prova nella sessione
    sessione.set_temporary_state("prova_abilita", state.to_dict())
    
    # Salva la sessione aggiornata
    salva_sessione(id_sessione, sessione)

def handle_prova_abilita_select_npc(data):
    """
    Gestisce la selezione di un NPG durante una prova di abilità
    
    Args:
        data (dict): Contiene id_sessione e npg_id
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'npg_id']):
        return
        
    id_sessione = data['id_sessione']
    npg_id = data['npg_id']
    
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        return
    
    # Ottieni lo stato della prova di abilità
    stato_prova = sessione.get_temporary_state("prova_abilita")
    if not stato_prova:
        emit('error', {'message': 'Nessuna prova di abilità in corso'})
        return
        
    # Deserializza lo stato
    from states.prova_abilita import ProvaAbilitaState
    state = ProvaAbilitaState.from_dict(stato_prova)
    state.set_game_context(sessione)
    
    # Utilizza il sistema EventBus se disponibile
    if hasattr(state, 'event_bus'):
        # Emetti evento di selezione NPC
        state.emit_event(Events.PROVA_ABILITA_NPC_SELEZIONATO, npg_id=npg_id)
    else:
        # Fallback al vecchio sistema
        # Ottieni l'NPG selezionato
        npg = sessione.get_entity(npg_id)
        if not npg:
            emit('error', {'message': 'NPG non trovato'})
            return
            
        # Aggiorna lo stato con l'NPG selezionato
        state.dati_contestuali["target_id"] = npg_id
        state.dati_contestuali["target_nome"] = npg.nome if hasattr(npg, "nome") else f"NPG {npg_id}"
        
        # Se stiamo facendo un confronto, passa alla selezione dell'abilità
        if state.dati_contestuali.get("tipo_prova") == "confronto":
            state.fase = "scegli_abilita"
            
            # Emetti evento per aggiornare l'interfaccia
            emit('prova_abilita_update', {
                'fase': state.fase,
                'messaggio': f"NPG selezionato: {state.dati_contestuali['target_nome']}. Seleziona un'abilità per il confronto:",
                'target': state.dati_contestuali['target_nome']
            })
        else:
            # Se è una prova NPG normale, ottieni le abilità disponibili
            response = requests.get(
                f"http://localhost:5000/prova_abilita/abilita_disponibili?id_sessione={id_sessione}&entita_id={npg_id}"
            )
            
            if response.status_code == 200:
                abilita_data = response.json()
                state.fase = "scegli_abilita_npg"
                emit('prova_abilita_update', {
                    'fase': state.fase,
                    'messaggio': f"NPG selezionato: {state.dati_contestuali['target_nome']}. Seleziona un'abilità da testare:",
                    'abilita_disponibili': abilita_data.get('abilita', []),
                    'target': state.dati_contestuali['target_nome']
                })
            else:
                emit('error', {'message': 'Errore nell\'ottenimento delle abilità dell\'NPG'})
    
    # Aggiorna lo stato della prova nella sessione
    sessione.set_temporary_state("prova_abilita", state.to_dict())
    
    # Salva la sessione aggiornata
    salva_sessione(id_sessione, sessione)

def handle_prova_abilita_select_oggetto(data):
    """
    Gestisce la selezione di un oggetto durante una prova di abilità
    
    Args:
        data (dict): Contiene id_sessione e oggetto_id
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'oggetto_id']):
        return
        
    id_sessione = data['id_sessione']
    oggetto_id = data['oggetto_id']
    
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        return
    
    # Ottieni lo stato della prova di abilità
    stato_prova = sessione.get_temporary_state("prova_abilita")
    if not stato_prova:
        emit('error', {'message': 'Nessuna prova di abilità in corso'})
        return
        
    # Deserializza lo stato
    from states.prova_abilita import ProvaAbilitaState
    state = ProvaAbilitaState.from_dict(stato_prova)
    state.set_game_context(sessione)
    
    # Utilizza il sistema EventBus se disponibile
    if hasattr(state, 'event_bus'):
        # Emetti evento di selezione oggetto
        state.emit_event(Events.PROVA_ABILITA_OGGETTO_SELEZIONATO, oggetto_id=oggetto_id)
    else:
        # Fallback al vecchio sistema
        # Ottieni l'oggetto selezionato
        oggetto = sessione.get_entity(oggetto_id)
        if not oggetto:
            emit('error', {'message': 'Oggetto non trovato'})
            return
            
        # Aggiorna lo stato con l'oggetto selezionato
        state.dati_contestuali["target_id"] = oggetto_id
        state.dati_contestuali["target_nome"] = oggetto.nome if hasattr(oggetto, "nome") else f"Oggetto {oggetto_id}"
        state.fase = "scegli_abilita_oggetto"
        
        # Emetti evento per aggiornare l'interfaccia
        emit('prova_abilita_update', {
            'fase': state.fase,
            'messaggio': f"Oggetto selezionato: {state.dati_contestuali['target_nome']}. Seleziona un'abilità per interagire:",
            'target': state.dati_contestuali['target_nome']
        })
    
    # Aggiorna lo stato della prova nella sessione
    sessione.set_temporary_state("prova_abilita", state.to_dict())
    
    # Salva la sessione aggiornata
    salva_sessione(id_sessione, sessione)

def handle_prova_abilita_imposta_difficolta(data):
    """
    Gestisce l'impostazione della difficoltà durante una prova di abilità
    
    Args:
        data (dict): Contiene id_sessione e difficolta
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'difficolta']):
        return
        
    id_sessione = data['id_sessione']
    difficolta = data['difficolta']
    
    try:
        difficolta = int(difficolta)
        if difficolta < 5 or difficolta > 30:
            emit('error', {'message': 'Difficoltà non valida (deve essere tra 5 e 30)'})
            return
    except ValueError:
        emit('error', {'message': 'Difficoltà deve essere un numero'})
        return
        
    # Ottieni la sessione
    sessione = core.get_session(id_sessione)
    if not sessione:
        return
    
    # Ottieni lo stato della prova di abilità
    stato_prova = sessione.get_temporary_state("prova_abilita")
    if not stato_prova:
        emit('error', {'message': 'Nessuna prova di abilità in corso'})
        return
        
    # Deserializza lo stato
    from states.prova_abilita import ProvaAbilitaState
    state = ProvaAbilitaState.from_dict(stato_prova)
    state.set_game_context(sessione)
    
    # Utilizza il sistema EventBus se disponibile
    if hasattr(state, 'event_bus'):
        # Emetti evento di impostazione difficoltà
        state.emit_event(Events.PROVA_ABILITA_DIFFICOLTA_IMPOSTATA, difficolta=difficolta)
    else:
        # Fallback al vecchio sistema
        # Aggiorna lo stato con la difficoltà impostata
        state.dati_contestuali["difficolta"] = difficolta
        state.fase = "esegui_prova"
        
        # Emetti evento per aggiornare l'interfaccia
        emit('prova_abilita_update', {
            'fase': state.fase,
            'messaggio': f"Difficoltà impostata a {difficolta}. Esecuzione prova in corso...",
            'in_corso': True
        })
        
        # Chiamata all'endpoint per eseguire la prova
        modalita = state.dati_contestuali.get("modalita", "avanzata")
        abilita = state.abilita_scelta
        entita_id = state.dati_contestuali.get("entita_id")
        target_id = state.dati_contestuali.get("target_id")
        
        # Prepara i dati per la richiesta
        payload = {
            "id_sessione": id_sessione,
            "modalita": modalita,
            "abilita": abilita,
            "difficolta": difficolta
        }
        
        if entita_id:
            payload["entita_id"] = entita_id
            
        if target_id:
            payload["target_id"] = target_id
        
        # Esegui la richiesta
        response = requests.post(
            "http://localhost:5000/prova_abilita/esegui",
            json=payload
        )
        
        if response.status_code == 200:
            result_data = response.json()
            emit('prova_abilita_risultato', result_data)
            
            # Aggiorna la fase dello stato
            state.fase = "conclusione"
        else:
            emit('error', {'message': 'Errore nell\'esecuzione della prova'})
    
    # Aggiorna lo stato della prova nella sessione
    sessione.set_temporary_state("prova_abilita", state.to_dict())
    
    # Salva la sessione aggiornata
    salva_sessione(id_sessione, sessione)

def register_handlers(socketio):
    """
    Registra tutti gli handler per gli eventi WebSocket relativi alle prove di abilità
    
    Args:
        socketio: Istanza di Flask-SocketIO
    """
    socketio.on_event('prova_abilita_inizializza', handle_prova_abilita_inizializza)
    socketio.on_event('prova_abilita_scelta', handle_prova_abilita_scelta)
    socketio.on_event('prova_abilita_esegui', handle_prova_abilita_esegui)
    socketio.on_event('prova_abilita_termina', handle_prova_abilita_termina)
    socketio.on_event('prova_abilita_input', handle_prova_abilita_input)
    socketio.on_event('prova_abilita_select_npc', handle_prova_abilita_select_npc)
    socketio.on_event('prova_abilita_select_oggetto', handle_prova_abilita_select_oggetto)
    socketio.on_event('prova_abilita_imposta_difficolta', handle_prova_abilita_imposta_difficolta)
    
    logger.info("Handler per prove di abilità registrati") 