#!/usr/bin/env python
"""
Script per correggere automaticamente tutte le importazioni problematiche 'gioco_rpg' nel progetto.
Usa questo script quando hai problemi con importazioni del tipo 'from xxx import yyy'.

Uso: cd percorso/progetto && python fix_multiple_imports.py
"""

import os
import re
import glob
from pathlib import Path
import fileinput
import sys

# Regex per individuare le importazioni problematiche
IMPORT_REGEX_1 = r'from\s+gioco_rpg\.([a-zA-Z0-9_.]+)\s+import\s+([a-zA-Z0-9_, ]+)'
IMPORT_REGEX_2 = r'import\s+gioco_rpg\.([a-zA-Z0-9_.]+)(?:\s+as\s+([a-zA-Z0-9_]+))?'

def fix_imports():
    """Corregge tutte le importazioni che iniziano con 'gioco_rpg'"""
    
    total_files = 0
    modified_files = 0
    
    print("Ricerca di file Python in corso...")
    
    # Trova tutti i file Python nel progetto
    python_files = []
    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"Trovati {len(python_files)} file Python")
    
    # Esamina e correggi ogni file
    for file_path in python_files:
        total_files += 1
        file_modified = False
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
        except Exception as e:
            print(f"Errore nella lettura di {file_path}: {e}")
            continue
            
        new_content = content
        
        # Cerca e correggi "from xxx import yyy"
        for match in re.finditer(IMPORT_REGEX_1, content):
            module_path = match.group(1)
            imports = match.group(2)
            old_import = match.group(0)
            new_import = f"from {module_path} import {imports}"
            
            print(f"In {file_path}: {old_import} -> {new_import}")
            new_content = new_content.replace(old_import, new_import)
            file_modified = True
        
        # Cerca e correggi "import xxx [as yyy]"
        for match in re.finditer(IMPORT_REGEX_2, content):
            module_path = match.group(1)
            alias = match.group(2)
            old_import = match.group(0)
            
            if alias:
                new_import = f"import {module_path} as {alias}"
            else:
                new_import = f"import {module_path}"
                
            print(f"In {file_path}: {old_import} -> {new_import}")
            new_content = new_content.replace(old_import, new_import)
            file_modified = True
        
        # Scrivi il file solo se sono state fatte modifiche
        if file_modified:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                modified_files += 1
                print(f"File corretto: {file_path}")
            except Exception as e:
                print(f"Errore nella scrittura di {file_path}: {e}")
    
    print(f"\nOperazione completata. Modificati {modified_files} file su {total_files} totali.")
    return modified_files

def fix_prova_abilita():
    """Corregge l'errore specifico nel file prova_abilita.py"""
    
    # Cerca il file prova_abilita.py
    prova_files = glob.glob('**/prova_abilita.py', recursive=True)
    
    if not prova_files:
        print("File prova_abilita.py non trovato.")
        return False
        
    file_path = prova_files[0]
    print(f"Analisi file prova_abilita: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Correggi le importazioni problematiche
        new_content = re.sub(r'from\s+gioco_rpg\.([a-zA-Z0-9_.]+)\s+import', r'from \1 import', content)
        
        # Scrivi il file modificato
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(new_content)
            
        print(f"Corrette importazioni in {file_path}")
        return True
    except Exception as e:
        print(f"Errore nella correzione di {file_path}: {e}")
        return False

def fix_zombie_socket():
    """Corregge l'errore nel handler zombie connections"""
    
    # Cerca il file connection.py
    conn_files = glob.glob('**/connection.py', recursive=True)
    
    if not conn_files:
        print("File connection.py non trovato.")
        return False
        
    file_path = conn_files[0]
    print(f"Analisi file connection: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Cerca il codice problematico
        if "socketio.disconnect(zombie)" in content:
            # Sostituisci con una soluzione alternativa
            new_content = content.replace(
                "socketio.disconnect(zombie)",
                "socketio.emit('force_disconnect', {'reason': 'inactive'}, room=zombie)"
            )
            
            # Scrivi il file modificato
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(new_content)
                
            print(f"Corretto metodo di disconnessione zombie in {file_path}")
            return True
    except Exception as e:
        print(f"Errore nella correzione di {file_path}: {e}")
    
    return False

if __name__ == "__main__":
    print("=== Script di correzione delle importazioni e altri errori ===")
    
    # Ottieni la directory corrente
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Directory corrente: {current_dir}")
    
    # Correggi le importazioni problematiche
    modified = fix_imports()
    
    # Correggi l'errore nel file prova_abilita.py
    fixed_prova = fix_prova_abilita()
    
    # Correggi l'errore di disconnessione zombie
    fixed_zombie = fix_zombie_socket()
    
    # Riassunto delle operazioni
    print("\nRiepilogo delle correzioni:")
    print(f"- {modified} file con importazioni problematiche corretti")
    print(f"- Correzione file prova_abilita.py: {'Completata' if fixed_prova else 'Non necessaria/Non riuscita'}")
    print(f"- Correzione disconnessione zombie: {'Completata' if fixed_zombie else 'Non necessaria/Non riuscita'}")
    
    print("\nCorrezioni completate. Riavvia il server per verificare il funzionamento.") 