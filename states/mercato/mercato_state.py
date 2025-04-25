from states.base_state import BaseGameState
from entities.npg import NPG
from states.dialogo import DialogoState
from entities.giocatore import Giocatore
from states.inventario import GestioneInventarioState
from states.prova_abilita import ProvaAbilitaState
from util.funzioni_utili import avanti
import logging

# Importa i moduli specifici del mercato
from states.mercato.oggetti_interattivi import crea_tutti_oggetti_interattivi
from states.mercato.menu_handlers import MenuMercatoHandler
from states.mercato.ui_handlers import UIMercatoHandler
from states.mercato.movimento import MovimentoMercatoHandler
from states.mercato.dialogo import DialogoMercatoHandler

class MercatoState(BaseGameState):
    """Classe che rappresenta lo stato del mercato"""
    
    def __init__(self, game):
        """
        Inizializza lo stato del mercato.
        
        Args:
            game: L'istanza del gioco
        """
        super().__init__(game)
        self.nome_stato = "mercato"
        
        # Carica gli NPC specifici del mercato
        self.npg_presenti = {
            "Araldo": NPG("Araldo"),
            "Violetta": NPG("Violetta"),
            "Gundren": NPG("Gundren")
        }
        self.nome_npg_attivo = None
        self.stato_conversazione = "inizio"
        self.stato_precedente = None
        
        # Inizializza menu e comandi
        self._init_commands()
        
        # Attributi per gestione asincrona
        self.fase = "menu_principale"
        self.ultimo_input = None
        self.dati_contestuali = {}  # Per memorizzare dati tra più fasi
        
        # Attributi per l'interfaccia grafica
        self.ui_aggiornata = False
        self.menu_attivo = "principale"
        self.gioco = None
        self.oggetto_selezionato = None
        self.npg_selezionato = None
        
        # Carica gli oggetti interattivi del mercato
        self.oggetti_interattivi = crea_tutti_oggetti_interattivi()
        
        # Attributo per tenere traccia della visualizzazione mappa
        self.mostra_mappa = False
        
        # Inizializza i gestori per i vari aspetti del mercato
        self.menu_handler = MenuMercatoHandler(self)
        self.ui_handler = UIMercatoHandler(self)
        self.movimento_handler = MovimentoMercatoHandler(self)
        self.dialogo_handler = DialogoMercatoHandler(self)
    
    def esegui(self, gioco):
        """
        Esegue lo stato del mercato.
        
        Args:
            gioco: L'istanza del gioco
        """
        # Salva il contesto di gioco
        self.set_game_context(gioco)
        
        # Se è la prima visita al mercato, inizializza la posizione e popola la mappa
        if not hasattr(self, 'prima_visita_completata'):
            mappa = gioco.gestore_mappe.ottieni_mappa("mercato")
            if mappa:
                gioco.gestore_mappe.imposta_mappa_attuale("mercato")
                x, y = mappa.pos_iniziale_giocatore
                gioco.giocatore.imposta_posizione("mercato", x, y)
                # Popola la mappa con gli oggetti interattivi e gli NPG
                gioco.gestore_mappe.trasferisci_oggetti_da_stato("mercato", self)
            self.prima_visita_completata = True
        
        # Aggiorna il renderer grafico se necessario
        if not self.ui_aggiornata:
            self.ui_handler.aggiorna_renderer(gioco)
            self.ui_aggiornata = True
            
        # Gestione asincrona basata sulla fase corrente
        if self.fase == "menu_principale":
            self.menu_handler.mostra_menu_principale(gioco)
        elif self.fase == "compra_pozione":
            self.menu_handler.mostra_compra_pozione(gioco)
        elif self.fase == "vendi_oggetto_lista":
            self.menu_handler.mostra_vendi_oggetto_lista(gioco)
        elif self.fase == "vendi_oggetto_conferma":
            self.menu_handler.mostra_vendi_oggetto_conferma(gioco)
        elif self.fase == "parla_npg_lista":
            self.menu_handler.mostra_parla_npg_lista(gioco)
        elif self.fase == "visualizza_mappa":
            self._visualizza_mappa(gioco)
        elif self.fase == "esplora_oggetti_lista":
            self.menu_handler.mostra_esplora_oggetti_lista(gioco)
    
    def _visualizza_mappa(self, gioco):
        """
        Visualizza la mappa del mercato.
        
        Args:
            gioco: L'istanza del gioco
        """
        # Attiva la visualizzazione mappa
        self.mostra_mappa = True
        self.ui_aggiornata = False  # Forza l'aggiornamento dell'UI
        
        # Usa il movimento handler per visualizzare la mappa
        self.movimento_handler.visualizza_mappa(gioco)
        
        # Torna al menu principale
        self.fase = "menu_principale"
    
    def _init_commands(self):
        """Inizializza i comandi disponibili nel mercato"""
        self.comandi = {
            "guarda": self._cmd_guarda,
            "parla": self._cmd_parla,
            "compra": self._cmd_compra,
            "vendi": self._cmd_vendi,
            "esamina": self._cmd_esamina,
            "inventario": self._cmd_inventario,
            "mappa": self._cmd_mappa,
            "aiuto": self._cmd_aiuto,
            "esci": self._cmd_esci
        }
    
    def _cmd_guarda(self, gioco, parametri=None):
        """Comando per guardare l'ambiente circostante"""
        gioco.io.mostra_messaggio("Ti trovi al mercato del villaggio. Intorno a te ci sono bancarelle, mercanti e avventori.")
        # Descrivi gli oggetti e gli NPC vicini
        oggetti_vicini = self.ottieni_oggetti_vicini(gioco, 2)
        npg_vicini = self.ottieni_npg_vicini(gioco, 2)
        
        if oggetti_vicini:
            nomi_oggetti = ", ".join(oggetti_vicini.keys())
            gioco.io.mostra_messaggio(f"Vedi: {nomi_oggetti}")
            
        if npg_vicini:
            nomi_npg = ", ".join(npg_vicini.keys())
            gioco.io.mostra_messaggio(f"Persone vicine: {nomi_npg}")
        
        return True
    
    def _cmd_parla(self, gioco, parametri=None):
        """Comando per parlare con un NPC"""
        if not parametri:
            self.fase = "parla_npg_lista"
            return True
            
        nome_npg = " ".join(parametri)
        return self.dialogo_handler.inizia_dialogo(gioco, nome_npg)
    
    def _cmd_compra(self, gioco, parametri=None):
        """Comando per comprare oggetti"""
        self.fase = "compra_pozione"
        return True
    
    def _cmd_vendi(self, gioco, parametri=None):
        """Comando per vendere oggetti"""
        self.fase = "vendi_oggetto_lista"
        return True
    
    def _cmd_esamina(self, gioco, parametri=None):
        """Comando per esaminare oggetti"""
        if not parametri:
            self.fase = "esplora_oggetti_lista"
            return True
            
        nome_oggetto = " ".join(parametri)
        if nome_oggetto in self.oggetti_interattivi:
            oggetto = self.oggetti_interattivi[nome_oggetto]
            gioco.io.mostra_messaggio(f"Esamini {oggetto.nome}: {oggetto.descrizione}")
            return True
            
        gioco.io.mostra_messaggio(f"Non vedi alcun {nome_oggetto} nei paraggi.")
        return False
    
    def _cmd_inventario(self, gioco, parametri=None):
        """Comando per visualizzare l'inventario"""
        inventario_state = GestioneInventarioState(gioco)
        gioco.push_stato(inventario_state)
        return True
    
    def _cmd_mappa(self, gioco, parametri=None):
        """Comando per visualizzare la mappa"""
        self.fase = "visualizza_mappa"
        return True
    
    def _cmd_aiuto(self, gioco, parametri=None):
        """Comando per visualizzare l'aiuto"""
        gioco.io.mostra_messaggio("Comandi disponibili:")
        for cmd in self.comandi.keys():
            gioco.io.mostra_messaggio(f"- {cmd}")
        return True
    
    def _cmd_esci(self, gioco, parametri=None):
        """Comando per uscire dal mercato"""
        gioco.io.mostra_messaggio("Lasci il mercato.")
        gioco.pop_stato()
        return True
    
    def to_dict(self):
        """
        Serializza lo stato del mercato in un dizionario.
        
        Returns:
            dict: Dizionario rappresentante lo stato
        """
        data = super().to_dict()
        data.update({
            "nome_stato": self.nome_stato,
            "fase": self.fase,
            "npg_presenti": {nome: npg.to_dict() for nome, npg in self.npg_presenti.items()},
            "nome_npg_attivo": self.nome_npg_attivo,
            "stato_conversazione": self.stato_conversazione,
            "mostra_mappa": self.mostra_mappa,
            # Non serializzare gli handler poiché saranno ricreati all'inizializzazione
        })
        return data
    
    @classmethod
    def from_dict(cls, data, game=None):
        """
        Crea un'istanza di MercatoState da un dizionario serializzato.
        
        Args:
            data: Dizionario serializzato
            game: Istanza del gioco (opzionale)
            
        Returns:
            MercatoState: Nuova istanza deserializzata
        """
        instance = cls(game)
        
        # Ripristina i dati dello stato base
        if "nome_stato" in data:
            instance.nome_stato = data["nome_stato"]
        if "fase" in data:
            instance.fase = data["fase"]
        if "nome_npg_attivo" in data:
            instance.nome_npg_attivo = data["nome_npg_attivo"]
        if "stato_conversazione" in data:
            instance.stato_conversazione = data["stato_conversazione"]
        if "mostra_mappa" in data:
            instance.mostra_mappa = data["mostra_mappa"]
        
        # Ripristina gli NPC presenti
        if "npg_presenti" in data:
            instance.npg_presenti = {}
            for nome, npg_data in data["npg_presenti"].items():
                instance.npg_presenti[nome] = NPG.from_dict(npg_data)
        
        return instance
    
    def __getstate__(self):
        """
        Prepara lo stato per la serializzazione pickle.
        
        Returns:
            dict: Stato serializzabile
        """
        state = self.__dict__.copy()
        # Rimuovi riferimenti non serializzabili
        state["menu_handler"] = None
        state["ui_handler"] = None
        state["movimento_handler"] = None
        state["dialogo_handler"] = None
        
        return state
    
    def __setstate__(self, state):
        """
        Ripristina lo stato dopo la deserializzazione pickle.
        
        Args:
            state: Stato deserializzato
        """
        self.__dict__.update(state)
        # Ricrea i gestori
        self.menu_handler = MenuMercatoHandler(self)
        self.ui_handler = UIMercatoHandler(self)
        self.movimento_handler = MovimentoMercatoHandler(self)
        self.dialogo_handler = DialogoMercatoHandler(self)
    
    def _register_ui_handlers(self, io_handler):
        """
        Registra i gestori di eventi dell'interfaccia utente.
        
        Args:
            io_handler: L'handler IO del gioco
        """
        self.ui_handler.register_ui_handlers(io_handler)
    
    def _unregister_ui_handlers(self, io_handler):
        """
        Deregistra i gestori di eventi dell'interfaccia utente.
        
        Args:
            io_handler: L'handler IO del gioco
        """
        self.ui_handler.unregister_ui_handlers(io_handler)
    
    def entra(self, gioco=None):
        """
        Metodo chiamato quando si entra nello stato mercato.
        
        Args:
            gioco: L'istanza del gioco (opzionale)
        """
        super().entra(gioco)
        
        if gioco:
            gioco.io.mostra_messaggio("Sei entrato nel mercato del villaggio.")
            gioco.io.mostra_messaggio("C'è un'atmosfera vivace, con mercanti che gridano le loro offerte e avventori che contrattano sui prezzi.")
            
            # Registra i gestori di eventi UI
            self._register_ui_handlers(gioco.io)
    
    def esci(self, gioco=None):
        """
        Metodo chiamato quando si esce dallo stato mercato.
        
        Args:
            gioco: L'istanza del gioco (opzionale)
        """
        super().esci(gioco)
        
        if gioco:
            # Deregistra i gestori di eventi UI
            self._unregister_ui_handlers(gioco.io)
    
    def pausa(self, gioco=None):
        """
        Metodo chiamato quando lo stato mercato viene temporaneamente sospeso.
        
        Args:
            gioco: L'istanza del gioco (opzionale)
        """
        super().pausa(gioco)
        
        # Niente di specifico da fare qui, ma potremmo aggiungere logica in futuro
    
    def riprendi(self, gioco=None):
        """
        Metodo chiamato quando lo stato mercato torna attivo dopo essere stato in pausa.
        
        Args:
            gioco: L'istanza del gioco (opzionale)
        """
        super().riprendi(gioco)
        
        if gioco:
            gioco.io.mostra_messaggio("Sei tornato al mercato del villaggio.")
            
            # Aggiorna l'interfaccia all'uscita
            self.ui_aggiornata = False 