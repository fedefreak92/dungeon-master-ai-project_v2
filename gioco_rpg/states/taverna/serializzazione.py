"""
Funzioni di serializzazione e deserializzazione per lo stato Taverna.
Questo modulo implementa funzioni che permettono di convertire lo stato Taverna
in un formato serializzabile e viceversa, con supporto per la migrazione tra 
diverse versioni dello schema.
"""

import logging

# Configura il logger
logger = logging.getLogger(__name__)

# Versione corrente dello schema
SCHEMA_VERSION = 2

def to_dict(stato):
    """
    Converte lo stato Taverna in un dizionario per la serializzazione.
    
    Args:
        stato: L'istanza dello stato Taverna
        
    Returns:
        dict: Rappresentazione serializzabile dello stato
    """
    # Crea un dizionario base
    data = {
        "schema_version": SCHEMA_VERSION,  # Aggiunta versione schema
        "nome_stato": getattr(stato, "nome_stato", "taverna"),
        "fase": getattr(stato, "fase", "menu_principale"),
        "prima_visita": getattr(stato, "prima_visita", False),
        "ultima_scelta": getattr(stato, "ultima_scelta", None),
        "ultimo_input": getattr(stato, "ultimo_input", None),
        "menu_attivo": getattr(stato, "menu_attivo", "menu_principale"),
    }
    
    # Serializza gli NPG
    npg_dict = {}
    try:
        for nome, npg in stato.npg_presenti.items():
            if hasattr(npg, 'to_dict') and callable(getattr(npg, 'to_dict')):
                npg_dict[nome] = npg.to_dict()
            else:
                npg_dict[nome] = {"nome": nome}
    except (AttributeError, TypeError):
        # In caso di errore, salviamo solo i nomi degli NPG
        npg_dict = {}
    
    # Aggiungi i nomi degli NPG (utile per la deserializzazione)
    data["npg_nomi"] = list(npg_dict.keys())
    
    # Aggiungi info sugli NPG attivi
    data["nome_npg_attivo"] = getattr(stato, "nome_npg_attivo", None)
    data["stato_conversazione"] = getattr(stato, "stato_conversazione", "inizio")
    
    return data

def migrate_schema(data):
    """
    Migra i dati del salvataggio alla versione corrente dello schema.
    
    Args:
        data (dict): Dizionario con i dati serializzati
        
    Returns:
        dict: Dizionario migrato alla versione corrente
    """
    # Se non c'è versione, assumiamo la versione 1 (prima dell'introduzione del versionamento)
    version = data.get("schema_version", 1)
    
    # Copia il dizionario originale per non modificarlo
    migrated_data = dict(data)
    
    # Migrazione dalla versione 1 alla 2
    if version < 2:
        logger.info(f"Migrazione schema TavernaState da versione {version} a versione 2")
        
        # Rimozione di _handle_click_event che non esiste più nella classe TavernaState
        if "_handle_click_event" in migrated_data:
            del migrated_data["_handle_click_event"]
        
        # Aggiunta campi obbligatori introdotti in versione 2
        if "menu_attivo" not in migrated_data:
            migrated_data["menu_attivo"] = "menu_principale"
        
        if "stato_conversazione" not in migrated_data:
            migrated_data["stato_conversazione"] = "inizio"
            
        # Aggiorna la versione
        migrated_data["schema_version"] = 2
    
    # Qui possiamo aggiungere future migrazioni da versione 2 a 3, ecc.
    # if version < 3:
    #     logger.info(f"Migrazione schema TavernaState da versione 2 a versione 3")
    #     ... logica di migrazione ...
    #     migrated_data["schema_version"] = 3
    
    return migrated_data

def from_dict(cls, data, game=None):
    """
    Crea un'istanza di stato Taverna da un dizionario.
    
    Args:
        cls: La classe TavernaState
        data (dict): Dizionario con i dati serializzati
        game: L'istanza del gioco (opzionale)
        
    Returns:
        TavernaState: Una nuova istanza dello stato Taverna
    """
    # Migra i dati alla versione corrente dello schema
    migrated_data = migrate_schema(data)
    
    # Crea una nuova istanza
    state = cls(game)
    
    # Imposta gli attributi base
    state.nome_stato = migrated_data.get("nome_stato", "taverna")
    state.fase = migrated_data.get("fase", "menu_principale")
    state.prima_visita = migrated_data.get("prima_visita", False)
    state.ultima_scelta = migrated_data.get("ultima_scelta")
    state.ultimo_input = migrated_data.get("ultimo_input")
    state.menu_attivo = migrated_data.get("menu_attivo", "menu_principale")
    state.nome_npg_attivo = migrated_data.get("nome_npg_attivo")
    state.stato_conversazione = migrated_data.get("stato_conversazione", "inizio")
    
    # Ricrea gli NPG
    npg_nomi = migrated_data.get("npg_nomi", ["Durnan", "Elminster", "Mirt"])
    state.npg_presenti = {}
    
    try:
        from entities.npg import NPG
        for nome in npg_nomi:
            state.npg_presenti[nome] = NPG(nome)
    except ImportError:
        # Gestisce l'errore se NPG non può essere importato
        state.npg_presenti = {nome: object() for nome in npg_nomi}
    
    # Inizializza gli oggetti interattivi
    try:
        from .oggetti_interattivi import inizializza_oggetti_taverna
        state.oggetti_interattivi = inizializza_oggetti_taverna()
    except ImportError:
        # Gestisce l'errore se non può inizializzare gli oggetti
        state.oggetti_interattivi = {}
    
    return state 