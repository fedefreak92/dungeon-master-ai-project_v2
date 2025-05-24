from .item_base import ItemBase
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class Pozione(ItemBase):
    def __init__(self, id: str = None, nome: str = "", descrizione: str = "", 
                 valore: int = 0, peso: float = 0.0, immagine: str = "", 
                 quantita: int = 1, proprietà: Dict[str, Any] = None,
                 effetto_tipo: str = "cura_hp", # es. "cura_hp", "cura_mana", "buff_forza"
                 effetto_valore: int = 0, durata_effetto: int = 0): # Durata in turni/secondi, 0 per istantaneo
        super().__init__(id, nome, descrizione, valore, "pozione", peso, immagine, quantita, proprietà)
        self.effetto_tipo = effetto_tipo
        self.effetto_valore = effetto_valore
        self.durata_effetto = durata_effetto # 0 per effetto istantaneo

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "effetto_tipo": self.effetto_tipo,
            "effetto_valore": self.effetto_valore,
            "durata_effetto": self.durata_effetto
        })
        return data

    @classmethod
    def from_dict(cls, dati: Dict[str, Any]) -> 'Pozione':
        pozione = cls(
            id=dati.get("id"),
            nome=dati.get("nome", "Pozione Sconosciuta"),
            descrizione=dati.get("descrizione", "Una pozione misteriosa."),
            valore=dati.get("valore", 0),
            peso=dati.get("peso", 0.0),
            immagine=dati.get("immagine", ""),
            quantita=dati.get("quantita", 1),
            proprietà=dati.get("proprietà", {}),
            effetto_tipo=dati.get("effetto_tipo", "cura_hp"),
            effetto_valore=dati.get("effetto_valore", 0),
            durata_effetto=dati.get("durata_effetto", 0)
        )
        return pozione

    def usa(self, entita_bersaglio, gioco=None):
        logger.info(f"{entita_bersaglio.nome} usa {self.nome}.")
        # Logica per applicare l'effetto della pozione
        if self.effetto_tipo == "cura_hp":
            if hasattr(entita_bersaglio, 'hp') and hasattr(entita_bersaglio, 'hp_max'):
                entita_bersaglio.hp = min(entita_bersaglio.hp_max, entita_bersaglio.hp + self.effetto_valore)
                logger.info(f"{self.nome} cura {self.effetto_valore} HP a {entita_bersaglio.nome}. HP attuali: {entita_bersaglio.hp}")
                if gioco and hasattr(gioco, 'io'):
                    gioco.io.mostra_messaggio(f"{entita_bersaglio.nome} usa {self.nome} e recupera {self.effetto_valore} HP.")
            else:
                logger.warning(f"L'entità {entita_bersaglio.nome} non ha attributi hp/hp_max per l'effetto cura_hp.")
        else:
            logger.warning(f"Effetto pozione '{self.effetto_tipo}' non ancora implementato per {self.nome}.")
            if gioco and hasattr(gioco, 'io'):
                 gioco.io.mostra_messaggio(f"L'effetto di {self.nome} non è ancora ben definito.")

        if self.quantita == 1 and hasattr(entita_bersaglio, 'rimuovi_item'):
            # Questo è un modo semplificato, la logica di rimozione item/stack è in Entita
            # entita_bersaglio.rimuovi_item(self.nome) 
            # Dovremmo piuttosto chiamare un metodo che decrementa la quantità e rimuove se zero
            if hasattr(entita_bersaglio, 'inventario_manager') and hasattr(entita_bersaglio.inventario_manager, 'rimuovi_item_per_id'):
                 entita_bersaglio.inventario_manager.rimuovi_item_per_id(self.id, 1)
            elif hasattr(entita_bersaglio, 'rimuovi_item_per_id'): # Se il metodo è direttamente sull'entità
                 entita_bersaglio.rimuovi_item_per_id(self.id, 1)
            else: # Fallback a rimozione per nome se il sistema di ID non è pervasivo
                 logger.info(f"Tentativo di rimozione di {self.nome} per nome come fallback.")
                 entita_bersaglio.rimuovi_item(self.nome) 
        elif self.quantita > 1:
            self.quantita -=1 
            logger.info(f"Quantità di {self.nome} ridotta a {self.quantita}.")
        
        if gioco and hasattr(gioco, 'event_bus'):
            gioco.event_bus.emit("POTION_USED", potion_name=self.nome, target_id=entita_bersaglio.id, effect_type=self.effetto_tipo)

    def equipaggia(self, entita_bersaglio):
        logger.info(f"Non puoi equipaggiare {self.nome}, è una pozione.")
        pass 