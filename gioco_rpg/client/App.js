import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import TestWebSocketPage from './pages/TestWebSocketPage';
import MapPage from './pages/MapPage';
import GameConnection from './components/GameConnection';
import './styles/App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <GameConnection>
          <header className="App-header">
            <h1>Gioco RPG</h1>
            <nav>
              <ul>
                <li><Link to="/">Home</Link></li>
                <li><Link to="/test-socket">Test Socket.IO</Link></li>
                <li><Link to="/map">Mappa</Link></li>
              </ul>
            </nav>
          </header>
          
          <main className="App-content">
            <Routes>
              <Route path="/" element={
                <div className="welcome-screen">
                  <h2>Benvenuto nel Gioco RPG</h2>
                  <p>Un gioco di ruolo basato su Socket.IO e React</p>
                  <div className="navigation-buttons">
                    <Link to="/test-socket" className="nav-button">
                      Test Socket.IO
                    </Link>
                    <Link to="/map" className="nav-button">
                      Inizia Gioco
                    </Link>
                  </div>
                </div>
              } />
              <Route path="/test-socket" element={<TestWebSocketPage />} />
              <Route path="/map" element={<MapPage />} />
            </Routes>
          </main>
          
          <footer className="App-footer">
            <p>Gioco RPG &copy; 2023 - Sviluppato con React e Socket.IO</p>
          </footer>
        </GameConnection>
      </div>
    </Router>
  );
}

export default App; 