"""
File di compatibilità per server.py
Questo file è stato suddiviso in moduli più piccoli.
Si prega di utilizzare il nuovo modulo 'server' invece di importare direttamente da questo file.
"""

# Import per compatibilità con il codice esistente
from server import app, socketio, run_server

if __name__ == "__main__":
    print("NOTA: Questo file è stato riorganizzato in una struttura modulare.")
    print("Per avviare il server, utilizzare 'python main.py' invece di 'python server.py'")
    print("Avvio del server in corso...")
    run_server() 