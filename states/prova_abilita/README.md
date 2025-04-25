# Sistema di Prove di Abilità

Questo modulo gestisce le prove di abilità nel gioco RPG. Le prove di abilità permettono al giocatore e ai personaggi non giocanti (NPG) di mettere alla prova le loro caratteristiche e abilità.

## Struttura dei File

- `prova_abilita_state.py`: Classe principale che gestisce lo stato delle prove di abilità
- `ui.py`: Funzioni per la visualizzazione dell'interfaccia utente
- `ui_handlers.py`: Gestori di eventi UI (click e scelte da dialoghi)
- `esecuzione.py`: Funzioni per l'esecuzione delle prove e la gestione dei risultati
- `interazioni.py`: Funzioni per l'interazione con NPG e oggetti
- `serializzazione.py`: Funzioni per serializzare e deserializzare lo stato

## Funzionalità Principali

### Tipi di Prove

1. **Prove Base**: Tiro semplice contro una difficoltà
2. **Prove contro NPG**: Confronto di abilità tra giocatore e NPG
3. **Prove con Oggetti**: Interazione con oggetti del mondo di gioco

### Abilità Supportate

- Caratteristiche di base: Forza, Destrezza, Costituzione, Intelligenza, Saggezza, Carisma
- Abilità specifiche: Percezione, Persuasione, Intimidire, ecc.

### Meccanica di Gioco

Le prove si basano sul lancio di un dado a 20 facce (d20) a cui viene aggiunto il modificatore dell'abilità o caratteristica. Il risultato viene confrontato con una difficoltà o con il risultato di un altro personaggio.

## Utilizzo

```python
# Esempio di utilizzo
from states.prova_abilita import ProvaAbilitaState

# Creazione dello stato
stato_prova = ProvaAbilitaState()

# Aggiunta allo stack di stati del gioco
gioco.push_stato(stato_prova)
```

## Integrazione con il Sistema

Il sistema di prove di abilità si integra con altri componenti del gioco:

- **Sistema di combattimento**: per determinare il successo di manovre speciali
- **Sistema di dialogo**: per influenzare le conversazioni con i NPG
- **Sistema di esplorazione**: per superare ostacoli e scoprire segreti

## Estensione

È possibile estendere il sistema con nuovi tipi di prove implementando funzioni aggiuntive nei moduli appropriati. Ad esempio, per aggiungere un nuovo tipo di prova basata su condizioni ambientali, si possono modificare i file `esecuzione.py` e `interazioni.py`. 