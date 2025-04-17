/**
 * Riduttore per la gestione dello stato dell'interfaccia utente
 * @param {Object} state - Stato corrente
 * @param {Object} action - Azione da eseguire
 * @returns {Object} - Nuovo stato
 */
export default function uiReducer(state, action) {
  switch (action.type) {
    case 'SET_GAME_STATE':
      return { 
        ...state, 
        gameState: action.payload 
      };
    
    case 'SET_LOADING':
      return { 
        ...state, 
        loading: action.payload 
      };
    
    case 'SET_ERROR':
      return { 
        ...state, 
        error: action.payload 
      };
    
    case 'CLEAR_ERROR':
      return { 
        ...state, 
        error: null 
      };
    
    case 'SET_SAVE_SUCCESS':
      return { 
        ...state, 
        saveSuccess: action.payload 
      };
    
    case 'CLEAR_SAVE_SUCCESS':
      return { 
        ...state, 
        saveSuccess: null 
      };
    
    // Altre azioni relative all'UI
    default:
      return state;
  }
} 