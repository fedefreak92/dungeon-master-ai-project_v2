"""
Package states - contiene tutti gli stati del gioco.
"""

# Importa gli stati di base
from states.base import BaseState, BaseGameState
from states.mercato import MercatoState
from states.inventario import GestioneInventarioState
from states.combattimento import CombattimentoState
from states.taverna import TavernaState
from states.dialogo import DialogoState

# Moduli importati automaticamente quando si importa il package states
from states.mappa import MappaState
from states.inventario import InventarioState

# Rendi disponibili i nomi a livello di pacchetto
__all__ = [
    'BaseState',
    'BaseGameState',
    'MercatoState',
    'GestioneInventarioState',
    'CombattimentoState',
    'TavernaState',
    'DialogoState',
    'MappaState',
    'InventarioState'
]
