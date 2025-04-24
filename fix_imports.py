#!/usr/bin/env python
"""
Script per correggere automaticamente i problemi nel progetto gioco_rpg:
1. Sostituisce le importazioni 'from gioco_rpg.' con importazioni relative
2. Corregge l'errore di inizializzazione NPG

Uso: python fix_imports.py
"""

import os
import re
import sys
import glob
from pathlib import Path
import fileinput

# Regex per individuare le importazioni problematiche
IMPORT_REGEX = r'from\s+gioco_rpg\.([a-zA-Z0-9_.]+)\s+import'
NPG_REGEX = r'super\(\).__init__\(nome,\s*hp=[^,]+,\s*hp_max=[^,]+,\s*forza_base=[^,]+,\s*difesa=[^,]+,\s*token=token\)'

def fix_imports():
    """Corregge tutte le importazioni che iniziano con 'gioco_rpg'"""
    
    total_files = 0
    modified_files = 0
    
    # Trova tutti i file Python nel progetto
    python_files = glob.glob('**/*.py', recursive=True)
    
    for file_path in python_files:
        total_files += 1
        file_modified = False
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Cerca importazioni problematiche
        if re.search(IMPORT_REGEX, content):
            print(f"Correzione importazioni in: {file_path}")
            # Sostituisci le importazioni 'from gioco_rpg.' con importazioni relative
            new_content = re.sub(IMPORT_REGEX, r'from \1 import', content)
            
            # Scrivi il file modificato
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(new_content)
                
            file_modified = True
            modified_files += 1
    
    print(f"\nCompletato fix importazioni. Modificati {modified_files} file su {total_files} totali.")

def fix_npg_init():
    """Corregge l'errore di inizializzazione NPG"""
    
    # Trova il file npg.py
    npg_files = glob.glob('**/npg.py', recursive=True)
    if not npg_files:
        print("File npg.py non trovato.")
        return
    
    npg_file = npg_files[0]
    print(f"Analisi file NPG: {npg_file}")
    
    with open(npg_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Cerca il pattern dell'inizializzazione problematica
    if re.search(NPG_REGEX, content):
        print(f"Correzione inizializzazione NPG in: {npg_file}")
        
        # Cerca anche il file entita.py per capire i parametri corretti
        entita_files = glob.glob('**/entita.py', recursive=True)
        if entita_files:
            entita_file = entita_files[0]
            print(f"Trovato file Entita: {entita_file}")
            
            # Leggi il file entita.py per analizzare i parametri del costruttore
            with open(entita_file, 'r', encoding='utf-8') as efile:
                entita_content = efile.read()
                
                # Cerca la firma del metodo __init__
                init_match = re.search(r'def\s+__init__\s*\(self,\s*([^)]+)\)', entita_content)
                if init_match:
                    # Estrai i parametri
                    params = init_match.group(1).split(',')
                    param_names = [p.strip().split('=')[0].strip() for p in params]
                    
                    print(f"Parametri di Entita.__init__: {param_names}")
                    
                    # Crea una nuova chiamata super().__init__ con i parametri corretti
                    new_init = "super().__init__(nome"
                    
                    # Aggiungi token se presente nei parametri
                    if 'token' in param_names:
                        new_init += ", token=token"
                    
                    new_init += ")"
                    
                    # Sostituisci la chiamata super().__init__ problematica
                    new_content = re.sub(NPG_REGEX, new_init, content)
                    
                    # Modifica anche hp e hp_max per aggiungerli come attributi dopo super().__init__
                    new_content = re.sub(r'super\(\).__init__\((.*?)\)', 
                                          r'super().__init__(\1)\n        self.hp = 10\n        self.hp_max = 10\n        self.forza_base = 13\n        self.difesa = 1', 
                                          new_content)
                    
                    # Scrivi il file modificato
                    with open(npg_file, 'w', encoding='utf-8') as file:
                        file.write(new_content)
                    
                    print(f"Corretto metodo __init__ in {npg_file}")

if __name__ == "__main__":
    # Ottieni la directory corrente
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)
    
    print(f"Directory corrente: {current_dir}")
    
    # Correggi le importazioni problematiche
    fix_imports()
    
    # Correggi l'errore NPG
    fix_npg_init()
    
    print("\nCorrezzioni completate. Riavvia il server per verificare.") 