import React, { useState, useEffect } from 'react';
import { useGame } from '../contexts/GameContext';
import { saveApi } from '../api/gameApi';
import '../styles/StartScreen.css';

/**
 * Componente per la schermata iniziale del gioco
 */
const StartScreen = ({ onStartNewGame, onLoadGame }) => {
  const { state } = useGame();
  const { loading, error, classes: availableClasses } = state;
  
  const [saveGames, setSaveGames] = useState([]);
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [selectedSaveGame, setSelectedSaveGame] = useState(null);
  const [currentScreen, setCurrentScreen] = useState('welcome'); // 'welcome', 'newGame', 'loadGame'
  
  // Stato per il form nuovo gioco
  const [playerName, setPlayerName] = useState('');
  const [playerClass, setPlayerClass] = useState('');
  
  // Aggiorna la classe selezionata quando le classi vengono caricate
  useEffect(() => {
    if (availableClasses.length > 0 && !playerClass) {
      setPlayerClass(availableClasses[0]?.id || '');
    }
  }, [availableClasses, playerClass]);
  
  // Carica la lista dei salvataggi dal server
  useEffect(() => {
    fetchSaveGames();
  }, []);

  const fetchSaveGames = async () => {
    try {
      setSaveLoading(true);
      setSaveError(null);
      
      const saves = await saveApi.getSaveGames();
      setSaveGames(saves);
    } catch (err) {
      console.error("Errore nel caricamento dei salvataggi:", err);
      setSaveError("Errore nel caricamento dei salvataggi: " + (err.message || err));
    } finally {
      setSaveLoading(false);
    }
  };

  // Gestisce il click sul pulsante "Nuovo"
  const handleNewGameClick = () => {
    setCurrentScreen('newGame');
  };

  // Gestisce il click sul pulsante "Carica"
  const handleLoadGameClick = () => {
    setCurrentScreen('loadGame');
  };

  // Gestisce il submit del form di creazione personaggio
  const handleNewGameSubmit = (e) => {
    e.preventDefault();
    if (!playerName.trim()) {
      setSaveError("Inserisci un nome per il tuo personaggio");
      return;
    }
    
    // Chiama la funzione di callback passata dal componente padre
    onStartNewGame(playerName, playerClass);
  };

  // Gestisce il click sul pulsante "Carica Partita Selezionata"
  const handleLoadSaveClick = () => {
    if (!selectedSaveGame) {
      setSaveError("Seleziona un salvataggio da caricare");
      return;
    }
    
    // Chiama la funzione di callback passata dal componente padre
    onLoadGame(selectedSaveGame);
  };

  // Gestisce il click sul pulsante "Torna indietro"
  const handleBackClick = () => {
    setCurrentScreen('welcome');
    setSaveError(null);
  };

  // Rendering condizionale in base allo stato currentScreen
  const renderContent = () => {
    switch (currentScreen) {
      case 'welcome':
        return (
          <div className="welcome-screen">
            <div className="welcome-title">
              <h1>Benvenuto Dungeon Master AI</h1>
              <p>L'esperienza definitiva per gli amanti di D&D!</p>
            </div>
            
            <div className="welcome-buttons">
              <button 
                className="main-button new-game-button"
                onClick={handleNewGameClick}
              >
                NUOVO
              </button>
              
              <button 
                className="main-button load-game-button"
                onClick={handleLoadGameClick}
              >
                CARICA
              </button>
            </div>
          </div>
        );

      case 'newGame':
        return (
          <div className="start-panel new-game-panel">
            <h2>Crea Nuovo Personaggio</h2>
            {loading ? (
              <div className="loading-spinner">Caricamento classi in corso...</div>
            ) : (
              <form onSubmit={handleNewGameSubmit} className="new-game-form">
                <div className="form-group">
                  <label htmlFor="playerName">Nome del personaggio:</label>
                  <input 
                    type="text" 
                    id="playerName"
                    value={playerName}
                    onChange={(e) => setPlayerName(e.target.value)}
                    placeholder="Inserisci un nome"
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="playerClass">Classe:</label>
                  <select 
                    id="playerClass"
                    value={playerClass}
                    onChange={(e) => setPlayerClass(e.target.value)}
                    style={{ color: "white", backgroundColor: "#333", borderColor: "#8e7851" }}
                  >
                    {availableClasses.map(cls => (
                      <option key={cls.id} value={cls.id} style={{ backgroundColor: "#333", color: "white" }}>
                        {cls.nome || cls.id}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div className="class-description">
                  {availableClasses.find(c => c.id === playerClass)?.descrizione || ''}
                </div>
                
                <div className="form-buttons">
                  <button 
                    type="button"
                    className="secondary-button"
                    onClick={handleBackClick}
                  >
                    Indietro
                  </button>
                  <button 
                    type="submit"
                    className="main-button"
                    disabled={loading || availableClasses.length === 0}
                  >
                    {loading ? 'Creazione in corso...' : 'Inizia Avventura'}
                  </button>
                </div>
              </form>
            )}
          </div>
        );

      case 'loadGame':
        return (
          <div className="start-panel load-game-panel">
            <h2>Carica Partita</h2>
            {saveLoading ? (
              <div className="loading-spinner">Caricamento salvataggi...</div>
            ) : saveGames.length > 0 ? (
              <>
                <div className="save-games-list">
                  {saveGames.map((save, index) => (
                    <div 
                      key={index}
                      className={`save-game-item ${selectedSaveGame === save.nome ? 'selected' : ''}`}
                      onClick={() => setSelectedSaveGame(save.nome)}
                    >
                      <div className="save-name">{save.nome}</div>
                      <div className="save-date">{save.data}</div>
                    </div>
                  ))}
                </div>
                
                <div className="form-buttons">
                  <button 
                    type="button"
                    className="secondary-button"
                    onClick={handleBackClick}
                  >
                    Indietro
                  </button>
                  <button 
                    className="main-button load-game-button"
                    onClick={handleLoadSaveClick}
                    disabled={!selectedSaveGame || loading}
                  >
                    {loading ? 'Caricamento...' : 'Carica Partita Selezionata'}
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="no-saves-message">
                  Nessun salvataggio disponibile. Inizia una nuova partita!
                </div>
                <button 
                  className="secondary-button"
                  onClick={handleBackClick}
                >
                  Indietro
                </button>
              </>
            )}
            
            <button 
              className="refresh-button"
              onClick={fetchSaveGames}
              disabled={saveLoading}
            >
              Aggiorna Lista
            </button>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="start-screen">
      <div className="start-screen-container">
        {(error || saveError) && <div className="error-message">{error || saveError}</div>}
        
        {renderContent()}
        
        <div className="start-screen-footer">
          <p>© 2023 Gioco RPG Fantasy - Versione 2.0.0</p>
        </div>
      </div>
    </div>
  );
};

export default StartScreen; 