// Questo script genera una semplice immagine placeholder che può essere usata
// come fallback quando le immagini reali non sono disponibili

// Crea un canvas per generare l'immagine
function createPlaceholderImage(width = 64, height = 64, color = '#8e7851', text = '?') {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  
  const ctx = canvas.getContext('2d');
  
  // Colore di sfondo
  ctx.fillStyle = color;
  ctx.fillRect(0, 0, width, height);
  
  // Bordo
  ctx.strokeStyle = '#ffffff';
  ctx.lineWidth = 2;
  ctx.strokeRect(4, 4, width - 8, height - 8);
  
  // Testo
  ctx.fillStyle = '#ffffff';
  ctx.font = `${Math.floor(width / 2)}px Arial, sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, width / 2, height / 2);
  
  // Converti in data URL (immagine PNG)
  return canvas.toDataURL('image/png');
}

// Esporta la funzione se in un ambiente Node.js
if (typeof module !== 'undefined' && module.exports) {
  module.exports = createPlaceholderImage;
}

// Se il script è caricato direttamente in un browser, crea un'immagine placeholder
// e la inserisce nel documento
if (typeof window !== 'undefined' && document.body) {
  const img = new Image();
  img.src = createPlaceholderImage();
  document.body.appendChild(img);
}
