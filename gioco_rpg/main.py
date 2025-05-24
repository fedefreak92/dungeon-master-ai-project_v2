#!/usr/bin/env python
"""
Punto di ingresso principale per l'applicazione del gioco RPG.
Avvia il server e configura tutto ciò che è necessario.
"""

# Monkey patch di eventlet prima di qualsiasi altra importazione
# Questo è fondamentale per evitare errori con eventlet
try:
    import eventlet
    eventlet.monkey_patch()
    print("Eventlet monkey patch applicato con successo")
except ImportError:
    print("Eventlet non disponibile, si utilizzerà una modalità asincrona alternativa")

import logging
import os
import sys
import importlib

# Configura il logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Assicurati che la directory corrente sia nel path di Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Inizializza il sistema di logging migliorato (se disponibile)
try:
    from util.logging_config import configurazione_logging
    configurazione_logging()
    print("Configurazione logging avanzata attivata")
except ImportError:
    print("Configurazione logging standard attiva")

# Importa le componenti necessarie
try:
    # Importiamo il modulo server direttamente come in server.py
    from server import app, socketio, run_server
    
    # Avvia il server
    if __name__ == "__main__":
        print("Avvio del server in corso...")
        # Chiamiamo direttamente run_server
        run_server(debug=True, host="0.0.0.0", port=5000)
except ImportError as e:
    if "circular import" in str(e).lower():
        logger.error("ERRORE IMPORTAZIONE CIRCOLARE RILEVATA!")
        logger.error(f"Dettaglio errore: {e}")
        logger.error("\nPossibili soluzioni:")
        logger.error("1. Controlla le importazioni nei moduli server/app.py e server/websocket/")
        logger.error("2. Usa importazioni ritardate (lazy loading) per rompere i cicli")
        logger.error("3. Verifica se le nuove modifiche EventBus hanno creato cicli di importazione")
    else:
        logger.error(f"Errore durante l'importazione dei moduli: {e}")
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1)
except Exception as e:
    logger.error(f"Errore durante l'avvio del server: {e}")
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1) 