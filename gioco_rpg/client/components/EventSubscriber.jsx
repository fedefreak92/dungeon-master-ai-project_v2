import React, { useEffect } from 'react';
import socketIOService from '../services/socketIOService';

/**
 * Componente che si iscrive a eventi specifici del server tramite Socket.IO
 * e richiama i callback forniti quando tali eventi vengono ricevuti.
 * 
 * @param {Object} props - Proprietà del componente
 * @param {Object} props.events - Mappa di eventi e relativi callback: { nomeEvento: callback, ... }
 * @param {Array} props.dependencies - Dipendenze per useEffect (opzionale)
 * @param {Function} props.onReady - Callback chiamato quando la connessione è pronta (opzionale)
 */
const EventSubscriber = ({ events = {}, dependencies = [], onReady }) => {
  // Effetto per iscriversi/disiscriversi agli eventi
  useEffect(() => {
    const isConnected = socketIOService.socket && socketIOService.socket.connected;
    
    // Se non siamo connessi, connettiti prima
    if (!isConnected) {
      socketIOService.connect()
        .then(() => {
          if (onReady) onReady();
          registerEvents();
        })
        .catch(error => {
          console.error('Errore di connessione Socket.IO:', error);
        });
    } else {
      if (onReady) onReady();
      registerEvents();
    }
    
    // Registra tutti gli eventi
    function registerEvents() {
      // Per ogni evento specificato nelle props, registra il callback
      Object.entries(events).forEach(([eventName, callback]) => {
        if (typeof callback === 'function') {
          socketIOService.on(eventName, callback);
        }
      });
    }
    
    // Cleanup: rimuovi tutti i callback
    return () => {
      Object.entries(events).forEach(([eventName, callback]) => {
        if (typeof callback === 'function') {
          socketIOService.off(eventName, callback);
        }
      });
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [onReady, ...dependencies]);

  // Questo componente non renderizza nulla
  return null;
};

export default EventSubscriber; 