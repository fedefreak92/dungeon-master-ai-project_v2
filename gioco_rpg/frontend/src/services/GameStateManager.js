import socketService from '../api/socketService';
import EventEmitter from 'events';

/**
 * Manager per la gestione dello stato di gioco e la sincronizzazione
 * Implementa pattern Observer per notificare i componenti dei cambiamenti
 */
class GameStateManager extends EventEmitter {
  constructor() {
    super();
    
    // Stato di sincronizzazione
    this.stateVersion = 0;
    this.fullState = null;
    this.pendingChanges = [];
    this.lastSyncTime = 0;
    this.resyncInProgress = false;
    
    // Componenti attivi che osservano lo stato
    this.activeComponents = new Set();
    
    // Flag per snapshot periodici
    this.snapshotInterval = null;
    this.snapshotFrequency = 30000; // 30 secondi
    
    // Inizializza i listener per eventi di stato dal server
    this.setupListeners();
  }
  
  /**
   * Configura i listener per gli eventi di stato
   * @private
   */
  setupListeners() {
    // Ascolta per aggiornamenti completi dello stato
    socketService.on('game_state_full', (data) => {
      this.applyFullState(data);
    });
    
    // Ascolta per aggiornamenti incrementali
    socketService.on('game_state_delta', (data) => {
      this.applyChanges(data.changes, data.version);
    });
    
    // Ascolta per eventi di notifica cambiamenti specifici
    socketService.on('game_event', (event) => {
      this.handleGameEvent(event);
    });
    
    // Gestione migliorata della riconnessione
    socketService.on('connect', () => {
      const disconnectionDuration = socketService.disconnectionDuration || 0;
      
      // Imposta una soglia più bassa per il risync (5 secondi)
      if (disconnectionDuration > 5000) {
        console.log(`Disconnesso per ${disconnectionDuration/1000}s, richiedo sincronizzazione completa`);
        this.requestFullSync();
      } else if (disconnectionDuration > 0) {
        console.log(`Breve disconnessione (${disconnectionDuration/1000}s), richiedo aggiornamenti recenti`);
        this.requestRecentUpdates();
      }
    });
    
    // Ascolta per errori di sincronizzazione
    socketService.on('sync_error', (data) => {
      console.warn('Errore di sincronizzazione:', data);
      // In caso di errori di versione, richiedi stato completo
      if (data.error === 'version_mismatch') {
        this.requestFullSync();
      }
    });
  }
  
  /**
   * Inizializza lo stato del gioco con i dati iniziali
   * @param {Object} initialState - Stato iniziale del gioco
   */
  initialize(initialState) {
    if (!initialState) return;
    
    this.fullState = initialState.data || initialState;
    this.stateVersion = initialState.version || 0;
    this.lastSyncTime = Date.now();
    
    // Emetti evento di inizializzazione completata
    this.emit('state_initialized', this.fullState);
    
    // Avvia snapshot periodici
    this.startPeriodicSnapshots();
    
    console.log(`Stato di gioco inizializzato, versione: ${this.stateVersion}`);
  }
  
  /**
   * Gestisce un evento di gioco ricevuto dal server
   * @param {Object} event - Evento di gioco
   * @private
   */
  handleGameEvent(event) {
    if (!event || !event.type) return;
    
    // Aggiorna la versione se fornita
    if (event.stateVersion && event.stateVersion > this.stateVersion) {
      this.stateVersion = event.stateVersion;
    }
    
    // Emetti l'evento per i componenti interessati
    this.emit(`game_event_${event.type}`, event.data);
    this.emit('game_event', event);
  }
  
