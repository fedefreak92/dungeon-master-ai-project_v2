"""
Middleware per il supporto di MessagePack nelle risposte delle routes.

Questo modulo fornisce funzioni e decoratori per facilitare l'utilizzo di MessagePack
nelle risposte HTTP delle routes Flask.
"""

import logging
import functools
from flask import request, Response, jsonify, current_app
import msgpack

# Configura il logger
logger = logging.getLogger(__name__)

def supports_msgpack(f):
    """
    Decoratore che permette a una route di rispondere con MessagePack se richiesto.
    
    Se l'header Accept del client include 'application/msgpack', la risposta sarà
    in formato MessagePack invece che JSON.
    
    Args:
        f: La funzione view da decorare
        
    Returns:
        La funzione wrapper che gestisce il formato della risposta
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        # Esegui la funzione originale
        result = f(*args, **kwargs)
        
        # Se il risultato è già una Response, ritorna senza modifiche
        if isinstance(result, Response):
            return result
        
        # Estrai i dati e il codice di stato
        if isinstance(result, tuple) and len(result) == 2:
            data, status_code = result
        else:
            data = result
            status_code = 200
        
        # Determina se il client accetta MessagePack
        accept_header = request.headers.get('Accept', '')
        use_msgpack = 'application/msgpack' in accept_header
        
        # Converti la risposta nel formato appropriato
        if use_msgpack:
            try:
                # Se data è un oggetto jsonify, ottieni il dizionario sottostante
                if hasattr(data, 'json') and callable(getattr(data, 'json')):
                    data_dict = data.json
                else:
                    data_dict = data
                
                # Serializza in MessagePack
                msgpack_data = msgpack.packb(data_dict, use_bin_type=True)
                
                # Crea la risposta
                response = Response(
                    msgpack_data,
                    status=status_code,
                    mimetype='application/msgpack'
                )
                
                logger.debug(f"Risposta inviata in formato MessagePack, dimensione: {len(msgpack_data)} bytes")
                return response
            except Exception as e:
                logger.error(f"Errore nella serializzazione MessagePack: {e}")
                # Fallback a JSON in caso di errore
        
        # Se non usiamo MessagePack o c'è stato un errore, usiamo JSON
        if isinstance(data, Response):
            return data
        else:
            return jsonify(data), status_code
    
    return wrapper

def msgpack_response(data, status_code=200):
    """
    Crea una risposta HTTP in formato MessagePack.
    
    Args:
        data: I dati da serializzare in MessagePack
        status_code: Il codice di stato HTTP (default: 200)
        
    Returns:
        Response: Oggetto risposta Flask con i dati MessagePack
    """
    try:
        # Serializza in MessagePack
        msgpack_data = msgpack.packb(data, use_bin_type=True)
        
        # Crea la risposta
        response = Response(
            msgpack_data,
            status=status_code,
            mimetype='application/msgpack'
        )
        
        return response
    except Exception as e:
        logger.error(f"Errore nella creazione della risposta MessagePack: {e}")
        # Fallback a JSON
        return jsonify(data), status_code

def accept_msgpack(f):
    """
    Decoratore che permette a una route di accettare dati MessagePack.
    
    Se il Content-Type del client è 'application/msgpack', i dati della richiesta
    saranno deserializzati da MessagePack e disponibili in request.msgpack_data.
    
    Args:
        f: La funzione view da decorare
        
    Returns:
        La funzione wrapper che gestisce il formato della richiesta
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        # Controlla se la richiesta contiene dati MessagePack
        content_type = request.headers.get('Content-Type', '')
        
        if 'application/msgpack' in content_type:
            try:
                # Deserializza i dati MessagePack
                request.msgpack_data = msgpack.unpackb(request.data, raw=False)
                logger.debug(f"Ricevuti dati MessagePack, dimensione: {len(request.data)} bytes")
            except Exception as e:
                logger.error(f"Errore nella deserializzazione MessagePack: {e}")
                # Non impostare request.msgpack_data in caso di errore
        
        # Esegui la funzione originale
        return f(*args, **kwargs)
    
    return wrapper 