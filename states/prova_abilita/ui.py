"""
Funzionalità di interfaccia utente per lo stato di prova abilità.
Contiene metodi per visualizzare i vari menu e dialoghi.
"""

def aggiorna_renderer(state, gioco):
    """Aggiorna il renderer grafico"""
    # Personalizza il rendering in base alle esigenze
    gioco.io.pulisci_schermo()
    gioco.io.mostra_messaggio("=== Sistema di Prove di Abilità ===")
    
def esegui_menu_principale(state, gioco):
    """Mostra il menu principale"""
    game_ctx = gioco if gioco else getattr(state, 'gioco', None)
    
    game_ctx.io.mostra_messaggio("\n=== MENU PROVE ABILITÀ ===")
    
    # Mostriamo il menu come dialogo con opzioni invece di richiedere input testuale
    opzioni = [
        "1. Prova abilità giocatore",
        "2. Prova abilità NPG", 
        "3. Prova confronto abilità",
        "0. Esci"
    ]
    game_ctx.io.mostra_dialogo("Menu Prove Abilità", "Seleziona un'opzione:", opzioni)

def mostra_menu_abilita(state, gioco):
    """Mostra il menu di selezione abilità tramite UI"""
    opzioni = [
        "1. Forza",
        "2. Destrezza",
        "3. Costituzione",
        "4. Intelligenza",
        "5. Saggezza",
        "6. Carisma",
        "7. Prova su abilità specifica (es. Percezione, Persuasione)",
        "8. Torna indietro"
    ]
    
    gioco.io.mostra_dialogo("Prova di Abilità", "Quale abilità vuoi mettere alla prova?", opzioni)
    state.menu_attivo = "abilita"

def mostra_menu_abilita_specifiche(state, gioco):
    """Mostra il menu di abilità specifiche tramite UI"""
    from entities.entita import ABILITA_ASSOCIATE
    
    opzioni = []
    
    for i, abilita in enumerate(ABILITA_ASSOCIATE.keys(), 1):
        # Mostra se il giocatore ha competenza
        competenza = " [Competente]" if gioco.giocatore.abilita_competenze.get(abilita.lower()) else ""
        opzioni.append(f"{i}. {abilita.capitalize()}{competenza}")
    
    opzioni.append("0. Torna indietro")
    
    gioco.io.mostra_dialogo("Abilità Specifiche", "Scegli l'abilità da provare:", opzioni)
    state.menu_attivo = "abilita_specifiche"

def mostra_menu_modalita_grafico(state, gioco):
    """Mostra il menu di modalità tramite UI"""
    opzioni = [
        "1. Prova base (contro difficoltà)",
        "2. Prova contro un personaggio non giocante (NPG)",
        "3. Prova con un oggetto interattivo",
        "4. Torna indietro"
    ]
    
    gioco.io.mostra_dialogo("Modalità di Prova", "Scegli la modalità di prova:", opzioni)
    state.menu_attivo = "modalita"

def esegui_menu_modalita(state, gioco):
    """Mostra il menu di scelta modalità"""
    game_ctx = gioco if gioco else getattr(state, 'gioco', None)
    
    game_ctx.io.mostra_messaggio("\n=== MODALITÀ PROVA ===")
    
    # Mostriamo il menu come dialogo con opzioni invece di richiedere input testuale
    opzioni = [
        "1. Prova semplice (tiro casuale)",
        "2. Prova avanzata (con dettagli)",
        "0. Indietro"
    ]
    game_ctx.io.mostra_dialogo("Modalità Prova", "Seleziona un'opzione:", opzioni)

def mostra_risultato_prova(state, risultato, successo, gioco):
    """Mostra il risultato di una prova di abilità"""
    game_ctx = gioco if gioco else getattr(state, 'gioco', None)
    
    status = "Successo!" if successo else "Fallimento!"
    game_ctx.io.mostra_messaggio(f"\nRisultato: {risultato} - {status}")
    
    # Mostra un dialogo con il risultato invece di richiedere input
    game_ctx.io.mostra_dialogo("Risultato Prova", 
                             f"Risultato: {risultato}\nEsito: {status}", 
                             ["Continua"])

