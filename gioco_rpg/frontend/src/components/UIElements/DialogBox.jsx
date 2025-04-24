import React from 'react';
import useIOService from '../../hooks/useIOService';
import './DialogBox.css';

/**
 * Componente per visualizzare finestre di dialogo nel gioco
 */
const DialogBox = () => {
  const { dialoghi, selezionaOpzioneDialogo } = useIOService();

  // Se non ci sono dialoghi attivi, non mostrare nulla
  if (!dialoghi || dialoghi.length === 0) {
    return null;
  }

  // Ottieni il dialogo più recente (quello in cima allo stack)
  const dialogoAttivo = dialoghi[dialoghi.length - 1];

  // Gestisci il click su un'opzione di dialogo
  const handleOptionClick = (index) => {
    selezionaOpzioneDialogo(dialogoAttivo.id, index);
  };

  return (
    <div className="dialog-overlay">
      <div className="dialog-box">
        <div className="dialog-header">
          <h3 className="dialog-title">{dialogoAttivo.titolo}</h3>
        </div>
        
        <div className="dialog-content">
          <p className="dialog-text">{dialogoAttivo.testo}</p>
        </div>
        
        {dialogoAttivo.opzioni && dialogoAttivo.opzioni.length > 0 ? (
          <div className="dialog-options">
            {dialogoAttivo.opzioni.map((opzione, index) => (
              <button
                key={`option-${index}`}
                className="dialog-option-btn"
                onClick={() => handleOptionClick(index)}
              >
                {opzione}
              </button>
            ))}
          </div>
        ) : (
          <div className="dialog-close">
            <button
              className="dialog-close-btn"
              onClick={() => selezionaOpzioneDialogo(dialogoAttivo.id, -1)}
            >
              Chiudi
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default DialogBox; 