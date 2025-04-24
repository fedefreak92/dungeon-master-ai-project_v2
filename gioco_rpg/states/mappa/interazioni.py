"""
Funzioni per gestire le interazioni del giocatore con elementi della mappa.
"""

import logging
from core.event_bus import EventBus
import core.events as Events

logger = logging.getLogger(__name__)

def interagisci_con_oggetto(stato, gioco):
    """
    Gestisce l'interazione con un oggetto adiacente al giocatore.
    
    Args:
        stato: Lo stato mappa corrente
        gioco: L'istanza del gioco
        
    Returns:
        bool: True se l'interazione è avvenuta, False altrimenti
    """
    # Ottieni la mappa corrente
    mappa_corrente = gioco.giocatore.mappa_corrente
    mappa = gioco.gestore_mappe.ottieni_mappa(mappa_corrente)
    
    if not mappa:
        gioco.io.mostra_messaggio("Errore: mappa non trovata.")
        return False
    
    # Ottieni oggetti adiacenti
    oggetti_adiacenti = gioco.giocatore.ottieni_oggetti_vicini(gioco.gestore_mappe, 1)
    
    if not oggetti_adiacenti:
        gioco.io.mostra_messaggio("Non ci sono oggetti con cui interagire nelle vicinanze.")
        return False
    
    # Mostra finestra di dialogo con lista di oggetti
    opzioni = [obj.nome for obj in oggetti_adiacenti.values()]
    gioco.io.mostra_dialogo("Oggetti Vicini", "Con quale oggetto vuoi interagire?", opzioni + ["Annulla"])
    
    # Memorizza oggetti per l'handler di dialogo
    stato.dati_contestuali = {"oggetti_adiacenti": oggetti_adiacenti}
    stato.ultima_scelta = "interagisci_oggetto"
    
    # Emetti evento di interazione iniziata
    if hasattr(stato, 'event_bus'):
        stato.event_bus.emit(
            Events.PLAYER_INTERACT,
            interaction_type="object",
            objects=list(oggetti_adiacenti.keys()),
            map_name=mappa_corrente
        )
    
    return True

def interagisci_con_npg(stato, gioco):
    """
    Gestisce l'interazione con un NPC adiacente al giocatore.
    
    Args:
        stato: Lo stato mappa corrente
        gioco: L'istanza del gioco
        
    Returns:
        bool: True se l'interazione è avvenuta, False altrimenti
    """
    # Ottieni la mappa corrente
    mappa_corrente = gioco.giocatore.mappa_corrente
    mappa = gioco.gestore_mappe.ottieni_mappa(mappa_corrente)
    
    if not mappa:
        gioco.io.mostra_messaggio("Errore: mappa non trovata.")
        return False
    
    # Ottieni NPC adiacenti
    npg_adiacenti = gioco.giocatore.ottieni_npg_vicini(gioco.gestore_mappe, 1)
    
    if not npg_adiacenti:
        gioco.io.mostra_messaggio("Non ci sono personaggi con cui parlare nelle vicinanze.")
        return False
    
    # Mostra finestra di dialogo con lista di NPC
    opzioni = [npg.nome for npg in npg_adiacenti.values()]
    gioco.io.mostra_dialogo("Personaggi Vicini", "Con chi vuoi parlare?", opzioni + ["Annulla"])
    
    # Memorizza NPC per l'handler di dialogo
    stato.dati_contestuali = {"npg_adiacenti": npg_adiacenti}
    stato.ultima_scelta = "interagisci_npg"
    
    # Emetti evento di interazione iniziata
    if hasattr(stato, 'event_bus'):
        stato.event_bus.emit(
            Events.PLAYER_INTERACT,
            interaction_type="npc",
            npcs=list(npg_adiacenti.keys()),
            map_name=mappa_corrente
        )
    
    return True

def esamina_area(stato, gioco):
    """
    Esamina l'area circostante per trovare oggetti o NPC.
    
    Args:
        stato: Lo stato mappa corrente
        gioco: L'istanza del gioco
    """
    # Ottieni la mappa corrente
    mappa_corrente = gioco.giocatore.mappa_corrente
    mappa = gioco.gestore_mappe.ottieni_mappa(mappa_corrente)
    
    if not mappa:
        gioco.io.mostra_messaggio("Errore: mappa non trovata.")
        return
    
    # Ottieni oggetti vicini
    oggetti_vicini = gioco.giocatore.ottieni_oggetti_vicini(gioco.gestore_mappe, 2)
    
    # Ottieni NPC vicini
    npg_vicini = gioco.giocatore.ottieni_npg_vicini(gioco.gestore_mappe, 2)
    
    # Mostra i risultati
    gioco.io.mostra_messaggio("\n=== AREA CIRCOSTANTE ===")
    
    if oggetti_vicini:
        gioco.io.mostra_messaggio("Oggetti nelle vicinanze:")
        for obj_id, obj in oggetti_vicini.items():
            x_diff = obj.x - gioco.giocatore.x
            y_diff = obj.y - gioco.giocatore.y
            direzione = determina_direzione(x_diff, y_diff)
            gioco.io.mostra_messaggio(f"- {obj.nome} ({direzione})")
    else:
        gioco.io.mostra_messaggio("Non ci sono oggetti nelle vicinanze.")
    
    if npg_vicini:
        gioco.io.mostra_messaggio("\nPersonaggi nelle vicinanze:")
        for npg_id, npg in npg_vicini.items():
            x_diff = npg.x - gioco.giocatore.x
            y_diff = npg.y - gioco.giocatore.y
            direzione = determina_direzione(x_diff, y_diff)
            gioco.io.mostra_messaggio(f"- {npg.nome} ({direzione})")
    else:
        gioco.io.mostra_messaggio("Non ci sono personaggi nelle vicinanze.")
    
    # Emetti evento di area esaminata
    if hasattr(stato, 'event_bus'):
        stato.event_bus.emit(
            Events.PLAYER_INTERACT,
            interaction_type="area",
            objects=list(oggetti_vicini.keys()) if oggetti_vicini else [],
            npcs=list(npg_vicini.keys()) if npg_vicini else [],
            range=2,
            map_name=mappa_corrente
        )

