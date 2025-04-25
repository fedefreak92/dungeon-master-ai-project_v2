import { io } from 'socket.io-client';

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
    
    // URL del server WebSocket
    this.serverUrl = process.env.REACT_APP_WS_URL || window.location.origin.replace(/^http/, 'ws');
    
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
          transports: ['websocket', 'polling'], // Preferisci WebSocket
          path: '/socket.io/',
          autoConnect: false, // Importante: non connettere automaticamente
          reconnection: true,
          reconnectionAttempts: 10,
          reconnectionDelay: 1000,
          timeout: 20000,
          upgrade: true,
          rememberUpgrade: true,
          query: sessionId ? { sessionId } : {}
        };
      
        // Crea la connessione socket ma non la avvia ancora
        this.socket = io(this.serverUrl, options);
        
        // Configura gli handler degli eventi base
        this._setupBaseEventHandlers(resolve, reject);
        
        // Avvia la connessione manualmente
        console.log('SocketService: avvio connessione socket manuale');
        this.socket.connect();
        
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
      
      // Risolvi la promise di connessione
      resolve(this.socket);
    });

    // Evento connect_error
    this.socket.on('connect_error', (error) => {
      console.error('SocketService: errore di connessione:', error.message);
      
      this.stats.errors++;
      
      // Solo la prima volta, se stiamo ancora aspettando la connessione, rifiuta la promise
      if (this.connecting) {
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
      }
    });

    // Evento reconnect
    this.socket.on('reconnect', (attemptNumber) => {
      console.log(`SocketService: riconnesso dopo ${attemptNumber} tentativi`);
      this.connected = true;
      this.stats.reconnects++;
    });
    
    // Evento error
    this.socket.on('error', (error) => {
      console.error('SocketService: errore:', error);
      this.stats.errors++;
    });
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