from util.dado import Dado
from util.data_manager import get_data_manager
import json

class OggettoInterattivo:
    def __init__(self, nome, descrizione="", stato="chiuso", contenuto=None, posizione=None, token="O"):
        """
        Inizializza un oggetto interattivo nel mondo di gioco.
        
        Args:
            nome: Nome dell'oggetto
            descrizione: Descrizione testuale dell'oggetto
            stato: Stato attuale dell'oggetto (es. "chiuso", "aperto", "attivo", "rotto")
            contenuto: Lista di oggetti contenuti (se applicabile)
            posizione: Posizione dell'oggetto nel mondo di gioco (es. "taverna", "mercato", o coordinate)
            token: Token per la rappresentazione sulla mappa
        """
        self.nome = nome
        self.descrizione = descrizione
        self.stato = stato
        self.contenuto = contenuto or []  # Lista di oggetti contenuti
        self.oggetti_collegati = {}  # Dizionario di oggetti che possono essere influenzati da questo
        self.posizione = posizione  # Posizione dell'oggetto nel mondo
        self.token = token  # Token per la rappresentazione sulla mappa
        
        # Nuovi attributi
        self.descrizioni_stati = {stato: descrizione}  # Descrizioni per ogni stato
        self.stati_possibili = {}  # Dizionario delle transizioni possibili
        self.abilita_richieste = {}  # Abilità necessarie per interazioni specifiche
        self.difficolta_abilita = {}  # Difficoltà per ogni abilità
        self.messaggi_interazione = {}  # Feedback narrativi per interazioni
        self.eventi = {}  # Eventi da attivare al cambiamento di stato
        self.tipo = "oggetto_interattivo"  # Tipo dell'oggetto, utile per la serializzazione
    
    def __getstate__(self):
        """
        Prepara l'oggetto per la serializzazione pickle/JSON rimuovendo attributi non serializzabili.
        
        Returns:
            dict: Dizionario con gli attributi serializzabili dell'oggetto
        """
        # Ottieni una copia dello stato corrente (dizionario degli attributi)
        state = self.__dict__.copy()
        
        # Rimuovi eventuali attributi non serializzabili
        # Ad esempio, funzioni, metodi, oggetti complessi
        for key, value in list(state.items()):
            # Rimuovi callable (funzioni, metodi)
            if callable(value):
                del state[key]
            # Gestisci contenuto ed oggetti collegati per evitare riferimenti circolari
            elif key == 'oggetti_collegati':
                # Converti oggetti collegati in riferimenti per nome
                oggetti_riferimenti = {}
                for nome_coll, obj in state[key].items():
                    if hasattr(obj, 'nome'):
                        oggetti_riferimenti[nome_coll] = obj.nome
                    else:
                        oggetti_riferimenti[nome_coll] = str(obj)
                state[key] = oggetti_riferimenti
        
        return state

    def __setstate__(self, state):
        """
        Ripristina lo stato dell'oggetto durante la deserializzazione.
        
        Args:
            state (dict): Lo stato dell'oggetto da ripristinare
        """
        # Ripristina tutti gli attributi dallo stato
        self.__dict__.update(state)
        
        # Inizializza attributi non serializzabili che potrebbero essere mancanti
        if not hasattr(self, 'listeners') or self.listeners is None:
            self.listeners = {}
            
        # Ripristina eventuali callback come funzioni vuote
        for attr_name in dir(self):
            if attr_name.startswith('on_') and not callable(getattr(self, attr_name, None)):
                setattr(self, attr_name, lambda *args, **kwargs: None)
    
    def __str__(self):
        """
        Restituisce una rappresentazione stringa dell'oggetto.
        
        Returns:
            str: Rappresentazione dell'oggetto come stringa
        """
        return f"{self.nome} [{self.stato}]"
    
    def __repr__(self):
        """
        Restituisce una rappresentazione debug dell'oggetto.
        
        Returns:
            str: Rappresentazione debug dell'oggetto come stringa
        """
        return f"{self.__class__.__name__}(nome='{self.nome}', stato='{self.stato}')"
    
    # Implementazione della serializzazione JSON
    def to_json(self):
        """
        Converte l'oggetto in formato JSON.
        
        Returns:
            str: Rappresentazione JSON dell'oggetto
        """
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    def interagisci(self, giocatore, gioco=None):
        """
        Metodo principale di interazione. Dovrebbe essere sovrascritto nelle sottoclassi.
        """
        if gioco:
            gioco.io.mostra_messaggio(f"Non succede nulla con {self.nome}...")
    
    def descrivi(self, gioco=None):
        """
        Mostra la descrizione dell'oggetto e il suo stato attuale.
        """
        if gioco:
            gioco.io.mostra_messaggio(f"{self.nome}: {self.descrizione} [{self.stato}]")
            if self.posizione:
                gioco.io.mostra_messaggio(f"Si trova in: {self.posizione}")
    
    def collega_oggetto(self, nome_collegamento, oggetto):
        """
        Collega un altro oggetto interattivo a questo (es. una leva a una porta).
        """
        self.oggetti_collegati[nome_collegamento] = oggetto
    
    def sposta(self, nuova_posizione, gioco=None):
        """
        Sposta l'oggetto in una nuova posizione.
        """
        self.posizione = nuova_posizione
        if gioco:
            gioco.io.mostra_messaggio(f"{self.nome} è stato spostato in: {nuova_posizione}")
        
    def interagisci_specifico(self, giocatore, abilita, gioco=None):
        """
        Gestisce interazioni basate su abilità specifiche.
        """
        if abilita not in self.abilita_richieste:
            if gioco:
                gioco.io.mostra_messaggio(f"Non puoi usare {abilita} con {self.nome} in questo momento.")
            return False
            
        # Ottieni messaggio narrativo se disponibile
        if abilita in self.messaggi_interazione and gioco:
            gioco.io.mostra_messaggio(self.messaggi_interazione[abilita])
        
        # Transizione di stato se necessaria
        if abilita in self.abilita_richieste:
            nuovo_stato = self.abilita_richieste[abilita]
            if nuovo_stato in self.stati_possibili.get(self.stato, []):
                self.cambia_stato(nuovo_stato, gioco)
                return True
        
        return False
    
    def cambia_stato(self, nuovo_stato, gioco=None):
        """
        Cambia lo stato dell'oggetto e attiva eventi nel mondo.
        """
        vecchio_stato = self.stato
        if nuovo_stato in self.stati_possibili.get(vecchio_stato, []):
            self.stato = nuovo_stato
            
            # Mostra descrizione del nuovo stato
            if gioco:
                if nuovo_stato in self.descrizioni_stati:
                    gioco.io.mostra_messaggio(self.descrizioni_stati[nuovo_stato])
                else:
                    gioco.io.mostra_messaggio(f"{self.nome} è ora {nuovo_stato}.")
            
            # Attiva eventi nel mondo
            if gioco and nuovo_stato in self.eventi:
                for evento in self.eventi[nuovo_stato]:
                    evento(gioco)
            
            return True
        else:
            if gioco:
                gioco.io.mostra_messaggio(f"Impossibile cambiare {self.nome} da {vecchio_stato} a {nuovo_stato}.")
            return False
    
    def aggiungi_transizione(self, stato_corrente, stato_nuovo):
        """
        Definisce una transizione possibile tra stati.
        """
        if stato_corrente not in self.stati_possibili:
            self.stati_possibili[stato_corrente] = []
        
        if stato_nuovo not in self.stati_possibili[stato_corrente]:
            self.stati_possibili[stato_corrente].append(stato_nuovo)
    
    def imposta_descrizione_stato(self, stato, descrizione):
        """
        Definisce una descrizione per uno stato specifico.
        """
        self.descrizioni_stati[stato] = descrizione
    
    def richiedi_abilita(self, abilita, stato_risultante, difficolta=10, messaggio=None):
        """
        Definisce un'abilità che può essere usata con questo oggetto.
        """
        self.abilita_richieste[abilita] = stato_risultante
        self.difficolta_abilita[abilita] = difficolta
        
        if messaggio:
            self.messaggi_interazione[abilita] = messaggio
    
    def collega_evento(self, stato, evento):
        """
        Collega un evento da attivare quando l'oggetto entra in un certo stato.
        """
        if stato not in self.eventi:
            self.eventi[stato] = []
        
        self.eventi[stato].append(evento)
        
    def to_dict(self):
        """
        Converte l'oggetto in un dizionario serializzabile.
        
        Returns:
            dict: Rappresentazione dell'oggetto come dizionario
        """
        # Crea il dizionario base
        result = {
            'tipo': self.tipo,
            'nome': self.nome,
            'descrizione': self.descrizione,
            'stato': self.stato,
            'posizione': self.posizione,
            'token': self.token,
            'descrizioni_stati': self.descrizioni_stati,
            'stati_possibili': self.stati_possibili,
            'abilita_richieste': self.abilita_richieste,
            'difficolta_abilita': self.difficolta_abilita,
            'messaggi_interazione': self.messaggi_interazione,
        }
        
        # Gestisci il contenuto dell'oggetto
        if self.contenuto:
            try:
                # Prova a convertire gli oggetti nel contenuto in dizionari
                contenuto_serializzabile = []
                for item in self.contenuto:
                    if hasattr(item, 'to_dict') and callable(item.to_dict):
                        contenuto_serializzabile.append(item.to_dict())
                    elif isinstance(item, dict):
                        contenuto_serializzabile.append(item)
                    else:
                        contenuto_serializzabile.append({'nome': str(item)})
                result['contenuto'] = contenuto_serializzabile
            except Exception as e:
                # Fallback in caso di errore nella serializzazione del contenuto
                import logging
                logging.error(f"Errore nella serializzazione del contenuto di {self.nome}: {str(e)}")
                result['contenuto'] = [{'nome': str(item)} for item in self.contenuto]
        else:
            result['contenuto'] = []
        
        # Gestisci gli oggetti collegati
        if hasattr(self, 'oggetti_collegati') and self.oggetti_collegati:
            try:
                oggetti_collegati_dict = {}
                for key, obj in self.oggetti_collegati.items():
                    if hasattr(obj, 'nome'):
                        oggetti_collegati_dict[key] = obj.nome
                    else:
                        oggetti_collegati_dict[key] = str(obj)
                result['oggetti_collegati'] = oggetti_collegati_dict
            except Exception as e:
                import logging
                logging.error(f"Errore nella serializzazione degli oggetti collegati di {self.nome}: {str(e)}")
                result['oggetti_collegati'] = {}
        
        return result
    
    def to_msgpack(self):
        """
        Converte l'oggetto interattivo in formato MessagePack per la serializzazione.
        MessagePack è più efficiente di JSON per la serializzazione e deserializzazione.
        
        Returns:
            bytes: Rappresentazione dell'oggetto in formato MessagePack
        """
        import msgpack
        return msgpack.packb(self.to_dict(), use_bin_type=True)
    
    @classmethod
    def from_msgpack(cls, data_bytes):
        """
        Crea un'istanza di OggettoInterattivo da dati in formato MessagePack.
        
        Args:
            data_bytes (bytes): Dati in formato MessagePack
            
        Returns:
            OggettoInterattivo: Nuova istanza di OggettoInterattivo
        """
        import msgpack
        data = msgpack.unpackb(data_bytes, raw=False)
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data):
        """
        Crea un'istanza di OggettoInterattivo da un dizionario.
        
        Args:
            data (dict): Dizionario con i dati dell'oggetto
            
        Returns:
            OggettoInterattivo: Nuova istanza di OggettoInterattivo
        """
        from items.oggetto import Oggetto
        
        # Verifica che i dati siano validi
        if not isinstance(data, dict):
            return cls("Oggetto Sconosciuto")
            
        nome = data.get("nome", "")
        descrizione = data.get("descrizione", "")
        stato = data.get("stato", "chiuso")
        posizione = data.get("posizione")
        token = data.get("token", "O")
        
        oggetto = cls(
            nome=nome,
            descrizione=descrizione,
            stato=stato,
            posizione=posizione,
            token=token
        )
        
        # Imposta il tipo
        oggetto.tipo = data.get("tipo", "oggetto_interattivo")
        
        # Impostazione del contenuto
        contenuto_raw = data.get("contenuto", [])
        contenuto = []
        
        for item in contenuto_raw:
            if isinstance(item, dict):
                try:
                    contenuto.append(Oggetto.from_dict(item))
                except Exception as e:
                    # In caso di errore, crea un oggetto generico con il nome
                    nome_item = item.get("nome", "Oggetto Sconosciuto")
                    contenuto.append(Oggetto(nome_item, "comune"))
            elif isinstance(item, str):
                # Crea un oggetto generico se solo il nome è disponibile
                contenuto.append(Oggetto(item, "comune"))
        
        oggetto.contenuto = contenuto
        
        # Caricamento delle altre proprietà
        oggetto.descrizioni_stati = data.get("descrizioni_stati", {oggetto.stato: oggetto.descrizione})
        oggetto.stati_possibili = data.get("stati_possibili", {})
        oggetto.abilita_richieste = data.get("abilita_richieste", {})
        oggetto.difficolta_abilita = data.get("difficolta_abilita", {})
        oggetto.messaggi_interazione = data.get("messaggi_interazione", {})
        
        return oggetto

    @classmethod
    def carica_da_json(cls, nome_oggetto):
        """
        Carica un oggetto interattivo dal file JSON.
        
        Args:
            nome_oggetto (str): Nome dell'oggetto da caricare.
            
        Returns:
            OggettoInterattivo: Istanza dell'oggetto interattivo caricato.
        """
        data_manager = get_data_manager()
        dati_oggetto = data_manager.get_interactive_objects(nome_oggetto)
        
        if not dati_oggetto:
            return None
            
        # Determina il tipo di classe da istanziare
        tipo_oggetto = dati_oggetto.get("tipo", "oggetto_interattivo")
        
        if tipo_oggetto == "baule":
            return Baule.from_dict(dati_oggetto)
        elif tipo_oggetto == "porta":
            return Porta.from_dict(dati_oggetto)
        elif tipo_oggetto == "leva":
            return Leva.from_dict(dati_oggetto)
        elif tipo_oggetto == "trappola":
            return Trappola.from_dict(dati_oggetto)
        elif tipo_oggetto == "oggetto_rompibile":
            return OggettoRompibile.from_dict(dati_oggetto)
        else:
            return OggettoInterattivo.from_dict(dati_oggetto)

    def salva_su_json(self):
        """
        Salva l'oggetto interattivo su file JSON.
        
        Returns:
            bool: True se il salvataggio è avvenuto con successo, False altrimenti.
        """
        try:
            data_manager = get_data_manager()
            oggetti = data_manager.get_interactive_objects()
            
            # Converti l'oggetto in dizionario
            oggetto_dict = self.to_dict()
            
            # Cerca se l'oggetto esiste già e aggiornalo
            oggetto_esistente = False
            for i, oggetto in enumerate(oggetti):
                if isinstance(oggetto, dict) and oggetto.get("nome") == self.nome:
                    oggetti[i] = oggetto_dict
                    oggetto_esistente = True
                    break
                    
            # Se l'oggetto non esiste, aggiungilo
            if not oggetto_esistente:
                oggetti.append(oggetto_dict)
                
            # Salva gli oggetti aggiornati
            return data_manager.save_interactive_objects(oggetti)
        except Exception as e:
            import logging
            logging.error(f"Errore nel salvataggio dell'oggetto {self.nome}: {e}")
            return False


