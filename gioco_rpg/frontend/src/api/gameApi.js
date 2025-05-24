import axios from 'axios';

// Usa percorsi relativi invece di URL assoluto
const API_URL = '';

/**
 * Funzione di utilità per gestire i tentativi multipli
 * @param {Function} fn - Funzione da eseguire con retry
 * @param {number} maxRetries - Numero massimo di tentativi
 * @param {number} delay - Ritardo tra i tentativi in ms
 * @returns {Promise<any>} - Risultato della funzione
 */
const withRetry = async (fn, maxRetries = 3, delay = 1000) => {
  let lastError;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      console.log(`Tentativo ${attempt}/${maxRetries}`);
      return await fn();
    } catch (error) {
      console.warn(`Tentativo ${attempt} fallito:`, error.message);
      lastError = error;
      
      if (attempt < maxRetries) {
        // Attendi prima del prossimo tentativo (ritardo esponenziale)
        await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, attempt - 1)));
      }
    }
  }
  
  // Se arriviamo qui, tutti i tentativi sono falliti
  throw lastError;
};

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
    return withRetry(async () => {
      try {
        console.log(`Avvio nuova partita: nome=${playerName}, classe=${playerClass}`);
        const response = await axios.post(`${API_URL}/game/session/inizia`, {
          nome_personaggio: playerName,
          classe: playerClass,
          modalita_grafica: true, // Abilita la modalità grafica
          force_check_mappe: true // Forza il controllo delle mappe
        });
        
        // Verifica sia success che successo per retrocompatibilità
        if (response.data && (response.data.success || response.data.successo)) {
          console.log('Sessione iniziata con successo:', response.data);
          const sessionId = response.data.session_id || response.data.id_sessione; // Prendi il session_id
          if (sessionId) {
            localStorage.setItem('authToken', sessionId); // SALVA IN localStorage
            console.log('[gameApi.startNewGame] Session ID salvato in localStorage come authToken:', sessionId);
          } else {
            console.error('[gameApi.startNewGame] ERRORE: session_id non trovato nella risposta del server dopo startNewGame.');
          }
          return response.data;
        } else {
          console.error('Errore nella risposta del server:', response.data);
          throw new Error(response.data?.error || response.data?.errore || 'Risposta del server non valida');
        }
      } catch (error) {
        console.error('Errore nell\'inizializzazione del gioco:', error);
        throw error;
      }
    }, 3, 1500); // 3 tentativi con 1.5 secondi di ritardo iniziale
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
      if (!sessionId) {
        throw new Error('ID sessione non trovato nella risposta');
      }
      localStorage.setItem('authToken', sessionId); // SALVA IN localStorage
      console.log(`[gameApi.loadSavedGame] Session ID (${sessionId}) salvato in localStorage come authToken.`);
      
      console.log(`Sessione temporanea creata con ID: ${sessionId}`);
      
      // Attesa prima di procedere con il caricamento
      await new Promise(resolve => setTimeout(resolve, 300));
      
      // Poi carica il salvataggio nella sessione
      console.log(`Caricamento del salvataggio '${saveFileName}' nella sessione ${sessionId}`);
      const loadResponse = await axios.post(`${API_URL}/game/save/carica`, {
        id_sessione: sessionId,
        nome_salvataggio: saveFileName
      });
      
      // Verifica sia success che successo per retrocompatibilità
      if (!loadResponse.data || !(loadResponse.data.success || loadResponse.data.successo)) {
        const errorMsg = loadResponse.data?.error || loadResponse.data?.errore || 'Errore nel caricamento';
        console.error('Errore durante il caricamento:', errorMsg);
        throw new Error(errorMsg);
      }
      
      console.log('Salvataggio caricato con successo:', loadResponse.data);
      
      // Estrai le informazioni sul giocatore se presenti
      const playerInfo = loadResponse.data.player_info || {};
      
      // Attesa breve per permettere al server di completare le operazioni
      await new Promise(resolve => setTimeout(resolve, 300));
      
      // Richiedi informazioni aggiornate sul giocatore per verificare il caricamento
      try {
        const playerResponse = await axios.get(`${API_URL}/game/entity/player`, {
          params: { id_sessione: sessionId }
        });
        console.log('Informazioni giocatore aggiornate:', playerResponse.data);
      } catch (playerError) {
        console.warn('Impossibile ottenere informazioni aggiornate sul giocatore:', playerError);
        // Continuiamo comunque, potrebbe essere un errore non bloccante
      }
      
      return {
        ...loadResponse.data,
        session_id: sessionId,
        player_info: playerInfo
      };
    } catch (error) {
      console.error('Errore nel caricamento del salvataggio:', error);
      // Rilanciamo l'errore con dettagli
      if (error.response) {
        // Errore dal server con risposta
        throw new Error(`Errore ${error.response.status}: ${error.response.data?.errore || error.message}`);
      } else if (error.request) {
        // Nessuna risposta ricevuta
        throw new Error('Nessuna risposta dal server. Verificare la connessione.');
      } else {
        // Errore imprevisto
        throw error;
      }
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
      console.log(`[playerApi] Richiesta info giocatore con sessionId: ${sessionId}`);
      const response = await axios.get(`${API_URL}/game/entity/player`, {
        params: { id_sessione: sessionId }
      });
      
      console.log(`[playerApi] Risposta server completa:`, response.data);
      
      // Verifica sia success che successo per retrocompatibilità
      if (response.data && (response.data.success || response.data.successo)) {
        console.log(`[playerApi] Dati giocatore ricevuti dal server:`, response.data.player);
        
        // Log specifico per HP
        if (response.data.player) {
          const player = response.data.player;
          console.log(`[playerApi] HP ricevuti dal server: ${player.hp}/${player.hp_max}`);
          console.log(`[playerApi] Classe giocatore: ${typeof player.classe === 'object' ? player.classe.id : player.classe}`);
          
          // Controlla tutti i valori correlati agli HP
          console.log(`[playerApi] Tutti i valori HP disponibili:`, {
            hp: player.hp,
            hp_max: player.hp_max,
            currentHP: player.currentHP,
            maxHP: player.maxHP
          });
          
          // Controlla se il formato risponde allo schema aspettato
          if (player.hp === 100 && player.hp_max === 100) {
            console.warn(`[playerApi] ATTENZIONE: Il server sta restituendo HP 100/100, che potrebbe essere un valore di default hardcoded!`);
          } else {
            console.log(`[playerApi] HP ricevuto correttamente: ${player.hp}/${player.hp_max}`);
          }
        }
        
        return response.data.player;
      } else {
        console.error(`[playerApi] Errore nella risposta del server:`, response.data);
        throw new Error(response.data?.error || response.data?.errore || 'Impossibile recuperare i dati del giocatore');
      }
    } catch (error) {
      console.error('[playerApi] Errore nel recupero delle informazioni del giocatore:', error);
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