"""
Gestore delle mappe di gioco.
Implementato come "facade" che utilizza i manager specializzati.
"""

import logging
import time
import json
from pathlib import Path
from util.config import SAVE_FORMAT_VERSION
from world.managers.mappa_manager import MappaManager
from world.managers.oggetti_manager import OggettiManager
from world.managers.npg_manager import NPGManager
from world.managers.loader_manager import LoaderManager
from typing import Optional, TYPE_CHECKING

# Forward reference per World per evitare importazioni circolari
if TYPE_CHECKING:
    from core.ecs.world import World

class GestitoreMappe:
    """
    Classe che gestisce le mappe di gioco, orchestrando i manager specializzati.
    Agisce come un facade che coordina mappe, oggetti e NPC.
    """
    def __init__(self, percorso_mappe=None, percorso_npc=None, percorso_oggetti=None, limite_cache=5):
        """
        Inizializza il gestore delle mappe.
        
        Args:
            percorso_mappe: Percorso alla directory contenente le mappe JSON
            percorso_npc: Percorso alla directory contenente le configurazioni degli NPC
            percorso_oggetti: Percorso alla directory contenente le configurazioni degli oggetti
            limite_cache: Numero massimo di mappe da mantenere in cache
        """
        self.mappa_manager = MappaManager(limite_cache=limite_cache)
        self.oggetti_manager = OggettiManager(percorso_oggetti)
        self.npg_manager = NPGManager(percorso_npc)
        self.loader_manager = LoaderManager(percorso_mappe)
        self.cache_mappe = {}  # Inizializzazione della cache delle mappe
        self.world_context: Optional["World"] = None # Usare la stringa "World" per il forward reference effettivo
        
        logging.info("GestitoreMappe inizializzato con successo")
        
    @property
    def mappa_corrente(self):
        """Restituisce la mappa corrente."""
        return self.mappa_manager.mappa_corrente
        
    @property
    def mappe(self):
        """Restituisce il dizionario delle mappe."""
        return self.mappa_manager.mappe
        
    def inizializza_mappe(self, world_context: Optional["World"] = None):
        """Crea e configura tutte le mappe del gioco esclusivamente da JSON"""
        if world_context:
            self.world_context = world_context

        # Carica le mappe da file JSON
        mappe_json = self.carica_mappe_da_json()
        
        if not mappe_json:
            logging.error("Nessuna mappa JSON trovata. Il gioco non può continuare senza mappe.")
            raise ValueError("Nessuna mappa JSON trovata. Controlla che i file JSON delle mappe esistano nelle directory supportate.")
            
        # Usa le mappe caricate da JSON
        for nome, mappa in mappe_json.items():
            self.mappa_manager.aggiungi_mappa(mappa)
            # Carica gli oggetti interattivi e NPG per questa mappa
            self.oggetti_manager.carica_oggetti_su_mappa(mappa, nome, self.world_context)
            self.npg_manager.carica_npg_su_mappa(mappa, nome, self.world_context)
        
        logging.info(f"Caricate {len(mappe_json)} mappe da file JSON")
        
        # Imposta la mappa "taverna" come mappa attuale di default
        if "taverna" in self.mappe:
            self.imposta_mappa_attuale("taverna")
        elif self.mappe:
            # Altrimenti, usa la prima mappa disponibile
            primo_nome = next(iter(self.mappe.keys()))
            self.imposta_mappa_attuale(primo_nome)
            logging.info(f"Mappa taverna non trovata, impostata mappa {primo_nome} come default")
        else:
            logging.error("Nessuna mappa caricata")
        
    def carica_mappe_da_json(self):
        """
        Carica le mappe dai file JSON nelle directory supportate.
        
        Returns:
            dict: Dizionario di mappe caricate (nome -> oggetto Mappa) o {} se fallisce
        """
        mappe = {}
        
        try:
            # Ottieni l'elenco di tutti i file .json nella directory mappe
            file_mappe = self.loader_manager.elenca_mappe_disponibili()
            
            if not file_mappe:
                logging.error("Nessun file mappa JSON trovato nelle directory di ricerca")
                return {}
                
            # Carica ogni mappa
            for nome_file in file_mappe:
                try:
                    mappa = self.loader_manager.carica_mappa(nome_file)
                    # Verifica che la mappa sia valida
                    if self.mappa_manager._verifica_mappa_valida(mappa):
                        mappe[mappa.nome] = mappa
                        logging.info(f"Mappa caricata: {mappa.nome}")
                    else:
                        logging.error(f"Mappa {nome_file} non valida, ignorata")
                except Exception as e:
                    logging.error(f"Errore nel caricamento della mappa {nome_file}: {e}")
                    import traceback
                    logging.error(traceback.format_exc())
            
            return mappe
        except Exception as e:
            logging.error(f"Errore generale nel caricamento delle mappe: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return {}
    
    def salva_mappe_su_json(self):
        """
        Salva tutte le mappe correnti in file JSON.
        
        Returns:
            bool: True se il salvataggio è riuscito per tutte le mappe
        """
        successo = True
        
        for nome, mappa in self.mappe.items():
            try:
                # Salva la mappa in formato JSON
                if not self.loader_manager.salva_mappa(mappa):
                    successo = False
                    logging.error(f"Errore nel salvataggio della mappa {nome}")
            except Exception as e:
                successo = False
                logging.error(f"Errore durante il salvataggio della mappa {nome}: {e}")
                
        return successo

    def ottieni_mappa(self, nome_mappa):
        """
        Ottiene una mappa specifica per nome.
        
        Args:
            nome_mappa (str): Nome della mappa da ottenere
            
        Returns:
            Mappa: L'oggetto mappa richiesto o None se non trovata
        """
        # Verifica che il nome della mappa sia una stringa e non sia vuoto
        if not isinstance(nome_mappa, str) or not nome_mappa:
            logging.error(f"Nome mappa non valido: {nome_mappa}")
            return None
        
        # Assicurati che l'attributo cache_mappe esista
        if not hasattr(self, 'cache_mappe'):
            logging.warning("Attributo cache_mappe non trovato, inizializzazione")
            self.cache_mappe = {}
        
        # Verifica se è già in cache
        try:
            if nome_mappa in self.cache_mappe:
                logging.info(f"Mappa {nome_mappa} trovata in cache")
                return self.cache_mappe[nome_mappa]
        except Exception as e:
            logging.error(f"Errore nell'accesso alla cache: {e}")
            # Reset della cache in caso di problemi
            self.cache_mappe = {}
        
        try:    
            # Altrimenti, carica la mappa dai file
            mappa = self.mappa_manager.ottieni_mappa(nome_mappa)
            
            # Se non trovata, prova con fallback ai nomi comuni
            if mappa is None:
                logging.warning(f"Mappa {nome_mappa} non trovata, tentativo con fallback")
                # Mappa di nomi alternativi per gestire errori di case o varianti del nome
                alternative_names = {
                    "taverna": ["locanda", "inn"],
                    "villaggio": ["paese", "town", "village"],
                    "dungeon": ["prigione", "grotta", "cave"],
                    "mercato": ["market", "bazar", "negozio"],
                    "cantina": ["cellar", "cantinetta"]
                }
                
                # Cerca tra i nomi alternativi
                for base_name, alternatives in alternative_names.items():
                    if nome_mappa.lower() in alternatives or base_name.lower() == nome_mappa.lower():
                        logging.info(f"Tentativo di utilizzare la mappa {base_name} come fallback per {nome_mappa}")
                        mappa = self.mappa_manager.ottieni_mappa(base_name)
                        if mappa:
                            # Se trovato, aggiungi alla cache con il nome originale
                            try:
                                self.cache_mappe[nome_mappa] = mappa
                            except Exception as e:
                                logging.warning(f"Impossibile aggiungere alla cache: {e}")
                            return mappa
                
                # Se ancora non trovata, prova a cercare per somiglianza
                for mappa_name in self.mappa_manager.mappe.keys():
                    if mappa_name.startswith(nome_mappa[:3]) or nome_mappa.startswith(mappa_name[:3]):
                        logging.info(f"Trovata mappa con nome simile: {mappa_name} per {nome_mappa}")
                        mappa = self.mappa_manager.ottieni_mappa(mappa_name)
                        if mappa:
                            # Se trovato, aggiungi alla cache con il nome originale
                            try:
                                self.cache_mappe[nome_mappa] = mappa
                            except Exception as e:
                                logging.warning(f"Impossibile aggiungere alla cache: {e}")
                            return mappa
                
                logging.error(f"Nessuna mappa trovata per {nome_mappa} anche dopo tentativi con nomi alternativi")
                return None
            
            # Aggiungi alla cache
            try:
                self.cache_mappe[nome_mappa] = mappa
            except Exception as e:
                logging.warning(f"Impossibile aggiungere alla cache: {e}")
            
            return mappa
        except Exception as e:
            logging.error(f"Errore nel caricamento della mappa {nome_mappa}: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return None
    
    def imposta_mappa_attuale(self, nome):
        """
        Imposta la mappa attuale per riferimento facile.
        Utilizza il sistema di cache implementato in MappaManager.
        
        Args:
            nome (str): Nome della mappa da impostare come attuale
            
        Returns:
            bool: True se l'operazione è riuscita, False altrimenti
        """
        return self.mappa_manager.imposta_mappa_attuale(nome)
        
    def trasferisci_oggetti_da_stato(self, nome_mappa, stato):
        """
        Trasferisce oggetti e NPG dallo stato alla mappa corrispondente
        
        Args:
            nome_mappa (str): Nome della mappa
            stato: Stato del gioco contenente oggetti e NPG
            
        Returns:
            bool: True se l'operazione è riuscita, False altrimenti
        """
        mappa = self.mappa_manager.ottieni_mappa(nome_mappa)
        if not mappa:
            return False
            
        # Trasferisci gli oggetti
        for chiave, oggetto in stato.oggetti_interattivi.items():
            configurazione = self.oggetti_manager.ottieni_configurazione_oggetto(chiave)
            if configurazione and "posizione" in configurazione:
                x, y = configurazione["posizione"]
                self.oggetti_manager.posiziona_oggetto_su_mappa(mappa, oggetto, x, y)
                
        # Trasferisci gli NPG
        for nome, npg in stato.npg_presenti.items():
            configurazione = self.npg_manager.ottieni_configurazione_npc(nome)
            if configurazione and "posizione" in configurazione:
                x, y = configurazione["posizione"]
                self.npg_manager.posiziona_npc_su_mappa(mappa, npg, x, y)
            
        return True

    def muovi_giocatore(self, giocatore, dx, dy):
        """
        Gestisce lo spostamento del giocatore sulla mappa.
        
        Args:
            giocatore (Giocatore): Il giocatore da muovere
            dx, dy (int): Delta di spostamento
            
        Returns:
            dict: Risultato del movimento con chiavi 'successo', 'messaggio', 'cambio_mappa'
        """
        return self.mappa_manager.muovi_giocatore(giocatore, dx, dy)
    
    def cambia_mappa_giocatore(self, giocatore, nome_mappa, x=None, y=None):
        """
        Cambia la mappa corrente del giocatore.
        
        Args:
            giocatore (Giocatore): Il giocatore da spostare
            nome_mappa (str): Nome della nuova mappa
            x, y (int, optional): Posizione in cui posizionare il giocatore nella nuova mappa
            
        Returns:
            dict: Risultato dell'operazione con chiavi 'successo' e 'messaggio'
        """
        return self.mappa_manager.cambia_mappa_giocatore(giocatore, nome_mappa, x, y)
    
    def ottieni_info_posizione(self, x, y, mappa=None):
        """
        Ottiene informazioni su cosa si trova in una posizione specifica.
        
        Args:
            x, y (int): Coordinate da controllare
            mappa (Mappa, optional): Mappa in cui cercare. Se None, usa la mappa attuale.
            
        Returns:
            dict: Informazioni sulla posizione con chiavi 'tipo', 'oggetto' e 'messaggio'
        """
        return self.mappa_manager.ottieni_info_posizione(x, y, mappa)
    
    def to_dict(self):
        """
        Converte il gestore mappe in un dizionario per la serializzazione.
        
        Returns:
            dict: Rappresentazione del gestore mappe in formato dizionario
        """
        return self.mappa_manager.to_dict()
    
    def from_dict(self, data, world_context: Optional["World"] = None):
        """
        Carica lo stato del gestore mappe da un dizionario.
        
        Args:
            data (dict): Dizionario contenente lo stato del gestore mappe
            
        Returns:
            bool: True se il caricamento è avvenuto con successo, False altrimenti
        """
        result = self.mappa_manager.from_dict(data)
        
        # Ricarica gli oggetti e gli NPC per ogni mappa
        if result:
            if world_context: # Se fornito, aggiorna il contesto del gestore
                self.world_context = world_context
            elif not self.world_context: # Se non fornito e non già presente, logga un avviso
                logger.warning("GestoreMappe.from_dict chiamato senza world_context e nessun contesto preesistente. Le entità potrebbero non essere aggiunte al mondo ECS.")

            for nome_mappa, mappa in self.mappe.items():
                self.oggetti_manager.carica_oggetti_su_mappa(mappa, nome_mappa, self.world_context)
                self.npg_manager.carica_npg_su_mappa(mappa, nome_mappa, self.world_context)
                
        return result
    
    def salva(self, percorso_file="mappe_salvataggio.json"):
        """
        Salva lo stato completo di tutte le mappe e relativi oggetti interattivi.
        
        Args:
            percorso_file (str): Percorso del file in cui salvare i dati
            
        Returns:
            bool: True se il salvataggio è avvenuto con successo, False altrimenti
        """
        # Aggiungi l'estensione .json se non presente
        if not percorso_file.endswith('.json'):
            percorso_file = percorso_file + '.json'
        
        # Ottieni i dati da salvare
        data = self.to_dict()
        
        try:
            filepath = Path(percorso_file)
            filepath.parent.mkdir(exist_ok=True, parents=True)
            
            with open(filepath, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
            logging.info(f"Stato delle mappe salvato in formato JSON: {filepath}")
            
            # Salva gli oggetti interattivi
            oggetti_result = self.oggetti_manager.salva_oggetti_interattivi_modificati(self.mappe)
            
            return oggetti_result
        except Exception as e:
            logging.error(f"Errore nel salvataggio del gestore mappe: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return False

    def carica(self, percorso_file="mappe_salvataggio.json"):
        """
        Carica lo stato completo di tutte le mappe e relativi oggetti interattivi.
        
        Args:
            percorso_file (str): Percorso del file da cui caricare i dati
            
        Returns:
            bool: True se il caricamento è avvenuto con successo, False altrimenti
        """
        try:
            # Aggiungi l'estensione .json se non presente
            if not percorso_file.endswith('.json'):
                percorso_file = percorso_file + '.json'
                
            filepath = Path(percorso_file)
            
            # Verifica se esiste il file specificato
            if not filepath.exists():
                logging.error(f"File di salvataggio non trovato: {filepath}")
                return False
            
            with open(filepath, 'r', encoding='utf-8') as file:
                data = json.load(file)
            logging.info(f"Dati delle mappe caricati da JSON: {filepath}")
            
            # Processa i dati caricati
            return self.from_dict(data)
        except Exception as e:
            logging.error(f"Errore nel caricamento del gestore mappe: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return False

    def map_exists(self, nome_mappa):
        """
        Verifica se esiste una mappa con il nome specificato.
        
        Args:
            nome_mappa (str): Il nome della mappa da verificare
        
        Returns:
            bool: True se la mappa esiste, False altrimenti
        """
        return self.mappa_manager.map_exists(nome_mappa)

    def register_map(self, mappa):
        """
        Registra una nuova mappa nel gestore mappe.
        
        Args:
            mappa: L'oggetto mappa da registrare
        
        Returns:
            bool: True se la registrazione è avvenuta con successo, False altrimenti
        """
        return self.mappa_manager.aggiungi_mappa(mappa)

    def ottieni_lista_mappe(self):
        """
        Restituisce un dizionario con le informazioni sulle mappe disponibili
        
        Returns:
            dict: Dizionario con ID mappa come chiave e informazioni come valore
        """
        return self.mappa_manager.ottieni_lista_mappe()
