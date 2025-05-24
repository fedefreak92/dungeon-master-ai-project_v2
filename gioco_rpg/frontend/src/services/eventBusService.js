/**
 * EventBusService - Implementazione client-side del sistema EventBus
 * Gestisce gli eventi dell'applicazione frontend e la comunicazione con il server
 */

import socketService from './socketService';
import entityManager from '../pixi/entities/EntityManager'; // Importa l'istanza singleton

// Placeholder per ottenere l'ID del giocatore corrente e la scena
// Questi dovrebbero essere gestiti da un servizio di stato o contesto più robusto.
let currentLocalPlayerId = null;
let currentPixiSceneId = 'default_scene'; // Valore di default usato anche in EntityManager

// Funzione per MapPage (o chi gestisce lo stato del player) per impostare l'ID del giocatore
export function setLocalPlayerId(id) {
    currentLocalPlayerId = id;
    console.log(`[eventBusService] ID giocatore locale impostato a: ${id}`);
}

export function setCurrentPixiSceneId(id) {
    currentPixiSceneId = id;
    console.log(`[eventBusService] ID scena Pixi corrente impostato a: ${id}`);
}

class EventBusService {
    constructor() {
        this.subscribers = {};
        this.subscriberStats = {}; // Per tracking degli eventi e prevenire leak
        this.socketEventMap = {
            // Socket → EventBus (eventi in arrivo dal server)
            'map_data': 'MAP_DATA_RECEIVED',
            'map_change': 'MAP_CHANGED',
            'entity_moved': 'ENTITY_MOVED',
            'entity_spawn': 'ENTITY_SPAWNED',
            'entity_despawn': 'ENTITY_DESPAWNED',
            'combat_start': 'COMBAT_STARTED',
            'combat_end': 'COMBAT_ENDED',
            'combat_action_required': 'COMBAT_ACTION_REQUIRED',
            'damage_dealt': 'DAMAGE_DEALT',
            'dialog_open': 'DIALOG_OPENED',
            'dialog_close': 'DIALOG_CLOSED',
            'inventory_toggle': 'INVENTORY_TOGGLED',
            'trigger_activated': 'TRIGGER_ACTIVATED',
            'treasure_found': 'TREASURE_FOUND',
            
            // EventBus → Socket (eventi da inviare al server)
            'PLAYER_MOVE': { type: 'game_event', dataType: 'player_move' },
            'PLAYER_ATTACK': { type: 'game_event', dataType: 'player_attack' },
            'PLAYER_USE_ITEM': { type: 'game_event', dataType: 'use_item' },
            'PLAYER_INTERACT': { type: 'game_event', dataType: 'player_interact' }
        };
        
        this._setupSocketListeners();
        
        // Registro per gli eventi di sistema
        this._registerSystemHandlers();
        
        console.log('EventBusService inizializzato');
        
        // Controllo periodico per memory leak
        this._setupLeakDetection();
    }
    
    /**
     * Configura il rilevamento di memory leak
     */
    _setupLeakDetection() {
        // Ogni 60 secondi controlla se ci sono listener che non vengono più chiamati
        setInterval(() => {
            const now = Date.now();
            let orphanedSubscribers = 0;
            
            Object.keys(this.subscriberStats).forEach(id => {
                const stats = this.subscriberStats[id];
                // Se non chiamato negli ultimi 5 minuti e creato da più di 10 minuti, potrebbe essere un leak
                if ((now - stats.lastCalled > 5 * 60 * 1000) && 
                    (now - stats.createdAt > 10 * 60 * 1000)) {
                    console.warn('Possibile memory leak:', stats);
                    orphanedSubscribers++;
                }
            });
            
            if (orphanedSubscribers > 0) {
                console.warn(`Rilevati ${orphanedSubscribers} subscriber potenzialmente orfani. Verificare che useEffect chiami la funzione di cleanup.`);
            }
        }, 60 * 1000);
    }
    
    /**
     * Configura i listener per gli eventi socket
     */
    _setupSocketListeners() {
        socketService.onConnected(() => {
            // Quando il socket si connette, configuriamo tutti i listener
            Object.keys(this.socketEventMap).forEach(socketEvent => {
                // Solo per gli eventi in entrata (socket → eventBus)
                if (typeof this.socketEventMap[socketEvent] === 'string') {
                    socketService.on(socketEvent, (data) => {
                        this.emit(this.socketEventMap[socketEvent], data);
                    });
                }
            });
            
            // Evento socket connesso
            this.emit('SOCKET_CONNECTED');
        });
        
        socketService.onDisconnected(() => {
            this.emit('SOCKET_DISCONNECTED');
        });
    }
    
