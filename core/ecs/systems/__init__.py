"""
Modulo systems per il framework ECS (Entity-Component-System).
Contiene i sistemi di base per il motore di gioco.
"""

from .movement_system import MovementSystem
from .collision_system import CollisionSystem
from .interaction_system import InteractionSystem

# Export delle classi principali
__all__ = [
    'MovementSystem',
    'CollisionSystem',
    'InteractionSystem'
] 