import logging
import time
import uuid
from flask_socketio import emit
from flask import request

# Import moduli locali
from . import graphics_renderer

# Configura il logger
logger = logging.getLogger(__name__)

def handle_play_audio(data):
    """
    Riproduce un audio sul client
    
    Args:
        data (dict): Dati dell'audio da riprodurre
    """
    if not data or "type" not in data:
        emit('error', {"message": "Tipo audio mancante nella richiesta"})
        return
    
    # Tipo può essere "sound" o "music"
    audio_type = data["type"]
    
    if audio_type == "sound":
        # Riproduce un effetto sonoro
        if "name" not in data:
            emit('error', {"message": "Nome del suono mancante"})
            return
            
        sound_data = {
            "name": data["name"],
            "volume": data.get("volume", 1.0),
            "loop": data.get("loop", False),
            "position": data.get("position", None)  # Per audio posizionale
        }
        
        graphics_renderer.play_sound(sound_data)
        
    elif audio_type == "music":
        # Riproduce una traccia musicale
        if "track" not in data:
            emit('error', {"message": "Traccia musicale mancante"})
            return
            
        music_data = {
            "track": data["track"],
            "volume": data.get("volume", 1.0),
            "fade_in": data.get("fade_in", 0.0)
        }
        
        graphics_renderer.play_music(music_data)
        
    else:
        emit('error', {"message": f"Tipo audio '{audio_type}' non supportato"})
        return
    
    # Conferma al client
    emit('audio_started', {
        "type": audio_type,
        "audio_id": str(uuid.uuid4()),
        "timestamp": time.time()
    })

def register_handlers(socketio_instance):
    """
    Registra gli handler audio
    
    Args:
        socketio_instance: Istanza SocketIO
    """
    socketio_instance.on_event('play_audio', handle_play_audio)
    
    logger.info("Handler audio registrati") 