class Baule(OggettoInterattivo):
    def __init__(self, nome, descrizione="", stato="chiuso", contenuto=None, richiede_chiave=False, posizione=None, token="C"):
        super().__init__(nome, descrizione, stato, contenuto, posizione, token)
        self.richiede_chiave = richiede_chiave
        self.tipo = "baule"
    
    def interagisci(self, giocatore, gioco=None):
        if self.stato == "chiuso":
            if self.richiede_chiave:
                # Verifica se il giocatore ha una chiave
                chiave_trovata = False
                for item in giocatore.inventario:
                    if isinstance(item, str):
                        nome_item = item
                    else:
                        nome_item = item.nome
                    
                    if "chiave" in nome_item.lower():
                        chiave_trovata = True
                        break
                
                if not chiave_trovata:
                    if gioco:
                        gioco.io.mostra_messaggio("Il baule è chiuso a chiave. Ti serve una chiave per aprirlo.")
                    return
                if gioco:
                    gioco.io.mostra_messaggio("Usi la chiave per aprire il baule...")
            
            if gioco:
                gioco.io.mostra_messaggio(f"Apri il {self.nome}...")
            self.stato = "aperto"
            if self.contenuto:
                if gioco:
                    gioco.io.mostra_messaggio("Dentro trovi:")
                    for oggetto in self.contenuto:
                        gioco.io.mostra_messaggio(f"- {oggetto.nome}")
                giocatore.aggiungi_item(oggetto)
                self.contenuto = []
            else:
                if gioco:
                    gioco.io.mostra_messaggio("È vuoto.")
        else:
            if gioco:
                gioco.io.mostra_messaggio(f"Il {self.nome} è già aperto.")

    def to_dict(self):
        """Estende il metodo to_dict della classe base per aggiungere attributi specifici."""
        data = super().to_dict()
        data["richiede_chiave"] = self.richiede_chiave
        return data
    
    @classmethod
    def from_dict(cls, data):
        """Crea un'istanza di Baule da un dizionario."""
        baule = super(Baule, cls).from_dict(data)
        baule.richiede_chiave = data.get("richiede_chiave", False)
        return baule


