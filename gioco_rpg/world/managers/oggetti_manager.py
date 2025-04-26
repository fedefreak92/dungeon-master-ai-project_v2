"""
Manager per la gestione degli oggetti interattivi nelle mappe.
"""

import logging
import json
import os
from pathlib import Path
from items.oggetto_interattivo import OggettoInterattivo, Porta, Baule, Leva, Trappola
from util.data_manager import get_data_manager
from util.safe_loader import SafeLoader
from util.validators import valida_oggetto, trova_posizione_valida, verifica_coordinate_valide

class OggettiManager:
    """
    Manager per la gestione degli oggetti interattivi nelle mappe.
    Si occupa del caricamento, posizionamento e interazione con gli oggetti.
    """
    def __init__(self, percorso_oggetti=None):
        """
        Inizializza il manager degli oggetti interattivi.
        
        Args:
            percorso_oggetti: Percorso alla directory contenente le configurazioni degli oggetti
        """
        self.percorso_oggetti = percorso_oggetti or Path("data/items")
        if self.percorso_oggetti:
            self._verifica_percorso(self.percorso_oggetti, "oggetti")
            
        self.oggetti_configurazioni = self._carica_configurazioni_oggetti()
    
    def _verifica_percorso(self, percorso, tipo_percorso):
        """Verifica se un percorso esiste e prova alternative se necessario"""
        if percorso.exists():
            logging.info(f"Percorso {tipo_percorso} trovato: {percorso.absolute()}")
            return percorso
        
        logging.warning(f"Percorso {tipo_percorso} non trovato: {percorso.absolute()}")
        
        # Prova percorsi alternativi
        alternative = [
            Path(os.path.join(os.getcwd(), str(percorso))),
            Path(os.path.join(os.getcwd(), "gioco_rpg", str(percorso))),
            Path(os.path.join(os.getcwd(), "data", tipo_percorso.lower()))
        ]
        
        # Aggiungi percorso alternativo specifico per gli oggetti
        if tipo_percorso.lower() == "oggetti":
            alternative.append(Path(os.path.join(os.getcwd(), "data", "items")))
            alternative.append(Path(os.path.join(os.getcwd(), "gioco_rpg", "data", "items")))
        
        for alt_path in alternative:
            logging.info(f"Tentativo percorso alternativo per {tipo_percorso}: {alt_path}")
            if alt_path.exists():
                logging.info(f"Percorso alternativo per {tipo_percorso} trovato: {alt_path}")
                return alt_path
        
        logging.error(f"Nessun percorso valido trovato per {tipo_percorso}. Verificare l'installazione.")
        return None
    
    def _carica_configurazioni_oggetti(self):
        """
        Carica le configurazioni degli oggetti interattivi dai file JSON.
        
        Returns:
            dict: Dizionario di configurazioni di oggetti (id -> config)
        """
        configurazioni = {}
        
        if not self.percorso_oggetti or not self.percorso_oggetti.exists():
            logging.warning(f"Directory oggetti non trovata: {self.percorso_oggetti}")
            return configurazioni
            
        try:
            for file_path in self.percorso_oggetti.glob("*.json"):
                logging.info(f"Caricamento configurazione oggetto da {file_path}")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Gestisci sia i formati di array che di oggetti
                    if isinstance(data, list):
                        # Formato array come in oggetti_interattivi.json
                        for i, config in enumerate(data):
                            if not isinstance(config, dict):
                                logging.error(f"Elemento non valido in {file_path}, indice {i}")
                                continue
                                
                            # Usa il nome come ID se non c'è un ID esplicito
                            oggetto_id = config.get('id') or config.get('nome')
                            if not oggetto_id:
                                logging.error(f"ID/nome oggetto mancante nella configurazione in {file_path}, indice {i}")
                                continue
                                
                            configurazioni[oggetto_id] = config
                            logging.info(f"Oggetto '{oggetto_id}' caricato con successo")
                    elif isinstance(data, dict):
                        # Formato dizionario con ID come chiavi
                        if 'taverna' in data or 'mercato' in data or 'cantina' in data:
                            # È un file di mappatura come mappe_oggetti.json, non di configurazione
                            nome_file = os.path.basename(file_path)
                            configurazioni[nome_file] = data
                            logging.info(f"Mappatura oggetti caricata da {nome_file}")
                        else:
                            # Formato dizionario normale
                            for oggetto_id, config in data.items():
                                if not isinstance(config, dict):
                                    logging.error(f"Configurazione non valida per l'oggetto {oggetto_id} in {file_path}")
                                    continue
                                    
                                configurazioni[oggetto_id] = config
                                logging.info(f"Oggetto '{oggetto_id}' caricato con successo")
                    else:
                        logging.error(f"Formato non valido per la configurazione oggetto in {file_path}")
                except Exception as e:
                    logging.error(f"Errore durante il caricamento della configurazione oggetto da {file_path}: {e}")
                    import traceback
                    logging.error(traceback.format_exc())
        except Exception as e:
            logging.error(f"Errore durante il caricamento delle configurazioni oggetti: {e}")
            import traceback
            logging.error(traceback.format_exc())
            
        logging.info(f"Caricate {len(configurazioni)} configurazioni oggetti")
        return configurazioni
    
    def ottieni_configurazione_oggetto(self, oggetto_id):
        """
        Ottiene la configurazione di un oggetto specifico.
        
        Args:
            oggetto_id (str): ID dell'oggetto
            
        Returns:
            dict: Configurazione dell'oggetto o {} se non trovato
        """
        return self.oggetti_configurazioni.get(oggetto_id, {})
    
    def crea_oggetto(self, oggetto_id):
        """
        Crea un nuovo oggetto interattivo a partire dalla sua configurazione.
        
        Args:
            oggetto_id (str): ID dell'oggetto da creare
            
        Returns:
            OggettoInterattivo: Nuova istanza dell'oggetto o None se non è possibile crearlo
        """
        config = self.ottieni_configurazione_oggetto(oggetto_id)
        if not config:
            logging.error(f"Configurazione non trovata per oggetto {oggetto_id}")
            return None
            
        try:
            tipo_oggetto = config.get('tipo', 'oggetto_interattivo')
            
            if tipo_oggetto == 'porta':
                oggetto = Porta.from_dict(config)
            elif tipo_oggetto == 'baule':
                oggetto = Baule.from_dict(config)
            elif tipo_oggetto == 'leva':
                oggetto = Leva.from_dict(config)
            elif tipo_oggetto == 'trappola':
                oggetto = Trappola.from_dict(config)
            else:
                oggetto = OggettoInterattivo.from_dict(config)
                
            return oggetto
        except Exception as e:
            logging.error(f"Errore durante la creazione dell'oggetto {oggetto_id}: {e}")
            return None
    
    def posiziona_oggetto_su_mappa(self, mappa, oggetto, x, y):
        """
        Posiziona un oggetto su una mappa.
        
        Args:
            mappa: Oggetto mappa
            oggetto: Oggetto interattivo da posizionare
            x, y: Coordinate in cui posizionare l'oggetto
            
        Returns:
            bool: True se il posizionamento è riuscito, False altrimenti
        """
        # Verifica che la posizione sia valida
        if not mappa.is_posizione_valida(x, y):
            logging.warning(f"Posizione non valida per oggetto {oggetto.nome}: ({x}, {y})")
            
            # Cerca una posizione valida nelle vicinanze
            mappa_dict = mappa.to_dict() if hasattr(mappa, 'to_dict') else {'griglia': mappa.griglia, 'larghezza': mappa.larghezza, 'altezza': mappa.altezza}
            nuova_pos = trova_posizione_valida(mappa_dict, x, y)
            
            if nuova_pos:
                logging.info(f"Posizione corretta per oggetto {oggetto.nome}: ({nuova_pos[0]}, {nuova_pos[1]})")
                x, y = nuova_pos
            else:
                logging.error(f"Impossibile trovare posizione valida per oggetto {oggetto.nome}")
                return False
        
        # Verifica se la posizione è già occupata da altri oggetti o NPC
        if (x, y) in mappa.oggetti:
            logging.warning(f"Posizione ({x}, {y}) già occupata dall'oggetto {mappa.oggetti[(x, y)].nome}")
            # Se stai tentando di posizionare una porta sulla stessa cella di un'altra porta, permetti questo caso speciale
            if isinstance(oggetto, Porta) and isinstance(mappa.oggetti[(x, y)], Porta):
                logging.info(f"Sostituisco porta esistente in ({x}, {y}) con {oggetto.nome}")
            else:
                # Cerca una posizione valida in un'area più ampia
                mappa_dict = mappa.to_dict() if hasattr(mappa, 'to_dict') else {'griglia': mappa.griglia, 'larghezza': mappa.larghezza, 'altezza': mappa.altezza}
                nuova_pos = trova_posizione_valida(mappa_dict, x, y, raggio=5)
                
                if nuova_pos:
                    logging.info(f"Posizione alternativa trovata per oggetto {oggetto.nome}: ({nuova_pos[0]}, {nuova_pos[1]})")
                    x, y = nuova_pos
                else:
                    logging.error(f"Impossibile trovare posizione alternativa per oggetto {oggetto.nome}")
                    return False
        
        if (x, y) in mappa.npg:
            logging.warning(f"Posizione ({x}, {y}) già occupata dall'NPC {mappa.npg[(x, y)].nome}")
            # Cerca una posizione valida in un'area più ampia
            mappa_dict = mappa.to_dict() if hasattr(mappa, 'to_dict') else {'griglia': mappa.griglia, 'larghezza': mappa.larghezza, 'altezza': mappa.altezza}
            nuova_pos = trova_posizione_valida(mappa_dict, x, y, raggio=5)
            
            if nuova_pos:
                logging.info(f"Posizione alternativa trovata per oggetto {oggetto.nome}: ({nuova_pos[0]}, {nuova_pos[1]})")
                x, y = nuova_pos
            else:
                logging.error(f"Impossibile trovare posizione alternativa per oggetto {oggetto.nome}")
                return False
        
        # Posiziona l'oggetto sulla mappa
        mappa.aggiungi_oggetto(oggetto, x, y)
        logging.info(f"Oggetto {oggetto.nome} posizionato in ({x}, {y}) su mappa {mappa.nome}")
        return True
    
    def carica_oggetti_su_mappa(self, mappa, nome_mappa):
        """
        Carica gli oggetti interattivi per una mappa dalle configurazioni JSON.
        
        Args:
            mappa (Mappa): Oggetto mappa in cui posizionare gli oggetti
            nome_mappa (str): Nome della mappa
            
        Returns:
            bool: True se l'operazione è riuscita, False in caso di errori gravi
        """
        try:
            # Verifica se esiste una mappatura oggetti<->mappa
            mappe_oggetti = None
            for config_key, config_data in self.oggetti_configurazioni.items():
                if isinstance(config_data, dict) and nome_mappa in config_data:
                    if config_key.endswith('mappe_oggetti.json'):
                        mappe_oggetti = config_data[nome_mappa]
                        break
            
            if not mappe_oggetti:
                # Prova a caricare da DataManager
                data_manager = get_data_manager()
                mappe_oggetti = data_manager.get_map_objects(nome_mappa)
            
            if not mappe_oggetti:
                logging.info(f"Nessuna configurazione di mappatura oggetti trovata per la mappa {nome_mappa}")
                return True  # Non è un errore, solo nessun oggetto da caricare
                
            logging.info(f"Trovati {len(mappe_oggetti)} oggetti interattivi da posizionare nella mappa {nome_mappa}")
            
            # Crea un set di posizioni già occupate nella mappa
            posizioni_occupate = set()
            for pos in mappa.oggetti.keys():
                posizioni_occupate.add(pos)
            for pos in mappa.npg.keys():
                posizioni_occupate.add(pos)
            
            # Mantieni un registro delle posizioni che stiamo per inserire
            # per evitare inserimenti duplicati da mappe_oggetti.json
            posizioni_da_inserire = set()
            oggetti_da_inserire = []
            
            # Filtra gli oggetti da posizionare, escludendo quelli in posizioni già occupate
            for mappatura in mappe_oggetti:
                nome_oggetto = mappatura.get('nome')
                posizione = mappatura.get('posizione')
                
                if not nome_oggetto or not posizione or len(posizione) != 2:
                    logging.error(f"Mappatura oggetto non valida: {mappatura}")
                    continue
                    
                x, y = posizione
                tuple_pos = (x, y)
                
                # Se la posizione è già occupata nella mappa o da un altro oggetto in mappe_oggetti.json,
                # saltiamo questo oggetto e loghiamo un avviso
                if tuple_pos in posizioni_occupate:
                    oggetto_esistente = mappa.oggetti.get(tuple_pos)
                    nome_esistente = oggetto_esistente.nome if oggetto_esistente else "oggetto sconosciuto"
                    logging.warning(
                        f"Oggetto '{nome_oggetto}' non posizionato: posizione ({x}, {y}) "
                        f"già occupata dall'oggetto {nome_esistente} nella mappa {nome_mappa}"
                    )
                    continue
                    
                # Se questa posizione è già in attesa di essere popolata da un altro oggetto
                # in mappe_oggetti.json, saltiamo questo oggetto ed evidenziamo il problema
                if tuple_pos in posizioni_da_inserire:
                    logging.warning(
                        f"Oggetto '{nome_oggetto}' non posizionato: posizione ({x}, {y}) "
                        f"già assegnata a un altro oggetto in mappe_oggetti.json per la mappa {nome_mappa}"
                    )
                    continue
                    
                # La posizione è libera, possiamo inserire l'oggetto
                oggetto_id = mappatura.get('id', nome_oggetto)
                oggetto = self.crea_oggetto(oggetto_id)
                
                if not oggetto:
                    # Se non riesce a trovare la configurazione, usa i valori di default
                    logging.warning(f"Configurazione non trovata per l'oggetto {nome_oggetto}, uso valori di default")
                    oggetto = OggettoInterattivo(
                        nome=nome_oggetto,
                        descrizione=f'Un {nome_oggetto}',
                        stato='normale',
                        token='O'
                    )
                
                # Registra la posizione come "da inserire" e aggiungi l'oggetto alla lista
                posizioni_da_inserire.add(tuple_pos)
                oggetti_da_inserire.append((oggetto, x, y))
            
            # Ora possiamo posizionare tutti gli oggetti filtrati
            for oggetto, x, y in oggetti_da_inserire:
                # Posiziona l'oggetto sulla mappa
                mappa.aggiungi_oggetto(oggetto, x, y)
                logging.info(f"Oggetto {oggetto.nome} posizionato in ({x}, {y}) su mappa {nome_mappa}")
            
            logging.info(f"Posizionati {len(oggetti_da_inserire)} oggetti su {len(mappe_oggetti)} definiti per la mappa {nome_mappa}")
            
            # Se ci sono oggetti che non sono stati posizionati a causa di collisioni,
            # lo segnaliamo per un'eventuale correzione manuale del file mappe_oggetti.json
            oggetti_non_posizionati = len(mappe_oggetti) - len(oggetti_da_inserire)
            if oggetti_non_posizionati > 0:
                logging.warning(
                    f"{oggetti_non_posizionati} oggetti non posizionati sulla mappa {nome_mappa} "
                    f"a causa di collisioni di posizione. Correggere il file mappe_oggetti.json."
                )
            
            return True
        except Exception as e:
            logging.error(f"Errore durante il caricamento degli oggetti interattivi per la mappa {nome_mappa}: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return False
    
    def salva_oggetti_mappa(self, mappa):
        """
        Salva le configurazioni degli oggetti presenti su una mappa.
        
        Args:
            mappa (Mappa): Oggetto mappa contenente gli oggetti
            
        Returns:
            bool: True se il salvataggio è riuscito, False altrimenti
        """
        try:
            # Ottieni il data manager
            data_manager = get_data_manager()
            
            # Prepara la lista di oggetti per questa mappa
            oggetti_lista = []
            for pos, oggetto in mappa.oggetti.items():
                try:
                    # Converti gli oggetti in dizionari serializzabili
                    if hasattr(oggetto, 'to_dict') and callable(getattr(oggetto, 'to_dict')):
                        oggetto_config = {
                            "nome": oggetto.nome,
                            "posizione": list(pos),  # Converti la tupla in lista per la serializzazione JSON
                            "id": getattr(oggetto, 'id', oggetto.nome)
                        }
                        oggetti_lista.append(oggetto_config)
                        
                        # Salva anche la configurazione completa dell'oggetto
                        if hasattr(oggetto, 'salva_su_json') and callable(getattr(oggetto, 'salva_su_json')):
                            oggetto.salva_su_json()
                    else:
                        # Fallback per oggetti che non hanno to_dict
                        oggetto_config = {
                            "nome": str(oggetto),
                            "posizione": list(pos),
                            "tipo": "oggetto_interattivo"
                        }
                        oggetti_lista.append(oggetto_config)
                        logging.warning(f"Oggetto {oggetto} non ha metodo to_dict(), salvato con informazioni di base")
                except Exception as e:
                    logging.error(f"Errore durante la serializzazione dell'oggetto a {pos}: {e}")
            
            # Salva le posizioni degli oggetti per questa mappa
            return data_manager.save_map_objects(mappa.nome, oggetti_lista)
        except Exception as e:
            logging.error(f"Errore durante il salvataggio degli oggetti per la mappa {mappa.nome}: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return False
    
    def salva_oggetti_interattivi_modificati(self, mappe):
        """
        Salva gli oggetti interattivi modificati nel sistema JSON.
        
        Args:
            mappe (dict): Dizionario delle mappe (nome_mappa -> oggetto Mappa)
            
        Returns:
            bool: True se il salvataggio è avvenuto con successo, False altrimenti
        """
        try:
            # Ottieni tutti gli oggetti interattivi da tutte le mappe
            oggetti_per_mappa = {}
            oggetti_interattivi = []
            
            for nome_mappa, mappa in mappe.items():
                oggetti_per_mappa[nome_mappa] = []
                
                for pos, oggetto in mappa.oggetti.items():
                    try:
                        # Verifica che l'oggetto sia effettivamente un OggettoInterattivo
                        if isinstance(oggetto, OggettoInterattivo):
                            # Aggiungi l'oggetto alla lista generale per il salvataggio
                            oggetti_interattivi.append(oggetto)
                            
                            # Aggiungi la posizione alla lista per questa mappa
                            oggetti_per_mappa[nome_mappa].append({
                                "nome": oggetto.nome,
                                "posizione": list(pos)  # Converti la tupla in lista per la serializzazione JSON
                            })
                        else:
                            # Gestisci altri tipi di oggetti
                            oggetti_per_mappa[nome_mappa].append({
                                "nome": str(oggetto) if hasattr(oggetto, '__str__') else "Oggetto sconosciuto",
                                "posizione": list(pos),
                                "tipo": "oggetto_generico"
                            })
                            logging.warning(f"Oggetto in ({pos[0]}, {pos[1]}) non è di tipo OggettoInterattivo")
                    except Exception as e:
                        logging.error(f"Errore durante la preparazione dell'oggetto in {pos} per il salvataggio: {e}")
            
            # Ottieni il data manager
            data_manager = get_data_manager()
            
            # Salva le posizioni degli oggetti per ogni mappa
            for nome_mappa, oggetti in oggetti_per_mappa.items():
                try:
                    data_manager.save_map_objects(nome_mappa, oggetti)
                    logging.info(f"Salvate posizioni di {len(oggetti)} oggetti per la mappa {nome_mappa}")
                except Exception as e:
                    logging.error(f"Errore nel salvataggio delle posizioni oggetti per mappa {nome_mappa}: {e}")
            
            # Salva gli oggetti interattivi stessi
            oggetti_salvati = 0
            oggetti_con_errori = 0
            
            for oggetto in oggetti_interattivi:
                try:
                    # Verifica che l'oggetto sia serializzabile in JSON
                    if hasattr(oggetto, 'to_json') and callable(getattr(oggetto, 'to_json')):
                        # Prova la serializzazione per verificare che funzioni
                        oggetto.to_json()
                        
                    # Salva l'oggetto utilizzando il suo metodo specifico se disponibile
                    if hasattr(oggetto, 'salva_su_json') and callable(getattr(oggetto, 'salva_su_json')):
                        oggetto.salva_su_json()
                        oggetti_salvati += 1
                    else:
                        # Fallback utilizzando il data manager direttamente
                        oggetto_dict = oggetto.to_dict() if hasattr(oggetto, 'to_dict') else {"nome": str(oggetto)}
                        data_manager.save_interactive_object(oggetto.nome, oggetto_dict)
                        oggetti_salvati += 1
                except Exception as e:
                    logging.error(f"Errore nel salvataggio dell'oggetto {oggetto.nome if hasattr(oggetto, 'nome') else str(oggetto)}: {e}")
                    oggetti_con_errori += 1
            
            if oggetti_con_errori > 0:
                logging.warning(f"Salvati {oggetti_salvati} oggetti con {oggetti_con_errori} errori")
            else:
                logging.info(f"Salvati con successo {oggetti_salvati} oggetti interattivi")
                
            return oggetti_con_errori == 0
        except Exception as e:
            import traceback
            logging.error(f"Errore durante il salvataggio degli oggetti interattivi: {e}")
            logging.error(traceback.format_exc())
            return False
    
    def convalida_posizioni_oggetti_mappa(self, nome_mappa, percorso_file=None):
        """
        Analizza un file mappe_oggetti.json per una mappa specifica e verifica eventuali 
        conflitti di posizionamento, sia interni al file stesso che con oggetti predefiniti
        nella mappa.
        
        Args:
            nome_mappa: Nome della mappa da convalidare
            percorso_file: Percorso del file mappe_oggetti.json (opzionale)
            
        Returns:
            tuple: (è_valido, problemi_rilevati, correzioni_suggerite)
        """
        problemi = []
        correzioni = []
        
        # Carica il file mappe_oggetti.json
        data_manager = get_data_manager()
        mappa_oggetti = data_manager.get_map_objects(nome_mappa)
        
        if not mappa_oggetti:
            return True, [], []  # Nessun oggetto definito, nessun problema
        
        # Carica la mappa (se disponibile)
        mappa_json = None
        try:
            mappa_json = data_manager.get_map_data(nome_mappa)
        except Exception as e:
            logging.warning(f"Impossibile caricare la mappa {nome_mappa}: {e}")
        
        # Raccogli le posizioni predefinite nella mappa
        posizioni_predefinite = set()
        if mappa_json and 'oggetti' in mappa_json:
            for pos_str, _ in mappa_json['oggetti'].items():
                # Converti da stringa "[x, y]" in posizione (x, y)
                try:
                    pos_list = eval(pos_str)
                    if isinstance(pos_list, list) and len(pos_list) == 2:
                        posizioni_predefinite.add(tuple(pos_list))
                except Exception as e:
                    logging.error(f"Errore nella lettura della posizione {pos_str}: {e}")
        
        # Verifica le posizioni degli oggetti in mappe_oggetti.json
        posizioni_occupate = set()
        
        for i, oggetto in enumerate(mappa_oggetti):
            nome = oggetto.get('nome', f'oggetto_{i}')
            posizione = oggetto.get('posizione')
            
            if not posizione or len(posizione) != 2:
                problemi.append(f"Oggetto '{nome}' ha una posizione non valida: {posizione}")
                continue
            
            pos_tuple = tuple(posizione)
            
            # Controlla se la posizione è già occupata da un oggetto predefinito
            if pos_tuple in posizioni_predefinite:
                problemi.append(f"Oggetto '{nome}' nella posizione {posizione} confligge con un oggetto predefinito nella mappa {nome_mappa}")
                
                # Suggerisci una correzione spostando l'oggetto in una posizione vicina
                nuova_pos = self._trova_posizione_libera(pos_tuple, posizioni_predefinite, posizioni_occupate)
                if nuova_pos:
                    correzioni.append({
                        "oggetto": nome,
                        "posizione_originale": posizione,
                        "posizione_suggerita": list(nuova_pos)
                    })
            
            # Controlla se la posizione è già occupata da un altro oggetto in mappe_oggetti.json
            elif pos_tuple in posizioni_occupate:
                altro_nome = next((ogg.get('nome') for ogg in mappa_oggetti 
                               if ogg.get('posizione') and tuple(ogg.get('posizione')) == pos_tuple 
                               and ogg.get('nome') != nome), "oggetto sconosciuto")
                
                problemi.append(f"Oggetto '{nome}' nella posizione {posizione} confligge con '{altro_nome}' nella stessa mappa")
                
                # Suggerisci una correzione spostando l'oggetto in una posizione vicina
                nuova_pos = self._trova_posizione_libera(pos_tuple, posizioni_predefinite, posizioni_occupate)
                if nuova_pos:
                    correzioni.append({
                        "oggetto": nome,
                        "posizione_originale": posizione,
                        "posizione_suggerita": list(nuova_pos)
                    })
            
            # La posizione è libera, la aggiungiamo a quelle occupate
            else:
                posizioni_occupate.add(pos_tuple)
        
        return len(problemi) == 0, problemi, correzioni

    def _trova_posizione_libera(self, posizione, posizioni_predefinite, posizioni_occupate, max_distanza=5):
        """
        Trova una posizione libera vicina a quella specificata.
        
        Args:
            posizione: Tupla (x, y) della posizione di partenza
            posizioni_predefinite: Set delle posizioni già occupate nella mappa
            posizioni_occupate: Set delle posizioni già assegnate ad altri oggetti
            max_distanza: Distanza massima dalla posizione originale
            
        Returns:
            tuple: Nuova posizione libera (x, y) o None se non trovata
        """
        x, y = posizione
        
        # Prova posizioni in spirale partendo dal centro
        for d in range(1, max_distanza + 1):
            for dx in range(-d, d+1):
                for dy in range(-d, d+1):
                    # Controlla solo i bordi del quadrato
                    if abs(dx) == d or abs(dy) == d:
                        new_pos = (x + dx, y + dy)
                        
                        # Se la posizione non è occupata in nessun modo, restituiscila
                        if (new_pos not in posizioni_predefinite and 
                            new_pos not in posizioni_occupate):
                            return new_pos
        
        return None 