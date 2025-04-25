from flask import Blueprint, request, jsonify
from server.utils.session import get_session, salva_sessione
import logging

# Configura il logger
logger = logging.getLogger(__name__)

# Crea blueprint per le route del mercato
mercato_routes = Blueprint('mercato_routes', __name__)

@mercato_routes.route("/stato", methods=['GET'])
def get_mercato_state():
    """Ottiene lo stato attuale del mercato"""
    id_sessione = request.args.get('id_sessione')
    if not id_sessione:
        return jsonify({"success": False, "error": "ID sessione mancante"}), 400
        
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni lo stato mercato dalla sessione
    mercato_state = sessione.get_state("mercato")
    if not mercato_state:
        return jsonify({"success": False, "error": "Stato mercato non disponibile"}), 404
    
    # Restituisci i dati del mercato
    return jsonify({
        "success": True, 
        "stato": mercato_state.to_dict()
    })

@mercato_routes.route("/interagisci", methods=['POST'])
def interagisci_oggetto():
    """Gestisce l'interazione con un oggetto nel mercato"""
    data = request.json
    if not data or 'id_sessione' not in data or 'oggetto_id' not in data:
        return jsonify({"success": False, "error": "Dati mancanti"}), 400
    
    id_sessione = data['id_sessione']
    oggetto_id = data['oggetto_id']
    
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni lo stato mercato dalla sessione
    mercato_state = sessione.get_state("mercato")
    if not mercato_state:
        return jsonify({"success": False, "error": "Stato mercato non disponibile"}), 404
    
    # Verifica se l'oggetto esiste
    if oggetto_id not in mercato_state.oggetti_interattivi:
        return jsonify({"success": False, "error": "Oggetto non trovato"}), 404
    
    # Esegui l'interazione con l'oggetto
    oggetto = mercato_state.oggetti_interattivi[oggetto_id]
    risultato = oggetto.interagisci()
    
    # Salva la sessione aggiornata
    salva_sessione(id_sessione, sessione)
    
    return jsonify({
        "success": True,
        "risultato": risultato
    })

@mercato_routes.route("/dialoga", methods=['POST'])
def dialoga_npg():
    """Gestisce il dialogo con un NPG nel mercato"""
    data = request.json
    if not data or 'id_sessione' not in data or 'npg_nome' not in data:
        return jsonify({"success": False, "error": "Dati mancanti"}), 400
    
    id_sessione = data['id_sessione']
    npg_nome = data['npg_nome']
    opzione_scelta = data.get('opzione_scelta')
    
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni lo stato mercato dalla sessione
    mercato_state = sessione.get_state("mercato")
    if not mercato_state:
        return jsonify({"success": False, "error": "Stato mercato non disponibile"}), 404
    
    # Verifica se l'NPG esiste
    if npg_nome not in mercato_state.npg_presenti:
        return jsonify({"success": False, "error": "NPG non trovato"}), 404
    
    # Accedi all'NPG e gestisci il dialogo
    npg = mercato_state.npg_presenti[npg_nome]
    
    # Se è una nuova conversazione
    if not opzione_scelta:
        mercato_state.nome_npg_attivo = npg_nome
        mercato_state.stato_conversazione = "inizio"
        dialogo = npg.avvia_dialogo()
    else:
        # Continua la conversazione con la scelta corrente
        dialogo = npg.continua_dialogo(opzione_scelta)
        mercato_state.ultimo_input = opzione_scelta
    
    # Salva la sessione aggiornata
    salva_sessione(id_sessione, sessione)
    
    return jsonify({
        "success": True,
        "dialogo": dialogo
    })

