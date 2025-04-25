import React, { useCallback } from 'react';
import socketIOService from '../services/socketIOService';

/**
 * Hook personalizzato che fornisce i metodi per emettere eventi al server
 */
export const useEventEmitter = () => {
  /**
   * Emette un evento al server
   * @param {string} eventName - Nome dell'evento
   * @param {object} data - Dati da inviare
   * @returns {Promise} Promise che si risolve con la risposta del server
   */
  const emitEvent = useCallback((eventName, data = {}) => {
    return socketIOService.emit(eventName, data);
  }, []);

  /**
   * Emette un evento al server e attende una risposta (acknowledgement)
   * @param {string} eventName - Nome dell'evento
   * @param {object} data - Dati da inviare
   * @returns {Promise} Promise che si risolve con la risposta del server
   */
  const emitWithAck = useCallback((eventName, data = {}) => {
    return new Promise((resolve, reject) => {
      socketIOService.emit(eventName, data, (response) => {
        if (response && response.error) {
          reject(new Error(response.error));
        } else {
          resolve(response);
        }
      }).catch(reject);
    });
  }, []);

  /**
   * Emette un'azione di gioco al server
   * @param {string} actionType - Tipo di azione
   * @param {object} actionData - Dati dell'azione
   * @returns {Promise} Promise che si risolve con la risposta del server
   */
  const emitGameAction = useCallback((actionType, actionData = {}) => {
    return socketIOService.emit('player_action', {
      action: actionType,
      params: actionData
    });
  }, []);

  return {
    emitEvent,
    emitWithAck,
    emitGameAction
  };
};

/**
 * Componente che fornisce metodi per emettere eventi al server tramite Socket.IO
 * Questo componente viene utilizzato come wrapper per fornire i metodi di emissione
 * ai componenti figli tramite una funzione di render prop.
 * 
 * @param {Object} props - Proprietà del componente
 * @param {Function} props.children - Funzione di render prop che riceve i metodi di emissione
 */
const EventEmitter = ({ children }) => {
  const emitter = useEventEmitter();
  
  // Renderizza i children passando loro i metodi di emissione
  return children(emitter);
};

export default EventEmitter; 