import axios from 'axios';

const API_URL = 'http://localhost:5000';

/**
 * API per la gestione della sessione di gioco
 */
export const sessionApi = {
  /**
   * Inizia una nuova sessione di gioco
   * @param {string} playerName - Nome del personaggio
   * @param {string} playerClass - Classe del personaggio
   * @returns {Promise<Object>} - Risposta dal server
   */
  startNewGame: async (playerName, playerClass) => {
    try {
      const response = await axios.post(`${API_URL}/game/session/inizia`, {
        nome_personaggio: playerName,
        classe: playerClass,
        modalita_grafica: true // Abilita la modalità grafica
      });
      
      // Verifica sia success che successo per retrocompatibilità
      if (response.data && (response.data.success || response.data.successo)) {
        return response.data;
      } else {
        throw new Error(response.data?.error || response.data?.errore || 'Risposta del server non valida');
      }
    } catch (error) {
      console.error('Errore nell\'inizializzazione del gioco:', error);
      throw error;
    }
  },
  
  /**
   * Carica una partita salvata
   * @param {string} saveFileName - Nome del salvataggio
   * @returns {Promise<Object>} - Risposta dal server
   */
  loadSavedGame: async (saveFileName) => {
    try {
      // Prima crea una nuova sessione temporanea
      const initResponse = await axios.post(`${API_URL}/game/session/inizia`, {
        nome_personaggio: "Temporaneo",
        classe: "guerriero",
        modalita_grafica: true
      });
      
      // Verifica sia success che successo per retrocompatibilità
      if (!initResponse.data || !(initResponse.data.success || initResponse.data.successo)) {
        throw new Error('Impossibile creare sessione temporanea');
      }
      
      const sessionId = initResponse.data.session_id || initResponse.data.id_sessione;
      
      // Poi carica il salvataggio nella sessione
      const loadResponse = await axios.post(`${API_URL}/game/save/carica`, {
        id_sessione: sessionId,
        nome_salvataggio: saveFileName
      });
      
      // Verifica sia success che successo per retrocompatibilità
      if (!loadResponse.data || !(loadResponse.data.success || loadResponse.data.successo)) {
        throw new Error(loadResponse.data?.error || loadResponse.data?.errore || 'Errore nel caricamento');
      }
      
      return {
        ...loadResponse.data,
        session_id: sessionId
      };
    } catch (error) {
      console.error('Errore nel caricamento del salvataggio:', error);
      throw error;
    }
  }
};

/**
 * API per la gestione del salvataggio
 */
export const saveApi = {
  /**
   * Ottiene la lista dei salvataggi disponibili
   * @returns {Promise<Array>} - Lista dei salvataggi
   */
  getSaveGames: async () => {
    try {
      const response = await axios.get(`${API_URL}/game/save/elenco`);
      
      // Verifica sia success che successo per retrocompatibilità
      if (response.data && (response.data.success || response.data.successo)) {
        return response.data.salvataggi || [];
      } else {
        throw new Error(response.data?.error || response.data?.errore || 'Risposta del server non valida');
      }
    } catch (error) {
      console.error('Errore nel recupero dei salvataggi:', error);
      throw error;
    }
  },
  
  /**
   * Salva la partita in corso
   * @param {string} sessionId - ID della sessione
   * @param {string} saveName - Nome del salvataggio (opzionale)
   * @returns {Promise<Object>} - Risposta dal server
   */
  saveGame: async (sessionId, saveName = null) => {
    try {
      const saveResponse = await axios.post(`${API_URL}/game/save/salva`, {
        id_sessione: sessionId,
        nome_salvataggio: saveName
      });
      
      // Verifica sia success che successo per retrocompatibilità
      if (saveResponse.data && (saveResponse.data.success || saveResponse.data.successo)) {
        return saveResponse.data;
      } else {
        throw new Error(saveResponse.data?.error || saveResponse.data?.errore || 'Errore nel salvataggio');
      }
    } catch (error) {
      console.error('Errore nel salvataggio:', error);
      throw error;
    }
  }
};

/**
 * API per le informazioni sull'entità giocatore
 */
export const playerApi = {
  /**
   * Recupera le informazioni sul giocatore
   * @param {string} sessionId - ID della sessione
   * @returns {Promise<Object>} - Dati del giocatore
   */
  getPlayerInfo: async (sessionId) => {
    try {
      const response = await axios.get(`${API_URL}/game/entity/player`, {
        params: { id_sessione: sessionId }
      });
      
      // Verifica sia success che successo per retrocompatibilità
      if (response.data && (response.data.success || response.data.successo)) {
        return response.data.player;
      } else {
        throw new Error(response.data?.error || response.data?.errore || 'Impossibile recuperare i dati del giocatore');
      }
    } catch (error) {
      console.error('Errore nel recupero delle informazioni del giocatore:', error);
      throw error;
    }
  }
};

/**
 * API per le classi disponibili
 */
export const classesApi = {
  /**
   * Recupera le classi disponibili
   * @returns {Promise<Array>} - Lista delle classi disponibili
   */
  getAvailableClasses: async () => {
    try {
      const response = await axios.get(`${API_URL}/classes`);
      
      // Verifica sia success che successo per retrocompatibilità
      if (response.data && (response.data.success || response.data.successo)) {
        return response.data.classi || [];
      } else {
        throw new Error(response.data?.error || response.data?.errore || 'Impossibile recuperare le classi');
      }
    } catch (error) {
      console.error('Errore nel recupero delle classi:', error);
      throw error;
    }
  }
}; 