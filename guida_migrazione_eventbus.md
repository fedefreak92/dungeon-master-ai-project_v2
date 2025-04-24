# Guida alla Migrazione degli Stati all'architettura EventBus

## Introduzione

Questa guida descrive come migrare gli stati del gioco all'architettura EventBus. L'EventBus è un pattern di comunicazione che consente a componenti non direttamente correlati di comunicare tra loro senza creare dipendenze dirette. Questo approccio consente una migliore modularità, disaccoppiamento e manutenibilità del codice.

L'implementazione dello stato `MappaState` sarà utilizzata come modello di riferimento per la migrazione degli altri stati.

## Indice

1. [Vantaggi dell'architettura basata su eventi](#vantaggi-dellarchitettura-basata-su-eventi)
2. [Guida passo-passo per la migrazione](#guida-passo-passo-per-la-migrazione)
3. [Pattern comuni](#pattern-comuni)
4. [Gestione della retrocompatibilità](#gestione-della-retrocompatibilità)
5. [Best practices](#best-practices)
6. [Checklist di migrazione](#checklist-di-migrazione)

## Vantaggi dell'architettura basata su eventi

- **Disaccoppiamento**: I componenti comunicano attraverso eventi invece di dipendenze dirette
- **Flessibilità**: Più componenti possono reagire allo stesso evento
- **Estensibilità**: Nuove funzionalità possono essere aggiunte sottoscrivendo eventi esistenti
- **Manutenibilità**: Il codice è più modulare e facile da mantenere
- **Testabilità**: Gli stati sono più facili da testare in isolamento

## Guida passo-passo per la migrazione

### 1. Estendere EnhancedBaseState invece di BaseState

```python
# Prima
from states.base_state import BaseState

class StatoEsempio(BaseState):
    # ...

# Dopo
from states.base.enhanced_base_state import EnhancedBaseState
import gioco_rpg.core.events as Events

class StatoEsempio(EnhancedBaseState):
    # ...
```

### 2. Aggiungere il registro degli handler di eventi

```python
def __init__(self, param1=None):
    # Inizializzazione standard
    super().__init__()
    self.param1 = param1
    
    # ... altre inizializzazioni ...
    
    # Registra handler per eventi
    self._register_event_handlers()

def _register_event_handlers(self):
    """Registra gli handler per eventi relativi a questo stato"""
    # Registra eventi specifici dello stato
    self.event_bus.on(Events.TIPO_EVENTO_1, self._handle_evento_1)
    self.event_bus.on(Events.TIPO_EVENTO_2, self._handle_evento_2)
    # ... altri eventi ...
```

### 3. Implementare il metodo update()

```python
def update(self, dt):
    """
    Nuovo metodo di aggiornamento basato su EventBus.
    Sostituisce gradualmente esegui().
    
    Args:
        dt: Delta time, tempo trascorso dall'ultimo aggiornamento
    """
    # Ottieni il contesto di gioco
    gioco = self.gioco
    if not gioco:
        return
    
    # Logica di aggiornamento specifica dello stato
    if not self.ui_aggiornata:
        self.aggiorna_renderer(gioco)
        self.ui_aggiornata = True
    
    # Altre logiche di aggiornamento...
```

### 4. Mantenere il metodo esegui() per retrocompatibilità

```python
def esegui(self, gioco):
    """
    Implementazione dell'esecuzione dello stato.
    Mantenuta per retrocompatibilità.
    
    Args:
        gioco: L'istanza del gioco
    """
    # Salva il contesto di gioco
    self.set_game_context(gioco)
    
    # Logica esistente...
    
    # Aggiungi chiamata a update per integrazione con EventBus
    self.update(0.033)  # Valore dt predefinito
    
    # Processa gli eventi UI
    super().esegui(gioco)
```

### 5. Implementare gli handler per gli eventi

```python
def _handle_evento_1(self, param1, param2, **kwargs):
    """
    Gestisce l'evento di tipo TIPO_EVENTO_1
    
    Args:
        param1: Primo parametro dell'evento
        param2: Secondo parametro dell'evento
        **kwargs: Parametri aggiuntivi
    """
    gioco = self.gioco
    if not gioco:
        return
        
    # Implementazione specifica...
```

### 6. Convertire le chiamate dirette in emissione di eventi

```python
# Prima
def _metodo_azione(self, gioco, parametro):
    metodo_diretto(self, gioco, parametro)
    
# Dopo
def _metodo_azione(self, gioco, parametro):
    """
    Wrapper per retrocompatibilità che ora emette un evento
    invece di chiamare direttamente il metodo.
    """
    # Emetti evento
    self.emit_event(Events.TIPO_EVENTO, param=parametro)
    
    # Opzionale: mantieni per retrocompatibilità
    metodo_diretto(self, gioco, parametro)
```

## Pattern comuni

### Gestione del movimento

```python
# Emissione evento
self.emit_event(Events.PLAYER_MOVE, direction=direzione)

# Handler
def _handle_entity_moved(self, entity_id, from_pos, to_pos, **kwargs):
    gioco = self.gioco
    if not gioco or entity_id != gioco.giocatore.id:
        return
        
    # Logica di gestione del movimento...
```

### Gestione delle interazioni

```python
# Emissione evento
self.emit_event(Events.PLAYER_INTERACT, 
               interaction_type="object",
               objects=list(oggetti_adiacenti.keys()))

# Handler
def _handle_player_interact(self, interaction_type, **kwargs):
    if interaction_type == "object":
        # Logica per interazione con oggetti
    elif interaction_type == "npc":
        # Logica per interazione con NPG
```

### Gestione dei trigger

```python
# Emissione evento
self.event_bus.emit(
    Events.TRIGGER_ACTIVATED,
    trigger_id=trigger_id,
    trigger_type=trigger_type,
    entity_id=entity_id,
    position=position
)

# Handler
def _handle_trigger_activated(self, trigger_id, trigger_type, **kwargs):
    if trigger_type == "porta":
        # Logica per porte
    elif trigger_type == "trappola":
        # Logica per trappole
```

## Gestione della retrocompatibilità

Per garantire che il codice esistente continui a funzionare durante la migrazione:

1. **Mantieni i metodi wrapper**:
   ```python
   def metodo_vecchio(self, gioco):
       # Emetti l'evento
       self.emit_event(Events.NUOVO_EVENTO)
       
       # Esegui anche la vecchia implementazione per retrocompatibilità
       # ...codice originale...
   ```

2. **Verifica la presenza di event_bus**:
   ```python
   if hasattr(stato, 'event_bus'):
       stato.event_bus.emit(Events.TIPO_EVENTO, **params)
   else:
       # Fallback al vecchio metodo
       vecchio_metodo(stato, gioco, params)
   ```

## Best practices

1. **Nomi eventi semantici**:
   - Usa nomi descrittivi per gli eventi (es. `PLAYER_MOVE` invece di `MOVE`)
   - Usa il namespace `Events` per accedere agli eventi

2. **Parametri eventi**:
   - I parametri dovrebbero essere nomi descrittivi
   - Usa tipi base (int, str, bool, list, dict) per i parametri
   - Includi sempre l'ID dell'entità coinvolta

3. **Design degli handler**:
   - Controlla sempre se il contesto di gioco è disponibile
   - Gestisci solo gli eventi rilevanti per lo stato corrente
   - Considera il filtro per entità rilevanti

4. **Emissione eventi**:
   - Usa `emit_event()` per eventi normali
   - Considera `emit_immediate()` solo per eventi che richiedono risposta immediata

5. **Tracciamento**:
   - Aggiungi log per debug in Eventi complessi
   - Controlla eventi lenti (> 4ms) che possono causare rallentamenti

## Checklist di migrazione

Per ogni stato da migrare:

- [ ] Estendi `EnhancedBaseState` invece di `BaseState`
- [ ] Implementa il metodo `_register_event_handlers()`
- [ ] Implementa il metodo `update(dt)`
- [ ] Aggiorna `esegui()` per chiamare `update()`
- [ ] Implementa gli handler per ogni tipo di evento rilevante
- [ ] Converti le chiamate dirette in emissione di eventi
- [ ] Verifica la retrocompatibilità
- [ ] Testa lo stato migrato

## Esempio di migrazione: StatoDialogo

Esempio di conversione dello stato dialogo:

```python
from states.base.enhanced_base_state import EnhancedBaseState
import gioco_rpg.core.events as Events

class DialogoState(EnhancedBaseState):
    def __init__(self, npg=None, stato_ritorno=None):
        super().__init__()
        self.npg = npg
        self.stato_ritorno = stato_ritorno
        self.fase = "conversazione"
        self.ui_aggiornata = False
        
        # Registra handler per eventi
        self._register_event_handlers()
        
    def _register_event_handlers(self):
        """Registra gli handler per eventi relativi al dialogo"""
        self.event_bus.on(Events.UI_DIALOG_OPEN, self._handle_dialog_open)
        self.event_bus.on(Events.UI_DIALOG_CLOSE, self._handle_dialog_close)
        self.event_bus.on(Events.DIALOG_CHOICE, self._handle_dialog_choice)
        
    def update(self, dt):
        """Aggiornamento basato su eventi"""
        gioco = self.gioco
        if not gioco:
            return
            
        # Logica di aggiornamento...
        
    def _mostra_dialogo(self, gioco):
        """Mostra un dialogo emettendo eventi invece di chiamate dirette"""
        # Emetti evento di dialogo aperto
        self.emit_event(Events.UI_DIALOG_OPEN, 
                       dialog_id="dialogo_principale",
                       npc_id=self.npg.id if self.npg else None,
                       options=self.opzioni_dialogo)
```

## Conclusione

Questa guida fornisce le basi per migrare con successo tutti gli stati all'architettura EventBus. Il processo può essere implementato gradualmente, stato per stato, mantenendo sempre la compatibilità con il codice esistente. Man mano che più stati vengono migrati, il gioco diventerà più modulare, flessibile ed estensibile. 