import json
import os
import logging
import msgpack
from typing import Dict, List, Any, Optional, Type, Union

from items.oggetto import Oggetto
from items.arma import Arma
from items.armatura import Armatura
from items.pozione import Pozione
from items.item_base import ItemBase
from items.accessorio import Accessorio

logger = logging.getLogger(__name__)

class ItemFactory:
    """Factory per la creazione di oggetti in base al tipo"""
    
    ITEM_CLASSES = {
        "oggetto": Oggetto,
        "arma": Arma,
        "armatura": Armatura,
        "pozione": Pozione,
        "accessorio": Accessorio
    }
    
    @classmethod
    def crea_da_dict(cls, dati: Dict[str, Any]) -> Optional[ItemBase]:
        """
        Crea un oggetto dalle specifiche nel dizionario.
        
        Args:
            dati: Dizionario con i dati dell'oggetto
            
        Returns:
            ItemBase: L'oggetto creato o None se il tipo non è supportato
        """
        tipo = dati.get('tipo', 'oggetto').lower()
        
        # Ottieni la classe corretta in base al tipo
        item_class = cls.ITEM_CLASSES.get(tipo)
        
        if not item_class:
            logger.warning(f"Tipo di item non supportato: {tipo}")
            return None
            
        # Crea l'oggetto usando il metodo from_dict della classe
        try:
            return item_class.from_dict(dati)
        except Exception as e:
            logger.error(f"Errore nella creazione dell'oggetto: {e}")
            return None
    
    @classmethod
    def crea_da_json(cls, json_dati: str) -> Optional[ItemBase]:
        """
        Crea un oggetto dai dati JSON.
        
        Args:
            json_dati: Stringa JSON con i dati dell'oggetto
            
        Returns:
            ItemBase: L'oggetto creato o None se il formato non è valido
        """
        try:
            dati = json.loads(json_dati)
            return cls.crea_da_dict(dati)
        except json.JSONDecodeError as e:
            logger.error(f"Errore nella decodifica JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Errore inaspettato nella creazione da JSON: {e}")
            return None
    
    @classmethod
    def crea_da_msgpack(cls, msgpack_dati: bytes) -> Optional[ItemBase]:
        """
        Crea un oggetto dai dati MessagePack.
        
        Args:
            msgpack_dati: Dati binari MessagePack con i dati dell'oggetto
            
        Returns:
            ItemBase: L'oggetto creato o None se il formato non è valido
        """
        try:
            dati = msgpack.unpackb(msgpack_dati, raw=False)
            return cls.crea_da_dict(dati)
        except Exception as e:
            logger.error(f"Errore nella decodifica MessagePack: {e}")
            try:
                # Fallback a JSON se MessagePack fallisce
                dati = json.loads(msgpack_dati.decode())
                return cls.crea_da_dict(dati)
            except Exception as e2:
                logger.error(f"Fallback JSON fallito: {e2}")
                return None
    
    @classmethod
    def carica_da_file(cls, percorso: str) -> Optional[ItemBase]:
        """
        Carica un oggetto da un file.
        
        Args:
            percorso: Percorso del file da caricare
            
        Returns:
            ItemBase: L'oggetto caricato o None se il file non è valido
        """
        if not os.path.exists(percorso):
            logger.error(f"File non trovato: {percorso}")
            return None
            
        try:
            # Determina il formato in base all'estensione
            ext = os.path.splitext(percorso)[1].lower()
            
            if ext == '.msgpack':
                with open(percorso, 'rb') as f:
                    dati_binari = f.read()
                return cls.crea_da_msgpack(dati_binari)
            else:  # Assume JSON per default o esplicitamente .json
                with open(percorso, 'r', encoding='utf-8') as f:
                    dati_json = f.read()
                return cls.crea_da_json(dati_json)
        except Exception as e:
            logger.error(f"Errore nel caricamento del file {percorso}: {e}")
            return None
    
    @classmethod
    def salva_su_file(cls, item: ItemBase, percorso: str, formato: str = 'json') -> bool:
        """
        Salva un oggetto su un file.
        
        Args:
            item: Oggetto da salvare
            percorso: Percorso dove salvare il file
            formato: Formato del file ('json' o 'msgpack')
            
        Returns:
            bool: True se il salvataggio è riuscito, False altrimenti
        """
        try:
            # Crea la directory se non esiste
            directory = os.path.dirname(percorso)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
                
            # Salva nel formato richiesto
            if formato.lower() == 'msgpack':
                # Assicurati che l'estensione sia corretta
                if not percorso.lower().endswith('.msgpack'):
                    percorso += '.msgpack'
                    
                # Serializza e salva
                with open(percorso, 'wb') as f:
                    dati_dict = item.to_dict()
                    dati_msgpack = msgpack.packb(dati_dict, use_bin_type=True)
                    f.write(dati_msgpack)
            else:  # Default: JSON
                # Assicurati che l'estensione sia corretta
                if not percorso.lower().endswith('.json'):
                    percorso += '.json'
                    
                # Serializza e salva
                with open(percorso, 'w', encoding='utf-8') as f:
                    dati_dict = item.to_dict()
                    json.dump(dati_dict, f, indent=2, ensure_ascii=False)
                    
            return True
        except Exception as e:
            logger.error(f"Errore nel salvataggio dell'oggetto: {e}")
            return False
    
    @classmethod
    def carica_da_directory(cls, directory: str, tipo: Optional[str] = None) -> Dict[str, ItemBase]:
        """
        Carica tutti gli oggetti da una directory.
        
        Args:
            directory: Directory da cui caricare gli oggetti
            tipo: Tipo di oggetti da caricare (opzionale)
            
        Returns:
            Dict[str, ItemBase]: Dizionario di oggetti, con ID come chiave
        """
        if not os.path.exists(directory) or not os.path.isdir(directory):
            logger.error(f"Directory non valida: {directory}")
            return {}
            
        oggetti = {}
        
        for filename in os.listdir(directory):
            percorso = os.path.join(directory, filename)
            
            # Salta le directory
            if os.path.isdir(percorso):
                continue
                
            # Salta i file che non sono JSON o MessagePack
            ext = os.path.splitext(filename)[1].lower()
            if ext not in ['.json', '.msgpack']:
                continue
                
            # Carica l'oggetto
            oggetto = cls.carica_da_file(percorso)
            
            # Verifica se l'oggetto è valido e se corrisponde al tipo richiesto
            if oggetto is not None and (tipo is None or oggetto.tipo.lower() == tipo.lower()):
                oggetti[oggetto.id] = oggetto
                
        return oggetti
    
    @classmethod
    def converti_formato(cls, percorso_input: str, percorso_output: str, formato_output: str = 'msgpack') -> bool:
        """
        Converte un file da un formato all'altro.
        
        Args:
            percorso_input: Percorso del file di input
            percorso_output: Percorso del file di output
            formato_output: Formato di output ('json' o 'msgpack')
            
        Returns:
            bool: True se la conversione è riuscita, False altrimenti
        """
        # Carica l'oggetto
        oggetto = cls.carica_da_file(percorso_input)
        
        if oggetto is None:
            return False
            
        # Salva l'oggetto nel nuovo formato
        return cls.salva_su_file(oggetto, percorso_output, formato_output)
    
    @classmethod
    def converti_directory(cls, dir_input: str, dir_output: str, formato_output: str = 'msgpack') -> Dict[str, bool]:
        """
        Converte tutti i file in una directory da un formato all'altro.
        
        Args:
            dir_input: Directory di input
            dir_output: Directory di output
            formato_output: Formato di output ('json' o 'msgpack')
            
        Returns:
            Dict[str, bool]: Dizionario con i risultati delle conversioni
        """
        if not os.path.exists(dir_input) or not os.path.isdir(dir_input):
            logger.error(f"Directory di input non valida: {dir_input}")
            return {}
            
        # Crea la directory di output se non esiste
        if not os.path.exists(dir_output):
            os.makedirs(dir_output)
            
        risultati = {}
        
        for filename in os.listdir(dir_input):
            percorso_input = os.path.join(dir_input, filename)
            
            # Salta le directory
            if os.path.isdir(percorso_input):
                continue
                
            # Salta i file che non sono JSON o MessagePack
            ext = os.path.splitext(filename)[1].lower()
            if ext not in ['.json', '.msgpack']:
                continue
                
            # Determina il nome del file di output
            nome_base = os.path.splitext(filename)[0]
            estensione = '.msgpack' if formato_output.lower() == 'msgpack' else '.json'
            percorso_output = os.path.join(dir_output, nome_base + estensione)
            
            # Converti il file
            risultato = cls.converti_formato(percorso_input, percorso_output, formato_output)
            risultati[filename] = risultato
            
        return risultati 