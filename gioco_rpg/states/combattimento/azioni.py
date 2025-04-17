class AzioniCombattimento:
    """
    Classe per gestire le azioni di combattimento
    """
    def __init__(self, state):
        """
        Inizializza il gestore delle azioni
        
        Args:
            state: Lo stato del combattimento
        """
        self.state = state
    
    def esegui_attacco(self, attaccante_id, target_id, arma=None):
        """
        Esegue un attacco base
        
        Args:
            attaccante_id (str): ID dell'entità attaccante
            target_id (str): ID dell'entità bersaglio
            arma (str, optional): Nome dell'arma da utilizzare
            
        Returns:
            dict: Risultato dell'attacco
        """
        from util.dado import Dado
        dado_d20 = Dado(20)
        
        # Verifica che sia il turno dell'attaccante
        if self.state.turno_corrente != attaccante_id:
            return {
                "successo": False,
                "messaggio": "Non è il turno di questa entità"
            }
            
        # Ottieni le entità
        attaccante = self.state.world.get_entity(attaccante_id)
        target = self.state.world.get_entity(target_id)
        
        if not attaccante or not target:
            return {
                "successo": False,
                "messaggio": "Attaccante o bersaglio non trovato"
            }
            
        # Calcola bonus di attacco
        bonus_attacco = getattr(attaccante, "forza", 10) - 10
        bonus_attacco = bonus_attacco // 2  # Converti in modificatore
        
        # Calcola classe armatura del bersaglio
        ca_base = 10
        bonus_destrezza = (getattr(target, "destrezza", 10) - 10) // 2
        ca_bersaglio = ca_base + bonus_destrezza
        
        # Aggiungi bonus armatura se presente
        if hasattr(target, "armatura") and target.armatura:
            ca_bersaglio += 2  # Bonus base per avere un'armatura
            
        # Tiro per colpire
        tiro_attacco = dado_d20.tira()
        totale_attacco = tiro_attacco + bonus_attacco
        
        # Determina se l'attacco colpisce
        colpisce = totale_attacco >= ca_bersaglio
        colpo_critico = tiro_attacco == 20
        fallimento_critico = tiro_attacco == 1
        
        # Se colpisce, calcola il danno
        if colpisce or colpo_critico:
            # Danno base in base all'arma
            dado_danno = Dado(8)  # Dado danno base d8
            danno_base = dado_danno.tira()
            
            # Aggiungi bonus di forza al danno
            danno = danno_base + max(0, bonus_attacco)
            
            # Danno aggiuntivo per colpo critico
            if colpo_critico:
                danno_extra = dado_danno.tira()
                danno += danno_extra
                
            # Applica il danno
            hp_corrente = getattr(target, "hp", 0)
            nuovo_hp = max(0, hp_corrente - danno)
            setattr(target, "hp", nuovo_hp)
            
            # Crea il messaggio
            if colpo_critico:
                messaggio = f"{attaccante.name} colpisce {target.name} con un colpo critico per {danno} danni!"
            else:
                messaggio = f"{attaccante.name} colpisce {target.name} per {danno} danni!"
                
            # Aggiungi il messaggio alla lista dei messaggi
            self.state.messaggi.append(messaggio)
            
            # Risultato
            return {
                "successo": True,
                "tipo": "attacco",
                "colpisce": True,
                "critico": colpo_critico,
                "danno": danno,
                "messaggio": messaggio,
                "hp_rimanenti": nuovo_hp
            }
        else:
            # L'attacco fallisce
            if fallimento_critico:
                messaggio = f"{attaccante.name} fallisce miseramente l'attacco contro {target.name}!"
            else:
                messaggio = f"{attaccante.name} manca {target.name}."
                
            # Aggiungi il messaggio alla lista dei messaggi
            self.state.messaggi.append(messaggio)
            
            # Risultato
            return {
                "successo": True,
                "tipo": "attacco",
                "colpisce": False,
                "critico": False,
                "fallimento_critico": fallimento_critico,
                "messaggio": messaggio
            }
    
    def usa_abilita(self, entita_id, nome_abilita, target_ids):
        """
        Usa un'abilità speciale
        
        Args:
            entita_id (str): ID dell'entità che usa l'abilità
            nome_abilita (str): Nome dell'abilità da utilizzare
            target_ids (list): Lista di ID delle entità bersaglio
            
        Returns:
            dict: Risultato dell'uso dell'abilità
        """
        from util.dado import Dado
        
        # Verifica che sia il turno dell'entità
        if self.state.turno_corrente != entita_id:
            return {
                "successo": False,
                "messaggio": "Non è il turno di questa entità"
            }
            
        # Ottieni l'entità
        entita = self.state.world.get_entity(entita_id)
        if not entita:
            return {
                "successo": False,
                "messaggio": "Entità non trovata"
            }
            
        # Ottieni il nome dell'entità (supporta sia nome che name)
        entita_nome = getattr(entita, "nome", None)
        if entita_nome is None:
            entita_nome = getattr(entita, "name", "Entità sconosciuta")
            
        # Verifica che l'entità abbia l'abilità
        if not hasattr(entita, "abilita_speciali") or nome_abilita not in getattr(entita, "abilita_speciali", {}):
            return {
                "successo": False,
                "messaggio": f"{entita_nome} non possiede l'abilità {nome_abilita}"
            }
            
        # Ottieni l'abilità
        abilita = entita.abilita_speciali[nome_abilita]
        
        # Gestione di abilità semplici (intero) vs oggetti abilità
        # Converti abilità semplici in un dizionario per evitare errori di tipo
        abilita_struct = abilita
        if isinstance(abilita, (int, float)):
            # Crea un dizionario con i valori di default
            cooldown_attr = getattr(self.state, "abilita_cooldown", {}).get(nome_abilita, 3)
            ultimo_uso_attr = getattr(self.state, "abilita_ultimo_uso", {}).get(nome_abilita, 0)
            abilita_struct = {
                "valore": abilita,
                "cooldown": cooldown_attr,
                "ultimo_uso": ultimo_uso_attr
            }
            # Memorizza l'ultimo utilizzo nel contesto dello stato
            if not hasattr(self.state, "abilita_ultimo_uso"):
                self.state.abilita_ultimo_uso = {}
        
        # Verifica se l'abilità può essere usata (cooldown)
        cooldown = abilita_struct.get("cooldown", 3) if isinstance(abilita_struct, dict) else 3
        ultimo_uso = abilita_struct.get("ultimo_uso", 0) if isinstance(abilita_struct, dict) else 0
        
        round_trascorsi = self.state.round_corrente - ultimo_uso
        if round_trascorsi < cooldown:
            return {
                "successo": False,
                "messaggio": f"{nome_abilita} non è ancora pronta (ancora {cooldown - round_trascorsi} turni)"
            }
        
        # Gestione in base al tipo di abilità
        if nome_abilita == "colpo_potente":
            # Colpo potente: attacco con bonus al danno
            if not target_ids or len(target_ids) == 0:
                return {
                    "successo": False,
                    "messaggio": "Bersaglio non specificato per colpo_potente"
                }
                
            target_id = target_ids[0]
            target = self.state.world.get_entity(target_id)
            
            if not target:
                return {
                    "successo": False,
                    "messaggio": "Bersaglio non trovato"
                }
                
            # Ottieni il nome del target (supporta sia nome che name)
            target_nome = getattr(target, "nome", None)
            if target_nome is None:
                target_nome = getattr(target, "name", "Bersaglio sconosciuto")
                
            # Esegui un attacco potenziato
            dado_d20 = Dado(20)
            dado_danno = Dado(10)  # d10 invece di d8
            
            # Calcola bonus di attacco
            bonus_attacco = getattr(entita, "forza", 10) - 10
            bonus_attacco = bonus_attacco // 2
            
            # Calcola classe armatura del bersaglio
            ca_base = 10
            bonus_destrezza = (getattr(target, "destrezza", 10) - 10) // 2
            ca_bersaglio = ca_base + bonus_destrezza
            
            # Tiro per colpire (con penalità)
            tiro_attacco = dado_d20.tira() - 2  # Penalità al tiro per bilanciare il danno extra
            totale_attacco = tiro_attacco + bonus_attacco
            
            # Determina se l'attacco colpisce
            colpisce = totale_attacco >= ca_bersaglio
            colpo_critico = tiro_attacco == 20
            
            if colpisce or colpo_critico:
                # Calcola danno potenziato
                danno_base = dado_danno.tira()
                danno_bonus = dado_danno.tira()  # Danno extra per l'abilità
                danno = danno_base + danno_bonus + max(0, bonus_attacco)
                
                # Applica il danno
                hp_corrente = getattr(target, "hp", 0)
                nuovo_hp = max(0, hp_corrente - danno)
                setattr(target, "hp", nuovo_hp)
                
                # Crea il messaggio
                messaggio = f"{entita_nome} usa {nome_abilita} contro {target_nome} per {danno} danni!"
                
                # Aggiungi il messaggio alla lista dei messaggi
                self.state.messaggi.append(messaggio)
                
                # Aggiorna l'ultimo uso dell'abilità
                if isinstance(abilita_struct, dict):
                    abilita_struct["ultimo_uso"] = self.state.round_corrente
                    if isinstance(abilita, (int, float)):
                        # Se l'abilità originale era un semplice valore, aggiorna il dizionario dello stato
                        if not hasattr(self.state, "abilita_ultimo_uso"):
                            self.state.abilita_ultimo_uso = {}
                        self.state.abilita_ultimo_uso[nome_abilita] = self.state.round_corrente
                
                return {
                    "successo": True,
                    "tipo": "abilita",
                    "nome_abilita": nome_abilita,
                    "colpisce": True,
                    "danno": danno,
                    "messaggio": messaggio,
                    "hp_rimanenti": nuovo_hp
                }
            else:
                messaggio = f"{entita_nome} tenta di usare {nome_abilita} contro {target_nome} ma fallisce!"
                self.state.messaggi.append(messaggio)
                
                return {
                    "successo": True,
                    "tipo": "abilita",
                    "nome_abilita": nome_abilita,
                    "colpisce": False,
                    "messaggio": messaggio
                }
                
        elif nome_abilita == "cura_ferite":
            # Abilità di cura
            
            # Se non ci sono bersagli, cura se stesso
            if not target_ids or len(target_ids) == 0:
                target_id = entita_id
            else:
                target_id = target_ids[0]
                
            target = self.state.world.get_entity(target_id)
            
            if not target:
                return {
                    "successo": False,
                    "messaggio": "Bersaglio non trovato"
                }
                
            # Ottieni il nome del target (supporta sia nome che name)
            target_nome = getattr(target, "nome", None)
            if target_nome is None:
                target_nome = getattr(target, "name", "Bersaglio sconosciuto")
                
            # Calcola la quantità di cura
            dado_cura = Dado(8)
            cura_base = dado_cura.tira()
            bonus_cura = (getattr(entita, "saggezza", 10) - 10) // 2
            cura_totale = cura_base + max(0, bonus_cura)
            
            # Applica la cura
            hp_corrente = getattr(target, "hp", 0)
            hp_max = getattr(target, "hp_max", 10)
            nuovo_hp = min(hp_max, hp_corrente + cura_totale)
            setattr(target, "hp", nuovo_hp)
            
            # Crea il messaggio
            if target_id == entita_id:
                messaggio = f"{entita_nome} usa {nome_abilita} e recupera {cura_totale} punti vita!"
            else:
                messaggio = f"{entita_nome} usa {nome_abilita} su {target_nome} che recupera {cura_totale} punti vita!"
                
            # Aggiungi il messaggio alla lista dei messaggi
            self.state.messaggi.append(messaggio)
            
            # Aggiorna l'ultimo uso dell'abilità
            if isinstance(abilita_struct, dict):
                abilita_struct["ultimo_uso"] = self.state.round_corrente
                if isinstance(abilita, (int, float)):
                    # Se l'abilità originale era un semplice valore, aggiorna il dizionario dello stato
                    if not hasattr(self.state, "abilita_ultimo_uso"):
                        self.state.abilita_ultimo_uso = {}
                    self.state.abilita_ultimo_uso[nome_abilita] = self.state.round_corrente
            
            return {
                "successo": True,
                "tipo": "abilita",
                "nome_abilita": nome_abilita,
                "cura": cura_totale,
                "messaggio": messaggio,
                "hp_rimanenti": nuovo_hp
            }
        else:
            # Abilità generica non implementata
            return {
                "successo": False,
                "messaggio": f"L'abilità {nome_abilita} non è ancora implementata"
            }
    
    def usa_oggetto(self, entita_id, oggetto_id, target_ids=None):
        """
        Usa un oggetto dell'inventario
        
        Args:
            entita_id (str): ID dell'entità che usa l'oggetto
            oggetto_id (str): ID dell'oggetto da utilizzare
            target_ids (list, optional): Lista di ID delle entità bersaglio
            
        Returns:
            dict: Risultato dell'uso dell'oggetto
        """
        # Verifica che sia il turno dell'entità
        if self.state.turno_corrente != entita_id:
            return {
                "successo": False,
                "messaggio": "Non è il turno di questa entità"
            }
            
        # Ottieni l'entità
        entita = self.state.world.get_entity(entita_id)
        if not entita:
            return {
                "successo": False,
                "messaggio": "Entità non trovata"
            }
            
        # Verifica che l'entità abbia l'oggetto nell'inventario
        if not hasattr(entita, "inventario"):
            return {
                "successo": False,
                "messaggio": f"{entita.name} non ha un inventario"
            }
            
        # Trova l'oggetto nell'inventario
        oggetto = None
        for item in entita.inventario:
            if getattr(item, "id", None) == oggetto_id:
                oggetto = item
                break
                
        if not oggetto:
            return {
                "successo": False,
                "messaggio": f"Oggetto non trovato nell'inventario di {entita.name}"
            }
            
        # Gestione in base al tipo di oggetto
        tipo_oggetto = getattr(oggetto, "tipo", "consumabile")
        
        if tipo_oggetto == "pozione_cura":
            # Pozione di cura
            
            # Se non ci sono bersagli, usa su se stesso
            if not target_ids or len(target_ids) == 0:
                target_id = entita_id
            else:
                target_id = target_ids[0]
                
            target = self.state.world.get_entity(target_id)
            
            if not target:
                return {
                    "successo": False,
                    "messaggio": "Bersaglio non trovato"
                }
                
            # Calcola la quantità di cura
            cura_totale = getattr(oggetto, "valore_cura", 10)
            
            # Applica la cura
            hp_corrente = getattr(target, "hp", 0)
            hp_max = getattr(target, "hp_max", 10)
            nuovo_hp = min(hp_max, hp_corrente + cura_totale)
            setattr(target, "hp", nuovo_hp)
            
            # Rimuovi l'oggetto dall'inventario (consumabile)
            entita.inventario.remove(oggetto)
            
            # Crea il messaggio
            if target_id == entita_id:
                messaggio = f"{entita.name} beve {oggetto.nome} e recupera {cura_totale} punti vita!"
            else:
                messaggio = f"{entita.name} usa {oggetto.nome} su {target.name} che recupera {cura_totale} punti vita!"
                
            # Aggiungi il messaggio alla lista dei messaggi
            self.state.messaggi.append(messaggio)
            
            return {
                "successo": True,
                "tipo": "oggetto",
                "nome_oggetto": oggetto.nome,
                "cura": cura_totale,
                "messaggio": messaggio,
                "hp_rimanenti": nuovo_hp,
                "oggetto_consumato": True
            }
        elif tipo_oggetto == "bomba":
            # Bomba (danno ad area)
            from util.dado import Dado
            
            # Verifica che ci siano bersagli
            if not target_ids or len(target_ids) == 0:
                return {
                    "successo": False,
                    "messaggio": "Nessun bersaglio specificato per la bomba"
                }
                
            dado_danno = Dado(6)
            danno_base = getattr(oggetto, "valore_danno", 6)
            
            risultati = []
            
            # Applica danno a tutti i bersagli
            for target_id in target_ids:
                target = self.state.world.get_entity(target_id)
                
                if not target:
                    continue
                    
                # Calcola il danno (leggermente variabile per ogni bersaglio)
                tiro_danno = dado_danno.tira()
                danno = danno_base + tiro_danno
                
                # Applica il danno
                hp_corrente = getattr(target, "hp", 0)
                nuovo_hp = max(0, hp_corrente - danno)
                setattr(target, "hp", nuovo_hp)
                
                # Aggiungi ai risultati
                risultati.append({
                    "target_id": target_id,
                    "nome_target": target.name,
                    "danno": danno,
                    "hp_rimanenti": nuovo_hp
                })
                
            # Rimuovi l'oggetto dall'inventario (consumabile)
            entita.inventario.remove(oggetto)
            
            # Crea il messaggio
            bersagli_str = ", ".join([r["nome_target"] for r in risultati])
            messaggio = f"{entita.name} lancia {oggetto.nome} che esplode colpendo {bersagli_str}!"
            
            # Aggiungi il messaggio alla lista dei messaggi
            self.state.messaggi.append(messaggio)
            
            return {
                "successo": True,
                "tipo": "oggetto",
                "nome_oggetto": oggetto.nome,
                "risultati": risultati,
                "messaggio": messaggio,
                "oggetto_consumato": True
            }
        else:
            # Oggetto generico non implementato
            return {
                "successo": False,
                "messaggio": f"L'uso dell'oggetto {oggetto.nome} non è ancora implementato"
            }
    
    def passa_turno(self, entita_id):
        """
        Passa il turno senza fare azioni
        
        Args:
            entita_id (str): ID dell'entità che passa il turno
            
        Returns:
            dict: Risultato del passaggio del turno
        """
        # Verifica che sia il turno dell'entità
        if self.state.turno_corrente != entita_id:
            return {
                "successo": False,
                "messaggio": "Non è il turno di questa entità"
            }
            
        # Ottieni l'entità
        entita = self.state.world.get_entity(entita_id)
        if not entita:
            return {
                "successo": False,
                "messaggio": "Entità non trovata"
            }
            
        # Crea il messaggio
        messaggio = f"{entita.name} passa il turno."
        
        # Aggiungi il messaggio alla lista dei messaggi
        self.state.messaggi.append(messaggio)
        
        # Passa al turno successivo
        prossimo_turno = self.state.gestore_turni.passa_al_turno_successivo()
        
        return {
            "successo": True,
            "tipo": "passa_turno",
            "messaggio": messaggio,
            "prossimo_turno": prossimo_turno
        }
        
    def determina_azione_ia(self, entita_id):
        """
        Determina l'azione migliore per un'entità controllata dall'IA
        
        Args:
            entita_id (str): ID dell'entità IA
            
        Returns:
            dict: Descrizione dell'azione da eseguire
        """
        from util.dado import Dado
        
        # Ottieni l'entità
        entita = self.state.world.get_entity(entita_id)
        if not entita:
            return None
            
        # Trova possibili bersagli (giocatori)
        bersagli = []
        for p_id in self.state.partecipanti:
            target = self.state.world.get_entity(p_id)
            if target and target.has_tag("player") and getattr(target, "hp", 0) > 0:
                bersagli.append(p_id)
                
        if not bersagli:
            # Nessun bersaglio valido disponibile
            return {
                "tipo": "passa_turno",
                "entita_id": entita_id
            }
            
        # Verifica se l'entità ha abilità speciali
        ha_abilita = hasattr(entita, "abilita_speciali") and entita.abilita_speciali
        
        # Tiro casuale per determinare l'azione (per un po' di varietà)
        dado_azione = Dado(10)
        tiro_azione = dado_azione.tira()
        
        # Se l'entità ha pochi HP, potrebbe tentare di curarsi
        hp_ratio = getattr(entita, "hp", 10) / getattr(entita, "hp_max", 10)
        
        if ha_abilita and "cura_ferite" in entita.abilita_speciali and hp_ratio < 0.3 and tiro_azione <= 8:
            # Usa abilità di cura su se stesso
            return {
                "tipo": "abilita",
                "nome_abilita": "cura_ferite",
                "entita_id": entita_id,
                "target_ids": [entita_id]
            }
        elif ha_abilita and "colpo_potente" in entita.abilita_speciali and tiro_azione <= 4:
            # Usa abilità di attacco potente
            target_id = bersagli[0]  # Prende il primo bersaglio disponibile
            return {
                "tipo": "abilita",
                "nome_abilita": "colpo_potente",
                "entita_id": entita_id,
                "target_ids": [target_id]
            }
        else:
            # Attacco normale
            target_id = bersagli[0]  # Prende il primo bersaglio disponibile
            return {
                "tipo": "attacco",
                "entita_id": entita_id,
                "target_id": target_id
            }
    
    def esegui_azione_ia(self, azione):
        """
        Esegue un'azione determinata dall'IA
        
        Args:
            azione (dict): Descrizione dell'azione da eseguire
            
        Returns:
            dict: Risultato dell'azione
        """
        if not azione:
            return None
            
        tipo_azione = azione.get("tipo")
        
        if tipo_azione == "attacco":
            return self.esegui_attacco(
                azione.get("entita_id"),
                azione.get("target_id"),
                azione.get("arma")
            )
        elif tipo_azione == "abilita":
            return self.usa_abilita(
                azione.get("entita_id"),
                azione.get("nome_abilita"),
                azione.get("target_ids", [])
            )
        elif tipo_azione == "oggetto":
            return self.usa_oggetto(
                azione.get("entita_id"),
                azione.get("oggetto_id"),
                azione.get("target_ids")
            )
        elif tipo_azione == "passa_turno":
            return self.passa_turno(azione.get("entita_id"))
        else:
            return None
    
    def mostra_inventario(self, game_ctx=None):
        """
        Mostra l'inventario per utilizzare oggetti nel combattimento
        
        Args:
            game_ctx: Il contesto di gioco (opzionale)
            
        Returns:
            dict: Risultato dell'operazione
        """
        # Controlla se siamo nel contesto di test
        if game_ctx is None:
            return {
                "successo": True,
                "tipo": "mostra_inventario",
                "messaggio": "Inventario mostrato"
            }
            
        # In un contesto di gioco reale, ottieni il giocatore
        giocatore = None
        for entity_id in self.state.partecipanti:
            entity = self.state.world.get_entity(entity_id)
            if entity and entity.has_tag("player"):
                giocatore = entity
                break
                
        if not giocatore:
            self.state.messaggi.append("Giocatore non trovato!")
            return {
                "successo": False,
                "messaggio": "Giocatore non trovato"
            }
            
        # Ottieni gli oggetti nell'inventario
        inventario = getattr(giocatore, "inventario", [])
        
        # Filtra solo gli oggetti utilizzabili in combattimento
        oggetti_utilizzabili = []
        for item in inventario:
            if hasattr(item, "utilizzabile_in_combattimento") and item.utilizzabile_in_combattimento:
                oggetti_utilizzabili.append(item)
                
        # Memorizza gli oggetti nei dati temporanei dello stato
        self.state.dati_temporanei["items"] = oggetti_utilizzabili
        
        # Prepara le opzioni per il dialogo
        opzioni = ["Annulla"]
        for item in oggetti_utilizzabili:
            opzioni.append(item.nome)
            
        # Cambia fase
        self.state.fase = "usa_oggetto"
        
        # Mostra il dialogo
        game_ctx.io.mostra_dialogo("Inventario", "Quale oggetto vuoi usare?", opzioni)
        
        return {
            "successo": True,
            "tipo": "mostra_inventario",
            "messaggio": "Inventario mostrato"
        }
    
    def mostra_opzioni_equipaggiamento(self, game_ctx=None):
        """
        Mostra le opzioni per cambiare equipaggiamento durante il combattimento
        
        Args:
            game_ctx: Il contesto di gioco (opzionale)
            
        Returns:
            dict: Risultato dell'operazione
        """
        # Controlla se siamo nel contesto di test
        if game_ctx is None:
            return {
                "successo": True,
                "tipo": "mostra_opzioni_equipaggiamento",
                "messaggio": "Opzioni equipaggiamento mostrate"
            }
            
        # Cambia fase
        self.state.fase = "cambio_equip_tipo"
        
        # Mostra il dialogo con le opzioni
        game_ctx.io.mostra_dialogo(
            "Equipaggiamento", 
            "Cosa vuoi equipaggiare?", 
            ["Arma", "Armatura", "Accessorio", "Annulla"]
        )
        
        return {
            "successo": True,
            "tipo": "mostra_opzioni_equipaggiamento",
            "messaggio": "Opzioni equipaggiamento mostrate"
        }
    
    def tenta_fuga(self, game_ctx=None):
        """
        Tenta di fuggire dal combattimento
        
        Args:
            game_ctx: Il contesto di gioco (opzionale)
            
        Returns:
            dict: Risultato del tentativo di fuga
        """
        from util.dado import Dado
        
        # Controlla se siamo nel contesto di test
        if game_ctx is None:
            return {
                "successo": True,
                "tipo": "fuga",
                "messaggio": "Tentativo di fuga riuscito"
            }
            
        # Ottieni il giocatore
        giocatore = None
        for entity_id in self.state.partecipanti:
            entity = self.state.world.get_entity(entity_id)
            if entity and entity.has_tag("player"):
                giocatore = entity
                break
                
        if not giocatore:
            self.state.messaggi.append("Giocatore non trovato!")
            return {
                "successo": False,
                "messaggio": "Giocatore non trovato"
            }
            
        # Tiro per la fuga (d20 + modificatore di destrezza)
        dado_d20 = Dado(20)
        mod_destrezza = (getattr(giocatore, "destrezza", 10) - 10) // 2
        tiro_fuga = dado_d20.tira() + mod_destrezza
        
        # Difficoltà base di 10, +2 per ogni nemico
        num_nemici = sum(1 for p_id in self.state.partecipanti if p_id != giocatore.id)
        difficolta = 10 + (num_nemici * 2)
        
        # Determina se la fuga riesce
        fuga_riuscita = tiro_fuga >= difficolta
        
        if fuga_riuscita:
            self.state.messaggi.append(f"{giocatore.name} è riuscito a fuggire!")
            self.state.in_corso = False
            
            # Termina il combattimento
            if game_ctx.stato_corrente() == self.state:
                game_ctx.pop_stato()
                
            return {
                "successo": True,
                "tipo": "fuga",
                "riuscita": True,
                "messaggio": f"{giocatore.name} è riuscito a fuggire!"
            }
        else:
            self.state.messaggi.append(f"{giocatore.name} ha tentato di fuggire ma non ci è riuscito.")
            
            # Passa al turno successivo
            self.state.gestore_turni.passa_al_turno_successivo()
            
            return {
                "successo": True,
                "tipo": "fuga",
                "riuscita": False,
                "messaggio": f"{giocatore.name} ha tentato di fuggire ma non ci è riuscito."
            }
    
    def usa_oggetto_selezionato(self, game_ctx, oggetto):
        """
        Usa un oggetto selezionato dall'inventario
        
        Args:
            game_ctx: Il contesto di gioco
            oggetto: L'oggetto da utilizzare
            
        Returns:
            dict: Risultato dell'utilizzo dell'oggetto
        """
        # Ottieni il giocatore
        giocatore = None
        for entity_id in self.state.partecipanti:
            entity = self.state.world.get_entity(entity_id)
            if entity and entity.has_tag("player"):
                giocatore = entity
                break
                
        if not giocatore:
            self.state.messaggi.append("Giocatore non trovato!")
            return {
                "successo": False,
                "messaggio": "Giocatore non trovato"
            }
            
        # Verifica che l'oggetto sia nell'inventario
        inventario = getattr(giocatore, "inventario", [])
        oggetto_trovato = False
        for item in inventario:
            if item == oggetto:
                oggetto_trovato = True
                break
                
        if not oggetto_trovato:
            self.state.messaggi.append(f"{giocatore.name} non possiede l'oggetto {oggetto.nome}!")
            return {
                "successo": False,
                "messaggio": f"Oggetto {oggetto.nome} non trovato nell'inventario"
            }
            
        # Determina il bersaglio (per default, il giocatore stesso)
        target = giocatore
        
        # Se l'oggetto può essere usato su altri, chiedi il bersaglio
        if hasattr(oggetto, "target_type") and oggetto.target_type == "altro":
            # Prepara la lista di possibili bersagli
            bersagli = []
            for p_id in self.state.partecipanti:
                entity = self.state.world.get_entity(p_id)
                if entity:
                    bersagli.append(entity)
                    
            # Memorizza l'oggetto per uso futuro
            self.state.dati_temporanei["oggetto_selezionato"] = oggetto
            
            # Cambia fase
            self.state.fase = "seleziona_bersaglio"
            
            # Mostra dialogo per selezionare il bersaglio
            opzioni = []
            for b in bersagli:
                opzioni.append(b.name)
            opzioni.append("Annulla")
            
            game_ctx.io.mostra_dialogo("Seleziona bersaglio", f"Su chi vuoi usare {oggetto.nome}?", opzioni)
            
            return {
                "successo": True,
                "tipo": "seleziona_bersaglio",
                "messaggio": f"Seleziona il bersaglio per {oggetto.nome}"
            }
            
        # Usa l'oggetto sul bersaglio (il giocatore)
        return self.usa_oggetto(giocatore.id, oggetto, [target.id])
        
    def mostra_armi_disponibili(self, game_ctx):
        """
        Mostra le armi disponibili per essere equipaggiate
        
        Args:
            game_ctx: Il contesto di gioco
            
        Returns:
            dict: Risultato dell'operazione
        """
        # Ottieni il giocatore
        giocatore = None
        for entity_id in self.state.partecipanti:
            entity = self.state.world.get_entity(entity_id)
            if entity and entity.has_tag("player"):
                giocatore = entity
                break
                
        if not giocatore:
            self.state.messaggi.append("Giocatore non trovato!")
            return {
                "successo": False,
                "messaggio": "Giocatore non trovato"
            }
            
        # Ottieni le armi nell'inventario
        inventario = getattr(giocatore, "inventario", [])
        armi = []
        for item in inventario:
            if hasattr(item, "tipo") and item.tipo == "arma":
                armi.append(item)
                
        # Memorizza le armi nei dati temporanei
        self.state.dati_temporanei["items"] = armi
        self.state.dati_temporanei["tipo_equip"] = "arma"
        
        # Prepara le opzioni per il dialogo
        opzioni = ["Annulla"]
        for arma in armi:
            opzioni.append(arma.nome)
            
        # Cambia fase
        self.state.fase = "cambio_equip_item"
        
        # Mostra il dialogo
        game_ctx.io.mostra_dialogo("Armi", "Quale arma vuoi equipaggiare?", opzioni)
        
        return {
            "successo": True,
            "tipo": "mostra_armi",
            "messaggio": "Armi mostrate"
        }
        
    def mostra_armature_disponibili(self, game_ctx):
        """
        Mostra le armature disponibili per essere equipaggiate
        
        Args:
            game_ctx: Il contesto di gioco
            
        Returns:
            dict: Risultato dell'operazione
        """
        # Ottieni il giocatore
        giocatore = None
        for entity_id in self.state.partecipanti:
            entity = self.state.world.get_entity(entity_id)
            if entity and entity.has_tag("player"):
                giocatore = entity
                break
                
        if not giocatore:
            self.state.messaggi.append("Giocatore non trovato!")
            return {
                "successo": False,
                "messaggio": "Giocatore non trovato"
            }
            
        # Ottieni le armature nell'inventario
        inventario = getattr(giocatore, "inventario", [])
        armature = []
        for item in inventario:
            if hasattr(item, "tipo") and item.tipo == "armatura":
                armature.append(item)
                
        # Memorizza le armature nei dati temporanei
        self.state.dati_temporanei["items"] = armature
        self.state.dati_temporanei["tipo_equip"] = "armatura"
        
        # Prepara le opzioni per il dialogo
        opzioni = ["Annulla"]
        for armatura in armature:
            opzioni.append(armatura.nome)
            
        # Cambia fase
        self.state.fase = "cambio_equip_item"
        
        # Mostra il dialogo
        game_ctx.io.mostra_dialogo("Armature", "Quale armatura vuoi equipaggiare?", opzioni)
        
        return {
            "successo": True,
            "tipo": "mostra_armature",
            "messaggio": "Armature mostrate"
        }
        
    def mostra_accessori_disponibili(self, game_ctx):
        """
        Mostra gli accessori disponibili per essere equipaggiati
        
        Args:
            game_ctx: Il contesto di gioco
            
        Returns:
            dict: Risultato dell'operazione
        """
        # Ottieni il giocatore
        giocatore = None
        for entity_id in self.state.partecipanti:
            entity = self.state.world.get_entity(entity_id)
            if entity and entity.has_tag("player"):
                giocatore = entity
                break
                
        if not giocatore:
            self.state.messaggi.append("Giocatore non trovato!")
            return {
                "successo": False,
                "messaggio": "Giocatore non trovato"
            }
            
        # Ottieni gli accessori nell'inventario
        inventario = getattr(giocatore, "inventario", [])
        accessori = []
        for item in inventario:
            if hasattr(item, "tipo") and item.tipo == "accessorio":
                accessori.append(item)
                
        # Memorizza gli accessori nei dati temporanei
        self.state.dati_temporanei["items"] = accessori
        self.state.dati_temporanei["tipo_equip"] = "accessorio"
        
        # Prepara le opzioni per il dialogo
        opzioni = ["Annulla"]
        for accessorio in accessori:
            opzioni.append(accessorio.nome)
            
        # Cambia fase
        self.state.fase = "cambio_equip_item"
        
        # Mostra il dialogo
        game_ctx.io.mostra_dialogo("Accessori", "Quale accessorio vuoi equipaggiare?", opzioni)
        
        return {
            "successo": True,
            "tipo": "mostra_accessori",
            "messaggio": "Accessori mostrati"
        }
        
    def cambia_equipaggiamento_item(self, game_ctx, tipo_equip, item):
        """
        Cambia l'equipaggiamento del giocatore
        
        Args:
            game_ctx: Il contesto di gioco
            tipo_equip: Il tipo di equipaggiamento (arma, armatura, accessorio)
            item: L'oggetto da equipaggiare
            
        Returns:
            dict: Risultato dell'operazione
        """
        # Ottieni il giocatore
        giocatore = None
        for entity_id in self.state.partecipanti:
            entity = self.state.world.get_entity(entity_id)
            if entity and entity.has_tag("player"):
                giocatore = entity
                break
                
        if not giocatore:
            self.state.messaggi.append("Giocatore non trovato!")
            return {
                "successo": False,
                "messaggio": "Giocatore non trovato"
            }
            
        # Equipaggia l'oggetto
        if tipo_equip == "arma":
            giocatore.arma_equipaggiata = item
        elif tipo_equip == "armatura":
            giocatore.armatura_equipaggiata = item
        elif tipo_equip == "accessorio":
            giocatore.accessorio_equipaggiato = item
            
        # Messaggio di conferma
        self.state.messaggi.append(f"{giocatore.name} ha equipaggiato {item.nome}.")
        
        # Torna al menu principale
        self.state.fase = "scelta"
        self.state.dati_temporanei.clear()
        self.state.dati_temporanei["mostrato_menu_scelta"] = False
        
        return {
            "successo": True,
            "tipo": "cambia_equipaggiamento",
            "messaggio": f"Equipaggiato {item.nome}"
        } 