@mercato_routes.route("/menu", methods=['POST'])
def gestisci_menu():
    """Gestisce le interazioni con i menu del mercato"""
    data = request.json
    if not data or 'id_sessione' not in data or 'menu_id' not in data:
        return jsonify({"success": False, "error": "Dati mancanti"}), 400
    
    id_sessione = data['id_sessione']
    menu_id = data['menu_id']
    scelta = data.get('scelta')
    
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni lo stato mercato dalla sessione
    mercato_state = sessione.get_state("mercato")
    if not mercato_state:
        return jsonify({"success": False, "error": "Stato mercato non disponibile"}), 404
    
    # Gestisci l'interazione con il menu
    mercato_state.fase = menu_id
    
    if scelta:
        # Memorizza l'ultima scelta dell'utente
        mercato_state.ultima_scelta = scelta
        mercato_state.ultimo_input = scelta
    
    # Esegui la logica del menu appropriato
    if hasattr(mercato_state.menu_handler, f"gestisci_{menu_id}"):
        risultato = getattr(mercato_state.menu_handler, f"gestisci_{menu_id}")(sessione)
    else:
        risultato = {"error": "Menu non implementato"}
    
    # Salva la sessione aggiornata
    salva_sessione(id_sessione, sessione)
    
    return jsonify({
        "success": True,
        "risultato": risultato
    })

@mercato_routes.route("/movimento", methods=['POST'])
def gestisci_movimento():
    """Gestisce il movimento nel mercato"""
    data = request.json
    if not data or 'id_sessione' not in data or 'direzione' not in data:
        return jsonify({"success": False, "error": "Dati mancanti"}), 400
    
    id_sessione = data['id_sessione']
    direzione = data['direzione']
    
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni lo stato mercato dalla sessione
    mercato_state = sessione.get_state("mercato")
    if not mercato_state:
        return jsonify({"success": False, "error": "Stato mercato non disponibile"}), 404
    
    # Verifica se la direzione è valida
    if not hasattr(mercato_state.movimento_handler, 'direzioni') or direzione not in mercato_state.movimento_handler.direzioni:
        return jsonify({"success": False, "error": "Direzione non valida"}), 400
    
    # Ottieni la mappa del mercato e il giocatore
    mappa = sessione.gestore_mappe.ottieni_mappa("mercato")
    giocatore = sessione.giocatore
    
    # Calcola la nuova posizione
    x, y = giocatore.get_posizione("mercato")
    dx, dy = mercato_state.movimento_handler.direzioni[direzione]
    nuova_x, nuova_y = x + dx, y + dy
    
    # Verifica se il movimento è valido
    if mappa.is_valid_position(nuova_x, nuova_y):
        giocatore.imposta_posizione("mercato", nuova_x, nuova_y)
        
        # Verifica se ci sono eventi nella nuova posizione
        evento = mappa.get_event_at(nuova_x, nuova_y)
        
        # Salva la sessione aggiornata
        salva_sessione(id_sessione, sessione)
        
        return jsonify({
            "success": True,
            "posizione": {"x": nuova_x, "y": nuova_y},
            "evento": evento
        })
    else:
        return jsonify({
            "success": False, 
            "error": "Movimento non valido"
        }), 400

@mercato_routes.route("/compra", methods=['POST'])
def compra_oggetto():
    """Gestisce l'acquisto di un oggetto nel mercato"""
    data = request.json
    if not data or 'id_sessione' not in data or 'oggetto_id' not in data:
        return jsonify({"success": False, "error": "Dati mancanti"}), 400
    
    id_sessione = data['id_sessione']
    oggetto_id = data['oggetto_id']
    
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni lo stato mercato dalla sessione
    mercato_state = sessione.get_state("mercato")
    if not mercato_state:
        return jsonify({"success": False, "error": "Stato mercato non disponibile"}), 404
    
    # Ottieni il giocatore
    giocatore = sessione.giocatore
    
    # Simula la logica di acquisto (da implementare in dettaglio)
    try:
        # Verifica se l'oggetto esiste nel mercato
        # Nota: qui dovresti implementare la vera logica di ottenimento degli oggetti disponibili
        oggetti_disponibili = {"pozione_cura": {"nome": "Pozione di Cura", "prezzo": 50}}
        
        if oggetto_id not in oggetti_disponibili:
            return jsonify({"success": False, "error": "Oggetto non in vendita"}), 404
        
        oggetto = oggetti_disponibili[oggetto_id]
        prezzo = oggetto["prezzo"]
        
        # Verifica che il giocatore abbia abbastanza denaro
        if giocatore.monete < prezzo:
            return jsonify({"success": False, "error": "Monete insufficienti"}), 400
        
        # Rimuovi le monete dal giocatore
        giocatore.monete -= prezzo
        
        # Aggiungi l'oggetto all'inventario
        giocatore.inventario.aggiungi_oggetto(oggetto["nome"])
        
        # Salva la sessione aggiornata
        salva_sessione(id_sessione, sessione)
        
        return jsonify({
            "success": True,
            "messaggio": f"Hai acquistato {oggetto['nome']} per {prezzo} monete.",
            "monete_rimanenti": giocatore.monete
        })
    except Exception as e:
        logger.error(f"Errore nell'acquisto oggetto: {e}")
        return jsonify({
            "success": False,
            "error": f"Errore nell'acquisto: {str(e)}"
        }), 500

