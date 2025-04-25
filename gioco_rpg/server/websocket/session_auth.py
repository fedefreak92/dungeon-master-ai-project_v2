"""
Modulo per la gestione dell'autenticazione e persistenza delle sessioni WebSocket
Implementa un sistema di token JWT per autenticare e ripristinare le sessioni
"""

import logging
import jwt
import time
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import request, current_app, g
from flask_socketio import disconnect

# Configura logger
logger = logging.getLogger(__name__)

# Chiave di default per firma JWT (cambia questa in un file di configurazione nel progetto reale)
DEFAULT_SECRET_KEY = "chiave_sicura_per_jwt_sostituisci_in_produzione"

# Durata token in secondi (24 ore)
TOKEN_EXPIRY = 86400

# Classe per gestire autenticazione sessioni WebSocket
class SessionAuthManager:
    def __init__(self, app=None, socketio=None, secret_key=None):
        self.app = app
        self.socketio = socketio
        self.secret_key = secret_key or DEFAULT_SECRET_KEY
        
        # Mappa token -> data sessione per verifiche rapide
        self.active_sessions = {}
        
        # Registra questa istanza nell'app Flask
        if app:
            app.session_auth_manager = self
            
        # Carica sessioni persistenti da disco
        self._load_persisted_sessions()
        
        logger.info("SessionAuthManager inizializzato")
    
    def init_app(self, app, socketio):
        """Inizializza il manager con un'app Flask e Socket.IO"""
        self.app = app
        self.socketio = socketio
        app.session_auth_manager = self
    
    def _load_persisted_sessions(self):
        """Carica le informazioni delle sessioni persistenti salvate"""
        try:
            from util.config import SESSIONS_DIR
            import os
            import json
            
            # Cerca file di indice sessioni
            index_path = os.path.join(SESSIONS_DIR, "session_index.json")
            if not os.path.exists(index_path):
                logger.info("Nessun indice sessioni trovato")
                return
                
            with open(index_path, 'r') as f:
                session_index = json.load(f)
                
            # Carica info sessioni attive
            for session_id, info in session_index.items():
                # Verifica che il token non sia scaduto
                if info.get('exp', 0) > time.time():
                    self.active_sessions[info.get('token')] = {
                        'session_id': session_id,
                        'user_id': info.get('user_id'),
                        'created_at': info.get('created_at'),
                        'last_access': info.get('last_access'),
                        'exp': info.get('exp')
                    }
            
            logger.info(f"Caricate {len(self.active_sessions)} sessioni persistenti")
        except Exception as e:
            logger.error(f"Errore nel caricamento delle sessioni persistenti: {e}")
    
    def _save_persisted_sessions(self):
        """Salva le informazioni delle sessioni persistenti su disco"""
        try:
            from util.config import SESSIONS_DIR
            import os
            import json
            
            # Prepara indice sessioni con info minimali
            session_index = {}
            
            # Inverti mappa token->session in una mappa session_id->info
            for token, info in self.active_sessions.items():
                session_id = info.get('session_id')
                if session_id:
                    session_index[session_id] = {
                        'token': token,
                        'user_id': info.get('user_id'),
                        'created_at': info.get('created_at'),
                        'last_access': info.get('last_access', time.time()),
                        'exp': info.get('exp', 0)
                    }
            
            # Crea directory se non esiste
            os.makedirs(SESSIONS_DIR, exist_ok=True)
            
            # Salva file indice
            index_path = os.path.join(SESSIONS_DIR, "session_index.json")
            with open(index_path, 'w') as f:
                json.dump(session_index, f)
                
            logger.info(f"Salvate {len(session_index)} sessioni persistenti")
        except Exception as e:
            logger.error(f"Errore nel salvataggio delle sessioni persistenti: {e}")
    
    def create_session_token(self, session_id, user_id=None, expiry=None):
        """
        Crea un token JWT per una sessione di gioco
        
        Args:
            session_id (str): ID univoco della sessione
            user_id (str, optional): ID utente associato alla sessione 
            expiry (int, optional): Durata validità in secondi
            
        Returns:
            str: Token JWT firmato
        """
        now = datetime.utcnow()
        exp = now + timedelta(seconds=expiry or TOKEN_EXPIRY)
        
        # Payload del token
        payload = {
            'session_id': session_id,
            'user_id': user_id,
            'iat': now,
            'exp': exp
        }
        
        # Crea token JWT
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        
        # Aggiungi alla cache delle sessioni attive
        self.active_sessions[token] = {
            'session_id': session_id,
            'user_id': user_id,
            'created_at': time.time(),
            'last_access': time.time(),
            'exp': time.mktime(exp.timetuple())
        }
        
        # Salva le sessioni persistenti
        self._save_persisted_sessions()
        
        return token
    
    def verify_token(self, token):
        """
        Verifica un token JWT e restituisce i dati della sessione
        
        Args:
            token (str): Token JWT da verificare
            
        Returns:
            dict: Dati della sessione o None se token non valido
        """
        try:
            # Controlla prima nella cache per evitare decodifica
            if token in self.active_sessions:
                session_info = self.active_sessions[token]
                
                # Verifica scadenza
                if session_info.get('exp', 0) < time.time():
                    # Token scaduto, rimuovi dalla cache
                    del self.active_sessions[token]
                    return None
                
                # Aggiorna timestamp ultimo accesso
                session_info['last_access'] = time.time()
                return session_info
            
            # Se non in cache, decodifica il token
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            
            # Verifica che non sia scaduto (jwt.decode già controlla exp)
            session_id = payload.get('session_id')
            user_id = payload.get('user_id')
            
            # Aggiungi alla cache
            exp_timestamp = payload.get('exp')
            self.active_sessions[token] = {
                'session_id': session_id,
                'user_id': user_id,
                'created_at': payload.get('iat', time.time()),
                'last_access': time.time(),
                'exp': exp_timestamp
            }
            
            return self.active_sessions[token]
        except jwt.ExpiredSignatureError:
            logger.warning(f"Token JWT scaduto: {token[:10]}...")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token JWT non valido: {e}")
            return None
        except Exception as e:
            logger.error(f"Errore nella verifica del token: {e}")
            return None
    
    def invalidate_token(self, token):
        """
        Invalida un token di sessione
        
        Args:
            token (str): Token JWT da invalidare
            
        Returns:
            bool: True se il token è stato invalidato, False altrimenti
        """
        try:
            if token in self.active_sessions:
                # Rimuovi dalla cache
                session_info = self.active_sessions.pop(token)
                
                # Salva le sessioni persistenti
                self._save_persisted_sessions()
                
                logger.info(f"Token invalidato per sessione: {session_info.get('session_id')}")
                return True
            return False
        except Exception as e:
            logger.error(f"Errore nell'invalidazione del token: {e}")
            return False
    
    def invalidate_session(self, session_id):
        """
        Invalida tutti i token associati a una sessione
        
        Args:
            session_id (str): ID sessione da invalidare
            
        Returns:
            bool: True se almeno un token è stato invalidato, False altrimenti
        """
        try:
            tokens_to_remove = []
            
            # Trova tutti i token associati alla sessione
            for token, info in self.active_sessions.items():
                if info.get('session_id') == session_id:
                    tokens_to_remove.append(token)
            
            # Rimuovi i token trovati
            for token in tokens_to_remove:
                del self.active_sessions[token]
            
            # Salva le sessioni persistenti
            if tokens_to_remove:
                self._save_persisted_sessions()
                logger.info(f"Invalidati {len(tokens_to_remove)} token per sessione {session_id}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Errore nell'invalidazione della sessione: {e}")
            return False
    
    def cleanup_expired_sessions(self):
        """
        Rimuove tutte le sessioni scadute dalla cache
        
        Returns:
            int: Numero di sessioni rimosse
        """
        try:
            now = time.time()
            tokens_to_remove = []
            
            # Trova tutti i token scaduti
            for token, info in self.active_sessions.items():
                if info.get('exp', 0) < now:
                    tokens_to_remove.append(token)
            
            # Rimuovi i token scaduti
            for token in tokens_to_remove:
                del self.active_sessions[token]
            
            # Salva le sessioni persistenti
            if tokens_to_remove:
                self._save_persisted_sessions()
                logger.info(f"Rimosse {len(tokens_to_remove)} sessioni scadute")
            
            return len(tokens_to_remove)
        except Exception as e:
            logger.error(f"Errore nella pulizia delle sessioni scadute: {e}")
            return 0
    
    def get_active_sessions_count(self):
        """
        Restituisce il numero di sessioni attive
        
        Returns:
            int: Numero di sessioni attive
        """
        return len(self.active_sessions)
    
    def get_session_data(self, token):
        """
        Ottiene i dati associati a un token di sessione
        
        Args:
            token (str): Token JWT
            
        Returns:
            dict: Dati della sessione o None se token non valido
        """
        return self.verify_token(token)
    
    def get_session_by_id(self, session_id):
        """
        Cerca una sessione attiva per ID
        
        Args:
            session_id (str): ID della sessione
            
        Returns:
            dict: Dati della sessione o None se non trovata
        """
        for token, info in self.active_sessions.items():
            if info.get('session_id') == session_id:
                # Verifica che non sia scaduta
                if info.get('exp', 0) < time.time():
                    continue
                return info
        return None
    
    def extend_session(self, token, extension=None):
        """
        Estende la durata di una sessione
        
        Args:
            token (str): Token JWT
            extension (int, optional): Estensione in secondi
            
        Returns:
            str: Nuovo token con scadenza estesa o None se errore
        """
        try:
            # Verifica il token
            session_info = self.verify_token(token)
            if not session_info:
                return None
            
            # Invalida il vecchio token
            self.invalidate_token(token)
            
            # Crea nuovo token con scadenza estesa
            new_token = self.create_session_token(
                session_info['session_id'],
                session_info.get('user_id'),
                extension or TOKEN_EXPIRY
            )
            
            return new_token
        except Exception as e:
            logger.error(f"Errore nell'estensione della sessione: {e}")
            return None


