import { io } from 'socket.io-client';

class SocketService {
  constructor() {
    this.socket = null;
    this.connecting = false;
    this.connectedTimestamp = null;
    this.lastSessionId = null;
    this.connectionAttempts = 0;
    this.connectionPromise = null;
    this.connectionPromiseResolve = null;
    this.connectionPromiseReject = null;
  }
  
  /**
   * Connette al server WebSocket
   * @param {string} sessionId - ID sessione per l'autenticazione
   * @returns {Promise<Object>} - Promise che risolve con il socket connesso
   */
  connect(sessionId) {
    // Evita connessioni multiple
    if (this.connecting) {
      console.warn('SocketService: connessione già in corso, in attesa...');
      return this.connectionPromise;
    }
    
    if (this.isConnected() && this.lastSessionId === sessionId) {
      console.info('SocketService: già connesso con lo stesso sessionId, riutilizzo connessione');
      return Promise.resolve(this.socket);
    }
    
    this.connectionAttempts++;
    this.connecting = true;
    this.lastSessionId = sessionId;
    
    // Crea un nuovo promise per la connessione
    this.connectionPromise = new Promise((resolve, reject) => {
      this.connectionPromiseResolve = resolve;
      this.connectionPromiseReject = reject;
      
      console.log(`SocketService: tentativo di connessione #${this.connectionAttempts} a ${import.meta.env.VITE_API_URL || 'http://localhost:5000'}`);
      
      // Se c'è un socket esistente, disconnettilo prima
      if (this.socket) {
        console.info('SocketService: disconnessione socket esistente prima della riconnessione');
        this.socket.disconnect();
        this.socket = null;
      }
      
      const options = {
        transports: ['websocket'],
        path: '/socket.io/',
        autoConnect: false,
        reconnection: true,
        reconnectionAttempts: 10,
        reconnectionDelay: 1000,
        timeout: 30000,
        upgrade: true,
        rememberUpgrade: true,
        query: {
          sessionId: sessionId
        },
        forceNew: true,
        timestampRequests: true,
        extraHeaders: {
          'X-Client-Version': '1.0.0',
          'X-Session-ID': sessionId
        }
      };
      
      console.log('SocketService: opzioni di connessione:', JSON.stringify(options));
      
      // Crea il socket con le opzioni
      const url = import.meta.env.VITE_API_URL || 'http://localhost:5000';
      console.log(`SocketService: tentativo di connessione WebSocket all'URL completo: ${url}`);
      
      try {
        // Verifica validità URL
        const urlObj = new URL(url);
        console.log('SocketService: URL verificato per il socket:', urlObj);
        this.socket = io(url, options);
        
        // Configura handler eventi
        this.setupSocketHandlers();
        
        // Avvia connessione
        console.log('SocketService: avvio connessione socket manuale');
        this.socket.connect();
      } catch (error) {
        console.error('SocketService: errore nella creazione del socket:', error);
        this.connecting = false;
        this.connectionPromiseReject(error);
        reject(error);
      }
    });
    
    return this.connectionPromise;
  }
  
  /**
   * Configura gli handler per gli eventi del socket
   */
  setupSocketHandlers() {
    if (!this.socket) return;
    
    this.socket.on('connect', () => {
      console.log(`SocketService: connesso al server (id: ${this.socket.id})`);
      this.connecting = false;
      this.connectedTimestamp = Date.now();
      
      if (this.connectionPromiseResolve) {
        this.connectionPromiseResolve(this.socket);
      }
    });
    
    this.socket.on('connect_error', (error) => {
      console.error('SocketService: errore di connessione:', error);
      
      // Rifiuta il promise solo se è il primo errore
      if (this.connecting && this.connectionPromiseReject) {
        this.connecting = false;
        this.connectionPromiseReject(error);
      }
    });
    
    this.socket.on('disconnect', (reason) => {
      console.warn(`SocketService: disconnesso, motivo: ${reason}`);
      this.connectedTimestamp = null;
    });
    
    this.socket.on('error', (error) => {
      console.error('SocketService: errore nel socket:', error);
    });
    
    // Gestione eventi di risposta dal server
    this.socket.on('game_load_confirmed', (data) => {
      console.log('SocketService: caricamento gioco confermato dal server:', data);
      // Qui puoi emettere un evento personalizzato o chiamare una callback
      if (window.dispatchEvent) {
        window.dispatchEvent(new CustomEvent('game_load_confirmed', { detail: data }));
      }
    });
    
    this.socket.on('request_game_state_update', (data) => {
      console.log('SocketService: richiesta aggiornamento stato di gioco dal server:', data);
      // Qui puoi emettere un evento personalizzato o chiamare una callback
      if (window.dispatchEvent) {
        window.dispatchEvent(new CustomEvent('request_game_state_update', { detail: data }));
      }
    });
  }
  
  /**
   * Disconnette dal server WebSocket
   */
  disconnect() {
    if (this.socket) {
      console.log('SocketService: disconnessione dal server');
      this.socket.disconnect();
      this.socket = null;
      this.connecting = false;
      this.connectedTimestamp = null;
    }
  }
  
  /**
   * Verifica se il socket è connesso
   * @returns {boolean} true se connesso
   */
  isConnected() {
    return this.socket !== null && this.socket.connected;
  }
  
  /**
   * Verifica se il socket è in fase di connessione
   * @returns {boolean} true se in connessione
   */
  isConnecting() {
    return this.connecting;
  }
  
  /**
   * Ottiene il socket corrente
   * @returns {Object|null} il socket o null se non connesso
   */
  getSocket() {
    return this.socket;
  }
  
  /**
   * Emette un evento sul socket
   * @param {string} event - Nome dell'evento
   * @param {Object} data - Dati dell'evento
   * @returns {boolean} true se l'evento è stato emesso
   */
  emit(event, data) {
    if (this.isConnected()) {
      this.socket.emit(event, data);
      return true;
    }
    console.warn(`SocketService: impossibile emettere evento ${event}, socket non connesso`);
    return false;
  }
  
  /**
   * Ottiene informazioni sullo stato di connessione
   * @returns {Object} informazioni sulla connessione
   */
  getConnectionInfo() {
    return {
      connected: this.isConnected(),
      connecting: this.connecting,
      socketId: this.socket?.id,
      lastSessionId: this.lastSessionId,
      connectedSince: this.connectedTimestamp ? new Date(this.connectedTimestamp) : null,
      connectionAttempts: this.connectionAttempts
    };
  }
}

// Esporta un'istanza singleton
export const socketService = new SocketService(); 