    /**
     * Registra gli handler di sistema
     */
    _registerSystemHandlers() {
        // Handler per eventi che devono essere inviati al server
        Object.keys(this.socketEventMap).forEach(eventType => {
            // Solo per gli eventi in uscita (eventBus → socket)
            if (typeof this.socketEventMap[eventType] === 'object') {
                this.on(eventType, (data) => {
                    const config = this.socketEventMap[eventType];
                    if (config.type === 'game_event') {
                        socketService.emit(config.type, {
                            type: config.dataType,
                            data: data
                        });
                    } else {
                        // Per eventi che mappano direttamente
                        socketService.emit(config.type, data);
                    }
                }, 'system:socket_bridge');
            }
        });
        
        // Gestione animazioni e altri eventi UI
        this.on('ENTITY_MOVED', this._handleEntityMoved, 'system:animation');
    }
    
    /**
     * Gestisce l'animazione di movimento entità
     */
    _handleEntityMoved(data) {
        // Questo è solo un esempio, l'implementazione reale dipenderà
        // dal sistema di rendering utilizzato (Pixi.js, ecc.)
        const { entity_id, position, from_position, to_position } = data; 

        // console.log(`Animazione e aggiornamento posizione PixiJS per: ${entity_id} a ${JSON.stringify(position)} (da ${JSON.stringify(from_position)} a ${JSON.stringify(to_position)})`);
        // console.log(`Confronto con playerId locale: ${currentLocalPlayerId}, scena: ${currentPixiSceneId}`);

        if (!position || typeof position.x === 'undefined' || typeof position.y === 'undefined') {
            console.error('[eventBusService] _handleEntityMoved: Dati di posizione mancanti o malformati', data);
            return;
        }

        if (entityManager) {
            if (currentLocalPlayerId && entity_id === currentLocalPlayerId) {
                // console.log(`[eventBusService] Aggiorno posizione GIOCATORE ${entity_id} in Pixi a (${position.x}, ${position.y}) sulla scena ${currentPixiSceneId}`);
                entityManager.updatePlayerPosition(currentPixiSceneId, position.x, position.y);
            } else {
                // Per altre entità, aggiornamento PixiJS:
                // console.log(`[eventBusService] Aggiorno posizione ENTITA ${entity_id} in Pixi a (${position.x}, ${position.y}) sulla scena ${currentPixiSceneId}`);
                // Attualmente EntityManager.updateEntities() è distruttivo. 
                // Per un aggiornamento granulare, EntityManager necessita di un metodo tipo updateSingleEntityPosition(sceneId, entityId, x, y)
                // o MapPage deve essere notificata per richiedere tutte le entità e fare un re-render.
                // console.warn(`[eventBusService] Movimento per entità non-giocatore (${entity_id}) in PixiJS: update granulare non implementato. Considerare refresh completo entità se necessario.`);
                
                // Soluzione temporanea: se l'entità non è il giocatore, si potrebbe emettere un evento
                // che MapPage ascolta per poi aggiornare il suo stato 'entities' e far sì che il componente Pixi 
                // ri-renderizzi le entità. Questo è indiretto.
                this.emit('NON_PLAYER_ENTITY_MOVED', { entity_id, position });
            }
        } else {
            console.error('[eventBusService] EntityManager non disponibile.');
        }

        // Il codice di animazione simulata può rimanere o essere rimosso/integrato
        setTimeout(() => {
            this.emit('ANIMATION_COMPLETED', {
                type: 'movement',
                entity_id
            });
        }, 50); // Ridotto il timeout per reattività
    }
    
