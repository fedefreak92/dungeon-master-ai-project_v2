import { useState, useEffect } from 'react';
import ioService from '../services/IOService';

/**
 * Hook personalizzato per utilizzare il servizio IO nei componenti React
 * @param {Object} options - Opzioni di configurazione
 * @returns {Object} - Metodi e stato del servizio IO
 */
export default function useIOService(options = {}) {
  // Stati per i vari elementi dell'interfaccia
  const [messaggi, setMessaggi] = useState([]);
  const [dialoghi, setDialoghi] = useState([]);
  const [menuContestuale, setMenuContestuale] = useState(null);
  const [inventario, setInventario] = useState({ aperto: false, items: [], capacity: 0 });
  const [tooltip, setTooltip] = useState(null);
  const [elementiInterattivi, setElementiInterattivi] = useState({});
  const [animazioni, setAnimazioni] = useState([]);
  const [mappa, setMappa] = useState({ celle: [], entita: [], visibilita: [] });

  // Carica lo stato iniziale
  useEffect(() => {
    // Inizializza con lo stato corrente del servizio
    const statoUI = ioService.getStatoUI();
    setMessaggi(statoUI.messaggi);
    setDialoghi(statoUI.uiAttiva.dialoghi);
    setMenuContestuale(statoUI.uiAttiva.menuContestuale);
    setInventario({
      aperto: statoUI.uiAttiva.inventarioAperto,
      items: statoUI.uiAttiva.inventarioData?.items || [],
      capacity: statoUI.uiAttiva.inventarioData?.capacity || 0
    });
    setTooltip(statoUI.uiAttiva.tooltip);
    setElementiInterattivi(statoUI.elementiInterattivi);
    setAnimazioni(statoUI.animazioniAttive);
    setMappa(statoUI.mappaVisuale);

    // Registra handler per vari eventi
    const handlers = {
      messaggio: (msg) => setMessaggi(prev => [...prev, msg]),
      clearMessaggi: () => setMessaggi([]),
      dialogoMostrato: (dialogo) => setDialoghi(prev => [...prev, dialogo]),
      dialogoChiuso: (dialogo) => setDialoghi(prev => prev.filter(d => d.id !== dialogo.id)),
      menuMostrato: (menu) => setMenuContestuale(menu),
      menuNascosto: () => setMenuContestuale(null),
      inventarioMostrato: (data) => setInventario({ aperto: true, items: data.items, capacity: data.capacity }),
      inventarioNascosto: () => setInventario(prev => ({ ...prev, aperto: false })),
      tooltipMostrato: (tip) => setTooltip(tip),
      tooltipNascosto: () => setTooltip(null),
      elementoAggiunto: (elemento) => setElementiInterattivi(prev => ({ ...prev, [elemento.id]: elemento })),
      elementoRimosso: (elemento) => setElementiInterattivi(prev => {
        const newState = { ...prev };
        delete newState[elemento.id];
        return newState;
      }),
      statoElementoAggiornato: (elemento) => setElementiInterattivi(prev => ({
        ...prev,
        [elemento.id]: { ...prev[elemento.id], ...elemento }
      })),
      animazioneAggiunta: (anim) => setAnimazioni(prev => [...prev, anim]),
      animazioneCompletata: (anim) => setAnimazioni(prev => prev.filter(a => a.id !== anim.id)),
      mappaAggiornata: (datiMappa) => setMappa(datiMappa)
    };

    // Registra tutti gli handler
    const handlerIds = {};
    Object.entries(handlers).forEach(([evento, handler]) => {
      handlerIds[evento] = ioService.on(evento, handler);
    });

    // Pulizia alla chiusura
    return () => {
      // Rimuovi tutti gli handler registrati
      Object.entries(handlerIds).forEach(([evento, id]) => {
        ioService.off(evento, id);
      });
    };
  }, []);

  // Funzione ausiliaria per inviare input interattivi
  const inviaInput = (tipo, target = null, dati = {}) => {
    return ioService.inviaEventoInput(tipo, target, dati);
  };

  // Metodi comuni wrappati
  return {
    // Metodi di base
    mostraMessaggio: ioService.mostraMessaggio.bind(ioService),
    messaggioSistema: ioService.messaggioSistema.bind(ioService),
    messaggioErrore: ioService.messaggioErrore.bind(ioService),
    
    // Metodi per dialoghi
    mostraDialogo: ioService.mostraDialogo.bind(ioService),
    chiudiDialogo: ioService.chiudiDialogo.bind(ioService),
    selezionaOpzioneDialogo: ioService.selezionaOpzioneDialogo.bind(ioService),
    
    // Metodi per menu contestuale
    mostraMenuContestuale: ioService.mostraMenuContestuale.bind(ioService),
    nascondiMenuContestuale: ioService.nascondiMenuContestuale.bind(ioService),
    selezionaOpzioneMenu: ioService.selezionaOpzioneMenu.bind(ioService),
    
    // Metodi per inventario
    mostraInventario: ioService.mostraInventario.bind(ioService),
    nascondiInventario: ioService.nascondiInventario.bind(ioService),
    
    // Metodi per tooltips
    mostraTooltip: ioService.mostraTooltip.bind(ioService),
    nascondiTooltip: ioService.nascondiTooltip.bind(ioService),
    
    // Metodi per elementi interattivi
    aggiungiElementoInterattivo: ioService.aggiungiElementoInterattivo.bind(ioService),
    rimuoviElementoInterattivo: ioService.rimuoviElementoInterattivo.bind(ioService),
    
    // Metodi per animazioni
    aggiungiAnimazione: ioService.aggiungiAnimazione.bind(ioService),
    
    // Metodi per eventi
    inviaInput,
    
    // Stati correnti
    messaggi,
    dialoghi,
    menuContestuale,
    inventario,
    tooltip,
    elementiInterattivi,
    animazioni,
    mappa
  };
} 