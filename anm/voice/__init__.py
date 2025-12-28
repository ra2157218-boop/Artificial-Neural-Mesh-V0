# ============================================================
#  ANM V0-OpenSource — VOICE I/O MODULE
#  Offline Speech-to-Text and Text-to-Speech
#  
#  Components:
#  - STT: Whisper (OpenAI) - Best accuracy, fully offline
#  - TTS: Piper - Fast, lightweight, high quality, offline
#  
#  Both systems work completely offline on device.
# ============================================================

"""
ANM Voice I/O System

Provides offline voice input/output capabilities:
- Speech-to-Text using Whisper (tiny/base/small models)
- Text-to-Speech using Piper (fast neural TTS)
- Unified VoiceIO interface for easy integration

Usage:
    from anm.voice import VoiceIO
    
    voice = VoiceIO()
    
    # Listen to user
    text = voice.listen()
    
    # Speak response
    voice.speak("Hello, I am ANM")
    
    # Full conversation loop
    voice.conversation_loop(anm.query)
"""

from anm.voice.stt import WhisperSTT, STTConfig
from anm.voice.tts import PiperTTS, TTSConfig
from anm.voice.voice_io import VoiceIO, VoiceConfig
from anm.voice.audio_utils import (
    record_audio,
    play_audio,
    save_audio,
    load_audio,
    get_audio_devices,
    AudioConfig,
)

__all__ = [
    # Main Interface
    "VoiceIO",
    "VoiceConfig",
    # STT
    "WhisperSTT",
    "STTConfig",
    # TTS
    "PiperTTS",
    "TTSConfig",
    # Audio Utilities
    "record_audio",
    "play_audio",
    "save_audio",
    "load_audio",
    "get_audio_devices",
    "AudioConfig",
]

__version__ = "0.1.0-opensource"
