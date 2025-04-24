import React from 'react';
import useIOService from '../../hooks/useIOService';
import './Inventory.css';

/**
 * Componente per visualizzare l'inventario del giocatore
 */
const Inventory = () => {
  const { inventario, nascondiInventario, inviaInput } = useIOService();

  // Se l'inventario non è aperto, non mostrare nulla
  if (!inventario.aperto) {
    return null;
  }

  // Gestisci il click su un oggetto dell'inventario
  const handleItemClick = (item, index) => {
    inviaInput('inventory_action', item.id, { 
      action: 'select',
      item_id: item.id,
      item_index: index
    });
  };

  // Gestisci il click per usare un oggetto
  const handleUseItem = (item) => {
    inviaInput('inventory_action', item.id, { 
      action: 'use',
      item_id: item.id
    });
  };

  // Gestisci il click per eliminare un oggetto
  const handleDropItem = (item) => {
    inviaInput('inventory_action', item.id, { 
      action: 'drop',
      item_id: item.id
    });
  };

  return (
    <div className="inventory-overlay">
      <div className="inventory-container">
        <div className="inventory-header">
          <h2 className="inventory-title">Inventario</h2>
          <span className="inventory-capacity">
            {inventario.items.length} / {inventario.capacity}
          </span>
          <button 
            className="inventory-close"
            onClick={nascondiInventario}
          >
            ×
          </button>
        </div>
        
        <div className="inventory-content">
          {inventario.items.length === 0 ? (
            <div className="inventory-empty">
              <p>Il tuo inventario è vuoto</p>
            </div>
          ) : (
            <div className="inventory-grid">
              {inventario.items.map((item, index) => (
                <div 
                  key={`item-${item.id || index}`}
                  className="inventory-item"
                  onClick={() => handleItemClick(item, index)}
                >
                  <div className="item-icon">
                    {item.icona ? (
                      <img src={item.icona} alt={item.nome} />
                    ) : (
                      <div className="item-placeholder">{item.nome.charAt(0)}</div>
                    )}
                  </div>
                  <div className="item-details">
                    <div className="item-name">{item.nome}</div>
                    <div className="item-quantity">
                      {item.quantita > 1 ? `x${item.quantita}` : ''}
                    </div>
                  </div>
                  <div className="item-actions">
                    <button 
                      className="item-action use"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleUseItem(item);
                      }}
                    >
                      Usa
                    </button>
                    <button 
                      className="item-action drop"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDropItem(item);
                      }}
                    >
                      Getta
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Inventory; 