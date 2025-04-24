import React, { useState, useEffect, useCallback } from 'react';
import { useGame } from '../../contexts/GameContext';
import { useGameState } from '../../hooks/useGameState';
import MapContainer from '../../components/MapContainer';
import GameActions from '../components/GameActions';
import GameInventory from '../components/GameInventory';
import GameCharacterInfo from '../components/GameCharacterInfo';
import DialogContainer from '../components/DialogContainer';
import '../../styles/GameMapScreen.css';

/**
 * Schermata principale del gioco che mostra la mappa e i controlli
 */
const GameMapScreen = () => {
  const { state } = useGame();
  const { gameState, sendAction, loadMap, isConnected } = useGameState();
  const [currentMapId, setCurrentMapId] = useState(state.currentMap || 'world-1');
  const [mapName, setMapName] = useState('');
  const [showDialog, setShowDialog] = useState(false);
  const [dialog, setDialog] = useState(null);
  const [inventoryItems, setInventoryItems] = useState([]);
  
  // Prepara i dati del giocatore in un formato appropriato
  const preparePlayerData = useCallback(() => {
    if (!state.player) return null;
    
    // Adatta i nomi delle proprietà al formato atteso dai componenti
    return {
      name: state.player.nome || 'Sconosciuto',
      class: state.player.classe || 'Sconosciuto',
      level: state.player.livello || 1,
      currentHP: state.player.hp_attuali || 0,
      maxHP: state.player.hp_massimi || 100,
      stats: state.player.statistiche || {
        forza: state.player.forza || 10,
        destrezza: state.player.destrezza || 10,
        costituzione: state.player.costituzione || 10,
        intelligenza: state.player.intelligenza || 10,
        saggezza: state.player.saggezza || 10,
        carisma: state.player.carisma || 10
      }
    };
  }, [state.player]);
  
  // Ottiene l'ID della mappa dallo stato del gioco
  useEffect(() => {
    if (state.currentMap) {
      // Se currentMap è un oggetto, estrai l'ID e il nome
      if (typeof state.currentMap === 'object') {
        setCurrentMapId(state.currentMap.id || 'world-1');
        setMapName(state.currentMap.nome || state.currentMap.id || 'Mappa');
      } else {
        // Se è una stringa, usa direttamente come ID
        setCurrentMapId(state.currentMap);
        setMapName(state.currentMap);
      }
    }
  }, [state.currentMap]);
  
  // Prepara i dati dell'inventario quando lo stato cambia
  useEffect(() => {
    // Spostato la funzione all'interno dell'useEffect
    const prepareInventoryItems = () => {
      if (!state.inventory || !Array.isArray(state.inventory)) return [];
      
      return state.inventory.map(item => ({
        id: item.id || `item-${Math.random().toString(36).substr(2, 9)}`,
        name: item.nome || 'Oggetto sconosciuto',
        type: item.tipo || 'default',
        quantity: item.quantita || 1,
        description: item.descrizione || 'Nessuna descrizione disponibile.',
        usable: item.utilizzabile || false
      }));
    };
    
    setInventoryItems(prepareInventoryItems());
  }, [state.inventory]);
  
  // Gestisce i dialoghi e le interazioni
  useEffect(() => {
    if (gameState?.dialog) {
      setDialog(gameState.dialog);
      setShowDialog(true);
    } else {
      setShowDialog(false);
    }
  }, [gameState?.dialog]);
  
  // Carica la mappa corrente se necessario
  useEffect(() => {
    if (isConnected && currentMapId) {
      loadMap(currentMapId);
    }
  }, [isConnected, currentMapId, loadMap]);
  
  // Gestisce il movimento del giocatore
  const handlePlayerMove = (direction) => {
    console.log(`Movimento ${direction} inviato`);
    sendAction('move_player', { direction });
  };
  
  // Gestisce l'interazione con gli oggetti
  const handleInteract = () => {
    console.log('Interazione inviata');
    sendAction('interact');
  };
  
  // Gestisce le opzioni di dialogo
  const handleDialogOption = (optionIndex) => {
    console.log(`Opzione dialogo ${optionIndex} selezionata`);
    sendAction('dialog_response', { option_index: optionIndex });
  };
  
  // Gestisce il salvataggio del gioco
  const handleSaveGame = () => {
    const saveName = prompt('Inserisci un nome per il salvataggio:');
    if (saveName) {
      console.log(`Salvataggio partita: ${saveName}`);
      sendAction('save_game', { name: saveName });
    }
  };
  
  // Torna al menu principale
  const handleExitToMenu = () => {
    if (window.confirm('Vuoi davvero tornare al menu principale? I progressi non salvati andranno persi.')) {
      console.log('Ritorno al menu principale');
      sendAction('exit_to_menu');
    }
  };
  
  // Ottieni i dati formattati del giocatore
  const playerData = preparePlayerData();
  
  // Assicurati che il nome della mappa sia una stringa valida
  const displayMapName = typeof mapName === 'string' ? mapName : 
                       (typeof mapName === 'object' && mapName !== null) ? 
                       (mapName.nome || mapName.id || 'Mappa') : 
                       'Mappa';
  
  return (
    <div className="game-map-screen">
      <header className="game-header">
        <h2>Mappa: {displayMapName}</h2>
        <div className="game-header-actions">
          <button onClick={handleSaveGame}>Salva partita</button>
          <button onClick={handleExitToMenu}>Esci al menu</button>
        </div>
      </header>
      
      <div className="game-layout">
        <div className="game-sidebar">
          <GameCharacterInfo player={playerData} />
          <GameInventory inventory={inventoryItems} />
        </div>
        
        <div className="game-main-area">
          <MapContainer mapId={currentMapId} />
          
          <GameActions 
            onMove={handlePlayerMove}
            onInteract={handleInteract}
          />
          
          {showDialog && dialog && (
            <DialogContainer 
              dialog={dialog} 
              onSelectOption={handleDialogOption} 
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default GameMapScreen; 