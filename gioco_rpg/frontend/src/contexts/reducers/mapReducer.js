/**
 * Riduttore per la gestione della mappa e delle entità
 * @param {Object} state - Stato corrente
 * @param {Object} action - Azione da eseguire
 * @returns {Object} - Nuovo stato
 */
export default function mapReducer(state, action) {
  switch (action.type) {
    case 'SET_MAP':
      return { 
        ...state, 
        currentMap: action.payload 
      };
    
    case 'SET_ENTITIES':
      return { 
        ...state, 
        entities: action.payload 
      };
    
    case 'UPDATE_ENTITY':
      return {
        ...state,
        entities: state.entities.map(entity => 
          entity.id === action.payload.id 
            ? { ...entity, ...action.payload.data }
            : entity
        )
      };
    
    case 'ADD_ENTITY':
      // Aggiungi solo se l'entità non esiste già
      if (state.entities.some(e => e.id === action.payload.id)) {
        return state;
      }
      
      return {
        ...state,
        entities: [...state.entities, action.payload]
      };
    
    case 'REMOVE_ENTITY':
      return {
        ...state,
        entities: state.entities.filter(entity => entity.id !== action.payload)
      };
    
    // Altre azioni relative alla mappa
    default:
      return state;
  }
} 