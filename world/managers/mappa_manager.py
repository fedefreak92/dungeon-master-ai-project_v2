"""
Manager principale per la gestione delle mappe di gioco.
"""

import logging
import json
import os
import time
import threading
from pathlib import Path
from world.mappa import Mappa
from util.config import get_save_path, create_backup, SAVE_FORMAT_VERSION

class MappaManager:
    """
    Manager per la gestione delle mappe di gioco.
    Si occupa della registrazione, accesso e modifica delle mappe.
    Implementa un sistema di caching per ottimizzare le prestazioni.
    """
    def __init__(self, limite_cache=5):
        """
        Inizializza il manager delle mappe.
        
        Args:
            limite_cache (int): Numero massimo di mappe da mantenere in cache
        """
        self.mappe = {}  # nome_mappa -> oggetto Mappa
        self.mappa_corrente = None
        
        # Sistema di caching
        self.cache_mappe = {}  # nome_mappa -> {"mappa": mappa, "ultimo_accesso": timestamp}
        self.limite_cache = limite_cache
        self.lock_cache = threading.RLock()  # Lock per operazioni di cache
        
    def aggiungi_mappa(self, mappa):
        """
        Registra una nuova mappa nel manager.
        
        Args:
            mappa (Mappa): L'oggetto mappa da registrare
        
        Returns:
            bool: True se la registrazione è avvenuta con successo, False altrimenti
        """
        try:
            if not mappa or not hasattr(mappa, 'nome') or not mappa.nome:
                logging.error("Impossibile registrare mappa senza nome")
                return False
            
            # Aggiungi la mappa al dizionario delle mappe
            self.mappe[mappa.nome] = mappa
            
            # Aggiungi alla cache
            with self.lock_cache:
                self.cache_mappe[mappa.nome] = {
                    "mappa": mappa,
                    "ultimo_accesso": time.time()
                }
                
            logging.info(f"Mappa '{mappa.nome}' registrata con successo")
            return True
        except Exception as e:
            logging.error(f"Errore nella registrazione della mappa: {e}")
            return False

    def ottieni_mappa(self, nome):
        """
        Restituisce una mappa per nome.
        Utilizza il sistema di cache per ottimizzare l'accesso.
        
        Args:
            nome (str): Nome della mappa da recuperare
        
        Returns:
            Mappa: L'oggetto mappa o None se non esiste
        """
        # Verifica se la mappa è in cache
        with self.lock_cache:
            if nome in self.cache_mappe:
                # Aggiorna il timestamp di ultimo accesso
                self.cache_mappe[nome]["ultimo_accesso"] = time.time()
                logging.debug(f"Mappa '{nome}' recuperata dalla cache")
                return self.cache_mappe[nome]["mappa"]
                
        # Se la mappa è registrata ma non in cache, caricala
        if nome in self.mappe:
            # Ottieni la mappa dalla collezione principale
            mappa = self.mappe[nome]
            
            # Aggiungi alla cache
            self._aggiungi_alla_cache(nome, mappa)
            
            # Avvia il prefetching delle mappe adiacenti in background
            threading.Thread(target=self._prefetch_mappe_adiacenti, args=(nome,), daemon=True).start()
            
            return mappa
            
        return None
    
    def _aggiungi_alla_cache(self, nome_mappa, mappa):
        """
        Aggiunge una mappa alla cache, gestendo il limite.
        
        Args:
            nome_mappa (str): Nome della mappa
            mappa (Mappa): Oggetto mappa da aggiungere alla cache
        """
        with self.lock_cache:
            # Se la cache è piena, rimuovi la mappa meno usata
            if len(self.cache_mappe) >= self.limite_cache:
                self._rimuovi_mappa_meno_usata()
                
            # Aggiungi la mappa alla cache
            self.cache_mappe[nome_mappa] = {
                "mappa": mappa,
                "ultimo_accesso": time.time()
            }
            logging.debug(f"Mappa '{nome_mappa}' aggiunta alla cache")
    
    def _rimuovi_mappa_meno_usata(self):
        """Rimuove dalla cache la mappa con il timestamp di accesso più vecchio."""
        if not self.cache_mappe:
            return
            
        # Trova la mappa meno usata (timestamp più vecchio)
        mappa_da_rimuovere = min(self.cache_mappe.items(), 
                              key=lambda x: x[1]["ultimo_accesso"])
        
        # Rimuovi dalla cache
        nome_mappa = mappa_da_rimuovere[0]
        del self.cache_mappe[nome_mappa]
        logging.debug(f"Mappa '{nome_mappa}' rimossa dalla cache")
    
    def _prefetch_mappe_adiacenti(self, nome_mappa):
        """
        Precarica in background le mappe adiacenti a quella specificata.
        
        Args:
            nome_mappa (str): Nome della mappa di riferimento
        """
        try:
            # Ottieni la mappa
            mappa = self.mappe.get(nome_mappa)
            if not mappa:
                return
                
            # Raccogli i nomi delle mappe adiacenti (collegate da porte)
            mappe_adiacenti = set()
            for porta_dest in mappa.porte.values():
                mappa_dest = porta_dest[0]
                if mappa_dest != nome_mappa and mappa_dest in self.mappe:
                    mappe_adiacenti.add(mappa_dest)
            
            # Precarica le mappe adiacenti
            for nome_mappa_adiacente in mappe_adiacenti:
                # Non precarica se è già in cache
                with self.lock_cache:
                    if nome_mappa_adiacente in self.cache_mappe:
                        continue
                
                # Ottieni la mappa e aggiungila alla cache
                mappa_adiacente = self.mappe.get(nome_mappa_adiacente)
                if mappa_adiacente:
                    self._aggiungi_alla_cache(nome_mappa_adiacente, mappa_adiacente)
                    logging.debug(f"Mappa adiacente '{nome_mappa_adiacente}' precaricata")
        except Exception as e:
            logging.error(f"Errore durante il prefetch delle mappe adiacenti: {e}")
    
    def imposta_mappa_attuale(self, nome):
        """
        Imposta la mappa attuale per riferimento facile.
        
        Args:
            nome (str): Nome della mappa da impostare come attuale
            
        Returns:
            bool: True se l'operazione è riuscita, False altrimenti
        """
        if nome in self.mappe:
            # Ottieni la mappa (questo attiverà anche il sistema di cache)
            mappa = self.ottieni_mappa(nome)
            self.mappa_corrente = mappa
            
            # Avvia il prefetching delle mappe adiacenti in background
            threading.Thread(target=self._prefetch_mappe_adiacenti, args=(nome,), daemon=True).start()
            
            return True
        return False
    
    def map_exists(self, nome_mappa):
        """
        Verifica se esiste una mappa con il nome specificato.
        
        Args:
            nome_mappa (str): Il nome della mappa da verificare
        
        Returns:
            bool: True se la mappa esiste, False altrimenti
        """
        return nome_mappa in self.mappe
        
    def ottieni_lista_mappe(self):
        """
        Restituisce un dizionario con le informazioni sulle mappe disponibili
        
        Returns:
            dict: Dizionario con ID mappa come chiave e informazioni come valore
        """
        mappe_disponibili = {}
        
        for id_mappa, mappa in self.mappe.items():
            # Estrai informazioni rilevanti dalla mappa
            info_mappa = {
                "nome": getattr(mappa, "nome", id_mappa),
                "descrizione": mappa.descrizione if hasattr(mappa, "descrizione") else "Nessuna descrizione disponibile",
                "livello_min": getattr(mappa, "livello_min", 1)
            }
            
            # Aggiungi eventuali informazioni aggiuntive
            if hasattr(mappa, "tags") and mappa.tags:
                info_mappa["tags"] = mappa.tags
                
            if hasattr(mappa, "dimensioni"):
                info_mappa["dimensioni"] = mappa.dimensioni
            
            mappe_disponibili[id_mappa] = info_mappa
        
        return mappe_disponibili
    
    def _verifica_mappa_valida(self, mappa):
        """
        Verifica che una mappa sia valida e completa.
        
        Args:
            mappa: L'oggetto Mappa da verificare
            
        Returns:
            bool: True se la mappa è valida, False altrimenti
        """
        # Verifica che la mappa abbia un nome
        if not mappa.nome:
            logging.error("Mappa senza nome")
            return False
            
        # Verifica che la griglia sia presente e delle dimensioni corrette
        if not mappa.griglia:
            logging.error(f"Mappa {mappa.nome} senza griglia")
            return False
            
        # Verifica che le dimensioni della griglia corrispondano a quelle dichiarate
        if len(mappa.griglia) != mappa.altezza:
            logging.error(f"Mappa {mappa.nome}: altezza dichiarata {mappa.altezza} ma griglia ha {len(mappa.griglia)} righe")
            return False
            
        for riga in mappa.griglia:
            if len(riga) != mappa.larghezza:
                logging.error(f"Mappa {mappa.nome}: larghezza dichiarata {mappa.larghezza} ma riga ha {len(riga)} colonne")
                return False
        
        # Verifica che la posizione iniziale sia impostata e valida
        if not mappa.pos_iniziale_giocatore or not isinstance(mappa.pos_iniziale_giocatore, (list, tuple)) or len(mappa.pos_iniziale_giocatore) != 2:
            logging.error(f"Mappa {mappa.nome}: posizione iniziale del giocatore non impostata correttamente")
            return False
            
        # Estrai le coordinate x,y indipendentemente dal tipo (tupla o lista)
        x, y = mappa.pos_iniziale_giocatore[0], mappa.pos_iniziale_giocatore[1]
        
        if x < 0 or x >= mappa.larghezza or y < 0 or y >= mappa.altezza:
            logging.error(f"Mappa {mappa.nome}: posizione iniziale del giocatore ({x}, {y}) fuori dai limiti della mappa")
            return False
            
        # Se la posizione iniziale è in un muro, è un errore
        if mappa.griglia[y][x] != 0:  # Assumendo che 0 sia lo spazio vuoto
            logging.error(f"Mappa {mappa.nome}: posizione iniziale del giocatore ({x}, {y}) è in un muro")
            return False
            
        # Tutte le verifiche sono passate
        return True
    
    def ottieni_info_posizione(self, x, y, mappa=None):
        """
        Ottiene informazioni su cosa si trova in una posizione specifica.
        
        Args:
            x, y (int): Coordinate da controllare
            mappa (Mappa, optional): Mappa in cui cercare. Se None, usa la mappa attuale.
            
        Returns:
            dict: Informazioni sulla posizione con chiavi 'tipo', 'oggetto' e 'messaggio'
        """
        # Se non è specificata una mappa, usa la mappa attuale
        mappa = mappa or self.mappa_corrente
        if not mappa:
            return {"tipo": "errore", "oggetto": None, "messaggio": "Nessuna mappa attiva"}
            
        # Verifica che la posizione sia valida
        if not (0 <= x < mappa.larghezza and 0 <= y < mappa.altezza):
            return {"tipo": "fuori_mappa", "oggetto": None, "messaggio": "Posizione fuori dai limiti della mappa"}
            
        # Verifica se c'è un muro
        if mappa.griglia[y][x] != 0:  # Assumendo che 0 sia lo spazio vuoto
            return {"tipo": "muro", "oggetto": None, "messaggio": "C'è un muro qui"}
            
        # Verifica se c'è un oggetto
        if (x, y) in mappa.oggetti:
            oggetto = mappa.oggetti[(x, y)]
            return {"tipo": "oggetto", "oggetto": oggetto, "messaggio": f"C'è {oggetto.nome} qui"}
            
        # Verifica se c'è un NPC
        if (x, y) in mappa.npg:
            npg = mappa.npg[(x, y)]
            return {"tipo": "npg", "oggetto": npg, "messaggio": f"C'è {npg.nome} qui"}
            
        # Verifica se c'è una porta
        if (x, y) in mappa.porte:
            porta_dest = mappa.porte[(x, y)]
            mappa_dest = porta_dest[0]
            return {"tipo": "porta", "oggetto": porta_dest, "messaggio": f"C'è una porta verso {mappa_dest} qui"}
            
        # Se non c'è nulla
        return {"tipo": "vuoto", "oggetto": None, "messaggio": "Non c'è nulla qui"}
    
    def muovi_giocatore(self, giocatore, dx, dy):
        """
        Gestisce lo spostamento del giocatore sulla mappa.
        
        Args:
            giocatore (Giocatore): Il giocatore da muovere
            dx, dy (int): Delta di spostamento
            
        Returns:
            dict: Risultato del movimento con chiavi 'successo', 'messaggio', 'cambio_mappa'
        """
        # Verifica che siamo su una mappa valida
        if not giocatore.mappa_corrente or giocatore.mappa_corrente not in self.mappe:
            return {"successo": False, "messaggio": "Mappa non valida", "cambio_mappa": False}
            
        # Ottieni la mappa corrente (questo attiverà anche il sistema di cache)
        mappa = self.ottieni_mappa(giocatore.mappa_corrente)
        
        # Calcola la nuova posizione
        nuovo_x = giocatore.x + dx
        nuovo_y = giocatore.y + dy
        
        # Verifica che la nuova posizione sia valida
        if not (0 <= nuovo_x < mappa.larghezza and 0 <= nuovo_y < mappa.altezza):
            return {"successo": False, "messaggio": "Posizione fuori dai limiti della mappa", "cambio_mappa": False}
        
        # Verifica se c'è un muro
        if mappa.griglia[nuovo_y][nuovo_x] != 0:  # Assumendo che 0 sia lo spazio vuoto
            return {"successo": False, "messaggio": "C'è un muro in quella direzione", "cambio_mappa": False}
        
        # Verifica se c'è un oggetto bloccante
        if (nuovo_x, nuovo_y) in mappa.oggetti:
            oggetto = mappa.oggetti[(nuovo_x, nuovo_y)]
            # Verifica se l'oggetto è bloccante
            if hasattr(oggetto, 'bloccante') and oggetto.bloccante:
                return {"successo": False, "messaggio": f"C'è un {oggetto.nome} bloccante", "cambio_mappa": False}
        
        # Verifica se c'è un NPC (che sono sempre bloccanti)
        if (nuovo_x, nuovo_y) in mappa.npg:
            npg = mappa.npg[(nuovo_x, nuovo_y)]
            return {"successo": False, "messaggio": f"{npg.nome} ti blocca il passaggio", "cambio_mappa": False}
        
        # Verifica se c'è una porta
        porta_dest = None
        if (nuovo_x, nuovo_y) in mappa.porte:
            porta_dest = mappa.porte[(nuovo_x, nuovo_y)]
        
        # Aggiorna la posizione del giocatore
        giocatore.x = nuovo_x
        giocatore.y = nuovo_y
        
        # Se c'è una porta, cambia mappa
        if porta_dest:
            mappa_dest, x_dest, y_dest = porta_dest
            # Cambia mappa
            risultato = self.cambia_mappa_giocatore(giocatore, mappa_dest, x_dest, y_dest)
            if risultato["successo"]:
                return {"successo": True, "messaggio": f"Sei entrato in {mappa_dest}", "cambio_mappa": True}
            else:
                return {"successo": True, "messaggio": risultato["messaggio"], "cambio_mappa": False}
        
        return {"successo": True, "messaggio": "Ti sei spostato", "cambio_mappa": False}
    
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
        # Verifica che la mappa esista
        if nome_mappa not in self.mappe:
            return {"successo": False, "messaggio": f"Mappa {nome_mappa} non esistente"}
            
        # Ottieni la nuova mappa (questo attiverà anche il sistema di cache)
        nuova_mappa = self.ottieni_mappa(nome_mappa)
        
        # Se x e y non sono specificati, usa la posizione iniziale della mappa
        if x is None or y is None:
            x, y = nuova_mappa.pos_iniziale_giocatore
            
        # Verifica che la posizione sia valida
        if not (0 <= x < nuova_mappa.larghezza and 0 <= y < nuova_mappa.altezza):
            return {"successo": False, "messaggio": f"Posizione ({x}, {y}) fuori dai limiti della mappa {nome_mappa}"}
            
        # Verifica che la posizione non sia un muro
        if nuova_mappa.griglia[y][x] != 0:  # Assumendo che 0 sia lo spazio vuoto
            return {"successo": False, "messaggio": f"Posizione ({x}, {y}) è un muro nella mappa {nome_mappa}"}
            
        # Verifica che la posizione non sia occupata
        if (x, y) in nuova_mappa.oggetti or (x, y) in nuova_mappa.npg:
            return {"successo": False, "messaggio": f"Posizione ({x}, {y}) già occupata nella mappa {nome_mappa}"}
            
        # Aggiorna la mappa e la posizione del giocatore
        giocatore.mappa_corrente = nome_mappa
        giocatore.x = x
        giocatore.y = y
        
        # Imposta la nuova mappa come mappa attuale
        self.imposta_mappa_attuale(nome_mappa)
        
        return {"successo": True, "messaggio": f"Sei entrato in {nome_mappa}"}
    
    def to_dict(self):
        """
        Converte il manager mappe in un dizionario per la serializzazione.
        
        Returns:
            dict: Rappresentazione del manager mappe in formato dizionario
        """
        # Lista delle mappe serializzate
        mappe_dict = {}
        for nome, mappa in self.mappe.items():
            mappe_dict[nome] = mappa.to_dict()
            
        return {
            "mappe": mappe_dict,
            "mappa_attuale": self.mappa_corrente.nome if self.mappa_corrente else None,
            "versione": SAVE_FORMAT_VERSION
        }
        
    def from_dict(self, data):
        """
        Carica lo stato del manager mappe da un dizionario.
        
        Args:
            data (dict): Dizionario contenente lo stato del manager mappe
            
        Returns:
            bool: True se il caricamento è avvenuto con successo, False altrimenti
        """
        try:
            # Carica le mappe dal dizionario
            mappe_data = data.get("mappe", {})
            self.mappe = {}
            
            # Resettiamo la cache
            with self.lock_cache:
                self.cache_mappe = {}
            
            for nome_mappa, mappa_dict in mappe_data.items():
                self.mappe[nome_mappa] = Mappa.from_dict(mappa_dict)
            
            # Imposta la mappa attuale
            mappa_attuale_nome = data.get("mappa_attuale")
            if mappa_attuale_nome and mappa_attuale_nome in self.mappe:
                # Ottieni la mappa (questo la metterà in cache)
                self.mappa_corrente = self.ottieni_mappa(mappa_attuale_nome)
            elif self.mappe:
                # Se non c'è una mappa attuale, imposta la prima disponibile
                primo_nome = next(iter(self.mappe.keys()))
                self.mappa_corrente = self.ottieni_mappa(primo_nome)
            
            return True
        except Exception as e:
            logging.error(f"Errore durante il caricamento delle mappe: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return False
    
    def salva(self, percorso_file="mappe_salvataggio.json"):
        """
        Salva lo stato completo di tutte le mappe.
        
        Args:
            percorso_file (str): Percorso del file in cui salvare i dati
            
        Returns:
            bool: True se il salvataggio è avvenuto con successo, False altrimenti
        """
        try:
            # Crea il dizionario di salvataggio
            dati_salvataggio = self.to_dict()
            
            # Determina il percorso di salvataggio
            save_path = get_save_path(percorso_file)
            
            # Crea un backup se il file esiste già
            if os.path.exists(save_path):
                backup_success = create_backup(save_path)
                if backup_success:
                    logging.info(f"Backup creato per {save_path}")
                else:
                    logging.warning(f"Impossibile creare backup per {save_path}")
            
            # Assicura che la directory esista
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Salva il file
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(dati_salvataggio, f, indent=4, ensure_ascii=False)
            
            logging.info(f"Mappe salvate con successo in {save_path}")
            return True
        except Exception as e:
            import traceback
            logging.error(f"Errore durante il salvataggio delle mappe: {e}")
            logging.error(traceback.format_exc())
            return False
    
    def carica(self, percorso_file="mappe_salvataggio.json"):
        """
        Carica lo stato completo di tutte le mappe.
        
        Args:
            percorso_file (str): Percorso del file da cui caricare i dati
            
        Returns:
            bool: True se il caricamento è avvenuto con successo, False altrimenti
        """
        try:
            # Determina il percorso di caricamento
            save_path = get_save_path(percorso_file)
            
            # Verifica che il file esista
            if not os.path.exists(save_path):
                logging.error(f"File di salvataggio non trovato: {save_path}")
                return False
            
            # Carica il file
            with open(save_path, 'r', encoding='utf-8') as f:
                dati_salvati = json.load(f)
            
            # Verifica la versione
            versione_salvata = dati_salvati.get("versione", "1.0")
            if versione_salvata != SAVE_FORMAT_VERSION:
                logging.warning(f"Versione del salvataggio ({versione_salvata}) diversa da quella corrente ({SAVE_FORMAT_VERSION})")
            
            # Carica i dati
            result = self.from_dict(dati_salvati)
            
            if result:
                logging.info(f"Mappe caricate con successo da {save_path}")
            
            return result
        except Exception as e:
            import traceback
            logging.error(f"Errore durante il caricamento delle mappe: {e}")
            logging.error(traceback.format_exc())
            return False 