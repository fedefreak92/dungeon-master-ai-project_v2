#!/usr/bin/env python3
import sys
import os

# Aggiungi la directory corrente al percorso di importazione
sys.path.append(os.getcwd())

try:
    # Prova a importare il modulo
    print("Tentativo di importare CombattimentoState...")
    from states.combattimento.combattimento_state import CombattimentoState
    print("Importazione riuscita!")
except ImportError as e:
    print(f"Errore di importazione: {e}")
    print(f"sys.path: {sys.path}")
except Exception as e:
    print(f"Altro errore: {e}")
    import traceback
    traceback.print_exc() 