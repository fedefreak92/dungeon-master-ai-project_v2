"""
Gestione dell'interfaccia utente per lo stato mappa.
Contiene le funzioni di visualizzazione e i componenti UI.
"""

def mostra_leggenda(mappa_state, gioco):
    """
    Mostra la leggenda della mappa usando un componente UI
    
    Args:
        mappa_state: Istanza di MappaState
        gioco: Oggetto Game
    """
    # Crea un elenco di elementi della leggenda
    elementi_leggenda = [
        "P = Giocatore",
        "N = NPC generico",
        "O = Oggetto generico",
        "D = Porta",
        "C = Baule",
        "L = Leva",
        "T = Trappola",
        "M = Mostro/Nemico",
        "# = Muro",
        ". = Spazio vuoto"
    ]
    
    # Mostra la leggenda in un pannello informativo
    gioco.io.mostra_info_panel("Legenda Mappa", elementi_leggenda)
    
    # Manteniamo anche il messaggio di testo come fallback 
    # per sistemi che non supportano il pannello informativo
    if not gioco.io.supporta_ui_avanzata():
        gioco.io.mostra_messaggio("\nLegenda:")
        for elemento in elementi_leggenda:
            gioco.io.mostra_messaggio(elemento)

def mostra_menu_principale(mappa_state, gioco):
    """
    Mostra il menu principale
    
    Args:
        mappa_state: Istanza di MappaState
        gioco: Oggetto Game
    """
    gioco.io.mostra_dialogo("Azioni", "Cosa vuoi fare?", [
        "Muoviti",
        "Interagisci con l'ambiente",
        "Mostra elementi nelle vicinanze",
        "Mostra/nascondi leggenda",
        "Torna indietro"
    ])
    mappa_state.menu_attivo = "principale"

def mostra_opzioni_movimento(mappa_state, gioco):
    """
    Mostra le opzioni di movimento tramite UI
    
    Args:
        mappa_state: Istanza di MappaState
        gioco: Oggetto Game
    """
    gioco.io.mostra_dialogo("Movimento", "Scegli una direzione:", [
        "Nord",
        "Sud",
        "Est",
        "Ovest",
        "Indietro"
    ])

def mostra_opzioni_interazione(mappa_state, gioco):
    """
    Mostra le opzioni di interazione tramite UI
    
    Args:
        mappa_state: Istanza di MappaState
        gioco: Oggetto Game
    """
    gioco.io.mostra_dialogo("Interazione", "Cosa vuoi fare?", [
        "Interagisci con un oggetto",
        "Parla con un personaggio",
        "Esamina l'area",
        "Indietro"
    ])

def toggle_leggenda(mappa_state, gioco):
    """
    Attiva/disattiva la visualizzazione della leggenda
    
    Args:
        mappa_state: Istanza di MappaState
        gioco: Oggetto Game
    """
    mappa_state.mostra_leggenda = not mappa_state.mostra_leggenda
    gioco.io.messaggio_sistema("Leggenda " + ("attivata" if mappa_state.mostra_leggenda else "disattivata"))
    mappa_state.ui_aggiornata = False  # Forza l'aggiornamento dell'UI

def mostra_elementi_vicini(mappa_state, gioco):
    """
    Mostra oggetti e NPC nelle vicinanze
    
    Args:
        mappa_state: Istanza di MappaState
        gioco: Oggetto Game
    """
    oggetti_vicini = gioco.giocatore.ottieni_oggetti_vicini(gioco.gestore_mappe)
    npg_vicini = gioco.giocatore.ottieni_npg_vicini(gioco.gestore_mappe)
    
    if not oggetti_vicini and not npg_vicini:
        gioco.io.mostra_messaggio("Non ci sono elementi nelle vicinanze.")
        return
        
    gioco.io.mostra_messaggio("\n=== ELEMENTI NELLE VICINANZE ===")
    
    if oggetti_vicini:
        gioco.io.mostra_messaggio("\nOggetti:")
        for pos, obj in oggetti_vicini.items():
            x, y = pos
            gioco.io.mostra_messaggio(f"- {obj.nome} [{obj.stato}] a ({x}, {y})")
    
    if npg_vicini:
        gioco.io.mostra_messaggio("\nPersonaggi:")
        for pos, npg in npg_vicini.items():
            x, y = pos
            gioco.io.mostra_messaggio(f"- {npg.nome} a ({x}, {y})") 