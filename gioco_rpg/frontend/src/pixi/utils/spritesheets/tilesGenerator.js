/**
 * Utility per generare la definizione di una spritesheet di tile
 * Questo file serve a generare la struttura JSON per le spritesheet
 */

const fs = require('fs');
const path = require('path');

/**
 * Genera la definizione della spritesheet per i tile
 * 
 * @param {string} tilesPath - Percorso alla directory contenente i tile
 * @param {string} outputPath - Percorso dove salvare il file JSON di definizione
 * @param {number} tileSize - Dimensione dei tile (default: 32x32)
 */
function generateTileSpritesheet(tilesPath, outputPath, tileSize = 32) {
  try {
    console.log(`Generazione spritesheet da ${tilesPath}...`);
    
    // Verifica se la directory esiste
    if (!fs.existsSync(tilesPath)) {
      console.error(`La directory ${tilesPath} non esiste!`);
      return;
    }
    
    // Leggi il contenuto della directory
    const files = fs.readdirSync(tilesPath);
    
    // Filtra solo i file PNG
    const pngFiles = files.filter(file => file.toLowerCase().endsWith('.png'));
    
    if (pngFiles.length === 0) {
      console.warn('Nessun file PNG trovato nella directory!');
      return;
    }
    
    console.log(`Trovati ${pngFiles.length} file PNG`);
    
    // Calcola le dimensioni della spritesheet
    const tilesPerRow = Math.ceil(Math.sqrt(pngFiles.length));
    const sheetWidth = tilesPerRow * tileSize;
    const sheetHeight = Math.ceil(pngFiles.length / tilesPerRow) * tileSize;
    
    // Crea l'oggetto di definizione della spritesheet
    const spritesheet = {
      meta: {
        app: "Generatore Spritesheet",
        version: "1.0",
        image: "tiles.png", // Nome del file immagine della spritesheet
        format: "RGBA8888", // Formato dell'immagine
        size: { w: sheetWidth, h: sheetHeight },
        scale: "1"
      },
      frames: {},
      animations: {}
    };
    
    // Popola i frame nella definizione della spritesheet
    for (let i = 0; i < pngFiles.length; i++) {
      const fileName = pngFiles[i];
      const tileName = path.basename(fileName, '.png');
      
      // Calcola la posizione del tile nella spritesheet
      const row = Math.floor(i / tilesPerRow);
      const col = i % tilesPerRow;
      const x = col * tileSize;
      const y = row * tileSize;
      
      // Aggiungi la definizione del frame
      spritesheet.frames[fileName] = {
        frame: { x, y, w: tileSize, h: tileSize },
        rotated: false,
        trimmed: false,
        spriteSourceSize: { x: 0, y: 0, w: tileSize, h: tileSize },
        sourceSize: { w: tileSize, h: tileSize }
      };
      
      // Aggiungi anche una versione senza estensione come alias
      spritesheet.animations[tileName] = [fileName];
    }
    
    // Converti l'oggetto in formato JSON
    const jsonContent = JSON.stringify(spritesheet, null, 2);
    
    // Scrivi il file JSON
    fs.writeFileSync(outputPath, jsonContent);
    
    console.log(`File di definizione della spritesheet salvato in ${outputPath}`);
    console.log(`Dimensioni spritesheet: ${sheetWidth}x${sheetHeight} pixel`);
    console.log(`Creata definizione per ${pngFiles.length} tile`);
    
    // Istruzioni per creare l'immagine
    console.log('\nPer completare la spritesheet:');
    console.log('1. Crea un\'immagine vuota di dimensioni', `${sheetWidth}x${sheetHeight}`);
    console.log('2. Posiziona ogni tile secondo le coordinate definite nel JSON');
    console.log('3. Salva l\'immagine come "tiles.png" nella stessa directory del JSON');
    
    return {
      tileCount: pngFiles.length,
      width: sheetWidth,
      height: sheetHeight,
      tileSize: tileSize,
      outputPath: outputPath
    };
  } catch (error) {
    console.error('Errore durante la generazione della spritesheet:', error);
  }
}

