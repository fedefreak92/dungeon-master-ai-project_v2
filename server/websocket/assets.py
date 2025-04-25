"""
Modulo per la gestione di WebSocket per gli asset di gioco.
Fornisce funzionalità per notificare ai client aggiornamenti degli asset
e sincronizzare gli asset in tempo reale.
"""

import logging
import os
from flask import request
from flask_socketio import emit, join_room, leave_room
from pathlib import Path
import traceback

# Import moduli locali
from . import socketio
from util.asset_manager import get_asset_manager
from server.utils.session import sessioni_attive
from server.websocket.core import get_session, validate_request_data

# Configura il logger
logger = logging.getLogger(__name__)

# Room per gli aggiornamenti degli asset (tutti i client interessati agli asset)
ASSETS_ROOM = "assets_updates"

def register_handlers(socketio_instance):
    """
    Registra gli handler per gli eventi WebSocket relativi agli asset.
    
    Args:
        socketio_instance: Istanza SocketIO
    """
    logger.info("Registrazione degli handler per gli asset")
    
    @socketio_instance.on('join_assets_room')
    def handle_join_assets_room(data):
        """
        Gestisce l'ingresso di un client nella room degli asset.
        
        Args:
            data: Dati della richiesta (può contenere id_sessione per collegare la sessione)
        """
        logger.info(f"Client {request.sid} richiede di unirsi alla room degli asset")
        
        # Unisci il client alla room degli asset
        join_room(ASSETS_ROOM)
        
        # Se c'è un id_sessione, associa questo client anche alla sessione
        if 'id_sessione' in data:
            sessione = get_session(data['id_sessione'])
            if sessione:
                logger.info(f"Client {request.sid} associato alla sessione {data['id_sessione']}")
            
        emit('assets_room_joined', {'status': 'success'})
    
    @socketio_instance.on('leave_assets_room')
    def handle_leave_assets_room():
        """Gestisce l'uscita di un client dalla room degli asset."""
        logger.info(f"Client {request.sid} lascia la room degli asset")
        leave_room(ASSETS_ROOM)
        emit('assets_room_left', {'status': 'success'})
    
    @socketio_instance.on('request_assets_sync')
    def handle_request_assets_sync(data):
        """
        Gestisce la richiesta di sincronizzazione degli asset.
        
        Args:
            data: Dati della richiesta che può contenere filtri per i tipi di asset
        """
        logger.info(f"Richiesta sincronizzazione asset da client {request.sid}")
        
        try:
            # Se data è None, inizializza un dizionario vuoto
            if data is None:
                data = {}
                
            # Ottieni l'asset manager
            asset_manager = get_asset_manager()
            
            # Può contenere un filtro per i tipi di asset
            asset_types = data.get('types', None)
            
            # Raccogli le informazioni sugli asset
            assets_info = {}
            
            if not asset_types or 'sprites' in asset_types:
                assets_info['sprites'] = asset_manager.sprites
            
            if not asset_types or 'tiles' in asset_types:
                assets_info['tiles'] = asset_manager.tiles
            
            if not asset_types or 'animations' in asset_types:
                assets_info['animations'] = asset_manager.animations
            
            if not asset_types or 'tilesets' in asset_types:
                assets_info['tilesets'] = asset_manager.tilesets
            
            if not asset_types or 'ui_elements' in asset_types:
                assets_info['ui_elements'] = asset_manager.ui_elements
            
            # Invia i dati al client
            emit('assets_sync', {
                'status': 'success',
                'assets': assets_info
            })
            
            logger.info(f"Inviata sincronizzazione asset al client {request.sid}: {sum(len(v) for v in assets_info.values())} asset totali")
            return True
        except Exception as e:
            logger.error(f"Errore durante la sincronizzazione degli asset: {str(e)}")
            logger.debug(f"Dettaglio errore: {traceback.format_exc()}")
            
            # Invia un messaggio di errore al client
            emit('assets_sync', {
                'status': 'error',
                'message': 'Errore nella sincronizzazione degli asset'
            })
            return False
    
    @socketio_instance.on('update_asset')
    def handle_update_asset(data):
        """
        Gestisce l'aggiornamento di un asset.
        
        Args:
            data: Dati dell'asset da aggiornare
        """
        # Verifica i dati ricevuti
        if not validate_request_data(data, ['type', 'id', 'asset_data']):
            return
        
        logger.info(f"Richiesta aggiornamento asset: {data['type']}/{data['id']}")
        
        # Ottieni l'asset manager
        asset_manager = get_asset_manager()
        
        # Aggiorna l'asset in base al tipo
        updated = False
        
        try:
            if data['type'] == 'sprite':
                # Aggiorna uno sprite
                asset_data = data['asset_data']
                updated = asset_manager.register_sprite(
                    sprite_id=data['id'],
                    name=asset_data.get('name', data['id']),
                    file_path=asset_data.get('path', ''),
                    dimensions=asset_data.get('dimensions', None),
                    offset=asset_data.get('offset', None),
                    tags=asset_data.get('tags', None)
                )
            elif data['type'] == 'tile':
                # Aggiorna un tile
                asset_data = data['asset_data']
                updated = asset_manager.register_tile(
                    tile_id=data['id'],
                    name=asset_data.get('name', data['id']),
                    file_path=asset_data.get('path', ''),
                    dimensions=asset_data.get('dimensions', None),
                    properties=asset_data.get('properties', None),
                    tags=asset_data.get('tags', None)
                )
            elif data['type'] == 'ui':
                # Aggiorna un elemento UI
                asset_data = data['asset_data']
                updated = asset_manager.register_ui_element(
                    ui_id=data['id'],
                    name=asset_data.get('name', data['id']),
                    file_path=asset_data.get('path', ''),
                    dimensions=asset_data.get('dimensions', None),
                    tags=asset_data.get('tags', None)
                )
            
            # Notifica l'aggiornamento a tutti i client nella room degli asset
            if updated:
                # Salva il manifest dopo l'aggiornamento
                asset_manager.save_manifest()
                
                # Notifica a tutti i client nella room degli asset
                socketio_instance.emit('asset_updated', {
                    'type': data['type'],
                    'id': data['id'],
                    'status': 'success'
                }, room=ASSETS_ROOM)
                
                logger.info(f"Asset {data['type']}/{data['id']} aggiornato con successo")
                
                # Risposta al client che ha richiesto l'aggiornamento
                emit('update_asset_response', {
                    'status': 'success',
                    'message': f"Asset {data['type']}/{data['id']} aggiornato con successo"
                })
            else:
                logger.warning(f"Fallimento nell'aggiornamento dell'asset {data['type']}/{data['id']}")
                emit('update_asset_response', {
                    'status': 'error',
                    'message': f"Fallimento nell'aggiornamento dell'asset {data['type']}/{data['id']}"
                })
        
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento dell'asset: {str(e)}")
            emit('update_asset_response', {
                'status': 'error',
                'message': f"Errore nell'aggiornamento dell'asset: {str(e)}"
            })

    @socketio_instance.on('scan_assets')
    def handle_scan_assets():
        """
        Gestisce la scansione completa degli asset.
        Aggiorna tutti gli asset disponibili nel filesystem.
        """
        logger.info(f"Richiesta scansione completa degli asset da client {request.sid}")
        
        # Ottieni l'asset manager
        asset_manager = get_asset_manager()
        
        try:
            # Esegui la scansione completa
            result = asset_manager.update_all()
            
            if result:
                # Notifica a tutti i client nella room degli asset
                socketio_instance.emit('assets_updated', {
                    'status': 'success',
                    'message': 'Asset aggiornati con successo'
                }, room=ASSETS_ROOM)
                
                # Risposta al client che ha richiesto la scansione
                emit('scan_assets_response', {
                    'status': 'success',
                    'message': 'Asset aggiornati con successo',
                    'sprites_count': len(asset_manager.sprites),
                    'tiles_count': len(asset_manager.tiles),
                    'ui_elements_count': len(asset_manager.ui_elements)
                })
            else:
                emit('scan_assets_response', {
                    'status': 'error',
                    'message': 'Errore nella scansione degli asset'
                })
        
        except Exception as e:
            logger.error(f"Errore nella scansione degli asset: {str(e)}")
            emit('scan_assets_response', {
                'status': 'error',
                'message': f"Errore nella scansione degli asset: {str(e)}"
            })

