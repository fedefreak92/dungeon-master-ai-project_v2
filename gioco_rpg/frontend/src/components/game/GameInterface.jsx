import React, { useEffect, useState } from 'react';
import MessageLog from '../UIElements/MessageLog';
import DialogBox from '../UIElements/DialogBox';
import ContextMenu from '../UIElements/ContextMenu';
import Tooltip from '../UIElements/Tooltip';
import Inventory from '../UIElements/Inventory';
import socketService from '../../api/socketService';
import ioService from '../../services/IOService';
import './GameInterface.css';

/**
 * Componente principale che integra tutti gli elementi dell'interfaccia di gioco
 * utilizzando il sistema IO
 */
const GameInterface = ({ sessionId }) => {
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [connectionError, setConnectionError] = useState(null);
  const [connectionAttempts, setConnectionAttempts] = useState(0);
  const MAX_RETRY_ATTEMPTS = 3;

  // Effetto per connettere al websocket alla prima renderizzazione
  useEffect(() => {
    // Connetti solo se c'è un sessionId valido
    if (sessionId) {
      const setupConnection = async () => {
        try {
          // Aggiorna stato connessione
          setConnectionStatus('connecting');
          setConnectionError(null);
          
          // Verifica se il socket è già connesso
          if (socketService.isConnected()) {
            console.log('WebSocket già connesso, utilizzo connessione esistente');
            setConnectionStatus('connected');
            
            // Inizializza i listener sulla connessione esistente
            const listenerResult = ioService.initializeSocketListeners();
            console.log('Registrazione listener IO su connessione esistente:', listenerResult ? 'OK' : 'Fallita');
            
            // Richiedi lo stato iniziale del gioco
            socketService.requestGameState();
            return;
          }
          
          console.log('Tentativo di connessione WebSocket diretta...');
          
          // Forza una connessione WebSocket pulita solo se non è già connesso
          socketService.disconnect();
          
          // Aggiungi un piccolo ritardo per garantire che la disconnessione sia completata
          await new Promise(resolve => setTimeout(resolve, 500));
          
          await socketService.connect(sessionId, {
            transports: ['websocket'], // Solo WebSocket, nessun fallback
            forceNew: true,
            timeout: 10000
          });
          
          console.log('Connessione WebSocket stabilita con successo');
          setConnectionStatus('connected');
          
          // Inizializza i listener dopo la connessione
          const listenerResult = ioService.initializeSocketListeners();
          console.log('Registrazione listener IO:', listenerResult ? 'OK' : 'Fallita');
          
          // Richiedi lo stato iniziale del gioco
          socketService.requestGameState();
          
          // Reset dei tentativi di connessione
          setConnectionAttempts(0);
        } catch (error) {
          console.error('Errore nella connessione WebSocket:', error);
          setConnectionStatus('error');
          setConnectionError(error.message);
          
          // Incrementa contatore tentativi
          const newAttempts = connectionAttempts + 1;
          setConnectionAttempts(newAttempts);
          
          // Limita i tentativi automatici
          if (newAttempts < MAX_RETRY_ATTEMPTS) {
            console.log(`Nuovo tentativo di connessione WebSocket (${newAttempts}/${MAX_RETRY_ATTEMPTS}) tra 3 secondi...`);
            setTimeout(() => setupConnection(), 3000);
          } else {
            console.error(`Impossibile stabilire una connessione WebSocket dopo ${MAX_RETRY_ATTEMPTS} tentativi.`);
          }
        }
      };
      
      setupConnection();
      
      // Imposta listener per disconnessioni
      const handleDisconnect = (reason) => {
        console.log(`Connessione WebSocket persa: ${reason}`);
        setConnectionStatus('disconnected');
        
        // Solo una riconnessione automatica se era già connesso prima e non è una disconnessione volontaria
        if (connectionStatus === 'connected' && reason !== 'io client disconnect') {
          setTimeout(() => {
            if (!socketService.isConnected()) {
              console.log('Tentativo di riconnessione automatica dopo disconnessione...');
              
              // Usa il nuovo metodo reconnect per una riconnessione più efficiente
              socketService.reconnect()
                .then(() => {
                  console.log('Riconnessione rapida completata con successo');
                  setConnectionStatus('connected');
                  
                  // Inizializza i listener dopo la riconnessione
                  ioService.initializeSocketListeners();
                  
                  // Richiedi lo stato iniziale del gioco
                  socketService.requestGameState();
                })
                .catch(error => {
                  console.error('Errore nella riconnessione rapida:', error);
                  
                  // Fallback alla connessione normale
                  setupConnection();
                });
            }
          }, 2000); // Aumento del ritardo a 2 secondi
        }
      };
      
      socketService.on('disconnect', handleDisconnect);
      
      // Cleanup alla chiusura
      return () => {
        socketService.off('disconnect', handleDisconnect);
        // Non disconnettiamo qui, per evitare disconnessioni non necessarie
      };
    }
  }, [sessionId, connectionAttempts, connectionStatus]);

  // Aggiungiamo un listener per il cambio mappa
  useEffect(() => {
    if (!sessionId) return;
    
    const handleMapChangeComplete = (data) => {
      console.log('Cambio mappa completato:', data);
      
      // Se la connessione è stata interrotta durante il cambio mappa, tenta di riconnettersi
      if (!socketService.isConnected()) {
        console.log('Tentativo di riconnessione dopo cambio mappa...');
        
        setTimeout(() => {
          socketService.reconnect()
            .then(() => {
              console.log('Riconnessione dopo cambio mappa riuscita');
              setConnectionStatus('connected');
            })
            .catch(err => {
              console.error('Errore riconnessione dopo cambio mappa:', err);
              setConnectionStatus('error');
              setConnectionError(err.message);
            });
        }, 1000);
      }
    };
    
    // Registra il listener
    socketService.on('map_change_complete', handleMapChangeComplete);
    
    return () => {
      socketService.off('map_change_complete', handleMapChangeComplete);
    };
  }, [sessionId]);

  // Renderizza indicatore di caricamento o errore
  const renderConnectionStatus = () => {
    if (connectionStatus === 'connecting') {
      return <div className="connection-status connecting">Connessione WebSocket in corso...</div>;
    } else if (connectionStatus === 'error') {
      return (
        <div className="connection-status error">
          Errore di connessione WebSocket: {connectionError}
          <button onClick={() => window.location.reload()}>Riprova</button>
        </div>
      );
    } else if (connectionStatus === 'disconnected') {
      return <div className="connection-status disconnected">WebSocket disconnesso...</div>;
    }
    return null;
  };

  // Renderizza l'interfaccia completa
  return (
    <div className="game-interface">
      {/* Mostra stato connessione */}
      {renderConnectionStatus()}
      
      {/* Area di gioco principale (mappa, personaggi, elementi interattivi) */}
      <div className="game-display">
        {/* Qui renderizzerai la mappa di gioco con Pixi.js */}
        <div id="game-canvas-container" />
        
        {/* Componenti UI sovrapposti */}
        <Tooltip />
        <ContextMenu />
      </div>
      
      {/* Interfaccia di gioco inferiore */}
      <div className="game-controls">
        <MessageLog maxMessages={10} />
      </div>
      
      {/* Componenti modali */}
      <DialogBox />
      <Inventory />
    </div>
  );
};

export default GameInterface; 