import axios from 'axios';

const API_URL = 'http://localhost:5000';

/**
 * Funzione di debug per gestire i log in modo coerente
 */
const logDebug = (method, message, data = null, isError = false) => {
  const logFn = isError ? console.error : console.log;
  const prefix = `[MapAPI:${method}]`;
  
  if (data) {
    logFn(`${prefix} ${message}`, data);
  } else {
    logFn(`${prefix} ${message}`);
  }
};

/**
 * API per la gestione delle mappe
 */
const mapApi = {
  /**
   * Ottiene la lista delle mappe disponibili
   * @param {string} sessionId - ID della sessione
   * @returns {Promise<Object>} - Lista delle mappe e mappa corrente
   */
  getMaps: async (sessionId) => {
    logDebug('getMaps', `Richiesta liste mappe per sessione: ${sessionId}`);
    
    try {
      const response = await axios.get(`${API_URL}/game/scelta_mappa/liste_mappe`, {
        params: { id_sessione: sessionId }
      });
      
      logDebug('getMaps', "Risposta API scelta_mappa/liste_mappe:", response.data);
      
      if (response.data && response.data.success) {
        return {
          maps: response.data.mappe || {},
          currentMap: response.data.mappa_corrente
        };
      } else {
        const errMsg = response.data?.error || 'Impossibile recuperare le mappe';
        logDebug('getMaps', errMsg, response.data, true);
        throw new Error(errMsg);
      }
    } catch (error) {
      logDebug('getMaps', 'Errore nel recupero delle mappe:', error, true);
      throw error;
    }
  },
  
  /**
   * Cambia la mappa corrente
   * @param {string} sessionId - ID della sessione
   * @param {string} mapId - ID della mappa destinazione
   * @returns {Promise<Object>} - Risposta dal server
   */
  changeMap: async (sessionId, mapId) => {
    const MAX_RETRIES = 2;
    let retryCount = 0;
    let lastError = null;
    
    logDebug('changeMap', `Avvio richiesta cambio mappa: sessionId=${sessionId}, mapId=${mapId}`);
    
    while (retryCount <= MAX_RETRIES) {
      try {
        logDebug('changeMap', `Tentativo di cambio mappa (${retryCount+1}/${MAX_RETRIES+1}): sessione=${sessionId}, mappa=${mapId}`);
        
        if (!sessionId) {
          throw new Error('ID sessione mancante per la richiesta di cambio mappa');
        }
        
        if (!mapId) {
          throw new Error('ID mappa mancante per la richiesta di cambio mappa');
        }
        
        // Verifica che stiamo usando il metodo POST con URL corretto
        logDebug('changeMap', `Inviando richiesta POST a ${API_URL}/game/scelta_mappa/cambia_mappa`);
        
        const response = await axios({
          method: 'post',
          url: `${API_URL}/game/scelta_mappa/cambia_mappa`,
          data: {
            id_sessione: sessionId,
            id_mappa: mapId
          },
          timeout: 10000, // Aumentato il timeout a 10 secondi
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        logDebug('changeMap', `Risposta cambio mappa ricevuta:`, response.data);
        
        if (response.data && response.data.success) {
          return {
            success: true,
            mapId: response.data.mappa,
            position: response.data.posizione
          };
        } else {
          // Il server ha risposto ma con errore
          const errorMsg = response.data?.error || 'Impossibile cambiare mappa';
          logDebug('changeMap', `Errore dal server per cambio mappa:`, errorMsg, true);
          throw new Error(errorMsg);
        }
      } catch (error) {
        lastError = error;
        
        // Gestione dettagliata degli errori
        if (error.response) {
          // Il server ha risposto con un codice di errore
          const serverError = error.response.data?.error || 'Errore dal server';
          const status = error.response.status;
          
          logDebug('changeMap', `Errore server (${status}) nel cambio mappa:`, serverError, true);
          logDebug('changeMap', 'Dettagli risposta:', error.response.data, true);
          
          // Per alcuni errori non ha senso riprovare
          if (status === 403) { // Forbidden - es. livello insufficiente
            logDebug('changeMap', 'Errore di autorizzazione, non riprovo', null, true);
            throw new Error(`Errore ${status}: ${serverError}`);
          }
          
          if (status === 404) { // Not Found - es. mappa non esistente
            logDebug('changeMap', 'Risorsa non trovata, non riprovo', null, true);
            throw new Error(`Errore ${status}: ${serverError}`);
          }
        } else if (error.request) {
          // La richiesta è stata fatta ma non abbiamo ricevuto risposta
          logDebug('changeMap', 'Nessuna risposta dal server nel cambio mappa:', error.request, true);
        } else {
          // Errore durante l'impostazione della richiesta
          logDebug('changeMap', 'Errore nella configurazione della richiesta di cambio mappa:', error.message, true);
        }
        
        // Incrementa il contatore dei tentativi e riprova solo se è un errore di rete o 500
        retryCount++;
        if (retryCount <= MAX_RETRIES) {
          logDebug('changeMap', `Riprovo il cambio mappa tra 1 secondo...`);
          await new Promise(resolve => setTimeout(resolve, 1000)); // Attesa di 1 secondo
        }
      }
    }
    
    // Se arriviamo qui, tutti i tentativi sono falliti
    logDebug('changeMap', `Cambio mappa fallito dopo ${MAX_RETRIES+1} tentativi`, null, true);
    throw lastError || new Error('Impossibile cambiare mappa dopo multipli tentativi');
  },
  
  /**
   * Ottiene lo stato della scelta mappa
   * @param {string} sessionId - ID della sessione
   * @returns {Promise<Object>} - Stato della scelta mappa
   */
  getMapSelectState: async (sessionId) => {
    logDebug('getMapSelectState', `Richiesta stato scelta mappa: sessionId=${sessionId}`);
    
    try {
      const response = await axios.get(`${API_URL}/game/scelta_mappa/stato`, {
        params: { id_sessione: sessionId }
      });
      
      if (response.data && response.data.success) {
        return response.data.stato || {};
      } else {
        const errMsg = response.data?.error || 'Impossibile recuperare lo stato scelta mappa';
        logDebug('getMapSelectState', errMsg, response.data, true);
        throw new Error(errMsg);
      }
    } catch (error) {
      logDebug('getMapSelectState', 'Errore nel recupero dello stato scelta mappa:', error, true);
      throw error;
    }
  },
  
  /**
   * Ottiene i dati della mappa corrente (per rendering)
   * @param {string} sessionId - ID della sessione
   * @param {string} mapId - ID della mappa (opzionale)
   * @returns {Promise<Object>} - Dati della mappa
   */
  getMapData: async (sessionId, mapId = null) => {
    try {
      logDebug('getMapData', `Richiesta dati mappa: sessionId=${sessionId}, mapId=${mapId}`);
      
      if (!sessionId) {
        throw new Error('ID sessione mancante per la richiesta dei dati della mappa');
      }
      
      if (!mapId) {
        throw new Error('ID mappa mancante per la richiesta dei dati');
      }
      
      const response = await axios.get(`${API_URL}/mappa/dati`, {
        params: {
          id_sessione: sessionId,
          id_mappa: mapId
        },
        timeout: 8000 // Timeout di 8 secondi per la richiesta
      });
      
      logDebug('getMapData', 'Risposta API mappa/dati status:', response.status);
      logDebug('getMapData', 'Risposta API mappa/dati:', response.data);
      
      if (!response.data.successo) {
        const errorMsg = response.data.errore || 'Errore sconosciuto nel recupero dei dati della mappa';
        logDebug('getMapData', errorMsg, null, true);
        throw new Error(errorMsg);
      }
      
      if (!response.data.mappa) {
        const errorMsg = 'Dati mappa non presenti nella risposta del server';
        logDebug('getMapData', errorMsg, null, true);
        throw new Error(errorMsg);
      }
      
      // Verifica che i dati della mappa contengano le proprietà necessarie
      const mapData = response.data.mappa;
      if (!mapData.larghezza || !mapData.altezza || !mapData.griglia) {
        logDebug('getMapData', 'Dati mappa incompleti:', mapData, true);
        throw new Error('Dati mappa non validi: mancano larghezza, altezza o griglia');
      }
      
      // Log delle dimensioni della mappa per debug
      logDebug('getMapData', `Dati mappa validi ricevuti: larghezza=${mapData.larghezza}, altezza=${mapData.altezza}`);
      
      return mapData;
    } catch (error) {
      // Gestire gli errori in modo più granulare
      if (error.response) {
        // Errore del server con codice di stato
        const status = error.response.status;
        const serverError = error.response.data?.errore || error.response.data?.error || 'Errore server sconosciuto';
        
        logDebug('getMapData', `Errore server (${status}) nel recupero dati mappa:`, serverError, true);
        logDebug('getMapData', 'Risposta del server:', error.response.data, true);
        
        throw new Error(`Errore ${status}: ${serverError}`);
      } else if (error.request) {
        // Errore di connessione o timeout
        logDebug('getMapData', 'Nessuna risposta dal server nel recupero dati mappa', error.request, true);
        throw new Error(`Nessuna risposta dal server: ${error.message}`);
      } else {
        // Errore pre-richiesta
        logDebug('getMapData', 'Errore nel recupero dei dati della mappa:', error.message, true);
        throw error;
      }
    }
  },
  
  /**
   * Muove il giocatore sulla mappa
   * @param {string} sessionId - ID della sessione
   * @param {number} x - Coordinata X
   * @param {number} y - Coordinata Y
   * @returns {Promise<Object>} - Risposta dal server
   */
  movePlayer: async (sessionId, x, y) => {
    try {
      const response = await axios.post(`${API_URL}/mappa/muovi_giocatore`, {
        id_sessione: sessionId,
        pos_x: x,
        pos_y: y
      });
      
      if (response.data && response.data.success) {
        return {
          success: true,
          position: response.data.posizione,
          events: response.data.eventi || []
        };
      } else {
        throw new Error(response.data?.error || 'Impossibile muovere il giocatore');
      }
    } catch (error) {
      console.error('Errore nel movimento del giocatore:', error);
      throw error;
    }
  },
  
  /**
   * Controlla e ripara problemi comuni nei dati della mappa
   * @param {Object} mapData - Dati della mappa da controllare
   * @returns {Object} - Dati della mappa riparati
   */
  validateAndFixMapData: (mapData) => {
    if (!mapData) {
      logDebug('validateAndFixMapData', 'Dati mappa non validi: null o undefined', null, true);
      return null;
    }
    
    const fixedData = { ...mapData };
    let hasWarnings = false;
    
    // Controllo delle dimensioni
    if (!fixedData.larghezza || typeof fixedData.larghezza !== 'number') {
      logDebug('validateAndFixMapData', `Larghezza mappa non valida: ${fixedData.larghezza}`, null, true);
      if (fixedData.griglia && fixedData.griglia[0]) {
        fixedData.larghezza = fixedData.griglia[0].length;
        logDebug('validateAndFixMapData', `Larghezza mappa impostata a ${fixedData.larghezza} dalla griglia`);
        hasWarnings = true;
      } else {
        fixedData.larghezza = 10; // Valore predefinito
        logDebug('validateAndFixMapData', `Larghezza mappa impostata al valore predefinito ${fixedData.larghezza}`);
        hasWarnings = true;
      }
    }
    
    if (!fixedData.altezza || typeof fixedData.altezza !== 'number') {
      logDebug('validateAndFixMapData', `Altezza mappa non valida: ${fixedData.altezza}`, null, true);
      if (fixedData.griglia) {
        fixedData.altezza = fixedData.griglia.length;
        logDebug('validateAndFixMapData', `Altezza mappa impostata a ${fixedData.altezza} dalla griglia`);
        hasWarnings = true;
      } else {
        fixedData.altezza = 10; // Valore predefinito
        logDebug('validateAndFixMapData', `Altezza mappa impostata al valore predefinito ${fixedData.altezza}`);
        hasWarnings = true;
      }
    }
    
    // Controllo della griglia
    if (!fixedData.griglia || !Array.isArray(fixedData.griglia)) {
      logDebug('validateAndFixMapData', 'Griglia mappa non valida o mancante', null, true);
      // Crea una griglia vuota
      fixedData.griglia = Array(fixedData.altezza).fill().map(() => Array(fixedData.larghezza).fill(0));
      logDebug('validateAndFixMapData', `Creata griglia predefinita ${fixedData.altezza}x${fixedData.larghezza}`);
      hasWarnings = true;
    }
    
    // Controllo oggetti
    if (!fixedData.oggetti) {
      fixedData.oggetti = {};
      hasWarnings = true;
    }
    
    // Controllo NPG
    if (!fixedData.npg) {
      fixedData.npg = {};
      hasWarnings = true;
    }
    
    if (hasWarnings) {
      logDebug('validateAndFixMapData', 'Dati mappa riparati con warning', fixedData);
    } else {
      logDebug('validateAndFixMapData', 'Dati mappa validati senza problemi');
    }
    
    return fixedData;
  }
};

export default mapApi; 