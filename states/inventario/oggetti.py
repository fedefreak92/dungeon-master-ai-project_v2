from states.inventario.filtri import FiltriInventario

class GestoreOggetti:
    """
    Classe che gestisce le operazioni sugli oggetti dell'inventario.
    Gestisce l'uso, l'equipaggiamento, la rimozione e l'esame degli oggetti.
    """
    
    def __init__(self, inventario_state):
        """
        Inizializza il gestore oggetti.
        
        Args:
            inventario_state: L'istanza dello stato inventario
        """
        self.inventario_state = inventario_state
        
    def usa_oggetto_selezionato(self, gioco, oggetto):
        """
        Usa l'oggetto selezionato.
        
        Args:
            gioco: L'istanza del gioco
            oggetto: L'oggetto da usare
        """
        if isinstance(oggetto, str):
            gioco.io.mostra_messaggio(f"Non puoi usare {oggetto} direttamente.")
            gioco.io.mostra_dialogo("Attenzione", f"Non puoi usare {oggetto} direttamente.", ["Continua"])
            self.inventario_state.fase = "menu_principale"
            self.inventario_state.ui_aggiornata = False
            return
        
        # Effetto sonoro
        gioco.io.play_sound({
            "sound_id": "use_item",
            "volume": 0.6
        })
        
        # Animazione uso oggetto
        gioco.io.mostra_animazione({
            "type": "animation",
            "id": "anim_uso_oggetto",
            "animation": "item_use",
            "x": 400,
            "y": 300,
            "duration": 0.8
        })
        
        # Usa l'oggetto
        oggetto.usa(gioco.giocatore, gioco)
        
        # Messaggio di conferma
        gioco.io.mostra_dialogo("Oggetto Usato", f"Hai usato: {oggetto.nome}", ["Continua"])
        self.inventario_state.fase = "menu_principale"
        self.inventario_state.ui_aggiornata = False
        
    def equipaggia_oggetto_selezionato(self, gioco, oggetto):
        """
        Equipaggia l'oggetto selezionato.
        
        Args:
            gioco: L'istanza del gioco
            oggetto: L'oggetto da equipaggiare
        """
        # Effetto sonoro
        gioco.io.play_sound({
            "sound_id": "equip_item",
            "volume": 0.7
        })
        
        # Animazione equipaggiamento
        gioco.io.mostra_animazione({
            "type": "animation",
            "id": "anim_equipaggia",
            "animation": "item_equip",
            "x": 400,
            "y": 300,
            "duration": 0.8
        })
        
        # Equipaggia l'oggetto
        oggetto.equipaggia(gioco.giocatore)
        
        # Messaggio di conferma
        gioco.io.mostra_dialogo("Oggetto Equipaggiato", f"Hai equipaggiato: {oggetto.nome}", ["Continua"])
        self.inventario_state.fase = "menu_principale"
        self.inventario_state.ui_aggiornata = False
        
    def rimuovi_equipaggiamento_selezionato(self, gioco, oggetto):
        """
        Rimuove l'equipaggiamento selezionato.
        
        Args:
            gioco: L'istanza del gioco
            oggetto: L'oggetto da rimuovere
        """
        # Effetto sonoro
        gioco.io.play_sound({
            "sound_id": "unequip_item",
            "volume": 0.6
        })
        
        # Animazione rimozione
        gioco.io.mostra_animazione({
            "type": "animation",
            "id": "anim_rimozione",
            "animation": "item_unequip",
            "x": 400,
            "y": 300,
            "duration": 0.8
        })
        
        # Rimuovi l'oggetto
        oggetto.rimuovi(gioco.giocatore)
        
        # Messaggio di conferma
        gioco.io.mostra_dialogo("Equipaggiamento Rimosso", f"Hai rimosso: {oggetto.nome}", ["Continua"])
        self.inventario_state.fase = "menu_principale"
        self.inventario_state.ui_aggiornata = False
        
    def esamina_oggetto_selezionato(self, gioco, oggetto):
        """
        Esamina l'oggetto selezionato.
        
        Args:
            gioco: L'istanza del gioco
            oggetto: L'oggetto da esaminare
        """
        # Effetto sonoro
        gioco.io.play_sound({
            "sound_id": "examine_item",
            "volume": 0.5
        })
        
        # Delegare la visualizzazione dei dettagli al gestore UI
        self.inventario_state.ui_handler.mostra_dettagli_oggetto(gioco, oggetto)
        
        # Imposta la fase corrente
        self.inventario_state.fase = "visualizza_dettagli"
        
    def get_oggetti_equipaggiabili(self, gioco):
        """
        Ottiene gli oggetti equipaggiabili dall'inventario.
        
        Args:
            gioco: L'istanza del gioco
            
        Returns:
            list: Lista di oggetti equipaggiabili
        """
        return FiltriInventario.oggetti_equipaggiabili(gioco.giocatore.inventario)
        
    def get_oggetti_consumabili(self, gioco):
        """
        Ottiene gli oggetti consumabili dall'inventario.
        
        Args:
            gioco: L'istanza del gioco
            
        Returns:
            list: Lista di oggetti consumabili
        """
        return FiltriInventario.oggetti_consumabili(gioco.giocatore.inventario)
        
    def get_opzioni_rimozione(self, gioco):
        """
        Ottiene le opzioni di rimozione dell'equipaggiamento.
        
        Args:
            gioco: L'istanza del gioco
            
        Returns:
            list: Lista di tuple (tipo, oggetto) per gli oggetti equipaggiati
        """
        opzioni = []
        
        if gioco.giocatore.arma and not isinstance(gioco.giocatore.arma, str):
            opzioni.append(("arma", gioco.giocatore.arma))
        if gioco.giocatore.armatura and not isinstance(gioco.giocatore.armatura, str):
            opzioni.append(("armatura", gioco.giocatore.armatura))
        for i, acc in enumerate(gioco.giocatore.accessori):
            if not isinstance(acc, str):
                opzioni.append((f"accessorio {i+1}", acc))
                
        return opzioni 