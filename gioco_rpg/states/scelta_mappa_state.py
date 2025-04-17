from states.base_state import BaseGameState
from states.taverna import TavernaState
from states.mercato import MercatoState
from states.mappa import MappaState
from util.funzioni_utili import avanti

class SceltaMappaState(BaseGameState):
    """
    Stato che permette al giocatore di scegliere tra diverse mappe disponibili.
    Funziona come un hub centrale per navigare tra le diverse aree del gioco.
    """
    
    def __init__(self, gioco=None):
        """
        Inizializza lo stato di scelta mappa.
        
        Args:
            gioco: L'istanza del gioco (opzionale)
        """
        super().__init__(gioco)
        self.nome_stato = "scelta_mappa"
        self.stato_precedente = None
        self.ui_aggiornata = False
        # Flag per indicare se è la prima esecuzione dopo il caricamento del gioco
        self.prima_esecuzione = True
        
    def entra(self, gioco=None):
        """
        Metodo chiamato quando si entra nello stato.
        
        Args:
            gioco: L'istanza del gioco (opzionale)
        """
        super().entra(gioco)
        # Salva lo stato corrente della mappa per poter tornare indietro se necessario
        if gioco:
            self.mappa_corrente = gioco.giocatore.mappa_corrente
            self.ui_aggiornata = False
    
    def esegui(self, gioco=None):
        """Esegue lo stato di scelta mappa"""
        # Usa il contesto memorizzato se disponibile
        game_ctx = gioco if gioco else getattr(self, 'gioco', None)
        if not game_ctx:
            raise ValueError("Contesto di gioco non disponibile. Usa set_game_context() prima di eseguire.")
        
        # Ottieni la lista delle mappe disponibili
        lista_mappe = game_ctx.gestore_mappe.ottieni_lista_mappe()
        
        if not lista_mappe:
            self._mostra_errore(game_ctx, "Nessuna mappa disponibile.")
            game_ctx.pop_stato()
            return
        
        # Aggiorna il renderer grafico se necessario
        if not self.ui_aggiornata:
            self.aggiorna_renderer(game_ctx)
            self.ui_aggiornata = True
            
        # Mostra le mappe disponibili usando l'interfaccia grafica
        self._mostra_selezione_mappe(game_ctx, lista_mappe)
        
        # Elabora gli eventi UI
        super().esegui(game_ctx)
        
    def _mostra_selezione_mappe(self, gioco, lista_mappe):
        """Mostra la selezione delle mappe usando l'interfaccia grafica"""
        # Genera le opzioni per il dialogo
        opzioni_mappe = []
        id_mappa_giocatore = None
        
        for i, (id_mappa, info_mappa) in enumerate(lista_mappe.items(), 1):
            # Evidenzia la mappa corrente del giocatore
            marker = ""
            if gioco.giocatore.mappa_corrente == id_mappa:
                marker = " [CORRENTE]"
                id_mappa_giocatore = id_mappa
                
            # Ottieni informazioni sulla mappa
            nome_mappa = info_mappa.get("nome", id_mappa)
            livello_min = info_mappa.get("livello_min", 0)
            
            # Aggiungi alla lista di opzioni
            opzioni_mappe.append(f"{nome_mappa}{marker} (Livello: {livello_min}+)")
        
        # Aggiungi l'opzione per tornare indietro
        opzioni_mappe.append("Torna indietro")
        
        # Mostra un dialogo di selezione
        gioco.io.mostra_dialogo("Seleziona Mappa", "Scegli una destinazione:", opzioni_mappe)
    
    def _handle_dialog_choice(self, event):
        """
        Handler per le scelte dai dialoghi
        
        Args:
            event: Evento di scelta da dialogo
        """
        if not hasattr(event, "data") or not event.data:
            return
        
        choice = event.data.get("choice")
        if not choice:
            return
            
        game_ctx = self.gioco
        if not game_ctx:
            return
            
        # Gestione selezione mappa
        if choice == "Torna indietro":
            game_ctx.pop_stato()
            return
            
        # Estrai il nome della mappa dalla scelta
        nome_mappa = choice.split(" [")[0].split(" (")[0]
        
        # Trova la mappa corrispondente
        lista_mappe = game_ctx.gestore_mappe.ottieni_lista_mappe()
        id_mappa_selezionata = None
        
        for id_mappa, info_mappa in lista_mappe.items():
            if info_mappa.get("nome", id_mappa) == nome_mappa:
                id_mappa_selezionata = id_mappa
                break
                
        if id_mappa_selezionata:
            info_mappa = lista_mappe[id_mappa_selezionata]
            
            # Verifica requisiti
            livello_min = info_mappa.get("livello_min", 0)
            if game_ctx.giocatore.livello < livello_min:
                game_ctx.io.mostra_dialogo(
                    "Livello Insufficiente", 
                    f"Non puoi accedere a questa mappa.\nDevi essere almeno di livello {livello_min}.", 
                    ["OK"]
                )
                return
            
            # Cambia mappa
            self._viaggia_verso_mappa(game_ctx, id_mappa_selezionata, info_mappa)
    
    def _viaggia_verso_mappa(self, gioco, id_mappa, info_mappa):
        """Gestisce il viaggio verso una nuova mappa"""
        # Ottieni la posizione iniziale della mappa
        x, y = None, None
        mappa = gioco.gestore_mappe.ottieni_mappa(id_mappa)
        if mappa:
            x, y = mappa.pos_iniziale_giocatore
        
        # Esegui il cambio mappa
        success = gioco.cambia_mappa(id_mappa, x, y)
        
        if success:
            # Torna allo stato precedente (solitamente mappa_state)
            gioco.pop_stato()
            # Aggiorna il renderer se necessario
            if hasattr(gioco.stato_corrente(), 'aggiorna_renderer'):
                gioco.stato_corrente().aggiorna_renderer(gioco)
        else:
            gioco.io.mostra_dialogo(
                "Viaggio Impossibile", 
                "Non è possibile raggiungere questa destinazione.", 
                ["OK"]
            )
    
    def _mostra_errore(self, gioco, messaggio):
        """Mostra un messaggio di errore usando l'interfaccia grafica"""
        gioco.io.mostra_dialogo("Errore", messaggio, ["OK"])
            
    def to_dict(self):
        """
        Converte lo stato in un dizionario per la serializzazione.
        
        Returns:
            dict: Rappresentazione dello stato in formato dizionario
        """
        data = super().to_dict()
        data.update({
            "mappa_corrente": getattr(self, 'mappa_corrente', None),
            "prima_esecuzione": getattr(self, 'prima_esecuzione', False),
            "ui_aggiornata": getattr(self, 'ui_aggiornata', False)
        })
        return data
        
    @classmethod
    def from_dict(cls, data, game=None):
        """
        Crea un'istanza di SceltaMappaState da un dizionario.
        
        Args:
            data (dict): Dizionario con i dati dello stato
            game: Istanza del gioco (opzionale)
            
        Returns:
            SceltaMappaState: Nuova istanza dello stato
        """
        state = cls(game)
        state.mappa_corrente = data.get("mappa_corrente")
        state.prima_esecuzione = data.get("prima_esecuzione", False)
        state.ui_aggiornata = data.get("ui_aggiornata", False)
        return state 