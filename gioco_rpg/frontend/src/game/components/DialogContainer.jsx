import React from 'react';

/**
 * Componente per visualizzare e gestire i dialoghi nel gioco
 */
const DialogContainer = ({ dialog, onSelectOption }) => {
  if (!dialog) return null;
  
  const { 
    speaker, 
    content, 
    options = [] 
  } = dialog;
  
  return (
    <div className="dialog-container">
      {speaker && (
        <h3 className="dialog-speaker">{speaker}</h3>
      )}
      
      <div className="dialog-content">
        <p>{content}</p>
      </div>
      
      {options.length > 0 && (
        <div className="dialog-options">
          {options.map((option, index) => (
            <button 
              key={index} 
              className="dialog-option"
              onClick={() => onSelectOption(index)}
            >
              {option.text}
            </button>
          ))}
        </div>
      )}
      
      {options.length === 0 && (
        <button 
          className="dialog-continue"
          onClick={() => onSelectOption(-1)}
        >
          Continua
        </button>
      )}
    </div>
  );
};

export default DialogContainer; 