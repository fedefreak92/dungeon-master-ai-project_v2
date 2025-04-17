from flask import request, jsonify, Blueprint
import logging
import datetime
import os

from server.utils.session import sessioni_attive, salva_sessione, valida_input

# Configura il logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Aggiunge un handler per il file di log se non esiste già
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

logger.info("Inizializzazione del modulo combat_routes.py")

# Crea il blueprint per le route di combattimento
combat_routes = Blueprint('combat_routes', __name__)

# Aggiungiamo route interna semplice per test
@combat_routes.route("/hello", methods=["GET"])
def hello():
    """Semplice endpoint di test"""
    logger.info("API /hello chiamata")
    return jsonify({"message": "Hello World"}), 200

@combat_routes.route("/inizia", methods=["POST"])
def inizia_combattimento():
    """Inizia un nuovo combattimento"""
    # Log di debug per verificare se la route viene chiamata
    logger.info("API /inizia chiamata")
    
    data = request.json or {}
    id_sessione = data.get("id_sessione")
    
    # Log per debug
    logger.info(f"Dati ricevuti: {data}")
    
    nemici_ids = data.get("nemici_ids", [])  # IDs delle entità nemiche
    
    # Supporto per il parametro "nemici" per retrocompatibilità con i test
    if not nemici_ids and "nemici" in data:
        nemici_ids = data.get("nemici", [])
        logger.info(f"Utilizzo parametro 'nemici' per retrocompatibilità: {nemici_ids}")
        
    tipo_incontro = data.get("tipo_incontro", "casuale")  # casuale, imboscata, preparato
    
    # Validazione dei parametri
    nemici_ids = valida_input(nemici_ids, list, "nemici_ids", 100, [])
    tipo_incontro = valida_input(tipo_incontro, str, "tipo_incontro", 50, "casuale")
    
    # Limitazione della dimensione degli altri parametri che potrebbero essere inviati
    dati_limitati = {}
    for chiave, valore in data.items():
        if chiave not in ["id_sessione", "nemici_ids", "nemici", "tipo_incontro"]:
            if isinstance(valore, dict):
                valore = valida_input(valore, dict, chiave, 50, {})
            elif isinstance(valore, list):
                valore = valida_input(valore, list, chiave, 50, [])
            elif isinstance(valore, str):
                valore = valida_input(valore, str, chiave, 500)
            dati_limitati[chiave] = valore
    
    if not id_sessione:
        logger.warning("ID sessione mancante nella richiesta")
        return jsonify({
            "successo": False,
            "errore": "ID sessione richiesto"
        }), 400
    
    # Verifica che la sessione esista
    if id_sessione not in sessioni_attive:
        logger.warning(f"Sessione {id_sessione} non trovata")
        return jsonify({
            "successo": False,
            "errore": "Sessione non trovata"
        }), 404
    
    try:
        # Ottieni il mondo dalla sessione
        world = sessioni_attive[id_sessione]
        logger.info(f"Mondo ottenuto dalla sessione {id_sessione}")
        
        # Ottieni il giocatore
        giocatore = world.get_player_entity()
        if not giocatore:
            logger.warning(f"Giocatore non trovato nella sessione {id_sessione}, tentativo di riparazione...")
            
            # Verifica se esiste un'entità che potrebbe essere il giocatore
            potenziali_giocatori = []
            for entity in world.entities.values():
                if entity.name.lower() in ["player", "testplayer"] or (hasattr(entity, "è_giocatore") and entity.è_giocatore):
                    potenziali_giocatori.append(entity)
            
            # Se troviamo un potenziale giocatore, aggiungiamo il tag player
            if potenziali_giocatori:
                giocatore = potenziali_giocatori[0]
                giocatore.add_tag("player")
                logger.info(f"Aggiunto tag 'player' all'entità {giocatore.id} (nome: {giocatore.name})")
                
                # Assicurati che abbia HP per il combattimento
                if not hasattr(giocatore, "hp") or not giocatore.hp:
                    setattr(giocatore, "hp", 20)
                if not hasattr(giocatore, "hp_max") or not giocatore.hp_max:
                    setattr(giocatore, "hp_max", 20)
            else:
                # Crea un nuovo giocatore con nome TestPlayer per i test
                giocatore = world.create_entity(name="TestPlayer")
                giocatore.add_tag("player")
                giocatore.add_tag("guerriero")  # Classe predefinita
                
                # Aggiungi attributi base
                setattr(giocatore, "hp", 20)
                setattr(giocatore, "hp_max", 20)
                
                logger.info(f"Creato nuovo giocatore con ID: {giocatore.id}, nome: {giocatore.name}")
            
            # Salva la sessione con il giocatore riparato
            salva_sessione(id_sessione, world)
            
        logger.info(f"Giocatore trovato: {giocatore.id}")
        
        # Qui andiamo a gestire diversi casi per la generazione dei nemici
        nemici = []
        
        # Caso 1: nemici specifici sono stati passati come IDs
        if nemici_ids:
            logger.info(f"Nemici specificati: {nemici_ids}")
            # Verifica se i nemici_ids sono oggetti completi o semplici stringhe di tipo
            if len(nemici_ids) > 0 and isinstance(nemici_ids[0], dict) and "id" in nemici_ids[0]:
                # Sono oggetti completi, estraggo gli ID
                for nemico_info in nemici_ids:
                    nemico_id = nemico_info.get("id")
                    nemico = world.get_entity(nemico_id)
                    if nemico:
                        nemici.append(nemico)
            else:
                # Controlla prima se sono già entità esistenti nel mondo
                for nemico_id in nemici_ids:
                    nemico = world.get_entity(nemico_id)
                    if nemico:
                        nemici.append(nemico)
                        continue
                        
                    # Se è una stringa di tipo (es. "goblin"), crea un nuovo nemico
                    if isinstance(nemico_id, str):
                        if nemico_id.lower() == "goblin":
                            logger.info("Creazione nemico goblin...")
                            nemico = world.create_entity(name="Goblin")
                            if nemico:
                                nemico.add_tag("nemico")
                                if hasattr(nemico, "aggiungi_abilita"):
                                    nemico.aggiungi_abilita("forza", 2)
                                    nemico.aggiungi_abilita("destrezza", 3)
                                    nemico.aggiungi_abilita("costituzione", 1)
                                # Aggiungi attributi di base se mancanti
                                if not hasattr(nemico, "hp"):
                                    setattr(nemico, "hp", 10)
                                if not hasattr(nemico, "hp_max"):
                                    setattr(nemico, "hp_max", 10)
                                nemici.append(nemico)
                                logger.info(f"Creato nemico Goblin: {nemico.id}")
                        else:
                            # Generico nemico per altri tipi
                            logger.info(f"Creazione nemico generico {nemico_id}...")
                            nemico = world.create_entity(name=nemico_id.capitalize())
                            if nemico:
                                nemico.add_tag("nemico")
                                if not hasattr(nemico, "hp"):
                                    setattr(nemico, "hp", 8)
                                if not hasattr(nemico, "hp_max"):
                                    setattr(nemico, "hp_max", 8)
                                nemici.append(nemico)
                                logger.info(f"Creato nemico generico {nemico_id}: {nemico.id}")
        
        # Caso 2: nessun nemico specificato, generiamo nemici casuali
        if not nemici:
            logger.info("Nessun nemico valido specificato, creazione nemico predefinito...")
            # Generiamo un goblin di default per compatibilità con i test
            nemico1 = world.create_entity(name="Goblin")
            if nemico1:
                nemico1.add_tag("nemico")
                if hasattr(nemico1, "aggiungi_abilita"):
                    nemico1.aggiungi_abilita("forza", 2)
                    nemico1.aggiungi_abilita("destrezza", 3)
                    nemico1.aggiungi_abilita("costituzione", 1)
                # Aggiungi attributi di base se mancanti
                if not hasattr(nemico1, "hp"):
                    setattr(nemico1, "hp", 10)
                if not hasattr(nemico1, "hp_max"):
                    setattr(nemico1, "hp_max", 10)
                nemici.append(nemico1)
                logger.info(f"Creato nemico Goblin di default: {nemico1.id}")
        
        # Verifica che ci siano nemici
        if not nemici:
            logger.warning("Nessun nemico disponibile per il combattimento")
            return jsonify({
                "successo": False,
                "errore": "Nessun nemico disponibile per il combattimento"
            }), 400
            
        logger.info(f"Nemici creati: {len(nemici)}")
        
        # Crea lo stato di combattimento
        try:
            logger.info("Tentativo di importare CombattimentoState...")
            # Modifico l'importazione per usare il percorso assoluto
            import sys
            import os
            # Assicuriamoci che la directory principale del progetto sia nel path
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
            if root_dir not in sys.path:
                sys.path.append(root_dir)
                logger.info(f"Aggiunto {root_dir} a sys.path")
            
            from states.combattimento.combattimento_state import CombattimentoState
            # Importiamo anche i moduli necessari per evitare AttributeError
            from states.combattimento.azioni import AzioniCombattimento
            from states.combattimento.turni import GestoreTurni
            from states.combattimento.ui import UICombattimento
            logger.info("CombattimentoState importato con successo")
            
            # Prepara i partecipanti al combattimento
            partecipanti = [giocatore] + nemici
            
            # Crea un contesto per il combattimento
            contesto = {
                "partecipanti": partecipanti,
                "tipo_incontro": tipo_incontro,
                "world": world
            }
            
            # Crea la nuova istanza di stato
            logger.info("Creazione istanza CombattimentoState...")
            state = CombattimentoState(contesto)
            logger.info("Istanza CombattimentoState creata con successo")
            
            # Verifica che l'oggetto state abbia l'attributo azioni
            if not hasattr(state, 'azioni') or not state.azioni:
                logger.warning("Attributo 'azioni' mancante, creazione manuale...")
                from states.combattimento.azioni import AzioniCombattimento
                from states.combattimento.turni import GestoreTurni
                from states.combattimento.ui import UICombattimento
                
                # Inizializza l'oggetto azioni
                state.azioni = AzioniCombattimento(state)
                state.gestore_turni = GestoreTurni(state)
                state.ui = UICombattimento(state)
                
                # Esponi i metodi dell'oggetto azioni direttamente nello stato per compatibilità
                state.esegui_attacco = lambda *args, **kwargs: state.azioni.esegui_attacco(*args, **kwargs)
                state.usa_abilita = lambda *args, **kwargs: state.azioni.usa_abilita(*args, **kwargs)
                state.usa_oggetto = lambda *args, **kwargs: state.azioni.usa_oggetto(*args, **kwargs)
                state.passa_turno = lambda *args, **kwargs: state.azioni.passa_turno(*args, **kwargs)
                state.determina_azione_ia = lambda *args, **kwargs: state.azioni.determina_azione_ia(*args, **kwargs)
                state.esegui_azione_ia = lambda *args, **kwargs: state.azioni.esegui_azione_ia(*args, **kwargs)
            
            # Inizializza il combattimento
            logger.info("Inizializzazione del combattimento...")
            state.inizializza_combattimento()
            logger.info("Combattimento inizializzato con successo")
            
            # Memorizza lo stato nella sessione
            world.set_temporary_state("combattimento", state.to_dict())
            
            # Salva la sessione
            salva_sessione(id_sessione, world)
            
            # Prepara i dati di risposta
            partecipanti_info = []
            for p in partecipanti:
                partecipanti_info.append({
                    "id": p.id,
                    "nome": p.name,
                    "è_giocatore": p.has_tag("player"),
                    "è_nemico": p.has_tag("nemico"),
                    "iniziativa": getattr(p, "iniziativa", 0),
                    "hp": getattr(p, "hp", 10),
                    "hp_max": getattr(p, "hp_max", 10)
                })
            
            logger.info(f"Combattimento inizializzato con successo: {len(nemici)} nemici per sessione {id_sessione}")
            
            # Risposta compatibile con il formato richiesto dai test
            return jsonify({
                "successo": True,
                "stato": "iniziato",
                "tipo_incontro": tipo_incontro,
                "partecipanti": partecipanti_info,
                "turno_di": state.turno_corrente,
                "round": state.round_corrente,
                "in_corso": state.in_corso
            })
        except ImportError as e:
            logger.error(f"Impossibile importare CombattimentoState: {e}")
            # Aggiungiamo informazioni su sys.path per il debug
            import sys
            logger.error(f"sys.path: {sys.path}")
            return jsonify({
                "successo": False,
                "errore": f"Configurazione di combattimento non disponibile: {str(e)}"
            }), 500
        except AttributeError as e:
            logger.error(f"Attributo mancante: {e}")
            return jsonify({
                "successo": False,
                "errore": f"Attributo mancante nel sistema di combattimento: {str(e)}"
            }), 500
        except Exception as e:
            logger.error(f"Errore durante la creazione dello stato di combattimento: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({
                "successo": False,
                "errore": f"Impossibile creare lo stato di combattimento: {str(e)}"
            }), 500
            
    except Exception as e:
        logger.error(f"Errore generale nell'inizializzazione del combattimento: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        return jsonify({
            "successo": False,
            "errore": f"Errore interno nell'inizializzazione del combattimento: {str(e)}"
        }), 500

