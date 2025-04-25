"""
Funzionalità di interazione per lo stato di prova abilità.
Contiene metodi per interagire con NPG e oggetti.
"""

from util.dado import Dado
from entities.entita import ABILITA_ASSOCIATE

def ottieni_mappa_corrente(state, gioco):
    """
    Ottiene la mappa corrente dal gioco
    
    Args:
        state: Istanza dello stato ProvaAbilitaState
        gioco: Istanza del gioco
        
    Returns:
        La mappa corrente o None se non disponibile
    """
    try:
        return gioco.mappa_corrente
    except AttributeError:
        return None

def ottieni_npg_vicini(state, gioco):
    """
    Ottiene i personaggi non giocanti vicini al giocatore
    
    Args:
        state: Istanza dello stato ProvaAbilitaState
        gioco: Istanza del gioco
        
    Returns:
        dict: Dizionario di NPG vicini {id: npg}
    """
    mappa = ottieni_mappa_corrente(state, gioco)
    if not mappa:
        return {}
        
    # Esempio di logica per trovare NPG vicini, da adattare in base al gioco
    npg_vicini = {}
    pos_giocatore = gioco.giocatore.posizione
    
    for npg_id, npg in mappa.npg.items():
        # Calcola la distanza tra il giocatore e l'NPG (esempio semplificato)
        distanza = abs(npg.posizione[0] - pos_giocatore[0]) + abs(npg.posizione[1] - pos_giocatore[1])
        
        # Se l'NPG è abbastanza vicino (esempio: distanza <= 2 celle)
        if distanza <= 2:
            npg_vicini[npg_id] = npg
    
    return npg_vicini

def ottieni_oggetti_vicini(state, gioco):
    """
    Ottiene gli oggetti vicini al giocatore
    
    Args:
        state: Istanza dello stato ProvaAbilitaState
        gioco: Istanza del gioco
        
    Returns:
        dict: Dizionario di oggetti vicini {id: oggetto}
    """
    mappa = ottieni_mappa_corrente(state, gioco)
    if not mappa:
        return {}
        
    # Esempio di logica per trovare oggetti vicini, da adattare in base al gioco
    oggetti_vicini = {}
    pos_giocatore = gioco.giocatore.posizione
    
    for obj_id, obj in mappa.oggetti.items():
        # Calcola la distanza tra il giocatore e l'oggetto (esempio semplificato)
        distanza = abs(obj.posizione[0] - pos_giocatore[0]) + abs(obj.posizione[1] - pos_giocatore[1])
        
        # Se l'oggetto è abbastanza vicino (esempio: distanza <= 1 cella)
        if distanza <= 1:
            oggetti_vicini[obj_id] = obj
    
    return oggetti_vicini

def esegui_confronto_abilita(state, gioco, entita1, entita2, abilita):
    """
    Esegue un confronto di abilità tra due entità
    
    Args:
        state: Istanza dello stato ProvaAbilitaState
        gioco: Istanza del gioco
        entita1: Prima entità (solitamente il giocatore)
        entita2: Seconda entità (solitamente un NPG)
        abilita: Abilità da confrontare
        
    Returns:
        tuple: (risultato1, risultato2, successo) dove successo è True se entita1 ha vinto
    """
    dado = Dado(20)
    
    # Tiro per la prima entità
    tiro1 = dado.tira()
    if abilita in ABILITA_ASSOCIATE:
        mod1 = entita1.modificatore_abilita(abilita)
    else:
        mod1 = getattr(entita1, abilita)
    risultato1 = tiro1 + mod1
    
    # Tiro per la seconda entità
    tiro2 = dado.tira()
    if abilita in ABILITA_ASSOCIATE:
        mod2 = entita2.modificatore_abilita(abilita)
    else:
        mod2 = getattr(entita2, abilita)
    risultato2 = tiro2 + mod2
    
    # Determinare vincitore
    successo = risultato1 >= risultato2
    
    # Costruisce descrizione dettagliata
    desc1 = f"{tiro1} + {mod1} = {risultato1}"
    desc2 = f"{tiro2} + {mod2} = {risultato2}"
    
    return (desc1, desc2, successo)

def interagisci_con_oggetto_specifico(state, gioco, oggetto, abilita):
    """
    Interagisce con un oggetto specifico usando un'abilità
    
    Args:
        state: Istanza dello stato ProvaAbilitaState
        gioco: Istanza del gioco
        oggetto: Oggetto con cui interagire
        abilita: Abilità da usare
        
    Returns:
        tuple: (risultato, successo, messaggio)
    """
    # Imposta contesto
    state.contesto["tipo"] = "oggetto"
    state.contesto["oggetto"] = oggetto
    
    # Ottieni difficoltà dell'oggetto
    difficolta = getattr(oggetto, "difficolta", 10)
    
    # Esegui la prova
    dado = Dado(20)
    tiro = dado.tira()
    
    # Ottieni il modificatore
    if abilita in ABILITA_ASSOCIATE:
        mod = gioco.giocatore.modificatore_abilita(abilita)
    else:
        mod = getattr(gioco.giocatore, abilita)
        
    risultato = tiro + mod
    
    # Determina successo
    successo = risultato >= difficolta
    
    # Descrizione del risultato
    messaggio = f"{gioco.giocatore.nome} tira {tiro} + {mod} = {risultato} vs difficoltà {difficolta}"
    
    # Gestisci effetti dell'interazione
    if successo:
        # Attiva effetti dell'oggetto se ci sono
        if hasattr(oggetto, "attiva_effetto") and callable(getattr(oggetto, "attiva_effetto")):
            oggetto.attiva_effetto(gioco, gioco.giocatore)
    else:
        # Gestisci eventuali penalità
        if hasattr(oggetto, "penalita") and oggetto.penalita > 0:
            state.contesto["penalita"] = oggetto.penalita
            
    return (risultato, successo, messaggio)

def interagisci_con_npg_specifico(state, gioco, npg, abilita):
    """
    Interagisce con un NPG specifico usando un'abilità
    
    Args:
        state: Istanza dello stato ProvaAbilitaState
        gioco: Istanza del gioco
        npg: Personaggio non giocante
        abilita: Abilità da usare
        
    Returns:
        tuple: (risultato1, risultato2, successo, messaggio)
    """
    # Imposta contesto
    state.contesto["tipo"] = "npg"
    state.contesto["npg"] = npg
    
    # Esegui il confronto
    desc1, desc2, successo = esegui_confronto_abilita(state, gioco, gioco.giocatore, npg, abilita)
    
    # Messaggio del risultato
    messaggio = f"Confronto di {abilita} tra {gioco.giocatore.nome} e {npg.nome}:\n"
    messaggio += f"{gioco.giocatore.nome}: {desc1}\n"
    messaggio += f"{npg.nome}: {desc2}\n"
    messaggio += f"Risultato: {'Successo!' if successo else 'Fallimento!'}"
    
    return (desc1, desc2, successo, messaggio) 