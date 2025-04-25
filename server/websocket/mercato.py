import logging
import json
import requests
from flask_socketio import emit, join_room

# Import moduli locali
from server.utils.session import get_session, salva_sessione
from . import socketio, graphics_renderer
from . import core

# Configura il logger
logger = logging.getLogger(__name__)

def handle_mercato_inizializza(data):
    """
    Inizializza lo stato mercato e invia i dati iniziali al client
    
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
    
    # Ottieni lo stato mercato
    mercato_state = sessione.get_state("mercato")
    if not mercato_state:
        emit('error', {'message': 'Stato mercato non disponibile'})
        return
    
    # Crea il room_id per questa sessione
    room_id = f"session_{id_sessione}"
    join_room(room_id)
    
    # Preparazione dati iniziali
    dati_mercato = {
        "stato": mercato_state.to_dict(),
        "npg_presenti": {nome: npg.to_dict() for nome, npg in mercato_state.npg_presenti.items()},
        "oggetti_interattivi": {id: obj.to_dict() for id, obj in mercato_state.oggetti_interattivi.items()}
    }
    
    # Ottieni la mappa del mercato se disponibile
    try:
        mappa = sessione.gestore_mappe.ottieni_mappa("mercato")
        if mappa:
            dati_mercato["mappa"] = mappa.to_dict()
            # Aggiungi la posizione del giocatore
            giocatore = sessione.giocatore
            posizione = giocatore.get_posizione("mercato")
            dati_mercato["posizione_giocatore"] = {"x": posizione[0], "y": posizione[1]}
    except Exception as e:
        logger.error(f"Errore nel recupero della mappa: {e}")
    
    # Invia i dati iniziali al client
    emit('mercato_inizializzato', dati_mercato)
    
    # Aggiorna il renderer
    try:
        graphics_renderer.render_mercato(mercato_state, sessione)
    except Exception as e:
        logger.error(f"Errore durante il rendering del mercato: {e}")

def handle_mercato_interagisci(data):
    """
    Gestisce l'interazione con un oggetto nel mercato
    
    Args:
        data (dict): Contiene id_sessione e oggetto_id
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'oggetto_id']):
        return
        
    id_sessione = data['id_sessione']
    oggetto_id = data['oggetto_id']
    
    # Crea il room_id per questa sessione
    room_id = f"session_{id_sessione}"
    
    try:
        # Usa l'endpoint per interagire con l'oggetto
        response = requests.post(
            "http://localhost:5000/game/mercato/interagisci",
            json={
                "id_sessione": id_sessione,
                "oggetto_id": oggetto_id
            }
        )
        
        if response.status_code == 200:
            result_data = response.json()
            
            # Emetti evento per aggiornare l'interfaccia
            emit('mercato_oggetto_interagito', {
                'oggetto_id': oggetto_id,
                'risultato': result_data.get('risultato')
            })
            
            # Emetti anche un evento per tutti i client nella stessa sessione
            socketio.emit('mercato_oggetto_interagito', {
                'oggetto_id': oggetto_id,
                'risultato': result_data.get('risultato')
            }, room=room_id)
            
            # Aggiorna il renderer se necessario
            sessione = core.get_session(id_sessione)
            if sessione:
                mercato_state = sessione.get_state("mercato")
                if mercato_state:
                    graphics_renderer.render_mercato(mercato_state, sessione)
        else:
            emit('error', {'message': 'Errore nell\'interazione con l\'oggetto'})
    except Exception as e:
        logger.error(f"Errore nell'interazione con l'oggetto: {e}")
        emit('error', {'message': f'Errore interno: {str(e)}'})

