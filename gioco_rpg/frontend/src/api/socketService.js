import { io } from 'socket.io-client';

// URL del server fisso per evitare cambiamenti durante le riconnessioni
const SERVER_URL = "http://localhost:5000";

/**
 * Classe di servizio per gestire le comunicazioni Socket.IO
 * Implementato come singleton per garantire una sola istanza in tutta l'applicazione
 */
class SocketService {
  constructor() {
    this.socket = null;
    this.connected = false;
    this.listeners = new Map();
    this.pendingRequests = new Map();
    this.sessionId = null;
    this.connecting = false;
    this.connectionAttempts = 0;
    this.socketReady = false;
    
    // URL del server WebSocket - usa la costante globale
    this.serverUrl = SERVER_URL;  // URL esplicito invece di dedurlo dinamicamente
    
    console.log(`SocketService: utilizzo URL esplicito ${this.serverUrl} per la connessione WebSocket`);
    
    // Statistiche per debug
    this.stats = {
      sent: 0,
      received: 0,
      errors: 0,
      reconnects: 0
    };
    
    // Cleanup al reload della pagina
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => {
        this.disconnect();
      });
    }
    
    console.log('SocketService: singleton inizializzato');
  }

  /**
   * Inizializza la connessione Socket.IO
   * @param {string} sessionId - ID della sessione di gioco
   * @returns {Promise} Promise che si risolve quando la connessione è stabilita
   */
  connect(sessionId = null) {
    return new Promise((resolve, reject) => {
      // Non creare multiple connessioni
      if (this.connecting) {
        console.log('SocketService: connessione già in corso, in attesa...');
        return reject(new Error('Connessione già in corso'));
      }
      
      // Se già connesso e con lo stesso sessionId, riusa la connessione
      if (this.socket && this.socket.connected && sessionId === this.sessionId) {
        console.log(`SocketService: già connesso (sessionId: ${this.sessionId})`);
        
        // Imposta esplicitamente socketReady a true se il socket è già connesso
        if (!this.socketReady) {
          console.log('SocketService: socket connesso ma non pronto, imposto pronto');
          this.socketReady = true;
        }
        
        return resolve(this.socket);
      }
      
      // Imposta lo stato e il sessionId
      this.connecting = true;
      this.sessionId = sessionId;
      this.connectionAttempts++;
      
      // Forzare URL corretto per il server - usa la costante globale
      this.serverUrl = SERVER_URL;
      
      console.log(`SocketService: tentativo di connessione #${this.connectionAttempts} a ${this.serverUrl}`);
      
      try {
        // Chiudi l'eventuale socket esistente
        if (this.socket) {
          console.log('SocketService: chiusura socket esistente prima di crearne uno nuovo');
          this.socket.disconnect();
          this.socket = null;
        }
        
        // Opzioni ottimizzate per Socket.IO con Eventlet
        const options = {
          transports: ['websocket'], // SOLO WebSocket, rimuovo polling
          path: '/socket.io/',
          autoConnect: false, // Importante: non connettere automaticamente
          reconnection: true,
          reconnectionAttempts: 10,
          reconnectionDelay: 1000,
          timeout: 30000,         // Aumentato da 20000 a 30000
          upgrade: true,
          rememberUpgrade: true,
          query: sessionId ? { sessionId } : {},
          forceNew: true,        // Forzare sempre nuova connessione
          timestampRequests: true,// Aggiunge timestamp per evitare caching
          extraHeaders: {         // Headers aggiuntivi per autenticazione
            'X-Client-Version': '1.0.0',
            'X-Session-ID': sessionId || 'anonymous'
          }
        };
        
        console.log('SocketService: opzioni di connessione:', JSON.stringify(options));
        
        // Verifica URL completo prima di connessione
        const fullUrl = `${this.serverUrl}${options.path || ''}`;
        console.log(`SocketService: tentativo di connessione WebSocket all'URL completo: ${fullUrl}`);
        
        // Crea la connessione socket ma non la avvia ancora
        this.socket = io(this.serverUrl, options);
        
        // IMPORTANTE: Impedisci a Socket.IO di cambiare l'URL durante le riconnessioni
        if (this.socket.io && this.socket.io.uri) {
          // Verifica che l'URI impostato sia quello che vogliamo
          if (this.socket.io.uri !== this.serverUrl) {
            console.warn(`SocketService: Socket.IO ha impostato un URI diverso: ${this.socket.io.uri}, forzo a ${this.serverUrl}`);
            this.socket.io.uri = this.serverUrl;
          }
          
          // Salva l'URL originale per ripristinarlo durante le riconnessioni
          this.socket._originalUri = this.serverUrl;
          
          // Sovrascrivi il metodo che stabilisce l'URI per le riconnessioni
          const originalReconnection = this.socket.io.reconnection;
          this.socket.io.reconnection = (...args) => {
            console.log(`SocketService: forzando URI ${this.serverUrl} durante riconnessione`);
            this.socket.io.uri = this.serverUrl;  // Forza l'URI corretto
            return originalReconnection.apply(this.socket.io, args);
          };
        }
        
        // Debug extra - controlla quale URL effettivo sta utilizzando Socket.IO
        console.log(`SocketService: URL verificato per il socket:`, {
          url: this.socket.io.uri,
          opts: this.socket.io.opts,
          engine: this.socket.io.engine && this.socket.io.engine.hostname ? 
            `${this.socket.io.engine.secure ? 'wss://' : 'ws://'}${this.socket.io.engine.hostname}:${this.socket.io.engine.port}` : 'N/A'
        });
        
        // Configura gli handler degli eventi base
        this._setupBaseEventHandlers(resolve, reject);
        
        // Avvia la connessione manualmente
        console.log('SocketService: avvio connessione socket manuale');
        this.socket.connect();
        
        // Aggiungi un timeout di sicurezza ulteriore per prevenire blocchi
        const timeoutId = setTimeout(() => {
          // Se dopo 15 secondi siamo ancora nello stato "connecting", qualcosa è andato storto
          if (this.connecting) {
            console.error('SocketService: timeout durante la connessione, forzo fallimento');
            this.connecting = false;
            reject(new Error('Timeout durante la connessione al server'));
          }
        }, 15000);
        
        // Memorizza il timeout per cancellarlo in caso di connessione riuscita
        this._connectionTimeout = timeoutId;
        
      } catch (error) {
        this.connecting = false;
        console.error('SocketService: errore nella creazione del socket:', error);
        reject(error);
      }
    });
  }
  
  /**
   * Configura gli handler per gli eventi di base del socket
   * @private
   */
  _setupBaseEventHandlers(resolve, reject) {
    // Evento connect
    this.socket.on('connect', () => {
      console.log(`SocketService: connesso al server (id: ${this.socket.id})`);
      this.connected = true;
      this.connecting = false;
      this.socketReady = true;
      
      // Annulla il timeout di sicurezza
      if (this._connectionTimeout) {
        clearTimeout(this._connectionTimeout);
        this._connectionTimeout = null;
      }
      
      // Azzera i tentativi di connessione dopo una connessione riuscita
      this.connectionAttempts = 0;
      
      // Risolvi la promise di connessione
      resolve(this.socket);
    });

    // Evento connect_error
    this.socket.on('connect_error', (error) => {
      console.error('SocketService: errore di connessione:', error.message);
      
      this.stats.errors++;
      
      // Solo la prima volta, se stiamo ancora aspettando la connessione, rifiuta la promise
      if (this.connecting) {
        // Annulla il timeout di sicurezza
        if (this._connectionTimeout) {
          clearTimeout(this._connectionTimeout);
          this._connectionTimeout = null;
        }
        
        this.connecting = false;
        reject(error);
      }
    });
    
    // Evento disconnect
    this.socket.on('disconnect', (reason) => {
      console.log(`SocketService: disconnesso, motivo: ${reason}`);
      this.connected = false;
      
      if (reason === 'io server disconnect' || reason === 'io client disconnect') {
        // Disconnessione volontaria, non riconnettere
        this.socketReady = false;
      } else if (reason === 'transport close' || reason === 'transport error') {
        // Problemi di rete, imposta come non connesso ma lascia socketReady invariato
        // per permettere tentativi di riconnessione automatica
        console.log('SocketService: disconnessione dovuta a problemi di rete, permetterò riconnessione automatica');
      }
    });

    // Evento reconnect
    this.socket.on('reconnect', (attemptNumber) => {
      console.log(`SocketService: riconnesso dopo ${attemptNumber} tentativi`);
      this.connected = true;
      this.stats.reconnects++;
    });
    
    // Evento reconnect_attempt
    this.socket.on('reconnect_attempt', (attemptNumber) => {
      console.log(`SocketService: tentativo di riconnessione #${attemptNumber}`);
      
      // IMPORTANTE: Forza l'URL corretto durante la riconnessione
      if (this.socket.io) {
        console.log(`SocketService: forzando URL a ${SERVER_URL} prima della riconnessione`);
        this.socket.io.uri = SERVER_URL;
        
        // Forza WebSocket come transport per la riconnessione
        this.socket.io.opts.transports = ['websocket'];
      }
    });
    
    // Evento error
    this.socket.on('error', (error) => {
      console.error('SocketService: errore:', error);
      this.stats.errors++;
      
      // Gestisci specificatamente gli errori di timeout
      if (error && typeof error === 'string' && error.includes('timeout')) {
        console.error('SocketService: errore di timeout rilevato, tentativo di ripristino connessione');
        
        // Forza una riconnessione
        if (this.socket && !this.socket.disconnected) {
          this.socket.disconnect();
          setTimeout(() => {
            if (this.sessionId) {
              console.log('SocketService: tentativo di riconnessione dopo timeout');
              // Forza l'URL corretto prima di riconnettersi
              if (this.socket.io) {
                this.socket.io.uri = SERVER_URL;
              }
              this.socket.connect();
            }
          }, 2000);
        }
      }
    });
    
    // Evento ping e pong per debug
    if (this.socket.io && this.socket.io.engine) {
      this.socket.io.engine.on('ping', () => {
        console.debug('SocketService: PING inviato al server');
      });
      
      this.socket.io.engine.on('pong', (latency) => {
        console.debug(`SocketService: PONG ricevuto dal server (latenza: ${latency}ms)`);
      });
    }
  }

  /**
   * Disconnette il socket in modo sicuro
   */
  disconnect() {
    if (!this.socket) {
      return;
    }
    
    // Controlla lo stato della connessione
    if (this.socket.io && this.socket.io.readyState === 'opening') {
      // Se il socket è ancora in fase di apertura, evita di chiuderlo
      console.log('SocketService: socket in fase di connessione, evito disconnessione prematura');
      return;
      }
      
    console.log('SocketService: disconnessione socket');
    
    try {
      // Rimuovi tutti i listener prima di disconnettere
      if (this.socket.connected) {
        this.socket.disconnect();
      }
      
      this.connected = false;
      this.socketReady = false;
      
    } catch (error) {
      console.error('SocketService: errore durante la disconnessione:', error);
        }
  }

  /**
   * Registra un listener per un evento
   * @param {string} event - Nome dell'evento
   * @param {Function} callback - Funzione da chiamare quando l'evento viene emesso
   */
  on(event, callback) {
    if (!this.socket) {
      console.warn(`SocketService: impossibile registrare listener per "${event}", socket non inizializzato`);
      return;
      }
      
    // Aggiungi alla mappa dei listener per facilitare la rimozione
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    
    this.listeners.get(event).add(callback);
    this.socket.on(event, callback);
  }

  /**
   * Rimuove un listener per un evento
   * @param {string} event - Nome dell'evento
   * @param {Function} callback - Funzione da rimuovere
   */
  off(event, callback) {
    if (!this.socket) {
      return;
    }
    
    // Se il callback è specificato, rimuovi solo quello
    if (callback) {
      this.socket.off(event, callback);
      
      // Aggiorna la mappa dei listener
      if (this.listeners.has(event)) {
        const callbackSet = this.listeners.get(event);
        callbackSet.delete(callback);
        
        if (callbackSet.size === 0) {
          this.listeners.delete(event);
      }
    }
    } else {
      // Se non è specificato, rimuovi tutti i listener per quell'evento
      this.socket.off(event);
      this.listeners.delete(event);
    }
  }
  
  /**
   * Emette un evento socket
   * @param {string} event - Nome dell'evento
   * @param {Object} data - Dati da inviare
   */
  emit(event, data = {}) {
    if (!this.socket || !this.connected) {
      console.error(`SocketService: impossibile emettere evento "${event}", socket non connesso`);
      return Promise.reject(new Error('Socket non connesso'));
  }
  
    // IMPORTANTE: Verifica l'URL corretto prima di emettere l'evento
    if (this.socket.io && this.socket.io.uri !== SERVER_URL) {
      console.warn(`SocketService: URI errato rilevato prima dell'emissione, correggo da ${this.socket.io.uri} a ${SERVER_URL}`);
      this.socket.io.uri = SERVER_URL;
    }
  
    return new Promise((resolve) => {
      this.socket.emit(event, data);
      this.stats.sent++;
      resolve();
    });
  }
  
  /**
   * Emette un evento e attende una risposta (acknowledgement)
   * @param {string} event - Nome dell'evento
   * @param {Object} data - Dati da inviare
   * @param {number} timeout - Timeout in ms
   * @returns {Promise} Promise che si risolve con la risposta
   */
  emitWithAck(event, data = {}, timeout = 5000) {
    if (!this.socket || !this.connected) {
      console.error(`SocketService: impossibile emettere evento "${event}" con ack, socket non connesso`);
      return Promise.reject(new Error('Socket non connesso'));
    }
    
    // Verifica l'URL corretto prima di emettere l'evento
    if (this.socket.io && this.socket.io.uri !== SERVER_URL) {
      console.warn(`SocketService: URI errato rilevato prima dell'emissione con ACK, correggo da ${this.socket.io.uri} a ${SERVER_URL}`);
      this.socket.io.uri = SERVER_URL;
    }
    
    return new Promise((resolve, reject) => {
      // Timeout per la risposta
      const timeoutId = setTimeout(() => {
        reject(new Error(`Timeout nella risposta dell'evento "${event}"`));
      }, timeout);
      
      this.socket.emit(event, data, (response) => {
        clearTimeout(timeoutId);
        this.stats.sent++;
        resolve(response);
      });
    });
  }
  
  /**
   * Verifica se il socket è connesso
   * @returns {boolean} True se connesso
   */
  isConnected() {
    return this.socket && this.socket.connected;
  }
  
  /**
   * Verifica se il socket è pronto per l'uso
   * @returns {boolean} True se pronto
   */
  isReady() {
    return this.socketReady;
  }
  
  /**
   * Ottiene lo stato attuale della connessione
   * @returns {Object} Stato della connessione
   */
  getConnectionState() {
    return {
      connected: this.connected,
      connecting: this.connecting,
      socketId: this.socket?.id,
      sessionId: this.sessionId,
      ready: this.socketReady,
      stats: { ...this.stats }
    };
  }
  
  /**
   * Ottiene informazioni sul trasporto utilizzato
   * @returns {Object} Informazioni sul trasporto
   */
  getTransportInfo() {
    if (!this.socket || !this.socket.io || !this.socket.io.engine) {
      return { transport: 'none', connected: false };
    }
    
    return {
      transport: this.socket.io.engine.transport.name,
      connected: this.socket.connected,
      socketId: this.socket.id
    };
  }
}

// Crea una singola istanza e la esporta
const socketService = new SocketService();
export default socketService; 