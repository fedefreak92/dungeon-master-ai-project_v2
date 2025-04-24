"""
Test per le route di salvataggio e caricamento
"""

import pytest
import requests
import json
import os
import shutil
import random
import string
from unittest.mock import patch

# Importa la funzione helper che abbiamo definito in conftest.py
from ...conftest import post_with_json_header

# URL base per le richieste
BASE_URL = "http://localhost:5000"

@pytest.fixture
def nome_salvataggio_test():
    """Fixture che genera un nome casuale per i salvataggi di test"""
    caratteri_casuali = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_save_{caratteri_casuali}"

@pytest.fixture
def cartella_salvataggi_test():
    """Fixture che crea e gestisce una cartella temporanea per i salvataggi di test"""
    # Invece di importare percorsi, definiamo direttamente una cartella temporanea
    cartella_test = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "salvataggi_test")
    
    # Crea la cartella se non esiste
    os.makedirs(cartella_test, exist_ok=True)
    
    # Nessun patching necessario, usiamo le API direttamente
    yield cartella_test
    
    # Pulizia: rimuove i file nella cartella invece dell'intera cartella
    # Questo evita il problema di "Accesso negato" su Windows
    try:
        if os.path.exists(cartella_test):
            for file in os.listdir(cartella_test):
                file_path = os.path.join(cartella_test, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f"Errore nella rimozione del file {file_path}: {e}")
    except Exception as e:
        print(f"Errore durante la pulizia della cartella di test: {e}")

class TestSaveRoutes:
    """Test per le route di salvataggio e caricamento"""
    
    def test_elenco_salvataggi(self, cartella_salvataggi_test):
        """Verifica che l'API restituisca correttamente l'elenco dei salvataggi"""
        # Richiedi l'elenco dei salvataggi
        response = requests.get(f"{BASE_URL}/game/save/elenco")
        
        # Verifica che la richiesta sia andata a buon fine
        assert response.status_code == 200
        
        # Verifica il formato della risposta
        data = response.json()
        assert "successo" in data
        assert data["successo"] is True
        assert "salvataggi" in data
        assert isinstance(data["salvataggi"], list)
    
    def test_salva_e_carica_gioco(self, nome_salvataggio_test, cartella_salvataggi_test):
        """Verifica il ciclo completo di salvataggio e caricamento"""
        # Prima inizia una nuova sessione
        session_response = post_with_json_header(f"{BASE_URL}/game/session/inizia")
        assert session_response.status_code == 200
        session_data = session_response.json()
        assert session_data["successo"] is True
        id_sessione = session_data["id_sessione"]
        
        # Salva il gioco
        save_response = post_with_json_header(
            f"{BASE_URL}/game/save/salva",
            {"id_sessione": id_sessione, "nome_salvataggio": nome_salvataggio_test}
        )
        
        # Verifica che il salvataggio sia andato a buon fine
        assert save_response.status_code == 200
        save_data = save_response.json()
        assert save_data["successo"] is True
        
        # Verifica che il salvataggio appaia nell'elenco
        list_response = requests.get(f"{BASE_URL}/game/save/elenco")
        list_data = list_response.json()
        assert nome_salvataggio_test in [s["nome"] for s in list_data["salvataggi"]]
        
        # Carica il salvataggio appena creato
        load_response = post_with_json_header(
            f"{BASE_URL}/game/save/carica",
            {"nome_salvataggio": nome_salvataggio_test}
        )
        
        # Verifica che il caricamento sia andato a buon fine
        assert load_response.status_code == 200
        load_data = load_response.json()
        assert load_data["successo"] is True
        assert "id_sessione" in load_data
    
    def test_elimina_salvataggio(self, nome_salvataggio_test, cartella_salvataggi_test):
        """Verifica che l'eliminazione dei salvataggi funzioni correttamente"""
        # Prima crea un salvataggio da eliminare
        session_response = post_with_json_header(f"{BASE_URL}/game/session/inizia")
        assert session_response.status_code == 200
        id_sessione = session_response.json()["id_sessione"]
        
        # Salva il gioco
        save_response = post_with_json_header(
            f"{BASE_URL}/game/save/salva",
            {"id_sessione": id_sessione, "nome_salvataggio": nome_salvataggio_test}
        )
        assert save_response.status_code == 200
        
        # Elimina il salvataggio
        delete_response = post_with_json_header(
            f"{BASE_URL}/game/save/elimina",
            {"nome_salvataggio": nome_salvataggio_test}
        )
        
        # Verifica che l'eliminazione sia andata a buon fine
        assert delete_response.status_code == 200
        delete_data = delete_response.json()
        assert delete_data["successo"] is True
        
        # Verifica che il salvataggio non appaia più nell'elenco
        list_response = requests.get(f"{BASE_URL}/game/save/elenco")
        list_data = list_response.json()
        assert nome_salvataggio_test not in [s["nome"] for s in list_data["salvataggi"]]
    
    def test_gestione_errori(self):
        """Verifica la corretta gestione degli errori"""
        # Prova a caricare un salvataggio che non esiste
        load_response = post_with_json_header(
            f"{BASE_URL}/game/save/carica",
            {"nome_salvataggio": "questo_salvataggio_non_esiste"}
        )
        
        # Verifica che restituisca un errore appropriato
        assert load_response.status_code in [404, 400]
        load_data = load_response.json()
        assert load_data["successo"] is False
        assert "errore" in load_data 