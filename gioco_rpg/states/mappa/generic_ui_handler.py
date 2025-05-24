import logging

logger = logging.getLogger(__name__)

class GenericLuogoUIHandler:
    """
    Handler UI generico per MappaState.
    Fornisce implementazioni di base o placeholder.
    """
    def __init__(self, mappa_state):
        self.mappa_state = mappa_state
        logger.info(f"GenericLuogoUIHandler inizializzato per {self.mappa_state.nome_luogo}")

    def aggiorna_renderer(self, gioco):
        logger.debug(f"GenericLuogoUIHandler: aggiorna_renderer chiamato per {self.mappa_state.nome_luogo}")
        
        if not (gioco and hasattr(gioco, 'io') and hasattr(gioco, 'asset_manager')):
            logger.error("aggiorna_renderer: Contesto di gioco, IO o AssetManager mancante.")
            return

        renderer = gioco.io.get_renderer()
        asset_manager = gioco.asset_manager

        if not renderer:
            logger.error("aggiorna_renderer: Renderer non disponibile.")
            return

        renderer.clear()
        renderer.draw_title(self.mappa_state.nome_luogo.replace('_', ' ').title())
        renderer.draw_text(self.mappa_state.descrizione_luogo, 10, 50) # Posizione esempio

        if self.mappa_state.griglia and hasattr(renderer, 'draw_grid'):
            renderer.draw_grid(self.mappa_state.griglia)

        # Disegna gli Oggetti Interattivi
        for nome_oggetto, oggetto in self.mappa_state.oggetti_interattivi.items():
            if hasattr(oggetto, 'x') and hasattr(oggetto, 'y') and hasattr(oggetto, 'sprite'):
                sprite_id = oggetto.sprite
                sprite_path = asset_manager.get_sprite_path(sprite_id)
                if sprite_path:
                    if hasattr(renderer, 'draw_sprite'):
                        renderer.draw_sprite(sprite_path, oggetto.x, oggetto.y)
                    elif hasattr(renderer, 'draw_object'): # Manteniamo per compatibilità se draw_object usa l'oggetto intero
                        renderer.draw_object(oggetto) 
                    else:
                        logger.warn(f"Renderer non ha draw_sprite o draw_object per OggettoInterattivo '{nome_oggetto}'")
                else:
                    logger.warn(f"Impossibile trovare sprite_path per OggettoInterattivo '{nome_oggetto}' con sprite_id '{sprite_id}'")
            else:
                logger.warn(f"OggettoInterattivo '{nome_oggetto}' non ha x, y, o sprite (ID).")

        # Disegna gli NPG
        for nome_npg, npg in self.mappa_state.npg_presenti.items():
            if hasattr(npg, 'x') and hasattr(npg, 'y') and hasattr(npg, 'sprite'):
                sprite_id = npg.sprite
                sprite_path = asset_manager.get_sprite_path(sprite_id)
                if sprite_path:
                    if hasattr(renderer, 'draw_sprite'):
                        renderer.draw_sprite(sprite_path, npg.x, npg.y)
                    elif hasattr(renderer, 'draw_npc'):
                        renderer.draw_npc(npg)
                    else:
                        logger.warn(f"Renderer non ha draw_sprite o draw_npc per NPG '{nome_npg}'")
                else:
                    logger.warn(f"Impossibile trovare sprite_path per NPG '{nome_npg}' con sprite_id '{sprite_id}'")
            else:
                logger.warn(f"NPG '{nome_npg}' non ha x, y, o sprite (ID).")

        # Disegna il Giocatore
        if hasattr(gioco, 'giocatore') and gioco.giocatore:
            giocatore = gioco.giocatore
            if hasattr(giocatore, 'x') and hasattr(giocatore, 'y') and hasattr(giocatore, 'sprite'):
                if giocatore.mappa_corrente == self.mappa_state.nome_luogo:
                    sprite_id = giocatore.sprite
                    sprite_path = asset_manager.get_sprite_path(sprite_id)
                    if sprite_path:
                        if hasattr(renderer, 'draw_sprite'):
                            renderer.draw_sprite(sprite_path, giocatore.x, giocatore.y)
                        elif hasattr(renderer, 'draw_player'):
                            renderer.draw_player(giocatore)
                        else:
                            logger.warn("Renderer non ha draw_sprite o draw_player per Giocatore.")
                    else:
                        logger.warn(f"Impossibile trovare sprite_path per Giocatore con sprite_id '{sprite_id}'")
                else:
                    logger.debug(f"Giocatore non sulla mappa corrente ({giocatore.mappa_corrente} vs {self.mappa_state.nome_luogo}), non disegnato da questo handler.")
            else:
                logger.warn("Giocatore non ha x, y, o sprite (ID).")
        else:
            logger.warn("gioco.giocatore non trovato o nullo.")
        
        renderer.update()

    def mostra_messaggio_luogo(self, gioco, messaggio: str):
         logger.debug(f"GenericLuogoUIHandler: mostra_messaggio_luogo chiamato per {self.mappa_state.nome_luogo}")
         if gioco and hasattr(gioco, 'io'):
             gioco.io.mostra_messaggio(messaggio)

    def mostra_opzioni_principali(self, gioco):
        logger.debug(f"GenericLuogoUIHandler: mostra_opzioni_principali chiamato per {self.mappa_state.nome_luogo}")
        # Mostra le opzioni caricate da MappaState
        if gioco and hasattr(gioco, 'io') and hasattr(self.mappa_state, 'opzioni_menu_principale_luogo'):
             opzioni_testo = [op.get("testo", "Azione Sconosciuta") for op in self.mappa_state.opzioni_menu_principale_luogo]
             if not opzioni_testo:
                 opzioni_testo = ["Nessuna azione disponibile", "Indietro"] # Fallback
             # Usa mostra_menu o un metodo simile per mostrare le opzioni
             gioco.io.mostra_menu(
                 f"Cosa vuoi fare in {self.mappa_state.nome_luogo.replace('_', ' ').title()}?",
                 opzioni_testo, # Qui si passano solo le stringhe per un menu base
                 id_menu=f"menu_{self.mappa_state.nome_luogo}_principale"
             ) 