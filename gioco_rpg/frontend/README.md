# Guida API per Frontend React con Pixi.js

Questa documentazione fornisce informazioni su come interfacciare un'applicazione frontend sviluppata con React e Pixi.js con il backend del gioco RPG.

## Indice
- [Panoramica dell'architettura](#panoramica-dellarchitettura)
- [Setup Connessione](#setup-connessione)
- [Eventi WebSocket](#eventi-websocket)
- [Rendering con Pixi.js](#rendering-con-pixijs)
- [Gestione Input](#gestione-input)
- [Audio](#audio)
- [Esempi](#esempi)

## Panoramica dell'architettura

Il backend del gioco è costruito utilizzando un'architettura ECS (Entity-Component-System) e fornisce una serie di API WebSocket per comunicare con il frontend. Il frontend dovrebbe essere strutturato come un'applicazione React con un renderer Pixi.js integrato per visualizzare elementi di gioco, mappe e UI.

```
Frontend (React + Pixi.js) <--> Socket.IO <--> Backend (Flask + ECS)
```

## Setup Connessione

Per iniziare, è necessario installare le dipendenze necessarie:

```bash
npm install react react-dom pixi.js socket.io-client
```

Quindi, creare una connessione Socket.IO all'URL del server:

```javascript
import io from 'socket.io-client';

// Connessione al server
const socket = io('http://localhost:5000');

// Gestione eventi di connessione
socket.on('connect', () => {
  console.log('Connesso al server');
});

socket.on('disconnect', () => {
  console.log('Disconnesso dal server');
});

// Gestione errori
socket.on('error', (error) => {
  console.error('Errore socket:', error);
});
```

## Eventi WebSocket

Di seguito sono elencati i principali eventi WebSocket che vengono utilizzati per la comunicazione tra frontend e backend:

### Eventi da Frontend a Backend

| Evento | Descrizione | Parametri |
|--------|-------------|-----------|
| `join_game` | Entra in una sessione di gioco | `{id_sessione: string}` |
| `game_event` | Invia un evento di gioco | `{id_sessione: string, type: string, data: object}` |
| `request_map_data` | Richiede dati mappa | `{id_sessione: string, map_id: string}` |
| `player_input` | Invia input del giocatore | `{id_sessione: string, type: string, data: object}` |
| `request_game_state` | Richiede stato del gioco | `{id_sessione: string}` |
| `request_render_update` | Richiede aggiornamento rendering | `{id_sessione: string}` |
| `process_render_queue` | Processa coda di rendering | `{id_sessione: string, camera?: object}` |
| `set_camera` | Imposta parametri camera | `{id_sessione: string, x: number, y: number, zoom: number, viewport_width: number, viewport_height: number}` |
| `play_audio` | Riproduce un audio | `{type: "sound"|"music", name/track: string, volume?: number, loop?: boolean, position?: [x,y], fade_in?: number}` |

### Eventi da Backend a Frontend

| Evento | Descrizione | Dati |
|--------|-------------|------|
| `game_update` | Aggiornamento stato gioco | `{entities: array, events: array, timestamp: number}` |
| `map_data` | Dati mappa | `{id: string, tiles: array, width: number, height: number, layers: array}` |
| `render_update` | Aggiornamento rendering | `{events: array, timestamp: number}` |
| `render_entity` | Renderizza entità | `{id: string, type: string, x: number, y: number, sprite: string, ...}` |
| `render_particles` | Renderizza sistema particelle | `{id: string, effect_type: string, particles: array, ...}` |
| `render_ui` | Renderizza elemento UI | `{id: string, type: string, x: number, y: number, ...}` |
| `render_complete` | Rendering completato | `{render_id: string, frame: number, fps: number}` |
| `render_clear` | Pulisci schermo | `{render_id: string}` |
| `camera_updated` | Camera aggiornata | `{camera: object, timestamp: number}` |
| `message` | Messaggio di gioco | `{text: string, type: "narrative"|"system"|"error"}` |
| `input_request` | Richiesta input | `{prompt: string}` |
| `audio_started` | Audio iniziato | `{type: string, audio_id: string}` |

## Rendering con Pixi.js

Il rendering viene gestito attraverso Pixi.js, che dovrebbe essere integrato in un componente React. Il server invia eventi di rendering che il client deve interpretare per creare/aggiornare gli oggetti Pixi.js appropriati.

Esempio di componente React-Pixi.js:

```jsx
import React, { useRef, useEffect } from 'react';
import * as PIXI from 'pixi.js';

const GameRenderer = ({ socket, sessionId }) => {
  const pixiContainer = useRef(null);
  const app = useRef(null);
  const entities = useRef({});
  
  useEffect(() => {
    // Inizializza Pixi Application
    if (!app.current) {
      app.current = new PIXI.Application({
        width: 800,
        height: 600,
        backgroundColor: 0x1099bb,
        resolution: window.devicePixelRatio || 1,
      });
      pixiContainer.current.appendChild(app.current.view);
      
      // Sottoscrivi agli eventi di rendering
      socket.on('render_clear', handleRenderClear);
      socket.on('render_entity', handleRenderEntity);
      socket.on('render_particles', handleRenderParticles);
      socket.on('render_ui', handleRenderUI);
      socket.on('render_complete', handleRenderComplete);
      
      // Avvia il ciclo di rendering
      requestRenderUpdates();
    }
    
    return () => {
      // Cleanup alla dismissione
      socket.off('render_clear', handleRenderClear);
      socket.off('render_entity', handleRenderEntity);
      socket.off('render_particles', handleRenderParticles);
      socket.off('render_ui', handleRenderUI);
      socket.off('render_complete', handleRenderComplete);
      
      if (app.current) {
        app.current.destroy(true, true);
        app.current = null;
      }
    };
  }, []);
  
  const requestRenderUpdates = () => {
    socket.emit('request_render_update', { id_sessione: sessionId });
  };
  
  const handleRenderClear = (data) => {
    // Pulisci tutti gli oggetti dalla scena
    app.current.stage.removeChildren();
    entities.current = {};
  };
  
  const handleRenderEntity = (data) => {
    // Gestisci rendering entità
    // ...
  };
  
  const handleRenderParticles = (data) => {
    // Gestisci rendering particelle
    // ...
  };
  
  const handleRenderUI = (data) => {
    // Gestisci rendering UI
    // ...
  };
  
  const handleRenderComplete = (data) => {
    // Richiedi il prossimo aggiornamento quando il frame è completato
    requestRenderUpdates();
  };
  
  return <div ref={pixiContainer} className="game-renderer"></div>;
};

export default GameRenderer;
```

## Gestione Input

Gli input utente (click, tastiera, touch) devono essere catturati nel frontend e inviati al backend tramite eventi WebSocket:

```javascript
// Gestione click su elemento
const handleElementClick = (elementId) => {
  socket.emit('player_input', {
    id_sessione: sessionId,
    type: 'click',
    data: {
      target: elementId
    }
  });
};

// Gestione input da tastiera
const handleKeyPress = (key) => {
  socket.emit('player_input', {
    id_sessione: sessionId,
    type: 'keypress',
    data: {
      key: key
    }
  });
};
```

## Audio

Il sistema audio è supportato attraverso eventi WebSocket specifici:

```javascript
// Riproduzione suono
const playSound = (soundName, volume = 1.0, loop = false) => {
  socket.emit('play_audio', {
    type: 'sound',
    name: soundName,
    volume: volume,
    loop: loop
  });
};

// Riproduzione musica
const playMusic = (trackName, volume = 1.0, fadeIn = 0.0) => {
  socket.emit('play_audio', {
    type: 'music',
    track: trackName,
    volume: volume,
    fade_in: fadeIn
  });
};
```

## Esempi

### Caricamento e rendering mappa

```javascript
// Richiedi dati mappa
socket.emit('request_map_data', {
  id_sessione: sessionId,
  map_id: 'taverna'
});

// Gestisci risposta
socket.on('map_data', (data) => {
  // Crea tilemap con Pixi.js
  const tilemap = createTilemap(data);
  app.stage.addChild(tilemap);
});
```

### Gestione movimenti giocatore

```javascript
// Gestione tasti freccia
window.addEventListener('keydown', (event) => {
  let direction = null;
  
  switch(event.key) {
    case 'ArrowUp':
      direction = 'nord';
      break;
    case 'ArrowDown':
      direction = 'sud';
      break;
    case 'ArrowLeft':
      direction = 'ovest';
      break;
    case 'ArrowRight':
      direction = 'est';
      break;
  }
  
  if (direction) {
    socket.emit('player_input', {
      id_sessione: sessionId,
      type: 'move',
      data: {
        direction: direction
      }
    });
  }
});
```

### Interazione con NPC

```javascript
// Funzione per iniziare dialogo con NPC
const interactWithNPC = (npcId) => {
  socket.emit('game_event', {
    id_sessione: sessionId,
    type: 'interact',
    data: {
      target_type: 'npc',
      target_id: npcId
    }
  });
};

// Gestire risposta dialogo
socket.on('show_dialog', (dialogData) => {
  // Mostrare dialogo UI
  renderDialog(dialogData);
});
```

## Integrazione con React

Esempio di struttura dell'app React:

```jsx
import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import GameRenderer from './components/GameRenderer';
import DialogBox from './components/DialogBox';
import Inventory from './components/Inventory';
import LoginScreen from './components/LoginScreen';

const App = () => {
  const [socket, setSocket] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [gameState, setGameState] = useState({
    isLoggedIn: false,
    currentDialog: null,
    inventoryOpen: false,
    messages: []
  });
  
  useEffect(() => {
    // Inizializza socket
    const newSocket = io('http://localhost:5000');
    setSocket(newSocket);
    
    // Gestione eventi
    newSocket.on('connect', handleConnect);
    newSocket.on('message', handleMessage);
    newSocket.on('show_dialog', handleShowDialog);
    newSocket.on('show_inventory', handleShowInventory);
    
    return () => {
      newSocket.disconnect();
    };
  }, []);
  
  // Handlers per vari eventi...
  
  return (
    <div className="game-container">
      {!gameState.isLoggedIn ? (
        <LoginScreen socket={socket} onLogin={handleLogin} />
      ) : (
        <>
          <GameRenderer socket={socket} sessionId={sessionId} />
          
          {gameState.currentDialog && (
            <DialogBox 
              dialog={gameState.currentDialog} 
              onChoiceSelected={handleDialogChoice} 
            />
          )}
          
          {gameState.inventoryOpen && (
            <Inventory 
              items={gameState.inventory} 
              onClose={handleCloseInventory} 
              onItemUse={handleItemUse} 
            />
          )}
          
          <div className="message-log">
            {gameState.messages.map((msg, index) => (
              <div key={index} className={`message ${msg.type}`}>
                {msg.text}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default App;
```

Questa documentazione fornisce le basi per integrare un frontend React con Pixi.js al backend del gioco RPG. Ogni progetto può richiedere personalizzazioni aggiuntive in base alle specifiche esigenze. 