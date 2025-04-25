import React, { useState, useEffect } from 'react';
import socketIOService from '../services/socketIOService';
import { useEventEmitter } from '../components/EventEmitter';
import EventSubscriber from '../components/EventSubscriber';
import GameConnection from '../components/GameConnection';
import '../styles/TestWebSocketPage.css';

/**
 * Pagina di test per verificare la funzionalità Socket.IO
 */
const TestWebSocketPage = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [connectionStatus, setConnectionStatus] = useState('disconnesso');
  const [ngrokUrl, setNgrokUrl] = useState(localStorage.getItem('serverURL') || '');
  const [transportInfo, setTransportInfo] = useState({ transport: 'none', connected: false });
  
  // Utilizziamo il hook useEventEmitter per ottenere i metodi di emissione eventi
  const { emitEvent, emitGameAction } = useEventEmitter();

  // Aggiorna periodicamente le informazioni sul trasporto
  useEffect(() => {
    const updateTransportInfo = () => {
      if (socketIOService.socket && socketIOService.socket.connected) {
        const info = socketIOService.getTransportInfo();
        setTransportInfo(info);
      }
    };
    
    // Aggiorna immediatamente
    updateTransportInfo();
    
    // Poi aggiorna ogni 2 secondi
    const interval = setInterval(updateTransportInfo, 2000);
    
    return () => clearInterval(interval);
  }, [connectionStatus]);

  // Gestisce gli eventi di cambio connessione
  const handleConnectionChange = (status, error) => {
    setConnectionStatus(status);
    
    if (status === 'error' && error) {
      setMessages(prevMessages => [
        ...prevMessages,
        { type: 'error', text: `Errore di connessione: ${error}`, timestamp: new Date() }
      ]);
    } else if (status === 'connected') {
      // Ottieni informazioni sul trasporto
      const info = socketIOService.getTransportInfo();
      setTransportInfo(info);
      
      setMessages(prevMessages => [
        ...prevMessages,
        { 
          type: 'system', 
          text: `Connesso al server (trasporto: ${info.transport})`,
          timestamp: new Date() 
        }
      ]);
    } else if (status === 'disconnected') {
      setMessages(prevMessages => [
        ...prevMessages,
        { type: 'system', text: 'Disconnesso dal server', timestamp: new Date() }
      ]);
    }
  };

  // Imposta l'URL di ngrok e riconnette
  const handleNgrokSubmit = (e) => {
    e.preventDefault();
    // Aggiungi http:// o https:// se non presente
    let url = ngrokUrl;
    if (url && !url.startsWith('http://') && !url.startsWith('https://')) {
      url = 'https://' + url;
    }
    
    // Salva e imposta il nuovo URL
    socketIOService.setServerUrl(url);
    setMessages(prevMessages => [
      ...prevMessages,
      { type: 'system', text: `URL del server impostato a: ${url}`, timestamp: new Date() }
    ]);
    
    // Forza una riconnessione
    socketIOService.disconnect();
    setTimeout(() => {
      window.location.reload(); // Ricarica la pagina per iniziare una nuova connessione
    }, 1000);
  };

  // Esegue un test specifico WebSocket
  const testWebSocketConnection = () => {
    try {
      // Log stato attuale
      const info = socketIOService.getTransportInfo();
      
      setMessages(prevMessages => [
        ...prevMessages,
        { 
          type: 'system', 
          text: `Test connessione WebSocket - Stato attuale: ${info.transport}`,
          data: info,
          timestamp: new Date() 
        }
      ]);
      
      // Controlla le connessioni
      if (window.WEBSOCKET_DEBUG) {
        setMessages(prevMessages => [
          ...prevMessages,
          { 
            type: 'info', 
            text: `Connessioni WebSocket effettuate: ${window.WEBSOCKET_DEBUG.connections.length}`,
            data: window.WEBSOCKET_DEBUG.connections,
            timestamp: new Date() 
          }
        ]);
      }
      
      // Prova un'operazione specifica che potrebbe forzare un upgrade
      socketIOService.emit('test_upgrade', { time: Date.now() })
        .then(() => {
          setTimeout(() => {
            // Controlla se dopo l'operazione il trasporto è cambiato
            const newInfo = socketIOService.getTransportInfo();
            setTransportInfo(newInfo);
            
            setMessages(prevMessages => [
              ...prevMessages,
              { 
                type: 'success', 
                text: `Trasporto dopo test: ${newInfo.transport}`,
                data: newInfo,
                timestamp: new Date() 
              }
            ]);
          }, 1000);
        })
        .catch(error => {
          setMessages(prevMessages => [
            ...prevMessages,
            { 
              type: 'error', 
              text: `Errore nel test WebSocket: ${error.message}`,
              timestamp: new Date() 
            }
          ]);
        });
    } catch (err) {
      setMessages(prevMessages => [
        ...prevMessages,
        { 
          type: 'error', 
          text: `Errore nell'esecuzione del test: ${err.message}`,
          timestamp: new Date() 
        }
      ]);
    }
  };

  // Handlers per gli eventi del gioco
  const eventHandlers = {
    'game_update': (data) => {
      setMessages(prevMessages => [
        ...prevMessages,
        { 
          type: 'update', 
          text: `Aggiornamento di gioco: ${data.type}`, 
          data: data,
          timestamp: new Date() 
        }
      ]);
    },
    'action_response': (data) => {
      setMessages(prevMessages => [
        ...prevMessages,
        { 
          type: data.status === 'error' ? 'error' : 'response', 
          text: data.message || 'Risposta ricevuta', 
          data: data,
          timestamp: new Date() 
        }
      ]);
    },
    'game_state_update': (data) => {
      setMessages(prevMessages => [
        ...prevMessages,
        { 
          type: 'update', 
          text: `Aggiornamento stato di gioco`, 
          data: data,
          timestamp: new Date() 
        }
      ]);
    }
  };

  // Invia un'azione di test al server
  const sendTestAction = (actionType, actionData) => {
    setMessages(prevMessages => [
      ...prevMessages,
      { 
        type: 'sent', 
        text: `Invio azione: ${actionType}`, 
        data: actionData,
        timestamp: new Date() 
      }
    ]);

    emitGameAction(actionType, actionData).catch(error => {
      setMessages(prevMessages => [
        ...prevMessages,
        { 
          type: 'error', 
          text: `Errore nell'invio: ${error.message || 'Errore sconosciuto'}`, 
          timestamp: new Date() 
        }
      ]);
    });
  };

  // Invia un messaggio personalizzato
  const sendCustomMessage = () => {
    if (!inputMessage.trim()) return;

    try {
      // Prova a parsare come JSON se inizia con { o [
      let data = inputMessage;
      if (inputMessage.trim().startsWith('{') || inputMessage.trim().startsWith('[')) {
        data = JSON.parse(inputMessage);
      }

      sendTestAction('custom', { message: data });
      setInputMessage('');
    } catch (e) {
      setMessages(prevMessages => [
        ...prevMessages,
        { 
          type: 'error', 
          text: `Errore nel parsing del messaggio: ${e.message}`, 
          timestamp: new Date() 
        }
      ]);
    }
  };

  // Formatta la timestamp
  const formatTime = (date) => {
    return date.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  return (
    <GameConnection onConnectionChange={handleConnectionChange}>
      {/* Utilizziamo EventSubscriber per ascoltare gli eventi dal server */}
      <EventSubscriber 
        events={eventHandlers} 
        dependencies={[]} 
        onReady={() => console.log('EventSubscriber pronto a ricevere eventi')}
      />
      
      <div className="websocket-test-page">
        <div className="header">
          <h1>Test Socket.IO</h1>
          <div className="connection-info">
            <div className={`connection-status ${connectionStatus}`}>
              Stato: {connectionStatus}
            </div>
            <div className="transport-info">
              Trasporto: <span className={`transport-type ${transportInfo.transport}`}>
                {transportInfo.transport || 'nessuno'}
              </span>
              {transportInfo.connected && (
                <span className="socket-id">ID: {transportInfo.id}</span>
              )}
            </div>
            <button 
              className="test-websocket-btn" 
              onClick={testWebSocketConnection}
              disabled={connectionStatus !== 'connected'}
            >
              Test WebSocket
            </button>
          </div>
          
          {/* Form per inserire l'URL di ngrok */}
          <div className="ngrok-form">
            <form onSubmit={handleNgrokSubmit}>
              <label>
                URL Server (ngrok):
                <input 
                  type="text" 
                  value={ngrokUrl} 
                  onChange={(e) => setNgrokUrl(e.target.value)} 
                  placeholder="Es: https://abcd-123-456.ngrok-free.app"
                />
              </label>
              <button type="submit">Connetti</button>
            </form>
            <div className="ngrok-help">
              <p>
                <small>
                  Inserisci l'URL fornito da ngrok (es: https://abcd-123-456.ngrok-free.app)
                  e premi "Connetti" per utilizzare il tunnel ngrok.
                </small>
              </p>
            </div>
          </div>
        </div>

        <div className="actions-panel">
          <h2>Azioni di test</h2>
          <div className="action-buttons">
            <button 
              onClick={() => sendTestAction('move', { direction: 'up' })}
              disabled={connectionStatus !== 'connected'}
            >
              Muovi Su
            </button>
            <button 
              onClick={() => sendTestAction('move', { direction: 'down' })}
              disabled={connectionStatus !== 'connected'}
            >
              Muovi Giù
            </button>
            <button 
              onClick={() => sendTestAction('move', { direction: 'left' })}
              disabled={connectionStatus !== 'connected'}
            >
              Muovi Sinistra
            </button>
            <button 
              onClick={() => sendTestAction('move', { direction: 'right' })}
              disabled={connectionStatus !== 'connected'}
            >
              Muovi Destra
            </button>
            <button 
              onClick={() => sendTestAction('interact', { target_id: 'npc_1' })}
              disabled={connectionStatus !== 'connected'}
            >
              Interagisci NPC
            </button>
            <button
              onClick={() => emitEvent('MAP_LIST_REQUEST', {})}
              disabled={connectionStatus !== 'connected'}
            >
              Richiedi Lista Mappe
            </button>
          </div>

          <div className="custom-message">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Inserisci un messaggio personalizzato o oggetto JSON"
              disabled={connectionStatus !== 'connected'}
            />
            <button 
              onClick={sendCustomMessage}
              disabled={connectionStatus !== 'connected' || !inputMessage.trim()}
            >
              Invia
            </button>
          </div>
        </div>

        <div className="messages-panel">
          <h2>Messaggi</h2>
          <div className="messages-container">
            {messages.length === 0 ? (
              <div className="no-messages">Nessun messaggio</div>
            ) : (
              messages.map((msg, index) => (
                <div key={index} className={`message ${msg.type}`}>
                  <div className="message-header">
                    <span className="timestamp">{formatTime(msg.timestamp)}</span>
                    <span className="type">{msg.type}</span>
                  </div>
                  <div className="message-content">
                    <div className="message-text">{msg.text}</div>
                    {msg.data && (
                      <pre className="message-data">
                        {JSON.stringify(msg.data, null, 2)}
                      </pre>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
          <div className="controls">
            <button onClick={() => setMessages([])}>Cancella Messaggi</button>
          </div>
        </div>
      </div>
    </GameConnection>
  );
};

export default TestWebSocketPage; 