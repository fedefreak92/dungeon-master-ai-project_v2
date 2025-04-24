from locust import HttpUser, task, between
import json
import random

class RPGGameUser(HttpUser):
    """
    Classe per simulare utenti che interagiscono con il gioco RPG
    """
    # Attendi tra 1 e 5 secondi tra le richieste
    wait_time = between(1, 5)
    
    def on_start(self):
        """
        Metodo chiamato quando un utente virtuale inizia
        Effettua il login o inizializza altre variabili
        """
        # Simulazione di un nome utente casuale
        self.username = f"test_user_{random.randint(1000, 9999)}"
        self.giocatore_id = None
        
        # Connessione WebSocket
        self.client.get("/")
    
    @task(1)
    def visit_homepage(self):
        """
        Visita la home page del gioco
        """
        self.client.get("/")
    
    @task(3)
    def create_new_character(self):
        """
        Crea un nuovo personaggio
        """
        classes = ["Guerriero", "Mago", "Ladro", "Chierico"]
        character_data = {
            "nome": f"Eroe_{random.randint(100, 999)}",
            "classe": random.choice(classes)
        }
        
        response = self.client.post("/api/character/create", 
                                   json=character_data)
        
        if response.status_code == 200:
            result = response.json()
            if "id" in result:
                self.giocatore_id = result["id"]
    
    @task(5)
    def move_player(self):
        """
        Sposta il giocatore in una direzione casuale
        """
        if not self.giocatore_id:
            return
            
        directions = ["nord", "sud", "est", "ovest"]
        move_data = {
            "giocatore_id": self.giocatore_id,
            "direzione": random.choice(directions)
        }
        
        self.client.post("/api/player/move", json=move_data)
    
    @task(2)
    def interact_with_npc(self):
        """
        Interagisce con un NPC casuale
        """
        if not self.giocatore_id:
            return
            
        npcs = ["Durnan", "Elminster", "Mirt", "Mercante"]
        interaction_data = {
            "giocatore_id": self.giocatore_id,
            "npc": random.choice(npcs),
            "azione": "parla"
        }
        
        self.client.post("/api/npc/interact", json=interaction_data)
    
    @task(2)
    def check_inventory(self):
        """
        Controlla l'inventario del giocatore
        """
        if not self.giocatore_id:
            return
            
        self.client.get(f"/api/player/{self.giocatore_id}/inventory")
    
    @task(1)
    def save_game(self):
        """
        Salva lo stato del gioco
        """
        if not self.giocatore_id:
            return
            
        save_data = {
            "giocatore_id": self.giocatore_id,
            "nome_salvataggio": f"save_{self.username}"
        }
        
        self.client.post("/api/game/save", json=save_data)
    
    @task(1)
    def load_game(self):
        """
        Carica uno stato di gioco salvato
        """
        if not self.giocatore_id:
            return
            
        load_data = {
            "nome_salvataggio": f"save_{self.username}"
        }
        
        self.client.post("/api/game/load", json=load_data)
    
    @task(3)
    def enter_combat(self):
        """
        Entra in combattimento con un nemico casuale
        """
        if not self.giocatore_id:
            return
            
        enemies = ["Goblin", "Orco", "Lupo", "Bandito", "Scheletro"]
        combat_data = {
            "giocatore_id": self.giocatore_id,
            "nemico": random.choice(enemies)
        }
        
        self.client.post("/api/combat/start", json=combat_data)
    
    @task(4)
    def combat_action(self):
        """
        Esegue un'azione di combattimento
        """
        if not self.giocatore_id:
            return
            
        actions = ["attacca", "difendi", "abilita", "oggetto", "fuggi"]
        action_data = {
            "giocatore_id": self.giocatore_id,
            "azione": random.choice(actions),
            "bersaglio": "nemico_1"
        }
        
        self.client.post("/api/combat/action", json=action_data)

# Per eseguire il test:
# locust -f test/carico/test_carico_server.py --host=http://localhost:5000
# Poi apri http://localhost:8089 nel browser 