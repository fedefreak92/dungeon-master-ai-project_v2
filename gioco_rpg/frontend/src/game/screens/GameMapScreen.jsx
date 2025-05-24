import React, { useState, useEffect, useCallback } from 'react';
import { useGame } from '../../contexts/GameContext';
import { useGameState } from '../../hooks/useGameState';
import useItemService from '../../hooks/useItemService';
import useIOService from '../../hooks/useIOService';
import MapContainer from '../../components/MapContainer';
import GameActions from '../components/GameActions';
import GameInventory from '../components/GameInventory';
import GameCharacterInfo from '../components/GameCharacterInfo';
import DialogContainer from '../components/DialogContainer';
import '../../styles/GameMapScreen.css';

/**
 * Schermata principale del gioco che mostra la mappa e i controlli
 */
const GameMapScreen = (props) => {
  const { state } = useGame();
  const { gameState, sendAction, loadMap, isConnected } = useGameState();
  const { initialItems } = useItemService();
  const { mostraInventario } = useIOService();
  const [currentMapId, setCurrentMapId] = useState(state.currentMap || 'world-1');
  const [mapName, setMapName] = useState('');
  const [showDialog, setShowDialog] = useState(false);
  const [dialog, setDialog] = useState(null);
  const [inventoryItems, setInventoryItems] = useState([]);
  
  // Prepara i dati del giocatore in un formato appropriato
  const preparePlayerData = useCallback(() => {
    if (!state.player) return null;
    
    console.log('GameMapScreen: Preparo dati player, HP originali:', state.player.hp, '/', state.player.hp_max);
    
    // Adatta i nomi delle proprietà al formato atteso dai componenti
    return {
      nome: state.player.nome || 'Sconosciuto',
      name: state.player.nome || 'Sconosciuto', // Doppio campo per retrocompatibilità
      classe: state.player.classe || 'Sconosciuto',
      class: state.player.classe || 'Sconosciuto', // Doppio campo per retrocompatibilità
      livello: state.player.livello || 1,
      level: state.player.livello || 1, // Doppio campo per retrocompatibilità
      hp: state.player.hp, // Usa i campi HP originali dal server
      hp_max: state.player.hp_max,
      currentHP: state.player.hp, // Per retrocompatibilità
      maxHP: state.player.hp_max, // Per retrocompatibilità
      mana: state.player.mana || 0,
      mana_max: state.player.mana_max || 0,
      statistiche: state.player.statistiche || {
        forza: state.player.forza || 10,
        destrezza: state.player.destrezza || 10,
        costituzione: state.player.costituzione || 10,
        intelligenza: state.player.intelligenza || 10,
        saggezza: state.player.saggezza || 10,
        carisma: state.player.carisma || 10
      },
      stats: state.player.statistiche || { // Doppio campo per retrocompatibilità
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
      // Combina gli oggetti dell'inventario del giocatore con gli oggetti iniziali
      const combinedInventory = [
        ...(state.inventory || []),  // Oggetti dal server
        ...initialItems              // Oggetti iniziali dalla classe del giocatore
      ];
      
      if (!combinedInventory.length) return [];
      
      console.log('GameMapScreen: Preparo dati inventario, oggetti totali:', combinedInventory.length, 
                 '(server:', state.inventory?.length || 0, ', iniziali:', initialItems.length, ')');
      
      return combinedInventory.map(item => ({
        id: item.id || `item-${Math.random().toString(36).substr(2, 9)}`,
        nome: item.nome || item.name || 'Oggetto sconosciuto',
        name: item.nome || item.name || 'Oggetto sconosciuto', // Doppio campo per retrocompatibilità
        tipo: item.tipo || item.type || 'default',
        type: item.tipo || item.type || 'default', // Doppio campo per retrocompatibilità
        quantita: item.quantita || item.quantity || 1,
        quantity: item.quantita || item.quantity || 1, // Doppio campo per retrocompatibilità
        descrizione: item.descrizione || item.description || 'Nessuna descrizione disponibile.',
        description: item.descrizione || item.description || 'Nessuna descrizione disponibile.', // Doppio campo per retrocompatibilità
        usabile: item.utilizzabile || item.usabile || item.usable || false,
        usable: item.utilizzabile || item.usabile || item.usable || false, // Doppio campo per retrocompatibilità
        icona: item.icona || item.icon || null,
        icon: item.icona || item.icon || null // Doppio campo per retrocompatibilità
      }));
    };
    
    setInventoryItems(prepareInventoryItems());
  }, [state.inventory, initialItems]);
  
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

  // Verifica e pulisce eventuali canvas duplicati
  useEffect(() => {
    // Questa funzione cerca canvas duplicati o nascosti e li rimuove
    const cleanupDuplicateCanvases = () => {
      // Ottieni tutti i canvas nella pagina
      const canvases = document.querySelectorAll('canvas');
      
      // Se c'è più di un canvas, potrebbe esserci un problema
      if (canvases.length > 1) {
        console.warn(`Trovati ${canvases.length} elementi canvas - rimozione dei duplicati`);
        
        // Identifica il canvas attivo (quello visibile)
        let activeCanvas = null;
        for (let i = 0; i < canvases.length; i++) {
          const canvas = canvases[i];
          const style = window.getComputedStyle(canvas);
          
          // Se il canvas è visibile (width e height > 0, display non none), è quello attivo
          if (parseInt(style.width) > 0 && 
              parseInt(style.height) > 0 && 
              style.display !== 'none' && 
              canvas.parentElement && 
              canvas.parentElement.closest('.game-main-area')) {
            activeCanvas = canvas;
            break;
          }
        }
        
        // Rimuovi tutti i canvas tranne quello attivo
        for (let i = 0; i < canvases.length; i++) {
          const canvas = canvases[i];
          if (canvas !== activeCanvas && canvas.parentElement) {
            console.log('Rimozione canvas duplicato');
            canvas.parentElement.removeChild(canvas);
          }
        }
      }
    };
    
    // Esegui la pulizia dopo che il componente è stato montato
    const timerId = setTimeout(cleanupDuplicateCanvases, 1000);
    
    return () => {
      clearTimeout(timerId);
    };
  }, []);
  
  // Gestisce il movimento del giocatore
  const handlePlayerMove = (direction) => {
    console.log(`Movimento ${direction} inviato`);
    
    // Traduci le direzioni dall'inglese all'italiano per il server
    const directionMap = {
      'up': 'nord',
      'down': 'sud',
      'left': 'ovest',
      'right': 'est'
    };
    
    const italianDirection = directionMap[direction] || direction;
    console.log(`Direzione tradotta per il server: ${italianDirection}`);
    
    sendAction('move_player', { direction: italianDirection });
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
      console.log(`Salvataggio partita con nome: "${saveName}"`);
      
      // Utilizza il metodo di salvataggio tramite API REST fornito come prop
      if (props.onSaveGame) {
        props.onSaveGame(saveName);
        // Feedback all'utente
        alert(`Richiesta di salvataggio inviata con nome: "${saveName}"`);
      } else {
        // Fallback all'utilizzo di WebSocket se onSaveGame non è disponibile
        sendAction('save_game', { 
          name: saveName 
        });
      }
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
  
  // Gestisce gli eventi di tastiera per il movimento
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Previene il comportamento di default per i tasti freccia
      if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
        e.preventDefault();
      }
      
      let direction = null;
      
      switch (e.key) {
        case 'ArrowUp':
        case 'w':
        case 'W':
          direction = 'up';
          break;
        case 'ArrowDown':
        case 's':
        case 'S':
          direction = 'down';
          break;
        case 'ArrowLeft':
        case 'a':
        case 'A':
          direction = 'left';
          break;
        case 'ArrowRight':
        case 'd':
        case 'D':
          direction = 'right';
          break;
        case ' ':  // Barra spaziatrice per interagire
          handleInteract();
          return;
        default:
          return;
      }
      
      if (direction) {
        handlePlayerMove(direction);
      }
    };
    
    // Aggiungi il listener solo quando il componente è montato e connesso
    if (isConnected) {
      window.addEventListener('keydown', handleKeyDown);
      console.log('Listener tastiera per movimento registrato');
    }
    
    // Cleanup
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      console.log('Listener tastiera per movimento rimosso');
    };
  }, [isConnected, handlePlayerMove, handleInteract]); // Aggiunto handlePlayerMove e handleInteract come dipendenze
  
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
          {/* Pulsante dell'inventario nella sidebar */}
          <div className="sidebar-inventory-button">
            <button 
              className="open-inventory-button"
              onClick={() => {
                // Mostra l'UI dell'inventario localmente
                mostraInventario();
                
                // Invia l'evento UI_INVENTORY_TOGGLE al backend
                if (sendAction) {
                  sendAction('ui_event', { 
                    type: 'UI_INVENTORY_TOGGLE'
                  });
                  console.log('Richiesta di attivazione stato inventario inviata dal sidebar button');
                }
              }}
            >
              Apri Inventario
            </button>
          </div>
          {/* L'inventario viene mostrato come overlay, non più nel sidebar */}
        </div>
        
        {/* Contenitore principale della mappa */}
        <div className="game-main-area">
          {/* Utilizziamo solo MapContainer e nessun altro renderer */}
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
      
      {/* Aggiungiamo GameInventory qui, al di fuori del layout principale */}
      <GameInventory inventory={inventoryItems} />
    </div>
  );
};

export default GameMapScreen; 