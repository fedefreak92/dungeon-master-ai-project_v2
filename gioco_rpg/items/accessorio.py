from .item_base import ItemBase
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class Accessorio(ItemBase):
    def __init__(self, id: str = None, nome: str = "", descrizione: str = "", 
                 valore: int = 0, peso: float = 0.0, immagine: str = "", 
                 quantita: int = 1, proprietà: Dict[str, Any] = None,
                 slot_equip: str = "generico", # es. "anello", "collana", "mantello"
                 effetti_bonus: Dict[str, Any] = None): # es. {"forza": 1, "resistenza_fuoco": 5}
        super().__init__(id, nome, descrizione, valore, "accessorio", peso, immagine, quantita, proprietà)
        self.slot_equip = slot_equip
        self.effetti_bonus = effetti_bonus if effetti_bonus is not None else {}

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "slot_equip": self.slot_equip,
            "effetti_bonus": self.effetti_bonus
        })
        return data

    @classmethod
    def from_dict(cls, dati: Dict[str, Any]) -> 'Accessorio':
        accessorio = cls(
            id=dati.get("id"),
            nome=dati.get("nome", "Accessorio Sconosciuto"),
            descrizione=dati.get("descrizione", "Un accessorio misterioso."),
            valore=dati.get("valore", 0),
            peso=dati.get("peso", 0.0),
            immagine=dati.get("immagine", ""),
            quantita=dati.get("quantita", 1),
            proprietà=dati.get("proprietà", {}),
            slot_equip=dati.get("slot_equip", "generico"),
            effetti_bonus=dati.get("effetti_bonus", {})
        )
        return accessorio

    def equipaggia(self, entita_bersaglio, gioco=None):
        # Logica base per equipaggiare
        # In una implementazione reale, si controllerebbe se lo slot è libero
        # e si applicherebbero gli effetti_bonus all'entita_bersaglio
        logger.info(f"{entita_bersaglio.nome} equipaggia {self.nome} nello slot {self.slot_equip}.")
        if hasattr(entita_bersaglio, 'equipaggiamento') and hasattr(entita_bersaglio.equipaggiamento, 'equipaggia_item'):
            successo = entita_bersaglio.equipaggiamento.equipaggia_item(self, self.slot_equip)
            if successo:
                if gioco and hasattr(gioco, 'io'):
                    gioco.io.mostra_messaggio(f"{entita_bersaglio.nome} equipaggia {self.nome}.")
                # Qui si potrebbero applicare gli effetti bonus
            else:
                logger.warning(f"Impossibile equipaggiare {self.nome} su {entita_bersaglio.nome} nello slot {self.slot_equip}.")
                if gioco and hasattr(gioco, 'io'):
                    gioco.io.mostra_messaggio(f"Non puoi equipaggiare {self.nome} ora.")
        else:
            logger.warning(f"L'entità {entita_bersaglio.nome} non ha un sistema di equipaggiamento compatibile.")


    def usa(self, entita_bersaglio, gioco=None):
        logger.info(f"Non puoi 'usare' direttamente {self.nome} in questo modo. Prova ad equipaggiarlo.")
        if gioco and hasattr(gioco, 'io'):
            gioco.io.mostra_messaggio(f"{self.nome} non può essere usato direttamente. Prova ad equipaggiarlo.")
        pass 