def determina_direzione(x_diff, y_diff):
    """
    Determina la direzione in base alla differenza di coordinate.
    
    Args:
        x_diff: Differenza in x
        y_diff: Differenza in y
        
    Returns:
        str: Direzione (nord, sud, est, ovest, nord-est, ecc.)
    """
    if x_diff == 0 and y_diff < 0:
        return "nord"
    elif x_diff == 0 and y_diff > 0:
        return "sud"
    elif x_diff > 0 and y_diff == 0:
        return "est"
    elif x_diff < 0 and y_diff == 0:
        return "ovest"
    elif x_diff > 0 and y_diff < 0:
        return "nord-est"
    elif x_diff < 0 and y_diff < 0:
        return "nord-ovest"
    elif x_diff > 0 and y_diff > 0:
        return "sud-est"
    elif x_diff < 0 and y_diff > 0:
        return "sud-ovest"
    else:
        return "qui"

def torna_indietro(stato, gioco):
    """
    Torna allo stato precedente.
    
    Args:
        stato: Lo stato mappa corrente
        gioco: L'istanza del gioco
    """
    # Emetti evento di uscita dalla mappa
    if hasattr(stato, 'event_bus'):
        stato.event_bus.emit(
            Events.POP_STATE
        )
    else:
        # Retrocompatibilità
        gioco.pop_stato()
    
    gioco.io.mostra_messaggio("Stai tornando indietro...")

def gestisci_interazione_oggetto(stato, gioco, oggetto_id):
    """
    Gestisce l'interazione con un oggetto specifico.
    
    Args:
        stato: Lo stato mappa corrente
        gioco: L'istanza del gioco
        oggetto_id: ID dell'oggetto con cui interagire
        
    Returns:
        bool: True se l'interazione è avvenuta, False altrimenti
    """
    # Ottieni la mappa corrente
    mappa_corrente = gioco.giocatore.mappa_corrente
    mappa = gioco.gestore_mappe.ottieni_mappa(mappa_corrente)
    
    if not mappa:
        gioco.io.mostra_messaggio("Errore: mappa non trovata.")
        return False
    
    # Ottieni l'oggetto
    oggetto = mappa.oggetti.get(oggetto_id)
    
    if not oggetto:
        gioco.io.mostra_messaggio("L'oggetto non è più disponibile.")
        return False
    
    # Gestisci l'interazione in base al tipo di oggetto
    if oggetto.tipo == "porta":
        gioco.io.mostra_messaggio(f"Hai aperto la porta verso {oggetto.destinazione}.")
        
        # Emetti evento di cambio mappa
        if hasattr(stato, 'event_bus'):
            stato.event_bus.emit(
                Events.MAP_CHANGE,
                entity_id=gioco.giocatore.id,
                from_map=mappa_corrente,
                to_map=oggetto.destinazione,
                target_pos=oggetto.coordinate_destinazione
            )
        
    elif oggetto.tipo == "chest":
        gioco.io.mostra_messaggio(f"Hai aperto il forziere e trovato: {oggetto.contenuto}.")
        
        # Emetti evento di tesoro trovato
        if hasattr(stato, 'event_bus'):
            stato.event_bus.emit(
                Events.TREASURE_FOUND,
                entity_id=gioco.giocatore.id,
                treasure_id=oggetto_id,
                contents=oggetto.contenuto
            )
        
    elif oggetto.tipo == "lever":
        gioco.io.mostra_messaggio(f"Hai azionato la leva: {oggetto.descrizione}")
        
        # Emetti evento di trigger attivato
        if hasattr(stato, 'event_bus'):
            stato.event_bus.emit(
                Events.TRIGGER_ACTIVATED,
                trigger_id=oggetto_id,
                trigger_type="lever",
                entity_id=gioco.giocatore.id,
                position=(oggetto.x, oggetto.y)
            )
        
    else:
        gioco.io.mostra_messaggio(f"Hai esaminato: {oggetto.descrizione}")
    
    return True 