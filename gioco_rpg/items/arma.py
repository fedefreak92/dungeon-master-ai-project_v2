from .item_base import ItemBase
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class Arma(ItemBase):
    def __init__(self, id: str = None, nome: str = "", descrizione: str = "", 
                 valore: int = 0, peso: float = 0.0, immagine: str = "", 
                 quantita: int = 1, proprietà: Dict[str, Any] = None,
                 danno: int = 0, tipo_arma: str = "generica"):
        super().__init__(id, nome, descrizione, valore, "arma", peso, immagine, quantita, proprietà)
        self.danno = danno
        self.tipo_arma = tipo_arma # es. "spada", "ascia", "arco"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "danno": self.danno,
            "tipo_arma": self.tipo_arma
            # Aggiungere altri attributi specifici dell'arma se necessario
        })
        return data

    @classmethod
    def from_dict(cls, dati: Dict[str, Any]) -> 'Arma':
        arma = cls(
            id=dati.get("id"),
            nome=dati.get("nome", "Arma Sconosciuta"),
            descrizione=dati.get("descrizione", ""),
            valore=dati.get("valore", 0),
            peso=dati.get("peso", 0.0),
            immagine=dati.get("immagine", ""),
            quantita=dati.get("quantita", 1),
            proprietà=dati.get("proprietà", {}),
            danno=dati.get("danno", 0),
            tipo_arma=dati.get("tipo_arma", "generica")
        )
        return arma

    def equipaggia(self, entita_bersaglio):
        # Logica specifica per equipaggiare un'arma
        logger.info(f"{entita_bersaglio.nome} equipaggia {self.nome}.")
        # La logica di equipaggiamento più dettagliata è in Entita/Giocatore/NPG
        pass

    def usa(self, entita_bersaglio):
        # Un'arma di solito non si "usa" come una pozione, si equipaggia e si usa per attaccare.
        logger.info(f"Provi ad usare {self.nome}, ma è un'arma. Dovresti equipaggiarla.")
        pass 