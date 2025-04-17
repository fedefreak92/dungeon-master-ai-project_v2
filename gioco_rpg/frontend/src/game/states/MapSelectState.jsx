import React, { useEffect, useState } from 'react';
import { useGame } from '../../contexts/GameContext';
import mapApi from '../../api/mapApi';
import '../../styles/MapSelectState.css';

/**
 * Componente per la schermata di selezione della mappa
 */
const MapSelectState = () => {
  const { state, dispatch } = useGame();
  const { sessionId, player } = state;
  
  const [maps, setMaps] = useState({});
  const [currentMap, setCurrentMap] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Carica le mappe disponibili
  useEffect(() => {
    async function fetchMaps() {
      if (!sessionId) {
        console.error('Errore: Session ID non definito');
        setError('Sessione di gioco non disponibile. Torna alla schermata iniziale.');
        setLoading(false);
        return;
      }
      
      try {
        setLoading(true);
        setError(null);
        
        const mapsData = await mapApi.getMaps(sessionId);
        console.log("Dati delle mappe ricevuti:", mapsData);
        
        // Controllo che i dati delle mappe siano validi
        if (mapsData && typeof mapsData.maps === 'object') {
          setMaps(mapsData.maps);
          setCurrentMap(mapsData.currentMap);
          
          if (Object.keys(mapsData.maps).length === 0) {
            console.warn("Nessuna mappa disponibile");
          }
        } else {
          console.error("Formato dati mappe non valido:", mapsData);
          setError('Formato dati mappe non valido');
        }
        
        setLoading(false);
      } catch (err) {
        console.error('Errore nel caricamento delle mappe:', err);
        setError('Impossibile caricare le mappe: ' + (err.message || 'Errore sconosciuto'));
        setLoading(false);
      }
    }
    
    fetchMaps();
  }, [sessionId]);
  
  // Gestisce la selezione di una mappa
  const handleMapSelect = async (mapId) => {
    if (!sessionId) return;
    
    try {
      setLoading(true);
      
      const result = await mapApi.changeMap(sessionId, mapId);
      
      if (result.success) {
        // Aggiorna lo stato globale con la nuova mappa
        dispatch({ type: 'SET_MAP', payload: mapId });
        
        // Cambia stato del gioco a 'map'
        dispatch({ type: 'SET_GAME_STATE', payload: 'map' });
      }
    } catch (err) {
      console.error('Errore nel cambio mappa:', err);
      setError('Impossibile cambiare mappa: ' + (err.message || 'Errore sconosciuto'));
      setLoading(false);
    }
  };
  
  // Gestisce il click sul pulsante 'Indietro'
  const handleBackClick = () => {
    // Torna allo stato precedente (schermata iniziale)
    dispatch({ type: 'SET_GAME_STATE', payload: 'start-screen' });
  };
  
  // Mostra il loader
  if (loading) {
    return (
      <div className="map-select-loading">
        <div className="loader"></div>
        <p>Caricamento mappe in corso...</p>
      </div>
    );
  }
  
  // Gestione errori
  if (error) {
    return (
      <div className="map-select-error">
        <h3>Errore</h3>
        <p>{error}</p>
        <button onClick={handleBackClick}>Torna alla schermata iniziale</button>
      </div>
    );
  }
  
  // Nessuna mappa disponibile
  if (!maps || Object.keys(maps).length === 0) {
    return (
      <div className="map-select-empty">
        <h3>Nessuna mappa disponibile</h3>
        <p>Non ci sono destinazioni disponibili al momento.</p>
        <button onClick={handleBackClick}>Torna alla schermata iniziale</button>
      </div>
    );
  }
  
  return (
    <div className="map-select-container">
      <div className="map-select-header">
        <h2>Seleziona una destinazione</h2>
        <p>Scegli dove viaggiare</p>
      </div>
      
      <div className="maps-grid">
        {Object.entries(maps).map(([mapId, mapInfo]) => {
          const isCurrentMap = currentMap === mapId;
          const isLocked = player && player.livello < (mapInfo.livello_min || 0);
          
          return (
            <div 
              key={mapId}
              className={`map-item ${isCurrentMap ? 'current-map' : ''} ${isLocked ? 'locked-map' : ''}`}
              onClick={() => !isLocked && !isCurrentMap && handleMapSelect(mapId)}
            >
              <div className="map-item-content">
                <h3>{mapInfo.nome || mapId}</h3>
                <div className="map-level">Livello: {mapInfo.livello_min || 1}+</div>
                
                {isCurrentMap && (
                  <div className="map-status current">
                    <span>Posizione attuale</span>
                  </div>
                )}
                
                {isLocked && (
                  <div className="map-status locked">
                    <span>Livello insufficiente</span>
                  </div>
                )}
                
                <div className="map-description">
                  {mapInfo.descrizione || 'Nessuna descrizione disponibile.'}
                </div>
              </div>
            </div>
          );
        })}
      </div>
      
      <div className="map-select-footer">
        <button className="back-button" onClick={handleBackClick}>
          Indietro
        </button>
      </div>
    </div>
  );
};

export default MapSelectState; 