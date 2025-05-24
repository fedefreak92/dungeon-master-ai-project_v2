import React from 'react';
import { useGameState } from '../../hooks/useGameState';
import './GameActions.css';

/**
 * Componente che rappresenta i controlli del gioco
 */
const GameActions = ({ onMove, onInteract }) => {
  const { sendAction } = useGameState();

  return (
    <div className="game-actions-container">
      <div className="game-actions-compass">
        <button 
          onClick={() => onMove('up')} 
          className="compass-button north"
          title="Vai a nord"
        >
          N
        </button>
        
        <div className="compass-middle-row">
          <button 
            onClick={() => onMove('left')} 
            className="compass-button west"
            title="Vai a ovest"
          >
            O
          </button>
          
          <div className="compass-rose"></div>
          
          <button 
            onClick={() => onMove('right')} 
            className="compass-button east"
            title="Vai a est"
          >
            E
          </button>
        </div>
        
        <button 
          onClick={() => onMove('down')} 
          className="compass-button south"
          title="Vai a sud"
        >
          S
        </button>
      </div>
      
      <button 
        onClick={onInteract} 
        className="interact-button highlight-button"
        title="Interagisci con oggetti o personaggi nelle vicinanze"
      >
        <span className="interact-icon">✦</span>
        <span className="interact-text">Interagisci</span>
      </button>
    </div>
  );
};

export default GameActions; 