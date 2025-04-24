import React from 'react';

/**
 * Componente per visualizzare le informazioni del personaggio
 */
const GameCharacterInfo = ({ player }) => {
  if (!player) {
    return (
      <div className="character-info panel">
        <h3>Personaggio</h3>
        <p>Dati personaggio non disponibili</p>
      </div>
    );
  }

  // Funzione per estrarre string da proprietà che potrebbero essere oggetti
  const extractStringValue = (value, property = 'nome') => {
    if (value === null || value === undefined) return 'Sconosciuto';
    if (typeof value === 'string') return value;
    if (typeof value === 'object' && value !== null && value[property]) {
      return value[property];
    }
    return String(value);
  };

  return (
    <div className="character-info panel">
      <h3>Personaggio</h3>
      
      <div className="info-row">
        <span className="info-label">Nome:</span>
        <span className="info-value">{extractStringValue(player.name)}</span>
      </div>
      
      <div className="info-row">
        <span className="info-label">Classe:</span>
        <span className="info-value">{extractStringValue(player.class)}</span>
      </div>
      
      <div className="info-row">
        <span className="info-label">Livello:</span>
        <span className="info-value">{player.level || 1}</span>
      </div>
      
      <div className="info-row">
        <span className="info-label">Salute:</span>
        <div className="health-bar">
          <div 
            className="health-fill" 
            style={{ 
              width: `${player.currentHP / player.maxHP * 100}%`,
              backgroundColor: getHealthColor(player.currentHP, player.maxHP)
            }}
          ></div>
          <span className="health-text">
            {player.currentHP || 0}/{player.maxHP || 100}
          </span>
        </div>
      </div>
      
      {player.stats && (
        <div className="character-stats">
          <h4>Statistiche</h4>
          
          <div className="stats-grid">
            {Object.entries(player.stats).map(([stat, value]) => (
              <div className="stat-item" key={stat}>
                <span className="stat-name">{formatStatName(stat)}:</span>
                <span className="stat-value">{typeof value === 'object' ? extractStringValue(value) : value}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Formatta il nome della statistica
 */
const formatStatName = (stat) => {
  const statNames = {
    strength: 'Forza',
    dexterity: 'Destrezza',
    constitution: 'Costituzione',
    intelligence: 'Intelligenza',
    wisdom: 'Saggezza',
    charisma: 'Carisma',
    str: 'Forza',
    dex: 'Destrezza',
    con: 'Costituzione',
    int: 'Intelligenza',
    wis: 'Saggezza',
    cha: 'Carisma'
  };
  
  return statNames[stat.toLowerCase()] || stat;
};

/**
 * Determina il colore della barra della salute in base alla percentuale
 */
const getHealthColor = (current, max) => {
  const percentage = (current / max) * 100;
  
  if (percentage <= 25) {
    return '#ff4444'; // Rosso
  } else if (percentage <= 50) {
    return '#ffaa44'; // Arancione
  } else if (percentage <= 75) {
    return '#ffff44'; // Giallo
  } else {
    return '#44ff44'; // Verde
  }
};

export default GameCharacterInfo; 