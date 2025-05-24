import { useState, useEffect } from 'react';
import { useGame } from '../contexts/GameContext';

/**
 * Hook per gestire l'equipaggiamento iniziale del giocatore e gli oggetti in base alla classe
 */
export default function useItemService() {
  const { state } = useGame();
  const [initialItems, setInitialItems] = useState([]);
  
  // Mappa degli oggetti iniziali per ogni classe
  const classInitialItems = {
    guerriero: [
      {
        id: 'spada-corta-init',
        nome: 'Spada corta',
        tipo: 'arma',
        descrizione: 'Una piccola spada adatta a combattimenti ravvicinati',
        valore: 25,
        effetto: { forza: 3 },
        usabile: true
      },
      {
        id: 'scudo-legno-init',
        nome: 'Scudo di legno',
        tipo: 'armatura',
        descrizione: 'Uno scudo di legno che offre protezione base',
        valore: 15,
        effetto: { difesa: 1 },
        usabile: true
      },
      {
        id: 'armatura-cuoio-init',
        nome: 'Armatura di cuoio',
        tipo: 'armatura',
        descrizione: 'Una leggera armatura di cuoio che offre protezione di base',
        valore: 20,
        effetto: { difesa: 2 },
        usabile: true
      }
    ],
    mago: [
      {
        id: 'bastone-init',
        nome: 'Bastone',
        tipo: 'arma',
        descrizione: 'Un bastone di legno che può essere usato per amplificare i poteri magici',
        valore: 15,
        effetto: { forza: 1, intelligenza: 1 },
        usabile: true
      },
      {
        id: 'veste-mago-init',
        nome: 'Veste da mago',
        tipo: 'armatura',
        descrizione: 'Una veste incantata che migliora le capacità magiche',
        valore: 60,
        effetto: { difesa: 1, intelligenza: 2 },
        usabile: true
      },
      {
        id: 'libro-incantesimi-init',
        nome: 'Libro degli incantesimi',
        tipo: 'accessorio',
        descrizione: 'Un libro antico contenente formule magiche e incantesimi',
        valore: 50,
        effetto: { intelligenza: 1, saggezza: 1 },
        usabile: true
      }
    ],
    ladro: [
      {
        id: 'pugnale-init',
        nome: 'Pugnale',
        tipo: 'arma',
        descrizione: "Un'arma piccola ma letale se usata con precisione",
        valore: 15,
        effetto: { forza: 2, destrezza: 2 },
        usabile: true
      },
      {
        id: 'armatura-cuoio-ladro-init',
        nome: 'Armatura di cuoio',
        tipo: 'armatura',
        descrizione: 'Una leggera armatura di cuoio che offre protezione di base',
        valore: 20,
        effetto: { difesa: 2 },
        usabile: true
      },
      {
        id: 'grimaldelli-init',
        nome: 'Grimaldelli',
        tipo: 'accessorio',
        descrizione: 'Strumenti per scassinare serrature',
        valore: 25,
        effetto: { destrezza: 1 },
        usabile: true
      }
    ],
    chierico: [
      {
        id: 'mazza-init',
        nome: 'Mazza',
        tipo: 'arma',
        descrizione: "Un'arma contundente efficace contro creature non morte",
        valore: 30,
        effetto: { forza: 4 },
        usabile: true
      },
      {
        id: 'scudo-init',
        nome: 'Scudo',
        tipo: 'armatura',
        descrizione: 'Uno scudo metallico robusto che offre buona protezione',
        valore: 35,
        effetto: { difesa: 3 },
        usabile: true
      },
      {
        id: 'simbolo-sacro-init',
        nome: 'Simbolo sacro',
        tipo: 'accessorio',
        descrizione: 'Un simbolo religioso che canalizza il potere divino',
        valore: 40,
        effetto: { saggezza: 2 },
        usabile: true
      }
    ]
  };
  
  // Quando cambia il giocatore, determina l'equipaggiamento iniziale in base alla classe
  useEffect(() => {
    if (state && state.player) {
      const playerClass = state.player.classe?.toLowerCase() || 'guerriero';
      
      // Ottieni gli oggetti iniziali per la classe del giocatore
      const items = classInitialItems[playerClass] || classInitialItems.guerriero;
      setInitialItems(items);
      
      console.log(`useItemService: Caricati ${items.length} oggetti iniziali per classe ${playerClass}`);
    }
  }, [state?.player?.classe]);
  
  // Ottiene l'equipaggiamento iniziale per la classe corrente
  const getInitialItems = () => {
    return initialItems;
  };
  
  // Ottiene l'arma iniziale per la classe corrente
  const getInitialWeapon = () => {
    return initialItems.find(item => item.tipo === 'arma');
  };
  
  // Ottiene l'armatura iniziale per la classe corrente
  const getInitialArmor = () => {
    return initialItems.find(item => item.tipo === 'armatura');
  };
  
  return {
    initialItems,
    getInitialItems,
    getInitialWeapon,
    getInitialArmor
  };
} 