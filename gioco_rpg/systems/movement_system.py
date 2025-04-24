"""
Sistema di movimento basato su EventBus.
Gestisce il movimento di tutte le entità nel mondo di gioco.
"""

import logging
from core.event_bus import EventBus
import core.events as Events

logger = logging.getLogger(__name__)

class MovementSystem:
    """
    Sistema che gestisce il movimento delle entità nel mondo di gioco
    utilizzando l'architettura basata su eventi.
    """
    def __init__(self, world):
        """
        Inizializza il sistema di movimento.
        
        Args:
            world: Il mondo di gioco contenente mappa e entità
        """
        self.world = world
        self.event_bus = EventBus.get_instance()
        self._register_handlers()
        logger.info("Sistema di movimento inizializzato")
    
    def _register_handlers(self):
        """Registra gli handler per eventi di movimento"""
        self.event_bus.on(Events.TICK, self.update)
        self.event_bus.on(Events.PLAYER_MOVE, self.handle_player_move)
        self.event_bus.on("ENTITY_MOVE", self.handle_entity_move)
    
    def update(self, dt):
        """
        Aggiorna il movimento di tutte le entità con velocità.
        Chiamato ad ogni tick del game loop.
        
        Args:
            dt: Delta time, tempo trascorso dall'ultimo aggiornamento
        """
        # Implementazione per entità con movimento automatico
        # Per esempio NPC che si muovono autonomamente
        for entity in self.world.get_moving_entities():
            if hasattr(entity, 'update_movement') and callable(entity.update_movement):
                entity.update_movement(dt)
    
    def handle_player_move(self, direction, player_id=None):
        """
        Gestisce la richiesta di movimento del giocatore.
        
        Args:
            direction: Direzione del movimento ('north', 'south', 'east', 'west')
            player_id: ID del giocatore (opzionale, usa il giocatore principale se None)
        """
        # Ottieni il giocatore (può essere specifico o default)
        player = self.world.get_player(player_id)
        if not player:
            logger.warning(f"Player {player_id} non trovato")
            return
            
        # Calcola nuova posizione
        new_x, new_y = player.x, player.y
        if direction == "north": new_y -= 1
        elif direction == "south": new_y += 1
        elif direction == "east": new_x += 1
        elif direction == "west": new_x -= 1
        else:
            logger.warning(f"Direzione non valida: {direction}")
            return
        
        # Esegui il movimento
        self._move_entity(player, new_x, new_y)
    
    def handle_entity_move(self, entity_id, direction=None, target_pos=None):
        """
        Gestisce il movimento di una qualsiasi entità.
        
        Args:
            entity_id: ID dell'entità da muovere
            direction: Direzione del movimento (opzionale)
            target_pos: Posizione di destinazione (x, y) (opzionale)
            
        Note:
            Deve essere specificato o direction o target_pos
        """
        entity = self.world.get_entity(entity_id)
        if not entity:
            logger.warning(f"Entità {entity_id} non trovata")
            return
        
        # Calcola nuova posizione
        if target_pos:
            new_x, new_y = target_pos
        elif direction:
            new_x, new_y = entity.x, entity.y
            if direction == "north": new_y -= 1
            elif direction == "south": new_y += 1
            elif direction == "east": new_x += 1
            elif direction == "west": new_x -= 1
            else:
                logger.warning(f"Direzione non valida: {direction}")
                return
        else:
            logger.warning("Nessuna direzione o posizione target specificata")
            return
        
        # Esegui il movimento
        self._move_entity(entity, new_x, new_y)
    
    def _move_entity(self, entity, new_x, new_y):
        """
        Muove un'entità a una nuova posizione, gestendo collisioni e trigger.
        
        Args:
            entity: L'entità da muovere
            new_x, new_y: Nuove coordinate di destinazione
            
        Returns:
            bool: True se il movimento è avvenuto, False altrimenti
        """
        # Verifica collisioni
        if not self.world.can_move_to(new_x, new_y):
            # Emetti evento di movimento bloccato
            self.event_bus.emit(
                "MOVEMENT_BLOCKED",
                entity_id=entity.id,
                from_pos=(entity.x, entity.y),
                to_pos=(new_x, new_y),
                reason="collision"
            )
            logger.debug(f"Movimento bloccato per {entity.id} verso ({new_x}, {new_y})")
            return False
        
        # Salva vecchia posizione
        old_x, old_y = entity.x, entity.y
        
        # Esegui movimento
        entity.x, entity.y = new_x, new_y
        
        # Aggiorna mappa attuale se necessario
        if hasattr(entity, 'mappa_corrente') and self.world.gestore_mappe:
            mappa = self.world.gestore_mappe.ottieni_mappa(entity.mappa_corrente)
            if mappa:
                # Rimuovi entità dalla vecchia posizione
                if (old_x, old_y) in mappa.entita:
                    mappa.entita[(old_x, old_y)].discard(entity.id)
                
                # Aggiungi entità alla nuova posizione
                if (new_x, new_y) not in mappa.entita:
                    mappa.entita[(new_x, new_y)] = set()
                mappa.entita[(new_x, new_y)].add(entity.id)
        
        # Emetti evento di movimento completato
        self.event_bus.emit(
            Events.ENTITY_MOVED,
            entity_id=entity.id,
            from_pos=(old_x, old_y),
            to_pos=(new_x, new_y)
        )
        
        # Controlla trigger sulla nuova posizione
        self.check_position_triggers(entity, new_x, new_y)
        
        logger.debug(f"Entità {entity.id} mossa da ({old_x}, {old_y}) a ({new_x}, {new_y})")
        return True
    
    def check_position_triggers(self, entity, x, y):
        """
        Controlla se ci sono trigger sulla posizione attuale dell'entità.
        
        Args:
            entity: L'entità da controllare
            x, y: Coordinate della posizione
        """
        triggers = self.world.get_triggers_at(x, y)
        for trigger in triggers:
            self.event_bus.emit(
                Events.TRIGGER_ACTIVATED,
                trigger_id=trigger.id,
                trigger_type=trigger.type,
                entity_id=entity.id,
                position=(x, y)
            )
            
            # Gestisci trigger speciali
            if trigger.type == "porta":
                self._handle_door_trigger(entity, trigger)
            elif trigger.type == "trappola":
                self._handle_trap_trigger(entity, trigger)
            elif trigger.type == "tesoro":
                self._handle_treasure_trigger(entity, trigger)
    
    def _handle_door_trigger(self, entity, trigger):
        """Gestisce trigger di tipo porta/passaggio"""
        if not hasattr(entity, 'is_player') or not entity.is_player:
            return  # Solo i giocatori possono usare le porte
            
        # Ottieni informazioni sul cambio mappa
        target_map = trigger.get('target_map')
        target_x = trigger.get('target_x')
        target_y = trigger.get('target_y')
        
        if not target_map:
            logger.warning(f"Porta {trigger.id} senza mappa di destinazione")
            return
            
        # Emetti evento di cambio mappa
        self.event_bus.emit(
            Events.MAP_CHANGE,
            entity_id=entity.id,
            from_map=entity.mappa_corrente,
            to_map=target_map,
            target_pos=(target_x, target_y)
        )
    
    def _handle_trap_trigger(self, entity, trigger):
        """Gestisce trigger di tipo trappola"""
        # Calcola danno della trappola
        damage = trigger.get('damage', 1)
        
        # Emetti evento di danno
        self.event_bus.emit(
            Events.DAMAGE_TAKEN,
            entity_id=entity.id,
            damage=damage,
            damage_type="trap",
            source_id=trigger.id
        )
    
    def _handle_treasure_trigger(self, entity, trigger):
        """Gestisce trigger di tipo tesoro"""
        if not hasattr(entity, 'is_player') or not entity.is_player:
            return  # Solo i giocatori possono raccogliere tesori
            
        # Verifica se il tesoro è già stato raccolto
        if trigger.get('collected', False):
            return
            
        # Segna come raccolto
        trigger['collected'] = True
        
        # Emetti evento di tesoro trovato
        self.event_bus.emit(
            "TREASURE_FOUND",
            entity_id=entity.id,
            treasure_id=trigger.id,
            contents=trigger.get('contents', [])
        ) 