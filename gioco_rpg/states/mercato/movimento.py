class MovimentoMercatoHandler:
    def __init__(self, mercato_state):
        """
        Inizializza il gestore del movimento per il mercato.
        
        Args:
            mercato_state: L'istanza dello stato mercato
        """
        self.mercato_state = mercato_state
        
        # Definisci le direzioni di movimento
        self.direzioni = {
            "nord": (0, -1),
            "sud": (0, 1),
            "est": (1, 0),
            "ovest": (-1, 0)
        }
    
    def muovi_giocatore(self, gioco, direzione):
        """
        Muove il giocatore nella direzione specificata.
        
        Args:
            gioco: Il contesto di gioco
            direzione: La direzione in cui muoversi
            
        Returns:
            bool: True se il movimento è avvenuto, False altrimenti
        """
        if direzione not in self.direzioni:
            return False
            
        # Ottieni la mappa corrente
        mappa = gioco.gestore_mappe.ottieni_mappa_attuale()
        if not mappa:
            return False
            
        # Ottieni la posizione attuale del giocatore
        giocatore_x, giocatore_y = gioco.giocatore.x, gioco.giocatore.y
        
        # Calcola la nuova posizione
        dx, dy = self.direzioni[direzione]
        nuova_x, nuova_y = giocatore_x + dx, giocatore_y + dy
        
        # Verifica se la nuova posizione è valida
        if not mappa.posizione_valida(nuova_x, nuova_y):
            gioco.io.mostra_messaggio("Non puoi andare in quella direzione.")
            return False
            
        # Verifica se la nuova posizione contiene ostacoli
        if mappa.contiene_ostacoli(nuova_x, nuova_y):
            gioco.io.mostra_messaggio("C'è un ostacolo in quella direzione.")
            return False
            
        # Verifica punti di uscita dalla mappa
        punto_uscita = mappa.get_punto_uscita(nuova_x, nuova_y)
        if punto_uscita:
            destinazione, dest_x, dest_y = punto_uscita
            self._cambia_mappa(gioco, destinazione, dest_x, dest_y)
            return True
            
        # Esegui il movimento
        gioco.giocatore.x = nuova_x
        gioco.giocatore.y = nuova_y
        
        # Descrivi l'ambiente dopo il movimento
        self._descrivi_ambiente(gioco)
        
        return True
    
    def _cambia_mappa(self, gioco, mappa_dest, x=None, y=None):
        """
        Cambia la mappa del giocatore.
        
        Args:
            gioco: Il contesto di gioco
            mappa_dest: Il nome della mappa di destinazione
            x: La posizione X di destinazione (se None, usa la posizione iniziale)
            y: La posizione Y di destinazione (se None, usa la posizione iniziale)
            
        Returns:
            bool: True se il cambio mappa è avvenuto, False altrimenti
        """
        # Verifica se la mappa di destinazione esiste
        mappa = gioco.gestore_mappe.ottieni_mappa(mappa_dest)
        if not mappa:
            gioco.io.mostra_messaggio(f"La mappa {mappa_dest} non esiste!")
            return False
            
        # Se le coordinate non sono specificate, usa la posizione iniziale
        if x is None or y is None:
            x, y = mappa.pos_iniziale_giocatore
            
        # Esegui il cambio mappa
        gioco.cambia_mappa(mappa_dest, x, y)
        
        # Descrivi l'ambiente dopo il cambio mappa
        self._descrivi_ambiente(gioco)
        
        # Forza l'aggiornamento dell'UI dopo il cambio mappa
        self.mercato_state.ui_aggiornata = False
        
        return True
    
    def _descrivi_ambiente(self, gioco):
        """
        Descrive l'ambiente circostante al giocatore.
        
        Args:
            gioco: Il contesto di gioco
        """
        # Ottieni la mappa corrente
        mappa = gioco.gestore_mappe.ottieni_mappa_attuale()
        if not mappa:
            return
            
        # Ottieni la posizione del giocatore
        pos_x, pos_y = gioco.giocatore.x, gioco.giocatore.y
        
        # Ottieni la descrizione della cella
        desc_cella = mappa.get_descrizione_cella(pos_x, pos_y)
        
        if desc_cella:
            gioco.io.mostra_messaggio(desc_cella)
            
        # Ottieni oggetti e NPC vicini
        oggetti_vicini = self.mercato_state.ottieni_oggetti_vicini(gioco, 1)
        npg_vicini = self.mercato_state.ottieni_npg_vicini(gioco, 1)
        
        # Descrivi oggetti e NPC vicini
        if oggetti_vicini:
            nomi_oggetti = ", ".join(oggetti_vicini.keys())
            gioco.io.mostra_messaggio(f"Vedi: {nomi_oggetti}")
            
        if npg_vicini:
            nomi_npg = ", ".join(npg_vicini.keys())
            gioco.io.mostra_messaggio(f"Persone vicine: {nomi_npg}")
    
    def visualizza_mappa(self, gioco):
        """
        Visualizza una rappresentazione testuale della mappa.
        
        Args:
            gioco: Il contesto di gioco
        """
        # Ottieni la mappa corrente
        mappa = gioco.gestore_mappe.ottieni_mappa_attuale()
        if not mappa:
            gioco.io.mostra_messaggio("Nessuna mappa disponibile.")
            return
            
        # Ottieni le dimensioni della mappa
        larghezza, altezza = mappa.dimensioni
        
        # Crea una rappresentazione testuale della mappa
        mappa_testo = []
        
        for y in range(altezza):
            riga = []
            for x in range(larghezza):
                # Ottieni il carattere per questa posizione
                if gioco.giocatore.x == x and gioco.giocatore.y == y:
                    # Posizione del giocatore
                    riga.append("@")
                elif mappa.contiene_ostacoli(x, y):
                    # Ostacoli
                    riga.append("#")
                elif mappa.get_punto_uscita(x, y):
                    # Punti di uscita
                    riga.append("D")
                else:
                    # Terreno normale
                    riga.append(".")
            
            mappa_testo.append("".join(riga))
        
        # Visualizza la mappa
        gioco.io.mostra_messaggio("\n".join(mappa_testo))
        gioco.io.mostra_messaggio("@ = Tu, # = Ostacolo, D = Porta/Uscita, . = Terreno normale")
        
        return True 