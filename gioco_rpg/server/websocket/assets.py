"""
Modulo per la gestione di WebSocket per gli asset di gioco.
Fornisce funzionalità per notificare ai client aggiornamenti degli asset
e sincronizzare gli asset in tempo reale.
"""

import logging
import os
import time
import json
from flask import request
from flask_socketio import emit, join_room, leave_room
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

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
        
        # Verifica la validità dei dati (opzionale)
        if data is None:
            data = {}
        
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
                e la versione del client per sincronizzazione differenziale
        """
        # Se data è None, inizializza un dizionario vuoto
        if data is None:
            data = {}
            
        # Ottieni l'asset manager
        asset_manager = get_asset_manager()
        
        # Estrai parametri dal client
        asset_types = data.get('types', None)  # Tipi di asset richiesti
        client_version = data.get('version', 0)  # Versione del client
        
        # Timestamp attuale (usato come versione)
        current_version = int(asset_manager.manifest.get("last_updated", time.time()))
        
        # Determina se inviare tutti gli asset o solo quelli modificati
        is_differential = client_version > 0 and client_version < current_version
        
        # Raccogli le informazioni sugli asset
        assets_info = _get_assets_info(asset_manager, asset_types, is_differential, client_version)
        
        # Invia tutti i dati in una sola risposta
        emit('assets_sync', {
            'status': 'success',
            'current_version': current_version,
            'is_differential': is_differential,
            'assets': assets_info
        })
        
        logger.info(f"Inviata sincronizzazione asset al client {request.sid}")
    
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
        
        # Utilizza un metodo di helper per aggiornare l'asset
        updated = _update_asset(asset_manager, data['type'], data['id'], data['asset_data'])
        
        # Notifica l'aggiornamento a tutti i client nella room degli asset
        if updated:
            # Salva il manifest dopo l'aggiornamento
            asset_manager.save_manifest()
            
            # Notifica a tutti i client nella room degli asset
            socketio_instance.emit('asset_updated', {
                'type': data['type'],
                'id': data['id'],
                'status': 'success',
                'timestamp': time.time()
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

    @socketio_instance.on('scan_assets')
    def handle_scan_assets():
        """
        Gestisce la scansione completa degli asset.
        Aggiorna tutti gli asset disponibili nel filesystem.
        """
        logger.info(f"Richiesta scansione completa degli asset da client {request.sid}")
        
        # Ottieni l'asset manager
        asset_manager = get_asset_manager()
        
        # Esegui la scansione completa
        result = asset_manager.update_all()
        
        if result:
            # Ottieni la nuova versione
            current_version = int(asset_manager.manifest.get("last_updated", time.time()))
            
            # Notifica a tutti i client nella room degli asset
            socketio_instance.emit('assets_updated', {
                'status': 'success',
                'message': 'Asset aggiornati con successo',
                'version': current_version,
                'timestamp': time.time()
            }, room=ASSETS_ROOM)
            
            # Risposta al client che ha richiesto la scansione
            emit('scan_assets_response', {
                'status': 'success',
                'message': 'Asset aggiornati con successo',
                'version': current_version,
                'sprites_count': len(asset_manager.sprites),
                'tiles_count': len(asset_manager.tiles),
                'ui_elements_count': len(asset_manager.ui_elements)
            })
        else:
            emit('scan_assets_response', {
                'status': 'error',
                'message': 'Errore nella scansione degli asset'
            })

def _get_assets_info(asset_manager, asset_types=None, is_differential=False, client_version=0):
    """
    Ottiene le informazioni sugli asset, filtrando per tipo e versione.
    
    Args:
        asset_manager: Istanza dell'AssetManager
        asset_types: Lista dei tipi di asset richiesti
        is_differential: Se inviare solo le modifiche dalla versione del client
        client_version: Versione del client
        
    Returns:
        dict: Dizionario con le informazioni sugli asset
    """
    assets_info = {}
    
    # Tipi di asset da includere
    if not asset_types:
        asset_types = ["sprites", "tiles", "animations", "tilesets", "ui_elements"]
    
    # Per ogni tipo di asset
    for asset_type in asset_types:
        # Controlla il tipo di asset e ottieni i dati corrispondenti
        if asset_type == "sprites":
            all_assets = asset_manager.sprites
        elif asset_type == "tiles":
            all_assets = asset_manager.tiles
        elif asset_type == "animations":
            all_assets = asset_manager.animations
        elif asset_type == "tilesets":
            all_assets = asset_manager.tilesets
        elif asset_type == "ui_elements":
            all_assets = asset_manager.ui_elements
        else:
            # Tipo non supportato
            continue
        
        # Filtra gli asset per versione se necessario
        if is_differential:
            filtered_assets = {}
            for asset_id, asset_data in all_assets.items():
                # Se l'asset ha un timestamp di modifica, controlla se è più recente della versione del client
                asset_timestamp = asset_data.get("last_updated", 0)
                if asset_timestamp == 0 or asset_timestamp > client_version:
                    filtered_assets[asset_id] = asset_data
            assets_info[asset_type] = filtered_assets
        else:
            # Nessun filtro, invia tutti gli asset
            assets_info[asset_type] = all_assets
    
    return assets_info

def _update_asset(asset_manager, asset_type, asset_id, asset_data):
    """
    Aggiorna un asset nell'asset manager.
    
    Args:
        asset_manager: Istanza dell'AssetManager
        asset_type: Tipo di asset
        asset_id: ID dell'asset
        asset_data: Dati dell'asset
        
    Returns:
        bool: True se l'aggiornamento è riuscito, False altrimenti
    """
    # Aggiorna il timestamp di modifica
    asset_data["last_updated"] = time.time()
    
    # Aggiorna l'asset in base al tipo
    if asset_type == "sprite":
        # Aggiorna uno sprite
        return asset_manager.register_sprite(
            sprite_id=asset_id,
            name=asset_data.get('name', asset_id),
            file_path=asset_data.get('path', ''),
            dimensions=asset_data.get('dimensions', None),
            offset=asset_data.get('offset', None),
            tags=asset_data.get('tags', None)
        )
    elif asset_type == "tile":
        # Aggiorna un tile
        return asset_manager.register_tile(
            tile_id=asset_id,
            name=asset_data.get('name', asset_id),
            file_path=asset_data.get('path', ''),
            dimensions=asset_data.get('dimensions', None),
            properties=asset_data.get('properties', None),
            tags=asset_data.get('tags', None)
        )
    elif asset_type == "ui":
        # Aggiorna un elemento UI
        return asset_manager.register_ui_element(
            ui_id=asset_id,
            name=asset_data.get('name', asset_id),
            file_path=asset_data.get('path', ''),
            dimensions=asset_data.get('dimensions', None),
            tags=asset_data.get('tags', None)
        )
    else:
        logger.warning(f"Tipo di asset non supportato: {asset_type}")
        return False

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
    # Usa direttamente il modulo socketio importato
    if not socketio:
        logger.error("socketio non inizializzato")
        return False
    
    # Aggiungi timestamp alla notifica
    timestamp = time.time()
    
    # Forza l'emissione dell'evento anche a room vuote per assicurarsi che i test vedano l'evento
    logger.info(f"Invio notifica 'asset_updated' per {asset_type}/{asset_id} alla room {ASSETS_ROOM}")
    socketio.emit('asset_updated', {
        'type': asset_type,
        'id': asset_id,
        'status': 'success',
        'timestamp': timestamp
    }, room=ASSETS_ROOM, namespace='/')
    
    # Emetti anche su namespace di default senza specificare room per maggiore compatibilità
    if asset_type == 'all':
        logger.info("Invio notifica 'asset_updated' anche senza room specificata (per compatibilità)")
        socketio.emit('asset_updated', {
            'type': asset_type, 
            'id': asset_id,
            'status': 'success',
            'timestamp': timestamp
        })
    
    logger.info(f"Notifica aggiornamento asset {asset_type}/{asset_id} inviata a tutti i client")
    return True 