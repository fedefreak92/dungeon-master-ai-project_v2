/**
 * Riduttore per la gestione dei dati del giocatore
 * @param {Object} state - Stato corrente
 * @param {Object} action - Azione da eseguire
 * @returns {Object} - Nuovo stato
 */
export default function playerReducer(state, action) {
  switch (action.type) {
    case 'SET_PLAYER':
      return { 
        ...state, 
        player: action.payload 
      };
    
    case 'SET_CLASSES':
      return { 
        ...state, 
        classes: action.payload 
      };
    
    case 'UPDATE_PLAYER_HEALTH':
      if (!state.player) return state;
      
      return {
        ...state,
        player: {
          ...state.player,
          hp: action.payload
        }
      };
    
    case 'UPDATE_PLAYER_STATS':
      if (!state.player) return state;
      
      return {
        ...state,
        player: {
          ...state.player,
          ...action.payload
        }
      };
    
    // Altre azioni relative al giocatore
    default:
      return state;
  }
} 