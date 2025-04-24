import io from 'socket.io-client';

const API_URL = 'http://localhost:5000';

// Opzioni avanzate per Socket.IO con strategia di fallback
const SOCKET_OPTIONS = {
  transports: ['websocket', 'polling'],  // Fallback a polling se WebSocket fallisce
  reconnection: true,
  reconnectionAttempts: Infinity,  // Non limita i tentativi
  reconnectionDelay: 1000,
  reconnectionDelayMax: 30000,
  timeout: 20000,
  autoConnect: false,
  forceNew: true,  // Forza una nuova connessione
  path: '/socket.io/', 
  query: {}
};

/**
 * Classe di servizio per gestire le comunicazioni WebSocket
 */
class SocketService {
  constructor() {
    this.socket = null;
    this.connected = false;
    this.listeners = {};
    this.pendingListeners = {};
    this.sessionId = null;
    this.reconnecting = false;
    this.connectionRetries = 0;
    this.maxConnectionRetries = 5;
    this.pingInterval = null;
    this.lastPingTime = null;
    this.latency = null;
    this.disconnectionTime = null;
    this.pendingRequests = new Map();
    this.requestTimeout = 10000; // 10 secondi di timeout
    this.packetStats = {
      sent: 0,
      received: 0,
      errors: 0,
      timeout: 0
    };
    
    // Stato del gioco e sincronizzazione
    this.stateVersion = 0;
    this.lastFullStateTime = 0;
    this.fullState = null;
    this.pendingChanges = [];
    this.disconnectionDuration = 0;
    this.needsFullSync = false;
    
    // Pulizia del socket al caricamento della pagina
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => {
        this.disconnect();
      });
    }
  }

  /**
   * Inizializza la connessione WebSocket
   * @param {string} sessionId - ID della sessione di gioco
   * @param {Object} options - Opzioni aggiuntive per la connessione
   * @returns {Promise} - Promise che si risolve quando la connessione è stabilita
   */
  connect(sessionId, options = {}) {
    return new Promise((resolve, reject) => {
      // Se siamo già connessi con lo stesso sessionId, risolviamo subito
      if (this.isConnected() && this.sessionId === sessionId) {
        console.log(`Socket già connesso con sessione ${sessionId}, riutilizzo connessione esistente`);
        return resolve(this.socket);
      }
      
      // Se c'è un socket esistente ma con sessionId diverso o non connesso, disconnetti
      if (this.socket) {
        console.log(`Disconnect socket esistente prima di nuova connessione (connesso: ${this.connected})`);
        this.disconnect();
        
        // Piccolo ritardo per garantire la disconnessione completa
        setTimeout(() => this._createNewConnection(sessionId, options, resolve, reject), 300);
      } else {
        // Nessun socket esistente, crea una nuova connessione direttamente
        this._createNewConnection(sessionId, options, resolve, reject);
      }
    });
  }
  
  /**
   * Metodo interno per creare una nuova connessione
   * @private
   */
  _createNewConnection(sessionId, options, resolve, reject) {
    // Salva l'ID sessione per riconnessioni
    this.sessionId = sessionId;
    
    // Prepara le opzioni con fallback a polling
    const socketOptions = {
      ...SOCKET_OPTIONS,
      ...options,
      query: {
        ...SOCKET_OPTIONS.query,
        sessionId: sessionId,
        stateVersion: this.stateVersion
      }
    };
    
    try {
      // Crea la connessione socket
      console.log('Creazione connessione WebSocket con opzioni:', socketOptions);
      this.socket = io(API_URL, socketOptions);

      // Configura gli handler di eventi
      this.setupEventHandlers(resolve, reject);

      // Avvia la connessione
      console.log('Avvio connessione socket...');
      this.socket.connect();
      
      // Avvia monitoraggio performance
      this.startMonitoring();
    } catch (err) {
      console.error('Errore durante creazione socket:', err);
      this.socket = null;
      this.connected = false;
      reject(new Error(`Errore durante creazione socket: ${err.message}`));
    }
  }
  
  /**
   * Configura gli handler per gli eventi del socket
   * @private
   */
  setupEventHandlers(resolve, reject) {
    // Gestione eventi di connessione
    this.socket.on('connect', () => {
      console.log(`WebSocket connesso con ID: ${this.socket.id}`);
      this.connected = true;
      this.connectionRetries = 0;
      
      // Calcola durata disconnessione per decidere se richiede sync completo
      if (this.disconnectionTime) {
        this.disconnectionDuration = Date.now() - this.disconnectionTime;
        // Se disconnesso per più di 30 secondi, richiedi stato completo
        this.needsFullSync = this.disconnectionDuration > 30000;
        this.disconnectionTime = null;
      }
      
      // Registra tutti i listener in attesa
      this.registerPendingListeners();
      
      // Entra nella sessione di gioco con info di sincronizzazione
      this.socket.emit('join_game', { 
        id_sessione: this.sessionId,
        state_version: this.stateVersion,
        need_full_sync: this.needsFullSync,
        last_sync_time: this.lastFullStateTime
      });
      this.packetStats.sent++;
      
      resolve(this.socket);
    });

    this.socket.on('connect_error', (err) => {
      console.error('Errore connessione WebSocket:', err.message, err);
      this.packetStats.errors++;
      
      if (this.connectionRetries < this.maxConnectionRetries) {
        this.connectionRetries++;
        console.log(`Tentativo di riconnessione ${this.connectionRetries}/${this.maxConnectionRetries}...`);
      } else {
        console.error('Numero massimo di tentativi raggiunto');
        this.connected = false;
        this.reconnecting = false;
        this.cleanupPendingRequests('Connessione fallita dopo più tentativi');
        reject(new Error(`Impossibile connettersi: ${err.message}`));
      }
    });

    this.socket.on('disconnect', (reason) => {
      console.log(`WebSocket disconnesso: ${reason}`);
      this.connected = false;
      this.disconnectionTime = Date.now();
      
      // Pulisci tutte le richieste in sospeso
      this.cleanupPendingRequests('Socket disconnesso: ' + reason);
    });

    // Gestione errori generici
    this.socket.on('error', (err) => {
      console.error('Errore WebSocket:', err);
      this.packetStats.errors++;
    });
    
    // Intercetta tutti i messaggi ricevuti per statistiche
    this.socket.onAny((eventName) => {
      this.packetStats.received++;
    });
    
    // Gestire risposte specifiche per i request_id
    this.socket.on('response', (response) => {
      const requestId = response.requestId;
      if (requestId && this.pendingRequests.has(requestId)) {
        const { resolve, timeoutId } = this.pendingRequests.get(requestId);
        clearTimeout(timeoutId);
        this.pendingRequests.delete(requestId);
        resolve(response.data);
      }
    });
    
    // Ascolta gli eventi di sincronizzazione stato
    this.socket.on('game_state_full', (data) => {
      this.applyFullState(data);
    });
    
    this.socket.on('game_state_delta', (data) => {
      if (!this.applyStateDelta(data)) {
        // Delta non applicabile, richiedi lo stato completo
        this.requestFullState();
      }
    });
  }

  /**
   * Avvia il monitoraggio delle prestazioni della connessione
   * @private
   */
  startMonitoring() {
    // Implementa un semplice ping per misurare la latenza
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
    }
    
    this.pingInterval = setInterval(() => {
      if (this.isConnected()) {
        this.lastPingTime = Date.now();
        this.emit('ping', { timestamp: this.lastPingTime });
      }
    }, 30000); // Ping ogni 30 secondi
    
    // Handler per il pong dal server
    this.on('pong', (data) => {
      if (this.lastPingTime) {
        this.latency = Date.now() - this.lastPingTime;
        this.lastPingTime = null;
        console.debug(`Latenza WebSocket: ${this.latency}ms`);
      }
    });
  }

  /**
   * Disconnette il socket
   */
  disconnect() {
    if (this.socket) {
      console.log('Chiusura connessione WebSocket');
      
      // Pulisci intervallo di ping
      if (this.pingInterval) {
        clearInterval(this.pingInterval);
        this.pingInterval = null;
      }
      
      // Pulisci tutte le richieste in sospeso
      this.cleanupPendingRequests('Disconnessione manuale');
      
      // Conserva una copia del socket per evitare problemi di riferimento
      const tempSocket = this.socket;
      
      // Aggiorna lo stato prima di disconnettere
      this.socket = null;
      this.connected = false;
      
      // Disconnetti solo se il socket è attivo e non in fase di connessione
      if (tempSocket.connected) {
        try {
          // Disconnetti in modo sicuro
          tempSocket.disconnect();
        } catch (e) {
          console.error('Errore durante disconnessione:', e);
        }
      } else {
        console.log('Socket già disconnesso o in fase di connessione, salto la disconnessione esplicita');
      }
      
      // Pulisci lo stato
      this.listeners = {};
      this.sessionId = null;
    }
  }

  /**
   * Invia un evento al server
   * @param {string} eventName - Nome dell'evento
   * @param {Object} data - Dati da inviare
   * @returns {boolean} - true se l'invio è riuscito, false altrimenti
   */
  emit(eventName, data) {
    if (!this.isConnected()) {
      console.warn(`Tentativo di inviare evento '${eventName}' ma socket non connesso`);
      return false;
    }
    
    try {
      this.socket.emit(eventName, data);
      this.packetStats.sent++;
      return true;
    } catch (err) {
      console.error(`Errore nell'emissione dell'evento ${eventName}:`, err);
      this.packetStats.errors++;
      return false;
    }
  }
  
  /**
   * Invia un evento al server e attende una risposta
   * @param {string} eventName - Nome dell'evento
   * @param {Object} data - Dati da inviare
   * @param {number} timeout - Timeout in millisecondi (opzionale)
   * @returns {Promise} - Promise che si risolve con la risposta del server
   */
  emitWithAck(eventName, data, timeout = this.requestTimeout) {
    return new Promise((resolve, reject) => {
      if (!this.isConnected()) {
        reject(new Error('Socket non connesso'));
        return;
      }
      
      const requestId = this.generateRequestId();
      const timeoutId = setTimeout(() => {
        if (this.pendingRequests.has(requestId)) {
          this.pendingRequests.delete(requestId);
          this.packetStats.timeout++;
          reject(new Error(`Timeout della richiesta: ${eventName}`));
        }
      }, timeout);
      
      this.pendingRequests.set(requestId, {
        resolve,
        reject,
        timeoutId,
        eventName,
        timestamp: Date.now()
      });
      
      const payloadWithId = {
        ...data,
        requestId,
        stateVersion: this.stateVersion
      };
      
      // Associa un handler per la risposta specifica
      const responseEventName = `${eventName}_response_${requestId}`;
      const onceCallback = (response) => {
        if (this.pendingRequests.has(requestId)) {
          clearTimeout(timeoutId);
          this.pendingRequests.delete(requestId);
          resolve(response);
        }
      };
      
      this.socket.once(responseEventName, onceCallback);
      
      // Invia la richiesta
      this.socket.emit(eventName, payloadWithId);
      this.packetStats.sent++;
    });
  }

  /**
   * Registra un listener per un evento
   * @param {string} eventName - Nome dell'evento
   * @param {Function} callback - Funzione da chiamare quando l'evento viene ricevuto
   * @returns {boolean} - true se il listener è stato registrato, false altrimenti
   */
  on(eventName, callback) {
    // Verifica se il callback è una funzione
    if (typeof callback !== 'function') {
      console.error(`Tentativo di registrare un callback non valido per l'evento '${eventName}'`);
      return false;
    }

    // Se il socket non è inizializzato, salva il listener per registrarlo più tardi
    if (!this.socket) {
      console.log(`Socket non ancora inizializzato, salvo listener per '${eventName}' per registrazione differita`);
      
      // Inizializza la struttura dei listener pendenti se necessario
      if (!this.pendingListeners) {
        this.pendingListeners = {};
      }
      
      if (!this.pendingListeners[eventName]) {
        this.pendingListeners[eventName] = [];
      }
      
      // Aggiungi il callback alla lista di attesa se non è già presente
      const isAlreadyRegistered = this.pendingListeners[eventName].some(
        existingCallback => existingCallback === callback
      );
      
      if (!isAlreadyRegistered) {
        console.log(`Aggiunto listener pendente per '${eventName}'`);
        this.pendingListeners[eventName].push(callback);
      }
      
      return false;
    }
    
    // Crea un wrapper sicuro per il callback
    const safeCallback = (...args) => {
      try {
        callback(...args);
      } catch (err) {
        console.error(`Errore nell'esecuzione del callback per '${eventName}':`, err);
      }
    };
    
    // Registra il callback nel sistema interno
    if (!this.listeners[eventName]) {
      this.listeners[eventName] = [];
    }
    
    // Controlla se il callback è già stato registrato
    const existingListener = this.listeners[eventName].find(
      item => item.original === callback
    );
    
    // Se il callback è già registrato, non duplicarlo
    if (existingListener) {
      console.log(`Listener per '${eventName}' già registrato, ignoro duplicato`);
      return true;
    }
    
    // Salva la referenza per poterla rimuovere in seguito
    this.listeners[eventName].push({ original: callback, wrapped: safeCallback });
    
    // Registra effettivamente l'evento
    this.socket.on(eventName, safeCallback);
    
    return true;
  }

  /**
   * Rimuove un listener per un evento
   * @param {string} eventName - Nome dell'evento
   * @param {Function} callback - Funzione da rimuovere
   * @returns {boolean} - true se il listener è stato rimosso, false altrimenti
   */
  off(eventName, callback) {
    if (!this.socket || !this.listeners[eventName]) {
      return false;
    }
    
    // Trova l'indice del callback nella lista
    const index = this.listeners[eventName].findIndex(item => item.original === callback);
    
    if (index !== -1) {
      // Rimuovi il callback dal socket
      this.socket.off(eventName, this.listeners[eventName][index].wrapped);
      
      // Rimuovi il callback dalla lista
      this.listeners[eventName].splice(index, 1);
      
      return true;
    }
    
    return false;
  }

  /**
   * Verifica se il socket è connesso
   * @returns {boolean} - true se il socket è connesso, false altrimenti
   */
  isConnected() {
    return this.socket && this.connected && this.socket.connected;
  }

  /**
   * Ottiene la latenza corrente
   * @returns {number|null} - Latenza in millisecondi, o null se non disponibile
   */
  getLatency() {
    return this.latency;
  }

  /**
   * Ottiene le statistiche di comunicazione
   * @returns {Object} - Statistiche di comunicazione
   */
  getStats() {
    return {
      ...this.packetStats,
      pendingRequests: this.pendingRequests.size,
      connected: this.isConnected(),
      latency: this.latency,
      disconnectionTime: this.disconnectionTime,
      stateVersion: this.stateVersion
    };
  }
  
  /**
   * Richiede le entità dalla sessione di gioco
   * @returns {Promise} - Promise che si risolve con le entità
   */
  async requestEntities() {
    return this.emitWithAck('get_entities', { 
      id_sessione: this.sessionId 
    });
  }
  
  /**
   * Richiede un aggiornamento della mappa
   * @param {string} mapId - ID della mappa (opzionale)
   * @returns {Promise} - Promise che si risolve con i dati della mappa
   */
  async requestMapUpdate(mapId = null) {
    return this.emitWithAck('get_map_data', { 
      id_sessione: this.sessionId,
      id_mappa: mapId 
    });
  }
  
  /**
   * Richiede lo stato del gioco
   * @returns {Promise} - Promise che si risolve con lo stato del gioco
   */
  async requestGameState() {
    return this.emitWithAck('get_game_state', { 
      id_sessione: this.sessionId 
    });
  }
  
  /**
   * Richiede lo stato completo del gioco al server
   * Usato quando si verifica un errore di sincronizzazione
   */
  requestFullState() {
    console.log('Richiesta sincronizzazione completa dello stato');
    this.emit('request_full_state', { 
      id_sessione: this.sessionId,
      current_version: this.stateVersion
    });
  }
  
  /**
   * Applica un aggiornamento incrementale dello stato
   * @param {Object} delta - Oggetto contenente le modifiche e il numero di versione
   * @returns {boolean} - true se l'applicazione è riuscita, false altrimenti
   */
  applyStateDelta(delta) {
    if (!delta || typeof delta.version !== 'number' || !Array.isArray(delta.changes)) {
      console.error('Formato delta stato non valido');
      return false;
    }
    
    // Verifica che la versione sia consecutiva
    if (delta.version !== this.stateVersion + 1) {
      console.warn(`Versione delta non consecutiva: attesa ${this.stateVersion + 1}, ricevuta ${delta.version}`);
      return false;
    }
    
    try {
      // Applica ogni modifica al fullState
      delta.changes.forEach(change => {
        this.applyChange(change);
      });
      
      // Aggiorna la versione
      this.stateVersion = delta.version;
      
      // Notifica gli abbonati del cambiamento
      this.notifyStateChange(delta.changes);
      
      return true;
    } catch (error) {
      console.error('Errore nell\'applicazione delle modifiche incrementali:', error);
      return false;
    }
  }
  
  /**
   * Applica una singola modifica allo stato
   * @param {Object} change - Oggetto che descrive la modifica
   * @private
   */
  applyChange(change) {
    if (!this.fullState || !change.path || !change.operation) {
      return;
    }
    
    const path = change.path.split('.');
    let target = this.fullState;
    
    // Naviga all'oggetto target (l'ultimo elemento del path)
    for (let i = 0; i < path.length - 1; i++) {
      const key = path[i];
      
      // Se il percorso include un indice array (item[3])
      if (key.includes('[') && key.includes(']')) {
        const arrName = key.substring(0, key.indexOf('['));
        const index = parseInt(key.substring(key.indexOf('[') + 1, key.indexOf(']')));
        
        if (!target[arrName] || !Array.isArray(target[arrName])) {
          console.error(`Percorso array '${arrName}' non valido per la modifica`);
          return;
        }
        
        if (index >= target[arrName].length) {
          console.error(`Indice array fuori dai limiti: ${index}`);
          return;
        }
        
        target = target[arrName][index];
      } else {
        // Percorso oggetto normale
        if (target[key] === undefined) {
          // Crea l'oggetto se non esiste
          target[key] = {};
        }
        target = target[key];
      }
      
      if (target === null || typeof target !== 'object') {
        console.error(`Impossibile navigare oltre ${key} nel path`);
        return;
      }
    }
    
    // Estrai la chiave finale
    const finalKey = path[path.length - 1];
    
    // Esegui l'operazione
    switch (change.operation) {
      case 'set':
        target[finalKey] = change.value;
        break;
      case 'delete':
        delete target[finalKey];
        break;
      case 'increment':
        if (typeof target[finalKey] === 'number') {
          target[finalKey] += change.value || 1;
        }
        break;
      case 'push':
        if (Array.isArray(target[finalKey])) {
          target[finalKey].push(change.value);
        }
        break;
      case 'splice':
        if (Array.isArray(target[finalKey]) && Array.isArray(change.args)) {
          target[finalKey].splice(...change.args);
        }
        break;
      default:
        console.warn(`Operazione non supportata: ${change.operation}`);
    }
  }
  
  /**
   * Applica uno stato completo ricevuto dal server
   * @param {Object} state - Stato completo del gioco
   */
  applyFullState(state) {
    if (!state || typeof state.version !== 'number') {
      console.error('Stato completo non valido');
      return;
    }
    
    this.fullState = state.data;
    this.stateVersion = state.version;
    this.lastFullStateTime = Date.now();
    this.needsFullSync = false;
    
    // Notifica gli abbonati del cambiamento completo
    this.notifyFullStateChange();
    
    console.log(`Stato completo applicato, versione: ${this.stateVersion}`);
  }
  
  /**
   * Notifica ai listener che lo stato è cambiato
   * @private
   */
  notifyStateChange(changes) {
    // Questo è un punto di estensione dove potremmo notificare
    // componenti React tramite un sistema di eventi o simili
  }
  
  /**
   * Notifica ai listener che lo stato completo è cambiato
   * @private
   */
  notifyFullStateChange() {
    // Questo è un punto di estensione dove potremmo notificare
    // componenti React tramite un sistema di eventi o simili
  }
  
  /**
   * Genera un ID univoco per le richieste
   * @returns {string} - ID univoco
   * @private
   */
  generateRequestId() {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  
  /**
   * Pulisce tutte le richieste in sospeso
   * @param {string} reason - Motivo della pulizia
   * @private
   */
  cleanupPendingRequests(reason) {
    if (this.pendingRequests.size > 0) {
      console.warn(`Pulizia di ${this.pendingRequests.size} richieste in sospeso: ${reason}`);
      
      this.pendingRequests.forEach(({ reject, timeoutId }, requestId) => {
        clearTimeout(timeoutId);
        reject(new Error(`Richiesta annullata: ${reason}`));
      });
      
      this.pendingRequests.clear();
    }
  }

  /**
   * Registra tutti i listener in attesa
   * @private
   */
  registerPendingListeners() {
    if (!this.socket) {
      console.warn('Impossibile registrare i listener pendenti: socket non inizializzato');
      return;
    }
    
    if (!this.pendingListeners) {
      return;
    }
    
    console.log('Registrazione listener pendenti...');
    
    for (const [eventName, callbacks] of Object.entries(this.pendingListeners)) {
      if (!callbacks || !Array.isArray(callbacks) || callbacks.length === 0) {
        continue;
      }
      
      console.log(`Registrazione di ${callbacks.length} listener pendenti per evento '${eventName}'`);
      
      for (const callback of callbacks) {
        if (typeof callback !== 'function') {
          console.warn(`Callback non valido trovato per '${eventName}'`);
          continue;
        }
        
        // Crea un wrapper sicuro per il callback
        const safeCallback = (...args) => {
          try {
            callback(...args);
          } catch (err) {
            console.error(`Errore nell'esecuzione del callback per '${eventName}':`, err);
          }
        };
        
        // Registra nell'array interno
        if (!this.listeners[eventName]) {
          this.listeners[eventName] = [];
        }
        
        // Aggiungi alla collezione interna
        this.listeners[eventName].push({ original: callback, wrapped: safeCallback });
        
        // Registra sul socket
        this.socket.on(eventName, safeCallback);
      }
      
      // Pulisci i listener già registrati
      this.pendingListeners[eventName] = [];
    }
    
    // Reimposta la collezione pendingListeners
    this.pendingListeners = {};
  }

  /**
   * Tenta una riconnessione rapida utilizzando il sessionId memorizzato
   * @returns {Promise} - Promise che si risolve quando la riconnessione è stabilita
   */
  reconnect() {
    return new Promise((resolve, reject) => {
      // Verifica se abbiamo un ID sessione memorizzato
      if (!this.sessionId) {
        return reject(new Error('Nessun ID sessione disponibile per la riconnessione'));
      }
      
      console.log(`Tentativo di riconnessione rapida per la sessione ${this.sessionId}...`);
      
      if (this.socket) {
        // Pulizia socket esistente se presente
        this.disconnect();
        
        // Piccolo ritardo per garantire la disconnessione completa
        setTimeout(() => this._attemptReconnect(resolve, reject), 500);
      } else {
        this._attemptReconnect(resolve, reject);
      }
    });
  }
  
  /**
   * Metodo interno per tentare una riconnessione
   * @private
   */
  _attemptReconnect(resolve, reject) {
    try {
      // Ricrea il socket con le stesse opzioni di prima
      const socketOptions = {
        ...SOCKET_OPTIONS,
        forceNew: true,
        reconnection: true,
        query: {
          ...SOCKET_OPTIONS.query,
          sessionId: this.sessionId,
          stateVersion: this.stateVersion,
          isReconnect: true
        }
      };
      
      console.log('Tentativo di riconnessione con opzioni:', socketOptions);
      this.socket = io(API_URL, socketOptions);
      
      // Configura callback per connessione
      this.socket.on('connect', () => {
        console.log(`WebSocket riconnesso con ID: ${this.socket.id}`);
        this.connected = true;
        this.connectionRetries = 0;
        
        // Invia direttamente un evento di tentativo riconnessione
        this.socket.emit('reconnect_attempt', { 
          id_sessione: this.sessionId,
          state_version: this.stateVersion,
          reconnect_time: Date.now()
        });
        
        // Attendi la risposta del server
        const timeoutId = setTimeout(() => {
          this.socket.off('reconnect_success');
          this.socket.off('reconnect_pending');
          reject(new Error('Timeout durante la riconnessione rapida'));
        }, 5000);
        
        // Handler per riconnessione rapida riuscita
        this.socket.once('reconnect_success', (data) => {
          clearTimeout(timeoutId);
          console.log('Riconnessione rapida completata con successo:', data);
          
          // Ripristina i listener pendenti
          this.registerPendingListeners();
          
          // Risolvi la promise
          resolve(this.socket);
        });
        
        // Handler per riconnessione lenta
        this.socket.once('reconnect_pending', (data) => {
          clearTimeout(timeoutId);
          console.log('Riconnessione rapida non disponibile, utilizzo procedura standard:', data);
          
          // Ripristina i listener pendenti
          this.registerPendingListeners();
          
          // Entra nella sessione di gioco con info di sincronizzazione
          this.socket.emit('join_game', { 
            id_sessione: this.sessionId,
            state_version: this.stateVersion,
            need_full_sync: true,
            last_sync_time: this.lastFullStateTime
          });
          
          resolve(this.socket);
        });
      });
      
      // Configura callback per errori
      this.socket.on('connect_error', (err) => {
        console.error('Errore riconnessione WebSocket:', err.message, err);
        this.packetStats.errors++;
        reject(new Error(`Errore durante la riconnessione: ${err.message}`));
      });
      
      // Avvia la connessione
      this.socket.connect();
      
    } catch (err) {
      console.error('Errore durante tentativo di riconnessione:', err);
      reject(new Error(`Errore durante tentativo di riconnessione: ${err.message}`));
    }
  }
}

// Esporta l'istanza Singleton
const socketService = new SocketService();
export default socketService; 