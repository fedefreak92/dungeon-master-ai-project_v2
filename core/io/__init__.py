"""
Package IO per la gestione dell'Input/Output nel gioco RPG.
Fornisce interfacce e implementazioni per la comunicazione con l'utente.
"""

from .base import GameIO
from .gui_io import GUI2DIO
from .mock_io import MockIO
from .adapter import IOInterface
from .events import EventManager

__all__ = [
    'GameIO',
    'GUI2DIO',
    'MockIO',
    'IOInterface',
    'EventManager'
] 