def seleziona_npg(state, gioco):
    """Seleziona un NPG dalla mappa corrente"""
    game_ctx = gioco if gioco else getattr(state, 'gioco', None)
    mappa = state.ottieni_mappa_corrente(game_ctx)
    
    if not mappa:
        game_ctx.io.mostra_messaggio("Nessuna mappa corrente.")
        return None
        
    npg_vicini = state.ottieni_npg_vicini(game_ctx)
    
    if not npg_vicini:
        game_ctx.io.mostra_messaggio("Nessun NPG nelle vicinanze.")
        return None
        
    game_ctx.io.mostra_messaggio("\nNPG disponibili:")
    
    # Crea una lista di opzioni per il dialogo
    opzioni_npg = []
    i = 1
    for npg_id, npg in npg_vicini.items():
        game_ctx.io.mostra_messaggio(f"{i}. {npg.nome}")
        opzioni_npg.append(f"{i}. {npg.nome}")
        i += 1
    
    opzioni_npg.append("0. Annulla")
    
    # Mostra un dialogo con le opzioni
    game_ctx.io.mostra_dialogo("Seleziona NPG", "Scegli un NPG per la prova:", opzioni_npg)
    state.menu_attivo = "npg"

def seleziona_npg_confronto(state, gioco):
    """Seleziona un NPG per il confronto di abilità"""
    game_ctx = gioco if gioco else getattr(state, 'gioco', None)
    npg_vicini = state.ottieni_npg_vicini(game_ctx)
    
    if not npg_vicini:
        game_ctx.io.mostra_messaggio("Nessun NPG nelle vicinanze.")
        return None
        
    game_ctx.io.mostra_messaggio("\nNPG disponibili per confronto:")
    
    # Crea una lista di opzioni per il dialogo
    opzioni_npg = []
    i = 1
    for npg_id, npg in npg_vicini.items():
        game_ctx.io.mostra_messaggio(f"{i}. {npg.nome}")
        opzioni_npg.append(f"{i}. {npg.nome}")
        i += 1
    
    opzioni_npg.append("0. Annulla")
    
    # Mostra un dialogo con le opzioni
    game_ctx.io.mostra_dialogo("Seleziona NPG per Confronto", "Scegli un NPG per il confronto di abilità:", opzioni_npg)
    state.menu_attivo = "confronto"

def mostra_risultato_confronto(state, entita1, entita2, abilita, risultato1, risultato2, confronto_successo, gioco):
    """Mostra il risultato di un confronto di abilità"""
    game_ctx = gioco if gioco else getattr(state, 'gioco', None)
    
    esito = f"{entita1.nome} ha vinto!" if confronto_successo else f"{entita2.nome} ha vinto!"
    game_ctx.io.mostra_messaggio(f"\nRisultato confronto di {abilita}:")
    game_ctx.io.mostra_messaggio(f"{entita1.nome}: {risultato1}")
    game_ctx.io.mostra_messaggio(f"{entita2.nome}: {risultato2}")
    game_ctx.io.mostra_messaggio(f"Esito: {esito}")
    
    # Mostra un dialogo con il risultato invece di richiedere input
    game_ctx.io.mostra_dialogo("Risultato Confronto", 
                             f"Confronto di {abilita}:\n{entita1.nome}: {risultato1}\n{entita2.nome}: {risultato2}\n\nEsito: {esito}", 
                             ["Continua"])

