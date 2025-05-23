"""
Manager per la gestione dei personaggi non giocanti (NPG).
"""

import logging
import json
import os
from pathlib import Path
from entities.npg import NPG
from util.data_manager import get_data_manager
from util.safe_loader import SafeLoader
from util.validators import valida_npc, trova_posizione_valida

logger = logging.getLogger(__name__)

# Importa World per il type hinting del contesto, se necessario
from typing import TYPE_CHECKING, Optional # Aggiunto Optional
if TYPE_CHECKING:
    from core.ecs.world import World # Assicurati che World sia importabile

class NPGManager:
    """
    Manager per la gestione degli NPC (Non Player Characters).
    Si occupa del caricamento, posizionamento e interazione con gli NPC.
    """
    def __init__(self, percorso_npc=None):
        """
        Inizializza il manager degli NPC.
        
        Args:
            percorso_npc: Percorso alla directory contenente le configurazioni degli NPC
        """
        self.percorso_npc = percorso_npc or Path("data/npc")
        if self.percorso_npc:
            self._verifica_percorso(self.percorso_npc, "NPC")
            
        self.npc_configurazioni = self._carica_configurazioni_npc()
        
        # Verifica la coerenza tra mappe_npg.json e npcs.json
        npc_mancanti = self.verifica_npc_mancanti()
        if npc_mancanti:
            logging.warning(f"Rilevati {len(npc_mancanti)} NPC utilizzati ma non definiti in npcs.json")
            logging.warning(f"È necessario definire in npcs.json gli NPC: {', '.join(npc_mancanti)}")
            # Non fermare l'esecuzione, ma avvisare in modo chiaro
    
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
        
        for alt_path in alternative:
            logging.info(f"Tentativo percorso alternativo per {tipo_percorso}: {alt_path}")
            if alt_path.exists():
                logging.info(f"Percorso alternativo per {tipo_percorso} trovato: {alt_path}")
                return alt_path
        
        logging.error(f"Nessun percorso valido trovato per {tipo_percorso}. Verificare l'installazione.")
        return None
    
    def _carica_configurazioni_npc(self):
        """
        Carica le configurazioni degli NPC dai file JSON.
        
        Returns:
            dict: Dizionario di configurazioni di NPC (id/nome -> config)
        """
        configurazioni = {}
        
        # Carica le configurazioni usando DataManager (metodo sicuro)
        try:
            data_manager = get_data_manager()
            npcs = data_manager.get_npc_data()
            
            # Log dettagliato sul caricamento
            if npcs:
                logging.info(f"DataManager ha caricato {len(npcs)} configurazioni NPC: {', '.join(npcs.keys())}")
            else:
                logging.warning("DataManager non ha trovato configurazioni NPC")
            
            # Adatta il formato: ogni NPC diventa una configurazione
            for nome, config in npcs.items():
                # Valida e correggi i dati dell'NPC
                config_corretta = valida_npc(config, nome)
                
                # Salva sia per ID che per nome per garantire doppio accesso
                configurazioni[nome] = config_corretta
                if "id" in config_corretta and config_corretta["id"] != nome:
                    configurazioni[config_corretta["id"]] = config_corretta
                    
            logging.info(f"Caricate {len(configurazioni)} configurazioni NPC")
            
        except Exception as e:
            logging.error(f"Errore durante il caricamento delle configurazioni NPC: {e}")
            import traceback
            logging.error(traceback.format_exc())
        
        # Se le configurazioni sono vuote, prova il metodo tradizionale
        if not configurazioni and self.percorso_npc and self.percorso_npc.exists():
            logging.warning("Tentativo di caricamento NPC da file JSON diretti")
            try:
                npcs_json_path = self.percorso_npc / "npcs.json"
                if npcs_json_path.exists():
                    logging.info(f"Caricamento configurazione NPC da {npcs_json_path}")
                    try:
                        # Usa SafeLoader per il caricamento
                        npcs = SafeLoader.safe_json_load(npcs_json_path, {})
                        
                        # Log dettagliato sul caricamento
                        if npcs:
                            logging.info(f"File npcs.json contiene {len(npcs)} configurazioni: {', '.join(npcs.keys())}")
                        else:
                            logging.warning("File npcs.json esiste ma è vuoto o non valido")
                        
                        # Adatta il formato per gli NPC
                        for nome, config in npcs.items():
                            config_corretta = valida_npc(config, nome)
                            configurazioni[nome] = config_corretta
                            
                            # Aggiungi anche per ID se diverso dal nome
                            if "id" in config_corretta and config_corretta["id"] != nome:
                                configurazioni[config_corretta["id"]] = config_corretta
                                
                        logging.info(f"Caricate {len(configurazioni)} configurazioni NPC da file npcs.json")
                    except Exception as e:
                        logging.error(f"Errore durante il caricamento della configurazione NPC da {npcs_json_path}: {e}")
                else:
                    logging.error(f"File npcs.json non trovato in {self.percorso_npc}. Crea questo file con le definizioni degli NPC necessari")
            except Exception as e:
                logging.error(f"Errore durante il caricamento delle configurazioni NPC: {e}")
        
        return configurazioni
    
    def ottieni_configurazione_npc(self, npc_id):
        """
        Ottiene la configurazione di un NPC specifico.
        
        Args:
            npc_id (str): ID o nome dell'NPC
            
        Returns:
            dict: Configurazione dell'NPC o {} se non trovato
        """
        config = self.npc_configurazioni.get(npc_id, None)
        
        # Se non trovato con ID, prova con il nome (potrebbe essere il nome dell'NPC)
        if config is None:
            # Cerca in tutte le configurazioni
            for conf in self.npc_configurazioni.values():
                if conf.get("nome") == npc_id:
                    config = conf
                    break
                    
        if config is None:
            # NPC non trovato, ricarica le configurazioni per assicurarsi che siano aggiornate
            logging.info(f"Ricarico le configurazioni NPC per cercare {npc_id}")
            self.npc_configurazioni = self._carica_configurazioni_npc()
            
            # Riprova la ricerca con le configurazioni aggiornate
            config = self.npc_configurazioni.get(npc_id, None)
            if config is None:
                for conf in self.npc_configurazioni.values():
                    if conf.get("nome") == npc_id:
                        config = conf
                        break
            
            # Se ancora non trovato, registra un errore critico
            if config is None:
                logging.error(f"Configurazione non trovata per NPC {npc_id}. È necessario definire questo NPC in npcs.json")
                # Crea una configurazione minima di default solo come misura d'emergenza
                config = {
                    "nome": npc_id,
                    "id": npc_id,
                    "token": npc_id[0].upper(),
                    "descrizione": f"Un personaggio chiamato {npc_id} (CONFIGURAZIONE MANCANTE - DA COMPLETARE)",
                    "livello": 1,
                    "hp": 10,
                    "hp_max": 10,
                    "forza": 10,
                    "destrezza": 10,
                    "costituzione": 10,
                    "intelligenza": 10,
                    "saggezza": 10,
                    "carisma": 10,
                    "inventario": [],
                    "oro": 0,
                    "amichevole": True
                }
                logging.warning(f"Creata configurazione temporanea per NPC {npc_id} - QUESTA È UNA MISURA D'EMERGENZA")
            
        return config
    
    def crea_npc(self, npc_id):
        """
        Crea un nuovo NPC a partire dalla sua configurazione.
        
        Args:
            npc_id (str): ID o nome dell'NPC da creare
            
        Returns:
            NPG: Nuova istanza dell'NPC o None se non è possibile crearlo
        """
        config = self.ottieni_configurazione_npc(npc_id)
        
        try:
            nome = config.get('nome', npc_id)
            token = config.get('token', 'N')
            dialoghi = config.get('dialoghi', {})
            
            npg = NPG(nome, token=token)
            
            # Imposta attributi extra se presenti
            for attr, value in config.items():
                if attr not in ['nome', 'token', 'id', 'dialoghi']:
                    setattr(npg, attr, value)
            
            # Imposta i dialoghi
            if hasattr(npg, 'imposta_dialoghi') and callable(getattr(npg, 'imposta_dialoghi')):
                npg.imposta_dialoghi(dialoghi)
                
            return npg
        except Exception as e:
            logging.error(f"Errore durante la creazione dell'NPC {npc_id}: {e}")
            # Fallback: crea un NPC minimale
            return NPG(npc_id, token=npc_id[0].upper())
    
    def posiziona_npc_su_mappa(self, mappa, npg, x, y):
        """
        Posiziona un NPC su una mappa.
        
        Args:
            mappa: Oggetto mappa
            npg: NPC da posizionare
            x, y: Coordinate in cui posizionare l'NPC
            
        Returns:
            bool: True se il posizionamento è riuscito, False altrimenti
        """
        # Verifica che la posizione sia valida e libera
        if not mappa.is_posizione_valida(x, y):
            logging.warning(f"Posizione non valida per NPC {npg.nome}: ({x}, {y})")
            
            # Cerca una posizione valida nelle vicinanze
            mappa_dict = mappa.to_dict() if hasattr(mappa, 'to_dict') else {'griglia': mappa.griglia, 'larghezza': mappa.larghezza, 'altezza': mappa.altezza}
            nuova_pos = trova_posizione_valida(mappa_dict, x, y)
            
            if nuova_pos:
                logging.info(f"Posizione corretta per NPC {npg.nome}: ({nuova_pos[0]}, {nuova_pos[1]})")
                x, y = nuova_pos
            else:
                logging.error(f"Impossibile trovare posizione valida per NPC {npg.nome}")
                return False
            
        if (x, y) in mappa.oggetti or (x, y) in mappa.npg:
            logging.warning(f"Posizione ({x}, {y}) già occupata, cerco posizione alternativa per NPC {npg.nome}")
            
            # Cerca una posizione valida in un'area più ampia
            mappa_dict = mappa.to_dict() if hasattr(mappa, 'to_dict') else {'griglia': mappa.griglia, 'larghezza': mappa.larghezza, 'altezza': mappa.altezza}
            nuova_pos = trova_posizione_valida(mappa_dict, x, y, raggio=5)
            
            if nuova_pos:
                logging.info(f"Posizione alternativa trovata per NPC {npg.nome}: ({nuova_pos[0]}, {nuova_pos[1]})")
                x, y = nuova_pos
            else:
                logging.error(f"Impossibile trovare posizione alternativa per NPC {npg.nome}")
                return False
            
        # Posiziona l'NPC
        mappa.aggiungi_npg(npg, x, y)
        logging.info(f"NPC {npg.nome} posizionato in ({x}, {y}) su mappa {mappa.nome}")
        return True
    
    def carica_npg_su_mappa(self, mappa, nome_mappa, world_context: Optional['World'] = None):
        """
        Carica gli NPC per una mappa dalle configurazioni JSON.
        
        Args:
            mappa (Mappa): Oggetto mappa in cui posizionare gli NPC
            nome_mappa (str): Nome della mappa
            world_context: Contest del mondo, se necessario
            
        Returns:
            bool: True se l'operazione è riuscita, False in caso di errori gravi
        """
        try:
            # Prima carica le configurazioni per questa mappa specifica
            npg_config = []
            
            # Carica da mappe_npg.json usando DataManager
            data_manager = get_data_manager()
            mappe_npg = data_manager.load_data("npc", "mappe_npg.json") or {}
            npg_config = mappe_npg.get(nome_mappa, [])
                
            if not npg_config:
                logging.info(f"Nessuna configurazione di NPG trovata per la mappa {nome_mappa}")
                return True  # Non è un errore, solo nessun NPC da caricare
                
            # Per ogni configurazione di NPG
            for config in npg_config:
                nome_npg = config.get("nome")
                posizione = config.get("posizione")
                
                if not nome_npg or not posizione or len(posizione) != 2:
                    logging.warning(f"Configurazione NPG non valida: {config}")
                    continue
                    
                # Crea l'NPG
                npc_id = config.get("id", nome_npg)
                npg = self.crea_npc(npc_id)
                
                # Posiziona l'NPG sulla mappa
                x, y = posizione
                self.posiziona_npc_su_mappa(mappa, npg, x, y)
                logger.debug(f"[CARICA_NPG_SU_MAPPA_DEBUG] Controllo world_context: {world_context is not None}, NPC: {npg.nome if hasattr(npg, 'nome') else 'N/A'}") # NUOVO LOG
                # Se abbiamo un contesto del mondo, aggiungiamo l'entità anche lì
                if world_context and hasattr(world_context, 'add_entity') and npg not in world_context.entities.values():
                    logger.debug(f"[CARICA_NPG_SU_MAPPA] Aggiungo NPC '{npg.nome}' (ID: {npg.id}) al world_context.")
                    world_context.add_entity(npg)
                elif world_context and hasattr(world_context, 'add_entity') and npg in world_context.entities.values():
                    logger.debug(f"[CARICA_NPG_SU_MAPPA] NPC '{npg.nome}' (ID: {npg.id}) già presente nel world_context. Non riaggiungo.")
            
            return True
        except Exception as e:
            logging.error(f"Errore durante il caricamento degli NPG per la mappa {nome_mappa}: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return False
    
    def salva_npg_mappa(self, mappa):
        """
        Salva le configurazioni degli NPC presenti su una mappa.
        
        Args:
            mappa (Mappa): Oggetto mappa contenente gli NPC
            
        Returns:
            bool: True se il salvataggio è riuscito, False altrimenti
        """
        try:
            # Ottieni il data manager
            data_manager = get_data_manager()
            
            # Carica il file mappe_npg.json esistente
            mappe_npg = data_manager.load_data("npc", "mappe_npg.json") or {}
            
            # Prepara la lista di NPC per questa mappa
            npg_lista = []
            for pos, npg in mappa.npg.items():
                npg_config = {
                    "nome": npg.nome,
                    "posizione": list(pos),  # Converti la tupla in lista per la serializzazione JSON
                    "id": getattr(npg, 'id', npg.nome)
                }
                npg_lista.append(npg_config)
            
            # Aggiorna la configurazione per questa mappa
            mappe_npg[mappa.nome] = npg_lista
            
            # Salva il file aggiornato
            return data_manager.save_data("npc", mappe_npg, "mappe_npg.json")
        except Exception as e:
            logging.error(f"Errore durante il salvataggio degli NPG per la mappa {mappa.nome}: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return False
    
    def verifica_npc_mancanti(self):
        """
        Verifica se ci sono NPC definiti in mappe_npg.json ma mancanti in npcs.json.
        
        Returns:
            list: Lista di nomi di NPC mancanti
        """
        # Ottieni il data manager
        data_manager = get_data_manager()
        
        # Carica mappe_npg.json per tutti gli NPC usati
        mappe_npg = data_manager.load_data("npc", "mappe_npg.json") or {}
        
        # Raccogli tutti gli NPC definiti in tutte le mappe
        npc_definiti = set()
        for mappa_nome, npg_lista in mappe_npg.items():
            for npg_config in npg_lista:
                # Usa l'id se presente, altrimenti il nome
                npc_id = npg_config.get("id", npg_config.get("nome"))
                if npc_id:
                    npc_definiti.add(npc_id)
                    
        # Ottieni tutti gli NPC configurati
        npcs_configurati = set(self.npc_configurazioni.keys())
        
        # Trova gli NPC mancanti
        npc_mancanti = npc_definiti - npcs_configurati
        
        # Se ci sono NPC mancanti, registra un avviso
        if npc_mancanti:
            npc_mancanti_lista = list(npc_mancanti)
            logging.warning(f"NPC mancanti in npcs.json: {', '.join(npc_mancanti_lista)}")
            return npc_mancanti_lista
            
        return []
        
    def carica_e_verifica_npg(self):
        """
        Ricarica tutte le configurazioni NPC e verifica eventuali incongruenze.
        
        Returns:
            dict: Rapporto sulla verifica con 'npc_mancanti', 'totale_npc_configurati'
        """
        # Ricarica le configurazioni
        self.npc_configurazioni = self._carica_configurazioni_npc()
        
        # Verifica NPC mancanti
        npc_mancanti = self.verifica_npc_mancanti()
        
        return {
            'npc_mancanti': npc_mancanti,
            'totale_npc_configurati': len(self.npc_configurazioni)
        } 