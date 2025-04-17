import axios from 'axios';

const API_URL = 'http://localhost:5000';

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
    try {
      const response = await axios.get(`${API_URL}/game/scelta_mappa/liste_mappe`, {
        params: { id_sessione: sessionId }
      });
      
      console.log("Risposta API scelta_mappa/liste_mappe:", response.data);
      
      if (response.data && response.data.success) {
        return {
          maps: response.data.mappe || {},
          currentMap: response.data.mappa_corrente
        };
      } else {
        throw new Error(response.data?.error || 'Impossibile recuperare le mappe');
      }
    } catch (error) {
      console.error('Errore nel recupero delle mappe:', error);
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
    try {
      const response = await axios.post(`${API_URL}/game/scelta_mappa/cambia_mappa`, {
        id_sessione: sessionId,
        id_mappa: mapId
      });
      
      if (response.data && response.data.success) {
        return {
          success: true,
          mapId: response.data.mappa,
          position: response.data.posizione
        };
      } else {
        throw new Error(response.data?.error || 'Impossibile cambiare mappa');
      }
    } catch (error) {
      console.error('Errore nel cambio mappa:', error);
      throw error;
    }
  },
  
  /**
   * Ottiene lo stato della scelta mappa
   * @param {string} sessionId - ID della sessione
   * @returns {Promise<Object>} - Stato della scelta mappa
   */
  getMapSelectState: async (sessionId) => {
    try {
      const response = await axios.get(`${API_URL}/game/scelta_mappa/stato`, {
        params: { id_sessione: sessionId }
      });
      
      if (response.data && response.data.success) {
        return response.data.stato || {};
      } else {
        throw new Error(response.data?.error || 'Impossibile recuperare lo stato scelta mappa');
      }
    } catch (error) {
      console.error('Errore nel recupero dello stato scelta mappa:', error);
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
      console.log(`Richiesta dati mappa: sessionId=${sessionId}, mapId=${mapId}`);
      
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
      
      console.log('Risposta API mappa/dati:', response.data);
      
      if (!response.data.successo) {
        throw new Error(response.data.errore || 'Errore sconosciuto nel recupero dei dati della mappa');
      }
      
      if (!response.data.mappa) {
        throw new Error('Dati mappa non presenti nella risposta del server');
      }
      
      return response.data.mappa;
    } catch (error) {
      // Gestisci errori di rete vs errori del server
      if (error.response) {
        // Il server ha risposto con un codice di errore
        const serverError = error.response.data?.errore || 'Errore dal server';
        const status = error.response.status;
        console.error(`Errore server (${status}): ${serverError}`);
        
        // Se abbiamo informazioni sulle mappe disponibili, mostriale
        if (error.response.data?.mappe_disponibili) {
          console.info('Mappe disponibili:', error.response.data.mappe_disponibili);
        }
        
        throw new Error(`Errore ${status}: ${serverError}`);
      } else if (error.request) {
        // La richiesta è stata fatta ma non abbiamo ricevuto risposta
        console.error('Nessuna risposta dal server:', error.request);
        throw new Error('Nessuna risposta dal server. Verifica la connessione.');
      } else {
        // Errore durante l'impostazione della richiesta
        console.error('Errore nel recupero dei dati della mappa:', error.message);
      }
      
      throw new Error('Impossibile recuperare i dati della mappa: ' + error.message);
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
  }
};

export default mapApi; 