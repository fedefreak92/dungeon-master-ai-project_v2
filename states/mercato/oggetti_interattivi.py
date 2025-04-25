from items.oggetto_interattivo import Baule, Leva, Porta, OggettoInterattivo, Trappola, OggettoRompibile
from items.oggetto import Oggetto
from world.mappa import Mappa

def crea_oggetti_base():
    """Crea gli oggetti interattivi di base del mercato."""
    oggetti_interattivi = {
        "bancarella": OggettoInterattivo("Bancarella", "Una bancarella di oggetti usati.", "aperta", posizione="mercato"),
        "baule_mercante": Baule("Baule del mercante", "Un baule di ferro con serratura robusta.", 
                               contenuto=[Oggetto("Amuleto", "accessorio", {"fortuna": 1}, 10)],
                               richiede_chiave=True, posizione="mercato"),
        "porta_magazzino": Porta("Porta del magazzino", "Una porta che conduce al magazzino del mercato.", 
                                stato="chiusa", richiede_chiave=True, posizione="mercato", 
                                posizione_destinazione="magazzino"),
        "leva_segreta": Leva("Leva nascosta", "Una leva nascosta sotto il bancone.", posizione="mercato")
    }
    
    # Colleghiamo la leva alla porta del magazzino
    oggetti_interattivi["leva_segreta"].collega_oggetto("porta", oggetti_interattivi["porta_magazzino"])
    
    return oggetti_interattivi

def crea_statua_antica():
    """Crea la statua antica del mercato."""
    statua_antica = OggettoInterattivo("Statua Antica", "Una statua di pietra raffigurante un mercante. Sembra molto vecchia.", stato="normale", posizione="mercato")
    
    # Configura descrizioni per vari stati
    statua_antica.imposta_descrizione_stato("normale", "Una statua di pietra raffigurante un mercante. Sembra molto vecchia.")
    statua_antica.imposta_descrizione_stato("esaminata", "Guardando attentamente, noti simboli strani incisi sulla base della statua.")
    statua_antica.imposta_descrizione_stato("decifrata", "I simboli sulla statua sembrano indicare la posizione di un tesoro nascosto.")
    statua_antica.imposta_descrizione_stato("ruotata", "La statua è stata ruotata. Si sente un click provenire dal pavimento.")
    
    # Definisci le transizioni possibili
    statua_antica.aggiungi_transizione("normale", "esaminata")
    statua_antica.aggiungi_transizione("esaminata", "decifrata")
    statua_antica.aggiungi_transizione("decifrata", "ruotata")
    statua_antica.aggiungi_transizione("ruotata", "normale")
    
    # Collega abilità alle transizioni
    statua_antica.richiedi_abilita("percezione", "esaminata", 12, 
                                  "Osservi attentamente la statua e noti dei piccoli simboli incisi sulla base.")
    statua_antica.richiedi_abilita("storia", "decifrata", 15, 
                                  "Grazie alla tua conoscenza storica, comprendi che i simboli raccontano di un tesoro nascosto.")
    statua_antica.richiedi_abilita("forza", "ruotata", 14, 
                                  "Con uno sforzo notevole, riesci a ruotare la pesante statua rivelando una piccola fessura nel pavimento.")
    
    # Collega un evento di gioco allo stato "ruotata"
    statua_antica.collega_evento("ruotata", lambda gioco: gioco.sblocca_area("cripta_mercante"))
    
    return statua_antica