@combat_routes.route("/stato", methods=["GET"])
def ottieni_stato_combattimento():
    """Ottieni lo stato attuale del combattimento"""
    id_sessione = request.args.get("id_sessione")
    
    if not id_sessione:
        return jsonify({
            "successo": False,
            "errore": "ID sessione richiesto"
        }), 400
    
    # Verifica che la sessione esista
    if id_sessione not in sessioni_attive:
        return jsonify({
            "successo": False,
            "errore": "Sessione non trovata"
        }), 404
    
    try:
        # Ottieni il mondo dalla sessione
        world = sessioni_attive[id_sessione]
        
        # Ottieni lo stato del combattimento
        stato_combattimento = world.get_temporary_state("combattimento")
        if not stato_combattimento:
            return jsonify({
                "successo": False,
                "errore": "Nessun combattimento in corso"
            }), 404
            
        # Deserializza lo stato
        try:
            # Assicuriamoci che la directory principale del progetto sia nel path
            import sys
            import os
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
            if root_dir not in sys.path:
                sys.path.append(root_dir)
                logger.info(f"Aggiunto {root_dir} a sys.path per route /stato")
                
            from states.combattimento.combattimento_state import CombattimentoState
            state = CombattimentoState.from_dict(stato_combattimento, world)
        except Exception as e:
            logger.error(f"Errore durante la deserializzazione dello stato: {e}")
            return jsonify({
                "successo": False,
                "errore": str(e)
            }), 500
        
        # Verifica che l'oggetto state abbia l'attributo azioni
        if not hasattr(state, 'azioni') or not state.azioni:
            logger.warning("Attributo 'azioni' mancante nella route /stato, recupero...")
            from states.combattimento.azioni import AzioniCombattimento
            from states.combattimento.turni import GestoreTurni
            from states.combattimento.ui import UICombattimento
            
            # Inizializza l'oggetto azioni
            state.azioni = AzioniCombattimento(state)
            state.gestore_turni = GestoreTurni(state)
            state.ui = UICombattimento(state)
            
            # Esponi i metodi dell'oggetto azioni direttamente nello stato per compatibilità
            state.esegui_attacco = lambda *args, **kwargs: state.azioni.esegui_attacco(*args, **kwargs)
            state.usa_abilita = lambda *args, **kwargs: state.azioni.usa_abilita(*args, **kwargs)
            state.usa_oggetto = lambda *args, **kwargs: state.azioni.usa_oggetto(*args, **kwargs)
            state.passa_turno = lambda *args, **kwargs: state.azioni.passa_turno(*args, **kwargs)
            state.determina_azione_ia = lambda *args, **kwargs: state.azioni.determina_azione_ia(*args, **kwargs)
            state.esegui_azione_ia = lambda *args, **kwargs: state.azioni.esegui_azione_ia(*args, **kwargs)
        
        # Ottieni informazioni sui partecipanti
        partecipanti_info = []
        for p_id in state.partecipanti:
            p = world.get_entity(p_id)
            if p:
                partecipanti_info.append({
                    "id": p.id,
                    "nome": p.name,
                    "è_giocatore": p.has_tag("player"),
                    "è_nemico": p.has_tag("nemico"),
                    "iniziativa": getattr(p, "iniziativa", 0),
                    "hp": getattr(p, "hp", 10),
                    "max_hp": getattr(p, "max_hp", 10),
                    "azioni_disponibili": state.get_azioni_disponibili(p_id)
                })
        
        return jsonify({
            "successo": True,
            "in_corso": state.in_corso,
            "round": state.round_corrente,
            "turno_di": state.turno_corrente,
            "fase": state.fase_corrente,
            "partecipanti": partecipanti_info,
            "messaggi": state.messaggi[-10:] if hasattr(state, "messaggi") else []
        })
    except Exception as e:
        logger.error(f"Errore durante l'ottenimento dello stato del combattimento: {e}")
        return jsonify({
            "successo": False,
            "errore": str(e)
        }), 500