def handle_mercato_dialoga(data):
    """
    Gestisce il dialogo con un NPG nel mercato
    
    Args:
        data (dict): Contiene id_sessione, npg_nome e opzionalmente opzione_scelta
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'npg_nome']):
        return
        
    id_sessione = data['id_sessione']
    npg_nome = data['npg_nome']
    opzione_scelta = data.get('opzione_scelta')
    
    # Crea il room_id per questa sessione
    room_id = f"session_{id_sessione}"
    
    try:
        # Usa l'endpoint per dialogare con l'NPG
        response = requests.post(
            "http://localhost:5000/game/mercato/dialoga",
            json={
                "id_sessione": id_sessione,
                "npg_nome": npg_nome,
                "opzione_scelta": opzione_scelta
            }
        )
        
        if response.status_code == 200:
            result_data = response.json()
            
            # Emetti evento per aggiornare l'interfaccia
            emit('mercato_dialogo_aggiornato', {
                'npg_nome': npg_nome,
                'dialogo': result_data.get('dialogo')
            })
            
            # Emetti anche un evento per tutti i client nella stessa sessione
            socketio.emit('mercato_dialogo_aggiornato', {
                'npg_nome': npg_nome,
                'dialogo': result_data.get('dialogo')
            }, room=room_id)
        else:
            emit('error', {'message': 'Errore nel dialogo con l\'NPG'})
    except Exception as e:
        logger.error(f"Errore nel dialogo con l'NPG: {e}")
        emit('error', {'message': f'Errore interno: {str(e)}'})

def handle_mercato_menu(data):
    """
    Gestisce l'interazione con i menu del mercato
    
    Args:
        data (dict): Contiene id_sessione, menu_id e opzionalmente scelta
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'menu_id']):
        return
        
    id_sessione = data['id_sessione']
    menu_id = data['menu_id']
    scelta = data.get('scelta')
    
    # Crea il room_id per questa sessione
    room_id = f"session_{id_sessione}"
    
    try:
        # Usa l'endpoint per gestire il menu
        response = requests.post(
            "http://localhost:5000/game/mercato/menu",
            json={
                "id_sessione": id_sessione,
                "menu_id": menu_id,
                "scelta": scelta
            }
        )
        
        if response.status_code == 200:
            result_data = response.json()
            
            # Emetti evento per aggiornare l'interfaccia
            emit('mercato_menu_aggiornato', {
                'menu_id': menu_id,
                'risultato': result_data.get('risultato')
            })
            
            # Emetti anche un evento per tutti i client nella stessa sessione
            socketio.emit('mercato_menu_aggiornato', {
                'menu_id': menu_id,
                'risultato': result_data.get('risultato')
            }, room=room_id)
            
            # Aggiorna il renderer se necessario
            sessione = core.get_session(id_sessione)
            if sessione:
                mercato_state = sessione.get_state("mercato")
                if mercato_state:
                    graphics_renderer.render_mercato(mercato_state, sessione)
        else:
            emit('error', {'message': 'Errore nella gestione del menu'})
    except Exception as e:
        logger.error(f"Errore nella gestione del menu: {e}")
        emit('error', {'message': f'Errore interno: {str(e)}'})

def handle_mercato_movimento(data):
    """
    Gestisce il movimento nel mercato
    
    Args:
        data (dict): Contiene id_sessione e direzione
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'direzione']):
        return
        
    id_sessione = data['id_sessione']
    direzione = data['direzione']
    
    # Crea il room_id per questa sessione
    room_id = f"session_{id_sessione}"
    
    try:
        # Usa l'endpoint per gestire il movimento
        response = requests.post(
            "http://localhost:5000/game/mercato/movimento",
            json={
                "id_sessione": id_sessione,
                "direzione": direzione
            }
        )
        
        if response.status_code == 200:
            result_data = response.json()
            
            # Emetti evento per aggiornare l'interfaccia
            emit('mercato_movimento_eseguito', {
                'direzione': direzione,
                'posizione': result_data.get('posizione'),
                'evento': result_data.get('evento')
            })
            
            # Emetti anche un evento per tutti i client nella stessa sessione
            socketio.emit('mercato_movimento_eseguito', {
                'direzione': direzione,
                'posizione': result_data.get('posizione'),
                'evento': result_data.get('evento')
            }, room=room_id)
            
            # Aggiorna il renderer se necessario
            sessione = core.get_session(id_sessione)
            if sessione:
                mercato_state = sessione.get_state("mercato")
                if mercato_state:
                    graphics_renderer.render_mercato(mercato_state, sessione)
        else:
            emit('error', {'message': 'Errore nel movimento'})
    except Exception as e:
        logger.error(f"Errore nel movimento: {e}")
        emit('error', {'message': f'Errore interno: {str(e)}'})

def handle_mercato_transizione(data):
    """
    Gestisce le transizioni tra il mercato e altri stati
    
    Args:
        data (dict): Contiene id_sessione, stato_destinazione e parametri
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'stato_destinazione']):
        return
        
    id_sessione = data['id_sessione']
    stato_destinazione = data['stato_destinazione']
    parametri = data.get('parametri', {})
    
    # Crea il room_id per questa sessione
    room_id = f"session_{id_sessione}"
    
    try:
        # Usa l'endpoint per gestire la transizione
        response = requests.post(
            "http://localhost:5000/game/mercato/transizione",
            json={
                "id_sessione": id_sessione,
                "stato_destinazione": stato_destinazione,
                "parametri": parametri
            }
        )
        
        if response.status_code == 200:
            result_data = response.json()
            
            # Emetti evento per aggiornare l'interfaccia
            emit('mercato_transizione_completata', {
                'stato_destinazione': stato_destinazione,
                'success': True
            })
            
            # Emetti anche un evento per tutti i client nella stessa sessione
            socketio.emit('mercato_transizione_completata', {
                'stato_destinazione': stato_destinazione,
                'success': True
            }, room=room_id)
        else:
            emit('error', {'message': 'Errore nella transizione di stato'})
    except Exception as e:
        logger.error(f"Errore nella transizione di stato: {e}")
        emit('error', {'message': f'Errore interno: {str(e)}'})