    /**
     * Sottoscrivi a un evento
     * @param {string} eventType - Tipo di evento
     * @param {function} callback - Funzione da chiamare quando l'evento viene emesso
     * @param {string} [subscriberId] - Identificatore opzionale del subscriber (per debug)
     * @returns {function} - Funzione per annullare la sottoscrizione
     */
    on(eventType, callback, subscriberId = null) {
        // Generiamo un ID univoco per il subscriber se non fornito
        const id = subscriberId || `${eventType}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        
        // Registriamo statistiche per questo subscriber
        this.subscriberStats[id] = {
            id,
            eventType,
            createdAt: Date.now(),
            lastCalled: Date.now(),
            callCount: 0,
            name: callback.name || 'anonymous'
        };
        
        // Wrapper che aggiorna le statistiche
        const trackedCallback = (data) => {
            this.subscriberStats[id].lastCalled = Date.now();
            this.subscriberStats[id].callCount++;
            
            try {
                callback(data);
            } catch (error) {
                console.error(`Errore nell'handler per ${eventType} (${id}):`, error);
            }
        };
        
        if (!this.subscribers[eventType]) {
            this.subscribers[eventType] = [];
        }
        
        this.subscribers[eventType].push({
            id,
            callback: trackedCallback
        });
        
        // Restituisci una funzione per annullare la sottoscrizione
        return () => {
            if (!this.subscribers[eventType]) return false;
            
            // Filtro gli handler, rimuovendo quello con l'ID specifico
            this.subscribers[eventType] = this.subscribers[eventType].filter(
                sub => sub.id !== id
            );
            
            // Se la lista è vuota, rimuovi la chiave per evitare memory leak
            if (this.subscribers[eventType].length === 0) {
                delete this.subscribers[eventType];
            }
            
            // Rimuovi anche le statistiche
            delete this.subscriberStats[id];
            
            return true;
        };
    }
    
    /**
     * Emetti un evento
     * @param {string} eventType - Tipo di evento
     * @param {object} data - Dati dell'evento
     */
    emit(eventType, data = {}) {
        console.log(`Evento emesso: ${eventType}`, data);
        
        if (!this.subscribers[eventType]) {
            return;
        }
        
        // Aggiunta timestamp
        const eventData = {
            ...data,
            _timestamp: Date.now()
        };
        
        this.subscribers[eventType].forEach(sub => {
            try {
                sub.callback(eventData);
            } catch (error) {
                console.error(`Errore nell'handler ${sub.id} per ${eventType}:`, error);
            }
        });
    }
    
    /**
     * Restituisce info sullo stato degli abbonamenti (utile per debug)
     */
    getDebugInfo() {
        const subscriberCounts = {};
        Object.keys(this.subscribers).forEach(eventType => {
            subscriberCounts[eventType] = this.subscribers[eventType].length;
        });
        
        return {
            activeEventTypes: Object.keys(this.subscribers),
            totalSubscribers: Object.keys(this.subscriberStats).length,
            subscribersByEvent: subscriberCounts,
            oldestSubscriber: Object.values(this.subscriberStats)
                .sort((a, b) => a.createdAt - b.createdAt)[0]
        };
    }
    
    /**
     * Richiede un movimento del giocatore
     * @param {string} direction - Direzione (north, south, east, west)
     */
    movePlayer(direction) {
        this.emit('PLAYER_MOVE', { direction });
    }
    
    /**
     * Richiede un attacco del giocatore
     * @param {string} targetId - ID del bersaglio
     */
    attackTarget(targetId) {
        this.emit('PLAYER_ATTACK', { target: targetId });
    }
    
    /**
     * Richiede l'uso di un oggetto
     * @param {string} itemId - ID dell'oggetto
     */
    useItem(itemId) {
        this.emit('PLAYER_USE_ITEM', { item_id: itemId });
    }
    
    /**
     * Richiede un'interazione con un'entità
     * @param {string} entityId - ID dell'entità
     */
    interact(entityId) {
        this.emit('PLAYER_INTERACT', { entity_id: entityId });
    }
    
    /**
     * Richiede l'apertura/chiusura dell'inventario
     */
    toggleInventory() {
        this.emit('UI_INVENTORY_TOGGLE');
    }
}

/**
 * Hook React per usare l'EventBus in modo sicuro nei componenti
 * 
 * Esempio di utilizzo:
 * ```jsx
 * function MyComponent() {
 *   useEventBus('ENTITY_MOVED', handleEntityMoved);
 *   // restante codice del componente...
 * }
 * ```
 */
export const useEventBus = (eventType, callback) => {
    const { useEffect } = require('react');
    
    useEffect(() => {
        // Crea subscriber con ID che include il nome del componente
        const componentName = callback.name || 'unknown';
        const unsubscribe = eventBus.on(eventType, callback, `react:${componentName}`);
        
        // Cleanup quando il componente viene smontato
        return () => {
            unsubscribe();
        };
    }, [eventType, callback]);
};

// Esporta un'istanza singleton
const eventBus = new EventBusService();
export default eventBus; 