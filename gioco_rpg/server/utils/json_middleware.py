"""
Middleware per il supporto JSON standard nelle risposte delle routes Flask.

Questo modulo fornisce funzioni e decoratori per standardizzare l'utilizzo di JSON
nelle risposte HTTP delle routes Flask.
"""

import logging
import functools
from flask import request, Response, jsonify, current_app

# Configura il logger
logger = logging.getLogger(__name__)

def json_response_formatter(f):
    """
    Decoratore che assicura una risposta JSON standardizzata.
    
    Args:
        f: La funzione view da decorare
        
    Returns:
        La funzione wrapper che gestisce il formato della risposta JSON
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
        
        # Usa sempre JSON come formato di risposta
        if isinstance(data, Response):
            return data
        else:
            logger.debug(f"Risposta inviata in formato JSON standard")
            return jsonify(data), status_code
    
    return wrapper

def json_response(data, status_code=200):
    """
    Funzione per creare risposte JSON standardizzate.
    
    Args:
        data: I dati da serializzare in JSON
        status_code: Il codice di stato HTTP (default: 200)
        
    Returns:
        Response: Oggetto risposta Flask con i dati JSON
    """
    try:
        # Usa jsonify per la serializzazione JSON
        json_response = jsonify(data)
        
        # Imposta il codice di stato
        json_response.status_code = status_code
        
        return json_response
    except Exception as e:
        logger.error(f"Errore nella creazione della risposta JSON: {e}")
        # Fallback generico
        return jsonify({"error": "Errore nella serializzazione dei dati"}), 500

def json_request_parser(f):
    """
    Decoratore che facilita l'accesso ai dati JSON della richiesta.
    
    Args:
        f: La funzione view da decorare
        
    Returns:
        La funzione wrapper che gestisce il formato della richiesta JSON
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        # Controlla se la richiesta contiene dati JSON
        content_type = request.headers.get('Content-Type', '')
        
        if 'application/json' in content_type:
            try:
                # I dati JSON sono già disponibili in request.json
                logger.debug(f"Ricevuti dati JSON standard")
            except Exception as e:
                logger.error(f"Errore nell'elaborazione dei dati JSON: {e}")
        
        # Esegui la funzione originale
        return f(*args, **kwargs)
    
    return wrapper

# Sostituisco le linee 101-103 con commenti che spiegano la transizione
# Questi alias sono ora deprecati ma mantenuti per retrocompatibilità
# Reindirizzano ai formattatori JSON standard
supports_msgpack = json_response_formatter  # Deprecato: usa json_response_formatter
msgpack_response = json_response  # Deprecato: usa json_response
accept_msgpack = json_request_parser  # Deprecato: usa json_request_parser 