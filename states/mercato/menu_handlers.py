from entities.giocatore import Giocatore

class MenuMercatoHandler:
    def __init__(self, mercato_state):
        """
        Inizializza il gestore dei menu per il mercato.
        
        Args:
            mercato_state: L'istanza dello stato mercato
        """
        self.mercato_state = mercato_state
    
    def mostra_menu_principale(self, game_ctx):
        """
        Mostra il menu principale del mercato.
        
        Args:
            game_ctx: Il contesto di gioco
        """
        game_ctx.io.mostra_menu(
            "Cosa vuoi fare al mercato?",
            [
                ("Compra pozioni", lambda: self._imposta_fase("compra_pozione")),
                ("Vendi oggetti", lambda: self._imposta_fase("vendi_oggetto_lista")),
                ("Parla con qualcuno", lambda: self._imposta_fase("parla_npg_lista")),
                ("Esplora", lambda: self._imposta_fase("esplora_oggetti_lista")),
                ("Visualizza mappa", lambda: self._imposta_fase("visualizza_mappa")),
                ("Lascia il mercato", lambda: self._esci_mercato(game_ctx))
            ],
            id_menu="menu_mercato"
        )
    
    def mostra_compra_pozione(self, game_ctx):
        """
        Mostra il menu per comprare pozioni.
        
        Args:
            game_ctx: Il contesto di gioco
        """
        opzioni = [
            ("Pozione di cura (10 oro)", lambda: self._acquista_pozione(game_ctx, "Pozione di cura", 10)),
            ("Pozione di mana (15 oro)", lambda: self._acquista_pozione(game_ctx, "Pozione di mana", 15)),
            ("Pozione di forza (25 oro)", lambda: self._acquista_pozione(game_ctx, "Pozione di forza", 25)),
            ("Indietro", lambda: self._imposta_fase("menu_principale"))
        ]
        
        game_ctx.io.mostra_menu(
            f"Hai {game_ctx.giocatore.oro} oro. Che pozione vuoi comprare?",
            opzioni,
            id_menu="menu_pozioni"
        )
    
    def mostra_vendi_oggetto_lista(self, gioco):
        """
        Mostra il menu per la vendita di oggetti.
        
        Args:
            gioco: Il contesto di gioco
        """
        # Ottieni gli oggetti vendibili (escludi quelli equipaggiati)
        oggetti_vendibili = gioco.giocatore.get_oggetti_vendibili()
        
        if not oggetti_vendibili:
            gioco.io.mostra_messaggio("Non hai oggetti da vendere!")
            self._imposta_fase("menu_principale")
            return
        
        opzioni = []
        for oggetto in oggetti_vendibili:
            valore_vendita = oggetto.valore // 2  # Vendi a metà prezzo
            opzioni.append(
                (f"{oggetto.nome} ({valore_vendita} oro)", lambda obj=oggetto: self._seleziona_oggetto_da_vendere(gioco, obj))
            )
        
        opzioni.append(("Indietro", lambda: self._imposta_fase("menu_principale")))
        
        gioco.io.mostra_menu(
            "Quale oggetto vuoi vendere?",
            opzioni,
            id_menu="menu_vendi"
        )
    
    def mostra_vendi_oggetto_conferma(self, gioco):
        """
        Mostra il menu di conferma per la vendita dell'oggetto selezionato.
        
        Args:
            gioco: Il contesto di gioco
        """
        if not self.mercato_state.oggetto_selezionato:
            gioco.io.mostra_messaggio("Nessun oggetto selezionato!")
            self._imposta_fase("menu_principale")
            return
        
        oggetto = self.mercato_state.oggetto_selezionato
        valore_vendita = oggetto.valore // 2  # Vendi a metà prezzo
        
        opzioni = [
            (f"Sì, vendi {oggetto.nome} per {valore_vendita} oro", lambda: self._vendi_oggetto_completato(gioco, True)),
            ("No, torna indietro", lambda: self._vendi_oggetto_completato(gioco, False))
        ]
        
        gioco.io.mostra_menu(
            f"Vuoi davvero vendere {oggetto.nome} per {valore_vendita} oro?",
            opzioni,
            id_menu="menu_conferma_vendita"
        )
    
    def mostra_parla_npg_lista(self, gioco):
        """
        Mostra il menu per parlare con gli NPG.
        
        Args:
            gioco: Il contesto di gioco
        """
        npg_vicini = self.mercato_state.ottieni_npg_vicini(gioco, 2)
        
        if not npg_vicini:
            gioco.io.mostra_messaggio("Non c'è nessuno nelle vicinanze con cui parlare!")
            self._imposta_fase("menu_principale")
            return
        
        opzioni = []
        for nome_npg, npg in npg_vicini.items():
            opzioni.append(
                (f"Parla con {nome_npg}", lambda n=nome_npg: self._parla_con_npg(gioco, n))
            )
        
        opzioni.append(("Indietro", lambda: self._imposta_fase("menu_principale")))
        
        gioco.io.mostra_menu(
            "Con chi vuoi parlare?",
            opzioni,
            id_menu="menu_parla_npg"
        )
    
    def mostra_esplora_oggetti_lista(self, gioco):
        """
        Mostra il menu per esplorare gli oggetti interattivi.
        
        Args:
            gioco: Il contesto di gioco
        """
        oggetti_vicini = self.mercato_state.ottieni_oggetti_vicini(gioco, 2)
        
        if not oggetti_vicini:
            gioco.io.mostra_messaggio("Non ci sono oggetti interessanti nelle vicinanze!")
            self._imposta_fase("menu_principale")
            return
        
        opzioni = []
        for nome_oggetto, oggetto in oggetti_vicini.items():
            opzioni.append(
                (f"Esamina {nome_oggetto}", lambda o=nome_oggetto: self._interagisci_con_oggetto(gioco, o))
            )
        
        opzioni.append(("Indietro", lambda: self._imposta_fase("menu_principale")))
        
        gioco.io.mostra_menu(
            "Cosa vuoi esplorare?",
            opzioni,
            id_menu="menu_esplora"
        )
    
    # Metodi helper privati
    def _imposta_fase(self, nuova_fase):
        """
        Imposta una nuova fase per lo stato mercato.
        
        Args:
            nuova_fase: La nuova fase da impostare
        """
        self.mercato_state.fase = nuova_fase
        self.mercato_state.ui_aggiornata = False  # Forza l'aggiornamento dell'UI
    
    def _esci_mercato(self, gioco):
        """
        Esce dallo stato mercato.
        
        Args:
            gioco: Il contesto di gioco
        """
        gioco.io.mostra_messaggio("Lasci il mercato.")
        gioco.pop_stato()
    
    def _seleziona_oggetto_da_vendere(self, gioco, oggetto):
        """
        Seleziona un oggetto da vendere.
        
        Args:
            gioco: Il contesto di gioco
            oggetto: L'oggetto da vendere
        """
        self.mercato_state.oggetto_selezionato = oggetto
        self._imposta_fase("vendi_oggetto_conferma")
    
    def _vendi_oggetto_completato(self, gioco, conferma):
        """
        Completa la vendita di un oggetto.
        
        Args:
            gioco: Il contesto di gioco
            conferma: True se l'utente conferma la vendita, False altrimenti
        """
        if conferma and self.mercato_state.oggetto_selezionato:
            oggetto = self.mercato_state.oggetto_selezionato
            valore_vendita = oggetto.valore // 2
            
            # Rimuovi l'oggetto dall'inventario
            if gioco.giocatore.rimuovi_item(oggetto):
                # Aggiungi oro al giocatore
                gioco.giocatore.aggiungi_oro(valore_vendita)
                gioco.io.mostra_messaggio(f"Hai venduto {oggetto.nome} per {valore_vendita} oro!")
            else:
                gioco.io.mostra_messaggio("Non è stato possibile vendere l'oggetto!")
                
        # Reset dell'oggetto selezionato e torna al menu principale
        self.mercato_state.oggetto_selezionato = None
        self._imposta_fase("menu_principale")
    
    def _acquista_pozione(self, game_ctx, nome_pozione, prezzo):
        """
        Acquista una pozione se il giocatore ha abbastanza oro.
        
        Args:
            game_ctx: Il contesto di gioco
            nome_pozione: Il nome della pozione da acquistare
            prezzo: Il prezzo della pozione
        """
        # Verifica se il giocatore ha abbastanza oro
        if game_ctx.giocatore.oro < prezzo:
            game_ctx.io.mostra_messaggio(f"Non hai abbastanza oro! Ti mancano {prezzo - game_ctx.giocatore.oro} monete.")
            return
        
        # Crea la pozione in base al tipo
        if nome_pozione == "Pozione di cura":
            pozione = {"nome": nome_pozione, "tipo": "pozione", "effetto": {"cura": 20}, "descrizione": "Ripristina 20 punti vita."}
        elif nome_pozione == "Pozione di mana":
            pozione = {"nome": nome_pozione, "tipo": "pozione", "effetto": {"mana": 15}, "descrizione": "Ripristina 15 punti mana."}
        elif nome_pozione == "Pozione di forza":
            pozione = {"nome": nome_pozione, "tipo": "pozione", "effetto": {"forza": 5, "durata": 3}, "descrizione": "Aumenta la forza di 5 per 3 turni."}
        else:
            game_ctx.io.mostra_messaggio("Pozione non disponibile!")
            return
        
        # Rimuovi l'oro dal giocatore
        game_ctx.giocatore.rimuovi_oro(prezzo)
        
        # Aggiungi la pozione all'inventario
        game_ctx.giocatore.aggiungi_pozione(pozione)
        
        game_ctx.io.mostra_messaggio(f"Hai acquistato {nome_pozione} per {prezzo} oro!")
    
    def _parla_con_npg(self, gioco, nome_npg):
        """
        Avvia una conversazione con un NPG.
        
        Args:
            gioco: Il contesto di gioco
            nome_npg: Il nome dell'NPG con cui parlare
        """
        # Salva il nome dell'NPG attivo
        self.mercato_state.nome_npg_attivo = nome_npg
        
        # Ottieni l'NPG corrispondente
        npg = self.mercato_state.npg_presenti.get(nome_npg)
        if not npg:
            gioco.io.mostra_messaggio(f"Non trovi {nome_npg} nei paraggi.")
            self._imposta_fase("menu_principale")
            return
        
        # Avvia lo stato di dialogo
        from states.dialogo import DialogoState
        dialogo_state = DialogoState(gioco, npg)
        gioco.push_stato(dialogo_state)
    
    def _interagisci_con_oggetto(self, gioco, nome_oggetto):
        """
        Interagisce con un oggetto.
        
        Args:
            gioco: Il contesto di gioco
            nome_oggetto: Il nome dell'oggetto con cui interagire
        """
        # Ottieni l'oggetto corrispondente
        oggetto = self.mercato_state.oggetti_interattivi.get(nome_oggetto)
        if not oggetto:
            gioco.io.mostra_messaggio(f"Non trovi {nome_oggetto} nei paraggi.")
            self._imposta_fase("menu_principale")
            return
        
        # Interagisci con l'oggetto
        if hasattr(oggetto, 'interagisci'):
            messaggio = oggetto.interagisci(gioco.giocatore, gioco)
            gioco.io.mostra_messaggio(messaggio)
        else:
            gioco.io.mostra_messaggio(f"Esamini {oggetto.nome}: {oggetto.descrizione}")
        
        # Torna al menu principale
        self._imposta_fase("menu_principale") 