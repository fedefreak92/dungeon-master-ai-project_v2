class BaseState:
    """
    Classe base per tutti gli stati del gioco.
    Ogni stato specifico deve ereditare da questa classe e implementare il metodo esegui().
    """
    def __init__(self):
        """Inizializza lo stato base"""
        # Contesto di gioco
        self.gioco = None
        
    def set_game_context(self, gioco):
        """
        Imposta il contesto di gioco per questo stato.
        
        Args:
            gioco: L'istanza del gioco
        """
        self.gioco = gioco
    
    def esegui(self, gioco=None):
        """
        Metodo principale che viene chiamato quando lo stato è attivo.
        Deve essere implementato da ogni classe figlia.
        
        Args:
            gioco: L'istanza del gioco che contiene lo stato corrente e il giocatore
        """
        # Usa il contesto memorizzato se disponibile
        game_ctx = gioco if gioco else getattr(self, 'gioco', None)
        if not game_ctx:
            raise ValueError("Contesto di gioco non disponibile. Usa set_game_context() prima di eseguire.")
            
        raise NotImplementedError("Ogni stato deve implementare esegui()")
    
    def entra(self, gioco=None):
        """
        Metodo chiamato quando si entra nello stato.
        Può essere sovrascritto per inizializzare lo stato.
        
        Args:
            gioco: L'istanza del gioco
        """
        # Memorizza il contesto se fornito
        if gioco:
            self.set_game_context(gioco)
    
    def esci(self, gioco=None):
        """
        Metodo chiamato quando si esce dallo stato.
        Può essere sovrascritto per pulire o salvare dati.
        
        Args:
            gioco: L'istanza del gioco
        """
        pass

    def pausa(self, gioco=None):
        """
        Metodo chiamato quando lo stato viene temporaneamente sospeso
        perché un nuovo stato viene messo sopra di esso.
        Può essere sovrascritto per gestire la sospensione temporanea.
        
        Args:
            gioco: L'istanza del gioco
        """
        pass

    def riprendi(self, gioco=None):
        """
        Metodo chiamato quando lo stato torna ad essere attivo
        dopo essere stato in pausa.
        Può essere sovrascritto per gestire la ripresa dello stato.
        
        Args:
            gioco: L'istanza del gioco
        """
        pass
        
    # Metodi di utilità per le mappe
    
    def ottieni_mappa_corrente(self, gioco=None):
        """
        Ottiene la mappa corrente dove si trova il giocatore.
        
        Args:
            gioco: L'istanza del gioco (opzionale se il contesto è già memorizzato)
            
        Returns:
            Mappa: L'oggetto mappa attuale o None se non disponibile
        """
        # Usa il contesto memorizzato se disponibile
        game_ctx = gioco if gioco else getattr(self, 'gioco', None)
        if not game_ctx or not game_ctx.giocatore.mappa_corrente:
            return None
            
        return game_ctx.gestore_mappe.ottieni_mappa(game_ctx.giocatore.mappa_corrente)
    
    def ottieni_oggetti_vicini(self, gioco=None, raggio=1):
        """
        Ottiene gli oggetti vicini al giocatore entro un certo raggio.
        
        Args:
            gioco: L'istanza del gioco (opzionale se il contesto è già memorizzato)
            raggio (int): Raggio di ricerca
            
        Returns:
            dict: Dizionario di oggetti vicini o dict vuoto se non disponibili
        """
        # Usa il contesto memorizzato se disponibile
        game_ctx = gioco if gioco else getattr(self, 'gioco', None)
        if not game_ctx or not game_ctx.giocatore.mappa_corrente:
            return {}
            
        return game_ctx.giocatore.ottieni_oggetti_vicini(game_ctx.gestore_mappe, raggio)
    
    def ottieni_npg_vicini(self, gioco=None, raggio=1):
        """
        Ottiene gli NPG vicini al giocatore entro un certo raggio.
        
        Args:
            gioco: L'istanza del gioco (opzionale se il contesto è già memorizzato)
            raggio (int): Raggio di ricerca
            
        Returns:
            dict: Dizionario di NPG vicini o dict vuoto se non disponibili
        """
        # Usa il contesto memorizzato se disponibile
        game_ctx = gioco if gioco else getattr(self, 'gioco', None)
        if not game_ctx or not game_ctx.giocatore.mappa_corrente:
            return {}
            
        return game_ctx.giocatore.ottieni_npg_vicini(game_ctx.gestore_mappe, raggio)
    
    def muovi_giocatore(self, direzione, gioco=None):
        """
        Muove il giocatore in una direzione.
        
        Args:
            direzione (str): Una delle direzioni "nord", "sud", "est", "ovest"
            gioco: L'istanza del gioco (opzionale se il contesto è già memorizzato)
            
        Returns:
            bool: True se il movimento è avvenuto, False altrimenti
        """
        # Usa il contesto memorizzato se disponibile
        game_ctx = gioco if gioco else getattr(self, 'gioco', None)
        if not game_ctx:
            return False
            
        return game_ctx.muovi_giocatore(direzione)
    
    def interagisci_con_oggetto_adiacente(self, gioco=None):
        """
        Fa interagire il giocatore con un oggetto adiacente.
        
        Args:
            gioco: L'istanza del gioco (opzionale se il contesto è già memorizzato)
            
        Returns:
            bool: True se l'interazione è avvenuta, False altrimenti
        """
        # Usa il contesto memorizzato se disponibile
        game_ctx = gioco if gioco else getattr(self, 'gioco', None)
        if not game_ctx or not game_ctx.giocatore.mappa_corrente:
            return False
            
        return game_ctx.giocatore.interagisci_con_oggetto_adiacente(game_ctx.gestore_mappe, game_ctx)
    
    def interagisci_con_npg_adiacente(self, gioco=None):
        """
        Fa interagire il giocatore con un NPG adiacente.
        
        Args:
            gioco: L'istanza del gioco (opzionale se il contesto è già memorizzato)
            
        Returns:
            bool: True se l'interazione è avvenuta, False altrimenti
        """
        # Usa il contesto memorizzato se disponibile
        game_ctx = gioco if gioco else getattr(self, 'gioco', None)
        if not game_ctx or not game_ctx.giocatore.mappa_corrente:
            return False
            
        return game_ctx.giocatore.interagisci_con_npg_adiacente(game_ctx.gestore_mappe, game_ctx)
    
    def cambia_mappa(self, mappa_dest, x=None, y=None, gioco=None):
        """
        Cambia la mappa corrente del giocatore.
        
        Args:
            mappa_dest (str): Nome della mappa di destinazione
            x, y (int, optional): Coordinate di destinazione
            gioco: L'istanza del gioco (opzionale se il contesto è già memorizzato)
            
        Returns:
            bool: True se il cambio mappa è avvenuto, False altrimenti
        """
        # Usa il contesto memorizzato se disponibile
        game_ctx = gioco if gioco else getattr(self, 'gioco', None)
        if not game_ctx:
            return False
            
        return game_ctx.cambia_mappa(mappa_dest, x, y)
    
    def visualizza_mappa(self, gioco=None):
        """
        Visualizza la mappa corrente usando il renderer grafico.
        Delega alla classe BaseUI.
        
        Args:
            gioco: L'istanza del gioco (opzionale se il contesto è già memorizzato)
            
        Returns:
            bool: True se la mappa è stata visualizzata, False altrimenti
        """
        from states.base.ui import BaseUI
        return BaseUI.visualizza_mappa(self, gioco)
    
    def aggiorna_renderer(self, gioco=None):
        """
        Aggiorna il renderer grafico con lo stato attuale del gioco.
        Delega alla classe BaseUI.
        
        Args:
            gioco: L'istanza del gioco (opzionale se il contesto è già memorizzato)
            
        Returns:
            bool: True se l'aggiornamento è avvenuto correttamente
        """
        from states.base.ui import BaseUI
        return BaseUI.aggiorna_renderer(self, gioco)
    
    def to_dict(self):
        """
        Converte lo stato in un dizionario per la serializzazione.
        Delega alla classe BaseSerializzazione.
        
        Returns:
            dict: Rappresentazione dello stato in formato dizionario
        """
        from states.base.serializzazione import BaseSerializzazione
        return BaseSerializzazione.to_dict(self)
    
    @classmethod
    def from_dict(cls, data):
        """
        Crea un'istanza di stato da un dizionario.
        Delega alla classe BaseSerializzazione.
        
        Args:
            data (dict): Dizionario con i dati dello stato
            
        Returns:
            BaseState: Nuova istanza di stato o istanza di base in caso di errore
        """
        from states.base.serializzazione import BaseSerializzazione
        return BaseSerializzazione.from_dict(cls, data) 