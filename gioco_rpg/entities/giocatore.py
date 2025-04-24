import json
import os
import uuid
from items.oggetto import Oggetto
from entities.entita import Entita, ABILITA_ASSOCIATE
from util.dado import Dado
import random
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Dadi per tirare le statistiche
d6 = Dado(6)

class Giocatore(Entita):
    def __init__(self, nome, classe, razza="umano", livello=1, hp=None, token="@", id=None):
        """
        Inizializza un nuovo giocatore.
        
        Args:
            nome (str): Nome del giocatore
            classe (str): Classe del giocatore (guerriero, mago, etc.)
            razza (str, optional): Razza del giocatore. Defaults to "umano".
            livello (int, optional): Livello iniziale. Defaults to 1.
            hp (int, optional): Punti vita. Se None, vengono calcolati in base alla classe.
            token (str, optional): Token per rappresentazione ASCII. Defaults to "@".
            id (str, optional): ID univoco. Se None, viene generato.
        """
        super().__init__(nome=nome, id=id, token=token)
        
        self.classe = classe
        self.razza = razza
        self.livello = livello
        
        # Imposta statistiche base in base alla classe
        self._init_stats_by_class(classe)
        
        # Punti vita basati sulla costituzione
        if hp is None:
            # Estrai il nome della classe corretto per il calcolo degli HP
            classe_nome = classe.get('id', classe) if isinstance(classe, dict) else classe
            classe_nome = str(classe_nome).lower()
            
            base_hp = {"guerriero": 10, "mago": 6, "ladro": 8}.get(classe_nome, 8)
            self.hp_max = base_hp + self.modificatore_costituzione
            self.hp = self.hp_max
        else:
            self.hp = hp
            self.hp_max = hp
        
        # Inventario e denaro
        self.inventario = []
        self.oro = 10
        
        # Equipaggiamento
        self.arma = None
        self.armatura = None
        self.accessori = []
        
        # Esperienza
        self.esperienza = 0
        self.esperienza_prossimo_livello = self._calcola_exp_livello(livello + 1)
        
        # Abilità speciali per classe
        self.abilita_speciali = self._init_abilita_speciali()
        
        # Missioni
        self.missioni = []
        self.missioni_completate = []
        
        # Dialogo
        self.dialogo_corrente = None
        
        # Stato di gioco
        self.nome_mappa_corrente = "taverna"  # Mappa di partenza
        
    def imposta_classe(self, classe):
        """
        Imposta o cambia la classe del giocatore e aggiorna le statistiche.
        
        Args:
            classe (str o dict): La nuova classe del giocatore
            
        Returns:
            bool: True se la classe è stata impostata con successo
        """
        # Salva la vecchia classe per log
        vecchia_classe = self.classe
        
        # Aggiorna l'attributo classe
        self.classe = classe
        
        # Reinizializza le statistiche in base alla nuova classe
        self._init_stats_by_class(classe)
        
        # Aggiorna le abilità speciali
        self.abilita_speciali = self._init_abilita_speciali()
        
        # Log del cambio classe
        classe_nome = classe.get('id', str(classe)) if isinstance(classe, dict) else str(classe)
        vecchia_classe_nome = vecchia_classe.get('id', str(vecchia_classe)) if isinstance(vecchia_classe, dict) else str(vecchia_classe)
        logger.info(f"Classe del giocatore {self.nome} cambiata da {vecchia_classe_nome} a {classe_nome}")
        
        return True
        
    def _init_stats_by_class(self, classe):
        """
        Inizializza le statistiche base in base alla classe.
        
        Args:
            classe (str o dict): Classe del giocatore
        """
        # Valori predefiniti
        self.forza_base = 10
        self.destrezza_base = 10
        self.costituzione_base = 10
        self.intelligenza_base = 10
        self.saggezza_base = 10
        self.carisma_base = 10
        
        # Estrai il nome della classe in caso sia un dizionario
        if isinstance(classe, dict):
            classe_id = classe.get('id')
            if classe_id:
                classe_nome = str(classe_id).lower()
            else:
                classe_nome = "guerriero"  # Valore predefinito in caso di assenza
                logger.warning(f"Il dizionario classe non contiene un campo 'id', usato valore predefinito: {classe_nome}")
        else:
            classe_nome = str(classe).lower()
        
        # Modifiche in base alla classe
        if classe_nome == "guerriero":
            self.forza_base = 14
            self.costituzione_base = 13
            self.abilita_competenze = {
                "atletica": True,
                "intimidire": True,
                "percezione": True
            }
            
        elif classe_nome == "mago":
            self.intelligenza_base = 14
            self.saggezza_base = 12
            self.abilita_competenze = {
                "arcano": True,
                "storia": True,
                "investigazione": True
            }
            
        elif classe_nome == "ladro":
            self.destrezza_base = 14
            self.carisma_base = 12
            self.abilita_competenze = {
                "acrobazia": True,
                "furtività": True,
                "raggirare": True
            }
            
        # Ricalcola i modificatori
        self.modificatore_forza = self.calcola_modificatore(self.forza_base)
        self.modificatore_destrezza = self.calcola_modificatore(self.destrezza_base)
        self.modificatore_costituzione = self.calcola_modificatore(self.costituzione_base)
        self.modificatore_intelligenza = self.calcola_modificatore(self.intelligenza_base)
        self.modificatore_saggezza = self.calcola_modificatore(self.saggezza_base)
        self.modificatore_carisma = self.calcola_modificatore(self.carisma_base)
        
    def _init_abilita_speciali(self):
        """
        Inizializza le abilità speciali in base alla classe.
        
        Returns:
            dict: Dizionario delle abilità speciali
        """
        abilita = {}
        
        # Estrai il nome della classe in caso sia un dizionario
        if isinstance(self.classe, dict):
            classe_nome = self.classe.get('id', 'guerriero').lower()
        else:
            classe_nome = str(self.classe).lower()
        
        if classe_nome == "guerriero":
            abilita["secondo_fiato"] = {
                "nome": "Secondo Fiato",
                "descrizione": "Recupera 1d10 + livello HP come azione bonus.",
                "utilizzi": 1,
                "utilizzi_max": 1,
                "ripristino": "riposo_breve"
            }
            
        elif classe_nome == "mago":
            abilita["dardo_incantato"] = {
                "nome": "Dardo Incantato",
                "descrizione": "Lancia un dardo magico che infligge 1d4+1 danni.",
                "utilizzi": 3,
                "utilizzi_max": 3,
                "ripristino": "riposo_lungo"
            }
            
        elif classe_nome == "ladro":
            abilita["attacco_furtivo"] = {
                "nome": "Attacco Furtivo",
                "descrizione": "Infligge 1d6 danni extra quando hai vantaggio.",
                "utilizzi": float('inf'),
                "utilizzi_max": float('inf'),
                "ripristino": None
            }
            
        return abilita
        
    def _calcola_exp_livello(self, livello):
        """
        Calcola l'esperienza necessaria per il livello specificato.
        
        Args:
            livello (int): Livello per cui calcolare l'esperienza
            
        Returns:
            int: Esperienza necessaria
        """
        # Formula semplificata per l'XP necessario
        return (livello * livello * 100)
        
    def guadagna_esperienza(self, exp):
        """
        Aggiunge esperienza al giocatore e gestisce l'avanzamento di livello.
        
        Args:
            exp (int): Quantità di esperienza da aggiungere
            
        Returns:
            bool: True se il giocatore è salito di livello
        """
        self.esperienza += exp
        
        if self.esperienza >= self.esperienza_prossimo_livello:
            return self.aumenta_livello()
            
        return False
        
    def aumenta_livello(self):
        """
        Aumenta di livello il giocatore.
        
        Returns:
            bool: True se l'aumento è avvenuto con successo
        """
        self.livello += 1
        
        # Calcola i nuovi HP
        # Estrai il nome della classe in caso sia un dizionario
        if isinstance(self.classe, dict):
            classe_nome = self.classe.get('id', 'guerriero').lower()
        else:
            classe_nome = str(self.classe).lower()
            
        dadi_vita = {"guerriero": 10, "mago": 6, "ladro": 8}.get(classe_nome, 8)
        guadagno_hp = max(1, Dado(dadi_vita).tira() + self.modificatore_costituzione)
        self.hp_max += guadagno_hp
        self.hp += guadagno_hp
        
        # Aggiorna il bonus di competenza ogni 4 livelli
        self.bonus_competenza = 2 + ((self.livello - 1) // 4)
        
        # Aggiorna la soglia per il prossimo livello
        self.esperienza_prossimo_livello = self._calcola_exp_livello(self.livello + 1)
        
        return True
        
    def aggiungi_item(self, item):
        """
        Aggiunge un oggetto all'inventario.
        
        Args:
            item: Oggetto da aggiungere
        """
        if isinstance(item, list):
            for i in item:
                self.inventario.append(i)
        else:
            self.inventario.append(item)
            
    def rimuovi_item(self, item_nome):
        """
        Rimuove un oggetto dall'inventario.
        
        Args:
            item_nome (str): Nome dell'oggetto da rimuovere
            
        Returns:
            bool: True se l'oggetto è stato rimosso, False altrimenti
        """
        for i, item in enumerate(self.inventario):
            nome_item = item.nome if hasattr(item, 'nome') else item
            if nome_item == item_nome:
                self.inventario.pop(i)
                return True
        return False
        
    def equipaggia_arma(self, arma):
        """
        Equipaggia un'arma.
        
        Args:
            arma: Arma da equipaggiare
        """
        self.arma = arma
        
    def equipaggia_armatura(self, armatura):
        """
        Equipaggia un'armatura.
        
        Args:
            armatura: Armatura da equipaggiare
        """
        self.armatura = armatura
        
    def riposa(self, tipo_riposo="breve"):
        """
        Fa riposare il giocatore.
        
        Args:
            tipo_riposo (str): "breve" o "lungo"
            
        Returns:
            int: Quantità di HP recuperati
        """
        hp_recuperati = 0
        
        if tipo_riposo == "breve":
            # Riposo breve: recupera 1d8 + modificatore costituzione
            recupero = Dado(8).tira() + self.modificatore_costituzione
            hp_recuperati = min(recupero, self.hp_max - self.hp)
            self.hp += hp_recuperati
            
            # Ripristina abilità
            for nome_abilita, abilita in self.abilita_speciali.items():
                if abilita["ripristino"] == "riposo_breve":
                    abilita["utilizzi"] = abilita["utilizzi_max"]
            
        elif tipo_riposo == "lungo":
            # Riposo lungo: recupera tutti gli HP
            hp_recuperati = self.hp_max - self.hp
            self.hp = self.hp_max
            
            # Ripristina tutte le abilità
            for nome_abilita, abilita in self.abilita_speciali.items():
                if abilita["ripristino"] in ["riposo_breve", "riposo_lungo"]:
                    abilita["utilizzi"] = abilita["utilizzi_max"]
        
        return hp_recuperati
        
    def subisci_danno(self, danno):
        """
        Fa subire danno al giocatore.
        
        Args:
            danno (int): Quantità di danno da infliggere
            
        Returns:
            int: Danno effettivamente inflitto
        """
        danno_effettivo = max(0, danno)
        self.hp -= danno_effettivo
        
        # Gestisci la morte
        if self.hp <= 0:
            self.hp = 0
            self.stato = "inconscio"
            
        return danno_effettivo
        
    def get_danno_arma(self):
        """
        Calcola il danno dell'arma corrente.
        
        Returns:
            int: Danno base dell'arma
        """
        if not self.arma:
            return 1  # Danno a mani nude
            
        # Implementazione di base
        if hasattr(self.arma, 'danno'):
            return self.arma.danno
            
        # Danni predefiniti se l'arma non ha l'attributo danno
        armi_base = {
            "spada": 6,
            "pugnale": 4,
            "ascia": 8,
            "bastone": 4,
            "arco": 6
        }
        
        if isinstance(self.arma, str):
            for tipo_arma, danno in armi_base.items():
                if tipo_arma in self.arma.lower():
                    return danno
                    
        return 4  # Danno predefinito
        
    def get_classe_armatura(self):
        """
        Calcola la classe armatura (CA) del giocatore.
        
        Returns:
            int: Classe armatura
        """
        ca_base = 10 + self.modificatore_destrezza
        
        if self.armatura:
            if hasattr(self.armatura, 'ca'):
                return self.armatura.ca
                
            # Calcolo predefinito
            armature_base = {
                "cuoio": 11,
                "cotta": 13,
                "piastre": 16,
                "scudo": 2  # Bonus
            }
            
            if isinstance(self.armatura, str):
                for tipo_armatura, ca in armature_base.items():
                    if tipo_armatura in self.armatura.lower():
                        # Se è uno scudo, aggiungi il bonus alla CA base
                        if tipo_armatura == "scudo":
                            return ca_base + ca
                        # Altrimenti, sostituisci la CA base con quella dell'armatura + mod destrezza
                        else:
                            return ca + min(2, self.modificatore_destrezza)
                            
        return ca_base
        
    def usa_abilita_speciale(self, nome_abilita):
        """
        Usa un'abilità speciale.
        
        Args:
            nome_abilita (str): Nome dell'abilità da usare
            
        Returns:
            dict: Risultato dell'abilità o None se non disponibile
        """
        if nome_abilita not in self.abilita_speciali:
            return None
            
        abilita = self.abilita_speciali[nome_abilita]
        
        if abilita["utilizzi"] <= 0:
            return {"successo": False, "messaggio": f"{abilita['nome']} non ha utilizzi rimanenti."}
            
        # Decrementa gli utilizzi
        abilita["utilizzi"] -= 1
        
        # Logica specifica per ogni abilità
        if nome_abilita == "secondo_fiato":
            recupero = Dado(10).tira() + self.livello
            hp_recuperati = min(recupero, self.hp_max - self.hp)
            self.hp += hp_recuperati
            return {
                "successo": True,
                "messaggio": f"Recuperi {hp_recuperati} punti ferita.",
                "hp_recuperati": hp_recuperati
            }
            
        elif nome_abilita == "dardo_incantato":
            danno = Dado(4).tira() + 1
            return {
                "successo": True,
                "messaggio": f"Il dardo magico infligge {danno} danni.",
                "danno": danno
            }
            
        elif nome_abilita == "attacco_furtivo":
            danno = Dado(6).tira()
            return {
                "successo": True,
                "messaggio": f"Colpisci un punto debole per {danno} danni extra.",
                "danno": danno
            }
            
        return {"successo": True, "messaggio": f"Hai usato {abilita['nome']}."}
        
    def get_tiro_salvezza(self, caratteristica):
        """
        Esegue un tiro salvezza per una caratteristica.
        
        Args:
            caratteristica (str): Caratteristica per cui fare il tiro
            
        Returns:
            dict: Risultato del tiro salvezza
        """
        # Ottieni il modificatore
        mod = getattr(self, f"modificatore_{caratteristica.lower()}", 0)
        
        # Aggiungi bonus di competenza se competente
        if caratteristica.lower() in ["forza", "costituzione"] and self.classe.lower() == "guerriero":
            mod += self.bonus_competenza
        elif caratteristica.lower() in ["intelligenza", "saggezza"] and self.classe.lower() == "mago":
            mod += self.bonus_competenza
        elif caratteristica.lower() in ["destrezza", "carisma"] and self.classe.lower() == "ladro":
            mod += self.bonus_competenza
            
        # Tira il dado
        tiro = Dado(20).tira()
        risultato = tiro + mod
        
        return {
            "tiro": tiro,
            "modificatore": mod,
            "risultato": risultato,
            "critico": tiro == 20,
            "fallimento_critico": tiro == 1
        }
        
    def get_tiro_abilita(self, abilita):
        """
        Esegue un tiro per un'abilità.
        
        Args:
            abilita (str): Abilità per cui fare il tiro
            
        Returns:
            dict: Risultato del tiro abilità
        """
        # Mappa delle abilità alle caratteristiche
        mappa_abilita_caratteristiche = {
            "acrobazia": "destrezza",
            "addestrare_animali": "saggezza",
            "arcano": "intelligenza",
            "atletica": "forza",
            "furtività": "destrezza",
            "indagare": "intelligenza",
            "inganno": "carisma",
            "intimidire": "carisma",
            "medicina": "saggezza",
            "natura": "intelligenza",
            "percezione": "saggezza",
            "persuasione": "carisma",
            "rapidità_di_mano": "destrezza",
            "religione": "intelligenza",
            "sopravvivenza": "saggezza",
            "storia": "intelligenza"
        }
        
        # Trova la caratteristica associata
        caratteristica = mappa_abilita_caratteristiche.get(abilita.lower(), "destrezza")
        
        # Ottieni il modificatore
        mod = getattr(self, f"modificatore_{caratteristica}", 0)
        
        # Aggiungi bonus di competenza se competente
        competente = self.abilita_competenze.get(abilita.lower(), False)
        bonus_comp = self.bonus_competenza if competente else 0
        
        # Tira il dado
        tiro = Dado(20).tira()
        risultato = tiro + mod + bonus_comp
        
        return {
            "tiro": tiro,
            "modificatore": mod,
            "bonus_competenza": bonus_comp,
            "competente": competente,
            "risultato": risultato,
            "critico": tiro == 20,
            "fallimento_critico": tiro == 1
        }
        
    def to_dict(self):
        """
        Converte il giocatore in un dizionario per la serializzazione.
        
        Returns:
            dict: Dizionario rappresentante lo stato del giocatore
        """
        # Ottieni il dizionario base dall'entità
        dati = super().to_dict()
        
        # Aggiungi attributi specifici del giocatore
        dati.update({
            "classe": self.classe,
            "razza": self.razza,
            "livello": self.livello,
            "hp": self.hp,
            "hp_max": self.hp_max,
            "esperienza": self.esperienza,
            "esperienza_prossimo_livello": self.esperienza_prossimo_livello,
            "abilita_speciali": self.abilita_speciali,
            "missioni": self.missioni,
            "missioni_completate": self.missioni_completate,
            "dialogo_corrente": self.dialogo_corrente,
            "nome_mappa_corrente": self.nome_mappa_corrente
        })
        
        return dati
    
    def to_msgpack(self):
        """
        Converte il giocatore in formato MessagePack.
        
        Returns:
            bytes: Dati serializzati in formato MessagePack
        """
        try:
            import msgpack
            return msgpack.packb(self.to_dict(), use_bin_type=True)
        except Exception as e:
            logger.error(f"Errore nella serializzazione MessagePack del giocatore {self.id}: {e}")
            # Fallback a dizionario serializzato in JSON e poi convertito in bytes
            return json.dumps(self.to_dict()).encode()
    
    @classmethod
    def from_dict(cls, dati):
        """
        Crea un'istanza del giocatore da un dizionario.
        
        Args:
            dati (dict): Dizionario con i dati del giocatore
            
        Returns:
            Giocatore: Istanza del giocatore
        """
        # Crea l'istanza base
        giocatore = cls(
            nome=dati.get("nome", "Avventuriero"),
            classe=dati.get("classe", "guerriero"),
            razza=dati.get("razza", "umano"),
            livello=dati.get("livello", 1),
            hp=dati.get("hp"),
            token=dati.get("token", "@"),
            id=dati.get("id")
        )
        
        # Aggiorna gli attributi specifici
        giocatore.hp = dati.get("hp", giocatore.hp)
        giocatore.hp_max = dati.get("hp_max", giocatore.hp_max)
        giocatore.esperienza = dati.get("esperienza", 0)
        giocatore.esperienza_prossimo_livello = dati.get("esperienza_prossimo_livello", giocatore._calcola_exp_livello(giocatore.livello + 1))
        giocatore.abilita_speciali = dati.get("abilita_speciali", giocatore.abilita_speciali)
        giocatore.missioni = dati.get("missioni", [])
        giocatore.missioni_completate = dati.get("missioni_completate", [])
        giocatore.dialogo_corrente = dati.get("dialogo_corrente")
        giocatore.nome_mappa_corrente = dati.get("nome_mappa_corrente", "taverna")
        
        # Imposta inventario e equipaggiamento
        giocatore.inventario = dati.get("inventario", [])
        giocatore.oro = dati.get("oro", 10)
        giocatore.arma = dati.get("arma")
        giocatore.armatura = dati.get("armatura")
        giocatore.accessori = dati.get("accessori", [])
        
        # Imposta caratteristiche
        giocatore.forza_base = dati.get("forza_base", giocatore.forza_base)
        giocatore.destrezza_base = dati.get("destrezza_base", giocatore.destrezza_base)
        giocatore.costituzione_base = dati.get("costituzione_base", giocatore.costituzione_base)
        giocatore.intelligenza_base = dati.get("intelligenza_base", giocatore.intelligenza_base)
        giocatore.saggezza_base = dati.get("saggezza_base", giocatore.saggezza_base)
        giocatore.carisma_base = dati.get("carisma_base", giocatore.carisma_base)
        
        # Ricalcola i modificatori
        giocatore.modificatore_forza = giocatore.calcola_modificatore(giocatore.forza_base)
        giocatore.modificatore_destrezza = giocatore.calcola_modificatore(giocatore.destrezza_base)
        giocatore.modificatore_costituzione = giocatore.calcola_modificatore(giocatore.costituzione_base)
        giocatore.modificatore_intelligenza = giocatore.calcola_modificatore(giocatore.intelligenza_base)
        giocatore.modificatore_saggezza = giocatore.calcola_modificatore(giocatore.saggezza_base)
        giocatore.modificatore_carisma = giocatore.calcola_modificatore(giocatore.carisma_base)
        
        # Imposta abilità
        giocatore.abilita_competenze = dati.get("abilita_competenze", {})
        
        return giocatore
    
    @classmethod
    def from_msgpack(cls, data_bytes):
        """
        Crea un'istanza del giocatore da dati in formato MessagePack.
        
        Args:
            data_bytes (bytes): Dati serializzati in formato MessagePack
            
        Returns:
            Giocatore: Istanza del giocatore
        """
        try:
            import msgpack
            dati = msgpack.unpackb(data_bytes, raw=False)
            return cls.from_dict(dati)
        except Exception as e:
            logger.error(f"Errore nella deserializzazione MessagePack del giocatore: {e}")
            try:
                # Tenta di interpretare i dati come JSON
                dati = json.loads(data_bytes.decode())
                return cls.from_dict(dati)
            except Exception as e2:
                logger.error(f"Errore anche con fallback JSON: {e2}")
                return cls("Giocatore Errore", "guerriero")  # Ritorna un giocatore base in caso di errore
    
    def __str__(self):
        return f"{self.nome} ({self.razza} {self.classe} liv. {self.livello}) HP: {self.hp}/{self.hp_max}"
