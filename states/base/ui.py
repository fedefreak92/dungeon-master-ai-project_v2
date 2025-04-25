class BaseUI:
    """
    Classe con funzionalità di interfaccia utente per gli stati base.
    Gestisce il rendering della mappa e l'aggiornamento degli elementi UI.
    """
    
    @staticmethod
    def visualizza_mappa(state, gioco=None):
        """
        Visualizza la mappa corrente usando il renderer grafico.
        
        Args:
            state: L'istanza dello stato corrente
            gioco: L'istanza del gioco (opzionale se il contesto è già memorizzato)
            
        Returns:
            bool: True se la mappa è stata visualizzata, False altrimenti
        """
        # Usa il contesto memorizzato se disponibile
        game_ctx = gioco if gioco else getattr(state, 'gioco', None)
        if not game_ctx:
            return False
            
        mappa = state.ottieni_mappa_corrente(game_ctx)
        if not mappa:
            return False
            
        # Prepara i dati della mappa per il renderer grafico
        mappa_dati = {
            "id": mappa.nome,
            "nome": mappa.nome,
            "larghezza": mappa.larghezza,
            "altezza": mappa.altezza,
            "tile_size": 32,  # Dimensione predefinita dei tile
            "layers": mappa.genera_layers_rendering(),
            "entities": mappa.genera_entities_rendering(game_ctx.giocatore),
            "position": {
                "x": game_ctx.giocatore.x,
                "y": game_ctx.giocatore.y
            }
        }
            
        # Aggiorna la visualizzazione della mappa
        game_ctx.io.aggiorna_mappa(mappa_dati)
        return True
    
    @staticmethod
    def aggiorna_renderer(state, gioco=None):
        """
        Aggiorna il renderer grafico con lo stato attuale del gioco.
        
        Args:
            state: L'istanza dello stato corrente
            gioco: L'istanza del gioco (opzionale se il contesto è già memorizzato)
            
        Returns:
            bool: True se l'aggiornamento è avvenuto correttamente
        """
        # Usa il contesto memorizzato se disponibile
        game_ctx = gioco if gioco else getattr(state, 'gioco', None)
        if not game_ctx:
            return False
            
        # Aggiorna la mappa
        BaseUI.visualizza_mappa(state, game_ctx)
        
        # Aggiorna gli elementi interattivi sulla mappa
        from states.base.interazioni import BaseInterazioni
        BaseInterazioni.aggiorna_elementi_interattivi(state, game_ctx)
        
        return True 