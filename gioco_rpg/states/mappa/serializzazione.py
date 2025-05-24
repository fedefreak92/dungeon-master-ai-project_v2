"""
Funzioni di serializzazione e deserializzazione per lo stato mappa.
Contiene le funzioni per convertire lo stato in formato JSON e viceversa.
"""

# from entities.npg import NPG # Se necessario per deserializzare istanze NPG complete
# from entities.oggetto_interattivo import OggettoInterattivo # Se necessario

def to_dict(state):
    """
    Converte lo stato mappa/luogo in un dizionario.
    
    Args:
        state: L'istanza di MappaState (LuogoState) da serializzare
        
    Returns:
        dict: Rappresentazione dello stato in formato dizionario
    """
    base_data = state.get_base_dict() # Metodo da EnhancedBaseState
    base_data.update({
        "nome_stato": state.nome_stato, # es. "luogo_taverna"
        "nome_luogo": state.nome_luogo, # es. "taverna"
        
        # Attributi generalizzati
        "npg_presenti": { 
            # Serializza lo stato degli NPG. Se NPG ha to_dict(), usalo.
            # Altrimenti, serializza i dati necessari per ricostruirlo.
            # L'approccio qui dipende da come _carica_dati_luogo istanzia gli NPG
            # e se le istanze NPG stesse hanno uno stato modificabile da salvare.
            nome: npg_data.get('istanza').to_dict() if npg_data.get('istanza') and hasattr(npg_data.get('istanza'), 'to_dict') else npg_data.get('dati', {})
            for nome, npg_data in state.npg_presenti.items()
        },
        "oggetti_interattivi": {
            # Simile agli NPG, serializza lo stato o i dati per la ricostruzione.
            nome: obj_data.get('istanza').to_dict() if obj_data.get('istanza') and hasattr(obj_data.get('istanza'), 'to_dict') else obj_data.get('dati', {})
            for nome, obj_data in state.oggetti_interattivi.items()
        },
        "nome_npg_attivo": state.nome_npg_attivo,
        "stato_conversazione": state.stato_conversazione,
        "fase_luogo": state.fase_luogo,
        "dati_contestuali_luogo": state.dati_contestuali_luogo,

        "mostra_leggenda": state.mostra_leggenda,
        "menu_attivo": state.menu_attivo,
        "ui_aggiornata": state.ui_aggiornata, # Probabilmente non serve salvarla, si resetta all'avvio
        "ultima_scelta": state.ultima_scelta,
        "attesa_risposta_mappa": state.attesa_risposta_mappa,
        "mostra_mappa": state.mostra_mappa,
        # Rimuovi "stato_origine" se non più usato, o serializzalo se necessario.
    })
    return base_data

def from_dict(cls, data, game=None):
    """
    Crea un'istanza di MappaState (LuogoState) da un dizionario.
    
    Args:
        cls: La classe MappaState (LuogoState)
        data (dict): Dizionario con i dati dello stato
        game: Istanza del gioco (opzionale)
            
    Returns:
        MappaState: Nuova istanza dello stato
    """
    nome_luogo_estratto = data.get("nome_luogo", "default_luogo") # Estrai nome_luogo prima
    # stato_origine_estratto = data.get("stato_origine") # Se mantenuto
    
    # instance = cls(nome_luogo=nome_luogo_estratto, stato_origine=stato_origine_estratto) # Passa gli argomenti richiesti
    instance = cls(nome_luogo=nome_luogo_estratto) # Assumendo che stato_origine non sia più un parametro del costruttore base

    # EnhancedBaseState.from_dict(instance, data, game) # Se EnhancedBaseState ha un metodo simile per popolare
    # Oppure popola attributi base manualmente se necessario, anche se _carica_dati_luogo dovrebbe rifare molto.

    # Molti attributi (npg_presenti, oggetti_interattivi, menu_attivo specifico del luogo) 
    # sono inizializzati da _carica_dati_luogo() e _init_handlers() nel costruttore di MappaState.
    # Qui dobbiamo ripristinare solo lo *stato* di quegli elementi che potrebbe essere cambiato *dopo* l'inizializzazione.

    # Esempio per ripristinare lo stato degli NPG (molto dipendente dall'implementazione):
    if "npg_presenti" in data:
        for nome_npg, npg_stato_salvato in data["npg_presenti"].items():
            if nome_npg in instance.npg_presenti and instance.npg_presenti[nome_npg].get('istanza'):
                # Se l'NPG esiste ed è stato istanziato, prova a ripristinare il suo stato
                # Questo assume che NPG abbia un metodo from_dict o che si possano impostare attributi
                if hasattr(instance.npg_presenti[nome_npg]['istanza'], 'from_dict'):
                    instance.npg_presenti[nome_npg]['istanza'].from_dict(npg_stato_salvato)
                else:
                    # Logica di ripristino manuale se NPG.from_dict non esiste
                    pass 
            # Altrimenti, l'NPG potrebbe essere stato aggiunto dinamicamente e non presente nel caricamento base
            # o i dati salvati sono solo per riferimento e non per stato.

    # Simile per oggetti_interattivi
    if "oggetti_interattivi" in data:
        for nome_obj, obj_stato_salvato in data["oggetti_interattivi"].items():
            if nome_obj in instance.oggetti_interattivi and instance.oggetti_interattivi[nome_obj].get('istanza'):
                if hasattr(instance.oggetti_interattivi[nome_obj]['istanza'], 'from_dict'):
                    instance.oggetti_interattivi[nome_obj]['istanza'].from_dict(obj_stato_salvato)
                else:
                    pass

    instance.nome_npg_attivo = data.get("nome_npg_attivo")
    instance.stato_conversazione = data.get("stato_conversazione", "inizio")
    instance.fase_luogo = data.get("fase_luogo", "menu_principale")
    instance.dati_contestuali_luogo = data.get("dati_contestuali_luogo", {})

    instance.mostra_leggenda = data.get("mostra_leggenda", True)
    # menu_attivo è spesso gestito da _carica_dati_luogo, ma potrebbe essere sovrascritto dallo stato salvato se necessario
    instance.menu_attivo = data.get("menu_attivo", instance.menu_attivo) 
    instance.ui_aggiornata = data.get("ui_aggiornata", False) # Si resetta solitamente
    instance.ultima_scelta = data.get("ultima_scelta")
    instance.attesa_risposta_mappa = data.get("attesa_risposta_mappa")
    instance.mostra_mappa = data.get("mostra_mappa", False)

    if game:
        instance.set_game_context(game)
            
    return instance 