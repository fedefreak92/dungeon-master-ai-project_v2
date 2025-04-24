/**
 * Servizio di diagnostica per il debugging del renderer e WebSocket
 * Raccoglie e invia dati al server per analisi
 */
import axios from 'axios';
import socketService from '../api/socketService';

const API_URL = 'http://localhost:5000';

class DiagnosticService {
  constructor() {
    this.isEnabled = process.env.NODE_ENV !== 'production';
    this.diagnosticData = {
      viewport: {
        width: 0,
        height: 0,
        scale: 1.0,
        center_x: 0,
        center_y: 0
      },
      textures: [],
      socket: {
        connected: false,
        latency: null,
        sent: 0,
        received: 0,
        errors: 0
      }
    };
    
    // Imposta intervallo di report solo in modalità sviluppo
    if (this.isEnabled) {
      this.reportInterval = setInterval(() => this.sendReport(), 10000);
      
      // Monitor per gli errori di Pixi.js
      if (window.PIXI) {
        this.setupPixiErrorMonitor();
      }
      
      console.log('Servizio diagnostica attivato in modalità sviluppo');
    }
  }
  
  /**
   * Configura il monitoraggio degli errori Pixi
   */
  setupPixiErrorMonitor() {
    const originalError = console.error;
    
    // Override di console.error per catturare errori Pixi
    console.error = (...args) => {
      // Richiama l'originale
      originalError.apply(console, args);
      
      // Controlla se è un errore Pixi
      const errorString = args.join(' ');
      if (errorString.includes('PIXI') || 
          errorString.includes('WebGL') || 
          errorString.includes('texture') ||
          errorString.includes('shader')) {
        this.logRenderingError(errorString);
      }
    };
  }
  
  /**
   * Aggiorna informazioni sul viewport
   * @param {Object} viewportData - Dati sul viewport Pixi
   */
  updateViewport(viewportData) {
    if (!this.isEnabled) return;
    
    this.diagnosticData.viewport = {
      ...this.diagnosticData.viewport,
      ...viewportData
    };
    
    // Invia aggiornamento immediato per il viewport
    this.sendViewportUpdate();
  }
  
  /**
   * Registra una texture caricata
   * @param {Object} texture - Informazioni sulla texture
   */
  registerTexture(texture) {
    if (!this.isEnabled) return;
    
    // Estrai solo i dati necessari
    const textureInfo = {
      url: texture.baseTexture ? texture.baseTexture.resource.url : texture.url,
      width: texture.width,
      height: texture.height,
      loaded: texture.baseTexture ? texture.baseTexture.valid : texture.valid,
      timestamp: Date.now()
    };
    
    // Evita duplicati
    const existingIndex = this.diagnosticData.textures.findIndex(t => t.url === textureInfo.url);
    if (existingIndex >= 0) {
      this.diagnosticData.textures[existingIndex] = textureInfo;
    } else {
      this.diagnosticData.textures.push(textureInfo);
    }
  }
  
  /**
   * Aggiorna statistiche WebSocket
   */
  updateSocketStats() {
    if (!this.isEnabled) return;
    
    // Ottieni statistiche dal servizio socket
    const stats = socketService.getStats();
    
    this.diagnosticData.socket = {
      connected: stats.connected,
      latency: stats.latency,
      sent: stats.packetStats.sent,
      received: stats.packetStats.received,
      errors: stats.packetStats.errors,
      sessionId: stats.sessionId,
      socketId: stats.socketId
    };
  }
  
  /**
   * Registra un errore di rendering
   * @param {string} errorMessage - Messaggio di errore
   */
  logRenderingError(errorMessage) {
    if (!this.isEnabled) return;
    
    console.warn('Errore rendering rilevato:', errorMessage);
    
    // Invia al server
    axios.post(`${API_URL}/api/diagnostics/error`, {
      type: 'rendering',
      message: errorMessage,
      timestamp: Date.now(),
      viewport: this.diagnosticData.viewport,
      browser: navigator.userAgent
    }).catch(err => {
      console.error('Impossibile inviare log errore:', err);
    });
  }
  
  /**
   * Invia i dati di diagnostica al server
   */
  async sendReport() {
    if (!this.isEnabled) return;
    
    try {
      // Aggiorna statistiche WebSocket prima dell'invio
      this.updateSocketStats();
      
      // Invia dati texture
      await axios.post(`${API_URL}/api/diagnostics/textures`, {
        textures: this.diagnosticData.textures
      });
      
      // Invia statistiche WebSocket
      await axios.post(`${API_URL}/api/diagnostics/websocket`, {
        connections: this.diagnosticData.socket.connected ? 1 : 0,
        events_sent: this.diagnosticData.socket.sent,
        events_received: this.diagnosticData.socket.received,
        sessions: {
          [this.diagnosticData.socket.socketId || 'unknown']: {
            session_id: this.diagnosticData.socket.sessionId,
            connected_at: new Date().toISOString(),
            latency: this.diagnosticData.socket.latency
          }
        }
      });
      
      console.debug('Report diagnostica inviato con successo');
    } catch (error) {
      console.error('Errore invio report diagnostica:', error);
    }
  }
  
  /**
   * Invia solo l'aggiornamento del viewport
   */
  async sendViewportUpdate() {
    if (!this.isEnabled) return;
    
    try {
      const params = new URLSearchParams({
        update: 'true',
        viewport_data: JSON.stringify(this.diagnosticData.viewport),
        timestamp: Date.now()
      });
      
      await axios.get(`${API_URL}/api/diagnostics/frontend?${params}`);
    } catch (error) {
      console.error('Errore invio aggiornamento viewport:', error);
    }
  }
  
  /**
   * Verifica la disponibilità di asset e risorse
   * @returns {Promise<Object>} Risultato della verifica
   */
  async checkAssets() {
    try {
      const response = await axios.get(`${API_URL}/api/diagnostics/assets-check`);
      return response.data;
    } catch (error) {
      console.error('Errore nella verifica degli asset:', error);
      return { error: error.message };
    }
  }
  
  /**
   * Richiede ed esegue il test di rendering
   * @returns {Promise<Object>} Mappa e entità di test
   */
  async requestRenderTest() {
    try {
      const response = await axios.get(`${API_URL}/api/diagnostics/render-test`);
      return response.data;
    } catch (error) {
      console.error('Errore nella richiesta del test di rendering:', error);
      return { error: error.message };
    }
  }
  
  /**
   * Esegue diagnostica completa con risultati dettagliati
   * @returns {Promise<Object>} Risultati diagnostica
   */
  async runDiagnostics() {
    try {
      // Update socket stats
      this.updateSocketStats();
      
      // Esegui controlli
      const [assets, renderTest, viewport] = await Promise.all([
        this.checkAssets(),
        this.requestRenderTest(),
        axios.get(`${API_URL}/api/diagnostics/frontend`)
      ]);
      
      // Prepara report
      const report = {
        timestamp: Date.now(),
        viewport: viewport.data.viewport,
        socket: this.diagnosticData.socket,
        assets: assets,
        renderTest: renderTest,
        textures: {
          count: this.diagnosticData.textures.length,
          loaded: this.diagnosticData.textures.filter(t => t.loaded).length
        }
      };
      
      console.log('Risultati diagnostica:', report);
      return report;
    } catch (error) {
      console.error('Errore durante la diagnostica:', error);
      return { error: error.message };
    }
  }
}

// Esporta istanza singleton
export default new DiagnosticService(); 