def seleziona_oggetto(state, gioco):
    """Seleziona un oggetto dalla mappa corrente"""
    game_ctx = gioco if gioco else getattr(state, 'gioco', None)
    
    oggetti_vicini = state.ottieni_oggetti_vicini(game_ctx)
    
    if not oggetti_vicini:
        game_ctx.io.mostra_messaggio("Nessun oggetto nelle vicinanze.")
        return None
        
    game_ctx.io.mostra_messaggio("\nOggetti disponibili:")
    
    # Crea una lista di opzioni per il dialogo
    opzioni_oggetti = []
    i = 1
    for obj_id, obj in oggetti_vicini.items():
        nome_obj = obj.nome if hasattr(obj, "nome") else f"Oggetto {i}"
        game_ctx.io.mostra_messaggio(f"{i}. {nome_obj}")
        opzioni_oggetti.append(f"{i}. {nome_obj}")
        i += 1
    
    opzioni_oggetti.append("0. Annulla")
    
    # Mostra un dialogo con le opzioni
    game_ctx.io.mostra_dialogo("Seleziona Oggetto", "Scegli un oggetto per interagire:", opzioni_oggetti)
    state.menu_attivo = "oggetto"

def seleziona_oggetto_interazione(state, gioco):
    """Seleziona un oggetto per l'interazione"""
    game_ctx = gioco if gioco else getattr(state, 'gioco', None)
    
    oggetti_vicini = state.ottieni_oggetti_vicini(game_ctx)
    
    if not oggetti_vicini:
        game_ctx.io.mostra_messaggio("Nessun oggetto nelle vicinanze.")
        return None
        
    game_ctx.io.mostra_messaggio("\nOggetti disponibili per interazione:")
    
    # Crea una lista di opzioni per il dialogo
    opzioni_oggetti = []
    i = 1
    for obj_id, obj in oggetti_vicini.items():
        nome_obj = obj.nome if hasattr(obj, "nome") else f"Oggetto {i}"
        game_ctx.io.mostra_messaggio(f"{i}. {nome_obj}")
        opzioni_oggetti.append(f"{i}. {nome_obj}")
        i += 1
    
    opzioni_oggetti.append("0. Annulla")
    
    # Mostra un dialogo con le opzioni
    game_ctx.io.mostra_dialogo("Seleziona Oggetto per Interazione", "Scegli un oggetto:", opzioni_oggetti)
    state.menu_attivo = "oggetto_interazione"

def mostra_risultato_interazione(state, oggetto, risultato, successo, gioco):
    """Mostra il risultato di un'interazione con un oggetto"""
    game_ctx = gioco if gioco else getattr(state, 'gioco', None)
    
    nome_obj = oggetto.nome if hasattr(oggetto, "nome") else "Oggetto"
    status = "Interazione riuscita!" if successo else "Interazione fallita!"
    
    game_ctx.io.mostra_messaggio(f"\nInterazione con {nome_obj}:")
    game_ctx.io.mostra_messaggio(f"Risultato: {risultato}")
    game_ctx.io.mostra_messaggio(f"Esito: {status}")
    
    # Mostra un dialogo con il risultato invece di richiedere input
    game_ctx.io.mostra_dialogo("Risultato Interazione", 
                             f"Interazione con {nome_obj}:\nRisultato: {risultato}\nEsito: {status}", 
                             ["Continua"])

def mostra_menu_finale(state, gioco):
    """Mostra il menu finale"""
    game_ctx = gioco if gioco else getattr(state, 'gioco', None)
    
    game_ctx.io.mostra_messaggio("\n=== AZIONI FINALI ===")
    
    # Mostra un dialogo con le opzioni
    opzioni = ["1. Torna al menu principale", "0. Esci"]
    game_ctx.io.mostra_dialogo("Azioni Finali", "Cosa vuoi fare?", opzioni)
    state.menu_attivo = "finale"

def esci_menu_finale(state, gioco):
    """Mostra un messaggio di uscita"""
    game_ctx = gioco if gioco else getattr(state, 'gioco', None)
    
    game_ctx.io.mostra_messaggio("\nUscita dal sistema di prove. Arrivederci!")
    
    # Mostra un dialogo con messaggio di uscita invece di richiedere input
    game_ctx.io.mostra_dialogo("Arrivederci", "Uscita dal sistema di prove.", ["Chiudi"]) 