  /**
   * Applica un insieme di modifiche incrementali allo stato
   * @param {Array} changes - Array di modifiche da applicare
   * @param {Number} newVersion - Nuova versione dello stato
   * @returns {Boolean} - true se applicato con successo, false altrimenti
   */
  applyChanges(changes, newVersion) {
    if (!Array.isArray(changes) || typeof newVersion !== 'number') {
      console.error('Formato modifiche non valido');
      return false;
    }
    
    // Verifica che la versione sia consecutiva
    if (newVersion !== this.stateVersion + 1) {
      console.warn(`Versione modifiche non consecutiva: attesa ${this.stateVersion + 1}, ricevuta ${newVersion}`);
      this.requestFullSync();
      return false;
    }
    
    try {
      // Applica ogni modifica allo stato
      changes.forEach(change => this.applyChange(change));
      
      // Aggiorna la versione
      this.stateVersion = newVersion;
      this.lastSyncTime = Date.now();
      
      // Notifica i componenti
      this.emit('state_changed', {
        changes,
        version: newVersion
      });
      
      return true;
    } catch (error) {
      console.error('Errore nell\'applicazione delle modifiche:', error);
      this.requestFullSync();
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
   * Applica uno stato completo al posto dello stato corrente
   * @param {Object} state - Stato completo da applicare
   */
  applyFullState(state) {
    if (!state || (!state.data && !state.version)) {
      console.error('Stato completo non valido');
      return;
    }
    
    this.fullState = state.data || state;
    this.stateVersion = state.version || this.stateVersion;
    this.lastSyncTime = Date.now();
    this.resyncInProgress = false;
    
    // Notifica i componenti
    this.emit('state_resync', this.fullState);
    
    console.log(`Stato completo applicato, versione: ${this.stateVersion}`);
  }
  
  /**
   * Richiede lo stato completo del gioco al server
   */
  requestFullSync() {
    if (this.resyncInProgress) return;
    
    console.log('Richiesta sincronizzazione completa dello stato');
    this.resyncInProgress = true;
    
    socketService.emit('request_full_state', {
      id_sessione: socketService.sessionId,
      current_version: this.stateVersion
    });
    
    // Timeout di sicurezza per resettare il flag se non riceviamo risposta
    setTimeout(() => {
      if (this.resyncInProgress) {
        this.resyncInProgress = false;
      }
    }, 10000);
  }
  
  /**
   * Ottiene il valore di una proprietà specifica dallo stato
   * @param {String} path - Percorso della proprietà (formato 'user.inventory.items')
   * @param {*} defaultValue - Valore di default se la proprietà non esiste
   * @returns {*} - Valore della proprietà o default
   */
  getStateValue(path, defaultValue = null) {
    if (!path || !this.fullState) return defaultValue;
    
    try {
      // Split del path e navigazione nell'oggetto
      const parts = path.split('.');
      let current = this.fullState;
      
      for (const part of parts) {
        if (current === null || current === undefined) return defaultValue;
        current = current[part];
      }
      
      return current !== undefined ? current : defaultValue;
    } catch (error) {
      console.error(`Errore nel recupero della proprietà ${path}:`, error);
      return defaultValue;
    }
  }
  
  /**
   * Registra un componente come osservatore dello stato
   * @param {String} componentId - ID univoco del componente
   * @param {Function} callback - Funzione da chiamare al cambiamento 
   * @param {Array} paths - Array di percorsi da osservare
   */
  subscribe(componentId, callback, paths = []) {
    if (!componentId || typeof callback !== 'function') return;
    
    // Registra il componente
    this.activeComponents.add(componentId);
    
    // Ascolta gli eventi di cambiamento generale
    this.on('state_changed', callback);
    
    // Se specificati paths specifici, registra callback specifici
    if (Array.isArray(paths) && paths.length > 0) {
      paths.forEach(path => {
        this.on(`change:${path}`, callback);
      });
    }
    
    // Restituisci lo stato attuale subito
    if (this.fullState) {
      callback({
        type: 'initial',
        state: this.fullState
      });
    }
  }
  
  /**
   * Annulla la registrazione di un componente
   * @param {String} componentId - ID del componente
   * @param {Function} callback - Funzione callback originale
   * @param {Array} paths - Array di percorsi osservati
   */
  unsubscribe(componentId, callback, paths = []) {
    if (!componentId) return;
    
    // Rimuovi il componente
    this.activeComponents.delete(componentId);
    
    // Rimuovi callback general
    if (callback) {
      this.removeListener('state_changed', callback);
    }
    
    // Rimuovi callback specifici per path
    if (Array.isArray(paths) && paths.length > 0 && callback) {
      paths.forEach(path => {
        this.removeListener(`change:${path}`, callback);
      });
    }
  }
  
  /**
   * Avvia il salvataggio periodico di snapshot dello stato
   * @private
   */
  startPeriodicSnapshots() {
    if (this.snapshotInterval) {
      clearInterval(this.snapshotInterval);
    }
    
    this.snapshotInterval = setInterval(() => {
      this.saveSnapshot();
    }, this.snapshotFrequency);
  }
  
  /**
   * Salva uno snapshot dello stato corrente
   * @private
   */
  saveSnapshot() {
    if (!this.fullState) return;
    
    try {
      // Salva lo snapshot in localStorage per recupero in caso di refresh
      const snapshot = {
        version: this.stateVersion,
        timestamp: Date.now(),
        data: this.fullState
      };
      
      localStorage.setItem('game_state_snapshot', JSON.stringify(snapshot));
      console.debug(`Snapshot dello stato salvato, versione: ${this.stateVersion}`);
    } catch (error) {
      console.error('Errore nel salvataggio dello snapshot:', error);
    }
  }
  
  /**
   * Carica uno snapshot salvato precedentemente
   * @returns {Object|null} - Snapshot caricato o null se non disponibile
   */
  loadSnapshot() {
    try {
      const snapshot = localStorage.getItem('game_state_snapshot');
      if (!snapshot) return null;
      
      const parsedSnapshot = JSON.parse(snapshot);
      
      // Verifica validità
      if (!parsedSnapshot.data || !parsedSnapshot.version) {
        return null;
      }
      
      // Verifica che non sia troppo vecchio (max 1 ora)
      const age = Date.now() - (parsedSnapshot.timestamp || 0);
      if (age > 3600000) {
        console.warn('Snapshot troppo vecchio, non utilizzato');
        return null;
      }
      
      console.log(`Snapshot caricato, versione: ${parsedSnapshot.version}`);
      return parsedSnapshot;
    } catch (error) {
      console.error('Errore nel caricamento dello snapshot:', error);
      return null;
    }
  }
  
  /**
   * Reset completo dello stato
   */
  reset() {
    this.fullState = null;
    this.stateVersion = 0;
    this.pendingChanges = [];
    this.lastSyncTime = 0;
    
    // Ferma gli snapshot periodici
    if (this.snapshotInterval) {
      clearInterval(this.snapshotInterval);
      this.snapshotInterval = null;
    }
    
    // Rimuovi snapshot salvati
    try {
      localStorage.removeItem('game_state_snapshot');
    } catch (error) {
      console.error('Errore nella rimozione dello snapshot:', error);
    }
    
    // Notifica reset
    this.emit('state_reset');
  }
  
  /**
   * Richiede aggiornamenti recenti invece dello stato completo
   * Utile per brevi disconnessioni
   */
  requestRecentUpdates() {
    if (!socketService.isConnected()) {
      console.warn('Impossibile richiedere aggiornamenti recenti: socket disconnesso');
      return;
    }
    
    socketService.emit('request_recent_updates', {
      last_version: this.state.version,
      timestamp: Date.now()
    });
    
    this.emit('sync_started', { type: 'partial' });
  }
}

// Esporta singola istanza del manager
const gameStateManager = new GameStateManager();
export default gameStateManager; 