"""
Test di integrazione dell'interfaccia utente web.
Verifica le interazioni API di base e la struttura delle risposte.
"""

import unittest
import json
import logging
import requests
import sys
import os
import time
import pytest
from urllib.parse import urljoin

# Configura il logging per il debug
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Modifica il percorso di sistema per l'importazione
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Definizione della classe di test
@pytest.mark.usefixtures("flask_server")
class TestUIInteractions(unittest.TestCase):
    """Test per verificare le interazioni dell'interfaccia utente con il backend."""

    @classmethod
    def setUpClass(cls):
        """Configura l'ambiente per i test."""
        # Usa un URL statico come base per i test
        cls.base_url = "http://localhost:5000"
        
        # Verifica che il server sia in esecuzione
        try:
            response = requests.get(cls.base_url)
            if response.status_code != 200:
                logger.warning(f"Il server restituisce status code {response.status_code}. Alcuni test potrebbero fallire.")
        except requests.exceptions.ConnectionError:
            logger.warning("Impossibile connettersi al server. Assicurati che sia in esecuzione prima di eseguire i test.")
    
    def get_api_url(self, endpoint):
        """Costruisce un URL API completo a partire da un endpoint relativo."""
        return urljoin(self.base_url + "/api/", endpoint)
    
    def test_home_page(self):
        """Verifica che la home page sia accessibile."""
        try:
            response = requests.get(self.base_url)
            self.assertEqual(response.status_code, 200, "La home page dovrebbe restituire uno stato 200")
            logger.info("Test home page completato con successo")
        except Exception as e:
            logger.error(f"Errore nel test home page: {e}")
            self.fail(f"Eccezione non prevista: {e}")
    
    def test_health_endpoint(self):
        """Verifica che l'endpoint /api/health restituisca lo stato corretto."""
        try:
            url = self.get_api_url("health")
            logger.debug(f"Testando health endpoint all'URL: {url}")
            response = requests.get(url)
            self.assertEqual(response.status_code, 200, "L'endpoint health dovrebbe restituire uno stato 200")
            
            # Verifica che il contenuto JSON sia valido con struttura corretta
            data = response.json()
            self.assertIn("status", data, "La risposta dovrebbe contenere il campo 'status'")
            self.assertEqual(data["status"], "ok", "Lo status dovrebbe essere 'ok'")
            
            logger.info("Test health endpoint completato con successo")
        except requests.exceptions.ConnectionError:
            logger.error("Endpoint health non raggiungibile")
            self.fail("Impossibile connettersi all'endpoint health - il server è avviato?")
        except Exception as e:
            logger.error(f"Errore nel test health endpoint: {e}")
            self.fail(f"Eccezione non prevista: {e}")
    
    def test_ping_endpoint(self):
        """Verifica che l'endpoint /ping restituisca la risposta corretta."""
        try:
            url = urljoin(self.base_url, "ping")
            logger.debug(f"Testando ping endpoint all'URL: {url}")
            response = requests.get(url)
            self.assertEqual(response.status_code, 200, "L'endpoint ping dovrebbe restituire uno stato 200")
            
            # Verifica che il contenuto JSON sia valido con struttura corretta
            data = response.json()
            self.assertIn("message", data, "La risposta dovrebbe contenere il campo 'message'")
            self.assertEqual(data["message"], "pong", "Il messaggio dovrebbe essere 'pong'")
            
            logger.info("Test ping endpoint completato con successo")
        except requests.exceptions.ConnectionError:
            logger.error("Endpoint ping non raggiungibile")
            self.fail("Impossibile connettersi all'endpoint ping - il server è avviato?")
        except Exception as e:
            logger.error(f"Errore nel test ping endpoint: {e}")
            self.fail(f"Eccezione non prevista: {e}")
    
    def test_entities_endpoint(self):
        """Verifica che l'endpoint /api/entities restituisca la struttura corretta."""
        try:
            url = self.get_api_url("entities")
            logger.debug(f"Testando entities endpoint all'URL: {url}")
            response = requests.get(url)
            self.assertEqual(response.status_code, 200, "L'endpoint entities dovrebbe restituire uno stato 200")
            
            # Verifica che il contenuto JSON sia valido con struttura corretta
            data = response.json()
            self.assertIn("entities", data, "La risposta dovrebbe contenere il campo 'entities'")
            self.assertIsInstance(data["entities"], list, "Il campo 'entities' dovrebbe essere una lista")
            
            # Se ci sono entità, verifica la struttura della prima
            if data["entities"]:
                entity = data["entities"][0]
                self.assertIn("id", entity, "Ogni entità dovrebbe avere un campo 'id'")
                
                # Adatta il test alle possibili strutture di risposta:
                # Verifica tipo entità e posizione (potrebbero essere chiamati in modo diverso)
                has_type = "tipo" in entity or "type" in entity
                has_position = "position" in entity or ("x" in entity and "y" in entity)
                
                self.assertTrue(has_type, "Ogni entità dovrebbe avere un campo tipo/type")
                self.assertTrue(has_position, "Ogni entità dovrebbe avere informazioni sulla posizione")
            
            logger.info("Test entities endpoint completato con successo")
        except requests.exceptions.ConnectionError:
            logger.error("Endpoint entities non raggiungibile")
            self.fail("Impossibile connettersi all'endpoint entities - il server è avviato?")
        except Exception as e:
            logger.error(f"Errore nel test entities endpoint: {e}")
            self.fail(f"Eccezione non prevista: {e}")
    
    def test_current_map_endpoint(self):
        """Verifica che l'endpoint /api/map/current restituisca la struttura corretta."""
        try:
            url = self.get_api_url("map/current")
            logger.debug(f"Testando current map endpoint all'URL: {url}")
            response = requests.get(url)
            self.assertEqual(response.status_code, 200, "L'endpoint current_map dovrebbe restituire uno stato 200")
            
            # Verifica che il contenuto JSON sia valido con struttura corretta
            data = response.json()
            
            # Adatta il test alle possibili strutture della risposta
            # Potrebbe esserci un campo 'map' o i dati della mappa direttamente nella radice
            if "map" in data:
                map_data = data["map"]
            else:
                map_data = data
            
            # Verifica i campi obbligatori della mappa (possono avere nomi diversi)
            has_id = "id" in map_data or "name" in map_data
            has_layers = "layers" in map_data
            
            self.assertTrue(has_id, "La mappa dovrebbe avere un identificatore (id o name)")
            self.assertTrue(has_layers, "La mappa dovrebbe avere un campo 'layers'")
            
            logger.info("Test current_map endpoint completato con successo")
        except requests.exceptions.ConnectionError:
            logger.error("Endpoint current_map non raggiungibile")
            self.fail("Impossibile connettersi all'endpoint current_map - il server è avviato?")
        except Exception as e:
            logger.error(f"Errore nel test current_map endpoint: {e}")
            self.fail(f"Eccezione non prevista: {e}")
    
    def test_diagnostics_endpoint(self):
        """Verifica che l'endpoint /api/diagnostics/frontend restituisca la struttura corretta."""
        try:
            url = self.get_api_url("diagnostics/frontend")
            logger.debug(f"Testando diagnostics endpoint all'URL: {url}")
            response = requests.get(url)
            self.assertEqual(response.status_code, 200, "L'endpoint diagnostics dovrebbe restituire uno stato 200")
            
            # Verifica che il contenuto JSON sia valido
            data = response.json()
            
            # Considera più formati possibili per la risposta
            # La risposta potrebbe avere diversi campi a seconda dell'implementazione
            self.assertIsInstance(data, dict, "La risposta dovrebbe essere un oggetto JSON")
            self.assertTrue(len(data) > 0, "La risposta non dovrebbe essere vuota")
            
            logger.info("Test diagnostics endpoint completato con successo")
        except requests.exceptions.ConnectionError:
            logger.error("Endpoint diagnostics non raggiungibile")
            self.fail("Impossibile connettersi all'endpoint diagnostics - il server è avviato?")
        except Exception as e:
            logger.error(f"Errore nel test diagnostics endpoint: {e}")
            self.fail(f"Eccezione non prevista: {e}")

if __name__ == '__main__':
    unittest.main() 