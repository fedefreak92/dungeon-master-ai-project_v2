class BaseInterazioni:
    """
    Classe con funzionalità di interazione per gli stati base.
    Gestisce le interazioni con oggetti e NPC sulla mappa.
    """
    
    @staticmethod
    def aggiorna_elementi_interattivi(state, gioco):
        """
        Aggiorna gli elementi interattivi sulla mappa
        
        Args:
            state: L'istanza dello stato corrente
            gioco: L'istanza del gioco
            
        Returns:
            bool: True se l'aggiornamento è avvenuto, False altrimenti
        """
        if not gioco or not gioco.giocatore.mappa_corrente:
            return False
            
        # Rimuovi tutti gli elementi interattivi esistenti
        for id_elemento in list(gioco.io.elementi_interattivi.keys()):
            gioco.io.rimuovi_elemento_interattivo(id_elemento)
            
        # Aggiungi oggetti interattivi
        oggetti_vicini = state.ottieni_oggetti_vicini(gioco, raggio=5)
        for obj_id, obj in oggetti_vicini.items():
            if hasattr(obj, 'x') and hasattr(obj, 'y'):
                gioco.io.aggiungi_elemento_interattivo(
                    f"oggetto_{obj_id}", 
                    "oggetto", 
                    (obj.x, obj.y),
                    obj.sprite if hasattr(obj, 'sprite') else "item_default",
                    {
                        "onClick": lambda elem, event, obj_id=obj_id: BaseInterazioni.on_oggetto_click(state, obj_id, gioco),
                        "onHover": lambda elem, event, obj_id=obj_id: BaseInterazioni.on_oggetto_hover(state, obj_id, gioco)
                    }
                )
                
        # Aggiungi NPC interattivi
        npg_vicini = state.ottieni_npg_vicini(gioco, raggio=5)
        for npc_id, npc in npg_vicini.items():
            if hasattr(npc, 'x') and hasattr(npc, 'y'):
                gioco.io.aggiungi_elemento_interattivo(
                    f"npc_{npc_id}", 
                    "npc", 
                    (npc.x, npc.y),
                    npc.sprite if hasattr(npc, 'sprite') else "npc_default",
                    {
                        "onClick": lambda elem, event, npc_id=npc_id: BaseInterazioni.on_npc_click(state, npc_id, gioco),
                        "onHover": lambda elem, event, npc_id=npc_id: BaseInterazioni.on_npc_hover(state, npc_id, gioco)
                    }
                )
                
        return True
    
    @staticmethod
    def on_oggetto_click(state, obj_id, gioco):
        """
        Handler per click su un oggetto
        
        Args:
            state: L'istanza dello stato corrente
            obj_id: ID dell'oggetto
            gioco: L'istanza del gioco
        """
        oggetti_vicini = state.ottieni_oggetti_vicini(gioco)
        if obj_id in oggetti_vicini:
            oggetto = oggetti_vicini[obj_id]
            # Mostra menu contestuale con azioni possibili
            azioni = ["esamina", "prendi"]
            if hasattr(oggetto, 'azioni_possibili'):
                azioni = oggetto.azioni_possibili(gioco.giocatore)
                
            # Posizione dell'oggetto sullo schermo
            x, y = oggetto.x, oggetto.y
            gioco.io.mostra_menu_contestuale((x, y), azioni)
    
    @staticmethod
    def on_oggetto_hover(state, obj_id, gioco):
        """
        Handler per hover su un oggetto
        
        Args:
            state: L'istanza dello stato corrente
            obj_id: ID dell'oggetto
            gioco: L'istanza del gioco
        """
        oggetti_vicini = state.ottieni_oggetti_vicini(gioco)
        if obj_id in oggetti_vicini:
            oggetto = oggetti_vicini[obj_id]
            # Mostra tooltip con nome dell'oggetto
            nome = oggetto.nome if hasattr(oggetto, 'nome') else obj_id
            x, y = oggetto.x, oggetto.y
            gioco.io.mostra_tooltip(nome, (x, y))
    
    @staticmethod
    def on_npc_click(state, npc_id, gioco):
        """
        Handler per click su un NPC
        
        Args:
            state: L'istanza dello stato corrente
            npc_id: ID del NPC
            gioco: L'istanza del gioco
        """
        npg_vicini = state.ottieni_npg_vicini(gioco)
        if npc_id in npg_vicini:
            npc = npg_vicini[npc_id]
            # Mostra menu contestuale con azioni possibili
            azioni = ["parla", "esamina"]
            if hasattr(npc, 'azioni_possibili'):
                azioni = npc.azioni_possibili(gioco.giocatore)
                
            # Posizione del NPC sullo schermo
            x, y = npc.x, npc.y
            gioco.io.mostra_menu_contestuale((x, y), azioni)
    
    @staticmethod
    def on_npc_hover(state, npc_id, gioco):
        """
        Handler per hover su un NPC
        
        Args:
            state: L'istanza dello stato corrente
            npc_id: ID del NPC
            gioco: L'istanza del gioco
        """
        npg_vicini = state.ottieni_npg_vicini(gioco)
        if npc_id in npg_vicini:
            npc = npg_vicini[npc_id]
            # Mostra tooltip con nome del NPC
            nome = npc.nome if hasattr(npc, 'nome') else npc_id
            x, y = npc.x, npc.y
            gioco.io.mostra_tooltip(nome, (x, y)) 