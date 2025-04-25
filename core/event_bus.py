from collections import defaultdict
import logging
from threading import RLock
from queue import SimpleQueue, Empty
import time

logger = logging.getLogger(__name__)

class EventBus:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = EventBus()
        return cls._instance
    
    def __init__(self):
        self.subscribers = defaultdict(list)
        self.q = SimpleQueue()
        self._lock = RLock()
        self._stats = {
            "events_processed": 0,
            "events_by_type": defaultdict(int),
            "slow_handlers": []
        }
        self._infinite_loop_warning_threshold = 950  # Soglia per avviso di possibile loop infinito
    
    def on(self, event_type, callback):
        """Sottoscrivi a un tipo di evento"""
        with self._lock:
            self.subscribers[event_type].append(callback)
        
        # Lambda thread-safe per unsubscribe
        def unsubscribe():
            with self._lock:
                if callback in self.subscribers[event_type]:
                    self.subscribers[event_type].remove(callback)
                    # Se la lista è vuota, rimuovi la chiave per evitare memory leak
                    if not self.subscribers[event_type]:
                        del self.subscribers[event_type]
                    return True
                return False
                
        return unsubscribe
    
    def emit(self, event_type, **data):
        """Emetti un evento da processare nel prossimo ciclo"""
        # Aggiungi timestamp per tracking/debugging
        data["_timestamp"] = time.time()
        
        # Inserisci nella coda thread-safe
        self.q.put((event_type, data))
        logger.debug(f"Evento emesso: {event_type}, dati: {data}")
    
    def emit_immediate(self, event_type, **data):
        """Emetti e processa un evento immediatamente"""
        logger.debug(f"Evento immediato: {event_type}, dati: {data}")
        
        # Aggiunta timestamp
        data["_timestamp"] = time.time()
        
        # Copia callbacks inclusi wildcard '*' con il lock
        with self._lock:
            # Combina i callback specifici + wildcard
            callbacks = self.subscribers.get(event_type, []).copy()
            callbacks.extend(self.subscribers.get('*', []))
        
        # Processa tutti i callback
        for callback in callbacks:
            try:
                start_time = time.time()
                callback(**data)
                # Monitora callback lenti (> 4ms)
                elapsed = (time.time() - start_time) * 1000
                if elapsed > 4:
                    logger.warning(f"Handler lento per {event_type}: {callback.__name__} - {elapsed:.2f}ms")
                    self._stats["slow_handlers"].append((event_type, callback.__name__, elapsed))
            except Exception as e:
                logger.error(f"Errore durante callback {callback.__name__} per evento {event_type}: {e}")
    
    def process(self, max_iter=1000):
        """Processa eventi dalla coda thread-safe"""
        processed = 0
        start_time = time.time()
        
        for i in range(max_iter):
            try:
                event_type, data = self.q.get_nowait()
                
                # Aggiorna statistiche
                self._stats["events_processed"] += 1
                self._stats["events_by_type"][event_type] += 1
                
                # Copia callbacks inclusi wildcard '*' con il lock
                with self._lock:
                    # Combina i callback specifici + wildcard
                    callbacks = self.subscribers.get(event_type, []).copy()
                    callbacks.extend(self.subscribers.get('*', []))
                
                # Tempo trascorso in coda (per debug)
                queue_time = (time.time() - data.get("_timestamp", 0)) * 1000
                if queue_time > 100:  # Avviso per eventi rimasti in coda > 100ms
                    logger.warning(f"Evento {event_type} è rimasto in coda per {queue_time:.2f}ms")
                
                # Processa tutti i callback
                for callback in callbacks:
                    try:
                        start_time_cb = time.time()
                        callback(**data)
                        # Monitora callback lenti (> 4ms)
                        elapsed = (time.time() - start_time_cb) * 1000
                        if elapsed > 4:
                            logger.warning(f"Handler lento per {event_type}: {callback.__name__} - {elapsed:.2f}ms")
                            self._stats["slow_handlers"].append((event_type, callback.__name__, elapsed))
                    except Exception as e:
                        logger.error(f"Errore durante callback {callback.__name__} per evento {event_type}: {e}")
                
                processed += 1
                
                # Controlla se siamo vicini al limite - potenziale loop infinito
                if processed > self._infinite_loop_warning_threshold:
                    logger.warning(f"Possibile loop infinito rilevato: processati {processed}/{max_iter} eventi " 
                                  f"senza svuotare la coda. Verificare che gli handler non emettano troppi eventi.")
            except Empty:
                break
        
        # Avviso se abbiamo raggiunto il limite massimo di iterazioni
        if processed == max_iter:
            logger.warning(f"EventBus backlog: processati {max_iter} eventi in una chiamata process(), "
                          f"potrebbero esserci altri eventi in coda. Considera di aumentare max_iter.")
        
        # Calcola throughput per debug/monitoring
        elapsed = time.time() - start_time
        if processed > 0 and elapsed > 0:
            logger.debug(f"EventBus ha processato {processed} eventi in {elapsed:.4f}s " 
                        f"({processed/elapsed:.1f} eventi/sec)")
        
        return processed
    
    def get_stats(self):
        """Restituisce statistiche sul bus per monitoring/debugging"""
        return self._stats
    
    def reset_stats(self):
        """Resetta le statistiche del bus"""
        self._stats = {
            "events_processed": 0,
            "events_by_type": defaultdict(int),
            "slow_handlers": []
        } 