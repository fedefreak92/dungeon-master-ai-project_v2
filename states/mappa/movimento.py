"""
Funzioni relative al movimento del giocatore nella mappa.
"""

import logging
from core.event_bus import EventBus
import core.events as Events

logger = logging.getLogger(__name__)

def sposta_giocatore(stato, gioco, direzione):
    """
    Sposta il giocatore nella direzione specificata.
    Versione legacy mantenuta per retrocompatibilità.
    
    Args:
        stato: Lo stato mappa corrente
        gioco: L'istanza del gioco
        direzione: Direzione in cui muoversi ('nord', 'sud', 'est', 'ovest')
    
    Returns:
        bool: True se il movimento è avvenuto, False altrimenti
    """
    # Ottieni la mappa corrente
    mappa_corrente = gioco.giocatore.mappa_corrente
    mappa = gioco.gestore_mappe.ottieni_mappa(mappa_corrente)
    
    # Verifica che la mappa esista
    if not mappa:
        gioco.io.mostra_messaggio("Errore: mappa non trovata!")
        return False
    
    # Calcola la nuova posizione
    delta_x, delta_y = stato.direzioni.get(direzione, (0, 0))
    nuova_x = gioco.giocatore.x + delta_x
    nuova_y = gioco.giocatore.y + delta_y
    
    # Verifica se la nuova posizione è valida
    if not mappa.posizione_valida(nuova_x, nuova_y):
        gioco.io.mostra_messaggio("Non puoi andare in quella direzione.")
        
        # Emetti evento movimento bloccato
        if hasattr(stato, 'event_bus'):
            stato.event_bus.emit(
                Events.MOVEMENT_BLOCKED,
                entity_id=gioco.giocatore.id,
                from_pos=(gioco.giocatore.x, gioco.giocatore.y),
                to_pos=(nuova_x, nuova_y),
                reason="boundary"
            )
        return False
    
    # Controlla se c'è un oggetto che blocca il passaggio
    if mappa.is_blocked(nuova_x, nuova_y):
        gioco.io.mostra_messaggio("La strada è bloccata. Non puoi procedere.")
        
        # Emetti evento movimento bloccato
        if hasattr(stato, 'event_bus'):
            stato.event_bus.emit(
                Events.MOVEMENT_BLOCKED,
                entity_id=gioco.giocatore.id,
                from_pos=(gioco.giocatore.x, gioco.giocatore.y),
                to_pos=(nuova_x, nuova_y),
                reason="obstacle"
            )
        return False
    
    # Memorizza la vecchia posizione
    vecchia_x, vecchia_y = gioco.giocatore.x, gioco.giocatore.y
    
    # Esegui il movimento
    gioco.giocatore.x = nuova_x
    gioco.giocatore.y = nuova_y
    
    # Aggiorna la posizione nella mappa
    mappa.update_entity_position(gioco.giocatore.id, vecchia_x, vecchia_y, nuova_x, nuova_y)
    
    # Controlla se c'è una porta/passaggio sulla nuova posizione
    porta = mappa.get_porta(nuova_x, nuova_y)
    if porta:
        mappa_dest = porta.get("mappa_destinazione")
        x_dest = porta.get("x_destinazione")
        y_dest = porta.get("y_destinazione")
        
        # Emetti evento map change se disponibile
        if hasattr(stato, 'event_bus'):
            stato.event_bus.emit(
                Events.MAP_CHANGE,
                entity_id=gioco.giocatore.id,
                from_map=mappa_corrente,
                to_map=mappa_dest,
                target_pos=(x_dest, y_dest)
            )
        else:
            # Fallback al vecchio metodo
            gestisci_cambio_mappa(stato, gioco, mappa_corrente, mappa_dest, (x_dest, y_dest))
            
        return True
    
    # Logga il movimento
    gioco.io.mostra_messaggio(f"Ti sei spostato verso {direzione}.")
    
    # Forza aggiornamento UI
    stato.ui_aggiornata = False
    
    # Emetti evento entity moved
    if hasattr(stato, 'event_bus'):
        stato.event_bus.emit(
            Events.ENTITY_MOVED,
            entity_id=gioco.giocatore.id,
            from_pos=(vecchia_x, vecchia_y),
            to_pos=(nuova_x, nuova_y)
        )
    
    # Controlla se ci sono trigger sulla nuova posizione
    check_position_triggers(stato, gioco, nuova_x, nuova_y)
    
    return True

