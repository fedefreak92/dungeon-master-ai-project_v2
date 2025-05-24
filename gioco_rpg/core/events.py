from enum import Enum, auto

class EventType(Enum):
    """
    Enum di tutti i tipi di evento supportati.
    Evita typos e permette code completion negli IDE.
    """
    # Eventi di sistema
    TICK = "TICK"
    INIT = "INIT"
    SHUTDOWN = "SHUTDOWN"
    GAME_INIT = "game_init"
    GAME_START = "game_start"
    GAME_EXIT = "game_exit"
    GAME_PAUSE = "game_pause"
    GAME_RESUME = "game_resume"
    GAME_SAVE = "game_save"
    GAME_LOAD = "game_load"
    GAME_LOADED = "game_loaded"  # Evento emesso quando un salvataggio è stato caricato con successo
    GAME_LOADED_CONFIRMED = "game_loaded_confirmed"  # Evento emesso quando il server conferma il caricamento
    
    # Eventi di gioco
    PLAYER_MOVE = "PLAYER_MOVE"
    PLAYER_ATTACK = "PLAYER_ATTACK"
    PLAYER_USE_ITEM = "PLAYER_USE_ITEM"
    PLAYER_INTERACT = "PLAYER_INTERACT"
    PLAYER_POSITION_UPDATED = "player_position_updated"
    GAME_STATE_REQUESTED = "game_state_requested"
    FULL_STATE_REQUESTED = "full_state_requested"
    RECENT_UPDATES_REQUESTED = "recent_updates_requested"
    ENTITIES_REQUESTED = "entities_requested"
    GAME_SAVE_REQUESTED = "game_save_requested"
    GAME_LOAD_REQUESTED = "game_load_requested"
    
    # Eventi di stato di gioco
    ENTER_STATE = "ENTER_STATE"
    EXIT_STATE = "EXIT_STATE"
    CHANGE_STATE = "CHANGE_STATE"
    PUSH_STATE = "PUSH_STATE"
    POP_STATE = "POP_STATE"
    STATE_PAUSED = "STATE_PAUSED"
    STATE_RESUMED = "STATE_RESUMED"
    
    # Eventi UI
    UI_UPDATE = "UI_UPDATE"
    UI_DIALOG_OPEN = "UI_DIALOG_OPEN"
    UI_DIALOG_CLOSE = "UI_DIALOG_CLOSE"
    UI_INVENTORY_TOGGLE = "UI_INVENTORY_TOGGLE"
    DIALOG_CHOICE = "DIALOG_CHOICE"
    UI_NOTIFICATION = "ui_notification"
    UI_BUTTON_CLICK = "ui_button_click"
    UI_HOVER = "ui_hover"
    UI_OPEN = "ui_open"
    UI_CLOSE = "ui_close"
    UI_NAVIGATE = "ui_navigate"
    
    # Eventi di mappa
    MAP_LOAD = "MAP_LOAD"
    MAP_CHANGE = "MAP_CHANGE"
    MAP_CHANGED = "MAP_CHANGED"
    MAP_LIST_REQUEST = "MAP_LIST_REQUEST"
    MAP_CHANGE_REQUEST = "MAP_CHANGE_REQUEST"
    MAP_DATA_REQUEST = "MAP_DATA_REQUEST"
    MAP_DATA_LOADED = "MAP_DATA_LOADED"
    MAP_STATE_REQUEST = "MAP_STATE_REQUEST"
    ENTITY_SPAWN = "ENTITY_SPAWN"
    ENTITY_DESPAWN = "ENTITY_DESPAWN"
    ENTITY_MOVED = "ENTITY_MOVED"
    MOVEMENT_BLOCKED = "MOVEMENT_BLOCKED"
    MAP_ITEM_SPAWN = "map_item_spawn"
    MAP_ENTITY_SPAWN = "map_entity_spawn"
    MAP_ENTITY_DESPAWN = "map_entity_despawn"
    MAP_DATA_REQUESTED = "map_data_requested"
    
    # Eventi di combattimento
    COMBAT_START = "COMBAT_START"
    COMBAT_END = "COMBAT_END"
    COMBAT_TURN = "COMBAT_TURN"
    DAMAGE_DEALT = "DAMAGE_DEALT"
    DAMAGE_TAKEN = "DAMAGE_TAKEN"
    ENTITY_DEFEATED = "ENTITY_DEFEATED"
    COMBAT_ACTION_REQUIRED = "COMBAT_ACTION_REQUIRED"
    COMBAT_TURN_START = "combat_turn_start"
    COMBAT_ACTION = "combat_action"
    COMBAT_DAMAGE_DEALT = "combat_damage_dealt"
    COMBAT_ENTITY_DEFEATED = "combat_entity_defeated"

    # Eventi di rete
    NETWORK_CONNECT = "NETWORK_CONNECT"
    NETWORK_DISCONNECT = "NETWORK_DISCONNECT"
    NETWORK_MESSAGE = "NETWORK_MESSAGE"
    
    # Eventi di trigger
    TRIGGER_ACTIVATED = "TRIGGER_ACTIVATED"
    TREASURE_FOUND = "TREASURE_FOUND"
    
    # Eventi di player
    PLAYER_JOIN = "PLAYER_JOIN"
    PLAYER_LEAVE = "PLAYER_LEAVE"
    PLAYER_LOGIN = "PLAYER_LOGIN"
    PLAYER_LOGOUT = "PLAYER_LOGOUT"
    PLAYER_CREATED = "PLAYER_CREATED"
    
    # Eventi di sessione
    SESSION_CREATE_START = "SESSION_CREATE_START"
    SESSION_CREATED = "SESSION_CREATED"
    SESSION_JOIN = "session_join"
    SESSION_LEAVE = "session_leave"
    SESSION_END = "session_end"
    TOKEN_REFRESH = "token_refresh"
    SESSION_VALIDATED = "session_validated"
    SESSION_EXPIRED = "session_expired"
    
    # Eventi di animazione (frontend)
    ANIMATION_STARTED = "ANIMATION_STARTED"
    ANIMATION_COMPLETED = "ANIMATION_COMPLETED"
    
    # Eventi di prova di abilità
    ABILITA_SCELTA = "ABILITA_SCELTA"
    PROVA_ABILITA_INIZIA = "PROVA_ABILITA_INIZIA"
    PROVA_ABILITA_ESEGUI = "PROVA_ABILITA_ESEGUI"
    PROVA_ABILITA_RISULTATO = "PROVA_ABILITA_RISULTATO"
    PROVA_ABILITA_TERMINA = "PROVA_ABILITA_TERMINA"
    PROVA_ABILITA_NPC_SELEZIONATO = "PROVA_ABILITA_NPC_SELEZIONATO"
    PROVA_ABILITA_OGGETTO_SELEZIONATO = "PROVA_ABILITA_OGGETTO_SELEZIONATO"
    PROVA_ABILITA_DIFFICOLTA_IMPOSTATA = "PROVA_ABILITA_DIFFICOLTA_IMPOSTATA"
    
    # Eventi di inventario
    INVENTORY_OPEN = "INVENTORY_OPEN"
    INVENTORY_CLOSE = "INVENTORY_CLOSE"
    INVENTORY_ITEM_ADDED = "INVENTORY_ITEM_ADDED"
    INVENTORY_ITEM_REMOVED = "INVENTORY_ITEM_REMOVED"
    INVENTORY_ITEM_USED = "INVENTORY_ITEM_USED"
    INVENTORY_ITEM_EXAMINE = "INVENTORY_ITEM_EXAMINE"
    INVENTORY_ITEM_EQUIP = "INVENTORY_ITEM_EQUIP"
    INVENTORY_ITEM_UNEQUIP = "INVENTORY_ITEM_UNEQUIP"
    INVENTORY_FILTER_CHANGED = "INVENTORY_FILTER_CHANGED"
    INVENTORY_SORT_CHANGED = "INVENTORY_SORT_CHANGED"
    INVENTORY_PAGE_CHANGED = "INVENTORY_PAGE_CHANGED"
    MENU_CHANGED = "MENU_CHANGED"
    MENU_SELECTION = "MENU_SELECTION"
    MENU_DISPLAY = "MENU_DISPLAY"
    ITEM_ACQUIRED = "item_acquired"
    ITEM_REMOVED = "item_removed"
    ITEM_EQUIPPED = "item_equipped"
    ITEM_UNEQUIPPED = "item_unequipped"
    INVENTORY_UPDATED = "inventory_updated"
    
    # Eventi di dialogo
    DIALOG_START = "dialog_start"
    DIALOG_END = "dialog_end"
    
    # Eventi di quesito
    QUEST_ACCEPT = "quest_accept"
    QUEST_COMPLETE = "quest_complete"
    QUEST_FAIL = "quest_fail"
    QUEST_ACCEPTED = "quest_accepted"
    QUEST_COMPLETED = "quest_completed"
    QUEST_UPDATED = "quest_updated"
    
    # Eventi di sistema / Debug
    SERVER_ERROR = "server_error"
    DEBUG_LOG = "debug_log"
    
    # Eventi di input utente (potrebbero essere più specifici)
    INPUT_RECEIVED = "input_received"
    
    # Wildcard per ascoltare tutti gli eventi
    WILDCARD = "*"

    def __str__(self):
        """Permette di usare l'enum come stringa"""
        return self.value

# Compatibilità retroattiva con il codice esistente
# Esporta tutti gli enum come costanti globali
for event in EventType:
    globals()[event.name] = event.value 