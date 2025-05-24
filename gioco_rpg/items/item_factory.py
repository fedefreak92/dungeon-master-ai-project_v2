import json
import os
import logging
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
    def carica_da_file(cls, percorso: str) -> Optional[ItemBase]:
        """
        Carica un oggetto da un file JSON.
        
        Args:
            percorso: Percorso del file da caricare
            
        Returns:
            ItemBase: L'oggetto caricato o None se il file non è valido
        """
        if not os.path.exists(percorso):
            logger.error(f"File non trovato: {percorso}")
            return None
            
        try:
            # Carica il file come JSON
            with open(percorso, 'r', encoding='utf-8') as f:
                dati_json = f.read()
            return cls.crea_da_json(dati_json)
        except Exception as e:
            logger.error(f"Errore nel caricamento del file {percorso}: {e}")
            return None
    
    @classmethod
    def salva_su_file(cls, item: ItemBase, percorso: str) -> bool:
        """
        Salva un oggetto su un file JSON.
        
        Args:
            item: Oggetto da salvare
            percorso: Percorso dove salvare il file
            
        Returns:
            bool: True se il salvataggio è riuscito, False altrimenti
        """
        try:
            # Crea la directory se non esiste
            directory = os.path.dirname(percorso)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
                
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
                
            # Carica solo file JSON
            if not filename.lower().endswith('.json'):
                continue
                
            # Carica l'oggetto
            oggetto = cls.carica_da_file(percorso)
            
            # Verifica se l'oggetto è valido e se corrisponde al tipo richiesto
            if oggetto is not None and (tipo is None or oggetto.tipo.lower() == tipo.lower()):
                oggetti[oggetto.id] = oggetto
                
        return oggetti 