/**
 * Genera la definizione della spritesheet per le entità
 * 
 * @param {string} entitiesPath - Percorso alla directory contenente le entità
 * @param {string} outputPath - Percorso dove salvare il file JSON di definizione
 * @param {number} entityWidth - Larghezza delle entità
 * @param {number} entityHeight - Altezza delle entità
 */
function generateEntitySpritesheet(entitiesPath, outputPath, entityWidth = 32, entityHeight = 48) {
  try {
    console.log(`Generazione spritesheet entità da ${entitiesPath}...`);
    
    // Verifica se la directory esiste
    if (!fs.existsSync(entitiesPath)) {
      console.error(`La directory ${entitiesPath} non esiste!`);
      return;
    }
    
    // Leggi il contenuto della directory
    const files = fs.readdirSync(entitiesPath);
    
    // Filtra solo i file PNG
    const pngFiles = files.filter(file => file.toLowerCase().endsWith('.png'));
    
    if (pngFiles.length === 0) {
      console.warn('Nessun file PNG trovato nella directory!');
      return;
    }
    
    console.log(`Trovate ${pngFiles.length} entità`);
    
    // Calcola le dimensioni della spritesheet
    // Per le entità, usiamo un layout a riga singola per semplificare l'organizzazione
    const sheetWidth = pngFiles.length * entityWidth;
    const sheetHeight = entityHeight;
    
    // Crea l'oggetto di definizione della spritesheet
    const spritesheet = {
      meta: {
        app: "Generatore Spritesheet",
        version: "1.0",
        image: "entities.png", // Nome del file immagine della spritesheet
        format: "RGBA8888", // Formato dell'immagine
        size: { w: sheetWidth, h: sheetHeight },
        scale: "1"
      },
      frames: {},
      animations: {}
    };
    
    // Popola i frame nella definizione della spritesheet
    for (let i = 0; i < pngFiles.length; i++) {
      const fileName = pngFiles[i];
      const entityName = path.basename(fileName, '.png');
      
      // Calcola la posizione dell'entità nella spritesheet
      const x = i * entityWidth;
      const y = 0; // Tutte le entità sono nella stessa riga
      
      // Aggiungi la definizione del frame
      spritesheet.frames[fileName] = {
        frame: { x, y, w: entityWidth, h: entityHeight },
        rotated: false,
        trimmed: false,
        spriteSourceSize: { x: 0, y: 0, w: entityWidth, h: entityHeight },
        sourceSize: { w: entityWidth, h: entityHeight }
      };
      
      // Aggiungi anche una versione senza estensione come alias
      spritesheet.animations[entityName] = [fileName];
    }
    
    // Converti l'oggetto in formato JSON
    const jsonContent = JSON.stringify(spritesheet, null, 2);
    
    // Scrivi il file JSON
    fs.writeFileSync(outputPath, jsonContent);
    
    console.log(`File di definizione della spritesheet salvato in ${outputPath}`);
    console.log(`Dimensioni spritesheet: ${sheetWidth}x${sheetHeight} pixel`);
    console.log(`Creata definizione per ${pngFiles.length} entità`);
    
    // Istruzioni per creare l'immagine
    console.log('\nPer completare la spritesheet:');
    console.log('1. Crea un\'immagine vuota di dimensioni', `${sheetWidth}x${sheetHeight}`);
    console.log('2. Posiziona ogni entità secondo le coordinate definite nel JSON');
    console.log('3. Salva l\'immagine come "entities.png" nella stessa directory del JSON');
    
    return {
      entityCount: pngFiles.length,
      width: sheetWidth,
      height: sheetHeight,
      dimensions: { width: entityWidth, height: entityHeight },
      outputPath: outputPath
    };
  } catch (error) {
    console.error('Errore durante la generazione della spritesheet per entità:', error);
  }
}

// Esempio d'uso:
// generateTileSpritesheet(
//   'path/to/tile/images',
//   'path/to/output/tiles.json',
//   32
// );
//
// generateEntitySpritesheet(
//   'path/to/entity/images',
//   'path/to/output/entities.json',
//   32,
//   48
// );

module.exports = {
  generateTileSpritesheet,
  generateEntitySpritesheet
}; 