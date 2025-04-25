#!/usr/bin/env python3
"""
Script per eseguire tutti i test del gioco RPG.
Esegue test unitari, di integrazione, di regressione ed end-to-end.
"""

import unittest
import sys
import os
import argparse

# Aggiungi la directory principale al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_all_tests():
    """Esegue tutti i test presenti nelle sottocartelle."""
    # Trova tutte le directory di test, escludendo quelle non rilevanti
    excluded_dirs = ['__pycache__', '.pytest_cache', 'manuali', 'salvataggi', 'logs', 
                     'assets', 'salvataggi_test']
    test_dirs = [d for d in os.listdir('.') if os.path.isdir(d) and 
               d not in excluded_dirs]
    
    # Crea un test suite vuoto
    test_suite = unittest.TestSuite()
    
    # Aggiungi i test da ogni directory
    for directory in test_dirs:
        print(f"Caricamento test da {directory}/...")
        # Verifica se la directory contiene almeno un file di test
        has_test_files = False
        for file in os.listdir(directory):
            if file.startswith('test_') and file.endswith('.py'):
                has_test_files = True
                break
        
        if not has_test_files:
            print(f"  Saltato: nessun file di test trovato in {directory}/")
            continue
            
        # Crea un loader per i test
        loader = unittest.TestLoader()
        # Carica i test dalla directory
        suite = loader.discover(
            start_dir=directory,
            pattern='test_*.py',
            top_level_dir=os.path.abspath('.')
        )
        # Aggiungi i test al suite principale
        test_suite.addTest(suite)
    
    # Crea un runner per i test
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Esegui i test
    return runner.run(test_suite)

def run_specific_tests(test_type):
    """Esegue i test di una specifica categoria."""
    # Verifica che la directory esista
    if not os.path.isdir(test_type):
        print(f"Errore: la directory '{test_type}' non esiste.")
        return None
    
    # Crea un loader per i test
    loader = unittest.TestLoader()
    
    # Carica i test dalla directory specificata
    test_suite = loader.discover(
        start_dir=test_type,
        pattern='test_*.py',
        top_level_dir=os.path.abspath('.')
    )
    
    # Crea un runner per i test
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Esegui i test
    return runner.run(test_suite)

if __name__ == '__main__':
    # Configura il parser per gli argomenti
    parser = argparse.ArgumentParser(description='Esegue i test per il gioco RPG.')
    parser.add_argument('--type', choices=['unitari', 'integrazione', 'regressione', 'e2e', 'ui', 'carico', 'all'],
                        default='all', help='Tipo di test da eseguire')
    
    # Analizza gli argomenti
    args = parser.parse_args()
    
    # Cambia directory a quella corrente del file
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Esegui i test in base al tipo specificato
    if args.type == 'all':
        print("Esecuzione di tutti i test...")
        result = run_all_tests()
    else:
        print(f"Esecuzione dei test '{args.type}'...")
        result = run_specific_tests(args.type)
    
    # Mostra un messaggio riepilogativo
    if result:
        print("\nRiepilogo:")
        print(f"Test eseguiti: {result.testsRun}")
        print(f"Errori: {len(result.errors)}")
        print(f"Fallimenti: {len(result.failures)}")
        
        # Esci con codice di errore se ci sono test falliti
        if result.errors or result.failures:
            sys.exit(1)
    else:
        sys.exit(1) 