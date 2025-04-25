"""
Safe Loader - Utility per il caricamento sicuro di dati con gestione degli errori.
"""

import logging
import json
import traceback
from typing import Any, Callable, Optional, TypeVar, Dict

T = TypeVar('T')

class SafeLoader:
    """
    Wrapper che fornisce funzionalità di caricamento sicuro con gestione degli errori e fallback.
    """
    
    @staticmethod
    def safe_load(load_function: Callable[..., T], *args, fallback: Optional[T] = None, **kwargs) -> T:
        """
        Esegue una funzione di caricamento con gestione sicura degli errori.
        
        Args:
            load_function: Funzione di caricamento da eseguire
            *args: Argomenti da passare alla funzione
            fallback: Valore da restituire in caso di errore
            **kwargs: Argomenti keyword da passare alla funzione
            
        Returns:
            Il risultato della funzione o il fallback in caso di errore
        """
        try:
            return load_function(*args, **kwargs)
        except Exception as e:
            function_name = getattr(load_function, '__name__', str(load_function))
            logging.error(f"Errore nell'esecuzione di {function_name}: {str(e)}")
            logging.debug(traceback.format_exc())
            return fallback
    
    @staticmethod
    def safe_json_load(file_path, fallback=None, encoding='utf-8'):
        """
        Carica un file JSON in modo sicuro.
        
        Args:
            file_path: Percorso del file JSON
            fallback: Valore da restituire in caso di errore
            encoding: Encoding del file
            
        Returns:
            Dati JSON o fallback in caso di errore
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Errore nel caricamento del file JSON {file_path}: {str(e)}")
            logging.debug(traceback.format_exc())
            return fallback if fallback is not None else {}
    
    @staticmethod
    def safe_json_save(file_path, data, fallback=False, encoding='utf-8', indent=2):
        """
        Salva dati in un file JSON in modo sicuro.
        
        Args:
            file_path: Percorso del file JSON
            data: Dati da salvare
            fallback: Valore da restituire in caso di errore
            encoding: Encoding del file
            indent: Indentazione JSON
            
        Returns:
            True se il salvataggio è riuscito, fallback altrimenti
        """
        try:
            with open(file_path, 'w', encoding=encoding) as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            return True
        except Exception as e:
            logging.error(f"Errore nel salvataggio del file JSON {file_path}: {str(e)}")
            logging.debug(traceback.format_exc())
            return fallback
    
    @staticmethod
    def safe_dict_get(dictionary: Dict, key, fallback=None):
        """
        Ottiene un valore da un dizionario in modo sicuro.
        
        Args:
            dictionary: Dizionario da cui ottenere il valore
            key: Chiave da cercare
            fallback: Valore da restituire se la chiave non esiste
            
        Returns:
            Valore associato alla chiave o fallback
        """
        try:
            return dictionary[key]
        except (KeyError, TypeError) as e:
            logging.debug(f"Chiave '{key}' non trovata nel dizionario: {str(e)}")
            return fallback
    
    @staticmethod
    def safe_call(func: Callable[..., T], *args, fallback: Optional[T] = None, **kwargs) -> T:
        """
        Esegue una funzione in modo sicuro gestendo le eccezioni.
        
        Args:
            func: Funzione da chiamare
            *args: Argomenti da passare alla funzione
            fallback: Valore da restituire in caso di errore
            **kwargs: Argomenti keyword da passare alla funzione
            
        Returns:
            Il risultato della funzione o il fallback in caso di errore
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            function_name = getattr(func, '__name__', str(func))
            logging.error(f"Errore nella chiamata a {function_name}: {str(e)}")
            logging.debug(traceback.format_exc())
            return fallback 