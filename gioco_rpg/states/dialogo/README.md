# Modulo Dialogo

Questo modulo gestisce le interazioni di dialogo tra il giocatore e i personaggi non giocanti (NPG).

## Struttura del Modulo

Il modulo è stato suddiviso in diversi file per una migliore manutenibilità e organizzazione:

- **dialogo_state.py**: Classe principale e metodi core che gestiscono lo stato del dialogo.
- **ui.py**: Funzioni per la gestione dell'interfaccia grafica del dialogo.
- **ui_handlers.py**: Handler per eventi dell'interfaccia utente (click, selezioni, menu).
- **effetti.py**: Gestione degli effetti che possono verificarsi durante il dialogo (guarigione, scambio di oggetti, ecc).
- **serializzazione.py**: Metodi per la serializzazione e deserializzazione dello stato del dialogo.
- **__init__.py**: Espone la classe DialogoState per mantenere la retrocompatibilità.

## Utilizzo del Modulo

Per avviare un dialogo con un NPG:

```python
from states.dialogo import DialogoState

# Crea uno stato di dialogo con l'NPG
stato_dialogo = DialogoState(npg=personaggio, stato_ritorno="mappa")

# Aggiungi lo stato al gioco
gioco.push_stato(stato_dialogo)
```

## Personalizzazione dei Dialoghi

I dialoghi sono definiti all'interno degli NPG attraverso una struttura di dizionari che rappresentano gli stati della conversazione. Ogni stato può avere:

- Un testo visualizzato
- Opzioni di risposta
- Effetti speciali (guarigione, consegna di oggetti, ecc.)

Per personalizzare i dialoghi, modifica la proprietà `conversazioni` dell'NPG.

## Effetti Speciali

Gli effetti possono essere semplici (stringa) o complessi (dizionario):

- **Semplici**: "riposo", "cura_leggera"
- **Complessi**: {"tipo": "consegna_oro", "quantita": 10}, {"tipo": "aggiungi_item", "oggetto": "Spada Arrugginita"}

## Eventi UI Supportati

Il modulo gestisce diversi tipi di eventi UI:

- Click su elementi dell'interfaccia
- Selezione di opzioni di dialogo
- Azioni dal menu contestuale 