import React, { useEffect } from 'react';

/**
 * Componente per visualizzare le informazioni del personaggio
 */
const GameCharacterInfo = ({ player }) => {
  useEffect(() => {
    if (player) {
      console.log(`GameCharacterInfo: Ricevuti valori HP dal player prop: ${player.hp}/${player.hp_max}`);
    }
  }, [player]);

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

  // Compatibilità con i campi dell'API
  const playerName = player.nome || player.name || 'Sconosciuto';
  const playerClass = player.classe || player.class || 'Sconosciuto';
  const playerLevel = player.livello || player.level || 1;
  
  // Gestione più robusta dei punti vita
  let currentHP = player.hp;
  let maxHP = player.hp_max;
  
  // Controlliamo se i valori sono validi o se dobbiamo usare alternative
  if (currentHP === undefined || currentHP === null) {
    currentHP = player.currentHP || 0;
  }
  
  if (maxHP === undefined || maxHP === null || maxHP === 0) {
    // Otteniamo la classe del giocatore per determinare valori appropriati
    const classeGiocatore = (() => {
      if (typeof playerClass === 'object') {
        return playerClass.id;
      }
      if (typeof playerClass === 'string') {
        // Rimuovi eventuali spazi e converti in minuscolo
        const classe = playerClass.trim().toLowerCase();
        // Se è solo "Sconosciuto", usiamo guerriero come fallback
        if (classe === 'sconosciuto') return 'guerriero';
        return classe;
      }
      return 'guerriero'; // Fallback predefinito
    })();
    
    // Valori di HP base per classe come fallback, allineati con il backend
    const hpBaseFallback = {
      'guerriero': 12,
      'mago': 6, 
      'ladro': 8,
      'chierico': 10
    }[classeGiocatore] || 10; // 10 è un valore ragionevole come ultimo fallback
    
    maxHP = player.maxHP || hpBaseFallback;
  }
  
  // IMPORTANTE: Impostiamo currentHP uguale a maxHP SOLO se è 0
  // Questo è il bug che causava la visualizzazione di 100/100
  if (maxHP > 0 && (currentHP === 0 || currentHP === null || currentHP === undefined)) {
    currentHP = maxHP;
    console.log(`GameCharacterInfo: HP inizializzati al valore massimo perché erano 0: ${currentHP}/${maxHP}`);
  } else {
    console.log(`GameCharacterInfo: Usando HP dal server: ${currentHP}/${maxHP}`);
  }
  
  // Ottieni le statistiche dal giusto campo
  const stats = player.statistiche || player.stats || {};

  return (
    <div className="character-info panel">
      <h3>Personaggio</h3>
      
      <div className="info-row">
        <span className="info-label">Nome:</span>
        <span className="info-value">{extractStringValue(playerName)}</span>
      </div>
      
      <div className="info-row">
        <span className="info-label">Classe:</span>
        <span className="info-value">{extractStringValue(playerClass)}</span>
      </div>
      
      <div className="info-row">
        <span className="info-label">Livello:</span>
        <span className="info-value">{playerLevel}</span>
      </div>
      
      <div className="info-row">
        <span className="info-label">Salute:</span>
        <div className="health-bar">
          <div 
            className="health-fill" 
            style={{ 
              width: `${maxHP ? ((currentHP / maxHP) * 100) : 0}%`,
              backgroundColor: getHealthColor(currentHP, maxHP)
            }}
          ></div>
          <span className="health-text">
            {currentHP}/{maxHP}
          </span>
        </div>
      </div>
      
      {stats && (
        <div className="character-stats">
          <h4>Statistiche</h4>
          
          <div className="stats-grid">
            {Object.entries(stats).map(([stat, value]) => (
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
    cha: 'Carisma',
    // Aggiunto supporto per le chiavi in italiano
    forza: 'Forza',
    destrezza: 'Destrezza',
    costituzione: 'Costituzione',
    intelligenza: 'Intelligenza',
    saggezza: 'Saggezza',
    carisma: 'Carisma'
  };
  
  return statNames[stat.toLowerCase()] || stat;
};

/**
 * Determina il colore della barra della salute in base alla percentuale
 */
const getHealthColor = (current, max) => {
  if (current <= 0 || max <= 0) return '#ff4444'; // Rosso per valori non validi
  
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