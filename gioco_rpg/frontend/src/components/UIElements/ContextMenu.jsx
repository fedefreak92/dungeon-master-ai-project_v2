import React from 'react';
import useIOService from '../../hooks/useIOService';
import './ContextMenu.css';

/**
 * Componente per visualizzare menu contestuali nel gioco
 */
const ContextMenu = () => {
  const { menuContestuale, selezionaOpzioneMenu, nascondiMenuContestuale } = useIOService();

  // Se non c'è un menu contestuale attivo, non mostrare nulla
  if (!menuContestuale) {
    return null;
  }

  // Gestisci il click su un'opzione del menu
  const handleOptionClick = (index) => {
    selezionaOpzioneMenu(index);
  };

  // Gestisci il click fuori dal menu per chiuderlo
  const handleBackdropClick = (e) => {
    if (e.currentTarget === e.target) {
      nascondiMenuContestuale();
    }
  };

  // Calcola lo stile di posizionamento
  const menuStyle = {
    left: `${menuContestuale.posizione[0]}px`,
    top: `${menuContestuale.posizione[1]}px`,
  };

  return (
    <div className="context-menu-overlay" onClick={handleBackdropClick}>
      <div className="context-menu" style={menuStyle}>
        <ul className="context-menu-list">
          {menuContestuale.opzioni.map((opzione, index) => (
            <li key={`option-${index}`} className="context-menu-item">
              <button 
                className="context-menu-button"
                onClick={() => handleOptionClick(index)}
              >
                {opzione}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default ContextMenu; 