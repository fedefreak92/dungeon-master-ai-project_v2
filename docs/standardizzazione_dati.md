# Standardizzazione e Ottimizzazione dei Formati Dati

## 📝 Panoramica

Questo documento descrive il processo di standardizzazione e ottimizzazione dei formati dati implementato nel progetto RPG. L'obiettivo principale è garantire coerenza, validità e prestazioni ottimali nella gestione dei dati di gioco.

Il sistema implementa:
- **Schema JSON unificato** per tutti i tipi di entità
- **Validazione automatica** dei dati
- **Classe Serializable** come base per tutti gli oggetti di gioco
- **Cache intelligente** con gestione TTL (time-to-live)
- **Sistema di versionamento** per la migrazione dei dati

## 🏗️ Architettura del Sistema

### 1. Componenti Principali

#### 1.1 Serializable (`serializable.py`)
La classe base per tutti gli oggetti serializzabili, fornisce:
- Metodo `to_dict()` per convertire un oggetto in dizionario
- Metodo `from_dict()` per ricreare un oggetto da un dizionario
- Gestione automatica dei riferimenti circolari
- Esclusione di attributi privati

#### 1.2 Registry delle Classi (`class_registry.py`)
Sistema di registrazione delle classi per la deserializzazione:
- Funzione `register_class()` per registrare classi
- Decoratore `auto_register_decoratore` per registrazione automatica
- Funzione `get_class()` per ottenere una classe dal nome

#### 1.3 Validatore JSON (`json_validator.py`)
Sistema di validazione dei dati basato su schemi JSON:
- Validazione automatica durante caricamento/salvataggio
- Generazione automatica di schemi dai dati esistenti
- Supporto per tipi di dati complessi

#### 1.4 DataManager Migliorato (`data_manager.py`)
Gestore centralizzato dei dati con:
- Cache intelligente con TTL configurabile per tipo di dati
- Caricamento lazy per ottimizzare le prestazioni
- Sistema di hook per personalizzare caricamento/salvataggio
- Versionamento integrato dei file dati

#### 1.5 Migratore Dati (`data_migrator.py`)
Strumento per la migrazione dei dati esistenti:
- Migrazione automatica al nuovo formato
- Supporto per regole di migrazione specifiche per tipo
- CLI per esecuzione selettiva

### 2. Processo di Standardizzazione

Il processo di standardizzazione prevede i seguenti passaggi:

1. **Setup** - Creazione directory e configurazione ambiente
2. **Generazione Schemi** - Creazione schemi JSON per ogni tipo di entità
3. **Validazione** - Controllo di validità di tutti i dati esistenti
4. **Migrazione** - Conversione dei dati al formato standardizzato
5. **Test** - Verifica del corretto funzionamento del sistema

## 🚀 Utilizzo

### Script Principale

Lo script `standardize_data.py` nella directory principale consente di eseguire l'intero processo o singoli passaggi:

```bash
# Esegui l'intero processo
python standardize_data.py --all

# Genera solo gli schemi
python standardize_data.py --schemas

# Valida solo i dati
python standardize_data.py --validate

# Migra i dati al nuovo formato
python standardize_data.py --migrate

# Testa il sistema di serializzazione
python standardize_data.py --test
```

### Implementazione nelle Classi Esistenti

Per utilizzare il sistema di serializzazione nelle classi esistenti:

```python
from gioco_rpg.util.serializable import Serializable
from gioco_rpg.util.class_registry import auto_register_decoratore

@auto_register_decoratore
class MiaClasse(Serializable):
    def __init__(self):
        self.attributo1 = "valore"
        self.attributo2 = 123
        self._attributo_privato = "non serializzato"

    # Opzionale: escludere attributi specifici
    _non_serializable_attrs = Serializable._non_serializable_attrs.union({"attributo_da_escludere"})
```

### DataManager Migliorato

Il DataManager migliorato viene utilizzato allo stesso modo di prima:

```python
from gioco_rpg.util.data_manager import get_data_manager

# Ottieni l'istanza singleton
data_manager = get_data_manager()

# Carica dati con validazione automatica
mostri = data_manager.load_data("mostri", "monsters.json")

# Salva dati con aggiunta automatica della versione
data_manager.save_data("mostri", mostri, "monsters.json")
```

## 📊 Schemi JSON

Gli schemi JSON sono memorizzati nella directory `gioco_rpg/data/schemas/` e seguono lo standard JSON Schema Draft-07. Esempio di schema per i mostri:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Schema Mostro",
  "description": "Schema per la validazione delle entità mostro",
  "type": "object",
  "required": [
    "nome",
    "descrizione",
    "statistiche",
    "armi",
    "armatura",
    "oro",
    "esperienza",
    "token",
    "difficolta"
  ],
  "properties": {
    "nome": {
      "type": "string",
      "description": "Nome del mostro"
    },
    // ... altre proprietà ...
  }
}
```

## 🔄 Sistema di Hook

Il sistema di hook consente di personalizzare il comportamento di caricamento e salvataggio:

```python
from gioco_rpg.util.data_manager import DataHooks

# Esempio: registrazione di hook di post-caricamento per i mostri
def post_load_monsters(data):
    # Modifica i dati dopo il caricamento
    for monster in data.values():
        if "hp_max" not in monster:
            monster["hp_max"] = monster["statistiche"]["hp"]
    return data

DataHooks.register_post_load("mostri", post_load_monsters)
```

## 🛠️ Estensibilità

Il sistema è progettato per essere facilmente estendibile:

- **Nuovi Tipi di Entità**: Aggiunta di nuove coppie chiave-valore in `_entity_mapping` del DataManager
- **Regole di Migrazione**: Implementazione di funzioni specifiche in `data_migrator.py`
- **Validazione Personalizzata**: Creazione di schemi JSON personalizzati
- **Cache Configurabile**: Impostazione TTL specifici in `_cache_ttl` del DataManager

## 📝 Note Tecniche

### Campi Speciali

I seguenti campi speciali vengono utilizzati nei dati serializzati:

- `_class`: Nome della classe per la deserializzazione
- `_ref_id`: Riferimento a un oggetto già serializzato (per evitare riferimenti circolari)
- `_version`: Versione del formato dati
- `_last_modified`: Timestamp dell'ultima modifica

### Gestione Errori

Il sistema implementa una robusta gestione degli errori:

- **Logging** dettagliato di tutti gli errori
- **Fallback** graceful in caso di dati mancanti o non validi
- **Recupero** automatico quando possibile

### Prestazioni

La cache intelligente migliora significativamente le prestazioni:

- **TTL configurabile** per tipo di dati
- **Invalidazione selettiva** della cache
- **Caricamento lazy** per ridurre l'utilizzo di memoria

## 🤝 Contribuire

È possibile contribuire al sistema di standardizzazione in diversi modi:

1. **Schemi JSON migliori** per i vari tipi di entità
2. **Regole di migrazione** più sofisticate
3. **Ottimizzazioni della cache** per casi d'uso specifici
4. **Test più completi** per verificare la robustezza del sistema

## 📚 Riferimenti

- [JSON Schema](https://json-schema.org/): standard per la validazione dei dati JSON
- [Flask-Marshmallow](https://flask-marshmallow.readthedocs.io/): ispirazione per il sistema di serializzazione
- [jsonschema](https://python-jsonschema.readthedocs.io/): libreria Python per la validazione JSON 