@mercato_routes.route("/vendi", methods=['POST'])
def vendi_oggetto():
    """Gestisce la vendita di un oggetto nel mercato"""
    data = request.json
    if not data or 'id_sessione' not in data or 'oggetto_id' not in data:
        return jsonify({"success": False, "error": "Dati mancanti"}), 400
    
    id_sessione = data['id_sessione']
    oggetto_id = data['oggetto_id']
    
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni lo stato mercato dalla sessione
    mercato_state = sessione.get_state("mercato")
    if not mercato_state:
        return jsonify({"success": False, "error": "Stato mercato non disponibile"}), 404
    
    # Ottieni il giocatore
    giocatore = sessione.giocatore
    
    # Simula la logica di vendita (da implementare in dettaglio)
    try:
        # Verifica se l'oggetto esiste nell'inventario del giocatore
        if not giocatore.inventario.ha_oggetto(oggetto_id):
            return jsonify({"success": False, "error": "Oggetto non nell'inventario"}), 404
        
        # Determina il valore di vendita (ad esempio, metà del valore originale)
        # Questa è una semplificazione, la logica reale potrebbe essere più complessa
        oggetto_info = giocatore.inventario.get_oggetto(oggetto_id)
        valore_vendita = oggetto_info.get("valore", 0) // 2
        
        # Rimuovi l'oggetto dall'inventario
        giocatore.inventario.rimuovi_oggetto(oggetto_id)
        
        # Aggiungi le monete al giocatore
        giocatore.monete += valore_vendita
        
        # Salva la sessione aggiornata
        salva_sessione(id_sessione, sessione)
        
        return jsonify({
            "success": True,
            "messaggio": f"Hai venduto {oggetto_id} per {valore_vendita} monete.",
            "monete_totali": giocatore.monete
        })
    except Exception as e:
        logger.error(f"Errore nella vendita oggetto: {e}")
        return jsonify({
            "success": False,
            "error": f"Errore nella vendita: {str(e)}"
        }), 500

@mercato_routes.route("/transizione", methods=['POST'])
def transizione_stato():
    """Gestisce le transizioni tra il mercato e altri stati"""
    data = request.json
    if not data or 'id_sessione' not in data or 'stato_destinazione' not in data:
        return jsonify({"success": False, "error": "Dati mancanti"}), 400
    
    id_sessione = data['id_sessione']
    stato_destinazione = data['stato_destinazione']
    parametri = data.get('parametri', {})
    
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni lo stato mercato dalla sessione
    mercato_state = sessione.get_state("mercato")
    if not mercato_state:
        return jsonify({"success": False, "error": "Stato mercato non disponibile"}), 404
    
    # Esegui la transizione verso il nuovo stato
    try:
        sessione.change_state(stato_destinazione, parametri)
        
        # Salva la sessione aggiornata
        salva_sessione(id_sessione, sessione)
        
        return jsonify({
            "success": True,
            "nuovo_stato": stato_destinazione
        })
    except Exception as e:
        logger.error(f"Errore nella transizione: {e}")
        return jsonify({
            "success": False,
            "error": f"Errore nella transizione: {str(e)}"
        }), 500

