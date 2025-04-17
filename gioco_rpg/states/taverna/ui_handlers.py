class TavernaUI:
    def __init__(self, stato_taverna):
        self.stato = stato_taverna
        self.ui_aggiornata = False
        
    def mostra_benvenuto(self, gioco):
        """Mostra il messaggio di benvenuto e inizializza la taverna"""
        gioco.io.mostra_dialogo(
            "Benvenuto alla Taverna", 
            f"Benvenuto {gioco.giocatore.nome}, sei appena arrivato nella Taverna Il Portale Spalancato a Waterdeep. Sei di ritorno da un lungo viaggio che ti ha permesso di ottenere molti tesori ma anche molte cicatrici. Entri con passo svelto e ti dirigi verso la tua prossima avventura",
            ["Continua"]
        )
        
        # Effetto audio di benvenuto
        gioco.io.play_sound({
            "sound_id": "tavern_enter",
            "volume": 0.7
        })
        
        # Imposta il menu attivo
        self.stato.menu_attivo = "benvenuto"
        
        # Gestione della conferma dialogo di benvenuto
        self._gestisci_conferma_benvenuto(gioco)
        
    def _gestisci_conferma_benvenuto(self, gioco):
        """Gestisce la conferma del dialogo di benvenuto"""
        original_handler = getattr(self.stato, "_handle_dialog_choice", None)
        
        def welcome_handler(event):
            if not hasattr(event, "data") or not event.data:
                return
                
            choice = event.data.get("choice")
            if not choice:
                return
            
            # Imposta valori iniziali
            self.stato.prima_visita = False
            
            # Imposta la posizione iniziale del giocatore sulla mappa della taverna
            self._inizializza_mappa_giocatore(gioco)
            
            # Mostra il menu principale
            self.stato.menu_handler.mostra_menu_principale(gioco)
            
            # Ripristina l'handler originale
            if original_handler:
                self.stato._handle_dialog_choice = original_handler
        
        # Imposta l'handler temporaneo
        self.stato._handle_dialog_choice = welcome_handler
        
    def _inizializza_mappa_giocatore(self, gioco):
        """Inizializza la mappa e posiziona il giocatore"""
        mappa = gioco.gestore_mappe.ottieni_mappa("taverna")
        if mappa:
            gioco.gestore_mappe.imposta_mappa_attuale("taverna")
            x, y = mappa.pos_iniziale_giocatore
            gioco.giocatore.imposta_posizione("taverna", x, y)
            # Popola la mappa con gli oggetti interattivi e gli NPG
            gioco.gestore_mappe.trasferisci_oggetti_da_stato("taverna", self.stato)
    
    def aggiorna_renderer(self, gioco):
        """Aggiorna il renderer con gli elementi UI della taverna"""
        # Implementazione dell'aggiornamento del renderer
        pass
        
    def mostra_notifica_salvataggio(self, gioco):
        """Mostra una notifica di salvataggio completato"""
        # Effetto di transizione
        gioco.io.mostra_transizione("fade", 0.3)
        
        # Effetto audio per il salvataggio
        gioco.io.play_sound({
            "sound_id": "save_game",
            "volume": 0.6
        })
        
        # Mostra un'animazione di salvataggio
        gioco.io.mostra_ui_elemento({
            "type": "sprite",
            "id": "saving_icon",
            "image": "save_icon",
            "x": 400,
            "y": 300,
            "scale": 1.0,
            "animation": {
                "type": "scale",
                "from": 0.5,
                "to": 1.0,
                "duration": 0.5
            },
            "z_index": 10
        })
        
        # Rimuovi l'animazione dopo 1 secondo
        gioco.io.imposta_timer("rimuovi_icona_salvataggio", 1.0, lambda: gioco.io.rimuovi_ui_elemento("saving_icon"))
        
        # Mostra un messaggio di conferma
        gioco.io.mostra_dialogo("Salvataggio", "Partita salvata con successo!", ["Continua"])
        
        # Imposta il menu attivo per gestire la conferma del salvataggio
        self.stato.menu_attivo = "salvataggio_completato"
        
        # Aggiorna l'handler per gestire la conferma di salvataggio
        self._gestisci_conferma_salvataggio(gioco)
        
    def _gestisci_conferma_salvataggio(self, gioco):
        """Gestisce la conferma del salvataggio"""
        original_handler = getattr(self.stato, "_handle_dialog_choice", None)
        
        def save_confirmation_handler(event):
            if not hasattr(event, "data") or not event.data:
                return
                
            # Ripristina l'handler originale
            self.stato._handle_dialog_choice = original_handler
                
            # Effetto audio di conferma
            gioco.io.play_sound({
                "sound_id": "menu_confirm",
                "volume": 0.5
            })
                
            # Torna al menu principale
            self.stato.menu_handler.mostra_menu_principale(gioco)
        
        # Sostituisci temporaneamente l'handler
        self.stato._handle_dialog_choice = save_confirmation_handler 