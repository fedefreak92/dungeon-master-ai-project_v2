def avanti(gioco=None):
    """
    Mostra un dialogo di pausa per l'utente
    
    Args:
        gioco: Istanza di gioco (opzionale)
    """
    if not gioco or not hasattr(gioco, 'io'):
        return
        
    # Mostra un dialogo con un pulsante per continuare
    gioco.io.mostra_dialogo("Continua", "Premi per continuare...", ["Continua"])
    
    # Nell'interfaccia grafica non è necessario richiedere input diretto
    # Il flusso continuerà quando l'utente interagirà con il dialogo

def mostra_statistiche_entita(entita, gioco=None):
    """
    Mostra le statistiche di un'entità
    
    Args:
        entita: L'entità di cui mostrare le statistiche
        gioco: Istanza di gioco (opzionale)
    """
    io = getattr(gioco, 'io', None)
    
    if not io:
        # Fallback solo per retrocompatibilità
        return
    
    # Intestazione
    io.mostra_messaggio(f"\n=== STATISTICHE DI {entita.nome.upper()} ===")
    
    # Statistiche principali
    io.mostra_messaggio(f"Nome: {entita.nome}")
    io.mostra_messaggio(f"HP: {entita.hp}/{entita.hp_max}")
    io.mostra_messaggio(f"FOR: {entita.forza_base} ({entita.modificatore_forza:+d})")
    io.mostra_messaggio(f"DES: {entita.destrezza_base} ({entita.modificatore_destrezza:+d})")
    io.mostra_messaggio(f"COS: {entita.costituzione_base} ({entita.modificatore_costituzione:+d})")
    io.mostra_messaggio(f"INT: {entita.intelligenza_base} ({entita.modificatore_intelligenza:+d})")
    io.mostra_messaggio(f"SAG: {entita.saggezza_base} ({entita.modificatore_saggezza:+d})")
    io.mostra_messaggio(f"CAR: {entita.carisma_base} ({entita.modificatore_carisma:+d})")
    io.mostra_messaggio(f"Difesa: {entita.difesa}")
    
    io.mostra_messaggio(f"Livello: {entita.livello}")
    
    io.mostra_messaggio(f"Oro: {entita.oro}")
    
    io.mostra_messaggio(f"Esperienza: {entita.esperienza}/{100 * entita.livello}")

def mostra_inventario(entita, gioco=None):
    """
    Mostra l'inventario di un'entità
    
    Args:
        entita: L'entità di cui mostrare l'inventario
        gioco: Istanza di gioco (opzionale)
    """
    io = getattr(gioco, 'io', None)
    
    if not io:
        # Fallback solo per retrocompatibilità
        return
    
    # Verifica che l'entità abbia un inventario
    if not hasattr(entita, 'inventario'):
        io.mostra_messaggio(f"{entita.nome} non ha un inventario.")
        return
    
    # Verifica che l'inventario non sia vuoto
    if not entita.inventario:
        io.mostra_messaggio(f"L'inventario di {entita.nome} è vuoto.")
        return
    
    # Intestazione
    io.mostra_messaggio(f"\n=== INVENTARIO DI {entita.nome.upper()} ===")
    
    # Mostra gli oggetti
    for i, item in enumerate(entita.inventario, 1):
        if isinstance(item, str):
            io.mostra_messaggio(f"{i}. {item}")
        elif hasattr(item, 'descrizione'):
            descrizione = f"{item.nome} - {item.descrizione}" if hasattr(item, 'descrizione') else item.nome
            io.mostra_messaggio(f"{i}. {descrizione}")
        else:
            io.mostra_messaggio(f"{i}. {str(item)}")
    
    # Mostra la quantità di oro
    io.mostra_messaggio(f"\nOro: {entita.oro}")
