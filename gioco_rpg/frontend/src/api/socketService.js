import io from 'socket.io-client';

const API_URL = 'http://localhost:5000';

/**
 * Classe di servizio per gestire le comunicazioni WebSocket
 */
class SocketService {
  constructor() {
    this.socket = null;
    this.connected = false;
    this.listeners = {};
    this.sessionId = null;
  }

  /**
   * Inizializza la connessione WebSocket
   * @param {string} sessionId - ID della sessione di gioco
   * @param {Object} options - Opzioni aggiuntive per la connessione
   * @returns {Promise} - Promise che si risolve quando la connessione è stabilita
   */
  connect(sessionId, options = {}) {
    return new Promise((resolve, reject) => {
      if (this.socket && this.connected) {
        console.log('Già connesso, riutilizzo la connessione esistente');
        resolve(this.socket);
        return;
      }

      // Salva l'ID sessione per riconnessioni
      this.sessionId = sessionId;
      
      // Crea la connessione socket
      this.socket = io(API_URL, {
        transports: ['websocket', 'polling'],
        ...options
      });

      // Gestione eventi di connessione
      this.socket.on('connect', () => {
        console.log('WebSocket connesso');
        this.connected = true;
        
        // Entra nella sessione di gioco
        this.socket.emit('join_game', { id_sessione: sessionId });
        
        resolve(this.socket);
      });

      this.socket.on('connect_error', (err) => {
        console.error('Errore connessione WebSocket:', err);
        this.connected = false;
        reject(err);
      });

      this.socket.on('disconnect', (reason) => {
        console.log(`WebSocket disconnesso: ${reason}`);
        this.connected = false;
        
        if (reason === 'io server disconnect') {
          // La disconnessione è stata iniziata dal server, riconnetti manualmente
          this.socket.connect();
        }
      });

      // Gestione errori generici
      this.socket.on('error', (err) => {
        console.error('Errore WebSocket:', err);
      });
    });
  }

  /**
   * Disconnette il socket
   */
  disconnect() {
    if (this.socket) {
      console.log('Chiusura connessione WebSocket');
      this.socket.disconnect();
      this.socket = null;
      this.connected = false;
      this.listeners = {};
    }
  }

  /**
   * Invia un evento al server
   * @param {string} eventName - Nome dell'evento
   * @param {Object} data - Dati da inviare
   * @returns {boolean} - true se l'invio è riuscito, false altrimenti
   */
  emit(eventName, data) {
    if (this.socket && this.connected) {
      this.socket.emit(eventName, data);
      return true;
    }
    console.warn(`Tentativo di inviare evento '${eventName}' ma socket non connesso`);
    return false;
  }

  /**
   * Registra un listener per un evento
   * @param {string} eventName - Nome dell'evento
   * @param {Function} callback - Funzione da chiamare quando l'evento viene ricevuto
   */
  on(eventName, callback) {
    if (!this.socket) {
      console.warn(`Tentativo di registrare un listener per '${eventName}' ma socket non inizializzato`);
      return;
    }
    
    // Memorizza il callback per gestione pulizia
    if (!this.listeners[eventName]) {
      this.listeners[eventName] = [];
    }
    this.listeners[eventName].push(callback);
    
    this.socket.on(eventName, callback);
  }

  /**
   * Rimuove un listener per un evento
   * @param {string} eventName - Nome dell'evento
   * @param {Function} callback - Funzione da rimuovere (opzionale)
   */
  off(eventName, callback) {
    if (!this.socket) return;
    
    if (callback && this.listeners[eventName]) {
      // Rimuovi solo il callback specifico
      this.socket.off(eventName, callback);
      this.listeners[eventName] = this.listeners[eventName].filter(cb => cb !== callback);
    } else {
      // Rimuovi tutti i listener per questo evento
      this.socket.off(eventName);
      delete this.listeners[eventName];
    }
  }

  /**
   * Richiede i dati delle entità al server
   * @returns {boolean} - true se la richiesta è stata inviata, false altrimenti
   */
  requestEntities() {
    return this.emit('request_entities', { id_sessione: this.sessionId });
  }

  /**
   * Invia un comando di movimento al server
   * @param {number} dx - Spostamento sull'asse X
   * @param {number} dy - Spostamento sull'asse Y
   * @returns {boolean} - true se la richiesta è stata inviata, false altrimenti
   */
  movePlayer(dx, dy) {
    return this.emit('player_move', { 
      id_sessione: this.sessionId, 
      dx, 
      dy 
    });
  }

  /**
   * Invia un comando di interazione al server
   * @param {string} entityId - ID dell'entità con cui interagire
   * @returns {boolean} - true se la richiesta è stata inviata, false altrimenti
   */
  interactWithEntity(entityId) {
    return this.emit('entity_interact', { 
      id_sessione: this.sessionId, 
      id_entita: entityId 
    });
  }
}

// Esporta un'istanza singleton del servizio
export default new SocketService(); 