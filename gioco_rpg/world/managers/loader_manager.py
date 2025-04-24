"""
Manager per il caricamento e salvataggio delle mappe da/su file JSON.
"""

import json
import logging
import os
import sys
from pathlib import Path
from world.mappa import Mappa

# Definizione del logger
logger = logging.getLogger(__name__)

class LoaderManager:
    """
    Classe responsabile del caricamento e salvataggio delle mappe da e verso file.
    """
    def __init__(self, percorso_base=None):
        """
        Inizializza il caricatore di mappe.
        
        Args:
            percorso_base: Percorso base dove cercare i file delle mappe
        """
        # Utilizziamo un percorso assoluto determinato a partire dalla directory corrente
        if percorso_base:
            self.percorso_base = Path(percorso_base)
        else:
            # Ottieni il percorso corrente e assicurati di puntare a gioco_rpg/data/mappe
            base_dir = Path(os.getcwd())
            
            # Log dettagliato della directory di lavoro e della struttura del progetto
            logger.info(f"Directory di lavoro attuale: {base_dir}")
            logger.info(f"Contenuto directory corrente: {os.listdir(base_dir)}")
            
            # Percorsi da controllare per le mappe
            possibili_percorsi = [
                base_dir / "gioco_rpg" / "data" / "mappe",
                base_dir / "data" / "mappe",
                Path(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "mappe")),
                Path("gioco_rpg/data/mappe"),
                Path("data/mappe")
            ]
            
            # Verifica ciascun percorso e utilizza il primo valido
            percorso_valido = None
            for percorso in possibili_percorsi:
                logger.info(f"Verifica percorso: {percorso.absolute()}")
                try:
                    if percorso.exists():
                        percorso_valido = percorso
                        logger.info(f"Trovato percorso valido: {percorso.absolute()}")
                        logger.info(f"Contenuto: {list(percorso.glob('*.json'))}")
                        break
                except Exception as e:
                    logger.warning(f"Errore nel controllare percorso {percorso}: {e}")
            
            if percorso_valido:
                self.percorso_base = percorso_valido
            else:
                # Se non troviamo nessun percorso valido, utilizziamo un percorso di default
                logger.warning("Nessun percorso valido trovato, uso percorso predefinito")
                self.percorso_base = base_dir / "gioco_rpg" / "data" / "mappe"
                # Crea la directory se non esiste
                self.percorso_base.mkdir(parents=True, exist_ok=True)
                
        logger.info(f"LoaderManager inizializzato con percorso base: {self.percorso_base.absolute()}")
        logger.info(f"Il percorso esiste: {self.percorso_base.exists()}")
        if self.percorso_base.exists():
            logger.info(f"Contenuto directory mappe: {list(self.percorso_base.glob('*.json'))}")
        
    def carica_mappa(self, nome_file):
        """
        Carica una mappa da un file JSON.
        
        Args:
            nome_file: Nome del file JSON (senza percorso)
            
        Returns:
            Mappa: L'oggetto mappa caricato
        """
        # Percorsi possibili dove cercare la mappa specifica
        percorsi_da_controllare = [
            self.percorso_base / nome_file,
            Path(os.path.join(os.getcwd(), "data", "mappe", nome_file)),
            Path(os.path.join(os.getcwd(), "gioco_rpg", "data", "mappe", nome_file)),
            Path("gioco_rpg/data/mappe") / nome_file,
            Path("data/mappe") / nome_file,
            # Aggiungi percorso assoluto come ultimo tentativo
            Path(os.path.abspath(os.path.join("gioco_rpg", "data", "mappe", nome_file)))
        ]
        
        # Rimuovi duplicati
        percorsi_unici = []
        for p in percorsi_da_controllare:
            if p not in percorsi_unici:
                percorsi_unici.append(p)
        
        # Log tutti i percorsi che stiamo controllando
        logger.info(f"Cercando mappa '{nome_file}' in percorsi multipli")
        
        # Controlla ogni percorso
        for percorso_completo in percorsi_unici:
            logger.info(f"Tentativo di caricare mappa da: {percorso_completo.absolute()}")
            
            if percorso_completo.exists():
                try:
                    with open(percorso_completo, 'r', encoding='utf-8') as f:
                        dati_mappa = json.load(f)
                        
                    mappa = Mappa.from_dict(dati_mappa)
                    logger.info(f"Mappa '{mappa.nome}' caricata con successo da {percorso_completo}")
                    
                    # Aggiorna il percorso base per usi futuri
                    self.percorso_base = percorso_completo.parent
                    
                    return mappa
                except Exception as e:
                    logger.error(f"Errore nel caricamento della mappa {nome_file} da {percorso_completo}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    continue  # Prova il prossimo percorso
        
        # Se arriviamo qui, non abbiamo trovato il file in nessun percorso
        error_msg = f"File mappa '{nome_file}' non trovato in nessuno dei percorsi controllati"
        logger.error(error_msg)
        logger.error(f"Percorsi controllati: {', '.join(str(p.absolute()) for p in percorsi_unici)}")
        raise FileNotFoundError(error_msg)
            
    def salva_mappa(self, mappa, nome_file=None):
        """
        Salva una mappa su un file JSON.
        
        Args:
            mappa: Oggetto mappa da salvare
            nome_file: Nome del file (se None, usa il nome della mappa)
            
        Returns:
            bool: True se il salvataggio è riuscito
        """
        nome_file = nome_file or f"{mappa.nome}.json"
        percorso_completo = self.percorso_base / nome_file
        
        # Assicurati che la directory esista
        logger.info(f"Tentativo di creare directory: {percorso_completo.parent}")
        percorso_completo.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(percorso_completo, 'w', encoding='utf-8') as f:
                json.dump(mappa.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"Mappa '{mappa.nome}' salvata con successo in {percorso_completo}")
            return True
        except Exception as e:
            logger.error(f"Errore nel salvataggio della mappa {nome_file}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
            
    def elenca_mappe_disponibili(self):
        """
        Elenca tutte le mappe disponibili nella directory.
        
        Returns:
            list: Lista di nomi di file delle mappe disponibili
        """
        # Percorsi possibili dove cercare le mappe
        percorsi_da_controllare = [
            self.percorso_base,
            Path(os.path.join(os.getcwd(), "data", "mappe")),
            Path(os.path.join(os.getcwd(), "gioco_rpg", "data", "mappe")),
            Path("gioco_rpg/data/mappe"),
            Path("data/mappe"),
            # Aggiungi percorso assoluto come ultimo tentativo
            Path(os.path.abspath(os.path.join("gioco_rpg", "data", "mappe")))
        ]
        
        # Rimuovi duplicati e filtra percorsi non esistenti
        percorsi_unici = []
        for p in percorsi_da_controllare:
            if p not in percorsi_unici:
                percorsi_unici.append(p)
        
        # Log dello stato attuale
        logger.info(f"Ricerca mappe in {len(percorsi_unici)} percorsi...")
        
        # Lista per raccogliere tutte le mappe trovate
        mappe_trovate = []
        
        # Controlla ogni percorso e raccogli tutte le mappe
        for percorso in percorsi_unici:
            try:
                logger.info(f"Controllo mappe in: {percorso.absolute()}")
                if percorso.exists():
                    files = list(percorso.glob("*.json"))
                    if files:
                        # Se troviamo mappe, aggiorna il percorso base per usi futuri
                        self.percorso_base = percorso
                        mappe = [f.name for f in files]
                        logger.info(f"Mappe trovate in {percorso}: {mappe}")
                        # Aggiungi alla lista complessiva
                        for mappa in mappe:
                            if mappa not in mappe_trovate:
                                mappe_trovate.append(mappa)
                    else:
                        logger.warning(f"Nessun file JSON trovato in {percorso}")
            except Exception as e:
                logger.error(f"Errore nel controllare percorso {percorso}: {e}")
        
        # Se abbiamo trovato mappe, restituiscile
        if mappe_trovate:
            logger.info(f"Totale mappe trovate: {len(mappe_trovate)}")
            return mappe_trovate
        
        # Se arriviamo qui, non abbiamo trovato mappe in nessun percorso
        logger.error(f"Nessuna mappa trovata in nessuno dei percorsi controllati")
        logger.error(f"Percorsi controllati: {', '.join(str(p.absolute()) for p in percorsi_unici)}")
        return []
        
    def _verifica_percorso(self, percorso, tipo_percorso):
        """Verifica se un percorso esiste e prova alternative se necessario"""
        if percorso.exists():
            logger.info(f"Percorso {tipo_percorso} trovato: {percorso.absolute()}")
            return percorso
        
        logger.warning(f"Percorso {tipo_percorso} non trovato: {percorso.absolute()}")
        
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
            logger.info(f"Tentativo percorso alternativo per {tipo_percorso}: {alt_path}")
            if alt_path.exists():
                logger.info(f"Percorso alternativo per {tipo_percorso} trovato: {alt_path}")
                return alt_path
        
        logger.error(f"Nessun percorso valido trovato per {tipo_percorso}. Verificare l'installazione.")
        return None 