@mercato_routes.route("/articoli_disponibili", methods=['GET'])
def ottieni_articoli_disponibili():
    """Ottiene la lista degli articoli disponibili nel mercato"""
    id_sessione = request.args.get('id_sessione')
    tipo_articolo = request.args.get('tipo', 'tutti')
    
    if not id_sessione:
        return jsonify({"success": False, "error": "ID sessione mancante"}), 400
        
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni lo stato mercato dalla sessione
    mercato_state = sessione.get_state("mercato")
    if not mercato_state:
        return jsonify({"success": False, "error": "Stato mercato non disponibile"}), 404
    
    # Ottieni il giocatore per informazioni su abilità di contrattazione, reputazione, ecc.
    giocatore = sessione.giocatore
    
    # Simula la logica per ottenere gli articoli disponibili in base al tipo
    try:
        articoli = {}
        
        if tipo_articolo == 'tutti' or tipo_articolo == 'pozioni':
            articoli['pozioni'] = [
                {"id": "pozione_cura", "nome": "Pozione di Cura", "prezzo_base": 10, "descrizione": "Ripristina 20 punti vita."},
                {"id": "pozione_mana", "nome": "Pozione di Mana", "prezzo_base": 15, "descrizione": "Ripristina 15 punti mana."},
                {"id": "pozione_forza", "nome": "Pozione di Forza", "prezzo_base": 25, "descrizione": "Aumenta la forza di 5 per 3 turni."}
            ]
        
        if tipo_articolo == 'tutti' or tipo_articolo == 'tessuti':
            articoli['tessuti'] = [
                {"id": "seta", "nome": "Rotolo di Seta", "prezzo_base": 15, "descrizione": "Seta pregiata delle Isole del Sud."},
                {"id": "cotone_lunare", "nome": "Cotone Lunare", "prezzo_base": 30, "descrizione": "Raro cotone che cresce solo sotto la luna piena."}
            ]
            
        if tipo_articolo == 'tutti' or tipo_articolo == 'armi':
            articoli['armi'] = [
                {"id": "spada_acciaio", "nome": "Spada d'Acciaio", "prezzo_base": 50, "descrizione": "Una robusta spada forgiata da Gundren."},
                {"id": "pugnale_avvelenato", "nome": "Pugnale Avvelenato", "prezzo_base": 75, "descrizione": "Un pugnale trattato con veleno di ragno."}
            ]
        
        return jsonify({
            "success": True,
            "articoli": articoli
        })
    except Exception as e:
        logger.error(f"Errore nel recupero articoli: {e}")
        return jsonify({
            "success": False,
            "error": f"Errore nel recupero articoli: {str(e)}"
        }), 500

@mercato_routes.route("/contratta", methods=['POST'])
def contratta_prezzo():
    """Gestisce la contrattazione del prezzo per un articolo"""
    data = request.json
    if not data or 'id_sessione' not in data or 'articolo_id' not in data:
        return jsonify({"success": False, "error": "Dati mancanti"}), 400
    
    id_sessione = data['id_sessione']
    articolo_id = data['articolo_id']
    offerta = data.get('offerta', 0)
    
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni lo stato mercato dalla sessione
    mercato_state = sessione.get_state("mercato")
    if not mercato_state:
        return jsonify({"success": False, "error": "Stato mercato non disponibile"}), 404
    
    # Ottieni il giocatore
    giocatore = sessione.giocatore
    
    # Simula la logica di contrattazione
    try:
        # Tabella degli articoli (in produzione, questi dati dovrebbero essere recuperati da un database)
        articoli_info = {
            "pozione_cura": {"nome": "Pozione di Cura", "prezzo_base": 10, "min_accettabile": 8},
            "pozione_mana": {"nome": "Pozione di Mana", "prezzo_base": 15, "min_accettabile": 12},
            "pozione_forza": {"nome": "Pozione di Forza", "prezzo_base": 25, "min_accettabile": 20},
            "seta": {"nome": "Rotolo di Seta", "prezzo_base": 15, "min_accettabile": 12},
            "cotone_lunare": {"nome": "Cotone Lunare", "prezzo_base": 30, "min_accettabile": 25},
            "spada_acciaio": {"nome": "Spada d'Acciaio", "prezzo_base": 50, "min_accettabile": 40},
            "pugnale_avvelenato": {"nome": "Pugnale Avvelenato", "prezzo_base": 75, "min_accettabile": 60}
        }
        
        if articolo_id not in articoli_info:
            return jsonify({"success": False, "error": "Articolo non disponibile per contrattazione"}), 404
            
        articolo = articoli_info[articolo_id]
        
        # Calcola il prezzo minimo accettabile (influenzato da abilità carisma/contrattazione)
        abilita_contrattazione = getattr(giocatore, 'abilita_contrattazione', 0)
        modificatore_carisma = getattr(giocatore, 'modificatore_carisma', 0)
        
        # Il prezzo minimo può essere ridotto fino al 20% con alta abilità di contrattazione
        min_accettabile = articolo["min_accettabile"] * (1 - (abilita_contrattazione + modificatore_carisma) * 0.02)
        min_accettabile = max(articolo["min_accettabile"] * 0.8, min_accettabile)  # Non scendere sotto l'80% del min iniziale
        
        # Determina se l'offerta è accettata
        if offerta >= min_accettabile:
            # Contrattazione riuscita
            return jsonify({
                "success": True,
                "esito": "accettato",
                "messaggio": f"La tua offerta di {offerta} monete per {articolo['nome']} è stata accettata!",
                "prezzo_finale": offerta
            })
        else:
            # Calcola una controproposta
            controproposta = (min_accettabile + articolo["prezzo_base"]) / 2
            controproposta = round(controproposta)
            
            return jsonify({
                "success": True,
                "esito": "rifiutato",
                "messaggio": f"La tua offerta è troppo bassa. Il mercante propone {controproposta} monete per {articolo['nome']}.",
                "controproposta": controproposta
            })
    except Exception as e:
        logger.error(f"Errore nella contrattazione: {e}")
        return jsonify({
            "success": False,
            "error": f"Errore nella contrattazione: {str(e)}"
        }), 500

