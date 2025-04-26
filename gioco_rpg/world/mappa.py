from items.oggetto_interattivo import OggettoInterattivo, Porta 
from entities.npg import NPG     
from entities.entita import Entita   
from entities.giocatore import Giocatore
from entities.nemico import Nemico
import json
import logging
from pathlib import Path
import os

class Mappa:
    def __init__(self, nome, larghezza, altezza, tipo="interno", descrizione=""):
        """
        Inizializza una mappa con nome, dimensioni e tipo.
        
        Args:
            nome (str): Nome identificativo della mappa
            larghezza (int): Larghezza della mappa in celle
            altezza (int): Altezza della mappa in celle
            tipo (str): Tipo di mappa (interno, esterno, sotterraneo)
            descrizione (str): Descrizione testuale della mappa
        """
        self.nome = nome
        self.larghezza = larghezza
        self.altezza = altezza
        self.tipo = tipo
        self.descrizione = descrizione
        
        # Inizializza la griglia con spazi vuoti (0)
        self.griglia = [[0 for _ in range(larghezza)] for _ in range(altezza)]
        
        # Inizializza dizionari per oggetti e NPG
        self.oggetti = {}  # (x, y) -> oggetto
        self.npg = {}      # (x, y) -> NPG
        self.porte = {}    # (x, y) -> (mappa_dest, x_dest, y_dest)
        
        # Posizione iniziale del giocatore
        self._pos_iniziale_giocatore = (1, 1)  # Default, può essere cambiata
        
    @property
    def pos_iniziale_giocatore(self):
        """Ottiene la posizione iniziale del giocatore come tupla."""
        return self._pos_iniziale_giocatore
        
    @pos_iniziale_giocatore.setter
    def pos_iniziale_giocatore(self, pos):
        """
        Imposta la posizione iniziale del giocatore, convertendo in tupla se necessario.
        
        Args:
            pos: Posizione (x, y) come tupla o lista
        """
        if isinstance(pos, list):
            self._pos_iniziale_giocatore = tuple(pos)
        else:
            self._pos_iniziale_giocatore = pos
        
    def aggiungi_oggetto(self, oggetto, x, y):
        """Aggiunge un oggetto alla mappa in una posizione specifica"""
        self.oggetti[(x, y)] = oggetto
        oggetto.posizione = (x, y, self.nome)  # Aggiorna la posizione dell'oggetto
        
    def aggiungi_npg(self, npg, x, y):
        """Aggiunge un NPG alla mappa in una posizione specifica"""
        self.npg[(x, y)] = npg
        npg.imposta_posizione(x, y)  # Utilizza il metodo esistente in NPG
        
    def aggiungi_porta(self, porta, x, y, mappa_dest, x_dest, y_dest):
        """Collega una porta a un'altra mappa e posizione"""
        self.oggetti[(x, y)] = porta
        porta.posizione = (x, y, self.nome)
        self.porte[(x, y)] = (mappa_dest, x_dest, y_dest)
        
    def imposta_muro(self, x, y):
        """Marca una cella come muro"""
        if 0 <= x < self.larghezza and 0 <= y < self.altezza:
            self.griglia[y][x] = 1
            
    def ottieni_oggetto_a(self, x, y):
        """Restituisce l'oggetto alla posizione specificata o None"""
        return self.oggetti.get((x, y))
        
    def ottieni_npg_a(self, x, y):
        """Restituisce l'NPG alla posizione specificata o None"""
        return self.npg.get((x, y))
    
    def ottieni_porta_a(self, x, y):
        """Restituisce la destinazione della porta alla posizione specificata o None"""
        return self.porte.get((x, y))
        
    def is_posizione_valida(self, x, y):
        """Verifica se la posizione è valida e attraversabile"""
        if 0 <= x < self.larghezza and 0 <= y < self.altezza:
            return self.griglia[y][x] == 0  # 0 = cella vuota
        return False
    
    def genera_rappresentazione_ascii(self, pos_giocatore=None):
        """
        Genera una rappresentazione ASCII della mappa
        
        Args:
            pos_giocatore: Tuple (x, y) della posizione del giocatore
        
        Returns:
            str: Rappresentazione ASCII della mappa
        """
        mappa_ascii = []
        for y in range(self.altezza):
            riga = ""
            for x in range(self.larghezza):
                if pos_giocatore and pos_giocatore == (x, y):
                    riga += "P"  # Giocatore, usiamo sempre P per coerenza visiva
                elif (x, y) in self.npg:
                    riga += self.npg[(x, y)].token  # Usa il token dell'NPG
                elif (x, y) in self.oggetti:
                    riga += self.oggetti[(x, y)].token  # Usa il token dell'oggetto
                elif self.griglia[y][x] == 1:
                    riga += "#"  # Muro
                else:
                    riga += "."  # Spazio vuoto
            mappa_ascii.append(riga)
        
        return "\n".join(mappa_ascii)
    
    def genera_layers_rendering(self):
        """
        Genera i layer per il rendering grafico della mappa.
        
        Returns:
            list: Lista di layer con informazioni per il rendering
        """
        # Inizializza i layer di base: pavimento, muri, oggetti
        layer_pavimento = {
            "id": 0,
            "name": "pavimento",
            "data": []
        }
        
        layer_muri = {
            "id": 1, 
            "name": "muri",
            "data": []
        }
        
        layer_porte = {
            "id": 2,
            "name": "porte",
            "data": []
        }
        
        # Prepara i dati dei layer
        for y in range(self.altezza):
            for x in range(self.larghezza):
                # Calcola l'indice lineare
                idx = y * self.larghezza + x
                
                # Determina il tipo di tile
                if (x, y) in self.porte:
                    # Porte hanno ID 3
                    layer_porte["data"].append(3)
                    layer_muri["data"].append(0)  # Nessun muro dove c'è una porta
                elif self.griglia[y][x] == 1:
                    # Muri hanno ID 2
                    layer_muri["data"].append(2)
                else:
                    # Pavimento ha ID 1
                    layer_muri["data"].append(0)  # Nessun muro
                
                # Pavimento è sempre presente
                if self.tipo == "interno":
                    layer_pavimento["data"].append(1)  # Pavimento interno
                elif self.tipo == "esterno":
                    layer_pavimento["data"].append(4)  # Erba o terreno esterno
                else:
                    layer_pavimento["data"].append(5)  # Pavimento sotterraneo
        
        # Ritorna tutti i layer in ordine di rendering (dal più basso al più alto)
        return [layer_pavimento, layer_muri, layer_porte]
    
    def genera_entities_rendering(self, giocatore=None):
        """
        Genera le entità per il rendering grafico della mappa.
        
        Args:
            giocatore: Oggetto giocatore (opzionale)
            
        Returns:
            list: Lista di entità con informazioni per il rendering
        """
        entities = []
        
        # Aggiungi gli oggetti interattivi
        for pos, oggetto in self.oggetti.items():
            if pos in self.porte:
                continue  # Saltiamo le porte che sono già nel layer dedicato
                
            x, y = pos
            entities.append({
                "id": f"oggetto_{oggetto.id if hasattr(oggetto, 'id') else id(oggetto)}",
                "tipo": "oggetto",
                "nome": oggetto.nome if hasattr(oggetto, 'nome') else "Oggetto",
                "x": x,
                "y": y,
                "sprite": oggetto.sprite if hasattr(oggetto, 'sprite') else "default_object",
                "interagibile": True
            })
        
        # Aggiungi gli NPG
        for pos, npg in self.npg.items():
            x, y = pos
            entities.append({
                "id": f"npg_{npg.id if hasattr(npg, 'id') else id(npg)}",
                "tipo": "npg",
                "nome": npg.nome if hasattr(npg, 'nome') else "NPG",
                "x": x,
                "y": y,
                "sprite": npg.sprite if hasattr(npg, 'sprite') else "default_npc",
                "interagibile": True
            })
        
        # Aggiungi il giocatore se presente
        if giocatore:
            entities.append({
                "id": "giocatore",
                "tipo": "giocatore",
                "nome": giocatore.nome,
                "x": giocatore.x,
                "y": giocatore.y,
                "sprite": "player",
                "interagibile": False
            })
        
        return entities
    
    def ottieni_oggetti_vicini(self, x, y, raggio=1):
        """
        Restituisce gli oggetti entro un certo raggio dalla posizione
        
        Args:
            x, y: Coordinate centrali
            raggio: Distanza massima in celle
            
        Returns:
            dict: Dizionario di posizioni e oggetti
        """
        oggetti_vicini = {}
        for dx in range(-raggio, raggio + 1):
            for dy in range(-raggio, raggio + 1):
                pos = (x + dx, y + dy)
                if pos in self.oggetti:
                    oggetti_vicini[pos] = self.oggetti[pos]
        return oggetti_vicini
    
    def ottieni_npg_vicini(self, x, y, raggio=1):
        """
        Restituisce gli NPG entro un certo raggio dalla posizione
        
        Args:
            x, y: Coordinate centrali
            raggio: Distanza massima in celle
            
        Returns:
            dict: Dizionario di posizioni e NPG
        """
        npg_vicini = {}
        for dx in range(-raggio, raggio + 1):
            for dy in range(-raggio, raggio + 1):
                pos = (x + dx, y + dy)
                if pos in self.npg:
                    npg_vicini[pos] = self.npg[pos]
        return npg_vicini
    
    def carica_layout_da_stringa(self, layout_str):
        """
        Carica il layout della mappa da una stringa di caratteri
        # = muro, . = pavimento, P = posizione iniziale giocatore
        
        Args:
            layout_str: Stringa multi-linea che rappresenta la mappa
        """
        righe = layout_str.strip().split('\n')
        for y, riga in enumerate(righe):
            for x, cella in enumerate(riga):
                if cella == '#':
                    self.imposta_muro(x, y)
                elif cella == 'P':
                    self.pos_iniziale_giocatore = (x, y)
    
    def to_dict(self):
        """
        Converte la mappa in un dizionario per la serializzazione.
        
        Returns:
            dict: Rappresentazione della mappa in formato dizionario
        """
        # Converte la griglia in una lista per la serializzazione
        griglia_serializzata = [riga.copy() for riga in self.griglia]
        
        # Serializza oggetti e NPG usando to_dict se disponibile
        oggetti_dict = {}
        for pos, obj in self.oggetti.items():
            if hasattr(obj, 'to_dict'):
                oggetti_dict[str(pos)] = obj.to_dict()
            else:
                oggetti_dict[str(pos)] = {"nome": obj.nome, "token": obj.token}
        
        npg_dict = {}
        for pos, npg in self.npg.items():
            if hasattr(npg, 'to_dict'):
                npg_dict[str(pos)] = npg.to_dict()
            else:
                npg_dict[str(pos)] = {"nome": npg.nome, "token": npg.token}
        
        # Serializza le porte
        porte_dict = {str(pos): list(dest) for pos, dest in self.porte.items()}
        
        return {
            "nome": self.nome,
            "larghezza": self.larghezza,
            "altezza": self.altezza,
            "tipo": self.tipo,
            "descrizione": self.descrizione,
            "griglia": griglia_serializzata,
            "oggetti": oggetti_dict,
            "npg": npg_dict,
            "porte": porte_dict,
            "pos_iniziale_giocatore": self.pos_iniziale_giocatore
        }
        
    @classmethod
    def from_dict(cls, data):
        """
        Crea una nuova istanza di Mappa da un dizionario.
        
        Args:
            data (dict): Dizionario con i dati della mappa
            
        Returns:
            Mappa: Nuova istanza di Mappa
        """
        # Crea una nuova mappa con i parametri di base
        mappa = cls(
            nome=data.get("nome", "mappa_sconosciuta"),
            larghezza=data.get("larghezza", 10),
            altezza=data.get("altezza", 10),
            tipo=data.get("tipo", "interno"),
            descrizione=data.get("descrizione", "")
        )
        
        # Imposta la griglia
        if "griglia" in data:
            mappa.griglia = data["griglia"]
            
        # Carica la posizione iniziale del giocatore
        if "pos_iniziale_giocatore" in data:
            mappa.pos_iniziale_giocatore = data["pos_iniziale_giocatore"]
            
        # Carica oggetti
        # Nota: Le chiavi potrebbero essere stringhe come "[x, y]" o "(x, y)"
        from items.oggetto_interattivo import OggettoInterattivo, Porta
        for key, obj_data in data.get("oggetti", {}).items():
            try:
                # Converti la chiave in coordinate (x, y) se necessario
                if isinstance(key, str):
                    if key.startswith("[") and key.endswith("]"):
                        # Formato [x, y]
                        coord_str = key.strip("[]")
                        x, y = map(int, coord_str.split(","))
                        pos = (x, y)
                    elif key.startswith("(") and key.endswith(")"):
                        # Formato (x, y)
                        coord_str = key.strip("()")
                        x, y = map(int, coord_str.split(","))
                        pos = (x, y)
                    else:
                        # Tenta una valutazione sicura della stringa
                        import ast
                        try:
                            pos_eval = ast.literal_eval(key)
                            # Verifica che sia una coppia di numeri
                            if isinstance(pos_eval, (list, tuple)) and len(pos_eval) == 2:
                                x, y = pos_eval
                                pos = (x, y)
                            else:
                                raise ValueError(f"Formato posizione non valido: {key}")
                        except (ValueError, SyntaxError):
                            print(f"Errore durante il caricamento dell'oggetto in {key}: formato posizione non valido")
                            continue
                elif isinstance(key, (list, tuple)) and len(key) == 2:
                    # Il nostro formato standardizzato (x, y)
                    x, y = key
                    pos = (x, y)
                else:
                    print(f"Errore durante il caricamento dell'oggetto in {key}: tipo di chiave non supportato")
                    continue
                
                # Gestione speciale per le porte
                if isinstance(obj_data, dict) and obj_data.get("tipo") == "porta":
                    porta = Porta(
                        nome=obj_data.get("nome", "Porta"),
                        descrizione=obj_data.get("descrizione", ""),
                        stato=obj_data.get("stato", "chiusa")
                    )
                    mappa.oggetti[pos] = porta
                    
                    # Se c'è informazione sulla destinazione, aggiungi anche alle porte
                    if "mappa_dest" in obj_data and "pos_dest" in obj_data:
                        mappa.porte[pos] = (obj_data["mappa_dest"], obj_data["pos_dest"])
                # Altri oggetti interattivi
                elif isinstance(obj_data, dict):
                    oggetto = OggettoInterattivo(
                        nome=obj_data.get("nome", "Oggetto"),
                        descrizione=obj_data.get("descrizione", ""),
                        stato=obj_data.get("stato", "normale")
                    )
                    # Aggiungi altri attributi se disponibili
                    for attr, value in obj_data.items():
                        if attr not in ["nome", "descrizione", "stato"]:
                            setattr(oggetto, attr, value)
                    mappa.oggetti[pos] = oggetto
                else:
                    print(f"Errore durante il caricamento dell'oggetto in {pos}: dati non validi")
            except Exception as e:
                print(f"Errore durante il caricamento dell'oggetto in {key}: {str(e)}")
                
        # Carica NPG
        for key, npg_data in data.get("npg", {}).items():
            try:
                # Converti la chiave in coordinate (x, y) se necessario
                if isinstance(key, str):
                    if key.startswith("[") and key.endswith("]"):
                        # Formato [x, y]
                        coord_str = key.strip("[]")
                        x, y = map(int, coord_str.split(","))
                        pos = (x, y)
                    elif key.startswith("(") and key.endswith(")"):
                        # Formato (x, y)
                        coord_str = key.strip("()")
                        x, y = map(int, coord_str.split(","))
                        pos = (x, y)
                    else:
                        # Tenta una valutazione sicura della stringa
                        import ast
                        try:
                            pos_eval = ast.literal_eval(key)
                            # Verifica che sia una coppia di numeri
                            if isinstance(pos_eval, (list, tuple)) and len(pos_eval) == 2:
                                x, y = pos_eval
                                pos = (x, y)
                            else:
                                raise ValueError(f"Formato posizione non valido: {key}")
                        except (ValueError, SyntaxError):
                            print(f"Errore durante il caricamento dell'NPG in {key}: formato posizione non valido")
                            continue
                elif isinstance(key, (list, tuple)) and len(key) == 2:
                    # Il nostro formato standardizzato (x, y)
                    x, y = key
                    pos = (x, y)
                else:
                    print(f"Errore durante il caricamento dell'NPG in {key}: tipo di chiave non supportato")
                    continue
                
                # Importa NPG solo se necessario
                from entities.npg import NPG
                
                if isinstance(npg_data, dict):
                    npg = NPG(
                        nome=npg_data.get("nome", "NPC"),
                        token=npg_data.get("token", "N")
                    )
                    # Aggiungi altri attributi se disponibili
                    for attr, value in npg_data.items():
                        if attr not in ["nome", "token"]:
                            setattr(npg, attr, value)
                    mappa.npg[pos] = npg
                else:
                    print(f"Errore durante il caricamento dell'NPG in {pos}: dati non validi")
            except Exception as e:
                print(f"Errore durante il caricamento dell'NPG in {key}: {str(e)}")
                
        # Carica porte (collegamenti tra mappe)
        for key, porta_data in data.get("porte", {}).items():
            try:
                # Converti la chiave in coordinate (x, y) se necessario
                if isinstance(key, str):
                    if key.startswith("[") and key.endswith("]"):
                        # Formato [x, y]
                        coord_str = key.strip("[]")
                        x, y = map(int, coord_str.split(","))
                        pos = (x, y)
                    elif key.startswith("(") and key.endswith(")"):
                        # Formato (x, y)
                        coord_str = key.strip("()")
                        x, y = map(int, coord_str.split(","))
                        pos = (x, y)
                    else:
                        # Tenta una valutazione sicura della stringa
                        import ast
                        try:
                            pos_eval = ast.literal_eval(key)
                            # Verifica che sia una coppia di numeri
                            if isinstance(pos_eval, (list, tuple)) and len(pos_eval) == 2:
                                x, y = pos_eval
                                pos = (x, y)
                            else:
                                raise ValueError(f"Formato posizione non valido: {key}")
                        except (ValueError, SyntaxError):
                            print(f"Errore durante il caricamento della porta in {key}: formato posizione non valido")
                            continue
                elif isinstance(key, (list, tuple)) and len(key) == 2:
                    # Il nostro formato standardizzato (x, y)
                    x, y = key
                    pos = (x, y)
                else:
                    print(f"Errore durante il caricamento della porta in {key}: tipo di chiave non supportato")
                    continue
                
                # Le porte possono essere in formato (mappa_dest, (x_dest, y_dest)) o [mappa_dest, [x_dest, y_dest]]
                # o anche nel formato comune [mappa_dest, x_dest, y_dest]
                if isinstance(porta_data, (list, tuple)):
                    if len(porta_data) == 3:
                        # Formato [mappa_dest, x_dest, y_dest]
                        mappa_dest = porta_data[0]
                        x_dest = porta_data[1]
                        y_dest = porta_data[2]
                        mappa.porte[pos] = (mappa_dest, (x_dest, y_dest))
                    elif len(porta_data) == 2:
                        # Formato (mappa_dest, (x_dest, y_dest)) o [mappa_dest, [x_dest, y_dest]]
                        mappa_dest = porta_data[0]
                        pos_dest = porta_data[1]
                        # Converti pos_dest in tupla se è una lista
                        if isinstance(pos_dest, list):
                            pos_dest = tuple(pos_dest)
                        mappa.porte[pos] = (mappa_dest, pos_dest)
                    else:
                        print(f"Errore durante il caricamento della porta in {pos}: dati destinazione non validi")
                else:
                    print(f"Errore durante il caricamento della porta in {pos}: dati destinazione non validi")
            except Exception as e:
                print(f"Errore durante il caricamento della porta in {key}: {str(e)}")
                
        return mappa

