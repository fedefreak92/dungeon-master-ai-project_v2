import React, { useState, useEffect } from 'react';
import GameConnection from '../components/GameConnection';
import EventSubscriber from '../components/EventSubscriber';
import { useEventEmitter } from '../components/EventEmitter';
import gameEventService from '../services/gameEventService';
import '../styles/MapPage.css';

/**
 * Pagina della mappa di gioco che utilizza Socket.IO per comunicare con il server
 */
const MapPage = () => {
  const [mapData, setMapData] = useState(null);
  const [player, setPlayer] = useState({ x: 0, y: 0 });
  const [entities, setEntities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState('session_1'); // Esempio di ID sessione
  
  // Utilizziamo il hook useEventEmitter
  const { emitEvent, emitGameAction } = useEventEmitter();

  // Effetto per caricare i dati iniziali della mappa
  useEffect(() => {
    // Inizializza il servizio e carica la lista delle mappe
    gameEventService.initialize()
      .then(() => {
        return gameEventService.requestMapList(sessionId);
      })
      .then(() => {
        // Per semplicità, carichiamo sempre la prima mappa disponibile
        // In un'implementazione reale questo verrebbe fatto dopo la selezione della mappa
        return gameEventService.requestMapData(sessionId, 'mappa_iniziale');
      })
      .then(data => {
        setLoading(false);
      })
      .catch(err => {
        setError(err.message || 'Errore nel caricamento della mappa');
        setLoading(false);
      });
  }, [sessionId]);

  // Handler per gli eventi della mappa
  const mapEventHandlers = {
    // Ricezione dei dati della mappa
    'map_data_response': (data) => {
      console.log('Dati mappa ricevuti:', data);
      if (data && data.map) {
        setMapData(data.map);
        
        // Se ci sono informazioni sul player, aggiorniamo la sua posizione
        if (data.player) {
          setPlayer(data.player.position || { x: 0, y: 0 });
        }
        
        // Aggiorna la lista delle entità
        if (data.entities) {
          setEntities(data.entities);
        }
      }
    },
    
    // Movimento di un'entità (incluso il player)
    'entity_moved': (data) => {
      console.log('Entità mossa:', data);
      
      // Se è il player che si è mosso, aggiorna la sua posizione
      if (data.entity_id === 'player') {
        setPlayer(data.position);
      } else {
        // Altrimenti aggiorna la posizione dell'entità nella lista
        setEntities(prevEntities => 
          prevEntities.map(entity => 
            entity.id === data.entity_id 
              ? { ...entity, position: data.position } 
              : entity
          )
        );
      }
    },
    
    // Spawn di una nuova entità
    'entity_spawned': (data) => {
      console.log('Nuova entità spawned:', data);
      if (data.entity) {
        setEntities(prev => [...prev, data.entity]);
      }
    },
    
    // Despawn di un'entità
    'entity_despawned': (data) => {
      console.log('Entità despawned:', data);
      if (data.entity_id) {
        setEntities(prev => prev.filter(entity => entity.id !== data.entity_id));
      }
    },
    
    // Cambio della mappa
    'map_changed': (data) => {
      console.log('Cambio mappa:', data);
      if (data.map_id) {
        // Carica i dati della nuova mappa
        gameEventService.requestMapData(sessionId, data.map_id);
      }
    },
    
    // Errore nel movimento
    'movement_blocked': (data) => {
      console.log('Movimento bloccato:', data);
      // Qui si potrebbe mostrare un messaggio all'utente
    }
  };

  // Gestione dei tasti per il movimento
  const handleKeyDown = (e) => {
    let direction = null;
    
    switch (e.key) {
      case 'ArrowUp':
      case 'w':
        direction = 'up';
        break;
      case 'ArrowDown':
      case 's':
        direction = 'down';
        break;
      case 'ArrowLeft':
      case 'a':
        direction = 'left';
        break;
      case 'ArrowRight':
      case 'd':
        direction = 'right';
        break;
      default:
        return; // Ignora altri tasti
    }
    
    // Invia l'azione di movimento al server
    emitGameAction('move', { 
      direction,
      player_id: 'player',
      position: player
    });
  };

  // Aggiungiamo l'event listener per i tasti
  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [player]);

  // Render della mappa di gioco
  const renderMap = () => {
    if (!mapData) return null;
    
    // Questa è una rappresentazione semplificata
    // In un'implementazione reale si userebbe Pixi.js o un altro motore di rendering
    return (
      <div className="game-map">
        {/* Visualizzazione della griglia della mappa */}
        <div className="map-grid" style={{ 
          width: `${mapData.width * 32}px`,
          height: `${mapData.height * 32}px`
        }}>
          {/* Celle della mappa */}
          {mapData.tiles && mapData.tiles.map((row, y) => 
            row.map((tile, x) => (
              <div 
                key={`${x}-${y}`}
                className={`map-tile ${tile.type}`}
                style={{ 
                  left: x * 32,
                  top: y * 32
                }}
              />
            ))
          )}
          
          {/* Player */}
          <div 
            className="player"
            style={{ 
              left: player.x * 32,
              top: player.y * 32
            }}
          />
          
          {/* Altre entità */}
          {entities.map(entity => (
            <div 
              key={entity.id}
              className={`entity ${entity.type}`}
              style={{ 
                left: entity.position.x * 32,
                top: entity.position.y * 32
              }}
            />
          ))}
        </div>
      </div>
    );
  };

  // Gestione dello stato di connessione
  const handleConnectionChange = (status, error) => {
    if (status === 'error') {
      setError(error || 'Errore di connessione');
    } else if (status === 'connected') {
      // Richiedi i dati della mappa quando la connessione è stabilita
      gameEventService.requestMapData(sessionId, 'mappa_iniziale');
    }
  };

  return (
    <GameConnection onConnectionChange={handleConnectionChange}>
      {/* Utilizziamo EventSubscriber per gestire gli eventi della mappa */}
      <EventSubscriber 
        events={mapEventHandlers} 
        dependencies={[]} 
      />
      
      <div className="map-page">
        <div className="map-header">
          <h1>Mappa di Gioco</h1>
          {mapData && <div className="map-info">Mappa: {mapData.name}</div>}
        </div>
        
        {loading ? (
          <div className="loading">Caricamento mappa in corso...</div>
        ) : error ? (
          <div className="error-message">{error}</div>
        ) : (
          <div className="map-container">
            {renderMap()}
            
            <div className="map-controls">
              <div className="movement-controls">
                <button onClick={() => handleKeyDown({ key: 'ArrowUp' })}>▲</button>
                <div className="horizontal-controls">
                  <button onClick={() => handleKeyDown({ key: 'ArrowLeft' })}>◄</button>
                  <button onClick={() => handleKeyDown({ key: 'ArrowRight' })}>►</button>
                </div>
                <button onClick={() => handleKeyDown({ key: 'ArrowDown' })}>▼</button>
              </div>
              
              <div className="action-controls">
                <button onClick={() => emitGameAction('interact', { target_id: null })}>
                  Interagisci
                </button>
                <button onClick={() => emitEvent('MAP_LIST_REQUEST', { session_id: sessionId })}>
                  Lista Mappe
                </button>
              </div>
            </div>
          </div>
        )}
        
        <div className="player-info">
          <h3>Informazioni giocatore</h3>
          <p>Posizione: ({player.x}, {player.y})</p>
          <p>Entità visibili: {entities.length}</p>
        </div>
      </div>
    </GameConnection>
  );
};

export default MapPage; 