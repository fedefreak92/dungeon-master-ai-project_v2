import React, { useState, useEffect } from 'react';
import mapApi from '../../api/mapApi';
import '../../styles/MapDebugTool.css';

/**
 * Componente di utilità per diagnosticare e risolvere problemi con le mappe
 */
const MapDebugTool = ({ sessionId, onClose }) => {
  const [mapList, setMapList] = useState([]);
  const [selectedMap, setSelectedMap] = useState('');
  const [mapData, setMapData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [logs, setLogs] = useState([]);
  
  // Aggiunge un log con timestamp
  const addLog = (message, isError = false) => {
    const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
    const newLog = { timestamp, message, isError };
    setLogs(prevLogs => [newLog, ...prevLogs].slice(0, 50));
    
    if (isError) {
      console.error(`[MapDebugTool] ${message}`);
    } else {
      console.log(`[MapDebugTool] ${message}`);
    }
  };
  
  // Carica la lista delle mappe disponibili
  useEffect(() => {
    if (!sessionId) {
      addLog('Sessione non disponibile', true);
      return;
    }
    
    const fetchMaps = async () => {
      try {
        setLoading(true);
        addLog('Caricamento liste mappe...');
        
        const mapsData = await mapApi.getMaps(sessionId);
        
        if (mapsData?.maps) {
          const mapsArray = Object.entries(mapsData.maps).map(([id, data]) => ({
            id,
            name: data.nome || id,
            minLevel: data.livello_min || 0,
            isCurrent: id === mapsData.currentMap
          }));
          
          setMapList(mapsArray);
          addLog(`Caricate ${mapsArray.length} mappe`);
          
          // Seleziona la mappa corrente se disponibile
          if (mapsData.currentMap) {
            setSelectedMap(mapsData.currentMap);
            addLog(`Mappa corrente: ${mapsData.currentMap}`);
          }
        } else {
          addLog('Nessuna mappa disponibile', true);
        }
        
        setLoading(false);
      } catch (err) {
        addLog(`Errore nel caricamento delle mappe: ${err.message}`, true);
        setError(err.message);
        setLoading(false);
      }
    };
    
    fetchMaps();
  }, [sessionId]);
  
  // Carica i dati di una mappa specifica
  const loadMapData = async (mapId) => {
    if (!mapId) {
      addLog('ID mappa non specificato', true);
      return;
    }
    
    try {
      setLoading(true);
      setError('');
      addLog(`Caricamento dati mappa: ${mapId}...`);
      
      const data = await mapApi.getMapData(sessionId, mapId);
      
      if (data) {
        // Valida e ripara i dati se necessario
        const validatedData = mapApi.validateAndFixMapData(data);
        setMapData(validatedData);
        addLog(`Dati mappa caricati: ${mapId}`);
        
        // Log delle proprietà principali per debug
        addLog(`Dimensioni: ${validatedData.larghezza}x${validatedData.altezza}`);
        addLog(`Elementi: ${Object.keys(validatedData.oggetti || {}).length} oggetti, ${Object.keys(validatedData.npg || {}).length} NPC`);
      } else {
        addLog(`Dati mappa non validi: ${mapId}`, true);
        setMapData(null);
      }
      
      setLoading(false);
    } catch (err) {
      addLog(`Errore nel caricamento dei dati mappa: ${err.message}`, true);
      setError(err.message);
      setLoading(false);
    }
  };
  
  // Verifica il formato della mappa
  const checkMapFormat = () => {
    if (!mapData) {
      addLog('Nessun dato mappa da verificare', true);
      return;
    }
    
    addLog('Verifica formato mappa...');
    
    try {
      let hasErrors = false;
      let hasWarnings = false;
      
      // Verifica le proprietà fondamentali
      if (!mapData.larghezza || typeof mapData.larghezza !== 'number') {
        addLog('ERRORE: Proprietà "larghezza" mancante o non valida', true);
        hasErrors = true;
      }
      
      if (!mapData.altezza || typeof mapData.altezza !== 'number') {
        addLog('ERRORE: Proprietà "altezza" mancante o non valida', true);
        hasErrors = true;
      }
      
      if (!mapData.griglia || !Array.isArray(mapData.griglia)) {
        addLog('ERRORE: Proprietà "griglia" mancante o non valida', true);
        hasErrors = true;
      } else {
        // Controllo dimensioni griglia
        if (mapData.griglia.length < mapData.altezza) {
          addLog(`AVVISO: Griglia più corta dell'altezza dichiarata (${mapData.griglia.length} < ${mapData.altezza})`, true);
          hasWarnings = true;
        }
        
        // Controllo larghezza righe
        for (let y = 0; y < mapData.griglia.length; y++) {
          const row = mapData.griglia[y];
          if (!Array.isArray(row)) {
            addLog(`ERRORE: Riga ${y} non è un array`, true);
            hasErrors = true;
          } else if (row.length < mapData.larghezza) {
            addLog(`AVVISO: Riga ${y} più corta della larghezza dichiarata (${row.length} < ${mapData.larghezza})`, true);
            hasWarnings = true;
          }
        }
      }
      
      // Controllo proprietà opzionali
      if (!mapData.oggetti) {
        addLog('AVVISO: Proprietà "oggetti" mancante', true);
        hasWarnings = true;
      }
      
      if (!mapData.npg) {
        addLog('AVVISO: Proprietà "npg" mancante', true);
        hasWarnings = true;
      }
      
      if (!mapData.nome) {
        addLog('AVVISO: Proprietà "nome" mancante', true);
        hasWarnings = true;
      }
      
      // Controllo formato oggetti
      if (mapData.oggetti) {
        for (const [id, obj] of Object.entries(mapData.oggetti)) {
          if (typeof obj.x !== 'number' || typeof obj.y !== 'number') {
            addLog(`ERRORE: Oggetto "${id}" con coordinate non valide`, true);
            hasErrors = true;
          }
        }
      }
      
      // Controllo formato NPC
      if (mapData.npg) {
        for (const [id, npc] of Object.entries(mapData.npg)) {
          if (typeof npc.x !== 'number' || typeof npc.y !== 'number') {
            addLog(`ERRORE: NPC "${id}" con coordinate non valide`, true);
            hasErrors = true;
          }
        }
      }
      
      if (!hasErrors && !hasWarnings) {
        addLog('Formato mappa valido ✅');
      } else if (!hasErrors) {
        addLog('Formato mappa valido con avvisi ⚠️');
      } else {
        addLog('Formato mappa non valido ❌', true);
      }
    } catch (err) {
      addLog(`Errore durante la verifica: ${err.message}`, true);
    }
  };
  
  // Tenta di riparare i problemi comuni della mappa
  const fixMapIssues = () => {
    if (!mapData) {
      addLog('Nessun dato mappa da riparare', true);
      return;
    }
    
    addLog('Tentativo di riparazione problemi mappa...');
    
    try {
      const fixedData = { ...mapData };
      let fixCount = 0;
      
      // Ripara dimensioni e griglia
      if (!fixedData.larghezza || typeof fixedData.larghezza !== 'number') {
        if (fixedData.griglia && fixedData.griglia[0]) {
          fixedData.larghezza = fixedData.griglia[0].length;
          addLog(`Riparato: larghezza impostata a ${fixedData.larghezza}`);
          fixCount++;
        } else {
          fixedData.larghezza = 10; // Valore predefinito
          addLog(`Riparato: larghezza impostata al valore predefinito ${fixedData.larghezza}`);
          fixCount++;
        }
      }
      
      if (!fixedData.altezza || typeof fixedData.altezza !== 'number') {
        if (fixedData.griglia) {
          fixedData.altezza = fixedData.griglia.length;
          addLog(`Riparato: altezza impostata a ${fixedData.altezza}`);
          fixCount++;
        } else {
          fixedData.altezza = 10; // Valore predefinito
          addLog(`Riparato: altezza impostata al valore predefinito ${fixedData.altezza}`);
          fixCount++;
        }
      }
      
      // Ripara griglia se mancante o non valida
      if (!fixedData.griglia || !Array.isArray(fixedData.griglia)) {
        fixedData.griglia = Array(fixedData.altezza).fill().map(() => Array(fixedData.larghezza).fill(0));
        addLog(`Riparato: creata nuova griglia ${fixedData.altezza}x${fixedData.larghezza}`);
        fixCount++;
      }
      
      // Assicura che la griglia abbia l'altezza corretta
      if (fixedData.griglia.length < fixedData.altezza) {
        const rowsToAdd = fixedData.altezza - fixedData.griglia.length;
        for (let i = 0; i < rowsToAdd; i++) {
          fixedData.griglia.push(Array(fixedData.larghezza).fill(0));
        }
        addLog(`Riparato: aggiunte ${rowsToAdd} righe alla griglia`);
        fixCount++;
      }
      
      // Assicura che ogni riga abbia la larghezza corretta
      for (let y = 0; y < fixedData.griglia.length; y++) {
        if (!Array.isArray(fixedData.griglia[y])) {
          fixedData.griglia[y] = Array(fixedData.larghezza).fill(0);
          addLog(`Riparato: sostituita riga ${y} non valida`);
          fixCount++;
        } else if (fixedData.griglia[y].length < fixedData.larghezza) {
          const cellsToAdd = fixedData.larghezza - fixedData.griglia[y].length;
          fixedData.griglia[y] = [...fixedData.griglia[y], ...Array(cellsToAdd).fill(0)];
          addLog(`Riparato: aggiunte ${cellsToAdd} celle alla riga ${y}`);
          fixCount++;
        }
      }
      
      // Verifica oggetti
      if (!fixedData.oggetti) {
        fixedData.oggetti = {};
        addLog('Riparato: aggiunta proprietà "oggetti" vuota');
        fixCount++;
      }
      
      // Verifica NPG
      if (!fixedData.npg) {
        fixedData.npg = {};
        addLog('Riparato: aggiunta proprietà "npg" vuota');
        fixCount++;
      }
      
      if (fixCount > 0) {
        setMapData(fixedData);
        addLog(`Riparazione completata: ${fixCount} problemi risolti ✅`);
      } else {
        addLog('Nessun problema da riparare trovato ✅');
      }
    } catch (err) {
      addLog(`Errore durante la riparazione: ${err.message}`, true);
    }
  };
  
  // Gestione cambio mappa
  const handleMapChange = (e) => {
    const mapId = e.target.value;
    setSelectedMap(mapId);
    
    if (mapId) {
      loadMapData(mapId);
    } else {
      setMapData(null);
    }
  };
  
  // Gestione ricaricamento dati mappa
  const handleReloadMap = () => {
    if (selectedMap) {
      loadMapData(selectedMap);
    }
  };

  return (
    <div className="map-debug-tool">
      <div className="map-debug-header">
        <h2>Strumento Debug Mappe</h2>
        <button className="close-button" onClick={onClose}>✕</button>
      </div>
      
      <div className="map-debug-content">
        <div className="map-selector">
          <label>
            Seleziona Mappa:
            <select value={selectedMap} onChange={handleMapChange}>
              <option value="">-- Seleziona una mappa --</option>
              {mapList.map(map => (
                <option key={map.id} value={map.id}>
                  {map.name} {map.isCurrent ? '(corrente)' : ''} (Lvl {map.minLevel})
                </option>
              ))}
            </select>
          </label>
          
          <button 
            className="reload-button" 
            onClick={handleReloadMap} 
            disabled={!selectedMap || loading}
          >
            {loading ? 'Caricamento...' : 'Ricarica'}
          </button>
        </div>
        
        {error && (
          <div className="error-message">
            <p>Errore: {error}</p>
          </div>
        )}
        
        <div className="map-debug-actions">
          <button 
            onClick={checkMapFormat} 
            disabled={!mapData || loading}
            className="check-button"
          >
            Verifica Formato
          </button>
          
          <button 
            onClick={fixMapIssues} 
            disabled={!mapData || loading}
            className="fix-button"
          >
            Ripara Problemi
          </button>
        </div>
        
        {mapData && (
          <div className="map-info">
            <h3>Informazioni Mappa</h3>
            <div className="map-properties">
              <div className="property">
                <span>Nome:</span>
                <span>{mapData.nome || 'Non specificato'}</span>
              </div>
              <div className="property">
                <span>Dimensioni:</span>
                <span>{mapData.larghezza || '?'} x {mapData.altezza || '?'}</span>
              </div>
              <div className="property">
                <span>Dimensioni Griglia:</span>
                <span>
                  {mapData.griglia ? `${mapData.griglia.length} righe` : 'Non disponibile'}
                  {mapData.griglia && mapData.griglia[0] ? ` x ${mapData.griglia[0].length} colonne` : ''}
                </span>
              </div>
              <div className="property">
                <span>Oggetti:</span>
                <span>{mapData.oggetti ? Object.keys(mapData.oggetti).length : 0}</span>
              </div>
              <div className="property">
                <span>NPC:</span>
                <span>{mapData.npg ? Object.keys(mapData.npg).length : 0}</span>
              </div>
            </div>
          </div>
        )}
        
        <div className="debug-logs">
          <h3>Log</h3>
          <ul>
            {logs.map((log, index) => (
              <li key={index} className={log.isError ? 'error-log' : ''}>
                <span className="log-time">[{log.timestamp}]</span>
                <span className="log-message">{log.message}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default MapDebugTool; 