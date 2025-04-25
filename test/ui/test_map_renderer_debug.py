"""
Test di debug per il rendering della mappa.

Questo modulo contiene test specifici per diagnosticare problemi di rendering
della mappa con il componente Pixi.js nel frontend.
"""
import unittest
import os
import sys
import json
import time
import requests
from unittest.mock import MagicMock, patch

# Aggiunta del percorso relativo per importare moduli
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

class TestMapRendererDebug(unittest.TestCase):
    """Test di debug per il rendering della mappa."""
    
    def setUp(self):
        """Configura l'ambiente di test prima di ogni test."""
        self.server_url = "http://localhost:5000"
        
    def test_map_assets_availability(self):
        """Verifica la disponibilità delle risorse grafiche per la mappa."""
        # Lista delle risorse da verificare
        tile_assets = [
            "tiles/floor.png",
            "tiles/wall.png",
            "tiles/door.png",
            "tiles/grass.png",
            "tiles/water.png"
        ]
        
        entity_assets = [
            "entities/player.png",
            "entities/npc.png",
            "entities/enemy.png",
            "objects/chest.png",
            "objects/furniture.png"
        ]
        
        # Verifica ogni asset
        missing_assets = []
        
        for asset in tile_assets + entity_assets:
            asset_url = f"{self.server_url}/assets/file/{asset}"
            try:
                response = requests.head(asset_url)
                if response.status_code != 200:
                    missing_assets.append(asset)
                    print(f"Asset non disponibile: {asset} - Status code: {response.status_code}")
                else:
                    print(f"Asset disponibile: {asset}")
            except Exception as e:
                missing_assets.append(asset)
                print(f"Errore nel controllo dell'asset {asset}: {str(e)}")
        
        # Report finale
        if missing_assets:
            print(f"Asset mancanti: {missing_assets}")
        else:
            print("Tutti gli asset sono disponibili")
            
        # Test superato se tutti gli asset sono presenti
        self.assertEqual(len(missing_assets), 0, f"Asset mancanti: {missing_assets}")
    
    def test_map_data_structure(self):
        """Verifica la struttura dei dati della mappa mediante API REST."""
        try:
            # Ottieni i dati della mappa tramite API REST
            response = requests.get(f"{self.server_url}/api/map/current")
            
            # Verifica risposta HTTP
            self.assertEqual(response.status_code, 200, 
                            f"Errore API, status code: {response.status_code}")
            
            # Converti in JSON
            map_data = response.json()
            
            # Verifica la struttura dei dati
            self.assertIsInstance(map_data, dict, "I dati mappa non sono un dizionario")
            self.assertIn('id', map_data, "Manca l'id nella mappa")
            self.assertIn('width', map_data, "Manca il campo width nella mappa")
            self.assertIn('height', map_data, "Manca il campo height nella mappa")
            
            # Verifica layers
            self.assertIn('layers', map_data, "Manca il campo layers nella mappa")
            self.assertIsInstance(map_data['layers'], list, "Il campo layers non è una lista")
            
            # Verifica che ci sia almeno un layer
            if len(map_data['layers']) > 0:
                first_layer = map_data['layers'][0]
                self.assertIn('name', first_layer, "Manca il nome nel primo layer")
                self.assertIn('data', first_layer, "Manca il campo data nel primo layer")
                self.assertIsInstance(first_layer['data'], list, "Il campo data non è una lista")
                
                # Verifica dimensioni layer
                expected_size = map_data['width'] * map_data['height']
                actual_size = len(first_layer['data'])
                
                # Verifica match dimensioni
                self.assertEqual(actual_size, expected_size, 
                                f"Dimensione layer ({actual_size}) non corrisponde a width*height ({expected_size})")
                
                # Verifica valori tile
                tile_values = set(first_layer['data'])
                print(f"Valori tile presenti nel layer: {tile_values}")
                
            # Stampa statistiche utili
            print(f"Dimensioni mappa: {map_data['width']}x{map_data['height']}")
            print(f"Numero di layer: {len(map_data['layers'])}")
            
            # Verifica validità dei dati
            self.assertGreater(map_data['width'], 0, "Larghezza mappa non valida")
            self.assertGreater(map_data['height'], 0, "Altezza mappa non valida")
            
        except Exception as e:
            self.fail(f"Errore nel test della struttura mappa: {str(e)}")
    
    def test_entities_data(self):
        """Verifica la struttura dei dati delle entità mediante API REST."""
        try:
            # Ottieni i dati delle entità tramite API REST
            response = requests.get(f"{self.server_url}/api/entities")
            
            # Verifica risposta HTTP
            self.assertEqual(response.status_code, 200, 
                            f"Errore API, status code: {response.status_code}")
            
            # Converti in JSON
            entities_data = response.json()
            
            # Verifica la struttura dei dati
            self.assertIsInstance(entities_data, dict, "I dati entità non sono un dizionario")
            self.assertIn('entities', entities_data, "Manca il campo entities nei dati")
            self.assertIsInstance(entities_data['entities'], list, "Il campo entities non è una lista")
            
            # Stampa informazioni utili
            print(f"Numero di entità: {len(entities_data['entities'])}")
            
            # Analizza ogni entità
            for entity in entities_data['entities']:
                self.assertIn('id', entity, "Manca l'id in un'entità")
                self.assertIn('tipo', entity, "Manca il tipo in un'entità")
                self.assertIn('x', entity, "Manca la coordinata x in un'entità")
                self.assertIn('y', entity, "Manca la coordinata y in un'entità")
                
                # Verifica posizione valida
                self.assertIsInstance(entity['x'], int, "La coordinata x non è un intero")
                self.assertIsInstance(entity['y'], int, "La coordinata y non è un intero")
                
                # Stampa info sulle entità
                print(f"Entità {entity['id']} di tipo {entity['tipo']} in posizione ({entity['x']}, {entity['y']})")
                
        except Exception as e:
            self.fail(f"Errore nel test dei dati entità: {str(e)}")
    
    def test_pixi_viewport_configuration(self):
        """Verifica la configurazione del viewport Pixi.js tramite API diagnostica."""
        try:
            # Chiama l'API di diagnostica frontend
            response = requests.get(f"{self.server_url}/api/diagnostics/frontend")
            
            # Verifica risposta HTTP
            self.assertEqual(response.status_code, 200, 
                            f"Errore API diagnostica, status code: {response.status_code}")
            
            # Converti in JSON
            diagnostic_data = response.json()
            
            # Verifica dati di diagnostica del viewport
            self.assertIn('viewport', diagnostic_data, "Mancano dati diagnostici del viewport")
            viewport_data = diagnostic_data['viewport']
            
            # Verifica campi essenziali del viewport
            self.assertIn('width', viewport_data, "Manca la larghezza del viewport")
            self.assertIn('height', viewport_data, "Manca l'altezza del viewport")
            self.assertIn('scale', viewport_data, "Manca il fattore di scala del viewport")
            
            # Stampa informazioni utili
            print(f"Dimensioni viewport: {viewport_data['width']}x{viewport_data['height']}")
            print(f"Scala viewport: {viewport_data['scale']}")
            
            # Verifica valori sensati
            self.assertGreater(viewport_data['width'], 0, "Larghezza viewport non valida")
            self.assertGreater(viewport_data['height'], 0, "Altezza viewport non valida")
            self.assertGreater(viewport_data['scale'], 0, "Scala viewport non valida")
            
        except requests.exceptions.ConnectionError:
            print("API di diagnostica frontend non disponibile")
            print("NOTA: Questa API potrebbe essere mancante e richiedere implementazione")
        except Exception as e:
            self.fail(f"Errore nel test della configurazione viewport: {str(e)}")
    
    def test_texture_cache(self):
        """Verifica lo stato della cache delle texture tramite API diagnostica."""
        try:
            # Chiama l'API di diagnostica frontend
            response = requests.get(f"{self.server_url}/api/diagnostics/textures")
            
            # Verifica risposta HTTP
            self.assertEqual(response.status_code, 200, 
                            f"Errore API diagnostica texture, status code: {response.status_code}")
            
            # Converti in JSON
            texture_data = response.json()
            
            # Verifica dati sulla cache delle texture
            self.assertIn('cached_textures', texture_data, "Mancano dati sulla cache delle texture")
            cached_textures = texture_data['cached_textures']
            
            # Verifica che ci siano texture in cache
            self.assertGreater(len(cached_textures), 0, "Nessuna texture in cache")
            
            # Stampa informazioni utili
            print(f"Numero di texture in cache: {len(cached_textures)}")
            for texture in cached_textures:
                print(f"Texture: {texture['url']} - Dimensioni: {texture['width']}x{texture['height']}")
            
        except requests.exceptions.ConnectionError:
            print("API di diagnostica texture non disponibile")
            print("NOTA: Questa API potrebbe essere mancante e richiedere implementazione")
        except Exception as e:
            self.fail(f"Errore nel test della cache texture: {str(e)}")

# Se eseguito direttamente
if __name__ == '__main__':
    unittest.main() 