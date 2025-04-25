from items.oggetto_interattivo import OggettoInterattivo, Baule, Porta, Leva, Trappola
from items.oggetto import Oggetto

def inizializza_oggetti_taverna():
    """Inizializza gli oggetti interattivi della taverna"""
    oggetti = {
        "bancone": OggettoInterattivo("Bancone", "Un lungo bancone di legno lucido dove vengono servite le bevande.", "pulito", posizione="taverna"),
        "camino": OggettoInterattivo("Camino", "Un grande camino in pietra con un fuoco scoppiettante.", "acceso", posizione="taverna"),
        "baule_nascondiglio": Baule("Baule nascosto", "Un piccolo baule nascosto sotto una tavola del pavimento.", 
                                 contenuto=[Oggetto("Chiave rugginosa", "chiave", {}, 2, "Una vecchia chiave arrugginita.")], 
                                 posizione="taverna"),
        "porta_cantina": Porta("Porta della cantina", "Una robusta porta che conduce alla cantina.", 
                              stato="chiusa", richiede_chiave=True, posizione="taverna", 
                              posizione_destinazione="cantina"),
        "trappola_pavimento": Trappola("Trappola nel pavimento", "Una parte del pavimento sembra instabile.", 
                                     danno=5, posizione="taverna", difficolta_salvezza=10)
    }
    
    # Colleghiamo alcuni oggetti tra loro per creare interazioni
    leva_segreta = Leva("Leva segreta", "Una leva nascosta dietro un quadro.", posizione="taverna")
    oggetti["leva_segreta"] = leva_segreta
    leva_segreta.collega_oggetto("trappola", oggetti["trappola_pavimento"])

    # Esempio di altare magico
    altare = OggettoInterattivo("Altare magico", "Un antico altare con simboli misteriosi.", stato="inattivo")
    altare.imposta_descrizione_stato("inattivo", "Un antico altare con simboli misteriosi che sembrano spenti.")
    altare.imposta_descrizione_stato("attivo", "L'altare emette una luce blu intensa e i simboli brillano.")
    altare.imposta_descrizione_stato("esaminato", "Noti che l'altare ha delle rune che formano un incantesimo antico.")

    # Aggiungi transizioni possibili
    altare.aggiungi_transizione("inattivo", "esaminato")
    altare.aggiungi_transizione("inattivo", "attivo")
    altare.aggiungi_transizione("esaminato", "attivo")
    altare.aggiungi_transizione("attivo", "inattivo")

    # Collega abilità 
    altare.richiedi_abilita("percezione", "esaminato", 12, 
                        "Scrutando attentamente l'altare, noti delle incisioni nascoste.")
    altare.richiedi_abilita("arcano", "attivo", 15, 
                        "Utilizzando la tua conoscenza arcana, attivi l'antico potere dell'altare.")

    # Collega eventi al mondo
    altare.collega_evento("attivo", lambda gioco: gioco.sblocca_area("cripta_magica"))

    # Aggiungi l'oggetto alla taverna
    oggetti["altare_magico"] = altare
    
    return oggetti

def gestisci_esplorazione_oggetti(stato, gioco):
    """Esplora gli oggetti presenti nella taverna usando l'interfaccia grafica"""
    # Proviamo a usare gli oggetti sulla mappa
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
    for nome, oggetto in stato.oggetti_interattivi.items():
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
        gioco.io.mostra_notifica({
            "text": "Non ci sono oggetti con cui interagire nelle vicinanze.",
            "type": "info",
            "duration": 2.0
        })
        stato.menu_handler.mostra_menu_principale(gioco)
        return
        
    # Prepara le opzioni per il dialogo
    opzioni = [f"{obj['nome']} [{obj['stato']}]" for obj in oggetti_lista]
    opzioni.append("Torna indietro")
    
    # Memorizza la lista degli oggetti per gestire la scelta
    stato.dati_contestuali["oggetti_lista"] = oggetti_lista
    
    # Mostra il dialogo con gli oggetti disponibili
    gioco.io.mostra_dialogo("Esplora Oggetti", "Scegli un oggetto con cui interagire:", opzioni)
    
    # Imposta il menu attivo
    stato.menu_attivo = "selezione_oggetti"
    
    # Aggiorna l'handler per gestire la scelta dell'oggetto
    stato._handle_dialog_choice = lambda event: handle_object_choice(event, stato)
    
def handle_object_choice(event, stato):
    """Gestisce la scelta dell'oggetto con cui interagire"""
    gioco = stato.gioco
    choice = event.get("choice", "")
    oggetti_lista = stato.dati_contestuali.get("oggetti_lista", [])
    
    # Se l'utente ha scelto di tornare indietro
    if choice == "Torna indietro":
        # Effetto audio
        gioco.io.play_sound({
            "sound_id": "menu_close",
            "volume": 0.5
        })
        stato.menu_handler.mostra_menu_principale(gioco)
        return
        
    # Trova l'oggetto selezionato
    oggetto_selezionato = None
    for i, oggetto_info in enumerate(oggetti_lista):
        if f"{oggetto_info['nome']} [{oggetto_info['stato']}]" == choice:
            oggetto_selezionato = oggetto_info
            break
    
    if oggetto_selezionato:
        # Effetto audio
        gioco.io.play_sound({
            "sound_id": "item_interact",
            "volume": 0.6
        })
        
        # Ottieni l'oggetto
        oggetto = oggetto_selezionato["oggetto"]
        
        # Mostra la descrizione dell'oggetto
        gioco.io.mostra_dialogo(
            f"Oggetto: {oggetto.nome}",
            oggetto.descrizione,
            ["Interagisci", "Torna alla lista"]
        )
        
        # Aggiorna l'handler per gestire l'interazione con l'oggetto
        stato._handle_dialog_choice = lambda event: handle_object_interaction(event, oggetto, stato)
    else:
        # Se non troviamo l'oggetto, mostra un errore
        gioco.io.mostra_notifica({
            "text": "Oggetto non trovato!",
            "type": "error",
            "duration": 2.0
        })
        
        # Torna al menu principale
        stato.menu_handler.mostra_menu_principale(gioco)

def handle_object_interaction(event, oggetto, stato):
    """Gestisce l'interazione con un oggetto specifico"""
    gioco = stato.gioco
    choice = event.get("choice", "")
    
    if choice == "Interagisci":
        # Effetto audio
        gioco.io.play_sound({
            "sound_id": "item_use",
            "volume": 0.7
        })
        
        # Interagisci con l'oggetto
        risultato = oggetto.interagisci(gioco.giocatore)
        
        # Mostra il risultato dell'interazione
        gioco.io.mostra_notifica({
            "text": risultato if risultato else f"Hai interagito con {oggetto.nome}",
            "type": "success" if risultato else "info",
            "duration": 2.0
        })
        
        # Torna al menu principale
        stato.menu_handler.mostra_menu_principale(gioco)
    elif choice == "Torna alla lista":
        # Effetto audio
        gioco.io.play_sound({
            "sound_id": "menu_back", 
            "volume": 0.5
        })
        
        # Torna alla lista degli oggetti
        gestisci_esplorazione_oggetti(stato, gioco)
    else:
        # Torna al menu principale
        stato.menu_handler.mostra_menu_principale(gioco) 