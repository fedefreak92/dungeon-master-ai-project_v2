from core.io_interface import GameIO

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
        
    def _handle_click_event(self, event):
        """
        Gestisce eventi di click.
        
        Args:
            event: L'evento di click
            
        Returns:
            bool: True se l'evento è stato gestito, False altrimenti
        """
        return self.inventario_state.menu_handler.handle_dialog_choice(event)
    
    def _handle_menu_action(self, event):
        """
        Gestisce azioni del menu.
        
        Args:
            event: L'evento di azione del menu
            
        Returns:
            bool: True se l'evento è stato gestito, False altrimenti
        """
        return self.inventario_state.menu_handler.handle_dialog_choice(event)
    
    def _handle_dialog_choice(self, event):
        """
        Gestisce scelte di dialogo.
        
        Args:
            event: L'evento di scelta di dialogo
            
        Returns:
            bool: True se l'evento è stato gestito, False altrimenti
        """
        return self.inventario_state.menu_handler.handle_dialog_choice(event)
    
    def _handle_keypress(self, event):
        """
        Gestisce eventi di tastiera.
        
        Args:
            event: L'evento di pressione tasto
            
        Returns:
            bool: True se l'evento è stato gestito, False altrimenti
        """
        # Ottieni il contesto di gioco
        gioco = self.inventario_state.gioco
        if not gioco:
            return False
            
        # Ottieni il tasto premuto
        key = event.get("key")
        if not key:
            return False
            
        # Gestisci tasti specifici
        if key == "Escape":
            # Torna indietro al menu principale o esci dall'inventario
            if self.inventario_state.fase != "menu_principale":
                self.inventario_state.fase = "menu_principale"
                self.inventario_state.ui_aggiornata = False
                return True
            else:
                self.inventario_state.menu_handler.torna_indietro(gioco)
                return True
                
        return False
    
    def mostra_menu_principale(self, gioco):
        """
        Mostra il menu principale dell'inventario.
        
        Args:
            gioco: L'istanza del gioco
        """
        # Mostra sfondo dell'inventario
        gioco.io.mostra_ui_elemento({
            "type": "panel",
            "id": "sfondo_inventario",
            "x": 100,
            "y": 50,
            "width": 600,
            "height": 500,
            "color": "#333333",
            "opacity": 0.9,
            "z_index": 10
        })
        
        # Titolo dell'inventario
        gioco.io.mostra_ui_elemento({
            "type": "text",
            "id": "titolo_inventario",
            "text": "GESTIONE INVENTARIO",
            "x": 400,
            "y": 80,
            "font_size": 24,
            "centered": True,
            "color": "#FFFFFF",
            "z_index": 11
        })
        
        # Mostra oro del giocatore
        gioco.io.mostra_ui_elemento({
            "type": "text",
            "id": "oro_giocatore",
            "text": f"Oro: {gioco.giocatore.oro}",
            "x": 400,
            "y": 120,
            "font_size": 18,
            "centered": True,
            "color": "#FFD700",
            "z_index": 11
        })
        
        # Mostra equipaggiamento attuale
        y_offset = 160
        if gioco.giocatore.arma:
            arma_nome = gioco.giocatore.arma.nome if hasattr(gioco.giocatore.arma, 'nome') else str(gioco.giocatore.arma)
            gioco.io.mostra_ui_elemento({
                "type": "text",
                "id": "arma_equipaggiata",
                "text": f"Arma: {arma_nome}",
                "x": 400,
                "y": y_offset,
                "font_size": 16,
                "centered": True,
                "color": "#FF8C00",
                "z_index": 11
            })
            y_offset += 30
                
        if gioco.giocatore.armatura:
            armatura_nome = gioco.giocatore.armatura.nome if hasattr(gioco.giocatore.armatura, 'nome') else str(gioco.giocatore.armatura)
            gioco.io.mostra_ui_elemento({
                "type": "text",
                "id": "armatura_equipaggiata",
                "text": f"Armatura: {armatura_nome}",
                "x": 400,
                "y": y_offset,
                "font_size": 16,
                "centered": True,
                "color": "#1E90FF",
                "z_index": 11
            })
            y_offset += 30
        
        # Lista oggetti nell'inventario
        y_offset = 200
        gioco.io.mostra_ui_elemento({
            "type": "text",
            "id": "titolo_lista_oggetti",
            "text": "OGGETTI",
            "x": 400,
            "y": y_offset,
            "font_size": 20,
            "centered": True,
            "color": "#FFFFFF",
            "z_index": 11
        })
        y_offset += 30
        
        # Aggiungi visualizzazione a scorrimento per l'inventario
        oggetti_per_pagina = 8
        
        for i, item in enumerate(gioco.giocatore.inventario[:oggetti_per_pagina], 1):
            nome_oggetto = item.nome if hasattr(item, 'nome') else str(item)
            tipo_oggetto = item.tipo if hasattr(item, 'tipo') else "N/A"
            
            gioco.io.mostra_ui_elemento({
                "type": "interactive_text",
                "id": f"oggetto_{i-1}",
                "text": f"{i}. {nome_oggetto} - {tipo_oggetto}",
                "x": 200,
                "y": y_offset,
                "width": 400,
                "font_size": 16,
                "color": "#FFFFFF",
                "hover_color": "#AAFFAA",
                "on_click": {"target": f"oggetto_{i-1}"},
                "z_index": 11
            })
            y_offset += 25
        
        # Pulsanti di azione
        y_offset = 450
        
        # Azioni disponibili come pulsanti
        gioco.io.mostra_dialogo("Azioni", "Cosa vuoi fare?", [
            "Usa oggetto",
            "Equipaggia oggetto",
            "Rimuovi equipaggiamento",
            "Esamina oggetto",
            "Torna indietro"
        ])
    
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