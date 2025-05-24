import logging

logger = logging.getLogger(__name__)

class GenericLuogoMenuHandler:
    """
    Handler Menu generico per MappaState.
    Gestisce le scelte basandosi sulla configurazione caricata.
    """
    def __init__(self, mappa_state):
        self.mappa_state = mappa_state
        logger.info(f"GenericLuogoMenuHandler inizializzato per {self.mappa_state.nome_luogo}")

    def gestisci_scelta_menu_principale(self, gioco, scelta: str):
        logger.debug(f"GenericLuogoMenuHandler: gestisci_scelta_menu_principale (scelta: '{scelta}') per {self.mappa_state.nome_luogo}")

        azione_trovata = None
        # Trova l'azione corrispondente alla scelta nelle opzioni caricate
        if hasattr(self.mappa_state, 'opzioni_menu_principale_luogo'):
            for opzione_config in self.mappa_state.opzioni_menu_principale_luogo:
                if opzione_config.get("testo") == scelta:
                    azione_trovata = opzione_config.get("azione_id")
                    break

        if azione_trovata:
            logger.info(f"Azione '{azione_trovata}' selezionata per la scelta '{scelta}' in {self.mappa_state.nome_luogo}")
            # Qui MappaState dovrebbe avere un metodo per processare queste azioni_id
            if hasattr(self.mappa_state, 'process_azione_menu'):
                 self.mappa_state.process_azione_menu(gioco, azione_trovata, {"scelta_testo": scelta})
            else:
                 logger.warning(f"Metodo 'process_azione_menu' non trovato in MappaState per gestire l'azione '{azione_trovata}'")
        elif scelta.lower() == "indietro":
             if hasattr(self.mappa_state, '_cmd_torna_indietro'):
                 self.mappa_state._cmd_torna_indietro(gioco)
        else:
            logger.warning(f"Nessuna azione definita per la scelta '{scelta}' nel menu principale di {self.mappa_state.nome_luogo}")
            if gioco and hasattr(gioco, 'io'):
                gioco.io.mostra_messaggio("Azione non implementata.")

    # Aggiungere metodi per altri sottomenu se necessario 