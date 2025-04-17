import React, { createContext, useReducer, useContext } from 'react';
import gameReducer, { initialState } from './reducers/gameReducer';

// Crea il context
const GameContext = createContext();

/**
 * Provider che avvolge l'applicazione e fornisce lo stato del gioco
 */
export function GameProvider({ children }) {
  const [state, dispatch] = useReducer(gameReducer, initialState);
  
  return (
    <GameContext.Provider value={{ state, dispatch }}>
      {children}
    </GameContext.Provider>
  );
}

/**
 * Hook personalizzato per utilizzare il GameContext
 */
export function useGame() {
  return useContext(GameContext);
} 