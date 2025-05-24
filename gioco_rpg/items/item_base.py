import json
import uuid
import logging
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class ItemBase:
    """Classe base per tutti gli oggetti di gioco"""
    
    def __init__(self, id: Optional[str] = None, nome: str = "", descrizione: str = "", 
                 valore: int = 0, tipo: str = "oggetto", peso: float = 0.0,
                 immagine: str = "", quantita: int = 1, proprietà: Optional[Dict[str, Any]] = None):
        """
        Inizializza un oggetto base.
        
        Args:
            id: ID univoco dell'oggetto (generato se non fornito)
            nome: Nome dell'oggetto
            descrizione: Descrizione dell'oggetto
            valore: Valore in monete dell'oggetto
            tipo: Tipo di oggetto
            peso: Peso dell'oggetto in kg
            immagine: Percorso dell'immagine dell'oggetto
            quantita: Quantità dell'oggetto nello stack
            proprietà: Dizionario con proprietà aggiuntive dell'oggetto
        """
        self.id = id if id else str(uuid.uuid4())
        self.nome = nome
        self.descrizione = descrizione
        self.valore = max(0, valore)
        self.tipo = tipo
        self.peso = max(0.0, peso)
        self.immagine = immagine
        self.quantita = max(1, quantita)
        self.proprietà = proprietà or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte l'oggetto in un dizionario.
        
        Returns:
            Dict[str, Any]: Dizionario con i dati dell'oggetto
        """
        return {
            "id": self.id,
            "nome": self.nome,
            "descrizione": self.descrizione,
            "valore": self.valore,
            "tipo": self.tipo,
            "peso": self.peso,
            "immagine": self.immagine,
            "quantita": self.quantita,
            "proprietà": self.proprietà
        }
    
    def to_json(self) -> str:
        """
        Converte l'oggetto in una stringa JSON.
        
        Returns:
            str: Stringa JSON con i dati dell'oggetto
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, dati: Dict[str, Any]) -> 'ItemBase':
        """
        Crea un oggetto da un dizionario.
        
        Args:
            dati: Dizionario con i dati dell'oggetto
            
        Returns:
            ItemBase: Oggetto creato
        """
        return cls(
            id=dati.get("id"),
            nome=dati.get("nome", ""),
            descrizione=dati.get("descrizione", ""),
            valore=dati.get("valore", 0),
            tipo=dati.get("tipo", "oggetto"),
            peso=dati.get("peso", 0.0),
            immagine=dati.get("immagine", ""),
            quantita=dati.get("quantita", 1),
            proprietà=dati.get("proprietà", {})
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> Optional['ItemBase']:
        """
        Crea un oggetto da una stringa JSON.
        
        Args:
            json_str: Stringa JSON con i dati dell'oggetto
            
        Returns:
            ItemBase: Oggetto creato o None se il formato non è valido
        """
        try:
            dati = json.loads(json_str)
            return cls.from_dict(dati)
        except json.JSONDecodeError as e:
            logger.error(f"Errore nella decodifica JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Errore inaspettato nella creazione da JSON: {e}")
            return None
    
    def copia(self) -> 'ItemBase':
        """
        Crea una copia dell'oggetto.
        
        Returns:
            ItemBase: Copia dell'oggetto
        """
        return self.__class__.from_dict(self.to_dict())
    
    def aggiungi_quantita(self, quantita: int) -> bool:
        """
        Aggiunge una quantità all'oggetto.
        
        Args:
            quantita: Quantità da aggiungere
            
        Returns:
            bool: True se l'aggiunta è riuscita, False altrimenti
        """
        if quantita <= 0:
            return False
            
        self.quantita += quantita
        return True
    
    def rimuovi_quantita(self, quantita: int) -> bool:
        """
        Rimuove una quantità dall'oggetto.
        
        Args:
            quantita: Quantità da rimuovere
            
        Returns:
            bool: True se la rimozione è riuscita, False altrimenti
        """
        if quantita <= 0 or quantita > self.quantita:
            return False
            
        self.quantita -= quantita
        return True
    
    def è_impilabile_con(self, altro: 'ItemBase') -> bool:
        """
        Verifica se l'oggetto è impilabile con un altro.
        
        Args:
            altro: Altro oggetto
            
        Returns:
            bool: True se gli oggetti sono impilabili, False altrimenti
        """
        # Gli oggetti sono impilabili se hanno lo stesso nome e tipo
        return (self.nome == altro.nome and 
                self.tipo == altro.tipo and
                self.id != altro.id)  # Non impilare lo stesso oggetto con se stesso
    
    def impila_con(self, altro: 'ItemBase') -> bool:
        """
        Impila l'oggetto con un altro.
        
        Args:
            altro: Altro oggetto
            
        Returns:
            bool: True se l'impilamento è riuscito, False altrimenti
        """
        if not self.è_impilabile_con(altro):
            return False
            
        self.quantita += altro.quantita
        return True
    
    def separa(self, quantita: int) -> Optional['ItemBase']:
        """
        Separa una quantità dall'oggetto.
        
        Args:
            quantita: Quantità da separare
            
        Returns:
            ItemBase: Nuovo oggetto con la quantità separata o None se la separazione non è riuscita
        """
        if quantita <= 0 or quantita >= self.quantita:
            return None
            
        # Crea una copia dell'oggetto
        nuovo = self.copia()
        
        # Imposta la quantità del nuovo oggetto
        nuovo.quantita = quantita
        
        # Rimuovi la quantità dall'oggetto originale
        self.quantita -= quantita
        
        # Genera un nuovo ID per l'oggetto separato
        nuovo.id = str(uuid.uuid4())
        
        return nuovo
    
    def __str__(self) -> str:
        """Rappresentazione testuale dell'oggetto"""
        return f"{self.nome} (x{self.quantita})"
    
    def __repr__(self) -> str:
        """Rappresentazione per debugging"""
        return f"{self.__class__.__name__}(id='{self.id}', nome='{self.nome}', quantita={self.quantita})"
    
    def __eq__(self, altro: object) -> bool:
        """
        Verifica se due oggetti sono uguali.
        
        Args:
            altro: Altro oggetto
            
        Returns:
            bool: True se gli oggetti sono uguali, False altrimenti
        """
        if not isinstance(altro, ItemBase):
            return False
            
        return self.id == altro.id
    
    def __hash__(self) -> int:
        """
        Calcola l'hash dell'oggetto.
        
        Returns:
            int: Hash dell'oggetto
        """
        return hash(self.id) 