import playerReducer from './playerReducer';
import sessionReducer from './sessionReducer';
import mapReducer from './mapReducer';
import uiReducer from './uiReducer';

// Stato iniziale globale del gioco
export const initialState = {
  // Sessione di gioco
  sessionId: null,
  
  // Dati giocatore
  player: null,
  classes: [],
  
  // Dati mappa
  currentMap: null,
  entities: [],
  
  // UI state
  gameState: 'start-screen', // 'init', 'start-screen', 'map-select', 'map', 'combat', 'dialog'
  loading: false,
  error: null,
  saveSuccess: null
};

/**
 * Riduttore principale che combina tutti i sotto-riduttori
 * @param {Object} state - Stato corrente
 * @param {Object} action - Azione da eseguire
 * @returns {Object} - Nuovo stato
 */
export default function gameReducer(state, action) {
  // Prima applica i sotto-riduttori specifici per dominio
  const sessionState = sessionReducer(state, action);
  const playerState = playerReducer(sessionState, action);
  const mapState = mapReducer(playerState, action);
  
  // Infine applica il riduttore dell'interfaccia utente
  return uiReducer(mapState, action);
} 