import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

// Miglioriamo la compatibilità WebSocket per Eventlet/Socket.IO
// Questo aiuta a risolvere problemi di connessione per Socket.IO
if (window.WebSocket) {
  console.log("WebSocket: miglioramento supporto per Socket.IO");
  
  // Aggiungi proprietà per debug nella console
  window.WEBSOCKET_DEBUG = {
    connections: [],
    interceptor: true,
    errors: []
  };
  
  // Mantieni l'implementazione originale
  const OrigWebSocket = window.WebSocket;
  
  // Estendi il WebSocket con migliore supporto per Socket.IO
  window.WebSocket = function(url, protocols) {
    // Trace delle connessioni WebSocket per debug
    const wsUrl = url.toString();
    
    // Aggiungi alla lista delle connessioni per debug
    window.WEBSOCKET_DEBUG.connections.push({
      url: wsUrl,
      time: new Date().toISOString(),
      protocols: protocols
    });
    
    // Crea l'istanza WebSocket originale
    const socket = new OrigWebSocket(url, protocols);
    
    // Estendi con logging avanzato
    const originalAddEventListener = socket.addEventListener;
    socket.addEventListener = function(type, listener, options) {
      // Migliora il logging per eventi WebSocket
      if (type === 'error' || type === 'close') {
        const wrappedListener = function(event) {
          if (wsUrl.includes('socket.io')) {
            console.log(`WebSocket [${type}] per ${wsUrl.split('?')[0]}`);
          }
          return listener.call(this, event);
        };
        return originalAddEventListener.call(this, type, wrappedListener, options);
      } else {
        return originalAddEventListener.call(this, type, listener, options);
      }
    };
    
    return socket;
  };
  
  // Mantieni l'API originale
  window.WebSocket.prototype = OrigWebSocket.prototype;
  window.WebSocket.CONNECTING = OrigWebSocket.CONNECTING;
  window.WebSocket.OPEN = OrigWebSocket.OPEN;
  window.WebSocket.CLOSING = OrigWebSocket.CLOSING;
  window.WebSocket.CLOSED = OrigWebSocket.CLOSED;
}

// Inizializza l'applicazione React
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
); 