# Decoratore per proteggere route con autenticazione token
def token_required(f):
    """
    Decoratore per richiedere un token JWT valido nelle route Flask
    Da usare su route API che richiedono autenticazione
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Cerca token nell'header o nei parametri
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        else:
            token = request.args.get('token')
        
        if not token:
            return {'status': 'error', 'message': 'Token mancante'}, 401
        
        # Verifica token
        session_auth = current_app.session_auth_manager
        session_info = session_auth.verify_token(token)
        
        if not session_info:
            return {'status': 'error', 'message': 'Token non valido o scaduto'}, 401
        
        # Salva dati sessione nel contesto globale Flask
        g.session_info = session_info
        
        return f(*args, **kwargs)
    
    return decorated

# Middleware per autenticazione WebSocket
def authenticate_socket(token):
    """
    Funzione per autenticare una connessione WebSocket
    
    Args:
        token (str): Token JWT
    
    Returns:
        bool: True se autenticato, False altrimenti
    """
    if not token:
        return False
    
    # Verifica token
    session_auth = current_app.session_auth_manager
    session_info = session_auth.verify_token(token)
    
    if not session_info:
        return False
    
    # Salva dati sessione nel contesto globale Flask
    g.session_info = session_info
    return True

# Inizializza il manager di default
auth_manager = SessionAuthManager() 