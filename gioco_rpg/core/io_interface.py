"""
Modulo per retrocompatibilità con il vecchio sistema IO.
L'implementazione è stata spostata nel pacchetto io/.
Questo file è mantenuto solo per retrocompatibilità e verrà rimosso in futuro.
"""

# Import delle classi dal nuovo pacchetto
from .io.base import GameIO
from .io.gui_io import GUI2DIO
from .io.mock_io import MockIO
from .io.adapter import IOInterface
from .io.events import EventManager

# Deprecation warning
import warnings
warnings.warn(
    "Il modulo io_interface.py è deprecato e verrà rimosso in future versioni. "
    "Utilizzare invece il package gioco_rpg.core.io",
    DeprecationWarning, 
    stacklevel=2
)