/**
 * Riduttore per la gestione della sessione di gioco
 * @param {Object} state - Stato corrente
 * @param {Object} action - Azione da eseguire
 * @returns {Object} - Nuovo stato
 */
export default function sessionReducer(state, action) {
  switch (action.type) {
    case 'SET_SESSION':
      return { 
        ...state, 
        sessionId: action.payload 
      };
      
    // Azioni relative alla sessione
    default:
      return state;
  }
} 