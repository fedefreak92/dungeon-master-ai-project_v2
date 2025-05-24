"""
Inizializzazione della taverna nel server
"""

import json
import logging
import os
from server.utils.session import get_session, salva_sessione

# Configura il logger
logger = logging.getLogger(__name__)

def inizializza_taverna(id_sessione):
    """
    Funzione wrapper per retrocompatibilità
    
    Args:
        id_sessione (str): ID della sessione
    
    Returns:
        bool: True se l'inizializzazione è riuscita, False altrimenti
    """
    return inizializza_taverna_per_sessione(id_sessione)

def inizializza_taverna_per_sessione(id_sessione):
    """
    Inizializza lo stato taverna per una sessione di gioco
    
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
        
        # Crea uno stato taverna se non esiste
        if not sessione.has_state("taverna"):
            # Assicurati che l'IO sia inizializzato prima di creare lo stato taverna
            if not hasattr(sessione, 'io') or sessione.io is None:
                logger.warning(f"L'interfaccia IO non è inizializzata nella sessione {id_sessione}, la creo ora")
                from core.io_interface import IOInterface
                sessione.io = IOInterface(sessione)
                
            from states.taverna import TavernaState
            taverna_state = TavernaState(nome_luogo="taverna")
            sessione.add_state("taverna", taverna_state)
            logger.info(f"Creato nuovo stato taverna per la sessione {id_sessione}")
        
        # Ottieni lo stato taverna
        taverna_state = sessione.get_state("taverna")
        
        # Inizializza la mappa, se necessario
        if not sessione.gestore_mappe.map_exists("taverna"):
            _configura_mappa_taverna(sessione)
        
        # Inizializza la posizione del giocatore nella mappa
        if not taverna_state.prima_visita:
            mappa = sessione.gestore_mappe.ottieni_mappa("taverna")
            if mappa:
                # Imposta la posizione iniziale solo se non è già impostata
                giocatore = sessione.giocatore
                if giocatore and not giocatore.has_position("taverna"):
                    x, y = mappa.pos_iniziale_giocatore if hasattr(mappa, "pos_iniziale_giocatore") else (5, 5)
                    giocatore.imposta_posizione("taverna", x, y)
        
        # Salva la sessione aggiornata
        salva_sessione(id_sessione, sessione)
        
        return True
    except Exception as e:
        logger.error(f"Errore nell'inizializzazione della taverna: {e}")
        return False

def _configura_mappa_taverna(sessione):
    """
    Configura la mappa della taverna
    
    Args:
        sessione: Sessione di gioco
    """
    try:
        # Crea una mappa base per la taverna
        from world.mappa import GameMap
        
        mappa_taverna = GameMap("taverna", 20, 15)
        mappa_taverna.pos_iniziale_giocatore = (10, 7)
        
        # Aggiungi pareti e ostacoli
        for x in range(20):
            mappa_taverna.set_cell(x, 0, "muro")
            mappa_taverna.set_cell(x, 14, "muro")
        
        for y in range(15):
            mappa_taverna.set_cell(0, y, "muro")
            mappa_taverna.set_cell(19, y, "muro")
        
        # Aggiungi elementi della taverna
        mappa_taverna.set_cell(10, 3, "bancone")
        mappa_taverna.set_cell(11, 3, "bancone")
        mappa_taverna.set_cell(12, 3, "bancone")
        
        mappa_taverna.set_cell(3, 5, "tavolo")
        mappa_taverna.set_cell(16, 5, "tavolo")
        mappa_taverna.set_cell(3, 10, "tavolo")
        mappa_taverna.set_cell(16, 10, "tavolo")
        
        mappa_taverna.set_cell(5, 2, "camino")
        
        # Posiziona gli NPC
        mappa_taverna.add_entity(11, 2, "NPC", {"nome": "Durnan", "tipo": "locandiere"})
        mappa_taverna.add_entity(3, 6, "NPC", {"nome": "Elminster", "tipo": "mago"})
        mappa_taverna.add_entity(16, 11, "NPC", {"nome": "Mirt", "tipo": "mercante"})
        
        # Aggiungi eventi alle celle
        mappa_taverna.add_event(12, 14, "exit", {"destinazione": "mappa_mondo", "x": 50, "y": 50})
        mappa_taverna.add_event(5, 2, "interazione", {"oggetto_id": "camino"})
        mappa_taverna.add_event(10, 3, "dialogo", {"npg_nome": "Durnan"})
        
        # Registra la mappa nel gestore mappe
        sessione.gestore_mappe.register_map(mappa_taverna)
        logger.info("Mappa della taverna configurata con successo")
    except Exception as e:
        logger.error(f"Errore nella configurazione della mappa della taverna: {e}")
        raise

def sincronizza_stato_taverna(sessione):
    """
    Sincronizza lo stato della taverna con la mappa
    
    Args:
        sessione: Sessione di gioco
    """
    try:
        # Ottieni lo stato taverna
        taverna_state = sessione.get_state("taverna")
        if not taverna_state:
            logger.warning("Stato taverna non trovato durante la sincronizzazione")
            return
        
        # Ottieni la mappa della taverna
        mappa = sessione.gestore_mappe.ottieni_mappa("taverna")
        if not mappa:
            logger.warning("Mappa della taverna non trovata durante la sincronizzazione")
            return
        
        # Sincronizza gli NPC
        entita_mappa = mappa.get_entities()
        for entita in entita_mappa:
            if entita["tipo"] == "NPC" and entita["properties"]["nome"] in taverna_state.npg_presenti:
                npg = taverna_state.npg_presenti[entita["properties"]["nome"]]
                npg.posizione = (entita["x"], entita["y"])
        
        # Sincronizza gli oggetti interattivi
        for oggetto_id, oggetto in taverna_state.oggetti_interattivi.items():
            for y in range(mappa.height):
                for x in range(mappa.width):
                    evento = mappa.get_event_at(x, y)
                    if evento and evento.get("tipo") == "interazione" and evento.get("oggetto_id") == oggetto_id:
                        oggetto.posizione = (x, y)
        
        logger.info("Stato taverna sincronizzato con successo")
    except Exception as e:
        logger.error(f"Errore nella sincronizzazione dello stato taverna: {e}") 