class MappaComponente:
    """
    Classe base per componenti di una mappa che possono essere serializzati e deserializzati.
    Usata per estendere le funzionalità della mappa con componenti modulari.
    """
    def __init__(self, nome, descrizione=""):
        self.nome = nome
        self.descrizione = descrizione
        
    def to_dict(self):
        """Converte il componente in un dizionario per la serializzazione"""
        return {
            "nome": self.nome,
            "descrizione": self.descrizione,
            "tipo": self.__class__.__name__
        }
    
    @classmethod
    def from_dict(cls, data):
        """Crea un'istanza del componente da un dizionario"""
        return cls(
            nome=data.get("nome", "componente_sconosciuto"),
            descrizione=data.get("descrizione", "")
        )
        
class MappaCaricatore:
    """
    Classe responsabile del caricamento e salvataggio di mappe da e verso file.
    """
    def __init__(self, percorso_base=None):
        """
        Inizializza il caricatore di mappe.
        
        Args:
            percorso_base: Percorso base dove cercare i file delle mappe
        """
        self.percorso_base = percorso_base or Path("data/mappe")
        logging.info(f"MappaCaricatore inizializzato con percorso base: {self.percorso_base.absolute()}")
        logging.info(f"Il percorso esiste: {self.percorso_base.exists()}")
        
    def carica_mappa(self, nome_file):
        """
        Carica una mappa da un file JSON.
        
        Args:
            nome_file: Nome del file JSON (senza percorso)
            
        Returns:
            Mappa: L'oggetto mappa caricato
        """
        percorso_completo = self.percorso_base / nome_file
        
        logging.info(f"Tentativo di caricare mappa da: {percorso_completo.absolute()}")
        
        if not percorso_completo.exists():
            logging.error(f"File mappa non trovato: {percorso_completo.absolute()}")
            # Prova un percorso alternativo in caso di problemi con il percorso relativo
            percorso_alternativo = Path(os.path.join(os.getcwd(), "data", "mappe", nome_file))
            logging.info(f"Tentativo con percorso alternativo: {percorso_alternativo}")
            
            if percorso_alternativo.exists():
                logging.info(f"File trovato nel percorso alternativo, utilizzo: {percorso_alternativo}")
                percorso_completo = percorso_alternativo
            else:
                raise FileNotFoundError(f"File mappa non trovato: {percorso_completo.absolute()} né in {percorso_alternativo}")
            
        try:
            with open(percorso_completo, 'r', encoding='utf-8') as f:
                dati_mappa = json.load(f)
                
            mappa = Mappa.from_dict(dati_mappa)
            logging.info(f"Mappa '{mappa.nome}' caricata con successo da {percorso_completo}")
            return mappa
        except Exception as e:
            logging.error(f"Errore nel caricamento della mappa {nome_file}: {e}")
            import traceback
            logging.error(traceback.format_exc())
            raise
            
    def salva_mappa(self, mappa, nome_file=None):
        """
        Salva una mappa su un file JSON.
        
        Args:
            mappa: Oggetto mappa da salvare
            nome_file: Nome del file (se None, usa il nome della mappa)
            
        Returns:
            bool: True se il salvataggio è riuscito
        """
        nome_file = nome_file or f"{mappa.nome}.json"
        percorso_completo = self.percorso_base / nome_file
        
        # Assicurati che la directory esista
        logging.info(f"Tentativo di creare directory: {percorso_completo.parent}")
        percorso_completo.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(percorso_completo, 'w', encoding='utf-8') as f:
                json.dump(mappa.to_dict(), f, indent=2, ensure_ascii=False)
            logging.info(f"Mappa '{mappa.nome}' salvata con successo in {percorso_completo}")
            return True
        except Exception as e:
            logging.error(f"Errore nel salvataggio della mappa {nome_file}: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return False
            
    def elenca_mappe_disponibili(self):
        """
        Elenca tutte le mappe disponibili nella directory.
        
        Returns:
            list: Lista di nomi di file delle mappe disponibili
        """
        if not self.percorso_base.exists():
            logging.warning(f"Directory mappe non trovata: {self.percorso_base.absolute()}")
            # Prova un percorso alternativo
            percorso_alternativo = Path(os.path.join(os.getcwd(), "data", "mappe"))
            logging.info(f"Tentativo con percorso alternativo per elenco: {percorso_alternativo}")
            
            if percorso_alternativo.exists():
                logging.info(f"Utilizzando percorso alternativo per elencare le mappe: {percorso_alternativo}")
                self.percorso_base = percorso_alternativo
            else:
                logging.error(f"Nessuna directory mappe trovata né in {self.percorso_base.absolute()} né in {percorso_alternativo}")
                return []
        
        files = list(self.percorso_base.glob("*.json"))
        result = [f.name for f in files]
        logging.info(f"Mappe disponibili in {self.percorso_base}: {result}")
        return result

# Aggiunta classe GameMap necessaria per server.init.taverna_init
class GameMap:
    """
    Classe per rappresentare una mappa di gioco.
    Compatibile con il sistema di inizializzazione della taverna.
    """
    
    def __init__(self, name, width, height):
        """
        Inizializza una nuova mappa di gioco.
        
        Args:
            name (str): Nome della mappa
            width (int): Larghezza in celle
            height (int): Altezza in celle
        """
        self.name = name
        self.width = width
        self.height = height
        self.pos_iniziale_giocatore = (1, 1)
        
        # Celle della mappa (pavimento, muri, ecc.)
        self.cells = [[{"type": "empty", "walkable": True} for _ in range(width)] for _ in range(height)]
        
        # Entità sulla mappa (NPC, oggetti, ecc.)
        self.entities = []
        
        # Eventi sulle celle
        self.events = {}  # (x, y) -> evento
    
    def set_cell(self, x, y, cell_type):
        """
        Imposta il tipo di una cella.
        
        Args:
            x, y: Coordinate
            cell_type: Tipo di cella (es. "muro", "pavimento")
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            walkable = cell_type != "muro"
            self.cells[y][x] = {"type": cell_type, "walkable": walkable}
    
    def add_entity(self, x, y, entity_type, properties=None):
        """
        Aggiunge un'entità alla mappa.
        
        Args:
            x, y: Coordinate
            entity_type: Tipo di entità (es. "NPC", "Oggetto")
            properties: Proprietà dell'entità (dizionario)
        """
        if properties is None:
            properties = {}
            
        entity = {
            "id": f"{entity_type}_{len(self.entities)}",
            "type": entity_type,
            "x": x,
            "y": y,
            "properties": properties
        }
        self.entities.append(entity)
    
    def add_event(self, x, y, event_type, params=None):
        """
        Aggiunge un evento a una cella.
        
        Args:
            x, y: Coordinate
            event_type: Tipo di evento (es. "exit", "dialogo")
            params: Parametri dell'evento (dizionario)
        """
        if params is None:
            params = {}
            
        self.events[(x, y)] = {
            "tipo": event_type,
            "parametri": params
        }
    
    def get_entities(self):
        """Restituisce tutte le entità sulla mappa"""
        return self.entities
    
    def get_event_at(self, x, y):
        """Restituisce l'evento alla posizione specificata, se presente"""
        return self.events.get((x, y))
    
    def to_dict(self):
        """Converte la mappa in dizionario per serializzazione"""
        return {
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "cells": self.cells,
            "entities": self.entities,
            "events": {f"{x},{y}": event for (x, y), event in self.events.items()},
            "pos_iniziale_giocatore": self.pos_iniziale_giocatore
        }
