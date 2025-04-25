class UICombattimento:
    """Classe che gestisce l'interfaccia utente del combattimento"""
    
    def __init__(self, stato_combattimento):
        """
        Inizializza il gestore dell'interfaccia
        
        Args:
            stato_combattimento: Riferimento allo stato di combattimento
        """
        self.stato = stato_combattimento
    
    def aggiorna_renderer(self, gioco):
        """
        Aggiorna il renderer per il combattimento
        
        Args:
            gioco: L'istanza del gioco
        """
        # Ottieni il renderer
        renderer = gioco.io.renderer
        
        # Pulisci lo schermo
        renderer.clear_screen()
        
        # Titolo del combattimento
        renderer.draw_ui_element({
            "type": "text",
            "id": "titolo_combattimento",
            "text": "COMBATTIMENTO", 
            "x": 400,
            "y": 50,
            "font_size": 36,
            "color": "#FF0000",
            "anchor": "center"
        })
        
        # Nome del nemico
        renderer.draw_ui_element({
            "type": "text",
            "id": "nome_nemico",
            "text": self.stato.avversario.nome,
            "x": 600,
            "y": 100,
            "font_size": 24,
            "color": "#FF0000",
            "anchor": "center"
        })
        
        # Nome del giocatore
        renderer.draw_ui_element({
            "type": "text",
            "id": "nome_giocatore",
            "text": gioco.giocatore.nome,
            "x": 200,
            "y": 100,
            "font_size": 24,
            "color": "#00FF00",
            "anchor": "center"
        })
        
        # Informazioni turno
        renderer.draw_ui_element({
            "type": "text",
            "id": "info_turno",
            "text": f"Turno: {self.stato.turno}", 
            "x": 400,
            "y": 20,
            "font_size": 16,
            "color": "#FFFFFF",
            "anchor": "center"
        })
        
        # Presentazione finale
        renderer.present()
    
    def mostra_interfaccia_combattimento(self, gioco):
        """
        Mostra l'interfaccia grafica del combattimento
        
        Args:
            gioco: L'istanza del gioco
        """
        giocatore = gioco.giocatore
        
        # Aggiungi elementi UI per il combattimento
        gioco.io.mostra_ui_elemento({
            "type": "background",
            "id": "sfondo_combattimento",
            "image": "battle_background",
            "z_index": 0
        })
        
        # Mostra il giocatore
        gioco.io.mostra_ui_elemento({
            "type": "character",
            "id": "giocatore_sprite",
            "image": "player_battle",
            "x": 200,
            "y": 350,
            "scale": 1.0,
            "z_index": 2
        })
        
        # Mostra l'avversario
        tipo_avversario = "nemico" if self.stato.nemico else "npg"
        immagine_avversario = self.stato.avversario.immagine if hasattr(self.stato.avversario, "immagine") else f"{tipo_avversario}_default"
        
        gioco.io.mostra_ui_elemento({
            "type": "character",
            "id": "avversario_sprite",
            "image": immagine_avversario,
            "x": 600,
            "y": 350,
            "scale": 1.0,
            "z_index": 2
        })
        
        # Mostra le barre HP
        self.aggiorna_barre_hp(gioco)
        
        # Mostra il nome dell'avversario
        gioco.io.mostra_ui_elemento({
            "type": "text",
            "id": "nome_avversario",
            "text": self.stato.avversario.nome,
            "x": 600,
            "y": 280,
            "font_size": 24,
            "centered": True,
            "color": "#FF3333"
        })
    
    def aggiorna_barre_hp(self, gioco):
        """
        Aggiorna le barre della salute
        
        Args:
            gioco: L'istanza del gioco
        """
        giocatore = gioco.giocatore
        
        # Calcola percentuali di salute
        hp_perc_giocatore = (giocatore.hp / giocatore.hp_max) * 100
        hp_perc_avversario = (self.stato.avversario.hp / self.stato.avversario.hp_max) * 100
        
        # Colori delle barre in base alla salute
        colore_hp_giocatore = "#00FF00" if hp_perc_giocatore > 50 else "#FFFF00" if hp_perc_giocatore > 25 else "#FF0000"
        colore_hp_avversario = "#00FF00" if hp_perc_avversario > 50 else "#FFFF00" if hp_perc_avversario > 25 else "#FF0000"
        
        # Aggiorna barra HP giocatore
        gioco.io.mostra_ui_elemento({
            "type": "progress_bar",
            "id": "barra_hp_giocatore",
            "x": 200,
            "y": 300,
            "width": 200,
            "height": 20,
            "value": hp_perc_giocatore,
            "max_value": 100,
            "color": colore_hp_giocatore,
            "text": f"HP: {giocatore.hp}/{giocatore.hp_max}",
            "z_index": 3
        })
        
        # Aggiorna barra HP avversario
        gioco.io.mostra_ui_elemento({
            "type": "progress_bar",
            "id": "barra_hp_avversario",
            "x": 600,
            "y": 300,
            "width": 200,
            "height": 20,
            "value": hp_perc_avversario,
            "max_value": 100,
            "color": colore_hp_avversario,
            "text": f"HP: {self.stato.avversario.hp}/{self.stato.avversario.hp_max}",
            "z_index": 3
        })
    
    def mostra_menu_scelta(self, gioco):
        """
        Mostra il menu delle azioni di combattimento
        
        Args:
            gioco: L'istanza del gioco
        """
        # Mostra un dialogo con le opzioni di combattimento
        gioco.io.mostra_dialogo("Combattimento", "Cosa vuoi fare?", [
            "Attacca",
            "Usa oggetto",
            "Cambia equipaggiamento",
            "Fuggi"
        ]) 