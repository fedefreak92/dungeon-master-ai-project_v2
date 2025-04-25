"""
Funzionalità di esecuzione delle prove di abilità.
Contiene metodi per eseguire prove e gestire i risultati.
"""

from util.dado import Dado
from entities.entita import ABILITA_ASSOCIATE
from states.prova_abilita.ui import mostra_risultato_prova

def esegui_prova_base_grafica(state, gioco, difficolta):
    """
    Esegue una prova base con interfaccia grafica
    
    Args:
        state: Istanza dello stato ProvaAbilitaState
        gioco: Istanza del gioco
        difficolta: Valore di difficoltà della prova
    """
    dado = Dado(20)
    tiro = dado.tira()
    
    # Ottieni il modificatore in base al tipo di abilità
    if state.abilita_scelta in ABILITA_ASSOCIATE:
        # Per abilità specifiche, usa il metodo modificatore_abilita
        modificatore = gioco.giocatore.modificatore_abilita(state.abilita_scelta)
    else:
        # Per caratteristiche base, usa l'attributo diretto
        modificatore = getattr(gioco.giocatore, state.abilita_scelta)
        
    risultato = tiro + modificatore
    
    # Crea il messaggio
    messaggio = f"{gioco.giocatore.nome} tira un {tiro} + {modificatore} ({state.abilita_scelta}) = {risultato}\n"
    messaggio += f"Difficoltà: {difficolta}\n\n"
    
    # Determina successo/fallimento
    successo = risultato >= difficolta
    if successo:
        messaggio += f"Hai superato la prova di {state.abilita_scelta}!"
        state._gestisci_successo(gioco, state.abilita_scelta)
    else:
        messaggio += f"Hai fallito la prova di {state.abilita_scelta}."
        state._gestisci_fallimento(gioco, state.abilita_scelta)
        
    # Mostra il risultato come dialogo
    gioco.io.mostra_dialogo("Risultato Prova", messaggio, ["Continua"])
    state.menu_attivo = "risultato"

def esegui_prova_avanzata(state, entita, abilita, gioco):
    """
    Esegue una prova di abilità avanzata con più dettagli
    
    Args:
        state: Istanza dello stato ProvaAbilitaState
        entita: Entità che esegue la prova
        abilita: Abilità da mettere alla prova
        gioco: Istanza del gioco
    """
    game_ctx = gioco if gioco else getattr(state, 'gioco', None)
    
    game_ctx.io.mostra_messaggio(f"\nProva di {abilita} per {entita.nome}:")
    
    # Ottieni la difficoltà (CD) tramite dialogo con opzioni predefinite
    difficolta_opzioni = ["5 (Molto facile)", "10 (Facile)", "15 (Medio)", "20 (Difficile)", "25 (Molto difficile)"]
    game_ctx.io.mostra_dialogo("Imposta Difficoltà", "Seleziona il livello di difficoltà:", difficolta_opzioni)
    
    # Useremo una difficoltà di default in attesa dell'input dell'utente
    difficolta = 10  # Valore predefinito mentre attendiamo la selezione dell'utente
    state.dati_contestuali["difficolta"] = difficolta
    state.dati_contestuali["entita"] = entita
    state.dati_contestuali["abilita"] = abilita
    
    # La difficoltà verrà impostata dal gestore eventi quando l'utente selezionerà un'opzione
    state.menu_attivo = "difficolta_avanzata"

def gestisci_successo(state, gioco, abilita):
    """
    Gestisce gli effetti del successo nella prova
    
    Args:
        state: Istanza dello stato ProvaAbilitaState
        gioco: Istanza del gioco
        abilita: Abilità messa alla prova
    """
    messaggio = ""
    
    if state.contesto.get("tipo") == "oggetto":
        oggetto = state.contesto.get("oggetto")
        if oggetto:
            messaggio += f"Sei riuscito a interagire correttamente con {oggetto.nome}!\n"
            
    # Piccola ricompensa per il successo
    exp = 5
    if gioco.giocatore.guadagna_esperienza(exp, gioco):
        messaggio += f"Hai guadagnato {exp} punti esperienza e sei salito di livello!"
    else:
        messaggio += f"Hai guadagnato {exp} punti esperienza."
        
    # Mostra il messaggio tramite dialogo invece di testo
    gioco.io.mostra_dialogo("Successo", messaggio, ["Continua"])
    
