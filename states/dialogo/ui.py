"""
Modulo per la gestione dell'interfaccia utente dello stato di dialogo
"""
import core.events as Events

def mostra_interfaccia_dialogo(self, gioco):
    """
    Mostra l'interfaccia grafica del dialogo
    
    Args:
        gioco: L'istanza del gioco
    """
    # Emetti evento per aggiornare l'interfaccia UI
    self.emit_event(Events.UI_UPDATE, 
                   component="dialog_interface",
                   state="open")
                   
    # Aggiungi elementi UI per il dialogo
    gioco.io.mostra_ui_elemento({
        "type": "dialog_background",
        "id": "sfondo_dialogo",
        "x": 0,
        "y": 400,
        "width": 800,
        "height": 200,
        "z_index": 10,
        "clickable": True  # Rende lo sfondo cliccabile
    })
    
    # Mostra il ritratto del personaggio
    immagine_npg = self.npg.immagine if hasattr(self.npg, "immagine") else "npc_default"
    gioco.io.mostra_ui_elemento({
        "type": "portrait",
        "id": "ritratto_npg",
        "image": immagine_npg,
        "x": 50,
        "y": 450,
        "scale": 1.0,
        "z_index": 11,
        "clickable": True,  # Ritratto cliccabile per mostrare informazioni
        "context_menu": ["Info Personaggio", "Mostra Inventario"]  # Menu contestuale
    })
    
    # Mostra il nome del personaggio
    gioco.io.mostra_ui_elemento({
        "type": "text",
        "id": "nome_npg",
        "text": self.npg.nome,
        "x": 120,
        "y": 420,
        "font_size": 18,
        "color": "#FFDD00",
        "z_index": 12
    })
    
    # Aggiungi pulsante per uscire dal dialogo
    gioco.io.mostra_ui_elemento({
        "type": "button",
        "id": "btn_chiudi_dialogo",
        "text": "X",
        "x": 760,
        "y": 410,
        "width": 30,
        "height": 30,
        "color": "#FF4444",
        "text_color": "#FFFFFF",
        "z_index": 15,
        "clickable": True,
        "onClick": lambda: self.emit_event(Events.UI_DIALOG_CLOSE)
    })

def mostra_dialogo_corrente(self, gioco):
    """
    Mostra il dialogo corrente e le opzioni disponibili
    
    Args:
        gioco: L'istanza del gioco
    """
    # Ottieni i dati della conversazione per lo stato corrente
    dati_conversazione = self.npg.ottieni_conversazione(self.stato_corrente)
    
    # Se i dati non esistono, torna al menu principale
    if not dati_conversazione:
        self.emit_event(Events.UI_DIALOG_OPEN, 
                       dialog_id="avviso",
                       title="Avviso",
                       content="Non c'è altro da dire.",
                       options=["Chiudi"])
        self.fase = "fine"
        return
    
    # Gestisce gli effetti legati allo stato della conversazione
    if "effetto" in dati_conversazione:
        self._gestisci_effetto(dati_conversazione["effetto"], gioco)
    
    # Effetto audio per il dialogo
    gioco.io.play_sound({
        "sound_id": "dialog_text",
        "volume": 0.4
    })
    
    # Emetti evento di aggiornamento dialogo
    self.emit_event(Events.UI_UPDATE, 
                   component="dialog_text",
                   content=dati_conversazione['testo'])
    
    # Aggiungi effetto di digitazione del testo
    testo_dialogo = dati_conversazione['testo']
    gioco.io.mostra_ui_elemento({
        "type": "text",
        "id": "testo_dialogo",
        "text": testo_dialogo,
        "x": 150,
        "y": 460, 
        "width": 600,
        "height": 100,
        "font_size": 16,
        "color": "#FFFFFF",
        "z_index": 12,
        "animation": {
            "type": "typing",
            "speed": 30  # Caratteri al secondo
        }
    })
    
    # Se la conversazione non ha opzioni, mostra solo un pulsante per continuare
    if not dati_conversazione.get("opzioni"):
        self.emit_event(Events.UI_DIALOG_OPEN, 
                        dialog_id="continua_dialogo",
                        title="",
                        content="",
                        options=["Continua"])
        self.fase = "fine"
    else:
        # Prepara le opzioni di dialogo
        opzioni = [testo for testo, _ in dati_conversazione["opzioni"]]
        
        # Emetti evento di opzioni dialogo
        self.emit_event(Events.UI_UPDATE, 
                       component="dialog_options",
                       options=opzioni)
        
        # Mostra le opzioni come pulsanti interattivi
        for i, opzione in enumerate(opzioni):
            gioco.io.mostra_ui_elemento({
                "type": "button",
                "id": f"opzione_dialogo_{i}",
                "text": opzione,
                "x": 150,
                "y": 520 + (i * 30),
                "width": 500,
                "height": 25,
                "color": "#444477",
                "text_color": "#FFFFFF",
                "z_index": 13,
                "clickable": True,
                "highlight_on_hover": True,
                "onClick": lambda idx=i: self.emit_event(Events.DIALOG_CHOICE, choice=opzioni[idx])
            })
        
        # Salva le opzioni di destinazione per l'handler
        self.dati_contestuali["opzioni_destinazioni"] = [dest for _, dest in dati_conversazione["opzioni"]]
        
        # Mostra anche come dialogo per compatibilità
        gioco.io.mostra_dialogo("Opzioni", "", opzioni)

