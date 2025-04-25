"""
Inizializzazione delle prove di abilità nel server
"""

import logging
from server.utils.session import get_session, salva_sessione

# Configura il logger
logger = logging.getLogger(__name__)

def inizializza_prova_abilita_per_sessione(id_sessione):
    """
    Inizializza lo stato prova_abilita per una sessione di gioco
    
    Args:
        id_sessione (str): ID della sessione
    
    Returns:
        bool: True se l'inizializzazione è riuscita, False altrimenti
    """
    try:
        # Ottieni la sessione
        sessione = get_session(id_sessione)
        if not sessione:
            logger.error(f"Sessione {id_sessione} non trovata")
            return False
        
        # Crea uno stato prova_abilita temporaneo se non esiste
        if not sessione.has_temporary_state("prova_abilita"):
            from states.prova_abilita import ProvaAbilitaState
            prova_state = ProvaAbilitaState()
            sessione.set_temporary_state("prova_abilita", prova_state.to_dict())
            logger.info(f"Creato nuovo stato temporaneo prova_abilita per la sessione {id_sessione}")
        
        # Salva la sessione aggiornata
        salva_sessione(id_sessione, sessione)
        
        return True
        
    except Exception as e:
        logger.error(f"Errore durante l'inizializzazione della prova_abilita: {e}")
        return False 