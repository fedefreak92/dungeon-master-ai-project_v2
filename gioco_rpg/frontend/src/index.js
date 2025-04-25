import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Importa il font Cinzel da Google Fonts
const link = document.createElement('link');
link.rel = 'stylesheet';
link.href = 'https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&display=swap';
document.head.appendChild(link);

// Crea il root dell'applicazione
const root = ReactDOM.createRoot(document.getElementById('root'));

// Renderizza l'app
// Temporaneamente disabilitato StrictMode per evitare problemi con i WebSocket
// in modalità sviluppo (doppio mounting/unmounting dei componenti)
root.render(
  // <React.StrictMode>
    <App />
  // </React.StrictMode>
); 