class Porta(OggettoInterattivo):
    def __init__(self, nome, descrizione="", stato="chiusa", richiede_chiave=False, posizione=None, posizione_destinazione=None, token="D"):
        super().__init__(nome, descrizione, stato, None, posizione, token)
        self.richiede_chiave = richiede_chiave
        self.posizione_destinazione = posizione_destinazione  # Dove porta questa porta
        self.tipo = "porta"
    
    def interagisci(self, giocatore, gioco=None):
        if self.stato == "chiusa":
            if self.richiede_chiave:
                # Verifica se il giocatore ha una chiave
                chiave_trovata = False
                for item in giocatore.inventario:
                    if isinstance(item, str):
                        nome_item = item
                    else:
                        nome_item = item.nome
                    
                    if "chiave" in nome_item.lower():
                        chiave_trovata = True
                        break
                
                if not chiave_trovata:
                    if gioco:
                        gioco.io.mostra_messaggio("La porta è chiusa a chiave. Ti serve una chiave per aprirla.")
                    return
                if gioco:
                    gioco.io.mostra_messaggio("Usi la chiave per aprire la porta...")
            
            if gioco:
                gioco.io.mostra_messaggio(f"Apri la {self.nome}...")
            self.stato = "aperta"
            if self.posizione_destinazione and gioco:
                gioco.io.mostra_messaggio(f"Puoi andare verso: {self.posizione_destinazione}")
        elif self.stato == "aperta":
            if gioco:
                gioco.io.mostra_messaggio(f"Chiudi la {self.nome}...")
            self.stato = "chiusa"
        else:
            if gioco:
                gioco.io.mostra_messaggio(f"La {self.nome} è {self.stato}.")

    def to_dict(self):
        """Estende il metodo to_dict della classe base per aggiungere attributi specifici."""
        data = super().to_dict()
        data["richiede_chiave"] = self.richiede_chiave
        data["posizione_destinazione"] = self.posizione_destinazione
        return data
    
    @classmethod
    def from_dict(cls, data):
        """Crea un'istanza di Porta da un dizionario."""
        porta = super(Porta, cls).from_dict(data)
        porta.richiede_chiave = data.get("richiede_chiave", False)
        porta.posizione_destinazione = data.get("posizione_destinazione")
        return porta