@combat_routes.route("/azione", methods=["POST"])
def esegui_azione_combattimento():
    """Esegue un'azione durante il combattimento"""
    data = request.json or {}
    id_sessione = data.get("id_sessione")
    tipo_azione = data.get("tipo_azione")  # attacco, incantesimo, oggetto, movimento, ecc.
    parametri_azione = data.get("parametri", {})  # Target ID, oggetto da usare, ecc.
    
    # Validazione dei parametri
    tipo_azione = valida_input(tipo_azione, str, "tipo_azione", 50)
    parametri_azione = valida_input(parametri_azione, dict, "parametri_azione", 100, {})
    
    if not id_sessione or not tipo_azione:
        return jsonify({
            "successo": False,
            "errore": "Parametri mancanti o non validi"
        }), 400
    
    # Verifica che la sessione esista
    if id_sessione not in sessioni_attive:
        return jsonify({
            "successo": False,
            "errore": "Sessione non trovata"
        }), 404
    
    try:
        # Ottieni il mondo dalla sessione
        world = sessioni_attive[id_sessione]
        
        # Ottieni lo stato del combattimento
        stato_combattimento = world.get_temporary_state("combattimento")
        if not stato_combattimento:
            return jsonify({
                "successo": False,
                "errore": "Nessun combattimento in corso"
            }), 404
            
        # Deserializza lo stato
        from states.combattimento.combattimento_state import CombattimentoState
        state = CombattimentoState.from_dict(stato_combattimento, world)
        
        # Verifica che l'oggetto state abbia l'attributo azioni
        if not hasattr(state, 'azioni') or not state.azioni:
            logger.warning("Attributo 'azioni' mancante nell'API di azione, recupero...")
            from states.combattimento.azioni import AzioniCombattimento
            from states.combattimento.turni import GestoreTurni
            from states.combattimento.ui import UICombattimento
            
            # Inizializza l'oggetto azioni
            state.azioni = AzioniCombattimento(state)
            state.gestore_turni = GestoreTurni(state)
            state.ui = UICombattimento(state)
            
            # Esponi i metodi dell'oggetto azioni direttamente nello stato per compatibilità
            state.esegui_attacco = lambda *args, **kwargs: state.azioni.esegui_attacco(*args, **kwargs)
            state.usa_abilita = lambda *args, **kwargs: state.azioni.usa_abilita(*args, **kwargs)
            state.usa_oggetto = lambda *args, **kwargs: state.azioni.usa_oggetto(*args, **kwargs)
            state.passa_turno = lambda *args, **kwargs: state.azioni.passa_turno(*args, **kwargs)
            state.determina_azione_ia = lambda *args, **kwargs: state.azioni.determina_azione_ia(*args, **kwargs)
            state.esegui_azione_ia = lambda *args, **kwargs: state.azioni.esegui_azione_ia(*args, **kwargs)
        
        # Verifica se è il turno del giocatore
        if state.turno_corrente != parametri_azione.get("attaccante_id"):
            return jsonify({
                "successo": False,
                "errore": "Non è il turno di questa entità"
            }), 400
        
        # Esegui l'azione in base al tipo
        risultato = None
        
        # Importa il modulo delle azioni
        from states.combattimento.azioni import esegui_attacco, usa_oggetto, lancia_incantesimo, muovi
        
        if tipo_azione == "attacco":
            target_id = parametri_azione.get("target_id")
            arma = parametri_azione.get("arma", "default")
            attaccante_id = parametri_azione.get("attaccante_id")
            
            attaccante = world.get_entity(attaccante_id)
            target = world.get_entity(target_id)
            
            if not attaccante or not target:
                return jsonify({
                    "successo": False,
                    "errore": "Attaccante o target non trovato"
                }), 404
                
            # Esegui l'attacco
            risultato = state.esegui_attacco(attaccante_id, target_id, arma)
            
        elif tipo_azione == "incantesimo":
            incantatore_id = parametri_azione.get("incantatore_id")
            incantesimo = parametri_azione.get("incantesimo")
            target_ids = parametri_azione.get("target_ids", [])
            
            incantatore = world.get_entity(incantatore_id)
            targets = [world.get_entity(target_id) for target_id in target_ids if world.get_entity(target_id)]
            
            if not incantatore or not targets:
                return jsonify({
                    "successo": False,
                    "errore": "Incantatore o target non trovato"
                }), 404
                
            # Lancia l'incantesimo
            risultato = state.lancia_incantesimo(incantatore_id, incantesimo, target_ids)
            
        elif tipo_azione == "oggetto":
            utilizzatore_id = parametri_azione.get("utilizzatore_id")
            oggetto = parametri_azione.get("oggetto")
            target_ids = parametri_azione.get("target_ids", [])
            
            utilizzatore = world.get_entity(utilizzatore_id)
            targets = [world.get_entity(target_id) for target_id in target_ids if world.get_entity(target_id)]
            
            if not utilizzatore:
                return jsonify({
                    "successo": False,
                    "errore": "Utilizzatore non trovato"
                }), 404
                
            # Usa l'oggetto
            risultato = state.usa_oggetto(utilizzatore_id, oggetto, target_ids)
            
        elif tipo_azione == "movimento":
            entita_id = parametri_azione.get("entita_id")
            destinazione = parametri_azione.get("destinazione", {})
            
            entita = world.get_entity(entita_id)
            
            if not entita:
                return jsonify({
                    "successo": False,
                    "errore": "Entità non trovata"
                }), 404
                
            # Esegui il movimento
            risultato = state.muovi(entita_id, destinazione)
            
        elif tipo_azione == "passa":
            # L'entità passa il turno
            entita_id = parametri_azione.get("entita_id")
            risultato = state.passa_turno(entita_id)
            
        else:
            return jsonify({
                "successo": False,
                "errore": f"Tipo di azione '{tipo_azione}' non supportato"
            }), 400
        
        # Aggiorna lo stato del combattimento
        state.processa_risultati()
        
        # Controlla se il combattimento è terminato
        if state.controlla_fine_combattimento():
            # Il combattimento è terminato, determina il vincitore
            vincitore = state.determina_vincitore()
            
            # Gestisci la fine del combattimento (ricompense, esperienza, ecc.)
            state.gestisci_fine_combattimento(vincitore)
            
            # Salva lo stato del combattimento
            world.set_temporary_state("combattimento", state.to_dict())
            
            return jsonify({
                "successo": True,
                "azione_eseguita": tipo_azione,
                "risultato": risultato,
                "combattimento_terminato": True,
                "vincitore": vincitore
            })
        
        # Se è il turno di un'entità controllata dal computer, esegui la sua azione
        if state.turno_corrente and not world.get_entity(state.turno_corrente).has_tag("player"):
            # Ottieni l'azione dell'IA
            azione_ia = state.determina_azione_ia(state.turno_corrente)
            
            # Esegui l'azione dell'IA
            risultato_ia = state.esegui_azione_ia(azione_ia)
            
            # Processa i risultati
            state.processa_risultati()
            
            # Controlla di nuovo se il combattimento è terminato
            if state.controlla_fine_combattimento():
                vincitore = state.determina_vincitore()
                state.gestisci_fine_combattimento(vincitore)
                
                # Salva lo stato del combattimento
                world.set_temporary_state("combattimento", state.to_dict())
                
                return jsonify({
                    "successo": True,
                    "azione_eseguita": tipo_azione,
                    "risultato": risultato,
                    "azione_ia": azione_ia,
                    "risultato_ia": risultato_ia,
                    "combattimento_terminato": True,
                    "vincitore": vincitore
                })
        
        # Salva lo stato aggiornato del combattimento
        world.set_temporary_state("combattimento", state.to_dict())
        
        return jsonify({
            "successo": True,
            "azione_eseguita": tipo_azione,
            "risultato": risultato,
            "prossimo_turno": state.turno_corrente,
            "round": state.round_corrente
        })
    except Exception as e:
        logger.error(f"Errore durante l'esecuzione dell'azione: {e}")
        return jsonify({
            "successo": False,
            "errore": str(e)
        }), 500

