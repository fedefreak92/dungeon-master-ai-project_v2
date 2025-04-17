# Modulo Gestione Inventario

Questo modulo gestisce tutte le funzionalità relative all'inventario del giocatore, inclusa la visualizzazione, l'uso degli oggetti, l'equipaggiamento e l'esame degli oggetti.

## Struttura

Il modulo è organizzato nei seguenti file:

- `inventario_state.py`: Classe principale che gestisce lo stato dell'inventario
- `ui_handlers.py`: Gestione dell'interfaccia utente e visualizzazione
- `filtri.py`: Funzioni di filtro per gli oggetti dell'inventario
- `oggetti.py`: Gestione delle interazioni con gli oggetti
- `menu_handlers.py`: Gestione delle azioni e scelte di menu

## Flusso di utilizzo

1. Il giocatore entra nello stato di gestione inventario
2. Viene mostrato il menu principale con le opzioni disponibili
3. Il giocatore può scegliere di:
   - Usare un oggetto
   - Equipaggiare un oggetto
   - Rimuovere equipaggiamento
   - Esaminare un oggetto
   - Tornare allo stato precedente

## Interazioni con altri moduli

- Interagisce con il sistema di equipaggiamento del giocatore
- Utilizza il sistema di interfaccia utente per la visualizzazione
- Si integra con il sistema di stati per la navigazione 