def crea_scaffale_merce():
    """Crea lo scaffale con merce speciale."""
    scaffale_merce = OggettoInterattivo("Scaffale di Merce", "Uno scaffale pieno di merci esotiche.", stato="intatto", posizione="mercato")
    
    # Configura descrizioni per vari stati
    scaffale_merce.imposta_descrizione_stato("intatto", "Uno scaffale pieno di merci esotiche dai vari paesi.")
    scaffale_merce.imposta_descrizione_stato("ispezionato", "Tra le varie merci, noti un piccolo cofanetto nascosto dietro alcune stoffe.")
    scaffale_merce.imposta_descrizione_stato("spostato", "Hai spostato alcuni oggetti rivelando un cofanetto decorato.")
    scaffale_merce.imposta_descrizione_stato("aperto", "Il cofanetto è aperto, rivelando una mappa di un luogo sconosciuto.")
    
    # Definisci le transizioni possibili
    scaffale_merce.aggiungi_transizione("intatto", "ispezionato")
    scaffale_merce.aggiungi_transizione("ispezionato", "spostato")
    scaffale_merce.aggiungi_transizione("spostato", "aperto")
    
    # Collega abilità alle transizioni
    scaffale_merce.richiedi_abilita("percezione", "ispezionato", 10, 
                                    "Guardando tra le merci esposte, noti qualcosa di insolito...")
    scaffale_merce.richiedi_abilita("indagare", "spostato", 12, 
                                    "Sposti con attenzione alcuni oggetti, rivelando un piccolo cofanetto decorato.")
    scaffale_merce.richiedi_abilita("destrezza", "aperto", 13, 
                                    "Con le tue dita agili riesci ad aprire il meccanismo di chiusura del cofanetto.")
    
    # Definisci un evento quando il cofanetto viene aperto
    def ricompensa_mappa(gioco):
        mappa = Oggetto("Mappa del tesoro", "mappa", {}, 50, "Una mappa che mostra la posizione di un tesoro nascosto.")
        gioco.giocatore.aggiungi_item(mappa)
        gioco.io.mostra_messaggio("Hai ottenuto una Mappa del tesoro!")
    
    scaffale_merce.collega_evento("aperto", ricompensa_mappa)
    
    return scaffale_merce

def crea_fontana_magica():
    """Crea la fontana magica."""
    fontana = OggettoInterattivo("Fontana Magica", "Una piccola fontana decorativa al centro del mercato.", stato="inattiva", posizione="mercato")
    
    # Configura descrizioni per vari stati
    fontana.imposta_descrizione_stato("inattiva", "Una piccola fontana decorativa che sembra non funzionare da tempo.")
    fontana.imposta_descrizione_stato("esaminata", "Noti dei simboli arcani incisi sul bordo della fontana.")
    fontana.imposta_descrizione_stato("attivata", "La fontana si illumina e l'acqua inizia a fluire, emanando un bagliore azzurro.")
    fontana.imposta_descrizione_stato("purificata", "L'acqua della fontana emana un bagliore dorato e sembra avere proprietà curative.")
    
    # Definisci le transizioni possibili
    fontana.aggiungi_transizione("inattiva", "esaminata")
    fontana.aggiungi_transizione("esaminata", "attivata")
    fontana.aggiungi_transizione("attivata", "purificata")
    fontana.aggiungi_transizione("purificata", "inattiva")
    
    # Collega abilità alle transizioni
    fontana.richiedi_abilita("arcano", "esaminata", 13, 
                            "Studiando la fontana, riconosci antichi simboli arcani di acqua ed energia.")
    fontana.richiedi_abilita("intelligenza", "attivata", 14, 
                            "Ricordando un antico incantesimo, pronunci le parole che attivano la fontana.")
    fontana.richiedi_abilita("religione", "purificata", 15, 
                            "Con una preghiera di purificazione, l'acqua della fontana cambia colore diventando dorata.")
    
    # Definisci eventi per i vari stati
    def bevi_acqua_guaritrice(gioco):
        gioco.io.mostra_messaggio("Bevi l'acqua dalla fontana e ti senti rivitalizzato!")
        gioco.giocatore.cura(10)
    
    fontana.collega_evento("purificata", bevi_acqua_guaritrice)
    
    return fontana

def crea_tutti_oggetti_interattivi():
    """Crea tutti gli oggetti interattivi del mercato e li restituisce come dizionario."""
    oggetti = crea_oggetti_base()
    oggetti["statua_antica"] = crea_statua_antica()
    oggetti["scaffale_merce"] = crea_scaffale_merce()
    oggetti["fontana_magica"] = crea_fontana_magica()
    
    return oggetti 