class Leva(OggettoInterattivo):
    def __init__(self, nome, descrizione="", stato="disattivata", posizione=None, token="L"):
        super().__init__(nome, descrizione, stato, None, posizione, token)
        self.tipo = "leva"
    
    def interagisci(self, giocatore, gioco=None):
        if self.stato == "disattivata":
            if gioco:
                gioco.io.mostra_messaggio(f"Attivi la {self.nome}...")
            self.stato = "attivata"
            
            # Attiva/disattiva oggetti collegati
            for nome, oggetto in self.oggetti_collegati.items():
                if oggetto.stato == "chiuso" or oggetto.stato == "chiusa":
                    if gioco:
                        gioco.io.mostra_messaggio(f"La {self.nome} sblocca {oggetto.nome}!")
                    oggetto.stato = "aperto" if oggetto.nome.lower() == "baule" else "aperta"
                elif oggetto.stato == "attiva":
                    if gioco:
                        gioco.io.mostra_messaggio(f"La {self.nome} disattiva {oggetto.nome}!")
                    oggetto.stato = "disattivata"
        else:
            if gioco:
                gioco.io.mostra_messaggio(f"Disattivi la {self.nome}...")
            self.stato = "disattivata"
            
            # Ripristina lo stato degli oggetti collegati
            for nome, oggetto in self.oggetti_collegati.items():
                if oggetto.stato == "aperto" or oggetto.stato == "aperta":
                    if gioco:
                        gioco.io.mostra_messaggio(f"La {self.nome} blocca {oggetto.nome}!")
                    oggetto.stato = "chiuso" if oggetto.nome.lower() == "baule" else "chiusa"
                elif oggetto.stato == "disattivata":
                    if gioco:
                        gioco.io.mostra_messaggio(f"La {self.nome} attiva {oggetto.nome}!")
                    oggetto.stato = "attiva"


