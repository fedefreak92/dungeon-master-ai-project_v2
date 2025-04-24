# Guida alla Migrazione delle Routes all'architettura EventBus

## Introduzione

Questo documento descrive il processo di migrazione dei file delle routes all'architettura EventBus. Dopo aver completato con successo la migrazione del modulo WebSocket, è necessario adattare anche le routes per utilizzare l'EventBus per una corretta comunicazione tra componenti del sistema.

## Indice

1. [Struttura di base per l'integrazione](#struttura-di-base-per-lintegrazione)
2. [Pattern comuni nelle routes](#pattern-comuni-nelle-routes)
3. [Esempi di migrazione per tipi di routes](#esempi-di-migrazione-per-tipi-di-routes)
4. [Gestione della retrocompatibilità](#gestione-della-retrocompatibilità)
5. [Best practices](#best-practices)
6. [Checklist di migrazione](#checklist-di-migrazione)

## Struttura di base per l'integrazione

### 1. Importare le dipendenze necessarie

All'inizio di ogni file route, aggiungi queste importazioni:

```python
from core.event_bus import EventBus
from core.events import EventType
```

### 2. Inizializzare l'istanza EventBus

Aggiungi questa riga dopo le importazioni e definizioni iniziali:

```python
# Ottieni l'istanza di EventBus
event_bus = EventBus.get_instance()
```

### 3. Utilizza emit() per le azioni

Sostituisci le chiamate dirette con emissioni di eventi:

```python
# Prima
giocatore.imposta_posizione("mercato", nuova_x, nuova_y)

# Dopo
event_bus.emit(EventType.PLAYER_MOVE, 
               player_id=giocatore.id,
               entity_id=giocatore.id,
               entity_type="player",
               from_position=(x, y),
               position=(nuova_x, nuova_y),
               map_id="mercato")
```

## Pattern comuni nelle routes

### Gestione del movimento

```python
@routes.route("/movimento", methods=['POST'])
def gestisci_movimento():
    # ... validazione e setup ...
    
    # Ottieni EventBus
    event_bus = EventBus.get_instance()
    
    # Calcola la nuova posizione
    x, y = giocatore.get_posizione(map_id)
    dx, dy = direzioni[direzione]
    nuova_x, nuova_y = x + dx, y + dy
    
    # Verifica se il movimento è valido
    if mappa.is_valid_position(nuova_x, nuova_y):
        # Emetti evento di movimento
        event_bus.emit(EventType.PLAYER_MOVE, 
                      player_id=giocatore.id,
                      entity_id=giocatore.id,
                      entity_type="player",
                      from_position=(x, y),
                      position=(nuova_x, nuova_y),
                      map_id=map_id)
        
        # Per retrocompatibilità
        giocatore.imposta_posizione(map_id, nuova_x, nuova_y)
        
        # ... continua logica ...
    else:
        # Emetti evento di movimento bloccato
        event_bus.emit(EventType.MOVEMENT_BLOCKED,
                      player_id=giocatore.id,
                      reason="obstacle",
                      position=(x, y),
                      direction=direzione)
        
        # ... gestione errore ...
```

### Gestione delle interazioni

```python
@routes.route("/interazione", methods=['POST'])
def gestisci_interazione():
    # ... validazione e setup ...
    
    # Ottieni EventBus
    event_bus = EventBus.get_instance()
    
    # Emetti evento di interazione
    event_bus.emit(EventType.PLAYER_INTERACT, 
                  player_id=giocatore.id,
                  target_id=target_id,
                  target_type=target_type,
                  interaction_type=tipo_interazione)
    
    # Per retrocompatibilità
    # ... chiamata diretta esistente ...
    
    # ... continua logica ...
```

### Gestione del cambio di stato

```python
@routes.route("/transizione", methods=['POST'])
def transizione_stato():
    # ... validazione e setup ...
    
    # Ottieni EventBus
    event_bus = EventBus.get_instance()
    
    # Emetti evento di cambio stato
    event_bus.emit(EventType.CHANGE_STATE, 
                  session_id=id_sessione,
                  player_id=giocatore.id,
                  current_state=stato_corrente,
                  target_state=stato_destinazione,
                  params=parametri)
    
    # Per retrocompatibilità
    # ... chiamata diretta esistente ...
    
    # ... continua logica ...
```

## Esempi di migrazione per tipi di routes

### Esempio 1: taverna_routes.py

```python
# Prima
@taverna_routes.route("/movimento", methods=['POST'])
def gestisci_movimento():
    # ... setup ...
    
    giocatore.imposta_posizione("taverna", nuova_x, nuova_y)
    
    # ... resto della logica ...

# Dopo
from core.event_bus import EventBus
from core.events import EventType

@taverna_routes.route("/movimento", methods=['POST'])
def gestisci_movimento():
    # ... setup ...
    
    # Ottieni EventBus
    event_bus = EventBus.get_instance()
    
    # Emetti evento di movimento
    event_bus.emit(EventType.PLAYER_MOVE, 
                  player_id=giocatore.id,
                  entity_id=giocatore.id,
                  entity_type="player",
                  from_position=(x, y),
                  position=(nuova_x, nuova_y),
                  map_id="taverna")
    
    # Per retrocompatibilità
    giocatore.imposta_posizione("taverna", nuova_x, nuova_y)
    
    # ... resto della logica ...
```

### Esempio 2: combat_routes.py

```python
# Prima
@combat_routes.route("/attacco", methods=['POST'])
def esegui_attacco():
    # ... setup ...
    
    state.azioni.esegui_attacco(attaccante, bersaglio, arma)
    
    # ... resto della logica ...

# Dopo
from core.event_bus import EventBus
from core.events import EventType

@combat_routes.route("/attacco", methods=['POST'])
def esegui_attacco():
    # ... setup ...
    
    # Ottieni EventBus
    event_bus = EventBus.get_instance()
    
    # Emetti evento di attacco
    event_bus.emit(EventType.COMBAT_ACTION, 
                  combat_id=combat_id,
                  action_type="attack",
                  attacker_id=attaccante.id,
                  target_id=bersaglio.id,
                  weapon_id=arma.id if arma else None)
    
    # Per retrocompatibilità
    state.azioni.esegui_attacco(attaccante, bersaglio, arma)
    
    # ... resto della logica ...
```

## Gestione della retrocompatibilità

Per garantire una transizione fluida, è possibile mantenere temporaneamente entrambi gli approcci:

```python
# Emetti evento (nuovo approccio)
event_bus.emit(EventType.PLAYER_MOVE, 
               player_id=giocatore.id,
               position=(nuova_x, nuova_y),
               map_id=map_id)

# Chiamata diretta (approccio originale per retrocompatibilità)
giocatore.imposta_posizione(map_id, nuova_x, nuova_y)
```

Man mano che il sistema si stabilizza, si possono rimuovere le chiamate dirette.

## Best practices

1. **Standardizza i parametri degli eventi**:
   - Usa sempre `player_id` per identificare il giocatore
   - Usa sempre `entity_id` e `entity_type` per entità
   - Usa sempre `from_position` e `position` per coordinate

2. **Nomi degli eventi**:
   - Usa sempre i nomi definiti in `EventType` da `core.events`
   - Non creare nuovi tipi di eventi senza aggiungerli prima a `EventType`

3. **Logica di fallback**:
   - Includi sempre una gestione degli errori
   - Controlla la presenza di EventBus prima di usarlo (per i casi di test)

4. **Logging**:
   - Aggiungi logging per gli eventi importanti

## Checklist di migrazione

Per ogni file route:

- [ ] Importa `EventBus` e `EventType` 
- [ ] Ottieni l'istanza di EventBus
- [ ] Identifica le azioni che dovrebbero emettere eventi
- [ ] Sostituisci le chiamate dirette con `event_bus.emit()`
- [ ] Mantieni temporaneamente le chiamate dirette per retrocompatibilità
- [ ] Aggiungi log per monitorare l'emissione degli eventi
- [ ] Testa la route per verificare che funzioni correttamente
- [ ] Verifica che gli handler degli eventi vengano attivati correttamente

## Eventi comuni per tipo di route

### taverna_routes.py, mercato_routes.py e simili
- `EventType.PLAYER_MOVE`
- `EventType.PLAYER_INTERACT`
- `EventType.MOVEMENT_BLOCKED`
- `EventType.UI_UPDATE`

### combat_routes.py
- `EventType.COMBAT_ACTION`
- `EventType.COMBAT_TURN` 
- `EventType.DAMAGE_DEALT`
- `EventType.DAMAGE_TAKEN`
- `EventType.COMBAT_END`

### dialogo_routes.py
- `EventType.DIALOG_OPEN`
- `EventType.DIALOG_CLOSE`
- `EventType.DIALOG_CHOICE`
- `EventType.UI_UPDATE`

### inventory_routes.py
- `EventType.ITEM_USED`
- `EventType.ITEM_ADDED`
- `EventType.ITEM_REMOVED`
- `EventType.UI_UPDATE`

### session_routes.py
- `EventType.PLAYER_JOIN`
- `EventType.PLAYER_LEAVE`
- `EventType.CHANGE_STATE`
- `EventType.PUSH_STATE`
- `EventType.POP_STATE` 