def handle_mercato_compra(data):
    """
    Gestisce l'acquisto di un oggetto nel mercato
    
    Args:
        data (dict): Contiene id_sessione e oggetto_id
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'oggetto_id']):
        return
        
    id_sessione = data['id_sessione']
    oggetto_id = data['oggetto_id']
    
    # Crea il room_id per questa sessione
    room_id = f"session_{id_sessione}"
    
    try:
        # Usa l'endpoint per comprare l'oggetto
        response = requests.post(
            "http://localhost:5000/game/mercato/compra",
            json={
                "id_sessione": id_sessione,
                "oggetto_id": oggetto_id
            }
        )
        
        if response.status_code == 200:
            result_data = response.json()
            
            # Emetti evento per aggiornare l'interfaccia
            emit('mercato_acquisto_completato', {
                'oggetto_id': oggetto_id,
                'messaggio': result_data.get('messaggio'),
                'monete_rimanenti': result_data.get('monete_rimanenti')
            })
            
            # Emetti anche un evento per tutti i client nella stessa sessione
            socketio.emit('mercato_acquisto_completato', {
                'oggetto_id': oggetto_id,
                'messaggio': result_data.get('messaggio'),
                'monete_rimanenti': result_data.get('monete_rimanenti')
            }, room=room_id)
        else:
            emit('error', {'message': 'Errore nell\'acquisto dell\'oggetto'})
    except Exception as e:
        logger.error(f"Errore nell'acquisto dell'oggetto: {e}")
        emit('error', {'message': f'Errore interno: {str(e)}'})

def handle_mercato_vendi(data):
    """
    Gestisce la vendita di un oggetto nel mercato
    
    Args:
        data (dict): Contiene id_sessione e oggetto_id
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'oggetto_id']):
        return
        
    id_sessione = data['id_sessione']
    oggetto_id = data['oggetto_id']
    
    # Crea il room_id per questa sessione
    room_id = f"session_{id_sessione}"
    
    try:
        # Usa l'endpoint per vendere l'oggetto
        response = requests.post(
            "http://localhost:5000/game/mercato/vendi",
            json={
                "id_sessione": id_sessione,
                "oggetto_id": oggetto_id
            }
        )
        
        if response.status_code == 200:
            result_data = response.json()
            
            # Emetti evento per aggiornare l'interfaccia
            emit('mercato_vendita_completata', {
                'oggetto_id': oggetto_id,
                'messaggio': result_data.get('messaggio'),
                'monete_totali': result_data.get('monete_totali')
            })
            
            # Emetti anche un evento per tutti i client nella stessa sessione
            socketio.emit('mercato_vendita_completata', {
                'oggetto_id': oggetto_id,
                'messaggio': result_data.get('messaggio'),
                'monete_totali': result_data.get('monete_totali')
            }, room=room_id)
        else:
            emit('error', {'message': 'Errore nella vendita dell\'oggetto'})
    except Exception as e:
        logger.error(f"Errore nella vendita dell'oggetto: {e}")
        emit('error', {'message': f'Errore interno: {str(e)}'})