class Trappola(OggettoInterattivo):
    def __init__(self, nome, descrizione="", stato="attiva", danno=10, posizione=None, difficolta_salvezza=10, token="T"):
        super().__init__(nome, descrizione, stato, None, posizione, token)
        self.danno = danno
        self.difficolta_salvezza = difficolta_salvezza
        self.tipo = "trappola"
    
    def interagisci(self, giocatore, gioco=None):
        if self.stato == "attiva":
            if gioco:
                gioco.io.mostra_messaggio(f"Hai attivato la {self.nome}!")
            dado = Dado(20)
            tiro = dado.tira()
            modificatore = giocatore.destrezza  # Supponiamo che il tiro salvezza sia basato sulla destrezza
            risultato = tiro + modificatore
            if gioco:
                gioco.io.mostra_messaggio(f"Tiro salvezza: {tiro} + {modificatore} = {risultato}")
            if risultato < self.difficolta_salvezza:
                if gioco:
                    gioco.io.mostra_messaggio(f"Subisci {self.danno} danni!")
                giocatore.subisci_danno(self.danno)
            else:
                if gioco:
                    gioco.io.mostra_messaggio("Hai evitato la trappola!")
        else:
            if gioco:
                gioco.io.mostra_messaggio(f"La {self.nome} è disattivata.")
    
    def disattiva(self, gioco=None):
        if self.stato == "attiva":
            if gioco:
                gioco.io.mostra_messaggio(f"Disattivi la {self.nome}.")
            self.stato = "disattivata"
        else:
            if gioco:
                gioco.io.mostra_messaggio(f"La {self.nome} è già disattivata.")

    def to_dict(self):
        """Estende il metodo to_dict della classe base per aggiungere attributi specifici."""
        data = super().to_dict()
        data["danno"] = self.danno
        data["difficolta_salvezza"] = self.difficolta_salvezza
        return data
    
    @classmethod
    def from_dict(cls, data):
        """Crea un'istanza di Trappola da un dizionario."""
        trappola = super(Trappola, cls).from_dict(data)
        trappola.danno = data.get("danno", 10)
        trappola.difficolta_salvezza = data.get("difficolta_salvezza", 10)
        return trappola


