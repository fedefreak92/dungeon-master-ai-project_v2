import { useState, useEffect, useCallback } from 'react';

/**
 * Hook personalizzato per gestire gli input da tastiera
 * @param {Object} options - Opzioni per la gestione degli input
 * @returns {Object} - Stato dei tasti e funzioni helper
 */
export default function useKeyboard(options = {}) {
  const [keysPressed, setKeysPressed] = useState({});
  
  // Opzioni di configurazione
  const {
    preventDefault = true,
    stopPropagation = false,
    keyFilter = null,
    disabled = false
  } = options;
  
  // Verifica se un tasto è premuto
  const isKeyDown = useCallback(
    (keyCode) => !!keysPressed[keyCode],
    [keysPressed]
  );
  
  // Controlla se tutti i tasti specificati sono premuti
  const areKeysDown = useCallback(
    (keyCodes = []) => keyCodes.every(code => !!keysPressed[code]),
    [keysPressed]
  );
  
  // Gestione dell'evento keydown
  const handleKeyDown = useCallback(
    (event) => {
      if (disabled) return;
      
      // Filtra i tasti se è stato specificato un filtro
      if (keyFilter && !keyFilter(event.code)) return;
      
      if (preventDefault) event.preventDefault();
      if (stopPropagation) event.stopPropagation();
      
      setKeysPressed(prev => ({
        ...prev,
        [event.code]: true
      }));
    },
    [disabled, keyFilter, preventDefault, stopPropagation]
  );
  
  // Gestione dell'evento keyup
  const handleKeyUp = useCallback(
    (event) => {
      if (disabled) return;
      
      // Filtra i tasti se è stato specificato un filtro
      if (keyFilter && !keyFilter(event.code)) return;
      
      if (preventDefault) event.preventDefault();
      if (stopPropagation) event.stopPropagation();
      
      setKeysPressed(prev => ({
        ...prev,
        [event.code]: false
      }));
    },
    [disabled, keyFilter, preventDefault, stopPropagation]
  );
  
  // Aggiungi e rimuovi gli event listener
  useEffect(() => {
    if (disabled) return;
    
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    
    // Pulizia al dismount
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [disabled, handleKeyDown, handleKeyUp]);
  
  // Resetta lo stato quando disabled cambia a true
  useEffect(() => {
    if (disabled) {
      setKeysPressed({});
    }
  }, [disabled]);
  
  return {
    keysPressed,
    isKeyDown,
    areKeysDown
  };
} 