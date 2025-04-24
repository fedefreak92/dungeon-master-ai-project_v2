"""
Utility di validazione per dati di gioco.
Fornisce funzioni per validare e correggere i dati di mappe, NPC e oggetti.
"""

import logging
from pathlib import Path

def valida_mappa(mappa_data):
    """
    Valida i dati di una mappa e corregge problemi comuni.
    
    Args:
        mappa_data (dict): Dati mappa da validare
        
    Returns:
        dict: Dati mappa corretti
    """
    # Correggi mappa_data in modo non distruttivo
    mappa_corretta = mappa_data.copy()
    
    # Verifica presenza campi essenziali
    campi_obbligatori = ["nome", "larghezza", "altezza", "griglia"]
    for campo in campi_obbligatori:
        if campo not in mappa_corretta:
            logging.error(f"Campo obbligatorio mancante nella mappa: {campo}")
            if campo == "nome":
                mappa_corretta["nome"] = "mappa_sconosciuta"
            elif campo == "larghezza":
                mappa_corretta["larghezza"] = 10
            elif campo == "altezza":
                mappa_corretta["altezza"] = 10
            elif campo == "griglia":
                # Crea una griglia di default
                larghezza = mappa_corretta.get("larghezza", 10)
                altezza = mappa_corretta.get("altezza", 10)
                mappa_corretta["griglia"] = [[0 for _ in range(larghezza)] for _ in range(altezza)]
    
    # Verifica dimensione griglia
    larghezza = mappa_corretta["larghezza"]
    altezza = mappa_corretta["altezza"]
    griglia = mappa_corretta["griglia"]
    
    if len(griglia) != altezza:
        logging.warning(f"Dimensione griglia non corretta: altezza dichiarata {altezza}, effettiva {len(griglia)}")
        # Correggi aggiungendo o rimuovendo righe
        if len(griglia) < altezza:
            # Aggiungi righe mancanti
            for _ in range(altezza - len(griglia)):
                griglia.append([0 for _ in range(larghezza)])
        else:
            # Tronca righe in eccesso
            griglia = griglia[:altezza]
    
    # Verifica larghezza di ogni riga
    for i, riga in enumerate(griglia):
        if len(riga) != larghezza:
            logging.warning(f"Larghezza riga {i} non corretta: attesa {larghezza}, effettiva {len(riga)}")
            # Correggi aggiungendo o rimuovendo colonne
            if len(riga) < larghezza:
                # Aggiungi colonne mancanti
                griglia[i].extend([0 for _ in range(larghezza - len(riga))])
            else:
                # Tronca colonne in eccesso
                griglia[i] = riga[:larghezza]
    
    mappa_corretta["griglia"] = griglia
    
    # Verifica posizione iniziale giocatore
    if "pos_iniziale_giocatore" not in mappa_corretta:
        logging.warning(f"Posizione iniziale giocatore mancante nella mappa {mappa_corretta['nome']}")
        # Trova una posizione valida (non un muro)
        pos_valida = (1, 1)  # Default
        for y in range(altezza):
            for x in range(larghezza):
                if griglia[y][x] == 0:  # Non è un muro
                    pos_valida = (x, y)
                    break
            if pos_valida != (1, 1):
                break
        mappa_corretta["pos_iniziale_giocatore"] = pos_valida
        logging.info(f"Impostata posizione iniziale giocatore a {pos_valida}")
    
    # Inizializza sezioni vuote se mancanti
    for sezione in ["oggetti", "npg", "porte"]:
        if sezione not in mappa_corretta:
            mappa_corretta[sezione] = {}
    
    # Aggiungi descrizione se mancante
    if "descrizione" not in mappa_corretta:
        mappa_corretta["descrizione"] = f"Una mappa chiamata {mappa_corretta['nome']}"
    
    return mappa_corretta

