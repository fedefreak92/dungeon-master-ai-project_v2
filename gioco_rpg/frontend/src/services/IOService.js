import socketService from '../api/socketService';

/**
 * Servizio per implementare l'interfaccia IO nel frontend
 * Gestisce comunicazione con il backend e mantiene lo stato UI
 */
class IOService {
  constructor() {
    // Buffer per messaggi e stato UI
    this.messaggiBuffer = [];
    this.animazioniAttive = [];
    this.elementiInterattivi = {};
    this.uiAttiva = {
      dialoghi: [],
      menuContestuale: null,
      inventarioAperto: false,
      tooltip: null
    };
    this.mappaVisuale = {
      celle: [],
      entita: [],
      visibilita: []
    };
    
    // Coda eventi e handler
    this.eventHandlers = {};
    this.pendingEvents = [];
    this.renderEvents = [];
    this.listenersRegistered = false;
    
    // Registra per l'evento di connessione completata
    socketService.on('connect', () => {
      if (!this.listenersRegistered) {
        this.setupSocketListeners();
        this.listenersRegistered = true;
        console.log('Listener WebSocket registrati con successo');
      }
    });
  }
  
  /**
   * Configura i listener per eventi dal server
   */
  setupSocketListeners() {
    // Controlla se il socket è connesso
    if (!socketService.isConnected()) {
      console.warn('Socket non ancora inizializzato, saltando registrazione eventi WebSocket');
      return;
    }
    
    console.log('Registrazione listener per eventi WebSocket...');
    
    // Ascolta eventi di messaggio
    socketService.on('message', (data) => {
      if (data.tipo === 'narrativo') {
        this.mostraMessaggio(data.testo);
      } else if (data.tipo === 'sistema') {
        this.messaggioSistema(data.testo);
      } else if (data.tipo === 'errore') {
        this.messaggioErrore(data.testo);
      }
    });
    
    // Ascolta aggiornamenti mappa
    socketService.on('map_update', (data) => {
      this.aggiornaMappa(data);
    });
    
    // Ascolta eventi di dialogo
    socketService.on('show_dialog', (data) => {
      this.mostraDialogo(data.title, data.text, data.options);
    });
    
    socketService.on('close_dialog', (data) => {
      this.chiudiDialogo(data.id);
    });
    
    // Ascolta eventi di menu contestuale
    socketService.on('show_context_menu', (data) => {
      this.mostraMenuContestuale(data.position, data.options);
    });
    
    socketService.on('hide_context_menu', () => {
      this.nascondiMenuContestuale();
    });
    
    // Ascolta eventi di inventario
    socketService.on('show_inventory', (data) => {
      this.mostraInventario(data.items, data.capacity);
    });
    
    socketService.on('hide_inventory', () => {
      this.nascondiInventario();
    });
    
    // Ascolta eventi di elementi interattivi
    socketService.on('add_interactive_element', (data) => {
      this.aggiungiElementoInterattivo(data.id, data.type, data.position, data.sprite);
    });
    
    socketService.on('remove_interactive_element', (data) => {
      this.rimuoviElementoInterattivo(data.id);
    });
    
    socketService.on('update_element_state', (data) => {
      this.aggiornaStatoElemento(data.id, data.state);
    });
    
    // Ascolta eventi di animazione
    socketService.on('start_animation', (data) => {
      this.aggiungiAnimazione(data.type, data.target, data.duration, data.parameters);
    });
    
    socketService.on('animation_complete', (data) => {
      this.completaAnimazione(data.id);
    });
    
    // Ascolta eventi di tooltip
    socketService.on('show_tooltip', (data) => {
      this.mostraTooltip(data.text, data.position, data.duration);
    });
    
    socketService.on('hide_tooltip', () => {
      this.nascondiTooltip();
    });
  }
  
  /**
   * Inizializzazione manuale quando la connessione è pronta
   * @returns {boolean} true se i listener sono stati inizializzati, false altrimenti
   */
  initializeSocketListeners() {
    if (!this.listenersRegistered && socketService.isConnected()) {
      this.setupSocketListeners();
      this.listenersRegistered = true;
      return true;
    }
    return false;
  }
  
  /**
   * Mostra un messaggio narrativo
   * @param {string} testo - Testo del messaggio
   */
  mostraMessaggio(testo) {
    const messaggio = { tipo: 'narrativo', testo, timestamp: Date.now() };
    this.messaggiBuffer.push(messaggio);
    this.notificaAbbonati('messaggio', messaggio);
    return messaggio;
  }
  
