from .item_base import ItemBase
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class Armatura(ItemBase):
    def __init__(self, id: str = None, nome: str = "", descrizione: str = "", 
                 valore: int = 0, peso: float = 0.0, immagine: str = "", 
                 quantita: int = 1, proprietà: Dict[str, Any] = None,
                 difesa_bonus: int = 0, tipo_armatura: str = "generica"): # es. "corazza", "cuoio", "stoffa"
        super().__init__(id, nome, descrizione, valore, "armatura", peso, immagine, quantita, proprietà)
        self.difesa_bonus = difesa_bonus
        self.tipo_armatura = tipo_armatura

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "difesa_bonus": self.difesa_bonus,
            "tipo_armatura": self.tipo_armatura
        })
        return data

    @classmethod
    def from_dict(cls, dati: Dict[str, Any]) -> 'Armatura':
        armatura = cls(
            id=dati.get("id"),
            nome=dati.get("nome", "Armatura Sconosciuta"),
            descrizione=dati.get("descrizione", ""),
            valore=dati.get("valore", 0),
            peso=dati.get("peso", 0.0),
            immagine=dati.get("immagine", ""),
            quantita=dati.get("quantita", 1),
            proprietà=dati.get("proprietà", {}),
            difesa_bonus=dati.get("difesa_bonus", 0),
            tipo_armatura=dati.get("tipo_armatura", "generica")
        )
        return armatura

    def equipaggia(self, entita_bersaglio):
        logger.info(f"{entita_bersaglio.nome} equipaggia {self.nome}.")
        # Logica specifica per equipaggiare un'armatura
        # Esempio: entita_bersaglio.difesa += self.difesa_bonus
        pass

    def usa(self, entita_bersaglio):
        logger.info(f"Provi ad usare {self.nome}, ma è un'armatura. Dovresti equipaggiarla.")
        pass 