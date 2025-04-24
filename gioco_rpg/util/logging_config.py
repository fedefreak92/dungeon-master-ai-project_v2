"""
Configurazione del sistema di logging per il gioco RPG.
Implementa un sistema di logging strutturato e dettagliato per debug.
"""

import logging
import logging.handlers
import os
import time
from pathlib import Path

def configurazione_logging(livello=logging.INFO, log_file=None, console=True, format_detail=True, debug_mode=False):
    """
    Configura il sistema di logging.
    
    Args:
        livello: Livello di logging (default: INFO per migliorare le performance)
        log_file: Percorso al file di log (default: logs/gioco_rpg.log)
        console: Se True, stampa anche su console
        format_detail: Se True, usa un formato dettagliato
        debug_mode: Se True, imposta il livello di logging a DEBUG indipendentemente dal parametro livello
    """
    # Imposta il livello a DEBUG se debug_mode è True
    if debug_mode:
        livello = logging.DEBUG
        print("Modalità DEBUG attivata: maggior verbosità dei log")
    
    # Crea percorso predefinito se non specificato
    if log_file is None:
        # Crea directory logs se non esiste
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Nome file con timestamp
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        log_file = logs_dir / f"gioco_rpg_{timestamp}.log"
    
    # Configura il logger root
    root_logger = logging.getLogger()
    root_logger.setLevel(livello)
    
    # Rimuovi tutti gli handler esistenti
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Crea il formato
    if format_detail:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
    
    # Aggiungi file handler
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=5*1024*1024,  # 5 MB
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Errore nella configurazione del file di log {log_file}: {e}")
        # In caso di errore, crea un file con nome alternativo
        try:
            alt_log_file = Path("gioco_rpg_error.log")
            file_handler = logging.handlers.RotatingFileHandler(
                alt_log_file, 
                maxBytes=5*1024*1024,
                backupCount=1,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"Impossibile configurare il file di log alternativo: {e}")
    
    # Aggiungi console handler se richiesto
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    logging.info("Sistema di logging inizializzato")

def get_logger(name):
    """
    Ottiene un logger configurato per il modulo specificato.
    
    Args:
        name: Nome del modulo
        
    Returns:
        logging.Logger: Logger configurato
    """
    return logging.getLogger(name)

class GameLogger:
    """
    Classe wrapper per il logging specifico del gioco.
    Fornisce metodi per logging standard e speciale.
    """
    
    def __init__(self, name):
        """
        Inizializza il logger.
        
        Args:
            name: Nome del logger
        """
        self.logger = logging.getLogger(name)
    
    def debug(self, message):
        """Log a livello DEBUG"""
        self.logger.debug(message)
    
    def info(self, message):
        """Log a livello INFO"""
        self.logger.info(message)
    
    def warning(self, message):
        """Log a livello WARNING"""
        self.logger.warning(message)
    
    def error(self, message):
        """Log a livello ERROR"""
        self.logger.error(message)
    
    def critical(self, message):
        """Log a livello CRITICAL"""
        self.logger.critical(message)
    
    def game_event(self, event_type, details):
        """
        Log di un evento di gioco.
        
        Args:
            event_type: Tipo di evento
            details: Dettagli dell'evento
        """
        self.logger.info(f"GAME_EVENT: {event_type} - {details}")
    
    def player_action(self, player, action, details=None):
        """
        Log di un'azione del giocatore.
        
        Args:
            player: Giocatore che ha eseguito l'azione
            action: Azione eseguita
            details: Dettagli opzionali
        """
        if details:
            self.logger.info(f"PLAYER_ACTION: {player} - {action} - {details}")
        else:
            self.logger.info(f"PLAYER_ACTION: {player} - {action}")
    
    def npc_action(self, npc, action, details=None):
        """
        Log di un'azione di un NPC.
        
        Args:
            npc: NPC che ha eseguito l'azione
            action: Azione eseguita
            details: Dettagli opzionali
        """
        if details:
            self.logger.info(f"NPC_ACTION: {npc} - {action} - {details}")
        else:
            self.logger.info(f"NPC_ACTION: {npc} - {action}")
    
    def system_event(self, component, event, details=None):
        """
        Log di un evento di sistema.
        
        Args:
            component: Componente che ha generato l'evento
            event: Tipo di evento
            details: Dettagli opzionali
        """
        if details:
            self.logger.info(f"SYSTEM_EVENT: {component} - {event} - {details}")
        else:
            self.logger.info(f"SYSTEM_EVENT: {component} - {event}")
            
    def exception(self, message, exc_info=True):
        """
        Log di un'eccezione.
        
        Args:
            message: Messaggio
            exc_info: Se True, include informazioni sull'eccezione
        """
        self.logger.exception(message, exc_info=exc_info) 