  /**
   * Mostra un messaggio di sistema
   * @param {string} testo - Testo del messaggio
   */
  messaggioSistema(testo) {
    const messaggio = { tipo: 'sistema', testo, timestamp: Date.now() };
    this.messaggiBuffer.push(messaggio);
    this.notificaAbbonati('messaggio', messaggio);
    return messaggio;
  }
  
  /**
   * Mostra un messaggio di errore
   * @param {string} testo - Testo del messaggio
   */
  messaggioErrore(testo) {
    const messaggio = { tipo: 'errore', testo, timestamp: Date.now() };
    this.messaggiBuffer.push(messaggio);
    this.notificaAbbonati('messaggio', messaggio);
    return messaggio;
  }
  
  /**
   * Ottiene tutti i messaggi nel buffer
   * @returns {Array} - Array di messaggi
   */
  getMessaggi() {
    return [...this.messaggiBuffer];
  }
  
  /**
   * Pulisce il buffer dei messaggi
   */
  clearMessaggi() {
    this.messaggiBuffer = [];
    this.notificaAbbonati('clearMessaggi');
  }
  
  /**
   * Aggiorna lo stato visuale della mappa
   * @param {Object} datiMappa - Dati della mappa da visualizzare
   */
  aggiornaMappa(datiMappa) {
    this.mappaVisuale = datiMappa;
    this.notificaAbbonati('mappaAggiornata', datiMappa);
  }
  
  /**
   * Ottiene lo stato attuale della mappa
   * @returns {Object} - Stato della mappa
   */
  getMappa() {
    return { ...this.mappaVisuale };
  }
  
