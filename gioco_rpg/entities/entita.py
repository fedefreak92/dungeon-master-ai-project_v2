import random
from core.io_interface import GUI2DIO
import uuid
from typing import Dict, List, Optional, Any
import json
import logging
from items.item_factory import ItemFactory

logger = logging.getLogger(__name__)

# Mappa delle abilità associate alle caratteristiche (D&D 5e style)
ABILITA_ASSOCIATE = {
    "acrobazia": "destrezza",
    "furtività": "destrezza",
    "giocare d'azzardo": "destrezza",
    "addestrare animali": "saggezza",
    "percezione": "saggezza",
    "intuito": "saggezza",
    "natura": "intelligenza",
    "religione": "intelligenza",
    "arcano": "intelligenza",
    "storia": "intelligenza",
    "indagare": "intelligenza",
    "persuasione": "carisma",
    "intimidire": "carisma",
    "inganno": "carisma",
    "atletica": "forza",
    "sopravvivenza": "saggezza",
    "medicina": "saggezza"
}

class Dado:
    def __init__(self, facce):
        self.facce = facce

    def tira(self):
        return random.randint(1, self.facce)

class Entita:
    """Classe base per tutte le entità del gioco."""
    
    def __init__(self, nome=None, id=None, posizione=None, token="E"):
        """
        Inizializza una nuova entità.
        
        Args:
            nome (str, optional): Nome dell'entità. Defaults to None.
            id (str, optional): ID univoco dell'entità. Defaults to None.
            posizione (tuple, optional): Posizione (x, y) dell'entità. Defaults to None.
            token (str, optional): Token per rappresentazione testuale. Defaults to "E".
        """
        self.id = id or str(uuid.uuid4())
        self.nome = nome or f"Entita-{self.id[:8]}"
        self.token = token
        self.stato = "normale"  # Stati possibili: normale, invisibile, morto, ecc.
        self.interagibile = True
        self.visibile = True
        self.tags = []
        
        # Attributo id per compatibilità con il sistema ECS
        self.id = id if id else str(uuid.uuid4())
        
        # Tags per il sistema ECS
        self.tags = set()
        
        # Valori base delle caratteristiche
        self.forza_base = 10
        self.destrezza_base = 10
        self.costituzione_base = 10
        self.intelligenza_base = 10
        self.saggezza_base = 10
        self.carisma_base = 10
        
        # Modificatori calcolati
        self.modificatore_forza = self.calcola_modificatore(self.forza_base)
        self.modificatore_destrezza = self.calcola_modificatore(self.destrezza_base)
        self.modificatore_costituzione = self.calcola_modificatore(self.costituzione_base)
        self.modificatore_intelligenza = self.calcola_modificatore(self.intelligenza_base)
        self.modificatore_saggezza = self.calcola_modificatore(self.saggezza_base)
        self.modificatore_carisma = self.calcola_modificatore(self.carisma_base)
        
        # Attributi per il movimento e la posizione
        self.x = 0
        self.y = 0
        self.mappa_corrente = "default_map" # Nome della mappa corrente dell'entità
        if posizione and isinstance(posizione, tuple) and len(posizione) == 2:
            self.x = posizione[0]
            self.y = posizione[1]
        
        # Competenze in abilità
        self.abilita_competenze = {}  # Esempio: {"percezione": True, "persuasione": False}
        self.bonus_competenza = 2  # Può crescere con il livello
        
        # Altri attributi
        self.difesa = 0
        self.inventario = []
        self.oro = 0
        self.esperienza = 0
        self.livello = 1
        self.arma = None
        self.armatura = None
        self.accessori = []
        
        # Contesto di gioco
        self.gioco = None
        
    def set_game_context(self, gioco):
        """
        Imposta il contesto di gioco per questa entità.
        
        Args:
            gioco: L'istanza del gioco
        """
        self.gioco = gioco
        
        # Propaga il contesto agli oggetti contenuti nell'inventario
        for item in self.inventario:
            if hasattr(item, 'set_game_context'):
                item.set_game_context(gioco)
                
    def subisci_danno(self, danno, gioco=None):
        """Metodo unificato per subire danno, considerando la difesa"""
        # Usa il contesto di gioco memorizzato se non viene fornito
        game_ctx = gioco if gioco else getattr(self, 'gioco', None)
        
        danno_effettivo = max(1, danno - self.difesa)
        self.hp = max(0, self.hp - danno_effettivo)
        
        if game_ctx:
            game_ctx.io.mostra_messaggio(f"{self.nome} subisce {danno_effettivo} danni!")
            
        return self.hp > 0
        
    def attacca(self, bersaglio, gioco=None):
        """Metodo unificato per attaccare"""
        # Usa il contesto di gioco memorizzato se non viene fornito
        game_ctx = gioco if gioco else getattr(self, 'gioco', None)
        
        danno = self.modificatore_forza
        
        if game_ctx:
            game_ctx.io.mostra_messaggio(f"{self.nome} attacca {bersaglio.nome} e infligge {danno} danni!")
            
        return bersaglio.subisci_danno(danno, game_ctx)
        
    def cura(self, quantita, gioco=None):
        """Cura l'entità"""
        # Usa il contesto di gioco memorizzato se non viene fornito
        game_ctx = gioco if gioco else getattr(self, 'gioco', None)
        
        self.hp = min(self.hp_max, self.hp + quantita)
        
        if game_ctx:
            game_ctx.io.mostra_messaggio(f"{self.nome} recupera {quantita} punti vita!")
        
    def aggiungi_item(self, item):
        """Aggiunge un item all'inventario"""
        # Se l'item è una stringa, verifichiamo se corrisponde a un oggetto conosciuto
        if isinstance(item, str):
            from util.data_manager import get_data_manager
            from items.oggetto import Oggetto
            
            data_manager = get_data_manager()
            
            # Cerca nelle pozioni
            pozioni = data_manager.load_data("oggetti", "pozioni.json")
            for pozione in pozioni:
                if pozione["nome"] == item or (item == "Pozione" and pozione["nome"] == "Pozione di cura"):
                    # Crea un oggetto corrispondente
                    oggetto = Oggetto.from_dict(pozione)
                    self.inventario.append(oggetto)
                    return
                    
            # Se non trova corrispondenze, aggiungi come stringa
            self.inventario.append(item)
        else:
            self.inventario.append(item)
        
    def rimuovi_item(self, nome_item):
        """Rimuove un item dall'inventario"""
        for item in self.inventario:
            if (isinstance(item, str) and item == nome_item) or (hasattr(item, 'nome') and item.nome == nome_item):
                self.inventario.remove(item)
                return True
        return False
        
    def e_vivo(self):
        """Verifica se l'entità è viva"""
        return self.hp > 0
        
    def ferisci(self, danno, gioco):
        """Metodo alternativo per subire danno, per compatibilità"""
        return self.subisci_danno(danno, gioco)
        
    def aggiungi_oro(self, quantita, gioco=None):
        """Aggiunge oro all'entità"""
        # Usa il contesto di gioco memorizzato se non viene fornito
        game_ctx = gioco if gioco else getattr(self, 'gioco', None)
        
        self.oro += quantita
        
        if game_ctx:
            game_ctx.io.mostra_messaggio(f"{self.nome} ha ricevuto {quantita} monete d'oro! (Totale: {self.oro})")
        
    def guadagna_esperienza(self, quantita, gioco=None):
        """Aggiunge esperienza e verifica se è possibile salire di livello"""
        # Usa il contesto di gioco memorizzato se non viene fornito
        game_ctx = gioco if gioco else getattr(self, 'gioco', None)
        
        self.esperienza += quantita
        
        # Verifica salita di livello: 100 * livello attuale
        esperienza_necessaria = 100 * self.livello
        
        if self.esperienza >= esperienza_necessaria:
            self.livello += 1
            self.esperienza -= esperienza_necessaria
            self._sali_livello(game_ctx)
            return True
        return False
        
    def _sali_livello(self, gioco=None):
        """Applica i miglioramenti per il salire di livello"""
        # Usa il contesto di gioco memorizzato se non viene fornito
        game_ctx = gioco if gioco else getattr(self, 'gioco', None)
        
        self.hp_max += 5
        self.hp = self.hp_max  # Cura completamente quando sale di livello
        
        # Incrementa un valore base a caso
        import random
        caratteristiche = ["forza_base", "destrezza_base", "costituzione_base", 
                          "intelligenza_base", "saggezza_base", "carisma_base"]
        caratteristica_da_aumentare = random.choice(caratteristiche)
        
        setattr(self, caratteristica_da_aumentare, getattr(self, caratteristica_da_aumentare) + 1)
        # Ricalcola il modificatore corrispondente
        nome_modificatore = f"modificatore_{caratteristica_da_aumentare[:-5]}"  # Rimuovi "_base"
        setattr(self, nome_modificatore, self.calcola_modificatore(getattr(self, caratteristica_da_aumentare)))
        
        self.difesa += 1
        
        if game_ctx:
            game_ctx.io.mostra_messaggio(f"\n*** {self.nome} è salito al livello {self.livello}! ***")
            game_ctx.io.mostra_messaggio(f"La sua {caratteristica_da_aumentare.replace('_base', '')}, difesa e salute massima sono aumentate!")

    def prova_abilita(self, abilita, difficolta, gioco=None):
        # Usa il contesto di gioco memorizzato se non viene fornito
        game_ctx = gioco if gioco else getattr(self, 'gioco', None)
        
        dado = Dado(20)
        tiro = dado.tira()
        
        # Ottieni il modificatore appropriato
        if abilita == "forza":
            modificatore = self.modificatore_forza
        elif abilita == "destrezza":
            modificatore = self.modificatore_destrezza
        # e così via...
        else:
            modificatore = getattr(self, f"modificatore_{abilita}", 0)
            
        risultato = tiro + modificatore
        
        if game_ctx:
            game_ctx.io.mostra_messaggio(f"{self.nome} tira un {tiro} + {modificatore} ({abilita}) = {risultato}")
            
        return risultato >= difficolta

    def tiro_salvezza(self, tipo, difficolta, gioco=None):
        return self.prova_abilita(tipo, difficolta, gioco)

    def calcola_modificatore(self, punteggio_caratteristica):
        return (punteggio_caratteristica - 10) // 2

    @property
    def forza(self):
        return self.modificatore_forza

    @forza.setter
    def forza(self, valore):
        self.modificatore_forza = valore
        
    @property
    def destrezza(self):
        return self.modificatore_destrezza
        
    @destrezza.setter
    def destrezza(self, valore):
        self.modificatore_destrezza = valore
        
    @property
    def costituzione(self):
        return self.modificatore_costituzione
        
    @costituzione.setter
    def costituzione(self, valore):
        self.modificatore_costituzione = valore
        
    @property
    def intelligenza(self):
        return self.modificatore_intelligenza
        
    @intelligenza.setter
    def intelligenza(self, valore):
        self.modificatore_intelligenza = valore
        
    @property
    def saggezza(self):
        return self.modificatore_saggezza
        
    @saggezza.setter
    def saggezza(self, valore):
        self.modificatore_saggezza = valore
        
    @property
    def carisma(self):
        return self.modificatore_carisma
        
    @carisma.setter
    def carisma(self, valore):
        self.modificatore_carisma = valore

    def imposta_posizione(self, mappa_nome_o_x, x_o_y=None, y=None):
        """
        Imposta la posizione dell'entità su una mappa specifica o solo le coordinate
        
        Supporta due modalità di chiamata:
        1. imposta_posizione(mappa_nome, x, y) - imposta mappa e coordinate
        2. imposta_posizione(x, y) - imposta solo le coordinate mantenendo la mappa corrente
        
        Args:
            mappa_nome_o_x: Nome della mappa o coordinata X
            x_o_y: Coordinata X o Y
            y: Coordinata Y o None
        """
        if y is None:
            # Vecchia modalità: imposta_posizione(x, y)
            x = mappa_nome_o_x
            y = x_o_y
            # Non modifichiamo mappa_corrente
        else:
            # Nuova modalità: imposta_posizione(mappa_nome, x, y)
            self.mappa_corrente = mappa_nome_o_x
            x = x_o_y
        
        self.x = x
        self.y = y
    
    def ottieni_posizione(self):
        """
        Restituisce la posizione corrente dell'entità
        
        Returns:
            tuple: Coordinate (x, y) o None se non impostata
        """
        if self.mappa_corrente:
            return (self.x, self.y)
        return None

    def modificatore_abilita(self, nome_abilita, gioco):
        """Calcola il modificatore totale di un'abilità considerando la competenza"""
        caratteristica = ABILITA_ASSOCIATE.get(nome_abilita.lower())
        if not caratteristica:
            gioco.io.mostra_messaggio(f"Abilità sconosciuta: {nome_abilita}")
            return 0

        modificatore_base = getattr(self, f"modificatore_{caratteristica}", 0)
        competenza_bonus = self.bonus_competenza if self.abilita_competenze.get(nome_abilita.lower()) else 0
        return modificatore_base + competenza_bonus

    def to_dict(self, already_serialized=None):
        """
        Converte l'entità in un dizionario per la serializzazione.
        
        Args:
            already_serialized (set, optional): Set di ID di oggetti già serializzati
            
        Returns:
            dict: Dizionario rappresentante lo stato dell'entità.
        """
        # Se already_serialized non è stato passato, inizializzalo come un set vuoto
        if already_serialized is None:
            already_serialized = set()
            
        # Verifica se questa entità è già stata serializzata
        if self.id in already_serialized:
            return {"id": self.id, "ref": True}  # Ritorna solo un riferimento all'ID
            
        # Aggiungi questa entità al set degli oggetti già serializzati
        already_serialized.add(self.id)
        
        return {
            "id": self.id,
            "nome": self.nome,
            "token": self.token,
            "stato": self.stato,
            "interagibile": self.interagibile,
            "visibile": self.visibile,
            "tags": list(self.tags),
            "tipo": self.__class__.__name__,
            "forza_base": self.forza_base,
            "destrezza_base": self.destrezza_base,
            "costituzione_base": self.costituzione_base,
            "intelligenza_base": self.intelligenza_base,
            "saggezza_base": self.saggezza_base,
            "carisma_base": self.carisma_base,
            "x": self.x,
            "y": self.y,
            "mappa_corrente": self.mappa_corrente,
            "abilita_competenze": self.abilita_competenze,
            "bonus_competenza": self.bonus_competenza,
            "difesa": self.difesa,
            "inventario": [item.to_dict() if hasattr(item, 'to_dict') else item for item in self.inventario],
            "oro": self.oro,
            "esperienza": self.esperienza,
            "livello": self.livello,
            "arma": self.arma.to_dict() if self.arma and hasattr(self.arma, 'to_dict') else None,
            "armatura": self.armatura.to_dict() if self.armatura and hasattr(self.armatura, 'to_dict') else None,
            "accessori": [acc.to_dict() if hasattr(acc, 'to_dict') else acc for acc in self.accessori]
        }
    
    # Alias per compatibilità con il sistema ECS
    serialize = to_dict
    
    @classmethod
    def from_dict(cls, data):
        """
        Crea un'entità da un dizionario.
        
        Args:
            data (dict): Dizionario con i dati dell'entità.
            
        Returns:
            Entita: Istanza dell'entità creata.
        """
        entita = cls(
            nome=data.get("nome"),
            id=data.get("id"),
            token=data.get("token", "E")
        )
        
        entita.stato = data.get("stato", "normale")
        entita.interagibile = data.get("interagibile", True)
        entita.visibile = data.get("visibile", True)
        entita.tags = set(data.get("tags", []))
        
        entita.forza_base = data.get("forza_base", 10)
        entita.destrezza_base = data.get("destrezza_base", 10)
        entita.costituzione_base = data.get("costituzione_base", 10)
        entita.intelligenza_base = data.get("intelligenza_base", 10)
        entita.saggezza_base = data.get("saggezza_base", 10)
        entita.carisma_base = data.get("carisma_base", 10)
        
        # Ricalcola modificatori dopo aver impostato le stats base
        entita.modificatore_forza = entita.calcola_modificatore(entita.forza_base)
        entita.modificatore_destrezza = entita.calcola_modificatore(entita.destrezza_base)
        entita.modificatore_costituzione = entita.calcola_modificatore(entita.costituzione_base)
        entita.modificatore_intelligenza = entita.calcola_modificatore(entita.intelligenza_base)
        entita.modificatore_saggezza = entita.calcola_modificatore(entita.saggezza_base)
        entita.modificatore_carisma = entita.calcola_modificatore(entita.carisma_base)

        entita.x = data.get("x", 0)
        entita.y = data.get("y", 0)
        entita.mappa_corrente = data.get("mappa_corrente") # Rimosso default "overworld" per coerenza se non presente
        
        entita.abilita_competenze = data.get("abilita_competenze", {})
        entita.bonus_competenza = data.get("bonus_competenza", 2)
        entita.difesa = data.get("difesa", 0)
        
        # Non più solo data.get, ma deserializzazione oggetti
        # entita.inventario = data.get("inventario", []) 
        entita.oro = data.get("oro", 0)
        
        entita.esperienza = data.get("esperienza", 0)
        entita.livello = data.get("livello", 1)
        
        # Non più solo data.get per arma, armatura, accessori
        # entita.arma = data.get("arma")
        # entita.armatura = data.get("armatura")
        # entita.accessori = data.get("accessori", [])

        # Deserializzazione Inventario e Equipaggiamento
        raw_inventario = data.get("inventario", [])
        entita.inventario = []
        if raw_inventario: # Solo se c'è qualcosa da processare
            for item_data_dict in raw_inventario:
                if isinstance(item_data_dict, dict):
                    item_instance = ItemFactory.crea_da_dict(item_data_dict)
                    if item_instance:
                        entita.inventario.append(item_instance)
                # else: Potremmo loggare un warning se l'item non è un dict
        
        arma_data_dict = data.get("arma")
        entita.arma = ItemFactory.crea_da_dict(arma_data_dict) if isinstance(arma_data_dict, dict) else None

        armatura_data_dict = data.get("armatura")
        entita.armatura = ItemFactory.crea_da_dict(armatura_data_dict) if isinstance(armatura_data_dict, dict) else None

        raw_accessori = data.get("accessori", [])
        entita.accessori = []
        if raw_accessori: # Solo se c'è qualcosa da processare
            for acc_data_dict in raw_accessori:
                if isinstance(acc_data_dict, dict):
                    item_instance = ItemFactory.crea_da_dict(acc_data_dict)
                    if item_instance:
                        entita.accessori.append(item_instance)
        
        return entita
    
    # Alias per compatibilità con il sistema ECS
    deserialize = classmethod(from_dict)
    
    def __str__(self):
        """
        Rappresentazione testuale dell'entità.
        
        Returns:
            str: Stringa che rappresenta l'entità.
        """
        pos_str = f"({self.x}, {self.y})" if (self.x, self.y) != (0, 0) else "(?, ?)"
        return f"{self.nome} [{self.token}] @ {pos_str} su '{self.mappa_corrente}'"

    def verifica_valori_vitali(self):
        pass # Implementazione specifica nelle sottoclassi (es. Giocatore)

    def muovi(self, dx, dy, gestore_mappe):
        """
        Tenta di muovere l'entità sulla mappa.

        Args:
            dx (int): Spostamento sull'asse X.
            dy (int): Spostamento sull'asse Y.
            gestore_mappe (GestitoreMappe): Il gestore delle mappe per i controlli.

        Returns:
            dict: Un dizionario con {"successo": bool, "nuova_posizione": Optional[tuple], "messaggio": Optional[str]}
        """
        if not gestore_mappe:
            logger.error(f"Entita {self.id}: GestoreMappe non fornito per il movimento.")
            return {"successo": False, "nuova_posizione": None, "messaggio": "Errore interno del server."}

        mappa = gestore_mappe.ottieni_mappa(self.mappa_corrente)
        if not mappa:
            logger.warning(f"Entita {self.id}: Mappa corrente '{self.mappa_corrente}' non trovata in GestoreMappe.")
            return {"successo": False, "nuova_posizione": None, "messaggio": f"Mappa '{self.mappa_corrente}' non caricata."}

        nuova_x = self.x + dx
        nuova_y = self.y + dy

        # Log del tentativo di movimento
        logger.debug(f"Entita {self.id} ({self.nome}) a ({self.x},{self.y}) su '{self.mappa_corrente}' tenta movimento a ({nuova_x},{nuova_y}). Dx: {dx}, Dy: {dy}")


        # 1. Controllo limiti mappa e se la casella base è calpestabile (non un muro definito nella griglia)
        if not mappa.is_posizione_valida(nuova_x, nuova_y):
            logger.debug(f"Movimento fallito per {self.id}: ({nuova_x},{nuova_y}) fuori dai limiti della mappa ({mappa.larghezza}x{mappa.altezza}) o su casella non calpestabile (muro base).")
            return {"successo": False, "nuova_posizione": None, "messaggio": "Non puoi muoverti lì."}

        # Il controllo mappa.is_casella_calpestabile(nuova_x, nuova_y) è ora implicito in mappa.is_posizione_valida,
        # che verifica self.griglia[y][x] == 0.

        # 3. Controllo collisione con altri NPG (se non è il giocatore stesso)
        #    Per ora, un'entità non può entrare in una casella occupata da un'altra entità.
        #    Questa logica potrebbe diventare più complessa (es. NPG amichevoli che si spostano)
        altre_entita_nella_mappa = []
        if hasattr(mappa, 'npg') and isinstance(mappa.npg, dict): # mappa.npg è {pos_key_str: npg_instance}
            altre_entita_nella_mappa.extend(mappa.npg.values())
        # Aggiungi anche il giocatore se presente sulla mappa e non è l'entità che si sta muovendo
        giocatore_sulla_mappa = mappa.giocatore if hasattr(mappa, 'giocatore') else None
        if giocatore_sulla_mappa and giocatore_sulla_mappa.id != self.id:
             altre_entita_nella_mappa.append(giocatore_sulla_mappa)


        for altra_entita in altre_entita_nella_mappa:
            if altra_entita.id != self.id and altra_entita.x == nuova_x and altra_entita.y == nuova_y and altra_entita.mappa_corrente == self.mappa_corrente:
                logger.debug(f"Movimento fallito per {self.id}: collisione con entità {altra_entita.id} a ({nuova_x},{nuova_y}).")
                return {"successo": False, "nuova_posizione": None, "messaggio": f"C'è già qualcuno lì ({altra_entita.nome})."}

        # 4. Controllo collisione con oggetti bloccanti sulla mappa
        oggetto_a_destinazione = mappa.ottieni_oggetto_a(nuova_x, nuova_y)
        if oggetto_a_destinazione and not getattr(oggetto_a_destinazione, 'calpestabile', True): # Assumiamo calpestabile se l'attributo non esiste
            # Ulteriore controllo: se l'oggetto è una porta e l'entità è il giocatore, gestisci la transizione
            if self.token == '@' and getattr(oggetto_a_destinazione, 'tipo_oggetto', '') == 'porta':
                destinazione_porta = getattr(oggetto_a_destinazione, 'destinazione', None)
                if destinazione_porta:
                    logger.info(f"Giocatore {self.id} interagisce con porta a ({nuova_x},{nuova_y}) verso '{destinazione_porta}'.")
                    # La logica di cambio mappa la gestirà il chiamante (es. MappaState)
                    # Qui segnaliamo solo il successo e la potenziale transizione.
                    self.x = nuova_x 
                    self.y = nuova_y
                    return {"successo": True, "nuova_posizione": (self.x, self.y), "messaggio": f"Sei entrato in {oggetto_a_destinazione.nome}.", "cambio_mappa_richiesto": destinazione_porta, "nuova_mappa_coords": getattr(oggetto_a_destinazione, 'pos_destinazione', None)}
            
            logger.debug(f"Movimento fallito per {self.id}: collisione con oggetto bloccante '{oggetto_a_destinazione.nome}' a ({nuova_x},{nuova_y}).")
            return {"successo": False, "nuova_posizione": None, "messaggio": f"Non puoi passare attraverso {oggetto_a_destinazione.nome}."}


        # Movimento riuscito
        self.x = nuova_x
        self.y = nuova_y
        logger.info(f"Movimento riuscito per {self.id}: nuova posizione ({self.x},{self.y}) su '{self.mappa_corrente}'.")
        
        # Eventuale cambio mappa se si finisce su un tile di transizione
        # Questa logica è più complessa e potrebbe risiedere in MappaState o GameManager
        # Per ora, il metodo muovi si occupa solo dell'aggiornamento delle coordinate sulla mappa corrente.
        # Ma se la mappa ha dei trigger di transizione, potremmo verificarli qui.
        trigger_transizione = mappa.ottieni_trigger_transizione_a(nuova_x, nuova_y)
        if trigger_transizione:
            logger.info(f"Entità {self.id} ha attivato un trigger di transizione a ({nuova_x},{nuova_y}) verso la mappa '{trigger_transizione['destinazione_mappa']}'.")
            # Potremmo voler aggiornare la mappa corrente dell'entità qui o segnalarlo
            return {
                "successo": True, 
                "nuova_posizione": (self.x, self.y), 
                "messaggio": "Hai trovato un passaggio!", 
                "cambio_mappa_richiesto": trigger_transizione['destinazione_mappa'],
                "nuova_mappa_coords": trigger_transizione.get('pos_destinazione') 
            }

        return {"successo": True, "nuova_posizione": (self.x, self.y), "messaggio": "Movimento effettuato."}

    def __str__(self):
        return f"{self.nome} (ID: {self.id}) a ({self.x}, {self.y}) su '{self.mappa_corrente}'"
