# Modulo Dialogo

Questo modulo gestisce le interazioni di dialogo tra il giocatore e i personaggi non giocanti (NPG).

## Struttura del Modulo

Il modulo è stato suddiviso in diversi file per una migliore manutenibilità e organizzazione:

- **dialogo_state.py**: Classe principale e metodi core che gestiscono lo stato del dialogo.
- **ui.py**: Funzioni per la gestione dell'interfaccia grafica del dialogo.
- **ui_handlers.py**: Handler per eventi dell'interfaccia utente (click, selezioni, menu).
- **effetti.py**: Gestione degli effetti che possono verificarsi durante il dialogo (guarigione, scambio di oggetti, ecc).
- **serializzazione.py**: Metodi per la serializzazione e deserializzazione dello stato del dialogo.
- **__init__.py**: Espone la classe DialogoState e definisce costanti utili per gli eventi.

## Aggiornamento all'architettura EventBus

Il modulo è stato aggiornato per supportare il sistema EventBus, che permette una comunicazione più flessibile e disaccoppiata tra i vari componenti. Principali miglioramenti:

- **Estensione di EnhancedBaseState**: La classe DialogoState ora estende EnhancedBaseState invece di BaseGameState
- **Registrazione handler eventi**: Nuovo metodo `_register_event_handlers()` per registrare gli handler per eventi specifici
- **Metodo update()**: Implementato il nuovo metodo di aggiornamento basato su eventi
- **Emissione eventi**: Utilizzo di `emit_event()` per comunicare cambiamenti di stato e azioni
- **Retrocompatibilità**: Mantenuta la compatibilità con il codice esistente

## Utilizzo del Modulo

Per avviare un dialogo con un NPG:

```python
from states.dialogo import DialogoState

# Metodo classico
stato_dialogo = DialogoState(npg=personaggio, stato_ritorno="mappa")
gioco.push_stato(stato_dialogo)

# Metodo basato su eventi
from states.dialogo import DIALOG_EVENTS
game_state.emit_event(Events.PUSH_STATE, 
                      state_class=DialogoState, 
                      npg=personaggio, 
                      stato_ritorno="mappa")
```

## Eventi supportati

Il modulo gestisce i seguenti tipi di eventi:

- **UI_DIALOG_OPEN**: Apertura di un dialogo (`dialog_id`, `title`, `content`, `options`)
- **UI_DIALOG_CLOSE**: Chiusura di un dialogo
- **DIALOG_CHOICE**: Selezione di un'opzione di dialogo (`choice`, `dialog_id`)
- **MENU_SELECTION**: Selezione dal menu contestuale (`menu_id`, `selection`)
- **INVENTORY_ITEM_ADDED**: Aggiunta di un oggetto all'inventario (`item_id`, `item_type`, `quantity`)
- **INVENTORY_ITEM_REMOVED**: Rimozione di un oggetto dall'inventario
- **INVENTORY_ITEM_USED**: Utilizzo di un oggetto o effetto
- **DAMAGE_TAKEN**: Cambiamenti ai punti vita (inclusa guarigione)
- **UI_UPDATE**: Aggiornamenti all'interfaccia utente

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

Ora ogni effetto emette anche eventi appropriati che possono essere intercettati da altri componenti del sistema.

## Integrazione con altri sistemi

Grazie all'architettura EventBus, il modulo Dialogo può ora:

- Comunicare con l'inventario senza dipendenze dirette
- Notificare modifiche allo stato del giocatore 
- Integrarsi meglio con i sistemi di UI
- Supportare estensioni future senza modificare il codice esistente 