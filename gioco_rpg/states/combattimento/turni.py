class GestoreTurni:
    """
    Classe per gestire i turni durante il combattimento
    """
    def __init__(self, state):
        """
        Inizializza il gestore dei turni
        
        Args:
            state: Lo stato del combattimento
        """
        self.state = state
        self.indice_turno_corrente = 0
    
    def calcola_iniziativa(self):
        """
        Calcola l'iniziativa per tutti i partecipanti e ordina la lista
        
        Returns:
            list: Lista ordinata di ID dei partecipanti in base all'iniziativa
        """
        from util.dado import Dado
        dado = Dado(20)
        
        # Calcola i valori di iniziativa per ogni partecipante
        iniziative = {}
        for p_id in self.state.partecipanti:
            entita = self.state.world.get_entity(p_id)
            if entita:
                # Calcola valore iniziativa basato su destrezza
                destrezza = getattr(entita, "destrezza", 10)
                mod_destrezza = (destrezza - 10) // 2
                tiro_dado = dado.tira() + mod_destrezza
                setattr(entita, "iniziativa", tiro_dado)
                iniziative[p_id] = tiro_dado
                
        # Ordina i partecipanti in base all'iniziativa (alto -> basso)
        self.state.ordine_iniziativa = sorted(
            self.state.partecipanti,
            key=lambda p_id: iniziative.get(p_id, 0),
            reverse=True
        )
        
        return self.state.ordine_iniziativa
    
    def inizia_combattimento(self):
        """
        Inizializza il primo turno del combattimento
        
        Returns:
            str: ID dell'entità di cui è il turno
        """
        # Calcola l'iniziativa se non è già stata calcolata
        if not hasattr(self.state, 'ordine_iniziativa') or not self.state.ordine_iniziativa:
            self.calcola_iniziativa()
            
        # Imposta il turno al primo giocatore nella lista di iniziativa
        if self.state.ordine_iniziativa:
            self.indice_turno_corrente = 0
            self.state.turno_corrente = self.state.ordine_iniziativa[0]
            self.state.fase_corrente = "azione"
        
        return self.state.turno_corrente
    
    def passa_al_turno_successivo(self):
        """
        Passa al turno dell'entità successiva nell'ordine di iniziativa
        
        Returns:
            str: ID dell'entità di cui è il turno ora
        """
        if not hasattr(self.state, 'ordine_iniziativa') or not self.state.ordine_iniziativa:
            return None
            
        # Passa al prossimo indice
        self.indice_turno_corrente = (self.indice_turno_corrente + 1) % len(self.state.ordine_iniziativa)
        
        # Se torniamo all'inizio, aumenta il contatore dei round
        if self.indice_turno_corrente == 0:
            self.state.round_corrente += 1
            
        # Imposta il nuovo turno
        self.state.turno_corrente = self.state.ordine_iniziativa[self.indice_turno_corrente]
        
        return self.state.turno_corrente
    
    def turno_entita(self, entita_id):
        """
        Verifica se è il turno dell'entità specificata
        
        Args:
            entita_id (str): ID dell'entità da verificare
            
        Returns:
            bool: True se è il turno dell'entità, False altrimenti
        """
        return self.state.turno_corrente == entita_id
    
    def entita_viventi(self):
        """
        Restituisce una lista di entità ancora vive nel combattimento
        
        Returns:
            list: Lista di ID delle entità ancora vive
        """
        vivi = []
        for p_id in self.state.partecipanti:
            entita = self.state.world.get_entity(p_id)
            if entita and getattr(entita, "hp", 0) > 0:
                vivi.append(p_id)
                
        return vivi
    
    def controlla_fine_combattimento(self):
        """
        Controlla se il combattimento è terminato (tutti i nemici morti o giocatore morto)
        
        Returns:
            bool: True se il combattimento è terminato, False altrimenti
        """
        # Trova i giocatori e i nemici vivi
        giocatori_vivi = []
        nemici_vivi = []
        
        for p_id in self.state.partecipanti:
            entita = self.state.world.get_entity(p_id)
            if entita and getattr(entita, "hp", 0) > 0:
                if entita.has_tag("player"):
                    giocatori_vivi.append(p_id)
                elif entita.has_tag("nemico") or entita.has_tag("ostile"):
                    nemici_vivi.append(p_id)
        
        # Il combattimento termina se tutti i nemici sono morti o tutti i giocatori sono morti
        return len(nemici_vivi) == 0 or len(giocatori_vivi) == 0
    
    def determina_vincitore(self):
        """
        Determina chi ha vinto il combattimento
        
        Returns:
            str: "giocatore" se ha vinto il giocatore, "nemico" se hanno vinto i nemici
        """
        # Trova i giocatori e i nemici vivi
        giocatori_vivi = []
        nemici_vivi = []
        
        for p_id in self.state.partecipanti:
            entita = self.state.world.get_entity(p_id)
            if entita and getattr(entita, "hp", 0) > 0:
                if entita.has_tag("player"):
                    giocatori_vivi.append(p_id)
                elif entita.has_tag("nemico") or entita.has_tag("ostile"):
                    nemici_vivi.append(p_id)
        
        # Determina il vincitore
        if len(nemici_vivi) == 0:
            return "giocatore"
        else:
            return "nemico"

    def attacco_nemico(self, giocatore, gioco):
        """
        Esegue l'attacco dell'avversario
        
        Args:
            giocatore: Il giocatore
            gioco: L'istanza del gioco
        """
        # Visualizza animazione di attacco nemico
        gioco.io.mostra_animazione({
            "type": "animation",
            "id": "anim_attacco_nemico",
            "animation": "enemy_attack",
            "x": 600,
            "y": 350,
            "duration": 1.0,
            "target_x": 200,
            "target_y": 350
        })
        
        # Calcola tiro d'attacco
        tiro_attacco = self.state.dado_d20.tira()
        
        # Aggiungi bonus dell'avversario
        tiro_attacco += self.state.avversario.forza
        
        # Verifica se l'attacco va a segno
        if tiro_attacco >= giocatore.difesa:
            # Calcola danno
            danno = max(1, self.state.avversario.forza + self.state.dado_d20.tira() // 2)
            
            # Effetto visivo del danno
            gioco.io.mostra_animazione({
                "type": "animation",
                "id": "anim_danno_giocatore",
                "animation": "hit_effect",
                "x": 200,
                "y": 350,
                "duration": 0.5
            })
            
            # Applica danno
            giocatore.hp = max(0, giocatore.hp - danno)
            
            # Mostra messaggio
            gioco.io.mostra_messaggio(f"{self.state.avversario.nome} ti ha colpito per {danno} danni!")
            
            # Effetto sonoro
            gioco.io.play_sound({
                "sound_id": "player_hit",
                "volume": 0.7
            })
        else:
            # Messaggio di attacco fallito
            gioco.io.mostra_messaggio(f"{self.state.avversario.nome} ha mancato il colpo!")
            
            # Effetto sonoro
            gioco.io.play_sound({
                "sound_id": "enemy_miss",
                "volume": 0.5
            })
        
        # Aggiorna le barre HP
        self.state.ui.aggiorna_barre_hp(gioco)
        
        # Controlla se il combattimento è finito
        if self.controlla_fine_combattimento():
            return
            
        # Torna alla fase di scelta per il turno successivo
        self.state.fase = "scelta"
        self.state.round_corrente += 1
        self.state.dati_temporanei.clear()
        self.state.dati_temporanei["mostrato_menu_scelta"] = False
    
    def mostra_stato_combattimento(self, giocatore, gioco):
        """
        Mostra lo stato attuale del combattimento
        
        Args:
            giocatore: Il giocatore
            gioco: L'istanza del gioco
        """
        gioco.io.mostra_messaggio("\n" + "="*60)
        gioco.io.mostra_messaggio(f"COMBATTIMENTO: {giocatore.nome} vs {self.state.avversario.nome}")
        gioco.io.mostra_messaggio(f"Turno: {self.state.turno}")
        gioco.io.mostra_messaggio(f"HP {giocatore.nome}: {giocatore.hp}/{giocatore.hp_max} | HP {self.state.avversario.nome}: {self.state.avversario.hp}/{self.state.avversario.hp_max}")
        
        # Mostra anche l'equipaggiamento attuale del giocatore
        arma = giocatore.arma if isinstance(giocatore.arma, str) else (giocatore.arma.nome if giocatore.arma else "Nessuna")
        armatura = giocatore.armatura if isinstance(giocatore.armatura, str) else (giocatore.armatura.nome if giocatore.armatura else "Nessuna")
        
        # Gestione degli accessori
        accessori_nomi = []
        for acc in giocatore.accessori:
            if isinstance(acc, str):
                accessori_nomi.append(acc)
            else:
                accessori_nomi.append(acc.nome)
        accessori = ", ".join(accessori_nomi) if accessori_nomi else "Nessuno"
        
        # Mostra equipaggiamento del giocatore
        gioco.io.mostra_messaggio(f"{giocatore.nome} - Arma: {arma} | Armatura: {armatura} | Accessori: {accessori}")
        gioco.io.mostra_messaggio(f"{giocatore.nome} - Forza: {giocatore.forza} | Difesa: {giocatore.difesa}")
        
        # Mostra informazioni sul nemico se disponibili
        if hasattr(self.state.avversario, 'armi') and self.state.avversario.armi:
            gioco.io.mostra_messaggio(f"{self.state.avversario.nome} - Armi: {', '.join(self.state.avversario.armi)}")
        
        if hasattr(self.state.avversario, 'armatura') and self.state.avversario.armatura:
            gioco.io.mostra_messaggio(f"{self.state.avversario.nome} - Armatura: {self.state.avversario.armatura}")
            
        if hasattr(self.state.avversario, 'forza'):
            gioco.io.mostra_messaggio(f"{self.state.avversario.nome} - Forza: {self.state.avversario.forza}")
            
        if hasattr(self.state.avversario, 'descrizione') and self.state.turno == 1:
            # Mostra la descrizione solo al primo turno
            gioco.io.mostra_messaggio(f"\n{self.state.avversario.descrizione}")
            
        gioco.io.mostra_messaggio("="*60) 