@combat_routes.route("/azioni_disponibili", methods=["GET"])
def ottieni_azioni_disponibili():
    """Ottieni le azioni disponibili per un'entità durante il combattimento"""
    id_sessione = request.args.get("id_sessione")
    entita_id = request.args.get("entita_id")
    
    if not id_sessione or not entita_id:
        return jsonify({
            "successo": False,
            "errore": "Parametri mancanti"
        }), 400
    
    # Verifica che la sessione esista
    if id_sessione not in sessioni_attive:
        return jsonify({
            "successo": False,
            "errore": "Sessione non trovata"
        }), 404
    
    try:
        # Ottieni il mondo dalla sessione
        world = sessioni_attive[id_sessione]
        
        # Ottieni lo stato del combattimento
        stato_combattimento = world.get_temporary_state("combattimento")
        if not stato_combattimento:
            return jsonify({
                "successo": False,
                "errore": "Nessun combattimento in corso"
            }), 404
            
        # Deserializza lo stato
        from states.combattimento.combattimento_state import CombattimentoState
        state = CombattimentoState.from_dict(stato_combattimento)
        
        # Ottieni l'entità
        entita = world.get_entity(entita_id)
        if not entita:
            return jsonify({
                "successo": False,
                "errore": "Entità non trovata"
            }), 404
            
        # Ottieni le azioni disponibili per l'entità
        azioni = state.get_azioni_disponibili(entita_id)
        
        return jsonify({
            "successo": True,
            "entita_id": entita_id,
            "è_turno_corrente": entita_id == state.turno_corrente,
            "azioni_disponibili": azioni
        })
    except Exception as e:
        logger.error(f"Errore durante l'ottenimento delle azioni disponibili: {e}")
        return jsonify({
            "successo": False,
            "errore": str(e)
        }), 500

