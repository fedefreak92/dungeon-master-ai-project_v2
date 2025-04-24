import React from 'react';

/**
 * Componente per i controlli delle azioni di gioco
 */
const GameActions = ({ onMove, onInteract }) => {
  return (
    <div className="game-controls">
      <div className="movement-controls">
        <button onClick={() => onMove('up')}>Su</button>
        <div className="horizontal-controls">
          <button onClick={() => onMove('left')}>Sinistra</button>
          <button onClick={() => onMove('right')}>Destra</button>
        </div>
        <button onClick={() => onMove('down')}>Giù</button>
      </div>
      
      <div className="action-controls">
        <button onClick={onInteract}>Interagisci</button>
      </div>
    </div>
  );
};

export default GameActions; 