def valida_npc(npc_data, nome=None):
    """
    Valida i dati di un NPC e corregge problemi comuni.
    
    Args:
        npc_data (dict): Dati NPC da validare
        nome (str, optional): Nome dell'NPC, se non presente nei dati
        
    Returns:
        dict: Dati NPC corretti
    """
    # Correggi npc_data in modo non distruttivo
    npc_correcto = npc_data.copy()
    
    # Assicurati che ci sia un nome
    if "nome" not in npc_correcto:
        if nome:
            npc_correcto["nome"] = nome
        else:
            npc_correcto["nome"] = "NPC Sconosciuto"
            logging.warning("Nome NPC mancante, impostato nome di default")
    
    # Assicurati che ci sia un id
    if "id" not in npc_correcto:
        npc_correcto["id"] = npc_correcto["nome"]
    
    # Assicurati che ci sia un token
    if "token" not in npc_correcto:
        # Usa la prima lettera del nome
        npc_correcto["token"] = npc_correcto["nome"][0].upper()
        logging.info(f"Token NPC mancante per {npc_correcto['nome']}, impostato a {npc_correcto['token']}")
    
    # Campi obbligatori con valori predefiniti
    campi_predefiniti = {
        "descrizione": f"Un personaggio chiamato {npc_correcto['nome']}",
        "livello": 1,
        "hp": 10,
        "hp_max": 10,
        "forza": 10,
        "destrezza": 10,
        "costituzione": 10,
        "intelligenza": 10,
        "saggezza": 10,
        "carisma": 10,
        "inventario": [],
        "oro": 0,
        "amichevole": True
    }
    
    # Aggiungi i campi mancanti
    for campo, valore in campi_predefiniti.items():
        if campo not in npc_correcto:
            npc_correcto[campo] = valore
            logging.debug(f"Campo {campo} mancante per NPC {npc_correcto['nome']}, impostato valore predefinito")
    
    # Verifica coerenza hp/hp_max
    if npc_correcto["hp"] > npc_correcto["hp_max"]:
        npc_correcto["hp"] = npc_correcto["hp_max"]
        logging.warning(f"HP maggiore di HP_MAX per NPC {npc_correcto['nome']}, corretto")
    
    return npc_correcto

def valida_oggetto(oggetto_data, nome=None):
    """
    Valida i dati di un oggetto e corregge problemi comuni.
    
    Args:
        oggetto_data (dict): Dati oggetto da validare
        nome (str, optional): Nome dell'oggetto, se non presente nei dati
        
    Returns:
        dict: Dati oggetto corretti
    """
    # Correggi oggetto_data in modo non distruttivo
    oggetto_corretto = oggetto_data.copy()
    
    # Assicurati che ci sia un nome
    if "nome" not in oggetto_corretto:
        if nome:
            oggetto_corretto["nome"] = nome
        else:
            oggetto_corretto["nome"] = "Oggetto Sconosciuto"
            logging.warning("Nome oggetto mancante, impostato nome di default")
    
    # Assicurati che ci sia un token
    if "token" not in oggetto_corretto:
        # Usa la prima lettera del nome
        oggetto_corretto["token"] = oggetto_corretto["nome"][0].upper()
        logging.info(f"Token oggetto mancante per {oggetto_corretto['nome']}, impostato a {oggetto_corretto['token']}")
    
    # Assicurati che ci sia un tipo
    if "tipo" not in oggetto_corretto:
        oggetto_corretto["tipo"] = "oggetto_interattivo"
        logging.info(f"Tipo oggetto mancante per {oggetto_corretto['nome']}, impostato a oggetto_interattivo")
    
    # Assicurati che ci sia una descrizione
    if "descrizione" not in oggetto_corretto:
        oggetto_corretto["descrizione"] = f"Un {oggetto_corretto['nome']} che si può esaminare."
        logging.info(f"Descrizione oggetto mancante per {oggetto_corretto['nome']}, impostata descrizione predefinita")
    
    # Verifica stato e stati possibili per oggetti interattivi
    if oggetto_corretto["tipo"] == "oggetto_interattivo":
        if "stato" not in oggetto_corretto:
            oggetto_corretto["stato"] = "inattivo"
            logging.info(f"Stato oggetto mancante per {oggetto_corretto['nome']}, impostato a inattivo")
        
        if "stati_possibili" not in oggetto_corretto:
            oggetto_corretto["stati_possibili"] = {
                "inattivo": ["attivo"],
                "attivo": ["inattivo"]
            }
            logging.info(f"Stati possibili mancanti per {oggetto_corretto['nome']}, impostati stati predefiniti")
    
    # Per le porte, verifica stato e stati possibili
    if oggetto_corretto["tipo"] == "porta":
        if "stato" not in oggetto_corretto:
            oggetto_corretto["stato"] = "chiusa"
            logging.info(f"Stato porta mancante per {oggetto_corretto['nome']}, impostato a chiusa")
        
        if "stati_possibili" not in oggetto_corretto:
            oggetto_corretto["stati_possibili"] = {
                "chiusa": ["aperta"],
                "aperta": ["chiusa"]
            }
            logging.info(f"Stati possibili mancanti per porta {oggetto_corretto['nome']}, impostati stati predefiniti")
    
    return oggetto_corretto

def verifica_coordinate_valide(x, y, mappa):
    """
    Verifica che le coordinate siano valide per una mappa.
    
    Args:
        x, y (int): Coordinate da verificare
        mappa (dict): Dati della mappa
        
    Returns:
        bool: True se le coordinate sono valide, False altrimenti
    """
    larghezza = mappa.get("larghezza", 0)
    altezza = mappa.get("altezza", 0)
    
    # Verifica che le coordinate siano all'interno dei limiti della mappa
    if x < 0 or x >= larghezza or y < 0 or y >= altezza:
        return False
    
    # Verifica che la cella non sia un muro
    if y < len(mappa.get("griglia", [])) and x < len(mappa.get("griglia", [])[y]):
        return mappa["griglia"][y][x] == 0  # 0 = spazio vuoto
    
    return False

