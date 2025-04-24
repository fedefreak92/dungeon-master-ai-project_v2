# Guida all'EventBus

## Introduzione

L'EventBus è un sistema centralizzato per la gestione degli eventi nel gioco. Permette a componenti non direttamente correlati di comunicare tra loro senza creare dipendenze dirette. Questo documento spiega come utilizzare l'EventBus, le best practice e come integrarlo con React.

## Indice

1. [Concetti base](#concetti-base)
2. [Utilizzo dell'EventBus](#utilizzo-delleventbus)
3. [Tipi di eventi disponibili](#tipi-di-eventi-disponibili)
4. [Integrazione con React](#integrazione-con-react)
5. [Thread-safety e prestazioni](#thread-safety-e-prestazioni)
6. [Debug e monitoring](#debug-e-monitoring)
7. [Migrazione dal vecchio sistema](#migrazione-dal-vecchio-sistema)

## Concetti base

L'EventBus implementa il pattern Observer (Publish-Subscribe) e ha tre componenti principali:

- **Subscriber**: Chi si iscrive per essere notificato quando un certo tipo di evento viene emesso
- **Publisher**: Chi emette eventi
- **EventBus**: Il mediatore che gestisce la comunicazione tra Publisher e Subscriber

Gli eventi sono identificati da un tipo (stringa o enum) e possono contenere dati aggiuntivi.

## Utilizzo dell'EventBus

### Ottenere l'istanza dell'EventBus

L'EventBus è un singleton, quindi c'è una sola istanza in tutto il sistema:

```python
# Backend (Python)
from gioco_rpg.core.event_bus import EventBus
from gioco_rpg.core.events import EventType

# Ottieni l'istanza singleton
event_bus = EventBus.get_instance()
```

```javascript
// Frontend (JavaScript)
import eventBus from 'services/eventBusService';
```

### Sottoscriversi a un evento

```python
# Backend
def handle_player_move(direction, player_id=None):
    print(f"Player {player_id} moved {direction}")

# Sottoscrivi e conserva il metodo per annullare la sottoscrizione
unsubscribe = event_bus.on(EventType.PLAYER_MOVE, handle_player_move)

# Quando non serve più, annulla la sottoscrizione
unsubscribe()
```

```javascript
// Frontend
function handleEntityMoved(data) {
  console.log(`Entity ${data.entity_id} moved to ${data.to}`);
}

// Sottoscrivi e conserva la funzione di cleanup
const unsubscribe = eventBus.on('ENTITY_MOVED', handleEntityMoved);

// Quando non serve più
unsubscribe();
```

### Emettere un evento

```python
# Backend
event_bus.emit(EventType.PLAYER_MOVE, direction="north", player_id="player1")

# Per eventi che richiedono esecuzione immediata (non messi in coda)
event_bus.emit_immediate(EventType.UI_DIALOG_OPEN, dialog_data={"text": "Ciao!"})
```

```javascript
// Frontend
eventBus.emit('PLAYER_MOVE', { direction: 'north' });
```

## Tipi di eventi disponibili

Gli eventi sono definiti in `gioco_rpg.core.events` come enum `EventType`. I principali gruppi sono:

- **Eventi di sistema**: `TICK`, `INIT`, `SHUTDOWN`
- **Eventi di gioco**: `PLAYER_MOVE`, `PLAYER_ATTACK`, `PLAYER_USE_ITEM`
- **Eventi di stato**: `ENTER_STATE`, `EXIT_STATE`, `CHANGE_STATE`, `PUSH_STATE`, `POP_STATE`
- **Eventi UI**: `UI_DIALOG_OPEN`, `UI_DIALOG_CLOSE`, `UI_INVENTORY_TOGGLE`
- **Eventi di mappa**: `MAP_LOAD`, `MAP_CHANGE`, `ENTITY_MOVED`
- **Eventi di rete**: `NETWORK_CONNECT`, `NETWORK_DISCONNECT`

Per una lista completa, vedere il file `gioco_rpg.core.events`.

### Wildcard

È possibile sottoscriversi a tutti gli eventi usando il wildcard `*`:

```python
def log_all_events(**kwargs):
    event_type = kwargs.get('_event_type', 'Unknown')
    print(f"Event: {event_type}, data: {kwargs}")

event_bus.on('*', log_all_events)
```

## Integrazione con React

Per i componenti React, è disponibile un hook personalizzato `useEventBus` che si occupa di gestire la sottoscrizione e la pulizia quando il componente viene smontato:

```jsx
import { useEventBus } from 'services/eventBusService';

function PlayerInfoComponent() {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  
  // Gestisce gli eventi di movimento del player
  const handlePlayerMoved = useCallback((data) => {
    if (data.entity_id === 'player') {
      setPosition(data.to);
    }
  }, []);
  
  // Sottoscrivi all'evento, la pulizia è gestita automaticamente
  useEventBus('ENTITY_MOVED', handlePlayerMoved);
  
  return (
    <div>
      Player position: {position.x}, {position.y}
    </div>
  );
}
```

### Prevenire memory leak in React

L'hook `useEventBus` gestisce automaticamente la pulizia delle sottoscrizioni quando un componente viene smontato. Se sottoscrivi manualmente, ricordati sempre di annullare la sottoscrizione nel cleanup:

```jsx
useEffect(() => {
  const unsubscribe = eventBus.on('ENTITY_MOVED', handlePlayerMoved);
  
  // Cleanup function
  return () => {
    unsubscribe();
  };
}, [handlePlayerMoved]);
```

## Thread-safety e prestazioni

L'EventBus è thread-safe e può essere utilizzato da qualsiasi thread senza problemi di concorrenza. Utilizza `RLock` e `SimpleQueue` internamente.

### Considerazioni sulle prestazioni

- Gli eventi vengono processati in batch nel game loop principale
- Gli handler lenti (>4ms) vengono loggati come warning
- Evita di emettere molti eventi in sequenza rapida dalla stessa origine
- Considera il pattern "batch events" per situazioni ad alta frequenza

## Debug e monitoring

L'EventBus offre strumenti di debug:

### Backend

```python
# Ottieni statistiche
stats = event_bus.get_stats()
print(f"Eventi processati: {stats['events_processed']}")
print(f"Handler lenti: {stats['slow_handlers']}")
```

### Frontend

```javascript
// Ottieni debug info
const info = eventBus.getDebugInfo();
console.log(`Subscriber attivi: ${info.totalSubscribers}`);
console.log(`Tipi di eventi attivi: ${info.activeEventTypes}`);
```

## Migrazione dal vecchio sistema

Se stai migrando dal vecchio sistema basato su chiamate dirette, ecco alcune linee guida:

### Per stati FSM

1. Usa `EnhancedBaseState` invece di `BaseState`
2. Implementa `update(dt)` invece di `esegui()`
3. Usa i metodi helper come `emit_event()`, `push_state()`, ecc.

### Per sistemi di gioco

1. Crea un handler per l'evento `TICK` che chiama `update(dt)`
2. Registra gli handler per eventi specifici
3. Emetti eventi invece di chiamare direttamente altri sistemi

### Esempio di conversione

**Prima**:
```python
def update_player(self):
    if self.key_pressed("UP"):
        self.move_player("north")
```

**Dopo**:
```python
def setup(self):
    self.event_bus.on(Events.PLAYER_MOVE, self.handle_player_move)

def handle_input(self, keys):
    if keys.get("UP"):
        self.event_bus.emit(Events.PLAYER_MOVE, direction="north")
```

Con questa modifica, qualsiasi componente può reagire al movimento del giocatore senza conoscerlo direttamente. 