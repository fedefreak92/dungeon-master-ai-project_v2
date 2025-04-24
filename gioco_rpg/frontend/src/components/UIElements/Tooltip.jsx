import React from 'react';
import useIOService from '../../hooks/useIOService';
import './Tooltip.css';

/**
 * Componente per visualizzare tooltip nel gioco
 */
const Tooltip = () => {
  const { tooltip } = useIOService();

  // Se non c'è un tooltip attivo, non mostrare nulla
  if (!tooltip) {
    return null;
  }

  // Calcola lo stile di posizionamento
  const tooltipStyle = {
    left: `${tooltip.posizione[0]}px`,
    top: `${tooltip.posizione[1]}px`,
  };

  return (
    <div className="tooltip" style={tooltipStyle}>
      {tooltip.testo}
    </div>
  );
};

export default Tooltip; 