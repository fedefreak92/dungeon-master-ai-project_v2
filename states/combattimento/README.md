# Modulo Combattimento

Questo modulo gestisce il sistema di combattimento del gioco, fornendo un'interfaccia per combattere contro nemici e NPG ostili.

## Struttura del modulo

Il modulo è organizzato in diversi file per facilitare la manutenzione e l'estensione:

- **__init__.py**: Espone la classe principale `CombattimentoState` per mantenere la retrocompatibilità
- **combattimento_state.py**: Contiene la classe principale che coordina tutti i componenti
- **azioni.py**: Gestisce le azioni possibili durante il combattimento (attacco, uso oggetti, ecc.)
- **turni.py**: Gestisce la sequenza dei turni e l'alternanza tra giocatore e nemico
- **ui.py**: Gestisce l'interfaccia utente del combattimento

## Funzionalità principali

- Combattimento a turni con sistema di lancio di dadi per il calcolo dell'esito delle azioni
- Gestione dell'equipaggiamento durante il combattimento
- Uso di oggetti dal proprio inventario
- Possibilità di tentare la fuga
- Interfaccia grafica con barre HP e animazioni
- Ricompense al termine del combattimento (oro, esperienza, oggetti)

## Come utilizzare il modulo

Per iniziare un combattimento, è sufficiente creare un'istanza di `CombattimentoState` con il nemico o l'NPG con cui combattere, e aggiungerla allo stack degli stati di gioco:

```python
from states.combattimento import CombattimentoState

# Con un nemico
nemico = Nemico("Goblin")
stato_combattimento = CombattimentoState(nemico=nemico)
gioco.push_stato(stato_combattimento)

# Con un NPG ostile
npg = NPG("Bandito")
stato_combattimento = CombattimentoState(npg_ostile=npg)
gioco.push_stato(stato_combattimento)
```

## Estensione del modulo

Per aggiungere nuove funzionalità al combattimento, seguire queste linee guida:

1. **Nuove azioni di combattimento**: Aggiungere metodi alla classe `AzioniCombattimento` in `azioni.py`
2. **Nuovi effetti di turno**: Estendere `GestoreTurni` in `turni.py`
3. **Nuovi elementi dell'interfaccia**: Aggiungere metodi a `UICombattimento` in `ui.py`

Mantenere la separazione delle responsabilità tra i diversi componenti per facilitare la manutenzione del codice. 