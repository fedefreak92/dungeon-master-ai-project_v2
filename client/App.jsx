import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import TestWebSocketPage from './pages/TestWebSocketPage';
import './App.css';

/**
 * Componente principale dell'applicazione
 */
const App = () => {
  return (
    <Router>
      <div className="app">
        <nav className="app-nav">
          <Link to="/" className="nav-logo">GIOCO RPG</Link>
          <ul className="nav-links">
            <li><Link to="/">Home</Link></li>
            <li><Link to="/test-websocket">Test WebSocket</Link></li>
            <li><Link to="/game">Gioco</Link></li>
            <li><Link to="/settings">Impostazioni</Link></li>
          </ul>
        </nav>

        <main className="app-content">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/test-websocket" element={<TestWebSocketPage />} />
            <Route path="/game" element={<GamePlaceholder />} />
            <Route path="/settings" element={<SettingsPlaceholder />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>

        <footer className="app-footer">
          <p>© 2023 Gioco RPG - Tutti i diritti riservati</p>
        </footer>
      </div>
    </Router>
  );
};

// Componenti temporanei per le pagine non ancora implementate
const HomePage = () => (
  <div className="home-page">
    <h1>Benvenuto nel Gioco RPG</h1>
    <p>Un'avventura RPG con architettura client-server e comunicazione in tempo reale.</p>
    <div className="feature-grid">
      <div className="feature-card">
        <h3>Comunicazione in tempo reale</h3>
        <p>Usa WebSocket per aggiornamenti istantanei del gioco.</p>
      </div>
      <div className="feature-card">
        <h3>Gestione dello stato</h3>
        <p>Architettura FSM (Finite State Machine) per gestire la logica di gioco.</p>
      </div>
      <div className="feature-card">
        <h3>Rendering avanzato</h3>
        <p>Usa Pixi.js per rendering 2D ottimizzato.</p>
      </div>
      <div className="feature-card">
        <h3>UI reattiva</h3>
        <p>Interfaccia utente costruita con React per un'esperienza fluida.</p>
      </div>
    </div>
    <div className="cta">
      <Link to="/game" className="button primary">Inizia a giocare</Link>
      <Link to="/test-websocket" className="button secondary">Test WebSocket</Link>
    </div>
  </div>
);

const GamePlaceholder = () => (
  <div className="placeholder">
    <h2>Gioco</h2>
    <p>Implementazione del gioco in corso...</p>
  </div>
);

const SettingsPlaceholder = () => (
  <div className="placeholder">
    <h2>Impostazioni</h2>
    <p>Implementazione delle impostazioni in corso...</p>
  </div>
);

const NotFound = () => (
  <div className="not-found">
    <h2>404 - Pagina non trovata</h2>
    <p>La pagina che stai cercando non esiste.</p>
    <Link to="/" className="button">Torna alla Home</Link>
  </div>
);

export default App; 