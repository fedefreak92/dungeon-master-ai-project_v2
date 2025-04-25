"""
Questo file è mantenuto per retrocompatibilità.
Importa e riespone le classi base del modulo states.base.
"""

from states.base.base_state import BaseState
from states.base.base_game_state import BaseGameState
from states.base.enhanced_base_state import EnhancedBaseState

# __all__ per esportare i nomi
__all__ = ['BaseState', 'BaseGameState', 'EnhancedBaseState'] 