def gestisci_cambio_mappa(stato, gioco, mappa_origine, mappa_destinazione, target_pos=None):
    """
    Gestisce il cambio mappa del giocatore.
    
    Args:
        stato: Lo stato mappa corrente
        gioco: L'istanza del gioco
        mappa_origine: Nome della mappa di origine
        mappa_destinazione: Nome della mappa di destinazione
        target_pos: Tupla (x, y) opzionale con la posizione di destinazione
        
    Returns:
        bool: True se il cambio mappa è avvenuto, False altrimenti
    """
    # Se mappa_destinazione è None, non fare nulla
    if not mappa_destinazione:
        gioco.io.mostra_messaggio("Errore: mappa di destinazione non specificata.")
        return False
    
    # Ottieni la mappa di destinazione
    mappa_dest = gioco.gestore_mappe.ottieni_mappa(mappa_destinazione)
    if not mappa_dest:
        gioco.io.mostra_messaggio(f"Errore: mappa {mappa_destinazione} non trovata!")
        return False
    
    # Determina le coordinate di destinazione
    if target_pos:
        x_dest, y_dest = target_pos
    else:
        # Usa le coordinate di entrata di default della mappa
        x_dest, y_dest = mappa_dest.pos_iniziale_giocatore
    
    # Verifica che la posizione sia valida
    if not mappa_dest.posizione_valida(x_dest, y_dest) or mappa_dest.is_blocked(x_dest, y_dest):
        # Se la posizione non è valida, usa la posizione iniziale
        x_dest, y_dest = mappa_dest.pos_iniziale_giocatore
        gioco.io.mostra_messaggio("La posizione di destinazione non è valida. Utilizzando posizione iniziale.")
    
    # Esegui il cambio mappa
    gioco.cambia_mappa(mappa_destinazione, x_dest, y_dest)
    
    # Mappa vecchia
    if mappa_origine:
        gioco.io.mostra_messaggio(f"Hai lasciato {mappa_origine.upper()}.")
    
    # Mostra messaggio relativo alla nuova mappa
    gioco.io.mostra_messaggio(f"Sei entrato in {mappa_destinazione.upper()}.")
    gioco.io.mostra_messaggio(f"Posizione: ({x_dest}, {y_dest})")
    
    # Forza aggiornamento UI
    stato.ui_aggiornata = False
    
    # Segna mappa come aggiornata per notifica eventi
    stato.mappa_aggiornata = True
    
    return True

def check_position_triggers(stato, gioco, x, y):
    """
    Controlla se ci sono trigger sulla posizione attuale del giocatore.
    
    Args:
        stato: Lo stato mappa corrente
        gioco: L'istanza del gioco
        x, y: Coordinate della posizione da controllare
    """
    mappa_corrente = gioco.giocatore.mappa_corrente
    mappa = gioco.gestore_mappe.ottieni_mappa(mappa_corrente)
    
    if not mappa:
        return
    
    # Ottieni i trigger nella posizione
    triggers = mappa.get_triggers_at(x, y)
    
    for trigger in triggers:
        trigger_id = trigger.get('id', f"trigger_{x}_{y}")
        trigger_type = trigger.get('type', 'generic')
        
        # Emetti evento di trigger attivato
        if hasattr(stato, 'event_bus'):
            stato.event_bus.emit(
                Events.TRIGGER_ACTIVATED,
                trigger_id=trigger_id,
                trigger_type=trigger_type,
                entity_id=gioco.giocatore.id,
                position=(x, y)
            )
        
        # Gestisci tipi specifici di trigger
        if trigger_type == 'trappola':
            damage = trigger.get('damage', 1)
            gioco.giocatore.subisci_danno(damage)
            gioco.io.mostra_messaggio(f"Hai attivato una trappola! Hai subito {damage} danni.")
            
            # Emetti evento di danno
            if hasattr(stato, 'event_bus'):
                stato.event_bus.emit(
                    Events.DAMAGE_TAKEN,
                    entity_id=gioco.giocatore.id,
                    damage=damage,
                    damage_type="trap",
                    source_id=trigger_id
                )
        
        elif trigger_type == 'tesoro':
            if not trigger.get('collected', False):
                trigger['collected'] = True
                contents = trigger.get('contents', [])
                
                gioco.io.mostra_messaggio("Hai trovato un tesoro!")
                if contents:
                    gioco.io.mostra_messaggio(f"Contenuto: {', '.join(item.get('name', 'Oggetto') for item in contents)}")
                    # Aggiungi items all'inventario
                
                # Emetti evento tesoro trovato
                if hasattr(stato, 'event_bus'):
                    stato.event_bus.emit(
                        Events.TREASURE_FOUND,
                        entity_id=gioco.giocatore.id,
                        treasure_id=trigger_id,
                        contents=contents
                    )
        
        elif trigger_type == 'evento':
            event_id = trigger.get('event_id')
            if event_id:
                gioco.io.mostra_messaggio("Si attiva un evento...")
                # Gestisci evento specifico

def gestisci_click_cella(mappa_state, gioco, x, y):
    """
    Gestisce il click su una cella della mappa
    
    Args:
        mappa_state: Istanza di MappaState
        gioco: Oggetto Game
        x: Coordinata X
        y: Coordinata Y
    """
    # Calcola la differenza rispetto alla posizione del giocatore
    dx = x - gioco.giocatore.x
    dy = y - gioco.giocatore.y
    
    # Se è una cella adiacente, prova a muovere il giocatore
    if abs(dx) + abs(dy) == 1:  # Distanza Manhattan = 1
        if dx == 1 and dy == 0:
            sposta_giocatore(mappa_state, gioco, "est")
        elif dx == -1 and dy == 0:
            sposta_giocatore(mappa_state, gioco, "ovest")
        elif dx == 0 and dy == 1:
            sposta_giocatore(mappa_state, gioco, "sud")
        elif dx == 0 and dy == -1:
            sposta_giocatore(mappa_state, gioco, "nord")
    else:
        gioco.io.mostra_messaggio("Non puoi muoverti direttamente in quella posizione.") 