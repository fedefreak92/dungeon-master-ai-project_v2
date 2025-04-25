import os
import json
import shutil
import logging
import msgpack
from typing import Dict, Any, List, Optional, Union, Tuple, TypeVar, Type, cast
from pathlib import Path

# Configurazione del logging
logger = logging.getLogger(__name__)

# Tipo generico per le classi deserializzabili
T = TypeVar('T')

class DataManager:
    """
    Gestore centralizzato per caricare e salvare i dati del gioco.
    Supporta sia il formato JSON che MessagePack.
    """
    
    def __init__(self, data_dir: str = "data", usa_msgpack: bool = True):
        """
        Inizializza il gestore dati.
        
        Args:
            data_dir: Directory principale dei dati
            usa_msgpack: Se True, usa MessagePack come formato predefinito
        """
        self.data_dir = data_dir
        self.usa_msgpack = usa_msgpack
        self._crea_directory_se_necessario(data_dir)
        logger.info(f"DataManager inizializzato con directory {data_dir}")
        logger.info(f"Formato dati predefinito: {'MessagePack' if usa_msgpack else 'JSON'}")
    
    def _crea_directory_se_necessario(self, percorso: str) -> None:
        """
        Crea una directory se non esiste.
        
        Args:
            percorso: Percorso della directory
        """
        if not os.path.exists(percorso):
            os.makedirs(percorso)
            logger.info(f"Creata directory {percorso}")
    
    def _percorso_completo(self, categoria: str, nome_file: str, estensione: Optional[str] = None) -> str:
        """
        Costruisce il percorso completo di un file.
        
        Args:
            categoria: Categoria dei dati (es. "mappe", "npc", "items")
            nome_file: Nome del file
            estensione: Estensione del file (.json o .msgpack)
            
        Returns:
            str: Percorso completo del file
        """
        # Se l'estensione non è specificata, usa quella predefinita
        if estensione is None:
            estensione = ".msgpack" if self.usa_msgpack else ".json"
        
        # Assicurati che l'estensione inizi con un punto
        if not estensione.startswith("."):
            estensione = f".{estensione}"
        
        # Costruisci il percorso
        categoria_dir = os.path.join(self.data_dir, categoria)
        self._crea_directory_se_necessario(categoria_dir)
        
        # Se il nome del file ha già l'estensione, non aggiungerla
        if nome_file.endswith(estensione):
            return os.path.join(categoria_dir, nome_file)
        else:
            return os.path.join(categoria_dir, f"{nome_file}{estensione}")
    
    def salva_json(self, categoria: str, nome_file: str, dati: Dict[str, Any]) -> bool:
        """
        Salva i dati in formato JSON.
        
        Args:
            categoria: Categoria dei dati
            nome_file: Nome del file
            dati: Dati da salvare
            
        Returns:
            bool: True se il salvataggio è riuscito, False altrimenti
        """
        try:
            percorso = self._percorso_completo(categoria, nome_file, ".json")
            with open(percorso, 'w', encoding='utf-8') as f:
                json.dump(dati, f, ensure_ascii=False, indent=2)
            logger.debug(f"Dati salvati in {percorso}")
            return True
        except Exception as e:
            logger.error(f"Errore nel salvataggio JSON in {nome_file}: {e}")
            return False
    
    def salva_msgpack(self, categoria: str, nome_file: str, dati: Dict[str, Any]) -> bool:
        """
        Salva i dati in formato MessagePack.
        
        Args:
            categoria: Categoria dei dati
            nome_file: Nome del file
            dati: Dati da salvare
            
        Returns:
            bool: True se il salvataggio è riuscito, False altrimenti
        """
        try:
            percorso = self._percorso_completo(categoria, nome_file, ".msgpack")
            with open(percorso, 'wb') as f:
                msgpack.pack(dati, f, use_bin_type=True)
            logger.debug(f"Dati salvati in formato MessagePack in {percorso}")
            return True
        except Exception as e:
            logger.error(f"Errore nel salvataggio MessagePack in {nome_file}: {e}")
            return False
    
    def salva(self, categoria: str, nome_file: str, dati: Dict[str, Any]) -> bool:
        """
        Salva i dati nel formato predefinito (JSON o MessagePack).
        
        Args:
            categoria: Categoria dei dati
            nome_file: Nome del file
            dati: Dati da salvare
            
        Returns:
            bool: True se il salvataggio è riuscito, False altrimenti
        """
        if self.usa_msgpack:
            return self.salva_msgpack(categoria, nome_file, dati)
        else:
            return self.salva_json(categoria, nome_file, dati)
    
    def carica_json(self, categoria: str, nome_file: str) -> Optional[Dict[str, Any]]:
        """
        Carica i dati da un file JSON.
        
        Args:
            categoria: Categoria dei dati
            nome_file: Nome del file
            
        Returns:
            Optional[Dict[str, Any]]: Dati caricati o None se il caricamento fallisce
        """
        try:
            percorso = self._percorso_completo(categoria, nome_file, ".json")
            with open(percorso, 'r', encoding='utf-8') as f:
                dati = json.load(f)
            logger.debug(f"Dati caricati da {percorso}")
            return dati
        except FileNotFoundError:
            logger.warning(f"File non trovato: {nome_file}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Errore di decodifica JSON in {nome_file}: {e}")
            return None
        except Exception as e:
            logger.error(f"Errore nel caricamento JSON da {nome_file}: {e}")
            return None
    
    def carica_msgpack(self, categoria: str, nome_file: str) -> Optional[Dict[str, Any]]:
        """
        Carica i dati da un file MessagePack.
        
        Args:
            categoria: Categoria dei dati
            nome_file: Nome del file
            
        Returns:
            Optional[Dict[str, Any]]: Dati caricati o None se il caricamento fallisce
        """
        try:
            percorso = self._percorso_completo(categoria, nome_file, ".msgpack")
            with open(percorso, 'rb') as f:
                dati = msgpack.unpack(f, raw=False)
            logger.debug(f"Dati caricati da MessagePack {percorso}")
            return dati
        except FileNotFoundError:
            logger.warning(f"File MessagePack non trovato: {nome_file}")
            return None
        except Exception as e:
            logger.error(f"Errore nel caricamento MessagePack da {nome_file}: {e}")
            return None
    
    def carica(self, categoria: str, nome_file: str) -> Optional[Dict[str, Any]]:
        """
        Carica i dati dal formato predefinito, con fallback all'altro formato.
        
        Args:
            categoria: Categoria dei dati
            nome_file: Nome del file
            
        Returns:
            Optional[Dict[str, Any]]: Dati caricati o None se il caricamento fallisce
        """
        # Rimuovi l'estensione dal nome del file se presente
        nome_base = nome_file.rsplit('.', 1)[0] if '.' in nome_file else nome_file
        
        # Prova prima con il formato predefinito
        if self.usa_msgpack:
            dati = self.carica_msgpack(categoria, nome_base)
            if dati is not None:
                return dati
            
            # Fallback su JSON
            logger.info(f"Fallback su JSON per {nome_base}")
            return self.carica_json(categoria, nome_base)
        else:
            dati = self.carica_json(categoria, nome_base)
            if dati is not None:
                return dati
            
            # Fallback su MessagePack
            logger.info(f"Fallback su MessagePack per {nome_base}")
            return self.carica_msgpack(categoria, nome_base)
    
    def carica_oggetto(self, categoria: str, nome_file: str, 
                      classe: Type[T], metodo_creazione: str = "from_dict") -> Optional[T]:
        """
        Carica i dati e li converte in un oggetto usando il metodo specificato.
        
        Args:
            categoria: Categoria dei dati
            nome_file: Nome del file
            classe: Classe dell'oggetto da creare
            metodo_creazione: Nome del metodo di classe da chiamare
            
        Returns:
            Optional[T]: Oggetto creato o None se il caricamento fallisce
        """
        dati = self.carica(categoria, nome_file)
        if dati is None:
            return None
            
        try:
            # Ottieni il metodo dalla classe
            creatore = getattr(classe, metodo_creazione)
            # Crea l'oggetto
            return creatore(dati)
        except AttributeError:
            logger.error(f"La classe {classe.__name__} non ha un metodo {metodo_creazione}")
            return None
        except Exception as e:
            logger.error(f"Errore nella creazione dell'oggetto da {nome_file}: {e}")
            return None
    
    def salva_oggetto(self, categoria: str, nome_file: str, 
                     oggetto: Any, metodo_conversione: str = "to_dict") -> bool:
        """
        Salva un oggetto convertendolo con il metodo specificato.
        
        Args:
            categoria: Categoria dei dati
            nome_file: Nome del file
            oggetto: Oggetto da salvare
            metodo_conversione: Nome del metodo dell'oggetto da chiamare
            
        Returns:
            bool: True se il salvataggio è riuscito, False altrimenti
        """
        try:
            # Ottieni il metodo dall'oggetto
            convertitore = getattr(oggetto, metodo_conversione)
            # Converti l'oggetto
            dati = convertitore()
            # Salva i dati
            return self.salva(categoria, nome_file, dati)
        except AttributeError:
            logger.error(f"L'oggetto non ha un metodo {metodo_conversione}")
            return False
        except Exception as e:
            logger.error(f"Errore nel salvataggio dell'oggetto in {nome_file}: {e}")
            return False
    
    def elenca_file(self, categoria: str, estensione: Optional[str] = None) -> List[str]:
        """
        Elenca i file in una categoria.
        
        Args:
            categoria: Categoria dei dati
            estensione: Estensione dei file da elencare (.json o .msgpack)
            
        Returns:
            List[str]: Lista dei nomi dei file senza estensione
        """
        # Se l'estensione non è specificata, usa entrambe
        estensioni = [estensione] if estensione else ['.json', '.msgpack'] if self.usa_msgpack else ['.json']
        
        # Assicurati che le estensioni inizino con un punto
        estensioni = [f".{e}" if not e.startswith(".") else e for e in estensioni]
        
        # Percorso della categoria
        categoria_dir = os.path.join(self.data_dir, categoria)
        
        # Se la directory non esiste, restituisci una lista vuota
        if not os.path.exists(categoria_dir):
            return []
        
        # Elenco dei file che hanno una delle estensioni specificate
        nomi_file = set()
        for e in estensioni:
            for nome in os.listdir(categoria_dir):
                if nome.endswith(e):
                    # Aggiungi il nome del file senza estensione
                    nomi_file.add(nome[:-len(e)])
        
        # Converti il set in una lista ordinata
        return sorted(list(nomi_file))
    
    def carica_tutti(self, categoria: str, classe: Optional[Type[T]] = None, 
                    metodo_creazione: str = "from_dict") -> Dict[str, Union[Dict[str, Any], T]]:
        """
        Carica tutti i file in una categoria, opzionalmente convertendoli in oggetti.
        
        Args:
            categoria: Categoria dei dati
            classe: Classe degli oggetti da creare (opzionale)
            metodo_creazione: Nome del metodo di classe da chiamare
            
        Returns:
            Dict[str, Union[Dict[str, Any], T]]: Dizionario con nome -> dati/oggetto
        """
        # Elenco dei file nella categoria
        nomi_file = self.elenca_file(categoria)
        
        # Dizionario dei dati/oggetti
        risultato = {}
        
        # Carica ogni file
        for nome in nomi_file:
            if classe is None:
                # Carica i dati grezzi
                dati = self.carica(categoria, nome)
                if dati is not None:
                    risultato[nome] = dati
            else:
                # Carica e converti in oggetto
                oggetto = self.carica_oggetto(categoria, nome, classe, metodo_creazione)
                if oggetto is not None:
                    risultato[nome] = oggetto
        
        return risultato
    
    def esiste_file(self, categoria: str, nome_file: str) -> bool:
        """
        Verifica se un file esiste.
        
        Args:
            categoria: Categoria dei dati
            nome_file: Nome del file
            
        Returns:
            bool: True se il file esiste, False altrimenti
        """
        # Rimuovi l'estensione dal nome del file se presente
        nome_base = nome_file.rsplit('.', 1)[0] if '.' in nome_file else nome_file
        
        # Controlla se esiste con estensione JSON
        percorso_json = self._percorso_completo(categoria, nome_base, ".json")
        percorso_msgpack = self._percorso_completo(categoria, nome_base, ".msgpack")
        
        return os.path.exists(percorso_json) or os.path.exists(percorso_msgpack)
    
    def elimina_file(self, categoria: str, nome_file: str) -> bool:
        """
        Elimina un file.
        
        Args:
            categoria: Categoria dei dati
            nome_file: Nome del file
            
        Returns:
            bool: True se l'eliminazione è riuscita, False altrimenti
        """
        # Rimuovi l'estensione dal nome del file se presente
        nome_base = nome_file.rsplit('.', 1)[0] if '.' in nome_file else nome_file
        
        successo = False
        
        # Elimina il file JSON se esiste
        percorso_json = self._percorso_completo(categoria, nome_base, ".json")
        if os.path.exists(percorso_json):
            try:
                os.remove(percorso_json)
                logger.debug(f"File eliminato: {percorso_json}")
                successo = True
            except Exception as e:
                logger.error(f"Errore nell'eliminazione di {percorso_json}: {e}")
        
        # Elimina il file MessagePack se esiste
        percorso_msgpack = self._percorso_completo(categoria, nome_base, ".msgpack")
        if os.path.exists(percorso_msgpack):
            try:
                os.remove(percorso_msgpack)
                logger.debug(f"File eliminato: {percorso_msgpack}")
                successo = True
            except Exception as e:
                logger.error(f"Errore nell'eliminazione di {percorso_msgpack}: {e}")
        
        return successo
    
    def copia_file(self, categoria_src: str, nome_file_src: str, 
                  categoria_dest: str, nome_file_dest: str) -> bool:
        """
        Copia un file.
        
        Args:
            categoria_src: Categoria di origine
            nome_file_src: Nome del file di origine
            categoria_dest: Categoria di destinazione
            nome_file_dest: Nome del file di destinazione
            
        Returns:
            bool: True se la copia è riuscita, False altrimenti
        """
        # Rimuovi l'estensione dai nomi dei file se presenti
        nome_base_src = nome_file_src.rsplit('.', 1)[0] if '.' in nome_file_src else nome_file_src
        nome_base_dest = nome_file_dest.rsplit('.', 1)[0] if '.' in nome_file_dest else nome_file_dest
        
        # Controlla se il file di origine esiste
        if not self.esiste_file(categoria_src, nome_base_src):
            logger.warning(f"File di origine non trovato: {nome_base_src}")
            return False
        
        # Carica i dati dal file di origine
        dati = self.carica(categoria_src, nome_base_src)
        if dati is None:
            return False
        
        # Salva i dati nel file di destinazione
        return self.salva(categoria_dest, nome_base_dest, dati)
    
    def rinomina_file(self, categoria: str, nome_vecchio: str, nome_nuovo: str) -> bool:
        """
        Rinomina un file.
        
        Args:
            categoria: Categoria dei dati
            nome_vecchio: Nome vecchio del file
            nome_nuovo: Nome nuovo del file
            
        Returns:
            bool: True se la rinomina è riuscita, False altrimenti
        """
        # Copia il file con il nuovo nome
        if not self.copia_file(categoria, nome_vecchio, categoria, nome_nuovo):
            return False
        
        # Elimina il file vecchio
        return self.elimina_file(categoria, nome_vecchio)
    
    def crea_backup(self, categoria: str, nome_file: str) -> bool:
        """
        Crea un backup di un file.
        
        Args:
            categoria: Categoria dei dati
            nome_file: Nome del file
            
        Returns:
            bool: True se il backup è riuscito, False altrimenti
        """
        # Rimuovi l'estensione dal nome del file se presente
        nome_base = nome_file.rsplit('.', 1)[0] if '.' in nome_file else nome_file
        
        # Nome del file di backup
        nome_backup = f"{nome_base}_backup"
        
        # Crea il backup
        return self.copia_file(categoria, nome_base, categoria, nome_backup)
    
    def backup_directory(self, categoria: str, dir_backup: str) -> bool:
        """
        Crea un backup di una categoria in una directory.
        
        Args:
            categoria: Categoria dei dati
            dir_backup: Directory di backup
            
        Returns:
            bool: True se il backup è riuscito, False altrimenti
        """
        # Percorso della categoria
        categoria_dir = os.path.join(self.data_dir, categoria)
        
        # Se la directory non esiste, restituisci False
        if not os.path.exists(categoria_dir):
            logger.warning(f"Directory non trovata: {categoria_dir}")
            return False
        
        try:
            # Crea la directory di backup se non esiste
            if not os.path.exists(dir_backup):
                os.makedirs(dir_backup)
            
            # Copia tutti i file dalla categoria alla directory di backup
            for nome_file in os.listdir(categoria_dir):
                src = os.path.join(categoria_dir, nome_file)
                dest = os.path.join(dir_backup, nome_file)
                
                if os.path.isfile(src):
                    shutil.copy2(src, dest)
            
            logger.info(f"Backup completato da {categoria_dir} a {dir_backup}")
            return True
        except Exception as e:
            logger.error(f"Errore nel backup di {categoria_dir}: {e}")
            return False
    
    def converti_json_a_msgpack(self, categoria: str, nome_file: str) -> bool:
        """
        Converte un file JSON in MessagePack.
        
        Args:
            categoria: Categoria dei dati
            nome_file: Nome del file
            
        Returns:
            bool: True se la conversione è riuscita, False altrimenti
        """
        # Rimuovi l'estensione dal nome del file se presente
        nome_base = nome_file.rsplit('.', 1)[0] if '.' in nome_file else nome_file
        
        # Carica i dati dal file JSON
        dati = self.carica_json(categoria, nome_base)
        if dati is None:
            return False
        
        # Salva i dati in formato MessagePack
        return self.salva_msgpack(categoria, nome_base, dati)
    
    def converti_msgpack_a_json(self, categoria: str, nome_file: str) -> bool:
        """
        Converte un file MessagePack in JSON.
        
        Args:
            categoria: Categoria dei dati
            nome_file: Nome del file
            
        Returns:
            bool: True se la conversione è riuscita, False altrimenti
        """
        # Rimuovi l'estensione dal nome del file se presente
        nome_base = nome_file.rsplit('.', 1)[0] if '.' in nome_file else nome_file
        
        # Carica i dati dal file MessagePack
        dati = self.carica_msgpack(categoria, nome_base)
        if dati is None:
            return False
        
        # Salva i dati in formato JSON
        return self.salva_json(categoria, nome_base, dati)
    
    def converti_directory(self, categoria: str, da_json_a_msgpack: bool = True) -> Tuple[int, int]:
        """
        Converte tutti i file in una categoria tra JSON e MessagePack.
        
        Args:
            categoria: Categoria dei dati
            da_json_a_msgpack: Se True, converte da JSON a MessagePack; altrimenti, il contrario
            
        Returns:
            Tuple[int, int]: (numero di file convertiti con successo, numero totale di file)
        """
        # Estensione di origine e destinazione
        estensione_src = ".json" if da_json_a_msgpack else ".msgpack"
        
        # Percorso della categoria
        categoria_dir = os.path.join(self.data_dir, categoria)
        
        # Se la directory non esiste, restituisci (0, 0)
        if not os.path.exists(categoria_dir):
            return (0, 0)
        
        # Elenco dei file con l'estensione di origine
        file_da_convertire = [
            nome for nome in os.listdir(categoria_dir)
            if nome.endswith(estensione_src)
        ]
        
        successi = 0
        
        # Converti ogni file
        for nome_file in file_da_convertire:
            # Rimuovi l'estensione
            nome_base = nome_file[:-len(estensione_src)]
            
            # Converti il file
            if da_json_a_msgpack:
                if self.converti_json_a_msgpack(categoria, nome_base):
                    successi += 1
            else:
                if self.converti_msgpack_a_json(categoria, nome_base):
                    successi += 1
        
        return (successi, len(file_da_convertire))
    
    def cambia_formato_predefinito(self, usa_msgpack: bool) -> None:
        """
        Cambia il formato predefinito per il salvataggio e caricamento dei dati.
        
        Args:
            usa_msgpack: Se True, usa MessagePack; altrimenti, usa JSON
        """
        self.usa_msgpack = usa_msgpack
        logger.info(f"Formato dati predefinito cambiato a {'MessagePack' if usa_msgpack else 'JSON'}")
    
    def get_formato_predefinito(self) -> str:
        """
        Restituisce il formato predefinito.
        
        Returns:
            str: "msgpack" o "json"
        """
        return "msgpack" if self.usa_msgpack else "json" 