@mercato_routes.route("/prova_abilita", methods=['POST'])
def prova_abilita_contrattazione():
    """Gestisce la prova di abilità per la contrattazione"""
    data = request.json
    if not data or 'id_sessione' not in data or 'articolo_id' not in data:
        return jsonify({"success": False, "error": "Dati mancanti"}), 400
    
    id_sessione = data['id_sessione']
    articolo_id = data['articolo_id']
    tipo_prova = data.get('tipo_prova', 'contrattazione')
    
    sessione = get_session(id_sessione)
    if not sessione:
        return jsonify({"success": False, "error": "Sessione non trovata"}), 404
    
    # Ottieni lo stato mercato dalla sessione
    mercato_state = sessione.get_state("mercato")
    if not mercato_state:
        return jsonify({"success": False, "error": "Stato mercato non disponibile"}), 404
    
    # Ottieni informazioni sull'articolo
    articoli_info = {
        "pozione_cura": {"nome": "Pozione di Cura", "prezzo_base": 10, "min_accettabile": 8, "difficolta": 10},
        "pozione_mana": {"nome": "Pozione di Mana", "prezzo_base": 15, "min_accettabile": 12, "difficolta": 12},
        "pozione_forza": {"nome": "Pozione di Forza", "prezzo_base": 25, "min_accettabile": 20, "difficolta": 15},
        "seta": {"nome": "Rotolo di Seta", "prezzo_base": 15, "min_accettabile": 12, "difficolta": 12},
        "cotone_lunare": {"nome": "Cotone Lunare", "prezzo_base": 30, "min_accettabile": 25, "difficolta": 18},
        "spada_acciaio": {"nome": "Spada d'Acciaio", "prezzo_base": 50, "min_accettabile": 40, "difficolta": 15},
        "pugnale_avvelenato": {"nome": "Pugnale Avvelenato", "prezzo_base": 75, "min_accettabile": 60, "difficolta": 20}
    }
    
    if articolo_id not in articoli_info:
        return jsonify({"success": False, "error": "Articolo non trovato"}), 404
    
    articolo = articoli_info[articolo_id]
    
    # Determina il tipo di prova (contrattazione, persuasione, intimidazione)
    prova_disponibili = {
        "contrattazione": {
            "abilita": "carisma",
            "descrizione": "Tenti di contrattare un prezzo migliore usando la tua abilità nel commercio.",
            "cd": articolo["difficolta"],
            "successo": {
                "sconto": 0.3,  # 30% di sconto sul prezzo base
                "messaggio": f"Sei riuscito a contrattare efficacemente! Il mercante abbassa il prezzo del {articolo['nome']}."
            },
            "fallimento": {
                "sconto": 0.05,  # 5% di sconto sul prezzo base
                "messaggio": "Il mercante non sembra molto impressionato dai tuoi tentativi di contrattazione."
            }
        },
        "persuasione": {
            "abilita": "carisma",
            "descrizione": "Tenti di persuadere il mercante che meriti un prezzo speciale.",
            "cd": articolo["difficolta"] + 2,  # Leggermente più difficile della contrattazione
            "successo": {
                "sconto": 0.35,  # 35% di sconto sul prezzo base
                "messaggio": f"Con le tue parole persuasive, convinci il mercante a darti un ottimo prezzo per il {articolo['nome']}!"
            },
            "fallimento": {
                "sconto": 0,  # Nessuno sconto
                "messaggio": "Il mercante è poco convinto dalle tue argomentazioni."
            }
        },
        "intimidazione": {
            "abilita": "forza",
            "descrizione": "Tenti di intimidire il mercante per ottenere un prezzo migliore.",
            "cd": articolo["difficolta"] + 5,  # Molto più difficile, con conseguenze
            "successo": {
                "sconto": 0.4,  # 40% di sconto sul prezzo base
                "messaggio": f"Il mercante, intimidito, abbassa significativamente il prezzo del {articolo['nome']}."
            },
            "fallimento": {
                "sconto": -0.1,  # Prezzo aumentato del 10%
                "messaggio": "Il mercante si offende per il tuo atteggiamento minaccioso e aumenta il prezzo! Inoltre, la tua reputazione al mercato è diminuita."
            }
        }
    }
    
    if tipo_prova not in prova_disponibili:
        return jsonify({"success": False, "error": "Tipo di prova non disponibile"}), 400
    
    prova = prova_disponibili[tipo_prova]
    
    # Ottieni il giocatore
    giocatore = sessione.giocatore
    
    try:
        # In una vera implementazione, qui dovremmo avviare lo stato ProvaAbilitaState
        # Per semplicità, simulo direttamente il risultato
        
        # Ottieni il valore di abilità del giocatore per la prova
        abilita_valore = getattr(giocatore, prova["abilita"], 10)  # Default a 10 se non trovata
        
        # Simula un tiro di dado (1d20 + abilità)
        import random
        risultato_dado = random.randint(1, 20)
        risultato_totale = risultato_dado + (abilita_valore - 10) // 2  # Calcola il modificatore
        
        # Determina se la prova è un successo
        successo = risultato_totale >= prova["cd"]
        
        if successo:
            # Calcola il nuovo prezzo con lo sconto
            prezzo_originale = articolo["prezzo_base"]
            sconto = prova["successo"]["sconto"]
            nuovo_prezzo = int(prezzo_originale * (1 - sconto))
            messaggio = prova["successo"]["messaggio"]
        else:
            # Calcola il nuovo prezzo (potrebbe essere più alto in caso di fallimento di intimidazione)
            prezzo_originale = articolo["prezzo_base"]
            sconto = prova["fallimento"]["sconto"]
            nuovo_prezzo = int(prezzo_originale * (1 - sconto))
            messaggio = prova["fallimento"]["messaggio"]
        
        # Aggiorna il prezzo dell'articolo nel contesto della sessione
        mercato_state.dati_contestuali[f"prezzo_{articolo_id}"] = nuovo_prezzo
        
        # Salva la sessione aggiornata
        salva_sessione(id_sessione, sessione)
        
        return jsonify({
            "success": True,
            "tipo_prova": tipo_prova,
            "risultato": "successo" if successo else "fallimento",
            "tiro_dado": risultato_dado,
            "totale": risultato_totale,
            "cd": prova["cd"],
            "messaggio": messaggio,
            "prezzo_originale": prezzo_originale,
            "nuovo_prezzo": nuovo_prezzo
        })
        
    except Exception as e:
        logger.error(f"Errore nella prova di abilità: {e}")
        return jsonify({
            "success": False,
            "error": f"Errore nella prova di abilità: {str(e)}"
        }), 500 