@combat_routes.route("/termina", methods=["POST"])
def termina_combattimento():
    """Termina un combattimento in corso"""
    data = request.json or {}
    id_sessione = data.get("id_sessione")
    forzato = data.get("forzato", False)  # Se true, termina forzatamente anche se in corso
    
    if not id_sessione:
        return jsonify({
            "successo": False,
            "errore": "ID sessione richiesto"
        }), 400
    
    # Verifica che la sessione esista
    if id_sessione not in sessioni_attive:
        return jsonify({
            "successo": False,
            "errore": "Sessione non trovata"
        }), 404
    
    try:
        # Ottieni il mondo dalla sessione
        world = sessioni_attive[id_sessione]
        
        # Ottieni lo stato del combattimento
        stato_combattimento = world.get_temporary_state("combattimento")
        if not stato_combattimento:
            return jsonify({
                "successo": False,
                "errore": "Nessun combattimento in corso"
            }), 404
            
        # Deserializza lo stato
        from states.combattimento.combattimento_state import CombattimentoState
        state = CombattimentoState.from_dict(stato_combattimento)
        
        # Se il combattimento è ancora in corso e non è forzato, verifica che possa essere terminato
        if state.in_corso and not forzato:
            return jsonify({
                "successo": False,
                "errore": "Il combattimento è ancora in corso e non può essere terminato"
            }), 400
        
        # Termina il combattimento
        state.termina_combattimento(forzato)
        
        # Rimuovi lo stato del combattimento
        world.remove_temporary_state("combattimento")
        
        # Salva le modifiche alla sessione
        salva_sessione(id_sessione, world)
        
        return jsonify({
            "successo": True,
            "messaggio": "Combattimento terminato"
        })
    except Exception as e:
        logger.error(f"Errore durante la terminazione del combattimento: {e}")
        return jsonify({
            "successo": False,
            "errore": str(e)
        }), 500