  /**
   * Mostra un dialogo con opzioni
   * @param {string} titolo - Titolo del dialogo
   * @param {string} testo - Testo del dialogo
   * @param {Array} opzioni - Array di opzioni disponibili
   * @returns {string} - ID del dialogo creato
   */
  mostraDialogo(titolo, testo, opzioni = []) {
    const id = `dialog-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const dialogo = {
      id,
      titolo,
      testo,
      opzioni: opzioni || []
    };
    
    this.uiAttiva.dialoghi.push(dialogo);
    this.notificaAbbonati('dialogoMostrato', dialogo);
    
    return id;
  }
  
  /**
   * Chiude un dialogo specifico o l'ultimo aperto
   * @param {string} idDialogo - ID del dialogo da chiudere (opzionale)
   */
  chiudiDialogo(idDialogo = null) {
    if (!this.uiAttiva.dialoghi.length) return;
    
    let dialogoChiuso;
    
    if (idDialogo) {
      // Trova e rimuovi il dialogo specifico
      const index = this.uiAttiva.dialoghi.findIndex(d => d.id === idDialogo);
      if (index !== -1) {
        dialogoChiuso = this.uiAttiva.dialoghi[index];
        this.uiAttiva.dialoghi.splice(index, 1);
      }
    } else {
      // Rimuovi l'ultimo dialogo
      dialogoChiuso = this.uiAttiva.dialoghi.pop();
    }
    
    if (dialogoChiuso) {
      this.notificaAbbonati('dialogoChiuso', dialogoChiuso);
    }
  }
  
  /**
   * Gestisce la selezione di un'opzione di dialogo
   * @param {string} idDialogo - ID del dialogo
   * @param {number} indiceOpzione - Indice dell'opzione selezionata
   */
  selezionaOpzioneDialogo(idDialogo, indiceOpzione) {
    const dialogo = this.uiAttiva.dialoghi.find(d => d.id === idDialogo);
    if (!dialogo || indiceOpzione < 0 || indiceOpzione >= dialogo.opzioni.length) return;
    
    const opzione = dialogo.opzioni[indiceOpzione];
    
    // Invia la selezione al server
    socketService.emit('player_input', {
      id_sessione: socketService.sessionId,
      tipo_input: 'dialog_choice',
      dati_input: {
        dialog_id: idDialogo,
        option_index: indiceOpzione,
        option_value: opzione
      }
    });
    
    // Chiudi il dialogo
    this.chiudiDialogo(idDialogo);
    
    return opzione;
  }
  
  /**
   * Mostra un menu contestuale in una posizione specifica
   * @param {Array} posizione - Array [x, y] con la posizione
   * @param {Array} opzioni - Array di opzioni disponibili
   */
  mostraMenuContestuale(posizione, opzioni) {
    this.uiAttiva.menuContestuale = {
      posizione,
      opzioni
    };
    
    this.notificaAbbonati('menuMostrato', this.uiAttiva.menuContestuale);
  }
  
  /**
   * Nasconde il menu contestuale attivo
   */
  nascondiMenuContestuale() {
    const menuPrecedente = this.uiAttiva.menuContestuale;
    this.uiAttiva.menuContestuale = null;
    
    if (menuPrecedente) {
      this.notificaAbbonati('menuNascosto', menuPrecedente);
    }
  }
  
  /**
   * Gestisce la selezione di un'opzione del menu
   * @param {number} indiceOpzione - Indice dell'opzione selezionata
   */
  selezionaOpzioneMenu(indiceOpzione) {
    const menu = this.uiAttiva.menuContestuale;
    if (!menu || indiceOpzione < 0 || indiceOpzione >= menu.opzioni.length) return;
    
    const opzione = menu.opzioni[indiceOpzione];
    
    // Invia la selezione al server
    socketService.emit('player_input', {
      id_sessione: socketService.sessionId,
      tipo_input: 'menu_choice',
      dati_input: {
        option_index: indiceOpzione,
        option_value: opzione
      }
    });
    
    // Nascondi il menu
    this.nascondiMenuContestuale();
    
    return opzione;
  }
  
  /**
   * Mostra l'inventario del giocatore
   * @param {Array} items - Array di oggetti nell'inventario
   * @param {number} capacity - Capacità massima dell'inventario
   */
  mostraInventario(items, capacity) {
    this.uiAttiva.inventarioAperto = true;
    this.uiAttiva.inventarioData = { items, capacity };
    
    this.notificaAbbonati('inventarioMostrato', { items, capacity });
  }
  
  /**
   * Nasconde l'inventario
   */
  nascondiInventario() {
    if (this.uiAttiva.inventarioAperto) {
      this.uiAttiva.inventarioAperto = false;
      this.notificaAbbonati('inventarioNascosto');
    }
  }
  
  /**
   * Aggiunge un elemento interattivo alla UI
   * @param {string} id - ID dell'elemento
   * @param {string} tipo - Tipo di elemento (npc, oggetto, ecc.)
   * @param {Array} posizione - Posizione [x, y] dell'elemento
   * @param {string} sprite - Path dello sprite
   */
  aggiungiElementoInterattivo(id, tipo, posizione, sprite) {
    this.elementiInterattivi[id] = {
      id,
      tipo,
      posizione,
      sprite,
      stato: 'normale'
    };
    
    this.notificaAbbonati('elementoAggiunto', this.elementiInterattivi[id]);
  }
  
  /**
   * Rimuove un elemento interattivo dalla UI
   * @param {string} id - ID dell'elemento da rimuovere
   */
  rimuoviElementoInterattivo(id) {
    if (this.elementiInterattivi[id]) {
      const elemento = this.elementiInterattivi[id];
      delete this.elementiInterattivi[id];
      
      this.notificaAbbonati('elementoRimosso', elemento);
    }
  }
  
  /**
   * Aggiorna lo stato di un elemento interattivo
   * @param {string} id - ID dell'elemento
   * @param {string} stato - Nuovo stato (normale, hover, selezionato)
   */
  aggiornaStatoElemento(id, stato) {
    if (this.elementiInterattivi[id]) {
      this.elementiInterattivi[id].stato = stato;
      this.notificaAbbonati('statoElementoAggiornato', this.elementiInterattivi[id]);
    }
  }
  
  /**
   * Ottiene tutti gli elementi interattivi attuali
   * @returns {Object} - Mappa di tutti gli elementi interattivi
   */
  getElementiInterattivi() {
    return { ...this.elementiInterattivi };
  }
  
  /**
   * Aggiunge un'animazione alla UI
   * @param {string} tipo - Tipo di animazione
   * @param {string} target - ID dell'elemento target
   * @param {number} durata - Durata in secondi
   * @param {Object} parametri - Parametri specifici dell'animazione
   * @returns {string} - ID dell'animazione creata
   */
  aggiungiAnimazione(tipo, target, durata, parametri = {}) {
    const id = `anim-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    const animazione = {
      id,
      tipo,
      target,
      durata,
      parametri,
      inizio: Date.now(),
      stato: 'attiva'
    };
    
    this.animazioniAttive.push(animazione);
    this.notificaAbbonati('animazioneAggiunta', animazione);
    
    // Se non è un'animazione infinita, programma il completamento
    if (durata && durata > 0) {
      setTimeout(() => {
        this.completaAnimazione(id);
      }, durata * 1000);
    }
    
    return id;
  }
  
  /**
   * Completa un'animazione
   * @param {string} id - ID dell'animazione da completare
   */
  completaAnimazione(id) {
    const index = this.animazioniAttive.findIndex(a => a.id === id);
    if (index !== -1) {
      const animazione = this.animazioniAttive[index];
      animazione.stato = 'completata';
      
      this.notificaAbbonati('animazioneCompletata', animazione);
      
      // Rimuovi l'animazione dalla lista delle attive
      this.animazioniAttive.splice(index, 1);
    }
  }
  
