import io from 'socket.io-client';

// Usa variabile di ambiente per l'URL API se disponibile, altrimenti usa il default
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// Opzioni ottimizzate per Socket.IO con strategia di connessione migliore
const SOCKET_OPTIONS = {
  transports: ['websocket', 'polling'],  // Preferisci WebSocket, fallback su polling
  reconnection: true,
  reconnectionAttempts: Infinity,    // Infiniti tentativi di riconnessione
  reconnectionDelay: 1000,           // 1 secondo iniziale
  reconnectionDelayMax: 5000,        // Max 5 secondi (ridotto)
  randomizationFactor: 0.5,          // Aggiunge casualità al backoff
  timeout: 20000,                    // Timeout di connessione a 20 secondi
  autoConnect: false,                // Controlliamo manualmente la connessione
  forceNew: false,                   // Non forzare una nuova connessione per permettere riutilizzo
  path: '/socket.io/',               // Path di default Socket.IO
  pingTimeout: 60000,                // Aumentato a 60 secondi per miglior stabilità
  pingInterval: 25000,               // Mantenuto a 25 secondi
  upgrade: true,                     // Abilita l'upgrade da polling a websocket
  rememberUpgrade: true,             // Ricorda se l'upgrade ha funzionato
  rejectUnauthorized: false,         // Utile per ambienti di sviluppo
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
        setTimeout(() => this._createNewConnection(sessionId, options, resolve, reject), 500);
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
    
    // Prepara le opzioni con parametri ottimizzati
    const socketOptions = {
      ...SOCKET_OPTIONS,
      ...options,
      query: {
        ...SOCKET_OPTIONS.query,
        sessionId: sessionId,
        stateVersion: this.stateVersion,
        reconnect: this.reconnecting ? 'true' : 'false'
      }
    };
    
    try {
      // Chiudiamo qualsiasi socket precedente
      if (this.socket) {
        this.socket.close();
        this.socket = null;
      }
      
      // Crea la connessione socket
      console.log('Creazione connessione WebSocket con opzioni:', socketOptions);
      this.socket = io(API_URL, socketOptions);

      // Configura monitor di latenza
      this._setupLatencyMonitor();
      
      // Configura gli handler di eventi prima che il socket si connetta
      this.setupEventHandlers(resolve, reject);

      // Aggiungi un timeout di sicurezza per garantire che la connessione non blocchi indefinitamente
      const connectionTimeout = setTimeout(() => {
        if (!this.connected) {
          console.error("Timeout durante il tentativo di connessione WebSocket");
          if (this.socket) {
            this.socket.close();
          }
          reject(new Error("Timeout durante il tentativo di connessione"));
        }
      }, socketOptions.timeout || 20000);

      // Avvia la connessione
      console.log('Avvio connessione socket...');
      this.socket.connect();
      
      // Callback aggiuntivo per gestire il successo della connessione
      this.socket.once('connect', () => {
        clearTimeout(connectionTimeout);
        // Il resto della gestione avverrà in setupEventHandlers
      });
      
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
   * Configura il monitor di latenza per il socket
   * @private
   */
  _setupLatencyMonitor() {
    // Ferma eventuali monitoraggi precedenti
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
    }
    
    // Imposta un intervallo per verificare la latenza
    this.pingInterval = setInterval(() => {
      if (this.socket && this.connected) {
        const startTime = Date.now();
        
        this.socket.emit('ping_test', {}, () => {
          const endTime = Date.now();
          this.latency = endTime - startTime;
          
          // Stampa la latenza solo in sviluppo
          if (process.env.NODE_ENV === 'development') {
            console.log(`Latenza WebSocket: ${this.latency}ms`);
          }
        });
      }
    }, 30000); // Verifica ogni 30 secondi
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
      
      // Implementa una strategia di backoff esponenziale
      if (this.connectionRetries < this.maxConnectionRetries) {
        this.connectionRetries++;
        const delay = Math.min(1000 * Math.pow(1.5, this.connectionRetries), 30000);
        console.log(`Tentativo di riconnessione ${this.connectionRetries}/${this.maxConnectionRetries} fra ${delay}ms...`);
        
        // Impostiamo un timer per il prossimo tentativo con backoff esponenziale
        this.reconnectTimer = setTimeout(() => {
          if (!this.connected && this.socket) {
            console.log('Tentativo di riconnessione...');
            this.socket.connect();
          }
        }, delay);
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
      
      // Avvia automaticamente la riconnessione per alcuni tipi di disconnessione
      if (reason === 'io server disconnect' || reason === 'io client disconnect') {
        // Disconnessione esplicita, non tentare la riconnessione
        console.log('Disconnessione esplicita, non tento la riconnessione');
      } else {
        // Per altri tipi di disconnessione (transport close, ping timeout), tenta la riconnessione
        console.log(`Disconnessione imprevista (${reason}), pianificazione riconnessione...`);
        this.reconnecting = true;
        
        // Imposta un piccolo ritardo prima di riconnettere
        setTimeout(() => {
          if (!this.connected && this.socket) {
            console.log('Tentativo di riconnessione dopo disconnessione imprevista...');
            this.socket.connect();
          }
        }, 1000);
      }
    });

    // Gestione errori generici
    this.socket.on('error', (err) => {
      console.error('Errore WebSocket:', err);
      this.packetStats.errors++;
    });
    
    // Gestione eventi di riconnessione
    this.socket.on('reconnect', (attemptNumber) => {
      console.log(`Socket riconnesso con successo dopo ${attemptNumber} tentativi`);
      this.reconnecting = false;
    });
    
    this.socket.on('reconnect_attempt', (attemptNumber) => {
      console.log(`Tentativo di riconnessione #${attemptNumber}`);
      // Verifica se abbiamo informazioni sullo stato per sincronizzare correttamente
      if (this.socket.io && this.socket.io.opts && this.socket.io.opts.query) {
        this.socket.io.opts.query.stateVersion = this.stateVersion;
        this.socket.io.opts.query.reconnect = 'true';
      }
    });
    
    this.socket.on('reconnect_error', (err) => {
      console.error('Errore durante la riconnessione:', err);
    });
    
    this.socket.on('reconnect_failed', () => {
      console.error('Riconnessione fallita dopo tutti i tentativi');
      this.reconnecting = false;
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