def handle_mercato_contratta(data):
    """
    Gestisce la contrattazione del prezzo per un articolo
    
    Args:
        data (dict): Contiene id_sessione, articolo_id e offerta
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'articolo_id']):
        return
        
    id_sessione = data['id_sessione']
    articolo_id = data['articolo_id']
    offerta = data.get('offerta', 0)
    
    # Crea il room_id per questa sessione
    room_id = f"session_{id_sessione}"
    
    try:
        # Usa l'endpoint per gestire la contrattazione
        response = requests.post(
            "http://localhost:5000/game/mercato/contratta",
            json={
                "id_sessione": id_sessione,
                "articolo_id": articolo_id,
                "offerta": offerta
            }
        )
        
        if response.status_code == 200:
            result_data = response.json()
            
            # Emetti evento per aggiornare l'interfaccia
            emit('mercato_contrattazione_risultato', {
                'articolo_id': articolo_id,
                'esito': result_data.get('esito'),
                'messaggio': result_data.get('messaggio'),
                'prezzo_finale': result_data.get('prezzo_finale'),
                'controproposta': result_data.get('controproposta')
            })
            
            # Emetti anche un evento per tutti i client nella stessa sessione
            socketio.emit('mercato_contrattazione_risultato', {
                'articolo_id': articolo_id,
                'esito': result_data.get('esito'),
                'messaggio': result_data.get('messaggio'),
                'prezzo_finale': result_data.get('prezzo_finale'),
                'controproposta': result_data.get('controproposta')
            }, room=room_id)
        else:
            emit('error', {'message': 'Errore nella contrattazione'})
    except Exception as e:
        logger.error(f"Errore nella contrattazione: {e}")
        emit('error', {'message': f'Errore interno: {str(e)}'})

def handle_mercato_prova_abilita(data):
    """
    Gestisce la prova di abilità per la contrattazione
    
    Args:
        data (dict): Contiene id_sessione, articolo_id e tipo_prova
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione', 'articolo_id']):
        return
        
    id_sessione = data['id_sessione']
    articolo_id = data['articolo_id']
    tipo_prova = data.get('tipo_prova', 'contrattazione')
    
    # Crea il room_id per questa sessione
    room_id = f"session_{id_sessione}"
    
    try:
        # Usa l'endpoint per gestire la prova di abilità
        response = requests.post(
            "http://localhost:5000/game/mercato/prova_abilita",
            json={
                "id_sessione": id_sessione,
                "articolo_id": articolo_id,
                "tipo_prova": tipo_prova
            }
        )
        
        if response.status_code == 200:
            result_data = response.json()
            
            # Emetti evento per aggiornare l'interfaccia
            emit('mercato_prova_abilita_risultato', result_data)
            
            # Emetti anche un evento per tutti i client nella stessa sessione
            socketio.emit('mercato_prova_abilita_risultato', result_data, room=room_id)
        else:
            emit('error', {'message': 'Errore nella prova di abilità'})
    except Exception as e:
        logger.error(f"Errore nella prova di abilità: {e}")
        emit('error', {'message': f'Errore interno: {str(e)}'})

def handle_mercato_articoli_disponibili(data):
    """
    Ottiene la lista degli articoli disponibili nel mercato
    
    Args:
        data (dict): Contiene id_sessione e opzionalmente tipo_articolo
    """
    # Valida i dati richiesti
    if not core.validate_request_data(data, ['id_sessione']):
        return
        
    id_sessione = data['id_sessione']
    tipo_articolo = data.get('tipo', 'tutti')
    
    try:
        # Usa l'endpoint per ottenere gli articoli disponibili
        url = f"http://localhost:5000/game/mercato/articoli_disponibili?id_sessione={id_sessione}"
        if tipo_articolo != 'tutti':
            url += f"&tipo={tipo_articolo}"
            
        response = requests.get(url)
        
        if response.status_code == 200:
            result_data = response.json()
            
            # Emetti evento per aggiornare l'interfaccia
            emit('mercato_articoli_disponibili', {
                'articoli': result_data.get('articoli')
            })
        else:
            emit('error', {'message': 'Errore nel recupero degli articoli disponibili'})
    except Exception as e:
        logger.error(f"Errore nel recupero degli articoli disponibili: {e}")
        emit('error', {'message': f'Errore interno: {str(e)}'})

def register_handlers(socketio_instance):
    """
    Registra gli handler WebSocket per il mercato
    
    Args:
        socketio_instance: Istanza SocketIO
    """
    socketio_instance.on_event('mercato_inizializza', handle_mercato_inizializza)
    socketio_instance.on_event('mercato_interagisci', handle_mercato_interagisci)
    socketio_instance.on_event('mercato_dialoga', handle_mercato_dialoga)
    socketio_instance.on_event('mercato_menu', handle_mercato_menu)
    socketio_instance.on_event('mercato_movimento', handle_mercato_movimento)
    socketio_instance.on_event('mercato_transizione', handle_mercato_transizione)
    socketio_instance.on_event('mercato_compra', handle_mercato_compra)
    socketio_instance.on_event('mercato_vendi', handle_mercato_vendi)
    socketio_instance.on_event('mercato_contratta', handle_mercato_contratta)
    socketio_instance.on_event('mercato_prova_abilita', handle_mercato_prova_abilita)
    socketio_instance.on_event('mercato_articoli_disponibili', handle_mercato_articoli_disponibili)
    
    logger.info("Handler WebSocket del mercato registrati") 