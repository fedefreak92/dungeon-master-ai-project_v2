from core.io_interface import GameIO
import core.events as Events

class UIInventarioHandler:
    """
    Classe che gestisce l'interfaccia utente dell'inventario.
    Gestisce la visualizzazione e l'interazione con gli elementi UI.
    """
    
    def __init__(self, inventario_state):
        """
        Inizializza il gestore UI.
        
        Args:
            inventario_state: L'istanza dello stato inventario
        """
        self.inventario_state = inventario_state
        self.handlers_registrati = []
    
    def register_ui_handlers(self, io_handler):
        """
        Registra i gestori di eventi dell'interfaccia utente.
        
        Args:
            io_handler: L'handler IO del gioco
        """
        if not io_handler:
            return
        
        # Registra i gestori di eventi
        self.handlers_registrati = [
            io_handler.register_event_handler("click", self._handle_click_event),
            io_handler.register_event_handler("menu_action", self._handle_menu_action),
            io_handler.register_event_handler("dialog_choice", self._handle_dialog_choice),
            io_handler.register_event_handler("keypress", self._handle_keypress)
        ]
    
    def unregister_ui_handlers(self, io_handler):
        """
        Deregistra i gestori di eventi dell'interfaccia utente.
        
        Args:
            io_handler: L'handler IO del gioco
        """
        if not io_handler:
            return
            
        # Deregistra tutti i gestori registrati in precedenza
        for handler_id in self.handlers_registrati:
            io_handler.unregister_event_handler(handler_id)
        
        # Resetta la lista dei gestori registrati
        self.handlers_registrati = []
    
    def aggiorna_renderer(self, gioco):
        """
        Aggiorna il renderer grafico con gli elementi dell'inventario.
        
        Args:
            gioco: L'istanza del gioco
            
        Returns:
            bool: True se l'aggiornamento è avvenuto con successo, False altrimenti
        """
        # Ottieni il renderer grafico
        renderer = gioco.io.get_renderer()
        if not renderer:
            return False
        
        # Pulisci il renderer
        renderer.clear()
        
        # Disegna il titolo e le informazioni
        renderer.draw_title("Gestione Inventario")
        renderer.draw_info(f"Oro: {gioco.giocatore.oro}")
        
        # Disegna informazioni sull'equipaggiamento attuale
        y_offset = 100
        if gioco.giocatore.arma:
            arma_nome = gioco.giocatore.arma.nome if hasattr(gioco.giocatore.arma, 'nome') else str(gioco.giocatore.arma)
            renderer.draw_text(f"Arma: {arma_nome}", 400, y_offset, color="#FF8C00")
            y_offset += 30
                
        if gioco.giocatore.armatura:
            armatura_nome = gioco.giocatore.armatura.nome if hasattr(gioco.giocatore.armatura, 'nome') else str(gioco.giocatore.armatura)
            renderer.draw_text(f"Armatura: {armatura_nome}", 400, y_offset, color="#1E90FF")
            y_offset += 30
        
        # Disegna la lista degli oggetti nell'inventario
        renderer.draw_text("OGGETTI", 400, y_offset + 20, size=20)
        
        # Se in fase di menu principale, disegna anche le opzioni disponibili
        if self.inventario_state.fase == "menu_principale":
            renderer.draw_menu(["Usa oggetto", "Equipaggia oggetto", "Rimuovi equipaggiamento", "Esamina oggetto", "Torna indietro"])
        
        # Aggiorna il renderer
        renderer.update()
        return True
        
    def mostra_menu_principale(self, gioco):
        """
        Mostra il menu principale dell'inventario.
        
        Args:
            gioco: L'istanza del gioco
        """
        # Emetti evento del menu principale
        if hasattr(self.inventario_state, 'emit_event'):
            self.inventario_state.emit_event("MENU_DISPLAY", 
                                           menu_id="inventario_principale", 
                                           options=["Usa oggetto", "Equipaggia oggetto", 
                                                   "Rimuovi equipaggiamento", "Esamina oggetto", 
                                                   "Torna indietro"])
        
        # Mostra intestazione
        gioco.io.mostra_messaggio("Inventario di " + gioco.giocatore.nome)
        
        # Mostra statistiche inventario
        capacita = len(gioco.giocatore.inventario)
        capacita_max = gioco.giocatore.capacita_inventario if hasattr(gioco.giocatore, 'capacita_inventario') else 20
        gioco.io.mostra_messaggio(f"Spazio: {capacita}/{capacita_max}")
        
        # Mostra il menu delle opzioni
        gioco.io.mostra_dialogo(
            "Gestione Inventario", 
            "Cosa vuoi fare?", 
            ["Usa oggetto", "Equipaggia oggetto", "Rimuovi equipaggiamento", "Esamina oggetto", "Torna indietro"]
        )
    
    def mostra_usa_oggetto(self, gioco):
        """
        Mostra la schermata di selezione oggetto da usare.
        
        Args:
            gioco: L'istanza del gioco
        """
        # Mostra sfondo dell'inventario
        gioco.io.mostra_ui_elemento({
            "type": "panel",
            "id": "sfondo_selezione",
            "x": 100,
            "y": 50,
            "width": 600,
            "height": 500,
            "color": "#333333",
            "opacity": 0.9,
            "z_index": 10
        })
        
        # Titolo
        gioco.io.mostra_ui_elemento({
            "type": "text",
            "id": "titolo_usa_oggetto",
            "text": "USA UN OGGETTO",
            "x": 400,
            "y": 80,
            "font_size": 24,
            "centered": True,
            "color": "#FFFFFF",
            "z_index": 11
        })
        
        # Prepara la lista di opzioni per il dialogo
        opzioni_oggetti = []
        for item in gioco.giocatore.inventario:
            nome_oggetto = item.nome if hasattr(item, 'nome') else str(item)
            opzioni_oggetti.append(nome_oggetto)
        
        # Aggiungi opzione Annulla
        opzioni_oggetti.append("Annulla")
        
        # Mostra dialogo di selezione
        gioco.io.mostra_dialogo("Selezione Oggetto", "Quale oggetto vuoi usare?", opzioni_oggetti)
    
    def mostra_equipaggia_oggetto(self, gioco):
        """
        Mostra la schermata di selezione oggetto da equipaggiare.
        
        Args:
            gioco: L'istanza del gioco
        """
        # Aggiorna la lista di oggetti equipaggiabili
        equipaggiabili = self.inventario_state.gestore_oggetti.get_oggetti_equipaggiabili(gioco)
        
        if not equipaggiabili:
            gioco.io.mostra_messaggio("Non hai oggetti equipaggiabili.")
            gioco.io.mostra_dialogo("Attenzione", "Non hai oggetti equipaggiabili.", ["Torna al Menu"])
            return
        
        # Mostra sfondo dell'inventario
        gioco.io.mostra_ui_elemento({
            "type": "panel",
            "id": "sfondo_selezione",
            "x": 100,
            "y": 50,
            "width": 600,
            "height": 500,
            "color": "#333333",
            "opacity": 0.9,
            "z_index": 10
        })
        
        # Titolo
        gioco.io.mostra_ui_elemento({
            "type": "text",
            "id": "titolo_equipaggia",
            "text": "EQUIPAGGIA OGGETTO",
            "x": 400,
            "y": 80,
            "font_size": 24,
            "centered": True,
            "color": "#FFFFFF",
            "z_index": 11
        })
        
        # Prepara la lista di opzioni per il dialogo
        opzioni_equipaggiare = []
        for item in equipaggiabili:
            opzioni_equipaggiare.append(f"{item.nome} ({item.tipo})")
        
        # Aggiungi opzione Annulla
        opzioni_equipaggiare.append("Annulla")
        
        # Mostra dialogo di selezione
        gioco.io.mostra_dialogo("Equipaggiamento", "Quale oggetto vuoi equipaggiare?", opzioni_equipaggiare)
    
    def mostra_rimuovi_equipaggiamento(self, gioco):
        """
        Mostra la schermata di selezione equipaggiamento da rimuovere.
        
        Args:
            gioco: L'istanza del gioco
        """
        # Prepara la lista di equipaggiamento
        opzioni_rimozione = self.inventario_state.gestore_oggetti.get_opzioni_rimozione(gioco)
        
        if not opzioni_rimozione:
            gioco.io.mostra_messaggio("Non hai nessun equipaggiamento da rimuovere.")
            gioco.io.mostra_dialogo("Attenzione", "Non hai equipaggiamento da rimuovere.", ["Torna al Menu"])
            return
        
        # Mostra sfondo dell'inventario
        gioco.io.mostra_ui_elemento({
            "type": "panel",
            "id": "sfondo_selezione",
            "x": 100,
            "y": 50,
            "width": 600,
            "height": 500,
            "color": "#333333",
            "opacity": 0.9,
            "z_index": 10
        })
        
        # Titolo
        gioco.io.mostra_ui_elemento({
            "type": "text",
            "id": "titolo_rimuovi",
            "text": "RIMUOVI EQUIPAGGIAMENTO",
            "x": 400,
            "y": 80,
            "font_size": 24,
            "centered": True,
            "color": "#FFFFFF",
            "z_index": 11
        })
        
        # Prepara la lista di opzioni per il dialogo
        opzioni_rimuovere = []
        for tipo, item in opzioni_rimozione:
            opzioni_rimuovere.append(f"{tipo.capitalize()}: {item.nome}")
        
        # Aggiungi opzione Annulla
        opzioni_rimuovere.append("Annulla")
        
        # Mostra dialogo di selezione
        gioco.io.mostra_dialogo("Rimozione", "Cosa vuoi rimuovere?", opzioni_rimuovere)
    
    def mostra_esamina_oggetto(self, gioco):
        """
        Mostra la schermata di selezione oggetto da esaminare.
        
        Args:
            gioco: L'istanza del gioco
        """
        # Mostra sfondo dell'inventario
        gioco.io.mostra_ui_elemento({
            "type": "panel",
            "id": "sfondo_selezione",
            "x": 100,
            "y": 50,
            "width": 600,
            "height": 500,
            "color": "#333333",
            "opacity": 0.9,
            "z_index": 10
        })
        
        # Titolo
        gioco.io.mostra_ui_elemento({
            "type": "text",
            "id": "titolo_esamina",
            "text": "ESAMINA OGGETTO",
            "x": 400,
            "y": 80,
            "font_size": 24,
            "centered": True,
            "color": "#FFFFFF",
            "z_index": 11
        })
        
        # Prepara la lista di opzioni per il dialogo
        opzioni_esaminare = []
        for item in gioco.giocatore.inventario:
            nome_oggetto = item.nome if hasattr(item, 'nome') else str(item)
            opzioni_esaminare.append(nome_oggetto)
        
        # Aggiungi opzione Annulla
        opzioni_esaminare.append("Annulla")
        
        # Mostra dialogo di selezione
        gioco.io.mostra_dialogo("Esame", "Quale oggetto vuoi esaminare?", opzioni_esaminare)
    
    def mostra_dettagli_oggetto(self, gioco, oggetto):
        """
        Mostra i dettagli di un oggetto specifico.
        
        Args:
            gioco: L'istanza del gioco
            oggetto: L'oggetto da esaminare
        """
        # Mostra sfondo dei dettagli
        gioco.io.mostra_ui_elemento({
            "type": "panel",
            "id": "sfondo_dettagli",
            "x": 150,
            "y": 100,
            "width": 500,
            "height": 400,
            "color": "#222233",
            "opacity": 0.95,
            "z_index": 12
        })
        
        # Titolo (nome oggetto)
        nome = oggetto.nome if hasattr(oggetto, 'nome') else str(oggetto)
        gioco.io.mostra_ui_elemento({
            "type": "text",
            "id": "titolo_oggetto",
            "text": nome,
            "x": 400,
            "y": 130,
            "font_size": 22,
            "centered": True,
            "color": "#FFFFFF",
            "z_index": 13
        })
        
        # Dettagli dell'oggetto
        y_offset = 180
        
        # Tipo
        tipo = oggetto.tipo if hasattr(oggetto, 'tipo') else "Generico"
        gioco.io.mostra_ui_elemento({
            "type": "text",
            "id": "tipo_oggetto",
            "text": f"Tipo: {tipo}",
            "x": 200,
            "y": y_offset,
            "font_size": 16,
            "color": "#AAAAFF",
            "z_index": 13
        })
        y_offset += 30
        
        # Descrizione
        descrizione = oggetto.descrizione if hasattr(oggetto, 'descrizione') else "Non disponibile"
        gioco.io.mostra_ui_elemento({
            "type": "text",
            "id": "descrizione_oggetto",
            "text": f"Descrizione: {descrizione}",
            "x": 200,
            "y": y_offset,
            "width": 400,
            "font_size": 16,
            "color": "#CCCCCC",
            "z_index": 13
        })
        y_offset += 60
        
        # Valore
        valore = oggetto.valore if hasattr(oggetto, 'valore') else "Sconosciuto"
        gioco.io.mostra_ui_elemento({
            "type": "text",
            "id": "valore_oggetto",
            "text": f"Valore: {valore} oro",
            "x": 200,
            "y": y_offset,
            "font_size": 16,
            "color": "#FFD700",
            "z_index": 13
        })
        y_offset += 30
        
        # Effetti (se presenti)
        if hasattr(oggetto, 'effetto') and oggetto.effetto:
            gioco.io.mostra_ui_elemento({
                "type": "text",
                "id": "titolo_effetti",
                "text": "Effetti:",
                "x": 200,
                "y": y_offset,
                "font_size": 16,
                "color": "#AAFFAA",
                "z_index": 13
            })
            y_offset += 30
            
            for stat, valore in oggetto.effetto.items():
                gioco.io.mostra_ui_elemento({
                    "type": "text",
                    "id": f"effetto_{stat}",
                    "text": f"  - {stat}: {valore}",
                    "x": 220,
                    "y": y_offset,
                    "font_size": 14,
                    "color": "#88FF88",
                    "z_index": 13
                })
                y_offset += 25
        
        # Pulsante per tornare indietro
        gioco.io.mostra_dialogo("", "", ["Chiudi"])
    
    # Conversione eventi IO in eventi EventBus
    def _convertire_evento_a_eventbus(self, event, event_type):
        """
        Converte un evento IO in un evento EventBus.
        
        Args:
            event: Evento IO originale
            event_type: Tipo di evento da emettere
            
        Returns:
            bool: True se l'evento è stato convertito e emesso, False altrimenti
        """
        if not hasattr(self.inventario_state, 'emit_event'):
            return False
            
        if not hasattr(event, "data") or not event.data:
            return False
            
        # Mappa le proprietà dell'evento IO in parametri per EventBus
        params = {}
        for key, value in event.data.items():
            params[key] = value
            
        # Emetti l'evento EventBus
        self.inventario_state.emit_event(event_type, **params)
        return True
    
    def _handle_click_event(self, event):
        """
        Gestisce eventi di click.
        
        Args:
            event: L'evento di click
            
        Returns:
            bool: True se l'evento è stato gestito, False altrimenti
        """
        # Converti in evento EventBus se possibile
        self._convertire_evento_a_eventbus(event, "UI_CLICK")
        
        return self.inventario_state.menu_handler.handle_dialog_choice(event)
    
    def _handle_menu_action(self, event):
        """
        Gestisce azioni del menu.
        
        Args:
            event: L'evento di azione del menu
            
        Returns:
            bool: True se l'evento è stato gestito, False altrimenti
        """
        # Converti in evento EventBus se possibile
        self._convertire_evento_a_eventbus(event, "MENU_ACTION")
        
        return self.inventario_state.menu_handler.handle_dialog_choice(event)
    
    def _handle_dialog_choice(self, event):
        """
        Gestisce scelte di dialogo.
        
        Args:
            event: L'evento di scelta di dialogo
            
        Returns:
            bool: True se l'evento è stato gestito, False altrimenti
        """
        # Converti in evento EventBus se possibile
        if hasattr(event, "data") and event.data and "choice" in event.data:
            if hasattr(self.inventario_state, 'emit_event'):
                self.inventario_state.emit_event("MENU_SELECTION", 
                                              menu_id="inventario", 
                                              choice=event.data["choice"])
        
        return self.inventario_state.menu_handler.handle_dialog_choice(event)
    
    def _handle_keypress(self, event):
        """
        Gestisce eventi di pressione tasti.
        
        Args:
            event: L'evento di pressione tasto
            
        Returns:
            bool: True se l'evento è stato gestito, False altrimenti
        """
        # Converti in evento EventBus se possibile
        self._convertire_evento_a_eventbus(event, "KEY_PRESSED")
        
        # Gestione specifica dei tasti
        if not hasattr(event, "data") or not event.data:
            return False
            
        key = event.data.get("key")
        if not key:
            return False
            
        # Tasto ESC per tornare indietro
        if key == "Escape":
            gioco = self.inventario_state.gioco
            if gioco:
                self.inventario_state.menu_handler.torna_indietro(gioco)
                return True
                
        return False 