  /**
   * Mostra un tooltip
   * @param {string} testo - Testo del tooltip
   * @param {Array} posizione - Posizione [x, y] del tooltip
   * @param {number} durata - Durata in secondi (opzionale)
   * @returns {string} - ID del tooltip creato
   */
  mostraTooltip(testo, posizione, durata = null) {
    const id = `tooltip-${Date.now()}`;
    
    this.uiAttiva.tooltip = {
      id,
      testo,
      posizione,
      creato: Date.now(),
      durata
    };
    
    this.notificaAbbonati('tooltipMostrato', this.uiAttiva.tooltip);
    
    // Se ha una durata, programma la chiusura automatica
    if (durata) {
      setTimeout(() => {
        if (this.uiAttiva.tooltip && this.uiAttiva.tooltip.id === id) {
          this.nascondiTooltip();
        }
      }, durata * 1000);
    }
    
    return id;
  }
  
  /**
   * Nasconde il tooltip attivo
   */
  nascondiTooltip() {
    if (this.uiAttiva.tooltip) {
      const tooltip = this.uiAttiva.tooltip;
      this.uiAttiva.tooltip = null;
      
      this.notificaAbbonati('tooltipNascosto', tooltip);
    }
  }
  
  /**
   * Invia un evento di input al server
   * @param {string} tipoEvento - Tipo di evento (click, hover, key_press)
   * @param {string} target - ID dell'elemento target (opzionale)
   * @param {Object} datiEvento - Dati aggiuntivi dell'evento
   */
  inviaEventoInput(tipoEvento, target = null, datiEvento = {}) {
    // Gestione locale di alcuni eventi
    if (tipoEvento === 'click') {
      // Click su un elemento del menu contestuale
      if (this.uiAttiva.menuContestuale && datiEvento.indiceOpzione !== undefined) {
        return this.selezionaOpzioneMenu(datiEvento.indiceOpzione);
      }
      
      // Click su un'opzione di dialogo
      if (this.uiAttiva.dialoghi.length && datiEvento.idDialogo && datiEvento.indiceOpzione !== undefined) {
        return this.selezionaOpzioneDialogo(datiEvento.idDialogo, datiEvento.indiceOpzione);
      }
    }
    
    // Invia l'evento al server
    socketService.emit('player_input', {
      id_sessione: socketService.sessionId,
      tipo_input: tipoEvento,
      dati_input: {
        target,
        ...datiEvento
      }
    });
  }
  
  /**
   * Registra un handler per un tipo di evento
   * @param {string} tipoEvento - Tipo di evento
   * @param {Function} handler - Funzione handler
   * @param {string} id - ID opzionale dell'handler
   */
  on(tipoEvento, handler, id = null) {
    const handlerId = id || `handler-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    if (!this.eventHandlers[tipoEvento]) {
      this.eventHandlers[tipoEvento] = {};
    }
    
    this.eventHandlers[tipoEvento][handlerId] = handler;
    return handlerId;
  }
  
  /**
   * Rimuove un handler per un tipo di evento
   * @param {string} tipoEvento - Tipo di evento
   * @param {string} id - ID dell'handler da rimuovere
   */
  off(tipoEvento, id) {
    if (this.eventHandlers[tipoEvento] && this.eventHandlers[tipoEvento][id]) {
      delete this.eventHandlers[tipoEvento][id];
      
      // Pulisci l'oggetto se non ci sono più handler
      if (Object.keys(this.eventHandlers[tipoEvento]).length === 0) {
        delete this.eventHandlers[tipoEvento];
      }
      
      return true;
    }
    
    return false;
  }
  
  /**
   * Notifica tutti gli handler registrati per un tipo di evento
   * @param {string} tipoEvento - Tipo di evento
   * @param {*} dati - Dati dell'evento
   */
  notificaAbbonati(tipoEvento, dati = null) {
    if (this.eventHandlers[tipoEvento]) {
      Object.values(this.eventHandlers[tipoEvento]).forEach(handler => {
        try {
          handler(dati);
        } catch (error) {
          console.error(`Errore nell'handler per l'evento ${tipoEvento}:`, error);
        }
      });
    }
  }
  
  /**
   * Ottiene lo stato completo dell'interfaccia UI
   * @returns {Object} - Stato completo dell'interfaccia
   */
  getStatoUI() {
    return {
      messaggi: this.getMessaggi(),
      elementiInterattivi: this.getElementiInterattivi(),
      mappaVisuale: this.getMappa(),
      uiAttiva: { ...this.uiAttiva },
      animazioniAttive: [...this.animazioniAttive]
    };
  }
}

// Esporta un'istanza singleton del servizio
const ioService = new IOService();
export default ioService; 