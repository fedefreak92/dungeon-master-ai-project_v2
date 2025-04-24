import React, { useState, useEffect, useRef } from 'react';
import useIOService from '../../hooks/useIOService';
import './MessageLog.css';

/**
 * Componente per visualizzare il log dei messaggi nel gioco
 */
const MessageLog = ({ maxMessages = 50 }) => {
  const { messaggi } = useIOService();
  const messagesEndRef = useRef(null);

  // Limita il numero di messaggi visualizzati
  const messaggiVisualizzati = messaggi.slice(-maxMessages);

  // Funzione per formattare la data del messaggio
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
  };

  // Scorrimento automatico quando arrivano nuovi messaggi
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messaggi.length]);

  return (
    <div className="message-log">
      <div className="message-container">
        {messaggiVisualizzati.map((messaggio, index) => (
          <div 
            key={`msg-${index}-${messaggio.timestamp}`} 
            className={`message message-${messaggio.tipo}`}
          >
            <span className="message-time">[{formatTimestamp(messaggio.timestamp)}]</span>
            <span className="message-text">{messaggio.testo}</span>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default MessageLog; 