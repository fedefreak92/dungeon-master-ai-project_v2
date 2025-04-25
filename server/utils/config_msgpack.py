"""
Configurazione globale per l'utilizzo di MessagePack nel server.

Questo modulo fornisce funzioni per abilitare/disabilitare e configurare
il supporto MessagePack a livello di applicazione.
"""

import logging
import os

# Configura il logger
logger = logging.getLogger(__name__)

# Impostazione predefinita per l'utilizzo di MessagePack
_use_msgpack = True

# Dimensione minima in byte per usare MessagePack invece di JSON
_msgpack_size_threshold = 1024  # Default: 1KB

def enable_msgpack():
    """
    Abilita l'utilizzo di MessagePack nelle risposte API.
    """
    global _use_msgpack
    _use_msgpack = True
    logger.info("Supporto MessagePack abilitato globalmente")

def disable_msgpack():
    """
    Disabilita l'utilizzo di MessagePack nelle risposte API.
    Verrà utilizzato sempre JSON.
    """
    global _use_msgpack
    _use_msgpack = False
    logger.info("Supporto MessagePack disabilitato globalmente")

def is_msgpack_enabled():
    """
    Verifica se MessagePack è abilitato globalmente.
    
    Returns:
        bool: True se MessagePack è abilitato, False altrimenti
    """
    return _use_msgpack

def set_msgpack_size_threshold(size_bytes):
    """
    Imposta la dimensione minima dei dati (in byte) per cui utilizzare MessagePack.
    Per risposte più piccole di questa soglia verrà sempre utilizzato JSON.
    
    Args:
        size_bytes (int): Dimensione soglia in byte
    """
    global _msgpack_size_threshold
    _msgpack_size_threshold = max(0, size_bytes)
    logger.info(f"Soglia dimensione MessagePack impostata a {_msgpack_size_threshold} bytes")

def get_msgpack_size_threshold():
    """
    Ottiene la soglia di dimensione corrente per l'utilizzo di MessagePack.
    
    Returns:
        int: Dimensione soglia in byte
    """
    return _msgpack_size_threshold

def should_use_msgpack(data_size):
    """
    Determina se utilizzare MessagePack per serializzare dati di una certa dimensione.
    
    Args:
        data_size (int): Dimensione stimata dei dati in byte
        
    Returns:
        bool: True se è preferibile usare MessagePack, False per JSON
    """
    if not _use_msgpack:
        return False
    
    return data_size >= _msgpack_size_threshold

def load_config_from_env():
    """
    Carica la configurazione di MessagePack dalle variabili d'ambiente.
    
    Le variabili supportate sono:
    - MSGPACK_ENABLED: "true"/"false" per abilitare/disabilitare MessagePack
    - MSGPACK_SIZE_THRESHOLD: Valore numerico in byte
    """
    # Controlla se MessagePack è abilitato o disabilitato
    msgpack_enabled = os.environ.get('MSGPACK_ENABLED', '').lower()
    if msgpack_enabled in ('true', 't', '1', 'yes', 'y'):
        enable_msgpack()
    elif msgpack_enabled in ('false', 'f', '0', 'no', 'n'):
        disable_msgpack()
    
    # Imposta la soglia di dimensione
    try:
        threshold = os.environ.get('MSGPACK_SIZE_THRESHOLD')
        if threshold:
            set_msgpack_size_threshold(int(threshold))
    except (ValueError, TypeError):
        logger.warning(f"Valore non valido per MSGPACK_SIZE_THRESHOLD: {os.environ.get('MSGPACK_SIZE_THRESHOLD')}")
    
    logger.info(f"Configurazione MessagePack caricata: abilitato={is_msgpack_enabled()}, soglia={get_msgpack_size_threshold()} bytes")

# Carica la configurazione dalle variabili d'ambiente all'importazione del modulo
load_config_from_env() 