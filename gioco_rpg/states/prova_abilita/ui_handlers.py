"""
Gestori di eventi UI per lo stato di prova abilità.
Contiene funzioni per gestire click e scelte da dialoghi.
"""

from states.prova_abilita.ui import (
    mostra_menu_abilita, 
    mostra_menu_modalita_grafico, 
    esegui_menu_principale,
    mostra_menu_abilita_specifiche,
    seleziona_npg,
    seleziona_npg_confronto,
    seleziona_oggetto,
    mostra_menu_finale
)
from states.prova_abilita.esecuzione import esegui_prova_base_grafica

def gestisci_scelta_dialogo(state, event):
    """
    Handler per le scelte dai dialoghi
    
    Args:
        state: Istanza dello stato ProvaAbilitaState
        event: Evento di scelta da dialogo
    """
    if not hasattr(event, "data") or not event.data:
        return
    
    choice = event.data.get("choice")
    if not choice:
        return
        
    game_ctx = state.gioco
    if not game_ctx:
        return
        
    # Memorizza l'ultima scelta
    state.ultimo_input = choice
    
    # Gestione menu principale
    if state.menu_attivo == "principale":
        if choice == "1. Prova abilità giocatore":
            state.fase = "scegli_abilita"
            mostra_menu_abilita(state, game_ctx)
            state.menu_attivo = "abilita"
        elif choice == "2. Prova abilità NPG":
            seleziona_npg(state, game_ctx)
            state.menu_attivo = "npg"
        elif choice == "3. Prova confronto abilità":
            seleziona_npg_confronto(state, game_ctx)
            state.menu_attivo = "confronto"
        elif choice == "0. Esci":
            if game_ctx.stato_corrente() == state:
                game_ctx.pop_stato()
    
    # Gestione menu abilità
    elif state.menu_attivo == "abilita":
        elabora_scelta_abilita_grafica(state, game_ctx, choice)
    
    # Gestione menu modalità
    elif state.menu_attivo == "modalita":
        elabora_modalita_grafica(state, game_ctx, choice)
        
    # Gestione altre scelte da dialogo in base al menu attivo
    elif state.menu_attivo == "difficolta":
        elabora_scelta_difficolta(state, game_ctx, choice)

def elabora_scelta_abilita_grafica(state, gioco, scelta):
    """
    Elabora la scelta dell'abilità da interfaccia grafica
    
    Args:
        state: Istanza dello stato ProvaAbilitaState
        gioco: Istanza del gioco
        scelta: Scelta fatta dall'utente
    """
    abilita = {
        "1. Forza": "forza",
        "2. Destrezza": "destrezza",
        "3. Costituzione": "costituzione", 
        "4. Intelligenza": "intelligenza",
        "5. Saggezza": "saggezza",
        "6. Carisma": "carisma"
    }
    
    for opzione, valore in abilita.items():
        if scelta.startswith(opzione):
            state.abilita_scelta = valore
            mostra_menu_modalita_grafico(state, gioco)
            return
    
    if scelta.startswith("7."):
        mostra_menu_abilita_specifiche(state, gioco)
        return
    elif scelta.startswith("8."):
        esegui_menu_principale(state, gioco)
        return
        
    # Se arriviamo qui, è una scelta non valida
    gioco.io.mostra_messaggio("Scelta non valida.")
    mostra_menu_abilita(state, gioco)

def elabora_modalita_grafica(state, gioco, scelta):
    """
    Elabora la scelta della modalità da interfaccia grafica
    
    Args:
        state: Istanza dello stato ProvaAbilitaState
        gioco: Istanza del gioco
        scelta: Scelta fatta dall'utente
    """
    if scelta.startswith("1."):
        # Richiedi la difficoltà
        opzioni_difficolta = [
            "5 (Molto facile)", 
            "10 (Facile)", 
            "15 (Medio)", 
            "20 (Difficile)"
        ]
        gioco.io.mostra_dialogo("Imposta Difficoltà", 
                               "Seleziona il livello di difficoltà:", 
                               opzioni_difficolta)
        state.menu_attivo = "difficolta"
    elif scelta.startswith("2."):
        seleziona_npg(state, gioco)
        state.menu_attivo = "npg"
    elif scelta.startswith("3."):
        seleziona_oggetto(state, gioco)
        state.menu_attivo = "oggetto"
    elif scelta.startswith("4."):
        mostra_menu_abilita(state, gioco)
        return

def elabora_scelta_difficolta(state, gioco, scelta):
    """
    Elabora la scelta della difficoltà da interfaccia grafica
    
    Args:
        state: Istanza dello stato ProvaAbilitaState
        gioco: Istanza del gioco
        scelta: Scelta fatta dall'utente
    """
    difficolta = 10  # Default
    
    if scelta.startswith("5"):
        difficolta = 5
    elif scelta.startswith("10"):
        difficolta = 10
    elif scelta.startswith("15"):
        difficolta = 15
    elif scelta.startswith("20"):
        difficolta = 20
    
    state.dati_contestuali["difficolta"] = difficolta
    esegui_prova_base_grafica(state, gioco, difficolta)

def gestisci_evento_click(state, event):
    """
    Handler per eventi di click
    
    Args:
        state: Istanza dello stato ProvaAbilitaState
        event: Evento di click
    """
    if not hasattr(event, "data") or not event.data:
        return
    
    target = event.data.get("target")
    if not target:
        return
        
    game_ctx = state.gioco
    if not game_ctx:
        return
        
    # Gestione click su elementi interattivi
    if target.startswith("oggetto_"):
        obj_id = target.replace("oggetto_", "")
        interagisci_con_oggetto(state, game_ctx, obj_id)
    elif target.startswith("npg_"):
        npc_id = target.replace("npg_", "")
        interagisci_con_npg(state, game_ctx, npc_id)

def interagisci_con_oggetto(state, gioco, obj_id):
    """
    Interagisce con un oggetto
    
    Args:
        state: Istanza dello stato ProvaAbilitaState
        gioco: Istanza del gioco
        obj_id: ID dell'oggetto
    """
    gioco.io.mostra_messaggio(f"Stai interagendo con l'oggetto {obj_id}")
    
    # Mostra menu contestuale per l'oggetto
    gioco.io.mostra_menu_contestuale((10, 10), [
        "Esamina",
        "Raccogli",
        "Usa"
    ])

def interagisci_con_npg(state, gioco, npc_id):
    """
    Interagisce con un NPC
    
    Args:
        state: Istanza dello stato ProvaAbilitaState
        gioco: Istanza del gioco
        npc_id: ID del personaggio
    """
    gioco.io.mostra_messaggio(f"Stai interagendo con il personaggio {npc_id}")
    
    # Mostra dialogo con il personaggio
    gioco.io.mostra_dialogo(f"Dialogo con {npc_id}", 
                           "Cosa vuoi fare?", 
                           ["Parla", "Commercia", "Addio"]) 