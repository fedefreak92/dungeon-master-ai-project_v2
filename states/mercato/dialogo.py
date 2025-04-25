from entities.npg import NPG
from states.dialogo import DialogoState

class DialogoMercatoHandler:
    def __init__(self, mercato_state):
        """
        Inizializza il gestore dei dialoghi per il mercato.
        
        Args:
            mercato_state: L'istanza dello stato mercato
        """
        self.mercato_state = mercato_state
        
        # Definisci i dialoghi specifici per i personaggi del mercato
        self.dialoghi = self._inizializza_dialoghi()
    
    def _inizializza_dialoghi(self):
        """
        Inizializza i dialoghi specifici per i personaggi del mercato.
        
        Returns:
            dict: Dizionario con i dialoghi per ogni personaggio
        """
        return {
            "Araldo": {
                "inizio": {
                    "testo": "Salve, viaggiatore! Sono l'Araldo del mercato. Posso informarti sugli eventi in corso o le notizie recenti.",
                    "opzioni": [
                        ("Parlami degli eventi in corso", "eventi"),
                        ("Ci sono notizie interessanti?", "notizie"),
                        ("Chi frequenta questo mercato?", "frequentatori"),
                        ("Addio", "fine")
                    ]
                },
                "eventi": {
                    "testo": "In questo periodo si festeggia la Festa del Raccolto! Ci saranno competizioni di forza, spettacoli di magia e un grande banchetto. Tutto il mercato è in fermento per i preparativi.",
                    "opzioni": [
                        ("Posso partecipare alle competizioni?", "competizioni"),
                        ("Parlami degli spettacoli di magia", "magia"),
                        ("Torna indietro", "inizio")
                    ]
                },
                "competizioni": {
                    "testo": "Certamente! Le iscrizioni sono aperte. C'è la gara di lancio del tronco, il tiro alla fune e la corsa con i sacchi. Il vincitore riceverà un premio speciale dal Signore del villaggio!",
                    "opzioni": [
                        ("Quanto costa l'iscrizione?", "costo_iscrizione"),
                        ("Torna indietro", "eventi")
                    ]
                },
                "costo_iscrizione": {
                    "testo": "L'iscrizione costa 5 monete d'oro. Una piccola somma per la possibilità di vincere gloria e un premio di 100 monete d'oro!",
                    "opzioni": [
                        ("Mi iscrivo (5 oro)", "iscrizione_completata"),
                        ("Ci penserò", "eventi")
                    ],
                    "azione": lambda gioco: self._gestisci_iscrizione(gioco, 5)
                },
                "iscrizione_completata": {
                    "testo": "Eccellente! Ti ho iscritto alla competizione. Presentati domani all'alba al campo grande dietro il mercato.",
                    "opzioni": [
                        ("Grazie!", "inizio")
                    ]
                },
                "magia": {
                    "testo": "Gli spettacoli di magia saranno tenuti dal famoso mago Zoltarn. Dice di poter evocare creature da altri piani e trasformare l'acqua in vino. Io non ci credo molto, ma la gente paga bene per vedere questi 'miracoli'.",
                    "opzioni": [
                        ("Interessante", "eventi"),
                        ("Torna all'inizio", "inizio")
                    ]
                },
                "notizie": {
                    "testo": "Si dice che una banda di briganti si aggiri nei boschi a nord. La guardia cittadina ha aumentato le pattuglie. Inoltre, pare che il vecchio negromante delle colline sia tornato ad aggirarsi nelle vicinanze.",
                    "opzioni": [
                        ("Dimmi di più sui briganti", "briganti"),
                        ("Chi è questo negromante?", "negromante"),
                        ("Torna indietro", "inizio")
                    ]
                },
                "briganti": {
                    "testo": "I briganti sono guidati da un ex soldato chiamato Mordrec. Si dice che attacchino soprattutto i mercanti. C'è una taglia di 200 monete d'oro sulla testa del loro capo.",
                    "opzioni": [
                        ("Una taglia interessante...", "notizie"),
                        ("Torna indietro", "inizio")
                    ]
                },
                "negromante": {
                    "testo": "Il Vecchio Krieger, lo chiamano. Vive in una torre nelle colline orientali. Alcuni lo considerano un pazzo, altri un pericoloso praticante di arti oscure. I contadini sostengono di vedere luci strane provenire dalla sua torre di notte.",
                    "opzioni": [
                        ("Capisco", "notizie"),
                        ("Torna indietro", "inizio")
                    ]
                },
                "frequentatori": {
                    "testo": "Qui al mercato puoi trovare persone di ogni tipo! C'è Violetta la mercante di stoffe, Gundren il fabbro, e poi ci sono i viaggiatori e i mercanti itineranti. Tutti hanno storie interessanti da raccontare!",
                    "opzioni": [
                        ("Parlami di Violetta", "violetta"),
                        ("Chi è Gundren?", "gundren"),
                        ("Torna indietro", "inizio")
                    ]
                },
                "violetta": {
                    "testo": "Violetta viene dalle terre del sud. Ha le stoffe più belle e colorate che abbia mai visto! Dice di tingere i tessuti con colori ricavati da piante e minerali rari.",
                    "opzioni": [
                        ("Interessante", "frequentatori"),
                        ("Torna indietro", "inizio")
                    ]
                },
                "gundren": {
                    "testo": "Gundren è un fabbro nano, il migliore della regione. Le sue armi sono di qualità superiore. Si dice che abbia studiato nelle fucine di Khaz'Modhan, la leggendaria città dei nani.",
                    "opzioni": [
                        ("Capisco", "frequentatori"),
                        ("Torna indietro", "inizio")
                    ]
                },
                "fine": {
                    "testo": "Buona permanenza al mercato, viaggiatore! Se hai bisogno di altre informazioni, sai dove trovarmi.",
                    "opzioni": [
                        ("Arrivederci", "exit")
                    ]
                }
            },
            "Violetta": {
                "inizio": {
                    "testo": "Benvenuto alla mia bancarella, caro. Sono Violetta, e vendo le stoffe più pregiate di tutto il regno. Provengono da terre lontane, oltre il Grande Mare.",
                    "opzioni": [
                        ("Cosa hai in vendita?", "vendita"),
                        ("Da dove vieni?", "origine"),
                        ("Ho sentito che tingi i tessuti con metodi speciali", "tintura"),
                        ("Addio", "fine")
                    ]
                },
                "vendita": {
                    "testo": "Ho seta delle Isole del Sud, lino di Estraval, lana dei pastori di Alton e persino il raro cotone lunare che cresce solo sotto la luce argentea della luna piena.",
                    "opzioni": [
                        ("Quanto costa la seta?", "prezzo_seta"),
                        ("Mi interessa il cotone lunare", "prezzo_cotone"),
                        ("Torna indietro", "inizio")
                    ]
                },
                "prezzo_seta": {
                    "testo": "La seta costa 15 monete d'oro per un rotolo. È resistente, morbida e perfetta per abiti eleganti. Ti piacerebbe acquistarne un po'?",
                    "opzioni": [
                        ("Acquista un rotolo (15 oro)", "acquisto_seta"),
                        ("È troppo costosa", "vendita")
                    ],
                    "azione": lambda gioco: self._gestisci_acquisto(gioco, "Rotolo di seta", 15)
                },
                "acquisto_seta": {
                    "testo": "Eccellente scelta! Questo è uno dei miei migliori rotoli di seta. Ti servirà bene, sia che tu voglia farne un abito o rivenderlo.",
                    "opzioni": [
                        ("Grazie", "vendita"),
                        ("Torna indietro", "inizio")
                    ]
                },
                "prezzo_cotone": {
                    "testo": "Il cotone lunare è molto raro. Costa 30 monete d'oro per un piccolo rotolo. Si dice che chi indossa abiti fatti con questo materiale sia benedetto dalla dea della luna.",
                    "opzioni": [
                        ("Acquista un rotolo (30 oro)", "acquisto_cotone"),
                        ("È troppo costoso", "vendita")
                    ],
                    "azione": lambda gioco: self._gestisci_acquisto(gioco, "Cotone lunare", 30)
                },
                "acquisto_cotone": {
                    "testo": "Una scelta eccellente! Questo cotone è stato raccolto durante l'ultima luna piena. Porta con sé la benedizione di Lunaris.",
                    "opzioni": [
                        ("Grazie", "vendita"),
                        ("Torna indietro", "inizio")
                    ]
                },
                "origine": {
                    "testo": "Vengo da Meridia, la città dei mille colori, oltre il Grande Mare. Lì, la mia famiglia ha lavorato con le stoffe per generazioni. Ho imparato l'arte della tintura da mia nonna, una vera maestra.",
                    "opzioni": [
                        ("Com'è Meridia?", "meridia"),
                        ("Torna indietro", "inizio")
                    ]
                },
                "meridia": {
                    "testo": "Meridia è una città colorata e vibrante! Le case sono dipinte in colori vivaci, i mercati sono pieni di tessuti sgargianti, e ci sono festival di colori in ogni stagione. Il più grande è la Festa dei Mille Colori, quando tutti indossano le loro vesti più colorate.",
                    "opzioni": [
                        ("Sembra bellissimo", "origine"),
                        ("Torna indietro", "inizio")
                    ]
                },
                "tintura": {
                    "testo": "Ah, sì! La tintura è un'arte che richiede anni di apprendimento. Uso piante, minerali e persino alcuni segreti tramandati nella mia famiglia. Ogni colore ha un significato e un potere diverso.",
                    "opzioni": [
                        ("Quali sono i colori più potenti?", "colori_potenti"),
                        ("Mi insegneresti a tingere?", "insegnamento"),
                        ("Torna indietro", "inizio")
                    ]
                },
                "colori_potenti": {
                    "testo": "Il blu profondo ottenuto dal fiore di Serathal protegge dai malefici. Il rosso della radice di Koros infonde coraggio. Il verde smeraldo ottenuto dal muschio delle montagne potenzia la percezione. Ma il più potente è il viola imperiale, che si dice aumenti la fortuna di chi lo indossa.",
                    "opzioni": [
                        ("Hai qualche abito di questi colori?", "abiti_speciali"),
                        ("Affascinante", "tintura"),
                        ("Torna indietro", "inizio")
                    ]
                },
                "abiti_speciali": {
                    "testo": "In effetti, ho una sciarpa tinta con il viola imperiale. Costa 25 monete d'oro. Chi la indossa, si dice, abbia maggiore fortuna nei suoi viaggi.",
                    "opzioni": [
                        ("Acquista la sciarpa (25 oro)", "acquisto_sciarpa"),
                        ("Troppo costosa", "tintura")
                    ],
                    "azione": lambda gioco: self._gestisci_acquisto(gioco, "Sciarpa viola imperiale", 25, {"fortuna": 1})
                },
                "acquisto_sciarpa": {
                    "testo": "Ottima scelta! Questa sciarpa è stata tinta durante l'ultimo plenilunio. Che la fortuna ti accompagni nei tuoi viaggi!",
                    "opzioni": [
                        ("Grazie", "inizio")
                    ]
                },
                "insegnamento": {
                    "testo": "Insegnare l'arte della tintura? Mmm... Potrei, ma i miei segreti di famiglia hanno un prezzo. Per 50 monete d'oro, potrei insegnarti alcune tecniche base.",
                    "opzioni": [
                        ("Accetto (50 oro)", "lezione_tintura"),
                        ("È troppo costoso", "tintura")
                    ],
                    "azione": lambda gioco: self._gestisci_lezione_tintura(gioco, 50)
                },
                "lezione_tintura": {
                    "testo": "Eccellente! La prima lezione: le piante blu vanno sempre macerate alla luce della luna, mai del sole, o il colore sbiadirà rapidamente. Per ottenere il miglior giallo, mescola il polline di girasole con un pizzico di zafferano...",
                    "opzioni": [
                        ("Grazie per la lezione", "inizio")
                    ]
                },
                "fine": {
                    "testo": "Arrivederci, caro cliente! Spero di rivederti presto alla mia bancarella. Che i colori del tuo cammino siano sempre vivaci!",
                    "opzioni": [
                        ("Arrivederci", "exit")
                    ]
                }
            },
            "Gundren": {
                "inizio": {
                    "testo": "Salve, straniero! Sono Gundren Forgiadura, il miglior fabbro di queste terre. Hai bisogno di armi, armature o attrezzi? Sei nel posto giusto!",
                    "opzioni": [
                        ("Mostrami le tue armi", "armi"),
                        ("Hai delle armature?", "armature"),
                        ("Raccontami della tua esperienza", "storia"),
                        ("Addio", "fine")
                    ]
                },
                "armi": {
                    "testo": "Ho spade, asce, martelli e persino alcune armi esotiche. Tutto forgiato da me, con le migliori tecniche naniche. La qualità è garantita!",
                    "opzioni": [
                        ("Vorrei una spada", "spada"),
                        ("Mi interessa un'ascia", "ascia"),
                        ("Hai armi magiche?", "armi_magiche"),
                        ("Torna indietro", "inizio")
                    ]
                },
                "spada": {
                    "testo": "Ho diverse spade: una spada corta da 25 monete d'oro, una spada lunga da 40 monete, e una spada a due mani da 60 monete. Qual è di tuo interesse?",
                    "opzioni": [
                        ("Spada corta (25 oro)", "acquisto_spada_corta"),
                        ("Spada lunga (40 oro)", "acquisto_spada_lunga"),
                        ("Spada a due mani (60 oro)", "acquisto_spada_due_mani"),
                        ("Nessuna di queste", "armi")
                    ]
                },
                "acquisto_spada_corta": {
                    "testo": "Eccellente scelta! Questa spada corta è perfetta per combattimenti ravvicinati o come arma secondaria. L'acciaio è stato temperato tre volte per garantire resistenza.",
                    "opzioni": [
                        ("Grazie", "armi"),
                        ("Torna indietro", "inizio")
                    ],
                    "azione": lambda gioco: self._gestisci_acquisto(gioco, "Spada corta", 25, {"danno": 4})
                },
                "acquisto_spada_lunga": {
                    "testo": "Una spada lunga, ottima scelta! Equilibrata, affilata e con un'ottima impugnatura. Questa è un'arma che ti servirà fedelmente in battaglia.",
                    "opzioni": [
                        ("Grazie", "armi"),
                        ("Torna indietro", "inizio")
                    ],
                    "azione": lambda gioco: self._gestisci_acquisto(gioco, "Spada lunga", 40, {"danno": 6})
                },
                "acquisto_spada_due_mani": {
                    "testo": "Ah, un'arma formidabile! Questa spada a due mani richiede forza, ma in cambio offre una potenza devastante. L'ho forgiata personalmente nella fucina più calda.",
                    "opzioni": [
                        ("Grazie", "armi"),
                        ("Torna indietro", "inizio")
                    ],
                    "azione": lambda gioco: self._gestisci_acquisto(gioco, "Spada a due mani", 60, {"danno": 10})
                },
                "ascia": {
                    "testo": "Le mie asce sono tra le migliori! Ho un'ascia da battaglia a 35 monete d'oro, e una grande ascia da guerra a 55 monete. Entrambe sono bilanciate perfettamente.",
                    "opzioni": [
                        ("Ascia da battaglia (35 oro)", "acquisto_ascia_battaglia"),
                        ("Grande ascia (55 oro)", "acquisto_grande_ascia"),
                        ("Nessuna di queste", "armi")
                    ]
                },
                "acquisto_ascia_battaglia": {
                    "testo": "Una solida scelta! Questa ascia da battaglia è versatile e letale. La lama è stata affilata con tecniche naniche segrete.",
                    "opzioni": [
                        ("Grazie", "armi"),
                        ("Torna indietro", "inizio")
                    ],
                    "azione": lambda gioco: self._gestisci_acquisto(gioco, "Ascia da battaglia", 35, {"danno": 5})
                },
                "acquisto_grande_ascia": {
                    "testo": "Questa grande ascia è un capolavoro di forgiatura! Con essa potrai abbattere anche i nemici più coriacei. Attento però, richiede notevole forza per essere maneggiata efficacemente.",
                    "opzioni": [
                        ("Grazie", "armi"),
                        ("Torna indietro", "inizio")
                    ],
                    "azione": lambda gioco: self._gestisci_acquisto(gioco, "Grande ascia", 55, {"danno": 9})
                },
                "armi_magiche": {
                    "testo": "Armi magiche? Hmm, quelle sono rare. Al momento ho solo un pugnale runato, forgiato con acciaio meteorico e inciso con rune antiche. Costa 100 monete d'oro.",
                    "opzioni": [
                        ("Compralo (100 oro)", "acquisto_pugnale_runato"),
                        ("È troppo costoso", "armi")
                    ]
                },
                "acquisto_pugnale_runato": {
                    "testo": "Un acquisto eccellente! Questo pugnale è stato forgiato durante un allineamento stellare raro. Le rune incise sulla lama si illuminano leggermente quando si avvicinano alla magia. Un'arma davvero speciale.",
                    "opzioni": [
                        ("Grazie", "armi"),
                        ("Torna indietro", "inizio")
                    ],
                    "azione": lambda gioco: self._gestisci_acquisto(gioco, "Pugnale runato", 100, {"danno": 3, "magico": True})
                },
                "armature": {
                    "testo": "Ho diverse armature: armatura di cuoio a 30 monete d'oro, armatura di maglia a 60 monete, e una corazza di piastre a 120 monete. Tutte forgiate con materiali di prima qualità.",
                    "opzioni": [
                        ("Armatura di cuoio (30 oro)", "acquisto_armatura_cuoio"),
                        ("Armatura di maglia (60 oro)", "acquisto_armatura_maglia"),
                        ("Corazza di piastre (120 oro)", "acquisto_corazza_piastre"),
                        ("Torna indietro", "inizio")
                    ]
                },
                "acquisto_armatura_cuoio": {
                    "testo": "L'armatura di cuoio è leggera e flessibile, perfetta per chi preferisce la mobilità. Ti proteggerà dai colpi, senza limitare i tuoi movimenti.",
                    "opzioni": [
                        ("Grazie", "armature"),
                        ("Torna indietro", "inizio")
                    ],
                    "azione": lambda gioco: self._gestisci_acquisto(gioco, "Armatura di cuoio", 30, {"difesa": 2})
                },
                "acquisto_armatura_maglia": {
                    "testo": "L'armatura di maglia offre un buon compromesso tra protezione e mobilità. Ogni anello è stato forgiato e intrecciato a mano da me.",
                    "opzioni": [
                        ("Grazie", "armature"),
                        ("Torna indietro", "inizio")
                    ],
                    "azione": lambda gioco: self._gestisci_acquisto(gioco, "Armatura di maglia", 60, {"difesa": 4})
                },
                "acquisto_corazza_piastre": {
                    "testo": "La corazza di piastre è l'armatura più protettiva che ho. Pesa un po', ma ti farà sentire invincibile in battaglia. È stata forgiata con le migliori tecniche naniche.",
                    "opzioni": [
                        ("Grazie", "armature"),
                        ("Torna indietro", "inizio")
                    ],
                    "azione": lambda gioco: self._gestisci_acquisto(gioco, "Corazza di piastre", 120, {"difesa": 8})
                },
                "storia": {
                    "testo": "Ho imparato l'arte della forgiatura nelle fucine di Khaz'Modhan, la più grande città nanica. Ho studiato sotto il grande maestro Thorgrim Barbafiamma per venti anni prima di mettermi in proprio.",
                    "opzioni": [
                        ("Com'è Khaz'Modhan?", "khaz_modhan"),
                        ("Chi è Thorgrim Barbafiamma?", "thorgrim"),
                        ("Torna indietro", "inizio")
                    ]
                },
                "khaz_modhan": {
                    "testo": "Khaz'Modhan è una meraviglia! Una città intera scavata nella montagna, con enormi sale, pilastri decorati e, naturalmente, le più grandi fucine del mondo. I fuochi delle forge non si spengono mai, e il suono dei martelli risuona giorno e notte.",
                    "opzioni": [
                        ("Affascinante", "storia"),
                        ("Torna indietro", "inizio")
                    ]
                },
                "thorgrim": {
                    "testo": "Thorgrim Barbafiamma è il più grande maestro fabbro di Khaz'Modhan. Si dice che abbia forgiato la leggendaria ascia del Re Nanico Durin IV. È un maestro severo ma giusto. Mi ha insegnato tutti i segreti della metallurgia nanica.",
                    "opzioni": [
                        ("Interessante", "storia"),
                        ("Torna indietro", "inizio")
                    ]
                },
                "fine": {
                    "testo": "Che le tue armi rimangano sempre affilate e le tue armature mai si pieghino, amico! Torna quando vuoi, la fucina di Gundren è sempre aperta!",
                    "opzioni": [
                        ("Arrivederci", "exit")
                    ]
                }
            }
        }
    
    def inizia_dialogo(self, gioco, nome_npg):
        """
        Inizia un dialogo con un NPC.
        
        Args:
            gioco: Il contesto di gioco
            nome_npg: Il nome dell'NPC con cui parlare
            
        Returns:
            bool: True se il dialogo è stato avviato, False altrimenti
        """
        # Verifica se l'NPC è presente nel mercato
        if nome_npg not in self.mercato_state.npg_presenti:
            gioco.io.mostra_messaggio(f"Non trovi {nome_npg} nei paraggi.")
            return False
            
        # Ottieni l'NPC
        npg = self.mercato_state.npg_presenti[nome_npg]
        
        # Salva il nome dell'NPC attivo
        self.mercato_state.nome_npg_attivo = nome_npg
        
        # Imposta i dialoghi specifici per questo NPC
        if nome_npg in self.dialoghi:
            npg.dialoghi = self.dialoghi[nome_npg]
        
        # Avvia lo stato di dialogo
        dialogo_state = DialogoState(gioco, npg)
        gioco.push_stato(dialogo_state)
        
        return True
    
    def _gestisci_acquisto(self, gioco, nome_oggetto, prezzo, bonus=None):
        """
        Gestisce l'acquisto di un oggetto.
        
        Args:
            gioco: Il contesto di gioco
            nome_oggetto: Il nome dell'oggetto da acquistare
            prezzo: Il prezzo dell'oggetto
            bonus: Eventuali bonus associati all'oggetto
            
        Returns:
            bool: True se l'acquisto è andato a buon fine, False altrimenti
        """
        # Verifica se il giocatore ha abbastanza oro
        if gioco.giocatore.oro < prezzo:
            gioco.io.mostra_messaggio(f"Non hai abbastanza oro! Ti mancano {prezzo - gioco.giocatore.oro} monete.")
            return False
        
        # Rimuovi l'oro dal giocatore
        gioco.giocatore.rimuovi_oro(prezzo)
        
        # Crea l'oggetto
        from items.oggetto import Oggetto
        tipo = "arma" if "danno" in (bonus or {}) else "armatura" if "difesa" in (bonus or {}) else "accessorio"
        oggetto = Oggetto(nome_oggetto, tipo, bonus or {}, prezzo)
        
        # Aggiungi l'oggetto all'inventario
        gioco.giocatore.aggiungi_item(oggetto)
        
        gioco.io.mostra_messaggio(f"Hai acquistato {nome_oggetto} per {prezzo} oro!")
        return True
    
    def _gestisci_iscrizione(self, gioco, costo):
        """
        Gestisce l'iscrizione a un evento.
        
        Args:
            gioco: Il contesto di gioco
            costo: Il costo dell'iscrizione
            
        Returns:
            bool: True se l'iscrizione è andata a buon fine, False altrimenti
        """
        # Verifica se il giocatore ha abbastanza oro
        if gioco.giocatore.oro < costo:
            gioco.io.mostra_messaggio(f"Non hai abbastanza oro! Ti mancano {costo - gioco.giocatore.oro} monete.")
            return False
        
        # Rimuovi l'oro dal giocatore
        gioco.giocatore.rimuovi_oro(costo)
        
        # Aggiungi l'iscrizione allo stato del giocatore
        if not hasattr(gioco.giocatore, 'iscrizioni'):
            gioco.giocatore.iscrizioni = []
        
        gioco.giocatore.iscrizioni.append("Competizione Festa del Raccolto")
        
        gioco.io.mostra_messaggio(f"Sei stato iscritto alla competizione per {costo} oro!")
        return True
    
    def _gestisci_lezione_tintura(self, gioco, costo):
        """
        Gestisce una lezione di tintura.
        
        Args:
            gioco: Il contesto di gioco
            costo: Il costo della lezione
            
        Returns:
            bool: True se la lezione è stata acquistata, False altrimenti
        """
        # Verifica se il giocatore ha abbastanza oro
        if gioco.giocatore.oro < costo:
            gioco.io.mostra_messaggio(f"Non hai abbastanza oro! Ti mancano {costo - gioco.giocatore.oro} monete.")
            return False
        
        # Rimuovi l'oro dal giocatore
        gioco.giocatore.rimuovi_oro(costo)
        
        # Aggiungi l'abilità di tintura al giocatore
        if not hasattr(gioco.giocatore, 'abilita'):
            gioco.giocatore.abilita = {}
        
        gioco.giocatore.abilita["tintura"] = gioco.giocatore.abilita.get("tintura", 0) + 1
        
        gioco.io.mostra_messaggio(f"Hai imparato i principi base della tintura per {costo} oro!")
        return True
    
    def handle_dialog_choice(self, event):
        """
        Gestisce le scelte di dialogo.
        
        Args:
            event: L'evento di scelta di dialogo
            
        Returns:
            bool: True se l'evento è stato gestito, False altrimenti
        """
        # Questo metodo viene chiamato quando il giocatore fa una scelta di dialogo
        # Può essere sovrascritto per gestire logiche specifiche del mercato
        
        # Se non abbiamo un NPG attivo, non possiamo gestire l'evento
        if not self.mercato_state.nome_npg_attivo:
            return False
            
        # Se l'evento non è una scelta di dialogo, non possiamo gestirlo
        if not event.get("choice"):
            return False
            
        # Qui potremmo aggiungere logiche specifiche per il mercato
        # Ad esempio, aggiornare lo stato del giocatore o del mercato
        
        return False 