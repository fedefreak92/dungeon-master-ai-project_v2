"""
Modulo per la gestione degli effetti durante il dialogo
"""

def gestisci_effetto(self, effetto, gioco):
    """
    Applica effetti speciali in base al tipo di effetto
    
    Args:
        effetto: L'effetto da applicare
        gioco: L'istanza del gioco
    """
    if isinstance(effetto, str):
        # Gestione effetti semplici
        if effetto == "riposo":
            _applica_effetto_riposo(self, gioco)
        elif effetto == "cura_leggera":
            _applica_effetto_cura_leggera(self, gioco)
    elif isinstance(effetto, dict):
        # Gestione effetti complessi
        tipo = effetto.get("tipo", "")
        
        if tipo == "consegna_oro":
            _applica_effetto_consegna_oro(self, effetto, gioco)
        elif tipo == "aggiungi_item":
            _applica_effetto_aggiungi_item(self, effetto, gioco)
        elif tipo == "rimuovi_item":
            _applica_effetto_rimuovi_item(self, effetto, gioco)
        elif tipo == "scambio":
            _applica_effetto_scambio(self, effetto, gioco)

def _applica_effetto_riposo(self, gioco):
    """Applica l'effetto di riposo"""
    gioco.giocatore.cura(5, gioco)
    gioco.io.mostra_messaggio("\n*Hai riposato e recuperato 5 HP*")
    
    # Effetto visivo di guarigione migliorato
    gioco.io.mostra_animazione({
        "type": "animation",
        "id": "anim_guarigione",
        "animation": "healing",
        "x": 400,
        "y": 300,
        "duration": 1.0,
        "particles": True,  # Aggiunge particelle
        "particle_color": "#44FF44",  # Verde per guarigione
        "scale": 1.2
    })
    
    # Effetto sonoro
    gioco.io.play_sound({
        "sound_id": "heal_effect",
        "volume": 0.7
    })
    
    # Mostra indicatore di HP recuperati
    gioco.io.mostra_ui_elemento({
        "type": "floating_text",
        "id": "hp_recuperati",
        "text": "+5 HP",
        "x": 400,
        "y": 250,
        "color": "#44FF44",
        "font_size": 20,
        "z_index": 20,
        "animation": {
            "type": "float_up",
            "distance": 50,
            "duration": 1.5,
            "fade_out": True
        }
    })

def _applica_effetto_cura_leggera(self, gioco):
    """Applica l'effetto di cura leggera"""
    gioco.giocatore.cura(3, gioco)
    gioco.io.mostra_messaggio("\n*L'unguento di Violetta ti cura per 3 HP*")
    
    # Effetto visivo di guarigione migliorato
    gioco.io.mostra_animazione({
        "type": "animation",
        "id": "anim_guarigione",
        "animation": "minor_healing",
        "x": 400,
        "y": 300,
        "duration": 0.8,
        "particles": True,
        "particle_color": "#88FF88",
        "scale": 0.9
    })
    
    # Effetto sonoro
    gioco.io.play_sound({
        "sound_id": "minor_heal",
        "volume": 0.6
    })
    
    # Mostra indicatore di HP recuperati
    gioco.io.mostra_ui_elemento({
        "type": "floating_text",
        "id": "hp_recuperati",
        "text": "+3 HP",
        "x": 400,
        "y": 250,
        "color": "#88FF88",
        "font_size": 18,
        "z_index": 20,
        "animation": {
            "type": "float_up",
            "distance": 40,
            "duration": 1.2,
            "fade_out": True
        }
    })

def _applica_effetto_consegna_oro(self, effetto, gioco):
    """Applica l'effetto di consegna oro"""
    quantita = effetto.get("quantita", 10)
    self.npg.trasferisci_oro(gioco.giocatore, quantita, gioco)
    gioco.io.mostra_messaggio(f"\n*{self.npg.nome} ti ha dato {quantita} monete d'oro*")
    
    # Effetto sonoro
    gioco.io.play_sound({
        "sound_id": "coins",
        "volume": 0.7
    })
    
    # Effetto visivo
    gioco.io.mostra_animazione({
        "type": "animation",
        "id": "anim_oro",
        "animation": "gold_sparkle",
        "x": 400,
        "y": 300,
        "duration": 1.0
    })

def _applica_effetto_aggiungi_item(self, effetto, gioco):
    """Applica l'effetto di aggiunta item"""
    oggetto = effetto.get("oggetto")
    if oggetto and self.npg.rimuovi_item(oggetto):
        gioco.giocatore.aggiungi_item(oggetto)
        gioco.io.mostra_messaggio(f"\n*Hai ricevuto {oggetto} da {self.npg.nome}*")
        
        # Effetto sonoro
        gioco.io.play_sound({
            "sound_id": "item_get",
            "volume": 0.7
        })
        
        # Effetto visivo
        gioco.io.mostra_animazione({
            "type": "animation",
            "id": "anim_item",
            "animation": "item_received",
            "x": 400,
            "y": 300,
            "duration": 1.0
        })

def _applica_effetto_rimuovi_item(self, effetto, gioco):
    """Applica l'effetto di rimozione item"""
    oggetto = effetto.get("oggetto")
    if oggetto and gioco.giocatore.rimuovi_item(oggetto):
        self.npg.aggiungi_item(oggetto)
        gioco.io.mostra_messaggio(f"\n*Hai dato {oggetto} a {self.npg.nome}*")
        
        # Effetto sonoro
        gioco.io.play_sound({
            "sound_id": "item_give",
            "volume": 0.7
        })

def _applica_effetto_scambio(self, effetto, gioco):
    """Applica l'effetto di scambio item"""
    oggetto_nome = effetto.get("oggetto")
    costo = effetto.get("costo", 0)
    
    # Trova l'oggetto nell'inventario dell'NPC
    oggetto_trovato = None
    for item in self.npg.inventario:
        if item.nome == oggetto_nome:
            oggetto_trovato = item
            break
    
    if gioco.giocatore.oro >= costo and oggetto_trovato is not None:
        gioco.giocatore.oro -= costo
        self.npg.oro += costo
        self.npg.rimuovi_item(oggetto_nome)
        gioco.giocatore.aggiungi_item(oggetto_trovato)
        gioco.io.mostra_messaggio(f"\n*Hai acquistato {oggetto_nome} da {self.npg.nome} per {costo} monete d'oro*")
        
        # Effetti speciali per l'acquisto
        gioco.io.play_sound({
            "sound_id": "purchase",
            "volume": 0.7
        })
        
        # Mostra animazione acquisto
        gioco.io.mostra_animazione({
            "type": "animation",
            "id": "anim_acquisto",
            "animation": "purchase",
            "x": 400,
            "y": 300,
            "duration": 1.0
        })
    else:
        if gioco.giocatore.oro < costo:
            gioco.io.mostra_messaggio(f"\n*Non hai abbastanza oro per acquistare {oggetto_nome}*")
            
            # Effetto sonoro per acquisto fallito
            gioco.io.play_sound({
                "sound_id": "purchase_failed",
                "volume": 0.5
            })
        else:
            gioco.io.mostra_messaggio(f"\n*{self.npg.nome} non ha più {oggetto_nome} disponibile*") 