def gestisci_fallimento(state, gioco, abilita):
    """
    Gestisce gli effetti del fallimento nella prova
    
    Args:
        state: Istanza dello stato ProvaAbilitaState
        gioco: Istanza del gioco
        abilita: Abilità messa alla prova
    """
    messaggio = ""
    
    if state.contesto.get("tipo") == "oggetto":
        oggetto = state.contesto.get("oggetto")
        if oggetto:
            messaggio += f"Non sei riuscito a interagire correttamente con {oggetto.nome}.\n"
            
            # Se c'è una penalità, applicarla
            if state.contesto.get("penalita"):
                danno = state.contesto.get("penalita")
                gioco.giocatore.subisci_danno(danno)
                messaggio += f"Subisci {danno} danni!"
    
    # Mostra il messaggio tramite dialogo invece di testo
    gioco.io.mostra_dialogo("Fallimento", messaggio, ["Continua"])

def gestisci_successo_npg(state, gioco, abilita, npg):
    """
    Gestisce gli effetti del successo nella prova contro un NPG
    
    Args:
        state: Istanza dello stato ProvaAbilitaState
        gioco: Istanza del gioco
        abilita: Abilità messa alla prova
        npg: Personaggio non giocante coinvolto
    """
    messaggio = f"L'interazione con {npg.nome} ha avuto successo!\n"
    
    # Comportamento diverso in base all'abilità
    if abilita in ABILITA_ASSOCIATE:
        # Abilità specifiche
        if abilita == "persuasione":
            messaggio += f"Sei riuscito a persuadere {npg.nome}!"
            if hasattr(npg, "stato_corrente"):
                npg.cambia_stato("persuaso")
        elif abilita == "intimidire":
            messaggio += f"Sei riuscito a intimidire {npg.nome}!"
            if hasattr(npg, "stato_corrente"):
                npg.cambia_stato("intimidito")
        elif abilita == "inganno":
            messaggio += f"Sei riuscito a ingannare {npg.nome}!"
            if hasattr(npg, "stato_corrente"):
                npg.cambia_stato("ingannato")
        elif abilita == "percezione" or abilita == "indagare":
            messaggio += f"Hai notato qualcosa di importante su {npg.nome}!"
    else:
        # Caratteristiche base
        if abilita == "forza":
            messaggio += f"Hai impressionato {npg.nome} con la tua forza!"
        elif abilita == "destrezza":
            messaggio += f"{npg.nome} è colpito dalla tua agilità!"
        elif abilita == "carisma":
            messaggio += f"{npg.nome} è affascinato dalla tua presenza!"
            if hasattr(npg, "stato_corrente"):
                npg.cambia_stato("amichevole")
    
    # Ricompensa base
    exp = 8
    if gioco.giocatore.guadagna_esperienza(exp, gioco):
        messaggio += f"\n\nHai guadagnato {exp} punti esperienza e sei salito di livello!"
    else:
        messaggio += f"\n\nHai guadagnato {exp} punti esperienza."
        
    # Mostra il messaggio tramite dialogo invece di testo
    gioco.io.mostra_dialogo("Successo con NPG", messaggio, ["Continua"])

def gestisci_fallimento_npg(state, gioco, abilita, npg):
    """
    Gestisce il fallimento di una prova contro un NPG
    
    Args:
        state: Istanza dello stato ProvaAbilitaState
        gioco: Istanza del gioco
        abilita: Abilità messa alla prova
        npg: Personaggio non giocante coinvolto
    """
    messaggio = ""
    
    # Determina gli effetti del fallimento in base all'abilità
    if abilita == "forza":
        messaggio += f"{npg.nome} si è dimostrato più forte e ti ha atterrato!"
        gioco.giocatore.subisci_danno(1)
    elif abilita == "destrezza":
        messaggio += f"{npg.nome} è troppo veloce per te!"
    elif abilita == "costituzione":
        messaggio += f"La tua resistenza non regge al confronto con {npg.nome}."
        gioco.giocatore.subisci_danno(1)
    elif abilita == "intelligenza":
        messaggio += f"{npg.nome} ti ha battuto in astuzia!"
    elif abilita == "saggezza":
        messaggio += f"{npg.nome} è più perspicace di te."
    elif abilita == "carisma":
        messaggio += f"{npg.nome} ti ignora completamente dopo il tuo tentativo fallito."
    else:  # Fallimento di un'abilità specifica
        messaggio += f"Il tuo tentativo di {abilita} contro {npg.nome} fallisce miseramente!"
        
    # Mostra il messaggio tramite dialogo invece di testo
    gioco.io.mostra_dialogo("Fallimento con NPG", messaggio, ["Continua"])