class OggettoRompibile(OggettoInterattivo):
    def __init__(self, nome, descrizione="", stato="integro", materiali=None, forza_richiesta=5, posizione=None, token="O"):
        super().__init__(nome, descrizione, stato, None, posizione, token)
        self.materiali = materiali or []  # Lista di oggetti che si ottengono rompendo
        self.forza_richiesta = forza_richiesta
        self.tipo = "oggetto_rompibile"
    
    def interagisci(self, giocatore, gioco=None):
        if self.stato == "integro":
            if hasattr(giocatore, 'forza') and giocatore.forza >= self.forza_richiesta:
                if gioco:
                    gioco.io.mostra_messaggio(f"Rompi {self.nome}!")
                self.stato = "rotto"
                if self.materiali:
                    if gioco:
                        gioco.io.mostra_messaggio("Ottieni:")
                        for oggetto in self.materiali:
                            gioco.io.mostra_messaggio(f"- {oggetto.nome}")
                    giocatore.aggiungi_item(oggetto)
            else:
                if gioco:
                    gioco.io.mostra_messaggio(f"Non sei abbastanza forte per rompere {self.nome}.")
        else:
            if gioco:
                gioco.io.mostra_messaggio(f"{self.nome} è già rotto.")

    def to_dict(self):
        """Estende il metodo to_dict della classe base per aggiungere attributi specifici."""
        data = super().to_dict()
        data["forza_richiesta"] = self.forza_richiesta
        data["materiali"] = [obj.to_dict() if hasattr(obj, 'to_dict') else {"nome": obj.nome} for obj in self.materiali]
        return data
    
    @classmethod
    def from_dict(cls, data):
        """Crea un'istanza di OggettoRompibile da un dizionario."""
        from items.oggetto import Oggetto
        
        oggetto = super(OggettoRompibile, cls).from_dict(data)
        oggetto.forza_richiesta = data.get("forza_richiesta", 5)
        
        # Carica i materiali
        materiali_raw = data.get("materiali", [])
        materiali = []
        
        for item in materiali_raw:
            if isinstance(item, dict):
                materiali.append(Oggetto.from_dict(item))
            elif isinstance(item, str):
                materiali.append(Oggetto(item, "comune"))
        
        oggetto.materiali = materiali
        return oggetto
