import json
import os
import uuid
from items.oggetto import Oggetto
from items.item_factory import ItemFactory
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
        
        # Normalizza la classe
        self.classe = self._normalizza_classe(classe)
        self.razza = razza
        self.livello = livello
        
        # Imposta statistiche base in base alla classe
        self._init_stats_by_class(self.classe)
        
        # Punti vita basati sulla costituzione
        classe_nome_per_hp = self._get_classe_nome()
        
        base_hp = 10 # Fallback generale
        try:
            from util.class_registry import get_player_class
            classe_def = get_player_class(classe_nome_per_hp)
            base_hp = classe_def.get("hp_base", 10)
        except Exception as e:
            logger.warning(f"Errore nel caricamento hp_base per la classe {classe_nome_per_hp}: {e}. Uso fallback {base_hp}.")
            # Fallback specifici se class_registry fallisce del tutto
            if classe_nome_per_hp == "guerriero": base_hp = 12
            elif classe_nome_per_hp == "mago": base_hp = 6
            elif classe_nome_per_hp == "ladro": base_hp = 8
            elif classe_nome_per_hp == "chierico": base_hp = 10
            
        self.hp_max = base_hp + self.modificatore_costituzione
        if self.hp_max < 1: self.hp_max = 1
        
        self.hp = min(hp, self.hp_max) if hp is not None else self.hp_max
        
        self.mana = 0
        self.mana_max = 0
        
        classe_nome_per_mana = self._get_classe_nome() # Usa nome normalizzato per MANA
        mana_base = 0 # Fallback
        mod_rilevante_mana = 0

        try:
            from util.class_registry import get_player_class
            classe_def_mana = get_player_class(classe_nome_per_mana)
            mana_base = classe_def_mana.get("mana_base", 0)
            if classe_nome_per_mana == "mago": mod_rilevante_mana = self.modificatore_intelligenza
            elif classe_nome_per_mana == "chierico": mod_rilevante_mana = self.modificatore_saggezza
            elif classe_nome_per_mana == "ladro": mod_rilevante_mana = self.modificatore_intelligenza # o carisma, a seconda del design
        except Exception as e:
            logger.warning(f"Errore caricamento mana_base per classe {classe_nome_per_mana}: {e}. Uso fallback.")
            if classe_nome_per_mana == "mago": mana_base = 20; mod_rilevante_mana = self.modificatore_intelligenza
            elif classe_nome_per_mana == "chierico": mana_base = 10; mod_rilevante_mana = self.modificatore_saggezza
            elif classe_nome_per_mana == "ladro": mana_base = 4; mod_rilevante_mana = self.modificatore_intelligenza
        
        if mana_base > 0 or classe_nome_per_mana in ["mago", "chierico", "ladro"]: # Classi che usano mana
            self.mana_max = mana_base + mod_rilevante_mana
            if self.mana_max < 0: self.mana_max = 0 # Mana non può essere negativo
            self.mana = self.mana_max
        
        self.inventario = []
        self.oro = 10
        self.arma = None
        self.armatura = None
        self.accessori = []
        self.esperienza = 0
        self.esperienza_prossimo_livello = self._calcola_exp_livello(livello + 1)
        self.abilita_speciali = self._init_abilita_speciali()
        self.missioni = []
        self.missioni_completate = []
        self.dialogo_corrente = None
        self.mappa_corrente = "taverna"
        
    def _normalizza_classe(self, classe_input):
        """
        Normalizza l'oggetto classe indipendentemente dal formato di input.
        
        Args:
            classe_input (str o dict): Classe del giocatore
            
        Returns:
            dict: Classe normalizzata come dizionario
        """
        if isinstance(classe_input, dict) and "id" in classe_input:
            return classe_input
        if isinstance(classe_input, str):
            try:
                from util.class_registry import get_player_class
                return get_player_class(classe_input.lower())
            except Exception as e:
                logger.warning(f"Errore caricamento classe {classe_input}: {e}. Creo definizione base.")
                return {"id": classe_input.lower(), "nome": classe_input.capitalize(), "descrizione": f"Classe {classe_input.capitalize()}"}
        if isinstance(classe_input, dict): # Dict senza id
            nome_classe = classe_input.get("nome", "guerriero")
            classe_mod = classe_input.copy()
            classe_mod["id"] = nome_classe.lower()
            return classe_mod
        try:
            return self._normalizza_classe(str(classe_input))
        except:
            logger.error(f"Impossibile normalizzare classe {classe_input}, uso 'guerriero' fallback.")
            try: from util.class_registry import get_player_class; return get_player_class("guerriero")
            except: return {"id": "guerriero", "nome": "Guerriero"}
        
    def _get_classe_nome(self):
        """
        Ottiene il nome della classe indipendentemente dal formato.
        
        Returns:
            str: Nome della classe in minuscolo
        """
        if isinstance(self.classe, str): return self.classe.lower()
        if isinstance(self.classe, dict): return self.classe.get("id", self.classe.get("nome", "guerriero")).lower()
        elif hasattr(self.classe, "id"):
            return self.classe.id.lower()
        elif hasattr(self.classe, "nome"):
            return self.classe.nome.lower()
        else:
            try: return str(self.classe).lower()
            except: return "guerriero"
        
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
        vecchia_classe_nome = self._get_classe_nome()
        
        # Normalizza e aggiorna l'attributo classe
        self.classe = self._normalizza_classe(classe)
        
        # Reinizializza le statistiche in base alla nuova classe
        self._init_stats_by_class(self.classe)
        
        # Aggiorna le abilità speciali
        self.abilita_speciali = self._init_abilita_speciali()
        
        # Aggiorna i punti mana se necessario
        if self._get_classe_nome() == "mago":
            self.mana_max = 20 + self.modificatore_intelligenza
            self.mana = min(self.mana, self.mana_max)  # Limita il mana attuale al massimo
        elif self._get_classe_nome() == "chierico":
            self.mana_max = 10 + self.modificatore_saggezza
            self.mana = min(self.mana, self.mana_max)
        
        # Log del cambio classe
        logger.info(f"Classe del giocatore {self.nome} cambiata da {vecchia_classe_nome} a {self._get_classe_nome()}")
        
        return True
        
    def _init_stats_by_class(self, classe_obj):
        """
        Inizializza le statistiche base in base alla classe.
        
        Args:
            classe_obj (str o dict): Classe del giocatore
        """
        # Esempio di come potrebbe iniziare:
        classe_nome_id = "guerriero" # Default
        if isinstance(classe_obj, dict):
            classe_nome_id = classe_obj.get('id', 'guerriero')
        elif isinstance(classe_obj, str):
            classe_nome_id = classe_obj.lower()
        
        # Imposta valori predefiniti
        self.forza_base = 10
        self.destrezza_base = 10
        self.costituzione_base = 10
        self.intelligenza_base = 10
        self.saggezza_base = 10
        self.carisma_base = 10
        self.abilita_competenze = {} # Resetta competenze

        try:
            from util.class_registry import get_player_class
            classe_def = get_player_class(classe_nome_id)
            stats = classe_def.get("statistiche_base", {})
            self.forza_base = stats.get("forza", self.forza_base)
            self.destrezza_base = stats.get("destrezza", self.destrezza_base)
            self.costituzione_base = stats.get("costituzione", self.costituzione_base)
            self.intelligenza_base = stats.get("intelligenza", self.intelligenza_base)
            self.saggezza_base = stats.get("saggezza", self.saggezza_base)
            self.carisma_base = stats.get("carisma", self.carisma_base)
            self.abilita_competenze = classe_def.get("competenze_abilita", {}) # Carica competenze
            logger.info(f"Statistiche e competenze caricate per classe {classe_nome_id} da class_registry.")
        except Exception as e:
            logger.error(f"Errore caricamento statistiche per {classe_nome_id} da class_registry: {e}. Uso fallback.")
            # Logica di fallback per stats e competenze se class_registry fallisce
            if classe_nome_id == "guerriero": self.forza_base = 15; self.costituzione_base = 14; self.abilita_competenze = {"atletica": True, "intimidire": True}
            elif classe_nome_id == "mago": self.intelligenza_base = 16; self.saggezza_base = 12; self.abilita_competenze = {"arcano": True, "storia": True}
            # ... ecc.
        
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
        
        # Ottieni il nome della classe
        classe_nome = self._get_classe_nome()
        
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
            
        elif classe_nome == "chierico":
            abilita["cura_ferite"] = {
                "nome": "Cura Ferite",
                "descrizione": "Cura 1d8 + modificatore saggezza punti ferita.",
                "utilizzi": 3,
                "utilizzi_max": 3,
                "ripristino": "riposo_lungo"
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
            vecchia_exp_necessaria = self.esperienza_prossimo_livello
            if self.aumenta_livello(): # aumenta_livello gestisce la sottrazione dell'exp usata
                 logger.info(f"{self.nome} è salito di livello! Exp attuale: {self.esperienza}, Exp per prossimo: {self.esperienza_prossimo_livello}")
                 # Entita._sali_livello è già chiamato da Entita.guadagna_esperienza, non chiamare due volte
                 return True 
        return False
        
    def aumenta_livello(self):
        """
        Aumenta di livello il giocatore.
        
        Returns:
            bool: True se l'aumento è avvenuto con successo
        """
        self.livello += 1
        logger.info(f"*** {self.nome} è salito al livello {self.livello}! ***")
        
        classe_nome = self._get_classe_nome()
        dadi_vita = 8 # Fallback
        mana_per_livello = 0
        mod_rilevante_mana_lvlup = 0

        try:
            from util.class_registry import get_player_class
            classe_def = get_player_class(classe_nome)
            progressione = classe_def.get("progressione", {})
            dadi_vita = progressione.get("hp_per_livello", dadi_vita)
            mana_per_livello = progressione.get("mana_per_livello", 0)
            if classe_nome == "mago": mod_rilevante_mana_lvlup = self.modificatore_intelligenza
            elif classe_nome == "chierico": mod_rilevante_mana_lvlup = self.modificatore_saggezza
            # Altre classi se usano mana
        except Exception as e:
            logger.warning(f"Errore caricamento progressione per {classe_nome}: {e}. Uso fallback per dadi vita.")
            dadi_vita = {"guerriero": 10, "mago": 4, "ladro": 6, "chierico": 8}.get(classe_nome, 8)

        guadagno_hp = max(1, Dado(dadi_vita).tira() + self.modificatore_costituzione)
        self.hp_max += guadagno_hp
        self.hp = self.hp_max # Cura completa al level up

        if mana_per_livello > 0 or classe_nome in ["mago", "chierico", "ladro"]:
            guadagno_mana = mana_per_livello + mod_rilevante_mana_lvlup
            self.mana_max += max(0, guadagno_mana) # Assicura che non sia negativo
            self.mana = self.mana_max
            logger.info(f"Mana aumentato a {self.mana_max}")

        self.bonus_competenza = 2 + ((self.livello - 1) // 4)
        self.esperienza_prossimo_livello = self._calcola_exp_livello(self.livello + 1)
        
        # Logica di Entita._sali_livello per aumento statistiche e difesa
        super()._sali_livello(self.gioco) # Chiama il metodo della classe base Entita per l'aumento di stats e difesa

        logger.info(f"Nuovi HP: {self.hp}/{self.hp_max}. Prossimo livello a {self.esperienza_prossimo_livello} XP.")
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
        mana_recuperato = 0 # Aggiunto recupero mana
        
        if tipo_riposo == "breve":
            recupero_dado = Dado(self.livello if self.livello <= 8 else 8).tira() # Es: 1d{livello} fino a 1d8
            recupero = recupero_dado + self.modificatore_costituzione
            hp_recuperati = min(max(0, recupero), self.hp_max - self.hp)
            self.hp += hp_recuperati
            
            # Ripristina abilità per riposo breve
            for _, abilita in self.abilita_speciali.items():
                if abilita.get("ripristino") == "riposo_breve":
                    abilita["utilizzi"] = abilita.get("utilizzi_max", 1)
            logger.info(f"{self.nome} fa un riposo breve. Recuperati {hp_recuperati} HP.")

        elif tipo_riposo == "lungo":
            hp_recuperati = self.hp_max - self.hp
            self.hp = self.hp_max
            mana_recuperato = self.mana_max - self.mana
            self.mana = self.mana_max
            
            # Ripristina tutte le abilità (breve e lungo)
            for _, abilita in self.abilita_speciali.items():
                if abilita.get("ripristino") in ["riposo_breve", "riposo_lungo"]:
                    abilita["utilizzi"] = abilita.get("utilizzi_max", 1)
            logger.info(f"{self.nome} fa un riposo lungo. Recuperati {hp_recuperati} HP e {mana_recuperato} Mana. Abilità ripristinate.")
        
        self.verifica_valori_vitali()
        return {"hp_recuperati": hp_recuperati, "mana_recuperato": mana_recuperato}
        
    def subisci_danno(self, danno, gioco=None):
        """
        Fa subire danno al giocatore.
        
        Args:
            danno (int): Quantità di danno da infliggere
            
        Returns:
            int: Danno effettivamente inflitto
        """
        danno_effettivo = max(1, danno - self.difesa) # Assumendo che self.difesa sia calcolata
        self.hp = max(0, self.hp - danno_effettivo)
        
        game_ctx = gioco if gioco else getattr(self, 'gioco', None)
        if game_ctx and hasattr(game_ctx, 'io'):
            game_ctx.io.mostra_messaggio(f"{self.nome} subisce {danno_effettivo} danni! HP rimasti: {self.hp}/{self.hp_max}")

        if self.hp <= 0:
            self.stato = "inconscio" # Stato specifico del giocatore
            logger.info(f"{self.nome} è {self.stato}.")
            if game_ctx and hasattr(game_ctx, 'io'):
                 game_ctx.io.mostra_messaggio(f"{self.nome} è {self.stato}!")
            # Qui potrebbe esserci logica per game over o gestione della "morte"
            # self.event_bus.emit(Events.PLAYER_DEFEATED, player_id=self.id)
        return self.hp > 0 # Restituisce True se ancora vivo (o cosciente)
        
    def get_danno_arma(self):
        """
        Calcola il danno dell'arma corrente.
        
        Returns:
            int: Danno base dell'arma
        """
        if not self.arma: return 1 
        if hasattr(self.arma, 'danno_base'): return self.arma.danno_base # Se l'arma è un oggetto con danno_base
        if isinstance(self.arma, dict) and 'danno_base' in self.arma: return self.arma['danno_base']
        # ... fallback se arma è una stringa ...
        return 1
        
    def get_classe_armatura(self):
        """
        Calcola la classe armatura (CA) del giocatore.
        
        Returns:
            int: Classe armatura
        """
        ca_base = 10 + self.modificatore_destrezza
        if self.armatura:
            if hasattr(self.armatura, 'valore_ca'): return self.armatura.valore_ca # Se armatura è oggetto
            if isinstance(self.armatura, dict) and 'valore_ca' in self.armatura: return self.armatura['valore_ca']
            # ... fallback se armatura è una stringa ...
        return ca_base
        
    def usa_abilita_speciale(self, nome_abilita, target=None):
        """
        Usa un'abilità speciale.
        
        Args:
            nome_abilita (str): Nome dell'abilità da usare
            
        Returns:
            dict: Risultato dell'abilità o None se non disponibile
        """
        if nome_abilita not in self.abilita_speciali:
            logger.warning(f"Abilità speciale '{nome_abilita}' non trovata per {self.nome}")
            return None
            
        abilita = self.abilita_speciali[nome_abilita]
        
        if abilita.get("utilizzi", 0) <= 0 and abilita.get("utilizzi_max", 1) != float('inf'): # Controllo utilizzi
            messaggio = f"{abilita.get('nome', nome_abilita)} non ha utilizzi rimanenti."
            if self.gioco and hasattr(self.gioco, 'io'): self.gioco.io.mostra_messaggio(messaggio)
            return {"successo": False, "messaggio": messaggio}
            
        if abilita.get("utilizzi_max", 1) != float('inf'):
            abilita["utilizzi"] = abilita.get("utilizzi", 1) -1
        
        risultato_esecuzione = {"successo": True, "messaggio": f"Hai usato {abilita.get('nome', nome_abilita)}.", "azione_eseguita": nome_abilita}
        # Logica specifica abilità (semplificata, da espandere)
        if nome_abilita == "secondo_fiato":
            recupero = Dado(10).tira() + self.livello
            hp_recuperati_effettivi = min(recupero, self.hp_max - self.hp)
            self.hp += hp_recuperati_effettivi
            self.verifica_valori_vitali()
            risultato_esecuzione["messaggio"] = f"Recuperi {hp_recuperati_effettivi} punti ferita."
            risultato_esecuzione["hp_recuperati"] = hp_recuperati_effettivi
        # ... altre abilità ...
        
        if self.gioco and hasattr(self.gioco, 'io'): self.gioco.io.mostra_messaggio(risultato_esecuzione["messaggio"])
        # self.event_bus.emit(Events.ABILITY_USED, player_id=self.id, ability_name=nome_abilita, result=risultato_esecuzione)
        return risultato_esecuzione
        
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
        
    def to_dict(self, already_serialized=None):
        """
        Converte il giocatore in un dizionario per la serializzazione.
        
        Args:
            already_serialized (set, optional): Set di ID di oggetti già serializzati
            
        Returns:
            dict: Dizionario rappresentante lo stato del giocatore
        """
        # Ottieni il dizionario base da Entita.to_dict()
        # Questo include già: id, nome, token, stato, interagibile, visibile, tags,
        # tipo (impostato a self.__class__.__name__), stats_base, x, y, mappa_corrente,
        # abilita_competenze, bonus_competenza, difesa, inventario, oro,
        # arma, armatura, accessori (serializzati correttamente se sono oggetti con to_dict).
        data = super().to_dict(already_serialized)

        if data.get("ref"): # Gestione riferimenti circolari da Entita.to_dict()
            return data

        # Assicura che il tipo sia "Giocatore" se Entita.to_dict() non l'ha fatto correttamente
        # (dovrebbe farlo con self.__class__.__name__)
        data['tipo'] = self.__class__.__name__ 

        # Serializza l'oggetto 'classe' in un dizionario se non lo è già
        classe_serializzata = self.classe # self.classe è già un dict grazie a _normalizza_classe
        if not isinstance(self.classe, dict): # Controllo di sicurezza aggiuntivo
             logger.warning(f"Attributo self.classe del giocatore {self.nome} non è un dict come atteso: {type(self.classe)}. Tentativo di normalizzazione.")
             classe_serializzata = self._normalizza_classe(self.classe)


        # Aggiungi/Aggiorna attributi specifici del Giocatore
        data.update({
            "classe": classe_serializzata, # Dovrebbe essere un dict serializzabile
            "razza": self.razza,
            "livello": self.livello, # 'livello' è anche in Entita, qui lo sovrascrive se diverso
            "hp": self.hp,
            "hp_max": self.hp_max,
            "mana": self.mana,
            "mana_max": self.mana_max,
            "esperienza": self.esperienza, # 'esperienza' è anche in Entita
            "esperienza_prossimo_livello": self.esperienza_prossimo_livello,
            "abilita_speciali": self.abilita_speciali, 
            "missioni": self.missioni, 
            "missioni_completate": self.missioni_completate,
            "dialogo_corrente": self.dialogo_corrente 
            # Gli attributi come inventario, oro, equipaggiamento, posizione, stats base
            # sono già gestiti da Entita.to_dict()
        })
        return data

    @classmethod
    def from_dict(cls, data):
        """
        Crea un'istanza del giocatore da un dizionario.
        
        Args:
            data (dict): Dizionario con i dati del giocatore
            
        Returns:
            Giocatore: Istanza del giocatore
        """
        # Estrai parametri per il costruttore di Giocatore
        nome_giocatore = data.get("nome", "Avventuriero Casuale")
        
        classe_data_salvata = data.get("classe", "guerriero") # Può essere un dict o una stringa
        classe_per_init = classe_data_salvata
        if isinstance(classe_data_salvata, dict): # Se è un dict, passa l'id/nome all'init
            classe_per_init = classe_data_salvata.get('id', classe_data_salvata.get('nome', 'guerriero'))

        # Crea istanza base di Giocatore usando il suo __init__
        # L'__init__ di Giocatore chiamerà _normalizza_classe e _init_stats_by_class
        giocatore = cls(
            nome=nome_giocatore,
            classe=classe_per_init, # Passa l'ID o il nome stringa della classe
            razza=data.get("razza", "umano"),
            livello=data.get("livello", 1),
            hp=data.get("hp"), # L'init di Giocatore gestirà hp e hp_max
            token=data.get("token", "@"),
            id=data.get("id") # L'init di Entita gestirà la creazione di un UUID se id è None
        )

        # Popola/Sovrascrive gli attributi di Entita (la maggior parte già gestita da Entita.__init__)
        # ma sovrascriviamo con i valori salvati se presenti.
        # Entita.from_dict(data) NON va chiamato qui perché creerebbe un'altra istanza di Entita.
        # Invece, impostiamo gli attributi direttamente sull'istanza 'giocatore'.

        giocatore.stato = data.get("stato", giocatore.stato)
        giocatore.interagibile = data.get("interagibile", giocatore.interagibile)
        giocatore.visibile = data.get("visibile", giocatore.visibile)
        giocatore.tags = set(data.get("tags", list(giocatore.tags)))
        
        # Sovrascrive le stats base se presenti nel salvataggio, poi ricalcola i modificatori
        # L'__init__ di Giocatore ha già chiamato _init_stats_by_class, ma i dati salvati potrebbero essere diversi.
        giocatore.forza_base = data.get("forza_base", giocatore.forza_base)
        giocatore.destrezza_base = data.get("destrezza_base", giocatore.destrezza_base)
        giocatore.costituzione_base = data.get("costituzione_base", giocatore.costituzione_base)
        giocatore.intelligenza_base = data.get("intelligenza_base", giocatore.intelligenza_base)
        giocatore.saggezza_base = data.get("saggezza_base", giocatore.saggezza_base)
        giocatore.carisma_base = data.get("carisma_base", giocatore.carisma_base)
        
        giocatore.modificatore_forza = giocatore.calcola_modificatore(giocatore.forza_base)
        giocatore.modificatore_destrezza = giocatore.calcola_modificatore(giocatore.destrezza_base)
        giocatore.modificatore_costituzione = giocatore.calcola_modificatore(giocatore.costituzione_base)
        giocatore.modificatore_intelligenza = giocatore.calcola_modificatore(giocatore.intelligenza_base)
        giocatore.modificatore_saggezza = giocatore.calcola_modificatore(giocatore.saggezza_base)
        giocatore.modificatore_carisma = giocatore.calcola_modificatore(giocatore.carisma_base)

        giocatore.x = data.get("x", giocatore.x)
        giocatore.y = data.get("y", giocatore.y)
        giocatore.mappa_corrente = data.get("mappa_corrente", giocatore.mappa_corrente)
        
        giocatore.abilita_competenze = data.get("abilita_competenze", giocatore.abilita_competenze)
        giocatore.bonus_competenza = data.get("bonus_competenza", giocatore.bonus_competenza)
        giocatore.difesa = data.get("difesa", giocatore.difesa)
        giocatore.oro = data.get("oro", giocatore.oro)
        
        # Deserializzazione Inventario e Equipaggiamento usando ItemFactory
        # Questo sovrascrive l'inventario vuoto inizializzato da Entita.__init__
        raw_inventario = data.get("inventario", [])
        giocatore.inventario = []
        if raw_inventario:
            for item_data_dict in raw_inventario:
                if isinstance(item_data_dict, dict):
                    item_instance = ItemFactory.crea_da_dict(item_data_dict)
                    if item_instance:
                        giocatore.inventario.append(item_instance)
        
        arma_data_dict = data.get("arma")
        giocatore.arma = ItemFactory.crea_da_dict(arma_data_dict) if isinstance(arma_data_dict, dict) else None

        armatura_data_dict = data.get("armatura")
        giocatore.armatura = ItemFactory.crea_da_dict(armatura_data_dict) if isinstance(armatura_data_dict, dict) else None

        raw_accessori = data.get("accessori", [])
        giocatore.accessori = []
        if raw_accessori:
            for acc_data_dict in raw_accessori:
                if isinstance(acc_data_dict, dict):
                    item_instance = ItemFactory.crea_da_dict(acc_data_dict)
                    if item_instance:
                        giocatore.accessori.append(item_instance)

        # Popola/Sovrascrive attributi specifici di Giocatore
        # (alcuni potrebbero essere già stati impostati dall'__init__ di Giocatore,
        # ma i valori salvati hanno la precedenza).
        giocatore.hp = data.get("hp", giocatore.hp) # Sovrascrive hp calcolato da __init__
        giocatore.hp_max = data.get("hp_max", giocatore.hp_max) # Sovrascrive hp_max calcolato
        
        giocatore.mana = data.get("mana", giocatore.mana)
        giocatore.mana_max = data.get("mana_max", giocatore.mana_max)

        giocatore.esperienza = data.get("esperienza", giocatore.esperienza)
        giocatore.esperienza_prossimo_livello = data.get("esperienza_prossimo_livello", giocatore.esperienza_prossimo_livello)
        giocatore.abilita_speciali = data.get("abilita_speciali", giocatore.abilita_speciali)
        giocatore.missioni = data.get("missioni", giocatore.missioni)
        giocatore.missioni_completate = data.get("missioni_completate", giocatore.missioni_completate)
        giocatore.dialogo_corrente = data.get("dialogo_corrente", giocatore.dialogo_corrente)

        # Ripristina l'oggetto classe completo se era un dict
        if isinstance(classe_data_salvata, dict):
            giocatore.classe = classe_data_salvata
        
        # Chiamata finale per assicurare coerenza dei valori vitali
        giocatore.verifica_valori_vitali()
        
        return giocatore
    
    def verifica_valori_vitali(self):
        """
        Verifica e corregge i valori di HP e mana per assicurarsi che siano validi.
        """
        # Assicurati che hp_max sia almeno 1
        if not hasattr(self, 'hp_max') or self.hp_max < 1:
             classe_nome_vv = self._get_classe_nome()
             base_hp_vv = 10
             try:
                 from util.class_registry import get_player_class
                 classe_def_vv = get_player_class(classe_nome_vv)
                 base_hp_vv = classe_def_vv.get("hp_base", 10)
             except: pass # Ignora se fallisce, usa fallback
             self.hp_max = base_hp_vv + self.modificatore_costituzione
             if self.hp_max < 1: self.hp_max = 1
        
        if not hasattr(self, 'hp') or self.hp is None: self.hp = self.hp_max
        self.hp = min(max(0, self.hp), self.hp_max)

        # Verifica mana per classi che lo usano
        classe_nome_vv_mana = self._get_classe_nome()
        if classe_nome_vv_mana in ["mago", "chierico", "ladro"]: # Aggiungi altre classi che usano mana
            if not hasattr(self, 'mana_max') or self.mana_max < 0: # Mana max non può essere negativo
                mana_base_vv = 0
                mod_rilevante_mana_vv = 0
                try:
                    from util.class_registry import get_player_class
                    classe_def_vv_mana = get_player_class(classe_nome_vv_mana)
                    mana_base_vv = classe_def_vv_mana.get("mana_base", 0)
                    if classe_nome_vv_mana == "mago": mod_rilevante_mana_vv = self.modificatore_intelligenza
                    elif classe_nome_vv_mana == "chierico": mod_rilevante_mana_vv = self.modificatore_saggezza
                    elif classe_nome_vv_mana == "ladro": mod_rilevante_mana_vv = self.modificatore_intelligenza
                except: pass
                self.mana_max = mana_base_vv + mod_rilevante_mana_vv
                if self.mana_max < 0: self.mana_max = 0
            
            if not hasattr(self, 'mana') or self.mana is None: self.mana = self.mana_max
            self.mana = min(max(0, self.mana), self.mana_max)
        else: # Per classi senza mana, assicurati che siano a 0
            self.mana = 0
            self.mana_max = 0
        
    def __str__(self):
        return f"{self.nome} ({self.razza} {self.classe.get('nome', self.classe) if isinstance(self.classe, dict) else self.classe} liv. {self.livello}) HP: {self.hp}/{self.hp_max}"