def esegui_prova(state, sessione, entita, abilita, difficolta, target=None):
    """
    Esegue una prova di abilità e restituisce il risultato per il server
    
    Args:
        state: Istanza dello stato ProvaAbilitaState
        sessione: Sessione di gioco
        entita: Entità che esegue la prova
        abilita: Abilità da testare
        difficolta: Difficoltà della prova
        target: Entità target opzionale (per prove di confronto)
        
    Returns:
        dict: Risultato della prova con tutte le informazioni
    """
    dado = Dado(20)
    tiro_base = dado.tira()
    
    # Ottieni il modificatore in base al tipo di abilità
    modificatore = 0
    if hasattr(entita, "modificatore_abilita") and callable(entita.modificatore_abilita):
        modificatore = entita.modificatore_abilita(abilita)
    else:
        # Fallback per entità senza metodo modificatore_abilita
        for componente in entita.get_all_components():
            if hasattr(componente, "get_bonus_abilita") and callable(componente.get_bonus_abilita):
                modificatore += componente.get_bonus_abilita(abilita)
    
    risultato_totale = tiro_base + modificatore
    successo = risultato_totale >= difficolta
    
    # Prepara il risultato di base
    risultato = {
        "entita": {
            "id": entita.id,
            "nome": entita.name if hasattr(entita, "name") else str(entita.id)
        },
        "abilita": abilita,
        "tiro_base": tiro_base,
        "modificatore": modificatore,
        "risultato_totale": risultato_totale,
        "difficolta": difficolta,
        "successo": successo
    }
    
    # Gestione target per prove di confronto
    if target:
        # Prova di confronto contro un'altra entità
        tiro_target = dado.tira()
        
        # Ottieni il modificatore del target
        mod_target = 0
        if hasattr(target, "modificatore_abilita") and callable(target.modificatore_abilita):
            mod_target = target.modificatore_abilita(abilita)
        else:
            # Fallback per entità senza metodo modificatore_abilita
            for componente in target.get_all_components():
                if hasattr(componente, "get_bonus_abilita") and callable(componente.get_bonus_abilita):
                    mod_target += componente.get_bonus_abilita(abilita)
        
        risultato_target = tiro_target + mod_target
        vittoria = risultato_totale >= risultato_target
        
        # Aggiungi informazioni sul confronto
        risultato["tipo"] = "confronto"
        risultato["target"] = {
            "id": target.id,
            "nome": target.name if hasattr(target, "name") else str(target.id),
            "tiro_base": tiro_target,
            "modificatore": mod_target,
            "risultato_totale": risultato_target
        }
        risultato["vittoria"] = vittoria
        
        # Gestisci gli effetti in base all'esito
        if vittoria:
            # Vittoria su NPG
            if target.has_tag("npg") or target.has_tag("npc"):
                if hasattr(state, "_gestisci_successo_npg"):
                    state._gestisci_successo_npg(sessione, abilita, target)
        else:
            # Sconfitta contro NPG
            if target.has_tag("npg") or target.has_tag("npc"):
                if hasattr(state, "_gestisci_fallimento_npg"):
                    state._gestisci_fallimento_npg(sessione, abilita, target)
    else:
        # Prova normale
        risultato["tipo"] = "normale"
        
        # Gestisci gli effetti in base all'esito
        if successo:
            # Gestisci successo
            if hasattr(state, "_gestisci_successo"):
                state._gestisci_successo(sessione, abilita)
        else:
            # Gestisci fallimento
            if hasattr(state, "_gestisci_fallimento"):
                state._gestisci_fallimento(sessione, abilita)
    
    # Piccola ricompensa per il successo
    if successo or (target and vittoria):
        if hasattr(entita, "guadagna_esperienza") and callable(entita.guadagna_esperienza):
            exp = 5 if not target else 8
            entita.guadagna_esperienza(exp, sessione)
            risultato["exp_guadagnata"] = exp
    
    return risultato 