# Funzione di utilità per notificare gli aggiornamenti degli asset alle sessioni attive
def notify_asset_update(asset_type, asset_id):
    """
    Notifica alle sessioni attive che un asset è stato aggiornato.
    
    Args:
        asset_type: Tipo di asset (sprite, tile, ui, ecc.)
        asset_id: ID dell'asset aggiornato
        
    Returns:
        bool: True se la notifica è stata inviata correttamente, False altrimenti
    """
    try:
        # Prova diverse strategie per ottenere un riferimento a socketio
        import sys
        
        # Strategia 1: Utilizzare socketio dal modulo corrente
        current_socketio = getattr(sys.modules.get('server.websocket.assets'), 'socketio', None)
        
        # Strategia 2: Verificare se socketio è disponibile nell'app Flask
        if current_socketio is None:
            logger.info("Tentativo di ottenere socketio dall'app Flask")
            try:
                from server.app import socketio as app_socketio
                current_socketio = app_socketio
                logger.info("Ottenuto socketio dall'app Flask")
            except ImportError:
                logger.warning("Non è stato possibile importare socketio dall'app Flask")
        
        # Strategia 3: Importare flask_socketio SocketIO e tentare di utilizzare l'istanza globale
        if current_socketio is None:
            logger.info("Tentativo di ottenere socketio dalle istanze globali")
            try:
                from flask_socketio import SocketIO
                # Tento di recuperare l'istanza attiva di SocketIO
                from server.utils.session import get_socketio
                current_socketio = get_socketio()
                logger.info(f"Ottenuto socketio dalle istanze globali: {current_socketio is not None}")
            except ImportError:
                logger.warning("Non è stato possibile importare flask_socketio o ottenere l'istanza globale")
        
        # Se socketio non è inizializzato dopo tutti i tentativi, registra un errore
        if current_socketio is None:
            logger.warning(f"Impossibile notificare aggiornamento asset {asset_type}/{asset_id}: socketio non inizializzato dopo tutti i tentativi")
            return False
        
        # Forza l'emissione dell'evento anche a room vuote per assicurarsi che i test vedano l'evento
        logger.info(f"Invio notifica 'asset_updated' per {asset_type}/{asset_id} alla room {ASSETS_ROOM}")
        current_socketio.emit('asset_updated', {
            'type': asset_type,
            'id': asset_id,
            'status': 'success'
        }, room=ASSETS_ROOM, namespace='/')
        
        # Emetti anche su namespace di default senza specificare room per maggiore compatibilità
        if asset_type == 'all':
            logger.info("Invio notifica 'asset_updated' anche senza room specificata (per compatibilità)")
            current_socketio.emit('asset_updated', {
                'type': asset_type, 
                'id': asset_id,
                'status': 'success'
            })
        
        logger.info(f"Notifica aggiornamento asset {asset_type}/{asset_id} inviata a tutti i client")
        return True
    
    except Exception as e:
        logger.error(f"Errore nell'invio della notifica di aggiornamento asset: {str(e)}")
        logger.debug(f"Dettaglio errore: {traceback.format_exc()}")
        return False 