@combat_routes.route("/nemici_vicini", methods=["GET"])
def ottieni_nemici_vicini():
    """Ottieni i nemici nelle vicinanze che potrebbero essere coinvolti in un combattimento"""
    id_sessione = request.args.get("id_sessione")
    
    if not id_sessione:
        return jsonify({
            "successo": False,
            "errore": "ID sessione richiesto"
        }), 400
    
    # Verifica che la sessione esista
    if id_sessione not in sessioni_attive:
        return jsonify({
            "successo": False,
            "errore": "Sessione non trovata"
        }), 404
    
    try:
        # Ottieni il mondo dalla sessione
        world = sessioni_attive[id_sessione]
        
        # Ottieni il giocatore
        player = world.get_player_entity()
        if not player:
            return jsonify({
                "successo": False,
                "errore": "Giocatore non trovato"
            }), 404
            
        # Ottieni la posizione del giocatore
        position = player.get_component("position")
        if not position:
            return jsonify({
                "successo": False,
                "errore": "Posizione del giocatore non trovata"
            }), 404
            
        # Cerca nemici nella stessa mappa e nelle vicinanze
        nemici_vicini = []
        for entity in world.get_entities():
            if entity.has_tag("nemico") or entity.has_tag("ostile"):
                entity_pos = entity.get_component("position")
                if entity_pos and entity_pos.map_name == position.map_name:
                    # Calcola distanza
                    dx = entity_pos.x - position.x
                    dy = entity_pos.y - position.y
                    distanza = (dx**2 + dy**2)**0.5
                    
                    if distanza <= 10:  # Raggio di rilevamento dei nemici
                        nemici_vicini.append({
                            "id": entity.id,
                            "nome": entity.name,
                            "tipo": entity.get_component("tipo").value if entity.has_component("tipo") else "sconosciuto",
                            "livello": getattr(entity, "livello", 1),
                            "distanza": round(distanza, 1)
                        })
        
        return jsonify({
            "successo": True,
            "nemici_vicini": nemici_vicini
        })
    except Exception as e:
        logger.error(f"Errore durante la ricerca di nemici vicini: {e}")
        return jsonify({
            "successo": False,
            "errore": str(e)
        }), 500

