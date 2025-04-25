class MenuTavernaHandler:
    def __init__(self, taverna_state):
        """
        Inizializza il gestore dei menu per la taverna.
        
        Args:
            taverna_state: L'istanza dello stato taverna
        """
        self.taverna_state = taverna_state
    
    def mostra_menu_principale(self, gioco):
        """
        Mostra il menu principale della taverna.
        
        Args:
            gioco: Il contesto di gioco
        """
        # Lista delle opzioni di menu
        opzioni = [
            ("Parla con qualcuno", lambda: self._imposta_fase("parla_npg")),
            ("Viaggia verso un'altra zona", lambda: self._viaggia(gioco)),
            ("Mostra statistiche", lambda: self._mostra_statistiche(gioco)),
            ("Combatti con un nemico", lambda: self._imposta_fase("scegli_nemico")),
            ("Sfida un NPC", lambda: self._imposta_fase("combatti_npg")),
            ("Esplora oggetti nella taverna", lambda: self._imposta_fase("esplora_oggetti")),
            ("Mostra inventario", lambda: self._mostra_inventario(gioco)),
            ("Prova abilità", lambda: self._prova_abilita(gioco)),
            ("Visualizza mappa", lambda: self._imposta_fase("visualizza_mappa")),
            ("Muoviti sulla mappa", lambda: self._imposta_fase("muovi_mappa")),
            ("Interagisci con l'ambiente", lambda: self._imposta_fase("interagisci_ambiente")),
            ("Salva partita", lambda: self._imposta_fase("salva_partita")),
            ("Esci dal gioco", lambda: self._conferma_uscita(gioco))
        ]
        
        # Effetto audio per apertura menu
        gioco.io.play_sound({
            "sound_id": "menu_open",
            "volume": 0.5
        })
        
        # Mostra il menu con le opzioni
        gioco.io.mostra_menu(
            "Cosa vuoi fare alla taverna?",
            opzioni,
            id_menu="menu_taverna"
        )
        
        # Imposta il menu attivo
        self.taverna_state.menu_attivo = "menu_principale"
    
    # Metodi per i vari menu e sottomenu
    def gestisci_dialogo_npg(self, gioco):
        """
        Mostra il menu per parlare con gli NPG.
        
        Args:
            gioco: Il contesto di gioco
        """
        # Ottieni la lista di NPG da mostrare
        npg_lista = []
        
        if gioco.giocatore.mappa_corrente:
            npg_vicini = gioco.giocatore.ottieni_npg_vicini(gioco.gestore_mappe)
            if npg_vicini:
                npg_lista = list(npg_vicini.values())
        
        # Se non ci sono NPG vicini, usa gli NPG della taverna
        if not npg_lista:
            npg_lista = list(self.taverna_state.npg_presenti.values())
        
        # Crea le opzioni per il menu
        opzioni = []
        for npg in npg_lista:
            opzioni.append((f"Parla con {npg.nome}", lambda n=npg: self._parla_con_npg(gioco, n)))
        
        # Aggiungi opzione per tornare indietro
        opzioni.append(("Torna indietro", lambda: self._imposta_fase("menu_principale")))
        
        # Effetto audio
        gioco.io.play_sound({
            "sound_id": "dialog_open",
            "volume": 0.5
        })
        
        # Mostra il menu
        gioco.io.mostra_menu(
            "Con chi vuoi parlare?",
            opzioni,
            id_menu="menu_dialogo_npg"
        )
        
        # Imposta il menu attivo
        self.taverna_state.menu_attivo = "selezione_npg"
    
    def gestisci_scegli_nemico(self, gioco):
        """
        Mostra il menu per scegliere un nemico da combattere.
        
        Args:
            gioco: Il contesto di gioco
        """
        # Opzioni di scelta nemico
        opzioni = [
            ("Nemico casuale", lambda: self._seleziona_nemico(gioco, "casuale")),
            ("Nemico casuale facile", lambda: self._seleziona_nemico(gioco, "facile")),
            ("Nemico casuale medio", lambda: self._seleziona_nemico(gioco, "medio")),
            ("Nemico casuale difficile", lambda: self._seleziona_nemico(gioco, "difficile")),
            ("Scegli un tipo specifico", lambda: self._imposta_fase("scegli_tipo_mostro")),
            ("Torna indietro", lambda: self._imposta_fase("menu_principale"))
        ]
        
        # Effetto audio
        gioco.io.play_sound({
            "sound_id": "combat_menu",
            "volume": 0.6
        })
        
        # Mostra il menu
        gioco.io.mostra_menu(
            "Come vuoi scegliere il nemico?",
            opzioni,
            id_menu="menu_scegli_nemico"
        )
        
        # Imposta il menu attivo
        self.taverna_state.menu_attivo = "scelta_modalita_nemico"
    
    def gestisci_tipi_mostri(self, gioco):
        """
        Mostra il menu con i tipi di mostri disponibili.
        
        Args:
            gioco: Il contesto di gioco
        """
        from entities.nemico import Nemico
        
        # Ottieni i tipi di mostri disponibili
        tipi_mostri = Nemico.ottieni_tipi_mostri()
        
        if not tipi_mostri:
            gioco.io.mostra_messaggio("Non ci sono tipi di mostri disponibili!")
            self._imposta_fase("menu_principale")
            return
        
        # Crea le opzioni per il menu
        opzioni = []
        for tipo in tipi_mostri:
            tipo_formattato = tipo.replace('_', ' ').title()
            opzioni.append((tipo_formattato, lambda t=tipo: self._seleziona_tipo_mostro(gioco, t)))
        
        # Aggiungi opzione per tornare indietro
        opzioni.append(("Torna indietro", lambda: self._imposta_fase("scegli_nemico")))
        
        # Memorizza i tipi di mostri originali
        self.taverna_state.dati_contestuali["tipi_mostri"] = tipi_mostri
        
        # Mostra il menu
        gioco.io.mostra_menu(
            "Scegli un tipo di mostro:",
            opzioni,
            id_menu="menu_tipi_mostri"
        )
        
        # Imposta il menu attivo
        self.taverna_state.menu_attivo = "scelta_tipo_mostro"
    
    def gestisci_combatti_npg(self, gioco):
        """
        Mostra il menu per combattere con gli NPG.
        
        Args:
            gioco: Il contesto di gioco
        """
        # Ottieni la lista di NPG da mostrare
        npg_lista = []
        
        if gioco.giocatore.mappa_corrente:
            npg_vicini = gioco.giocatore.ottieni_npg_vicini(gioco.gestore_mappe)
            if npg_vicini:
                npg_lista = list(npg_vicini.values())
        
        # Se non ci sono NPG vicini, usa gli NPG della taverna
        if not npg_lista:
            npg_lista = list(self.taverna_state.npg_presenti.values())
        
        # Crea le opzioni per il menu
        opzioni = []
        for npg in npg_lista:
            opzioni.append((f"Combatti con {npg.nome}", lambda n=npg: self._conferma_combattimento_npg(gioco, n)))
        
        # Aggiungi opzione per tornare indietro
        opzioni.append(("Torna indietro", lambda: self._imposta_fase("menu_principale")))
        
        # Memorizza la lista di NPG per gestire la scelta
        self.taverna_state.dati_contestuali["npg_lista"] = npg_lista
        
        # Effetto audio
        gioco.io.play_sound({
            "sound_id": "combat_menu",
            "volume": 0.6
        })
        
        # Mostra il menu
        gioco.io.mostra_menu(
            "Con chi vuoi combattere?",
            opzioni,
            id_menu="menu_combatti_npg"
        )
        
        # Imposta il menu attivo
        self.taverna_state.menu_attivo = "selezione_npg_combattimento"
    
    def gestisci_esplorazione_oggetti(self, gioco):
        """
        Mostra il menu per esplorare gli oggetti nella taverna.
        
        Args:
            gioco: Il contesto di gioco
        """
        # Ottieni gli oggetti interattivi
        oggetti_lista = []
        
        if gioco.giocatore.mappa_corrente:
            oggetti_vicini = gioco.giocatore.ottieni_oggetti_vicini(gioco.gestore_mappe)
            if oggetti_vicini:
                for pos, obj in oggetti_vicini.items():
                    oggetti_lista.append({
                        "nome": obj.nome,
                        "stato": obj.stato,
                        "posizione": pos,
                        "oggetto": obj,
                        "tipo": "mappa"
                    })
        
        # Aggiungi gli oggetti della taverna
        for nome, oggetto in self.taverna_state.oggetti_interattivi.items():
            oggetti_lista.append({
                "nome": oggetto.nome,
                "stato": oggetto.stato,
                "oggetto": oggetto,
                "tipo": "locale"
            })
        
        # Effetto audio
        gioco.io.play_sound({
            "sound_id": "menu_open",
            "volume": 0.6
        })
        
        if not oggetti_lista:
            # Se non ci sono oggetti, mostra un messaggio e torna al menu principale
            gioco.io.mostra_messaggio("Non ci sono oggetti con cui interagire nelle vicinanze.")
            self._imposta_fase("menu_principale")
            return
            
        # Crea le opzioni per il menu
        opzioni = []
        for oggetto_info in oggetti_lista:
            opzioni.append(
                (f"{oggetto_info['nome']} [{oggetto_info['stato']}]", 
                 lambda o=oggetto_info: self._seleziona_oggetto(gioco, o))
            )
        
        # Aggiungi opzione per tornare indietro
        opzioni.append(("Torna indietro", lambda: self._imposta_fase("menu_principale")))
        
        # Memorizza la lista degli oggetti
        self.taverna_state.dati_contestuali["oggetti_lista"] = oggetti_lista
        
        # Mostra il menu
        gioco.io.mostra_menu(
            "Scegli un oggetto con cui interagire:",
            opzioni,
            id_menu="menu_esplora_oggetti"
        )
        
        # Imposta il menu attivo
        self.taverna_state.menu_attivo = "selezione_oggetti"
    
    def gestisci_salva_partita(self, gioco):
        """
        Salva la partita corrente.
        
        Args:
            gioco: Il contesto di gioco
        """
        # Esegui il salvataggio
        gioco.salva()
        
        # Mostra notifica di salvataggio
        self.taverna_state.ui_handler.mostra_notifica_salvataggio(gioco)
        
        # Aggiorna la fase
        self._imposta_fase("menu_principale")
    
    def gestisci_visualizza_mappa(self, gioco):
        """
        Gestisce la visualizzazione della mappa.
        
        Args:
            gioco: Il contesto di gioco
        """
        from .movimento import visualizza_mappa
        visualizza_mappa(self.taverna_state, gioco)
    
    def gestisci_muovi_mappa(self, gioco):
        """
        Gestisce il movimento sulla mappa.
        
        Args:
            gioco: Il contesto di gioco
        """
        from .movimento import gestisci_movimento
        gestisci_movimento(self.taverna_state, gioco)
    
    def gestisci_interagisci_ambiente(self, gioco):
        """
        Gestisce l'interazione con l'ambiente.
        
        Args:
            gioco: Il contesto di gioco
        """
        from .movimento import interagisci_ambiente
        interagisci_ambiente(self.taverna_state, gioco)
    
    # Metodi helper privati
    def _imposta_fase(self, nuova_fase):
        """
        Imposta una nuova fase per lo stato taverna.
        
        Args:
            nuova_fase: La nuova fase da impostare
        """
        self.taverna_state.fase = nuova_fase
        self.taverna_state.ui_aggiornata = False  # Forza l'aggiornamento dell'UI
        
        # Se necessario, aggiorna il contesto
        self.taverna_state.dati_contestuali.clear()
        
        # Esegui l'azione associata alla fase
        if hasattr(self, f"gestisci_{nuova_fase}"):
            getattr(self, f"gestisci_{nuova_fase}")(self.taverna_state.gioco)
    
    def _viaggia(self, gioco):
        """
        Gestisce il passaggio ad un'altra zona.
        
        Args:
            gioco: Il contesto di gioco
        """
        from states.scelta_mappa_state import SceltaMappaState
        self.taverna_state._esegui_transizione(gioco, SceltaMappaState(gioco))
    
    def _mostra_statistiche(self, gioco):
        """
        Mostra le statistiche del giocatore.
        
        Args:
            gioco: Il contesto di gioco
        """
        gioco.io.mostra_statistiche_giocatore(gioco.giocatore)
        # Dopo aver mostrato le statistiche, torna al menu principale
        self._imposta_fase("menu_principale")
    
    def _mostra_inventario(self, gioco):
        """
        Mostra l'inventario del giocatore.
        
        Args:
            gioco: Il contesto di gioco
        """
        from states.inventario import GestioneInventarioState
        self.taverna_state._esegui_transizione(gioco, GestioneInventarioState())
    
    def _prova_abilita(self, gioco):
        """
        Passa alla schermata di prova abilità.
        
        Args:
            gioco: Il contesto di gioco
        """
        from states.prova_abilita import ProvaAbilitaState
        self.taverna_state._esegui_transizione(gioco, ProvaAbilitaState())
    
    def _conferma_uscita(self, gioco):
        """
        Mostra una richiesta di conferma per l'uscita dal gioco.
        
        Args:
            gioco: Il contesto di gioco
        """
        opzioni = [
            ("Sì, esci", lambda: self._esci_dal_gioco(gioco)),
            ("No, torna al gioco", lambda: self._imposta_fase("menu_principale"))
        ]
        
        gioco.io.mostra_menu(
            "Sei sicuro di voler uscire dal gioco?",
            opzioni,
            id_menu="menu_conferma_uscita"
        )
        
        self.taverna_state.menu_attivo = "conferma_uscita"
    
    def _esci_dal_gioco(self, gioco):
        """
        Esce dal gioco.
        
        Args:
            gioco: Il contesto di gioco
        """
        gioco.attivo = False
    
    def _parla_con_npg(self, gioco, npg):
        """
        Avvia un dialogo con un NPC.
        
        Args:
            gioco: Il contesto di gioco
            npg: L'oggetto NPC con cui parlare
        """
        # Effetto audio
        gioco.io.play_sound({
            "sound_id": "dialog_start",
            "volume": 0.6
        })
        
        # Avvia il dialogo con l'NPC
        from states.dialogo import DialogoState
        self.taverna_state._esegui_transizione(
            gioco, 
            DialogoState(npg), 
            tipo_transizione="fade", 
            durata=0.3
        )
        
        self.taverna_state.menu_attivo = "menu_principale"
    
    def _seleziona_nemico(self, gioco, difficolta):
        """
        Seleziona un nemico di una certa difficoltà.
        
        Args:
            gioco: Il contesto di gioco
            difficolta: La difficoltà del nemico
        """
        from entities.nemico import Nemico
        
        # Crea il nemico
        if difficolta == "casuale":
            nemico = Nemico.crea_casuale()
        else:
            nemico = Nemico.crea_casuale(difficolta)
        
        # Avvia il combattimento
        self._avvia_combattimento_con_nemico(gioco, nemico)
    
    def _seleziona_tipo_mostro(self, gioco, tipo_mostro):
        """
        Seleziona un nemico di un tipo specifico.
        
        Args:
            gioco: Il contesto di gioco
            tipo_mostro: Il tipo di mostro da creare
        """
        from entities.nemico import Nemico
        
        # Crea il nemico con il tipo specifico
        nemico = Nemico(nome="", tipo_mostro=tipo_mostro)
        
        # Avvia il combattimento
        self._avvia_combattimento_con_nemico(gioco, nemico)
    
    def _avvia_combattimento_con_nemico(self, gioco, nemico):
        """
        Avvia un combattimento con un nemico.
        
        Args:
            gioco: Il contesto di gioco
            nemico: Il nemico da combattere
        """
        from states.combattimento import CombattimentoState
        
        # Effetto audio
        gioco.io.play_sound({
            "sound_id": "battle_start",
            "volume": 0.7
        })
        
        # Transizione al combattimento
        self.taverna_state._esegui_transizione(
            gioco, 
            CombattimentoState(nemico=nemico), 
            tipo_transizione="battle_transition", 
            durata=0.5
        )
        
        self.taverna_state.menu_attivo = "menu_principale"
    
    def _conferma_combattimento_npg(self, gioco, npg):
        """
        Chiede conferma prima di combattere con un NPC.
        
        Args:
            gioco: Il contesto di gioco
            npg: L'NPC da combattere
        """
        # Memorizza l'NPC selezionato
        self.taverna_state.dati_contestuali["npg_selezionato"] = npg
        
        opzioni = [
            (f"Sì, attacca {npg.nome}", lambda: self._combatti_con_npg(gioco)),
            ("No, torna indietro", lambda: self._imposta_fase("menu_principale"))
        ]
        
        # Mostra il menu di conferma
        gioco.io.mostra_menu(
            f"Sei sicuro di voler attaccare {npg.nome}?",
            opzioni,
            id_menu="menu_conferma_combattimento"
        )
        
        # Imposta il menu attivo
        self.taverna_state.menu_attivo = "conferma_combattimento_npg"
    
    def _combatti_con_npg(self, gioco):
        """
        Avvia un combattimento con l'NPC selezionato.
        
        Args:
            gioco: Il contesto di gioco
        """
        from states.combattimento import CombattimentoState
        
        # Ottieni l'NPC selezionato
        npg = self.taverna_state.dati_contestuali.get("npg_selezionato")
        
        if npg:
            # Effetto audio
            gioco.io.play_sound({
                "sound_id": "battle_start",
                "volume": 0.7
            })
            
            # Transizione al combattimento
            self.taverna_state._esegui_transizione(
                gioco, 
                CombattimentoState(npg_ostile=npg), 
                tipo_transizione="battle_transition", 
                durata=0.5
            )
            
            self.taverna_state.menu_attivo = "menu_principale"
        else:
            gioco.io.mostra_messaggio("NPC non trovato!")
            self._imposta_fase("menu_principale")
    
    def _seleziona_oggetto(self, gioco, oggetto_info):
        """
        Seleziona un oggetto per interagire.
        
        Args:
            gioco: Il contesto di gioco
            oggetto_info: Le informazioni sull'oggetto
        """
        oggetto = oggetto_info["oggetto"]
        
        # Effetto audio
        gioco.io.play_sound({
            "sound_id": "item_interact",
            "volume": 0.6
        })
        
        opzioni = [
            ("Interagisci", lambda: self._interagisci_con_oggetto(gioco, oggetto)),
            ("Torna alla lista", lambda: self._imposta_fase("esplora_oggetti"))
        ]
        
        # Mostra la descrizione dell'oggetto
        gioco.io.mostra_menu(
            f"Oggetto: {oggetto.nome}\n{oggetto.descrizione}",
            opzioni,
            id_menu="menu_interagisci_oggetto"
        )
    
    def _interagisci_con_oggetto(self, gioco, oggetto):
        """
        Interagisce con un oggetto.
        
        Args:
            gioco: Il contesto di gioco
            oggetto: L'oggetto con cui interagire
        """
        # Effetto audio
        gioco.io.play_sound({
            "sound_id": "item_use",
            "volume": 0.7
        })
        
        # Interagisci con l'oggetto
        risultato = oggetto.interagisci(gioco.giocatore)
        
        # Mostra il risultato dell'interazione
        gioco.io.mostra_messaggio(risultato if risultato else f"Hai interagito con {oggetto.nome}")
        
        # Torna al menu principale
        self._imposta_fase("menu_principale") 