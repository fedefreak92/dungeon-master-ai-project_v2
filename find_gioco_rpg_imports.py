#!/usr/bin/env python
"""
Script per trovare tutte le importazioni problematiche 'gioco_rpg' nel progetto
"""

import os
import re
import glob
from pathlib import Path

# Regex per individuare le importazioni problematiche
IMPORT_REGEX = r'from\s+gioco_rpg\.([a-zA-Z0-9_.]+)\s+import'
IMPORT_REGEX_2 = r'import\s+gioco_rpg\.([a-zA-Z0-9_.]+)'

def find_all_imports():
    """Trova tutte le importazioni problematiche che iniziano con 'gioco_rpg'"""
    
    total_files = 0
    problematic_files = []
    
    # Trova tutti i file Python nel progetto
    python_files = glob.glob('**/*.py', recursive=True)
    
    for file_path in python_files:
        total_files += 1
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            try:
                content = file.read()
            except Exception as e:
                print(f"Errore nella lettura di {file_path}: {e}")
                continue
            
        # Cerca importazioni problematiche
        matches1 = re.findall(IMPORT_REGEX, content)
        matches2 = re.findall(IMPORT_REGEX_2, content)
        
        if matches1 or matches2:
            problematic_files.append((file_path, matches1 + matches2))
    
    # Stampa i risultati
    print(f"Analizzati {total_files} file Python")
    print(f"Trovati {len(problematic_files)} file con importazioni problematiche:")
    
    for file_path, matches in problematic_files:
        print(f"\n{file_path}:")
        for match in matches:
            print(f"  - gioco_rpg.{match}")

if __name__ == "__main__":
    # Ottieni la directory corrente
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)
    
    print(f"Directory corrente: {current_dir}")
    
    # Trova le importazioni problematiche
    find_all_imports() 