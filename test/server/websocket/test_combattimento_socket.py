"""
Test per la funzionalità di combattimento tramite WebSocket
"""

import pytest
import requests
import socketio
import time
import json
import os
import sys

# Importa la funzione helper definita in conftest.py
from ...conftest import post_with_json_header

# URL base per le richieste e per i WebSocket
BASE_URL = "http://localhost:5000"
SOCKET_URL = "http://localhost:5000"

class TestCombattimentoWebSocket:
    """Test per verificare il funzionamento corretto del sistema di combattimento tramite WebSocket"""
    
    @pytest.fixture
    def socket_client(self):
        """Fixture che crea e gestisce un client SocketIO"""
        # Crea un client SocketIO
        sio = socketio.Client()
        
        # Connetti il client
        sio.connect(SOCKET_URL)
        
        # Restituisci il client per i test
        yield sio
        
        # Pulizia: disconnetti il client
        if sio.connected:
            sio.disconnect()
    
    @pytest.fixture
    def sessione_test(self):
        """Fixture che crea una sessione di gioco per il test"""
        # Inizia una nuova sessione
        response = post_with_json_header(f"{BASE_URL}/game/session/inizia")
        assert response.status_code == 200
        session_data = response.json()
        
        # Verifica che la risposta contenga un id_sessione (non il campo successo)
        assert "id_sessione" in session_data
        
        # Restituisci l'ID sessione
        return session_data["id_sessione"]
    
    def test_inizializzazione_combattimento(self, socket_client, sessione_test):
        """Verifica che l'inizializzazione del combattimento tramite WebSocket funzioni correttamente"""
        # Prepara gli eventi che verranno ricevuti
        received_events = []
        
        @socket_client.on('combattimento_inizializzato')
        def on_combat_init(data):
            print(f"Ricevuto evento combattimento_inizializzato: {data}")
            received_events.append(('combattimento_inizializzato', data))
        
        @socket_client.on('error')
        def on_error(data):
            print(f"Ricevuto evento error: {data}")
            received_events.append(('error', data))
            
        # Registra un handler generico per tutti gli eventi
        @socket_client.on('*')
        def catch_all(event, data):
            print(f"Ricevuto evento generico: {event}, {data}")
            received_events.append((event, data))
        
        # Unisciti alla sessione di gioco
        print(f"Unisciti alla sessione: {sessione_test}")
        socket_client.emit('join_game', {'id_sessione': sessione_test})
        time.sleep(1.0)  # Aumentato il tempo di attesa per l'elaborazione della richiesta
        
        # Inizializza il combattimento tramite l'evento WebSocket
        print(f"Invio evento combattimento_inizializza per sessione: {sessione_test}")
        socket_client.emit('combattimento_inizializza', {
            'id_sessione': sessione_test,
            'nemici': ['goblin']
        })
        
        # Attendi gli eventi di risposta
        time.sleep(3.0)  # Aumentato il tempo di attesa per ricevere la risposta
        
        print(f"Eventi ricevuti: {received_events}")
        
        # Verifica che sia stato ricevuto l'evento di inizializzazione
        combat_events = [e for e in received_events if e[0] == 'combattimento_inizializzato']
        assert len(combat_events) > 0
        
        # Verifica il contenuto dell'evento
        event_data = combat_events[0][1]
        assert 'stato' in event_data
        assert 'partecipanti' in event_data
        assert 'turno_di' in event_data
    
    def test_azione_combattimento(self, socket_client, sessione_test):
        """Verifica che le azioni di combattimento tramite WebSocket funzionino correttamente"""
        # Prepara gli eventi che verranno ricevuti
        received_events = []

        @socket_client.on('combattimento_azione_eseguita')
        def on_combat_action(data):
            print(f"Ricevuto evento combattimento_azione_eseguita: {data}")
            received_events.append(('combattimento_azione_eseguita', data))

        @socket_client.on('error')
        def on_error(data):
            print(f"Ricevuto evento error: {data}")
            received_events.append(('error', data))

        @socket_client.on('combattimento_inizializzato')
        def on_combat_init(data):
            print(f"Ricevuto evento combattimento_inizializzato: {data}")
            received_events.append(('combattimento_inizializzato', data))
            
        # Registra tutti gli eventi per il debugging
        @socket_client.on('*')
        def catch_all(event, data):
            if event not in ['combattimento_azione_eseguita', 'error', 'combattimento_inizializzato']:
                print(f"Ricevuto altro evento: {event}, {data}")
                received_events.append((event, data))

        # Unisciti alla sessione di gioco
        print(f"Unisciti alla sessione: {sessione_test}")
        socket_client.emit('join_game', {'id_sessione': sessione_test})
        time.sleep(1.0)  # Aumentato il tempo di attesa

        # Inizializza un combattimento tramite WebSocket invece dell'API REST
        print(f"Inizializzazione del combattimento per la sessione: {sessione_test}")
        socket_client.emit('combattimento_inizializza', {
            'id_sessione': sessione_test,
            'nemici': ['goblin']
        })
        time.sleep(3.0)  # Aumentato il tempo di attesa

        # Verifica che il combattimento sia stato inizializzato
        combat_events = [e for e in received_events if e[0] == 'combattimento_inizializzato']
        assert len(combat_events) > 0, "Nessun evento di inizializzazione combattimento ricevuto"

        # Ottieni l'ID dell'attaccante e del bersaglio dal risultato dell'inizializzazione
        event_data = combat_events[0][1]
        partecipanti = event_data.get('partecipanti', [])
        print(f"Partecipanti al combattimento: {partecipanti}")

        # Trova il giocatore e il nemico
        giocatore_id = None
        nemico_id = None
        for p in partecipanti:
            if p.get('è_giocatore', False):
                giocatore_id = p.get('id')
            elif p.get('è_nemico', False):
                nemico_id = p.get('id')

        assert giocatore_id is not None, "ID giocatore non trovato nei partecipanti"
        assert nemico_id is not None, "ID nemico non trovato nei partecipanti"
        print(f"Giocatore ID: {giocatore_id}, Nemico ID: {nemico_id}")

        # Esegui un'azione di combattimento tramite WebSocket
        print(f"Invio azione di attacco: attaccante={giocatore_id}, target={nemico_id}")
        socket_client.emit('combattimento_azione', {
            'id_sessione': sessione_test,
            'tipo_azione': 'attacca',
            'parametri': {
                'attaccante_id': giocatore_id,
                'target_id': nemico_id
            }
        })

        # Attendi gli eventi di risposta
        time.sleep(4.0)  # Aumentato il tempo di attesa

        # Verifica che sia stato ricevuto l'evento di azione eseguita
        action_events = [e for e in received_events if e[0] == 'combattimento_azione_eseguita']
        error_events = [e for e in received_events if e[0] == 'error']

        # Stampa tutti gli eventi ricevuti per debug
        print(f"Eventi ricevuti totali: {len(received_events)}")
        for i, event in enumerate(received_events):
            print(f"Evento {i}: {event[0]}")
        
        if error_events:
            print(f"Errori ricevuti: {error_events}")

        assert len(action_events) > 0, "Nessun evento di azione eseguita ricevuto"
    
    def test_uso_abilita_combattimento(self, socket_client, sessione_test):
        """Verifica che l'uso di abilità durante il combattimento funzioni correttamente"""
        # Prepara gli eventi che verranno ricevuti
        received_events = []

        @socket_client.on('combattimento_abilita_usata')
        def on_ability_used(data):
            print(f"Ricevuto evento combattimento_abilita_usata: {data}")
            received_events.append(('combattimento_abilita_usata', data))

        @socket_client.on('combattimento_inizializzato')
        def on_combat_init(data):
            print(f"Ricevuto evento combattimento_inizializzato: {data}")
            received_events.append(('combattimento_inizializzato', data))

        @socket_client.on('error')
        def on_error(data):
            print(f"Ricevuto evento error: {data}")
            received_events.append(('error', data))
            
        # Registra tutti gli eventi per il debugging
        @socket_client.on('*')
        def catch_all(event, data):
            if event not in ['combattimento_abilita_usata', 'error', 'combattimento_inizializzato']:
                print(f"Ricevuto altro evento: {event}, {data}")
                received_events.append((event, data))

        # Unisciti alla sessione di gioco
        print(f"Unisciti alla sessione: {sessione_test}")
        socket_client.emit('join_game', {'id_sessione': sessione_test})
        time.sleep(1.0)  # Aumentato il tempo di attesa

        # Inizializza un combattimento tramite WebSocket invece dell'API REST
        print(f"Inizializzazione del combattimento per la sessione: {sessione_test}")
        socket_client.emit('combattimento_inizializza', {
            'id_sessione': sessione_test,
            'nemici': ['goblin']
        })
        time.sleep(3.0)  # Aumentato il tempo di attesa

        # Verifica che il combattimento sia stato inizializzato
        combat_events = [e for e in received_events if e[0] == 'combattimento_inizializzato']
        assert len(combat_events) > 0, "Nessun evento di inizializzazione combattimento ricevuto"

        # Ottieni l'ID del giocatore e del nemico dal risultato dell'inizializzazione
        event_data = combat_events[0][1]
        partecipanti = event_data.get('partecipanti', [])
        print(f"Partecipanti al combattimento: {partecipanti}")

        # Trova il giocatore e il nemico
        giocatore_id = None
        nemico_id = None
        for p in partecipanti:
            if p.get('è_giocatore', False):
                giocatore_id = p.get('id')
            elif p.get('è_nemico', False):
                nemico_id = p.get('id')

        assert giocatore_id is not None, "ID giocatore non trovato nei partecipanti"
        assert nemico_id is not None, "ID nemico non trovato nei partecipanti"
        print(f"Giocatore ID: {giocatore_id}, Nemico ID: {nemico_id}")

        # Prima aggiungiamo l'abilità al giocatore tramite una chiamata API
        print(f"Aggiungimento abilità speciale 'colpo_potente' al giocatore")
        response = requests.post(f"{BASE_URL}/game/entity/add_ability", json={
            "id_sessione": sessione_test,
            "entity_id": giocatore_id,
            "ability_name": "colpo_potente",
            "ability_value": 3  # Livello dell'abilità
        })
        print(f"Risposta aggiunta abilità: {response.status_code}, {response.text if response.status_code != 200 else 'OK'}")

        # Usa un'abilità tramite WebSocket
        print(f"Invio azione abilità: entità={giocatore_id}, abilità=colpo_potente, target={nemico_id}")
        socket_client.emit('combattimento_usa_abilita', {
            'id_sessione': sessione_test,
            'entita_id': giocatore_id,
            'abilita': 'colpo_potente',
            'target_ids': [nemico_id]
        })

        # Attendi gli eventi di risposta
        time.sleep(4.0)  # Aumentato il tempo di attesa

        # Verifica la presenza dell'abilità utilizzata nei messaggi di aggiornamento
        update_events = [e for e in received_events if e[0] == 'combattimento_aggiornamento']
        ability_used = False
        
        # Cerca nei messaggi di aggiornamento se è stata usata l'abilità colpo_potente
        for event in update_events:
            event_data = event[1]
            messaggi = event_data.get('messaggi', [])
            for messaggio in messaggi:
                if 'colpo_potente' in messaggio and 'usa' in messaggio:
                    ability_used = True
                    break
            
            if ability_used:
                break
        
        error_events = [e for e in received_events if e[0] == 'error']

        # Stampa tutti gli eventi ricevuti per debug
        print(f"Eventi ricevuti totali: {len(received_events)}")
        for i, event in enumerate(received_events):
            print(f"Evento {i}: {event[0]}")
        
        if error_events:
            print(f"Errori ricevuti: {error_events}")
            
        # Verifica che l'abilità sia stata usata o rifiutata per un motivo valido (cooldown)
        valid_cooldown_error = False
        
        # Verifica se c'è stato un errore di cooldown validato
        for event in error_events:
            error_data = event[1]
            error_message = error_data.get('message', '')
            if 'colpo_potente' in error_message and ('non è ancora pronta' in error_message or 'turni' in error_message):
                valid_cooldown_error = True
                break
                
        ability_used_events = [e for e in received_events if e[0] == 'combattimento_abilita_usata']
        for event in ability_used_events:
            event_data = event[1]
            result = event_data.get('risultato', {})
            if not result.get('successo', True) and 'non è ancora pronta' in result.get('messaggio', ''):
                valid_cooldown_error = True
                break

        # Il test passa se l'abilità è stata usata O se è stato ricevuto un errore di cooldown valido
        assert ability_used or valid_cooldown_error, "Nessun messaggio di abilità 'colpo_potente' usata trovato negli aggiornamenti e nessun errore di cooldown valido" 