/**
 * Servizio per gestire la comunicazione Socket.IO con il server.
 */

import { io } from 'socket.io-client';

class SocketIOService {
    constructor() {
        this.socket = null;
        
        // Ottieni URL da localStorage o usa l'URL predefinito
        const savedURL = localStorage.getItem('serverURL');
        this.serverUrl = process.env.REACT_APP_API_URL || 
                          savedURL || 
                          'http://localhost:5000';
        
        this.callbacks = {};
        this.isConnecting = false;
        this.autoReconnect = true;
        this.connectionAttempts = 0;
        
        // Stampa informazioni di debug
        console.log(`Socket.IO configurato per connettersi a: ${this.serverUrl}`);
    }

    /**
     * Imposta l'URL del server (utile per usare ngrok)
     * @param {string} url - Il nuovo URL del server
     */
    setServerUrl(url) {
        if (!url || typeof url !== 'string') return;
        
        // Salva nel localStorage per persistenza
        localStorage.setItem('serverURL', url);
        this.serverUrl = url;
        console.log(`Socket.IO: URL server cambiato a ${url}`);
        
        // Disconnetti se già connesso
        if (this.socket && this.socket.connected) {
            this.disconnect();
        }
    }

    /**
     * Inizializza la connessione Socket.IO
     * @returns {Promise} Promise che si risolve quando la connessione è stabilita
     */
    connect() {
        return new Promise((resolve, reject) => {
            if (this.socket && this.socket.connected) {
                console.log('Socket.IO: già connesso, riuso la connessione esistente');
                resolve(this.socket);
                return;
            }

            this.isConnecting = true;
            this.connectionAttempts++;
            console.log(`Socket.IO: tentativo di connessione #${this.connectionAttempts} a ${this.serverUrl}`);
            
            try {
                // CONFIGURAZIOME OTTIMALE PER WEBSOCKET CON EVENTLET
                // 1. Inizialmente utilizza polling per stabilire la connessione
                // 2. Poi tenta l'upgrade a WebSocket con parametri compatibili con eventlet
                const options = {
                    // Prima usa polling, poi tenta di passare a WebSocket
                    transports: ['polling', 'websocket'],
                    // Percorso standard Socket.IO
                    path: '/socket.io/',
                    // Versione Engine.IO compatibile col server
                    EIO: 4,
                    // Connessione e riconnessione
                    autoConnect: true,
                    reconnection: true,
                    reconnectionAttempts: 10,
                    reconnectionDelay: 1000,
                    // Timeout sufficiente per stabilire la connessione
                    timeout: 20000,
                    // Parametri cruciali per WebSocket
                    upgrade: true,
                    rememberUpgrade: true,
                    // Permetti aggiornamenti di connessione
                    forceNew: false,
                    // Parametri di sicurezza
                    withCredentials: false,
                    // Parametri extra per migliorare la compatibilità con eventlet
                    transportOptions: {
                        websocket: {
                            extraHeaders: {
                                "User-Agent": navigator.userAgent,
                                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                            }
                        },
                        polling: {
                            extraHeaders: {
                                "User-Agent": navigator.userAgent
                            }
                        }
                    }
                };
                
                // Log delle opzioni per debug
                console.log('Socket.IO: opzioni di connessione per WebSocket:', options);
                
                // Crea la connessione
                this.socket = io(this.serverUrl, options);
                
                // Registra tutti gli handler di eventi prima che avvenga qualsiasi connessione
                this._setupEventHandlers(resolve, reject);
                
            } catch (error) {
                this.isConnecting = false;
                console.error('Socket.IO: errore fatale durante la creazione della connessione:', error);
                reject(error);
            }
        });
    }
    
    /**
     * Configura tutti gli handler di eventi per la connessione Socket.IO
     * @private
     */
    _setupEventHandlers(resolve, reject) {
        // Evento di connessione avvenuta
        this.socket.on('connect', () => {
            console.log('Socket.IO: connessione stabilita con ID:', this.socket.id);
            this.isConnecting = false;
            
            // Controlla e mostra informazioni sul tipo di trasporto
            const transport = this.socket.io.engine.transport.name;
            console.log(`Socket.IO: trasporto utilizzato: ${transport}`);
            
            this._triggerEvent('connection_established', { 
                status: 'connected',
                transport: transport,
                id: this.socket.id
            });
            
            // Risolve la promise per indicare connessione completata
            resolve(this.socket);
        });
        
        // Evento di upgrade del trasporto (da polling a WebSocket)
        if (this.socket.io && this.socket.io.engine) {
            this.socket.io.engine.on('upgrade', (transport) => {
                console.log(`Socket.IO: trasporto aggiornato a ${transport.name}`);
            });
        }
        
        // Evento di disconnessione
        this.socket.on('disconnect', (reason) => {
            console.log('Socket.IO: disconnesso, motivo:', reason);
            this.isConnecting = false;
            this._triggerEvent('connection_closed', { reason });
        });
        
        // Evento di errore di connessione
        this.socket.on('connect_error', (error) => {
            console.error('Socket.IO: errore di connessione:', error);
            this.isConnecting = false;
            
            // Se si tratta di un errore WebSocket, logga dettagli
            if (error && error.message && error.message.includes('websocket')) {
                console.warn('Socket.IO: rilevato errore specifico WebSocket, tentativo fallback a polling');
            }
            
            this._triggerEvent('connection_error', { error: error.message || 'Errore sconosciuto' });
            
            // Se l'errore è critico e non è stato possibile stabilire connessione
            if (!this.socket.connected) {
                reject(error);
            }
        });
        
        // Tentativi di riconnessione
        this.socket.on('reconnect_attempt', (attemptNumber) => {
            console.log(`Socket.IO: tentativo di riconnessione #${attemptNumber}`);
        });
        
        // Riconnessione avvenuta
        this.socket.on('reconnect', (attemptNumber) => {
            console.log(`Socket.IO: riconnessione riuscita dopo ${attemptNumber} tentativi`);
            
            // Controlla e mostra informazioni sul tipo di trasporto dopo riconnessione
            if (this.socket.io && this.socket.io.engine) {
                const transport = this.socket.io.engine.transport.name;
                console.log(`Socket.IO: trasporto dopo riconnessione: ${transport}`);
            }
        });
        
        // Errori di riconnessione
        this.socket.on('reconnect_error', (error) => {
            console.error('Socket.IO: errore di riconnessione:', error);
        });
        
        // Errori generici
        this.socket.on('error', (error) => {
            console.error('Socket.IO: errore generico:', error);
        });
        
        // Gestione di eventi sconosciuti
        this.socket.onAny((eventName, ...args) => {
            if (eventName !== 'ping' && eventName !== 'pong') { // Filtra eventi di heartbeat
                console.log(`Socket.IO: ricevuto evento "${eventName}"`, args);
            }
            this._triggerEvent(eventName, args[0]);
        });
    }