def mostra_info_npg(self, gioco):
    """
    Mostra informazioni dettagliate sull'NPG
    
    Args:
        gioco: Istanza del gioco
    """
    # Informazioni base sull'NPG
    info = f"Nome: {self.npg.nome}\n"
    
    # Aggiungi altre informazioni se disponibili
    if hasattr(self.npg, "descrizione"):
        info += f"Descrizione: {self.npg.descrizione}\n"
    
    if hasattr(self.npg, "professione"):
        info += f"Professione: {self.npg.professione}\n"
    
    # Emetti evento di dialogo informazioni
    self.emit_event(Events.UI_DIALOG_OPEN, 
                   dialog_id="info_npg",
                   title=f"Informazioni su {self.npg.nome}",
                   content=info,
                   options=["Chiudi"])
    
    # Mostra le informazioni in un dialogo
    gioco.io.mostra_dialogo(f"Informazioni su {self.npg.nome}", info, ["Chiudi"])
    
    # Riproduci suono informazioni
    gioco.io.play_sound({
        "sound_id": "info_window",
        "volume": 0.5
    })

def mostra_inventario_npg(self, gioco):
    """
    Mostra l'inventario dell'NPG
    
    Args:
        gioco: Istanza del gioco
    """
    # Verifica se l'NPG ha un inventario
    if not hasattr(self.npg, "inventario") or not self.npg.inventario:
        self.emit_event(Events.UI_DIALOG_OPEN, 
                       dialog_id="inventario_vuoto",
                       title=f"Inventario di {self.npg.nome}",
                       content="Non ha oggetti da mostrare.",
                       options=["Chiudi"])
        gioco.io.mostra_dialogo(f"Inventario di {self.npg.nome}", "Non ha oggetti da mostrare.", ["Chiudi"])
        return
    
    # Elenca gli oggetti nell'inventario
    items = []
    for item in self.npg.inventario:
        if hasattr(item, "nome"):
            items.append(item.nome)
        else:
            items.append(str(item))
    
    items_text = "\n".join([f"- {item}" for item in items])
    
    # Emetti evento di dialogo inventario
    self.emit_event(Events.UI_DIALOG_OPEN, 
                   dialog_id="inventario_npg",
                   title=f"Inventario di {self.npg.nome}",
                   content=items_text,
                   options=["Chiudi"])
    
    gioco.io.mostra_dialogo(f"Inventario di {self.npg.nome}", items_text, ["Chiudi"])
    
    # Effetto sonoro per apertura inventario
    gioco.io.play_sound({
        "sound_id": "inventory_open",
        "volume": 0.6
    }) 