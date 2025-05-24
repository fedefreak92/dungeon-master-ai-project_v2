import React, { useState, useEffect } from 'react';
import useIOService from '../../hooks/useIOService';
import './GameInventory.css';

/**
 * Componente per visualizzare l'inventario del personaggio come popup
 */
const GameInventory = ({ inventory = [] }) => {
  const [selectedItem, setSelectedItem] = useState(null);
  const [filter, setFilter] = useState('tutti');
  const { inviaInput, inventario, mostraInventario, nascondiInventario } = useIOService();
  
  // Debug per tracciare l'apertura dell'inventario
  useEffect(() => {
    console.log('Stato inventario cambiato:', inventario.aperto ? 'APERTO' : 'CHIUSO');
  }, [inventario.aperto]);
  
  // Reset della selezione quando cambia l'inventario
  useEffect(() => {
    setSelectedItem(null);
  }, [inventory]);
  
  const handleItemSelect = (item) => {
    setSelectedItem(item);
  };
  
  const handleItemUse = () => {
    if (selectedItem) {
      // Invia l'azione al backend tramite socket.io
      inviaInput('inventory_action', selectedItem.id, { 
        action: 'use',
        item_id: selectedItem.id
      });
    }
  };
  
  const handleItemDrop = () => {
    if (selectedItem) {
      // Invia l'azione al backend tramite socket.io
      inviaInput('inventory_action', selectedItem.id, { 
        action: 'drop',
        item_id: selectedItem.id
      });
    }
  };
  
  const handleCloseInventory = () => {
    // Nascondi l'UI dell'inventario
    nascondiInventario();
    
    // Invia l'evento UI_INVENTORY_TOGGLE che è gestito da inventario_state.py
    inviaInput('ui_event', null, { 
      type: 'UI_INVENTORY_TOGGLE' 
    });
    
    console.log('Richiesta di disattivazione stato inventario inviata al backend (UI_INVENTORY_TOGGLE)');
  };

  // Se l'inventario non è aperto, non renderizzare nulla
  if (!inventario.aperto) {
    console.log('Inventario non visibile (inventario.aperto = false)');
    return null;
  }

  console.log('Rendering pannello inventario (inventario.aperto = true)');

  // Combina gli oggetti dall'inventario del giocatore e quelli passati come prop
  const mergedInventory = [...inventory, ...(inventario.items || [])];
  
  // Compatibilità con i nomi di campo: nel backend usiamo 'nome' invece di 'name', ecc.
  const normalizedInventory = mergedInventory.map(item => ({
    ...item,
    id: item.id || `item-${Math.random().toString(36).substr(2, 9)}`,
    name: item.nome || item.name || (typeof item === 'string' ? item : 'Oggetto sconosciuto'),
    description: item.descrizione || item.description || 'Nessuna descrizione disponibile.',
    quantity: item.quantita || item.quantity || 1,
    type: item.tipo || item.type || 'default',
    usable: item.usabile || item.usable || false,
    icon: item.icona || item.icon
  }));
  
  // Elimina duplicati (oggetti con lo stesso ID o nome)
  const uniqueInventory = normalizedInventory.reduce((acc, current) => {
    const isDuplicate = acc.find(item => 
      (item.id && current.id && item.id === current.id) || 
      (item.name && current.name && item.name === current.name)
    );
    if (!isDuplicate) {
      acc.push(current);
    }
    return acc;
  }, []);
  
  // Filtra l'inventario in base al tipo selezionato
  const filteredInventory = uniqueInventory.filter(item => {
    if (filter === 'tutti') return true;
    
    const itemType = (item.type || '').toLowerCase();
    if (filter === 'armi') return ['arma', 'weapon'].includes(itemType);
    if (filter === 'armature') return ['armatura', 'armor'].includes(itemType);
    if (filter === 'pozioni') return ['pozione', 'potion'].includes(itemType);
    if (filter === 'consumabili') return item.usable || ['pozione', 'potion', 'cibo', 'food'].includes(itemType);
    
    return itemType === filter;
  });
  
  // Renderizza il pannello dell'inventario quando è aperto
  return (
    <div className="inventory-popup-overlay">
      <div className="inventory-popup-panel">
        <div className="inventory-header">
          <h3>Inventario</h3>
          <button 
            className="close-inventory-button"
            onClick={handleCloseInventory}
          >
            ✕
          </button>
        </div>
        
        <div className="inventory-filters">
          <button 
            className={`filter-button ${filter === 'tutti' ? 'active' : ''}`}
            onClick={() => setFilter('tutti')}
          >
            Tutti
          </button>
          <button 
            className={`filter-button ${filter === 'armi' ? 'active' : ''}`}
            onClick={() => setFilter('armi')}
          >
            Armi
          </button>
          <button 
            className={`filter-button ${filter === 'armature' ? 'active' : ''}`}
            onClick={() => setFilter('armature')}
          >
            Armature
          </button>
          <button 
            className={`filter-button ${filter === 'consumabili' ? 'active' : ''}`}
            onClick={() => setFilter('consumabili')}
          >
            Consumabili
          </button>
        </div>
        
        {filteredInventory.length === 0 ? (
          <p className="empty-inventory">
            {uniqueInventory.length === 0 ? "Inventario vuoto" : "Nessun oggetto in questa categoria"}
          </p>
        ) : (
          <div className="inventory-content">
            <div className="items-list">
              {filteredInventory.map((item, index) => (
                <div 
                  className={`inventory-item ${selectedItem && selectedItem.id === item.id ? 'selected' : ''}`}
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
                <p className="item-description">{selectedItem.description}</p>
                
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
    // Aggiunti nomi di tipo in italiano
    arma: '#ff7700',
    armatura: '#4444ff',
    pozione: '#ff44ff',
    pergamena: '#ffff44',
    chiave: '#44ffff',
    missione: '#ff4444',
    default: '#aaaaaa'
  };
  
  return colors[type?.toLowerCase()] || colors.default;
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
    // Aggiunti nomi di tipo in italiano
    arma: '⚔️',
    armatura: '🛡️',
    pozione: '🧪',
    pergamena: '📜',
    chiave: '🔑',
    missione: '❗',
    default: '📦'
  };
  
  return icons[type?.toLowerCase()] || icons.default;
};

export default GameInventory; 