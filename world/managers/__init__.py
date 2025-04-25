"""
Package per i manager che si occupano della gestione delle mappe e dei relativi componenti.
Divide le responsabilità del vecchio GestitoreMappe in classi più piccole e focalizzate.
"""

from .mappa_manager import MappaManager
from .oggetti_manager import OggettiManager
from .npg_manager import NPGManager
from .loader_manager import LoaderManager

__all__ = ['MappaManager', 'OggettiManager', 'NPGManager', 'LoaderManager'] 