def trova_posizione_valida(mappa, x_originale, y_originale, raggio=3):
    """
    Trova una posizione valida vicino alle coordinate specificate.
    
    Args:
        mappa (dict): Dati della mappa
        x_originale, y_originale (int): Coordinate originali
        raggio (int): Raggio di ricerca
        
    Returns:
        tuple: (x, y) coordinate valide o None se non trovate
    """
    # Prima verifica se la posizione originale è valida
    if verifica_coordinate_valide(x_originale, y_originale, mappa):
        return (x_originale, y_originale)
    
    # Verifica posizioni vicine in ordine di distanza
    for r in range(1, raggio + 1):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                # Verifica solo il perimetro del quadrato di raggio r
                if abs(dx) == r or abs(dy) == r:
                    x, y = x_originale + dx, y_originale + dy
                    if verifica_coordinate_valide(x, y, mappa):
                        return (x, y)
    
    # Nessuna posizione valida trovata
    return None

def correggi_mappe_oggetti(mappe_oggetti, dati_mappe):
    """
    Corregge le posizioni degli oggetti per renderle valide in base alle mappe.
    
    Args:
        mappe_oggetti (dict): Configurazione oggetti per mappa
        dati_mappe (dict): Dati delle mappe
        
    Returns:
        dict: Configurazione oggetti corretta
    """
    mappe_oggetti_corrette = {}
    
    for nome_mappa, oggetti in mappe_oggetti.items():
        # Verifica se la mappa esiste
        if nome_mappa not in dati_mappe:
            logging.warning(f"Mappa {nome_mappa} non trovata, oggetti ignorati")
            continue
        
        mappa_data = dati_mappe[nome_mappa]
        oggetti_corretti = []
        
        for oggetto in oggetti:
            nome_oggetto = oggetto.get("nome", "oggetto_sconosciuto")
            if "posizione" not in oggetto:
                logging.warning(f"Posizione mancante per oggetto {nome_oggetto} in mappa {nome_mappa}")
                continue
            
            x, y = oggetto["posizione"]
            
            # Verifica e correggi le coordinate
            if not verifica_coordinate_valide(x, y, mappa_data):
                logging.warning(f"Posizione non valida per oggetto {nome_oggetto}: ({x}, {y})")
                nuova_pos = trova_posizione_valida(mappa_data, x, y)
                if nuova_pos:
                    logging.info(f"Posizione corretta per oggetto {nome_oggetto}: ({nuova_pos[0]}, {nuova_pos[1]})")
                    oggetto_corretto = oggetto.copy()
                    oggetto_corretto["posizione"] = list(nuova_pos)
                    oggetti_corretti.append(oggetto_corretto)
                else:
                    logging.error(f"Impossibile trovare posizione valida per oggetto {nome_oggetto}")
            else:
                oggetti_corretti.append(oggetto)
        
        mappe_oggetti_corrette[nome_mappa] = oggetti_corretti
    
    return mappe_oggetti_corrette

def correggi_mappe_npg(mappe_npg, dati_mappe):
    """
    Corregge le posizioni degli NPC per renderle valide in base alle mappe.
    
    Args:
        mappe_npg (dict): Configurazione NPC per mappa
        dati_mappe (dict): Dati delle mappe
        
    Returns:
        dict: Configurazione NPC corretta
    """
    mappe_npg_corrette = {}
    
    for nome_mappa, npg_lista in mappe_npg.items():
        # Verifica se la mappa esiste
        if nome_mappa not in dati_mappe:
            logging.warning(f"Mappa {nome_mappa} non trovata, NPC ignorati")
            continue
        
        mappa_data = dati_mappe[nome_mappa]
        npg_corretti = []
        
        for npg in npg_lista:
            nome_npg = npg.get("nome", "npg_sconosciuto")
            if "posizione" not in npg:
                logging.warning(f"Posizione mancante per NPC {nome_npg} in mappa {nome_mappa}")
                continue
            
            x, y = npg["posizione"]
            
            # Verifica e correggi le coordinate
            if not verifica_coordinate_valide(x, y, mappa_data):
                logging.warning(f"Posizione non valida per NPC {nome_npg}: ({x}, {y})")
                nuova_pos = trova_posizione_valida(mappa_data, x, y)
                if nuova_pos:
                    logging.info(f"Posizione corretta per NPC {nome_npg}: ({nuova_pos[0]}, {nuova_pos[1]})")
                    npg_corretto = npg.copy()
                    npg_corretto["posizione"] = list(nuova_pos)
                    npg_corretti.append(npg_corretto)
                else:
                    logging.error(f"Impossibile trovare posizione valida per NPC {nome_npg}")
            else:
                npg_corretti.append(npg)
        
        mappe_npg_corrette[nome_mappa] = npg_corretti
    
    return mappe_npg_corrette 