#!/usr/bin/env python3
"""
Script principale per avviare il server del gioco RPG
"""

from server import run_server

if __name__ == "__main__":
    print("Avvio del server del gioco RPG...")
    run_server(debug=True, host="0.0.0.0", port=5000) 