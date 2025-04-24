/**
 * Servizio per gestire gli eventi specifici del gioco RPG tramite Socket.IO
 */

import socketIOService from './socketIOService';

class GameEventService {
    constructor() {
        // Mantiene una cache delle risposte per richieste frequenti
        this.cache = {
            mapList: null,
            mapData: {},
        };
        
        // Flag per controllare se siamo già connessi
        this.isInitialized = false;
    }

    /**
     * Inizializza il servizio e si connette al server
     * @returns {Promise} Promise che si risolve quando la connessione è stabilita
     */
    initialize() {
        if (this.isInitialized) {
            return Promise.resolve();
        }
        
        return socketIOService.connect()
            .then(() => {
                this.isInitialized = true;
                this._registerEventHandlers();
                return Promise.resolve();
            });
    }

    /**
     * Registra gli handler per eventi comuni
     * @private
     */
    _registerEventHandlers() {
        // Eventi di mappa
        socketIOService.on('map_changed', this._handleMapChanged.bind(this));
        socketIOService.on('map_data_response', this._handleMapDataResponse.bind(this));
        socketIOService.on('map_list_response', this._handleMapListResponse.bind(this));
        
        // Eventi di stato
        socketIOService.on('game_state', this._handleGameStateUpdate.bind(this));
        socketIOService.on('game_state_update', this._handleGameStateUpdate.bind(this));
        
        // Altri eventi di gioco
        socketIOService.on('entity_moved', this._handleEntityMoved.bind(this));
        socketIOService.on('entity_spawned', this._handleEntitySpawned.bind(this));
        socketIOService.on('entity_despawned', this._handleEntityDespawned.bind(this));
    }

    /**
     * Richiede la lista delle mappe disponibili
     * @param {string} sessionId - ID della sessione di gioco
     * @returns {Promise} Promise che si risolve con la lista delle mappe
     */
    requestMapList(sessionId) {
        return this.initialize()
            .then(() => {
                // Se abbiamo la cache, usiamo quella
                if (this.cache.mapList) {
                    return Promise.resolve(this.cache.mapList);
                }
                
                // Altrimenti facciamo la richiesta
                return socketIOService.emit('MAP_LIST_REQUEST', { session_id: sessionId });
            });
    }

    /**
     * Richiede il cambio della mappa corrente
     * @param {string} sessionId - ID della sessione di gioco
     * @param {string} mapId - ID della mappa da caricare
     * @returns {Promise} Promise che si risolve quando la mappa è cambiata
     */
    requestMapChange(sessionId, mapId) {
        return this.initialize()
            .then(() => {
                return socketIOService.emit('MAP_CHANGE_REQUEST', { 
                    session_id: sessionId,
                    map_id: mapId
                });
            });
    }

    /**
     * Richiede i dati di una mappa specifica
     * @param {string} sessionId - ID della sessione di gioco
     * @param {string} mapId - ID della mappa da caricare
     * @returns {Promise} Promise che si risolve con i dati della mappa
     */
    requestMapData(sessionId, mapId) {
        return this.initialize()
            .then(() => {
                // Se abbiamo la cache per questa mappa, usiamo quella
                if (this.cache.mapData[mapId]) {
                    return Promise.resolve(this.cache.mapData[mapId]);
                }
                
                // Altrimenti facciamo la richiesta
                return socketIOService.emit('MAP_DATA_REQUEST', { 
                    session_id: sessionId,
                    map_id: mapId
                });
            });
    }

    /**
     * Richiede lo stato corrente del gioco
     * @param {string} sessionId - ID della sessione di gioco
     * @param {boolean} includeEntities - Se includere le entità nello stato
     * @param {boolean} includeMap - Se includere i dati della mappa nello stato
     * @returns {Promise} Promise che si risolve con lo stato del gioco
     */
    requestGameState(sessionId, includeEntities = true, includeMap = true) {
        return this.initialize()
            .then(() => {
                return socketIOService.emit('MAP_STATE_REQUEST', { 
                    session_id: sessionId,
                    include_entities: includeEntities,
                    include_map: includeMap
                });
            });
    }

    /**
     * Gestisce l'evento di cambio mappa
     * @param {object} data - Dati dell'evento
     * @private
     */
    _handleMapChanged(data) {
        // Evento emesso quando la mappa cambia
        // Potrebbe contenere informazioni sulla nuova mappa
        console.log('Mappa cambiata:', data);
    }

    /**
     * Gestisce la risposta con i dati della mappa
     * @param {object} data - Dati dell'evento
     * @private
     */
    _handleMapDataResponse(data) {
        // Salva nella cache i dati della mappa
        if (data && data.map_id) {
            this.cache.mapData[data.map_id] = data;
        }
    }

    /**
     * Gestisce la risposta con la lista delle mappe
     * @param {object} data - Dati dell'evento
     * @private
     */
    _handleMapListResponse(data) {
        // Salva nella cache la lista delle mappe
        if (data && data.maps) {
            this.cache.mapList = data.maps;
        }
    }

    /**
     * Gestisce l'aggiornamento dello stato di gioco
     * @param {object} data - Dati dell'evento
     * @private
     */
    _handleGameStateUpdate(data) {
        // Evento emesso quando lo stato del gioco cambia
        console.log('Stato di gioco aggiornato:', data);
    }

    /**
     * Gestisce l'evento di movimento di un'entità
     * @param {object} data - Dati dell'evento
     * @private
     */
    _handleEntityMoved(data) {
        // Evento emesso quando un'entità si muove
        console.log('Entità mossa:', data);
    }

    /**
     * Gestisce l'evento di spawn di un'entità
     * @param {object} data - Dati dell'evento
     * @private
     */
    _handleEntitySpawned(data) {
        // Evento emesso quando un'entità appare sulla mappa
        console.log('Entità spawned:', data);
    }

    /**
     * Gestisce l'evento di despawn di un'entità
     * @param {object} data - Dati dell'evento
     * @private
     */
    _handleEntityDespawned(data) {
        // Evento emesso quando un'entità scompare dalla mappa
        console.log('Entità despawned:', data);
    }

    /**
     * Pulisce le cache del servizio
     */
    clearCache() {
        this.cache.mapList = null;
        this.cache.mapData = {};
    }
}

// Esporta un'istanza singleton del servizio
const gameEventService = new GameEventService();
export default gameEventService; 