    /**
     * Chiude la connessione Socket.IO in modo sicuro
     */
    disconnect() {
        console.log('Socket.IO: tentativo di disconnessione');
        
        if (!this.socket) {
            console.log('Socket.IO: nessuna connessione attiva da disconnettere');
            return;
        }
        
        try {
            // Rimuovi tutti i listener prima di disconnettere
            this.socket.offAny();
            this.socket.disconnect();
            console.log('Socket.IO: disconnessione completata');
            this.socket = null;
        } catch (error) {
            console.error('Socket.IO: errore durante la disconnessione:', error);
        }
    }

    /**
     * Registra un callback per un tipo di evento
     * @param {string} eventType - Tipo di evento da ascoltare
     * @param {function} callback - Funzione da chiamare quando l'evento viene ricevuto
     */
    on(eventType, callback) {
        // Registra l'evento nelle callback interne
        if (!this.callbacks[eventType]) {
            this.callbacks[eventType] = [];
        }
        this.callbacks[eventType].push(callback);
        
        // Registra anche direttamente su Socket.IO se è un evento nativo
        if (this.socket && eventType !== 'connection_established' && 
            eventType !== 'connection_closed' && eventType !== 'connection_error') {
            this.socket.on(eventType, callback);
        }
    }

    /**
     * Rimuove un callback per un tipo di evento
     * @param {string} eventType - Tipo di evento
     * @param {function} callback - Callback da rimuovere
     */
    off(eventType, callback) {
        // Rimuovi dalle callback interne
        if (!this.callbacks[eventType]) return;
        
        this.callbacks[eventType] = this.callbacks[eventType].filter(
            registeredCallback => registeredCallback !== callback
        );
        
        // Rimuovi anche da Socket.IO se è un evento nativo
        if (this.socket && eventType !== 'connection_established' && 
            eventType !== 'connection_closed' && eventType !== 'connection_error') {
            this.socket.off(eventType, callback);
        }
    }

    /**
     * Invia un messaggio al server
     * @param {string} eventName - Nome dell'evento
     * @param {object} data - Dati da inviare
     * @param {function} ack - Callback di acknowledgement (opzionale)
     * @returns {Promise} Promise che si risolve quando il messaggio è stato inviato
     */
    emit(eventName, data = {}, ack = null) {
        return new Promise((resolve, reject) => {
            if (!this.socket || !this.socket.connected) {
                this.connect()
                    .then(() => this._emitMessage(eventName, data, ack, resolve, reject))
                    .catch(reject);
            } else {
                this._emitMessage(eventName, data, ack, resolve, reject);
            }
        });
    }

    /**
     * Metodo helper per scatenare un evento e chiamare tutti i callback registrati
     * @param {string} eventType - Tipo di evento
     * @param {object} data - Dati dell'evento
     * @private
     */
    _triggerEvent(eventType, data) {
        if (this.callbacks[eventType]) {
            this.callbacks[eventType].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Errore nell'esecuzione del callback per l'evento ${eventType}:`, error);
                }
            });
        }
    }

    /**
     * Metodo helper per inviare un messaggio al server
     * @param {string} eventName - Nome dell'evento
     * @param {object} data - Dati da inviare
     * @param {function} ack - Callback di acknowledgement
     * @param {function} resolve - Funzione resolve della Promise
     * @param {function} reject - Funzione reject della Promise
     * @private
     */
    _emitMessage(eventName, data, ack, resolve, reject) {
        try {
            if (ack) {
                // Se è stato fornito un callback di acknowledgement
                this.socket.emit(eventName, data, ack);
                resolve();
            } else {
                // Senza callback, risolviamo immediatamente
                this.socket.emit(eventName, data);
                resolve();
            }
        } catch (error) {
            console.error(`Errore nell'invio dell'evento ${eventName}:`, error);
            reject(error);
        }
    }
    
    /**
     * Ottiene informazioni sul trasporto attuale
     * @returns {object} Informazioni sul trasporto
     */
    getTransportInfo() {
        if (!this.socket || !this.socket.io || !this.socket.io.engine) {
            return { 
                connected: false, 
                transport: 'none'
            };
        }
        
        return {
            connected: this.socket.connected,
            transport: this.socket.io.engine.transport.name,
            upgradeable: this.socket.io.engine.upgrading,
            id: this.socket.id
        };
    }
}

// Esporta un'istanza singleton del servizio
const socketIOService = new SocketIOService();
export default socketIOService; 