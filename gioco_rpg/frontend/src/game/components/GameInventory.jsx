import React, { useState } from 'react';

/**
 * Componente per visualizzare l'inventario del personaggio
 */
const GameInventory = ({ inventory = [] }) => {
  const [selectedItem, setSelectedItem] = useState(null);
  
  const handleItemSelect = (item) => {
    setSelectedItem(item);
  };
  
  const handleItemUse = () => {
    if (selectedItem && selectedItem.usable) {
      // Qui dovrebbe essere implementata l'API per usare l'oggetto
      console.log(`Uso oggetto: ${selectedItem.name}`);
    }
  };
  
  const handleItemDrop = () => {
    if (selectedItem) {
      // Qui dovrebbe essere implementata l'API per eliminare l'oggetto
      console.log(`Eliminazione oggetto: ${selectedItem.name}`);
    }
  };
  
  return (
    <div className="inventory-panel panel">
      <h3>Inventario</h3>
      
      {inventory.length === 0 ? (
        <p className="empty-inventory">Inventario vuoto</p>
      ) : (
        <div className="inventory-content">
          <div className="items-list">
            {inventory.map((item, index) => (
              <div 
                className={`inventory-item ${selectedItem === item ? 'selected' : ''}`}
                key={`${item.id || item.name}-${index}`}
                onClick={() => handleItemSelect(item)}
              >
                <div className="item-icon" style={{ backgroundColor: getItemColor(item.type) }}>
                  {item.icon || getItemIcon(item.type)}
                </div>
                <div className="item-details">
                  <div className="item-name">{item.name}</div>
                  {item.quantity > 1 && (
                    <div className="item-quantity">x{item.quantity}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
          
          {selectedItem && (
            <div className="item-detail-panel">
              <h4>{selectedItem.name}</h4>
              <p className="item-description">{selectedItem.description || 'Nessuna descrizione disponibile.'}</p>
              
              <div className="item-actions">
                {selectedItem.usable && (
                  <button 
                    className="use-button"
                    onClick={handleItemUse}
                  >
                    Usa
                  </button>
                )}
                <button 
                  className="drop-button"
                  onClick={handleItemDrop}
                >
                  Elimina
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * Restituisce un colore in base al tipo di oggetto
 */
const getItemColor = (type) => {
  const colors = {
    weapon: '#ff7700',
    armor: '#4444ff',
    potion: '#ff44ff',
    scroll: '#ffff44',
    key: '#44ffff',
    quest: '#ff4444',
    default: '#aaaaaa'
  };
  
  return colors[type] || colors.default;
};

/**
 * Restituisce un'icona in base al tipo di oggetto
 */
const getItemIcon = (type) => {
  const icons = {
    weapon: '⚔️',
    armor: '🛡️',
    potion: '🧪',
    scroll: '📜',
    key: '🔑',
    quest: '❗',
    default: '📦'
  };
  
  return icons[type] || icons.default;
};

export default GameInventory; 