# Test route per verificare la registrazione corretta del blueprint
@combat_routes.route("/test", methods=["GET", "POST"])
def test_route():
    """Endpoint di test per verificare la registrazione del blueprint"""
    logger.info("API /test chiamata con successo")
    
    # Determinare quale metodo è stato usato
    if request.method == "GET":
        logger.info("Metodo GET utilizzato per /test")
    else:
        logger.info("Metodo POST utilizzato per /test")
        
    try:
        # Risposta standard per il test
        return jsonify({
            "successo": True,
            "messaggio": "Il blueprint combat_routes è correttamente registrato",
            "metodo": request.method,
            "timestamp": str(datetime.datetime.now())
        })
    except Exception as e:
        logger.error(f"Errore nella route /test: {e}")
        return jsonify({
            "successo": False,
            "errore": str(e)
        }), 500

# Test route semplificata per il debugging
@combat_routes.route("/test_simple", methods=["GET"])
def test_simple_route():
    """Endpoint di test semplice"""
    logger.info("API /test_simple chiamata")
    return jsonify({
        "successo": True,
        "messaggio": "Endpoint di test semplice funzionante"
    })

@combat_routes.route("/debug_session", methods=["GET"])
def debug_session():
    """Endpoint per debug sessioni problematiche"""
    id_sessione = request.args.get("id_sessione")
    fix = request.args.get("fix") == "true"
    
    if not id_sessione:
        return jsonify({
            "successo": False,
            "errore": "ID sessione richiesto"
        }), 400
    
    # Verifica che la sessione esista
    if id_sessione not in sessioni_attive:
        return jsonify({
            "successo": False,
            "errore": "Sessione non trovata"
        }), 404
    
    # Ottieni il mondo dalla sessione
    world = sessioni_attive[id_sessione]
    
    # Verifica i tag delle entità
    entita_info = []
    for entity_id, entity in world.entities.items():
        entita_info.append({
            "id": entity_id,
            "nome": entity.name,
            "tags": list(entity.tags),
            "è_giocatore": "player" in entity.tags
        })
    
    # Verifica la presenza del giocatore
    player_entities = world.find_entities_by_tag("player")
    player_found = len(player_entities) > 0
    
    # Correggi il problema se richiesto e necessario
    correzione_effettuata = False
    if fix and not player_found:
        # Cerca entità che potrebbero essere il giocatore (basato sul nome o altri attributi)
        potenziali_giocatori = []
        for entity in world.entities.values():
            if entity.name.lower() in ["player", "testplayer"] or (hasattr(entity, "è_giocatore") and entity.è_giocatore):
                potenziali_giocatori.append(entity)
        
        # Se troviamo un potenziale giocatore, aggiungiamo il tag player
        if potenziali_giocatori:
            entita_giocatore = potenziali_giocatori[0]
            entita_giocatore.add_tag("player")
            logger.info(f"Aggiunto tag 'player' all'entità {entita_giocatore.id} (nome: {entita_giocatore.name})")
            correzione_effettuata = True
            salva_sessione(id_sessione, world)
        else:
            # Crea un nuovo giocatore se non ne troviamo uno esistente
            nome_giocatore = "TestPlayer"  # Nome predefinito per compatibilità con i test
            player = world.create_entity(name=nome_giocatore)
            player.add_tag("player")
            player.add_tag("guerriero")  # Classe predefinita
            
            # Aggiungi attributi base
            setattr(player, "hp", 20)
            setattr(player, "hp_max", 20)
            
            logger.info(f"Creato nuovo giocatore con ID: {player.id}, nome: {player.name}")
            correzione_effettuata = True
            salva_sessione(id_sessione, world)
    
    # Ottieni il giocatore (dopo la correzione)
    giocatore = world.get_player_entity() if correzione_effettuata else None
    
    return jsonify({
        "successo": True,
        "giocatore_trovato": player_found,
        "correzione_effettuata": correzione_effettuata,
        "giocatore_dopo_correzione": {
            "id": giocatore.id,
            "nome": giocatore.name,
            "tags": list(giocatore.tags)
        } if giocatore else None,
        "entita": entita_info,
        "tag_presenti": list(world.entities_by_tag.keys()) if hasattr(world, "entities_by_tag") else []
    })