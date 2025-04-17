# Sistema di Mappe - Documentazione

Questo documento descrive la struttura e il funzionamento del sistema di mappe nel gioco RPG.

## Struttura delle Mappe

Ogni mappa è definita in un file JSON nella directory `data/mappe/`. I file JSON devono seguire una struttura standard per garantire la compatibilità con il sistema di caricamento.

### Schema Standard di una Mappa

```json
{
  "nome": "nome_mappa",
  "larghezza": 20,
  "altezza": 15,
  "tipo": "interno",
  "descrizione": "Descrizione della mappa",
  "griglia": [
    [1, 1, 1, 1, ...],
    [1, 0, 0, 0, ...],
    ...
  ],
  "oggetti": {},
  "npg": {},
  "porte": {
    "(x, y)": ["mappa_destinazione", x_dest, y_dest]
  },
  "pos_iniziale_giocatore": [5, 5]
}
```

### Campi Principali

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `nome` | string | Nome univoco della mappa, usato come identificatore |
| `larghezza` | integer | Larghezza della mappa in celle |
| `altezza` | integer | Altezza della mappa in celle |
| `tipo` | string | Tipo di mappa: "interno", "esterno", "dungeon", ecc. |
| `descrizione` | string | Descrizione testuale della mappa |
| `griglia` | array 2D | Matrice che rappresenta il terreno: 0=vuoto, 1=muro, 2=porta |
| `oggetti` | object | Dizionario di oggetti con chiave "(x, y)" |
| `npg` | object | Dizionario di NPG con chiave "(x, y)" |
| `porte` | object | Dizionario di porte con chiave "(x, y)" e valore [mappa_dest, x_dest, y_dest] |
| `pos_iniziale_giocatore` | array | Posizione iniziale del giocatore [x, y] |

## Posizionamento di Oggetti e NPC

Gli oggetti interattivi e gli NPC non vengono direttamente definiti nel file della mappa, ma vengono caricati dai file di configurazione corrispondenti.

### Oggetti Interattivi

Gli oggetti interattivi sono definiti in `data/items/oggetti_interattivi.json` e le loro posizioni sulle mappe in `data/items/mappe_oggetti.json`.

Struttura di `mappe_oggetti.json`:
```json
{
  "nome_mappa": [
    {
      "nome": "nome_oggetto",
      "posizione": [x, y]
    },
    ...
  ],
  ...
}
```

### NPC

Gli NPC sono definiti attraverso il codice e le loro posizioni sulle mappe in `data/npc/mappe_npg.json`.

Struttura di `mappe_npg.json`:
```json
{
  "nome_mappa": [
    {
      "nome": "nome_npg",
      "posizione": [x, y]
    },
    ...
  ],
  ...
}
```

Le conversazioni degli NPC sono definite in `data/npc/conversations.json`.

## Caricamento delle Mappe

Il caricamento delle mappe avviene attraverso la classe `GestitoreMappe` in `world/gestore_mappe.py`. Il gestore si occupa di:

1. Caricare le mappe dai file JSON
2. Verificare la validità delle mappe
3. Caricare gli oggetti interattivi per ogni mappa
4. Caricare gli NPC per ogni mappa
5. Gestire il movimento del giocatore tra le mappe

## Consigli per la Creazione di Mappe

1. **Usa nomi univoci**: Ogni mappa deve avere un nome univoco che corrisponde al nome del file JSON (senza estensione).
2. **Verifica la validità**: Assicurati che la griglia abbia le dimensioni corrette e che la posizione iniziale del giocatore sia valida.
3. **Definisci tutte le porte**: Ogni porta deve avere una destinazione valida in un'altra mappa.
4. **Posiziona oggetti e NPC**: Utilizza i file di configurazione per posizionare oggetti e NPC nelle mappe.
5. **Mantieni la consistenza**: Segui lo schema standard per garantire la compatibilità con il sistema.

## Esempi di Mappe Valide

- `data/mappe/taverna.json`
- `data/mappe/mercato.json`
- `data/mappe/cantina.json`

## Schema di Riferimento

Per una definizione completa della struttura dati, consulta `data/world_state/world_state_schema.json`. 