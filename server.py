"""
File principale per l'avvio del server di gioco RPG.
"""

# Applica il monkey patching di eventlet prima di importare altri moduli
try:
    import eventlet
    eventlet.monkey_patch()
    print("Eventlet monkey patch applicato con successo")
except ImportError as e:
    print(f"Eventlet non disponibile: {e}")
    print("Il server utilizzerà la modalità threading")

# Import per compatibilità con il codice esistente
from server import app, socketio, run_server
import sys
import os

# Aggiungi la directory radice al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Inizializza il sistema di logging migliorato
from util.logging_config import configurazione_logging
configurazione_logging()

if __name__ == "__main__":
    print("Avvio del server RPG in corso...")
    run_server() 