from world.mappa import Mappa
from world.gestore_mappe import GestitoreMappe
from entities.giocatore import Giocatore
import random
import logging
from util.data_manager import get_data_manager

class ControllerMappa:
    def __init__(self, larghezza=80, altezza=60, dim_cella=1, limite_cache=5):
        """
        Inizializza il controller che gestisce l'interazione tra l'interfaccia
        e la logica di gioco.
        
        Args:
            larghezza (int): Larghezza della mappa in celle
            altezza (int): Altezza della mappa in celle
            dim_cella (int): Dimensione di una cella (per compatibilità, non usato)
            limite_cache (int): Numero massimo di mappe da mantenere in cache
        """
        self.larghezza = larghezza
        self.altezza = altezza
        self.dim_cella = dim_cella
        
        # Inizializza il gestore delle mappe con sistema di caching
        self.gestore_mappe = GestitoreMappe(limite_cache=limite_cache)
        
        # Crea un giocatore
        self.giocatore = Giocatore("Avventuriero", "Guerriero")
        
        # Imposta la mappa iniziale
        self.giocatore.mappa_corrente = "taverna"
        self.gestore_mappe.imposta_mappa_attuale(self.giocatore.mappa_corrente)
        self.giocatore.x, self.giocatore.y = self.gestore_mappe.mappa_attuale.pos_iniziale_giocatore
        
        # Stato di interazione
        self.interazione_attiva = False
        self.oggetto_selezionato = None
        self.npg_selezionato = None
        
        logging.info("Controller mappa inizializzato con sistema di caching")

    def muovi_giocatore(self, dx, dy):
        """
        Gestisce lo spostamento del giocatore sulla mappa.
        
        Args:
            dx (int): Spostamento sull'asse X
            dy (int): Spostamento sull'asse Y
            
        Returns:
            bool: True se il movimento è avvenuto, False altrimenti
        """
        return self.giocatore.muovi(dx, dy, self.gestore_mappe)
    
    def interagisci(self):
        """
        Gestisce l'interazione con l'elemento adiacente al giocatore.
        
        Returns:
            tuple: (tipo_interazione, oggetto_interazione) o (None, None) se non è possibile interagire
        """
        mappa = self.gestore_mappe.ottieni_mappa(self.giocatore.mappa_corrente)
        if not mappa:
            return None, None
        
        # Controlla in tutte le direzioni adiacenti
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            x, y = self.giocatore.x + dx, self.giocatore.y + dy
            
            # Controlla se c'è un oggetto
            oggetto = mappa.ottieni_oggetto_a(x, y)
            if oggetto:
                self.oggetto_selezionato = oggetto
                return "oggetto", oggetto
            
            # Controlla se c'è un NPG
            npg = mappa.ottieni_npg_a(x, y)
            if npg:
                self.npg_selezionato = npg
                return "npg", npg
        
        return None, None
    
    def ottieni_elementi_mappa(self):
        """
        Recupera tutti gli elementi presenti sulla mappa attuale.
        
        Returns:
            dict: Dizionario con gli elementi sulla mappa (muri, oggetti, npg)
        """
        if not self.gestore_mappe.mappa_attuale:
            return {}
            
        mappa = self.gestore_mappe.mappa_attuale
        
        elementi = {
            "muri": [],
            "oggetti": {},
            "npg": {},
            "porte": {}
        }
        
        # Aggiungi i muri
        for y in range(mappa.altezza):
            for x in range(mappa.larghezza):
                if mappa.griglia[y][x] == 1:
                    elementi["muri"].append((x, y))
        
        # Aggiungi oggetti e NPG
        elementi["oggetti"] = mappa.oggetti
        elementi["npg"] = mappa.npg
        elementi["porte"] = mappa.porte
        
        return elementi
    
    def ottieni_oggetti_vicini(self, raggio=1):
        """
        Recupera gli oggetti vicini al giocatore.
        
        Args:
            raggio (int): Raggio di ricerca
            
        Returns:
            dict: Dizionario con gli oggetti vicini
        """
        return self.giocatore.ottieni_oggetti_vicini(self.gestore_mappe, raggio)
    
    def ottieni_npg_vicini(self, raggio=1):
        """
        Recupera gli NPG vicini al giocatore.
        
        Args:
            raggio (int): Raggio di ricerca
            
        Returns:
            dict: Dizionario con gli NPG vicini
        """
        mappa = self.gestore_mappe.ottieni_mappa(self.giocatore.mappa_corrente)
        if not mappa:
            return {}
        
        return mappa.ottieni_npg_vicini(self.giocatore.x, self.giocatore.y, raggio)
    
    def esegui_interazione_oggetto(self):
        """
        Esegue l'interazione con l'oggetto selezionato.
        
        Returns:
            str: Risultato dell'interazione
        """
        if self.oggetto_selezionato:
            risultato = self.oggetto_selezionato.interagisci(self.giocatore)
            self.oggetto_selezionato = None
            return risultato
        return None
    
    def esegui_interazione_npg(self):
        """
        Esegue l'interazione con l'NPC selezionato mostrando un dialogo.
        
        Returns:
            dict: Dati del dialogo o None
        """
        if not self.npg_selezionato:
            return None
        
        # Ottieni i dati del dialogo
        dialogo = self.npg_selezionato.ottieni_conversazione("inizio")
        
        # Salva l'NPC corrente per riferimento futuro
        npg_corrente = self.npg_selezionato
        self.npg_selezionato = None
        
        return {
            "npg": npg_corrente,
            "dialogo": dialogo
        }
    
    def continua_dialogo(self, npg, stato_dialogo):
        """
        Continua un dialogo esistente con un NPC.
        
        Args:
            npg: L'NPC con cui dialogare
            stato_dialogo: Lo stato del dialogo a cui passare
            
        Returns:
            dict: Nuovi dati del dialogo o None
        """
        if not stato_dialogo:
            return None
        
        # Ottieni i dati del nuovo stato di dialogo
        dialogo = npg.ottieni_conversazione(stato_dialogo)
        
        # Se c'è un effetto, applicalo
        if dialogo and "effetto" in dialogo:
            effetto = dialogo["effetto"]
            
            # Gestione effetti semplici
            if effetto == "riposo":
                # Usa cura invece di impostare direttamente hp
                quantita_cura = self.giocatore.hp_max - self.giocatore.hp
                if quantita_cura > 0:
                    self.giocatore.cura(quantita_cura, None)  # Passiamo None come gioco, dato che non abbiamo accesso all'oggetto gioco qui
                return {"npg": npg, "dialogo": dialogo, "messaggio": "Ti sei riposato e hai recuperato tutti i punti vita."}
            # Gestione effetti di scambio oggetti
            elif isinstance(effetto, dict) and effetto["tipo"] == "scambio":
                # Implementazione semplificata
                nome_oggetto = effetto["oggetto"]
                costo = effetto["costo"]
                
                if self.giocatore.oro >= costo:
                    self.giocatore.oro -= costo
                    # Qui andrebbe aggiunto l'oggetto all'inventario
                    return {"npg": npg, "dialogo": dialogo, "messaggio": f"Hai acquistato {nome_oggetto} per {costo} monete d'oro."}
                else:
                    return {"npg": npg, "dialogo": dialogo, "messaggio": "Non hai abbastanza oro per questo!"}
        
        return {"npg": npg, "dialogo": dialogo}
    
    def cambia_mappa(self, nome_mappa):
        """
        Cambia la mappa corrente.
        Utilizza il sistema di caching e prefetching integrato nel gestore mappe.
        
        Args:
            nome_mappa (str): Nome della nuova mappa
            
        Returns:
            bool: True se il cambio è avvenuto, False altrimenti
        """
        # Prima di cambiare mappa, verifica se esiste
        if not self.gestore_mappe.map_exists(nome_mappa):
            logging.warning(f"Tentativo di cambiare a una mappa non esistente: {nome_mappa}")
            return False
            
        logging.info(f"Cambio mappa a: {nome_mappa}")
        return self.gestore_mappe.cambia_mappa_giocatore(self.giocatore, nome_mappa)

    def trasferisci_oggetti_da_stato(self, nome_mappa, stato, gioco=None):
        """
        Trasferisce oggetti e NPG dallo stato alla mappa corrispondente.
        Utilizza il sistema di cache per accedere alla mappa.
        
        Args:
            nome_mappa: Nome della mappa
            stato: Stato del gioco contenente oggetti e NPG
            gioco: Riferimento al gioco principale (opzionale)
            
        Returns:
            bool: True se l'operazione è riuscita, False altrimenti
        """
        # Ottieni la mappa dalla cache o caricala
        mappa = self.gestore_mappe.ottieni_mappa(nome_mappa)
        if not mappa:
            logging.error(f"Impossibile trovare la mappa {nome_mappa} per trasferire gli oggetti")
            return False
        
        # Carica le configurazioni degli oggetti e NPC da mappe_oggetti.json e mappe_npg.json
        data_manager = get_data_manager()
        oggetti_config = data_manager.load_data("items", "mappe_oggetti.json")
        npg_config = data_manager.load_data("npc", "mappe_npg.json")
        
        # Verifica che i file di configurazione siano stati caricati
        if not oggetti_config:
            logging.warning(f"File di configurazione oggetti non trovato")
            oggetti_config = {}
        if not npg_config:
            logging.warning(f"File di configurazione NPG non trovato")
            npg_config = {}
        
        # Ottieni le configurazioni specifiche per questa mappa
        oggetti_mappa = oggetti_config.get(nome_mappa, [])
        npg_mappa = npg_config.get(nome_mappa, [])
        
        # Crea un dizionario delle posizioni degli oggetti per facilità di accesso
        pos_oggetti = {}
        for oggetto_info in oggetti_mappa:
            nome_oggetto = oggetto_info.get("nome")
            posizione = oggetto_info.get("posizione")
            if nome_oggetto and posizione and len(posizione) == 2:
                pos_oggetti[nome_oggetto] = posizione
        
        # Crea un dizionario delle posizioni degli NPG per facilità di accesso
        pos_npg = {}
        for npg_info in npg_mappa:
            nome_npg = npg_info.get("nome")
            posizione = npg_info.get("posizione")
            if nome_npg and posizione and len(posizione) == 2:
                pos_npg[nome_npg] = posizione
        
        # Posiziona gli oggetti interattivi sulla mappa
        for chiave, oggetto in stato.oggetti_interattivi.items():
            # Prima verifica se esiste una posizione configurata
            if chiave in pos_oggetti:
                x, y = pos_oggetti[chiave]
                if mappa.is_posizione_valida(x, y) and (x, y) not in mappa.oggetti and (x, y) not in mappa.npg:
                    mappa.aggiungi_oggetto(oggetto, x, y)
                    if gioco:
                        gioco.io.mostra_messaggio(f"Posizionato oggetto {chiave} in ({x}, {y})")
                    continue
            
            # Se non riesce, utilizza le posizioni predefinite come fallback
            posizioni_predefinite = {
                "bancone": (5, 5),
                "camino": (15, 3),
                "baule_nascondiglio": (8, 10),
                "porta_cantina": (9, 9),
                "leva_segreta": (18, 5),
                "trappola_pavimento": (10, 15),
                "altare_magico": (17, 13)
            }
            
            if chiave in posizioni_predefinite:
                x, y = posizioni_predefinite[chiave]
                if mappa.is_posizione_valida(x, y) and (x, y) not in mappa.oggetti and (x, y) not in mappa.npg:
                    mappa.aggiungi_oggetto(oggetto, x, y)
                    if gioco:
                        gioco.io.mostra_messaggio(f"Posizionato oggetto {chiave} in posizione predefinita ({x}, {y})")
                    continue
            
            # Se ancora non riesce, cerca una posizione alternativa
            posizioni_alternative = [(7, 12), (14, 7), (16, 10), (4, 8), (19, 7)]
            posizionato = False
            
            for x, y in posizioni_alternative:
                if mappa.is_posizione_valida(x, y) and (x, y) not in mappa.oggetti and (x, y) not in mappa.npg:
                    mappa.aggiungi_oggetto(oggetto, x, y)
                    if gioco:
                        gioco.io.mostra_messaggio(f"Posizionato oggetto {chiave} in posizione alternativa ({x}, {y})")
                    posizionato = True
                    break
            
            # Se non riesce neanche con le posizioni alternative, cerca una posizione casuale
            if not posizionato:
                tentativi = 0
                while tentativi < 20:
                    x = random.randint(1, mappa.larghezza - 2)
                    y = random.randint(1, mappa.altezza - 2)
                    
                    if mappa.is_posizione_valida(x, y) and (x, y) not in mappa.oggetti and (x, y) not in mappa.npg:
                        mappa.aggiungi_oggetto(oggetto, x, y)
                        if gioco:
                            gioco.io.mostra_messaggio(f"Posizionato oggetto {chiave} in posizione casuale ({x}, {y})")
                        break
                    
                    tentativi += 1
        
        # Posiziona NPG sulla mappa
        for nome, npg in stato.npg_presenti.items():
            # Prima verifica se esiste una posizione configurata
            if nome in pos_npg:
                x, y = pos_npg[nome]
                if mappa.is_posizione_valida(x, y) and (x, y) not in mappa.oggetti and (x, y) not in mappa.npg:
                    mappa.aggiungi_npg(npg, x, y)
                    if gioco:
                        gioco.io.mostra_messaggio(f"Posizionato {nome} in ({x}, {y})")
                    continue
            
            # Posizioni alternative in caso le principali siano occupate
            pos_npg_alternative = {
                "Durnan": [(5, 5), (6, 5), (5, 6)],
                "Elminster": [(8, 8), (9, 8), (8, 9)],
                "Mirt": [(7, 8), (8, 7), (6, 7)]
            }
            
            # Se c'è una lista di posizioni alternative, prova quelle
            if nome in pos_npg_alternative:
                posizionato = False
                for x, y in pos_npg_alternative[nome]:
                    if mappa.is_posizione_valida(x, y) and (x, y) not in mappa.oggetti and (x, y) not in mappa.npg:
                        mappa.aggiungi_npg(npg, x, y)
                        if gioco:
                            gioco.io.mostra_messaggio(f"Posizionato {nome} in posizione alternativa ({x}, {y})")
                        posizionato = True
                        break
                
                if posizionato:
                    continue
            
            # Se ancora non riesce, cerca una posizione casuale
            posizionato = False
            tentativi = 0
            
            while not posizionato and tentativi < 20:
                x = random.randint(1, mappa.larghezza - 2)
                y = random.randint(1, mappa.altezza - 2)
                
                if mappa.is_posizione_valida(x, y) and (x, y) not in mappa.oggetti and (x, y) not in mappa.npg:
                    mappa.aggiungi_npg(npg, x, y)
                    if gioco:
                        gioco.io.mostra_messaggio(f"Posizionato {nome} in posizione casuale ({x}, {y})")
                    posizionato = True
                
                tentativi += 1
                
            if not posizionato and gioco:
                gioco.io.mostra_messaggio(f"ERRORE: Non è stato possibile posizionare {nome}")
            
        return True
