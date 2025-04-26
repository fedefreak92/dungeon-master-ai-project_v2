import random
from core.io_interface import GUI2DIO
import uuid
from typing import Dict, List, Optional, Any
import json
import logging

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
        self.posizione = posizione
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
        
        # Attributi per la posizione
        self.x = 0
        self.y = 0
        self.mappa_corrente = None
        
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

    def calcola_modificatore(self, valore):
        return (valore - 10) // 2

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
            "posizione": self.posizione,
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
            "inventario": self.inventario,
            "oro": self.oro,
            "esperienza": self.esperienza,
            "livello": self.livello,
            "arma": self.arma,
            "armatura": self.armatura,
            "accessori": self.accessori
        }
    
    # Alias per compatibilità con il sistema ECS
    serialize = to_dict
    
    def to_msgpack(self, already_serialized=None):
        """
        Converte l'entità in formato MessagePack per la serializzazione.
        
        Args:
            already_serialized (set, optional): Set di ID di oggetti già serializzati
            
        Returns:
            bytes: Dati serializzati in formato MessagePack.
        """
        try:
            import msgpack
            return msgpack.packb(self.to_dict(already_serialized), use_bin_type=True)
        except Exception as e:
            logger.error(f"Errore nella serializzazione MessagePack dell'entità {self.id}: {e}")
            # Fallback a dizionario serializzato in JSON e poi convertito in bytes
            return json.dumps(self.to_dict(already_serialized)).encode()
    
    # Alias per compatibilità con il sistema ECS
    serialize_msgpack = to_msgpack
    
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
            posizione=data.get("posizione"),
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
        
        entita.x = data.get("x", 0)
        entita.y = data.get("y", 0)
        entita.mappa_corrente = data.get("mappa_corrente", "overworld")
        
        entita.abilita_competenze = data.get("abilita_competenze", {})
        entita.bonus_competenza = data.get("bonus_competenza", 2)
        entita.difesa = data.get("difesa", 0)
        
        entita.inventario = data.get("inventario", [])
        entita.oro = data.get("oro", 0)
        
        entita.esperienza = data.get("esperienza", 0)
        entita.livello = data.get("livello", 1)
        
        entita.arma = data.get("arma")
        entita.armatura = data.get("armatura")
        entita.accessori = data.get("accessori", [])
        
        return entita
    
    # Alias per compatibilità con il sistema ECS
    deserialize = classmethod(from_dict)
    
    @classmethod
    def from_msgpack(cls, data_bytes):
        """
        Crea un'entità da dati in formato MessagePack.
        
        Args:
            data_bytes (bytes): Dati serializzati in formato MessagePack.
            
        Returns:
            Entita: Istanza dell'entità creata.
        """
        try:
            import msgpack
            data = msgpack.unpackb(data_bytes, raw=False)
            return cls.from_dict(data)
        except Exception as e:
            logger.error(f"Errore nella deserializzazione MessagePack: {e}")
            try:
                # Tenta di interpretare i dati come JSON
                data = json.loads(data_bytes.decode())
                return cls.from_dict(data)
            except Exception as e2:
                logger.error(f"Errore anche con fallback JSON: {e2}")
                return cls()  # Ritorna un'entità vuota in caso di errore
    
    # Alias per compatibilità con il sistema ECS
    deserialize_msgpack = classmethod(from_msgpack)
    
    def __str__(self):
        """
        Rappresentazione testuale dell'entità.
        
        Returns:
            str: Stringa che rappresenta l'entità.
        """
        pos_str = f"({self.posizione[0]}, {self.posizione[1]})" if self.posizione else "(?, ?)"
        return f"{self.nome} [{self.token}] @ {pos_str}"
