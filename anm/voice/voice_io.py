# ============================================================
# ANM V0-OpenSource — UNIFIED VOICE I/O
#  Complete voice interaction system
#  Combines STT (Whisper) and TTS (Piper) for conversations
# ============================================================

from __future__ import annotations
from typing import Optional, Dict, Any, Callable, Union
from dataclasses import dataclass, field
import threading
import time
import os

from anm.voice.stt import WhisperSTT, STTConfig
from anm.voice.tts import PiperTTS, TTSConfig
from anm.voice.audio_utils import (
    record_audio,
    play_audio,
    AudioConfig,
    AUDIO_AVAILABLE,
)


@dataclass
class VoiceConfig:
    """Unified Voice I/O configuration."""
    # STT settings
    stt_model: str = "base"            # Whisper model size
    stt_language: Optional[str] = None # Auto-detect if None
    
    # TTS settings
    tts_voice: str = "en_US-lessac-medium"  # Piper voice
    tts_speed: float = 1.0             # Speaking speed
    
    # Audio settings
    sample_rate: int = 16000           # Recording sample rate
    silence_threshold: float = 0.01    # VAD threshold
    silence_duration: float = 1.5      # Seconds of silence to stop
    max_listen_duration: float = 30.0  # Max listening time
    
    # Behavior
    auto_play: bool = True             # Auto-play TTS output
    show_listening: bool = True        # Show listening indicator
    beep_on_listen: bool = False       # Beep when starting to listen
    
    # Cache
    cache_dir: str = ".anm_cache/voice"


class VoiceIO:
    """
    Unified Voice I/O for ANM.
    
    Provides a complete voice interaction system:
    - Listen: Record and transcribe speech
    - Speak: Synthesize and play text
    - Conversation loop: Full voice-based interaction
    
    Usage:
        voice = VoiceIO()
        
        # Simple usage
        text = voice.listen()        # Listen for speech
        voice.speak("Hello!")        # Speak text
        
        # With ANM integration
        def process(text):
            return anm.query(text)["result"]
        
        voice.conversation_loop(process)  # Full voice conversation
    """
    
    def __init__(self, config: Optional[VoiceConfig] = None):
        self.config = config or VoiceConfig()
        
        # Create cache directory
        os.makedirs(self.config.cache_dir, exist_ok=True)
        
        # Initialize STT
        self._stt = WhisperSTT(STTConfig(
            model_size=self.config.stt_model,
            language=self.config.stt_language,
            cache_dir=os.path.join(self.config.cache_dir, "stt"),
        ))
        
        # Initialize TTS
        self._tts = PiperTTS(TTSConfig(
            voice=self.config.tts_voice,
            speed=self.config.tts_speed,
            cache_dir=os.path.join(self.config.cache_dir, "tts"),
        ))
        
        # Audio config
        self._audio_config = AudioConfig(
            sample_rate=self.config.sample_rate,
            silence_threshold=self.config.silence_threshold,
            silence_duration=self.config.silence_duration,
            max_duration=self.config.max_listen_duration,
        )
        
        # State
        self._is_listening = False
        self._is_speaking = False
        self._should_stop = False
    
    @property
    def available(self) -> bool:
        """Check if voice I/O is available."""
        return AUDIO_AVAILABLE and (self._stt.available or self._tts.available)
    
    @property
    def stt_available(self) -> bool:
        """Check if speech-to-text is available."""
        return self._stt.available
    
    @property
    def tts_available(self) -> bool:
        """Check if text-to-speech is available."""
        return self._tts.available
    
    def load_models(self) -> Dict[str, bool]:
        """Pre-load all models."""
        return {
            "stt": self._stt.load_model(),
            "tts": self._tts.load_model(),
        }
    
    # ============================================================
    #  LISTENING (Speech-to-Text)
    # ============================================================
    
    def listen(
        self,
        timeout: Optional[float] = None,
        show_indicator: Optional[bool] = None,
    ) -> str:
        """
        Listen for speech and transcribe.
        
        Args:
            timeout: Override max listening duration
            show_indicator: Override show_listening setting
        
        Returns:
            Transcribed text (empty string if failed)
        """
        if not self._stt.available:
            print("Error: STT not available")
            return ""
        
        if not AUDIO_AVAILABLE:
            print("Error: Audio recording not available")
            return ""
        
        # Update config if overridden
        audio_config = self._audio_config
        if timeout:
            audio_config = AudioConfig(
                sample_rate=audio_config.sample_rate,
                silence_threshold=audio_config.silence_threshold,
                silence_duration=audio_config.silence_duration,
                max_duration=timeout,
            )
        
        show = show_indicator if show_indicator is not None else self.config.show_listening
        
        try:
            self._is_listening = True
            
            if show:
                print("🎤 Listening... (speak now, silence to stop)")
            
            # Record audio
            audio_bytes = record_audio(
                duration=None,  # Use VAD
                config=audio_config,
                voice_activity_detection=True,
            )
            
            if not audio_bytes:
                if show:
                    print("   No audio detected")
                return ""
            
            if show:
                print("   Processing...")
            
            # Transcribe
            result = self._stt.transcribe(audio_bytes)
            
            if not result.get("success", False):
                if show:
                    print(f"   Error: {result.get('error', 'Unknown')}")
                return ""
            
            text = result.get("text", "").strip()
            
            if show and text:
                print(f"   You said: \"{text}\"")
            
            return text
            
        finally:
            self._is_listening = False
    
    def listen_continuous(
        self,
        callback: Callable[[str], None],
        stop_word: str = "stop listening",
    ) -> None:
        """
        Continuously listen and call callback with transcriptions.
        
        Args:
            callback: Function to call with each transcription
            stop_word: Phrase to stop listening
        """
        print(f"🎤 Continuous listening started (say \"{stop_word}\" to stop)")
        
        while not self._should_stop:
            text = self.listen(show_indicator=False)
            
            if text:
                if stop_word.lower() in text.lower():
                    print("   Stopping continuous listen...")
                    break
                
                callback(text)
        
        self._should_stop = False
    
    # ============================================================
    #  SPEAKING (Text-to-Speech)
    # ============================================================
    
    def speak(
        self,
        text: str,
        blocking: bool = True,
        speed: Optional[float] = None,
    ) -> bool:
        """
        Speak text.
        
        Args:
            text: Text to speak
            blocking: Wait for speech to complete
            speed: Override speaking speed
        
        Returns:
            True if successful
        """
        if not self._tts.available:
            print("Error: TTS not available")
            return False
        
        if not text.strip():
            return True
        
        try:
            self._is_speaking = True
            return self._tts.speak(text, speed=speed, blocking=blocking)
        finally:
            self._is_speaking = False
    
    def speak_async(
        self,
        text: str,
        callback: Optional[Callable[[], None]] = None,
    ) -> threading.Thread:
        """
        Speak text asynchronously.
        
        Args:
            text: Text to speak
            callback: Optional callback when done
        
        Returns:
            Thread object
        """
        def _speak():
            self.speak(text, blocking=True)
            if callback:
                callback()
        
        thread = threading.Thread(target=_speak)
        thread.start()
        return thread
    
    def synthesize(
        self,
        text: str,
        output_path: Optional[str] = None,
    ) -> Optional[bytes]:
        """
        Synthesize text to audio without playing.
        
        Args:
            text: Text to synthesize
            output_path: Optional file path to save
        
        Returns:
            Audio bytes (or None if failed)
        """
        audio = self._tts.synthesize(text)
        
        if audio and output_path:
            with open(output_path, 'wb') as f:
                f.write(audio)
        
        return audio
    
    # ============================================================
    #  CONVERSATION LOOP
    # ============================================================
    
    def conversation_loop(
        self,
        process_fn: Callable[[str], str],
        greeting: str = "Hello! I'm ANM. How can I help you?",
        goodbye: str = "Goodbye!",
        exit_words: list = None,
        error_message: str = "Sorry, I didn't catch that. Could you repeat?",
    ) -> None:
        """
        Run a voice conversation loop.
        
        Args:
            process_fn: Function that takes user text and returns response
            greeting: Opening greeting
            goodbye: Closing message
            exit_words: Words that end the conversation
            error_message: Message on transcription failure
        """
        if exit_words is None:
            exit_words = ["goodbye", "bye", "exit", "quit", "stop"]
        
        print("\n" + "=" * 50)
        print("🎙️  ANM VOICE CONVERSATION")
        print("=" * 50)
        
        # Speak greeting
        if greeting:
            print(f"\n🤖 ANM: {greeting}")
            self.speak(greeting)
        
        try:
            while not self._should_stop:
                print()
                
                # Listen for user input
                user_text = self.listen()
                
                if not user_text:
                    print(f"🤖 ANM: {error_message}")
                    self.speak(error_message)
                    continue
                
                # Check for exit words
                if any(word in user_text.lower() for word in exit_words):
                    print(f"\n🤖 ANM: {goodbye}")
                    self.speak(goodbye)
                    break
                
                # Process with ANM
                print("   Thinking...")
                try:
                    response = process_fn(user_text)
                except Exception as e:
                    response = f"I encountered an error: {str(e)[:100]}"
                
                # Speak response
                print(f"🤖 ANM: {response}")
                self.speak(response)
        
        except KeyboardInterrupt:
            print(f"\n\n🤖 ANM: {goodbye}")
            self.speak(goodbye)
        
        finally:
            self._should_stop = False
        
        print("\n" + "=" * 50)
        print("Voice conversation ended")
        print("=" * 50 + "\n")
    
    def quick_conversation(
        self,
        process_fn: Callable[[str], str],
    ) -> str:
        """
        Single turn voice conversation.
        
        Listens once, processes, speaks response.
        
        Args:
            process_fn: Function that takes user text and returns response
        
        Returns:
            The response text
        """
        # Listen
        user_text = self.listen()
        if not user_text:
            response = "I didn't catch that."
            self.speak(response)
            return response
        
        # Process
        response = process_fn(user_text)
        
        # Speak
        self.speak(response)
        
        return response
    
    # ============================================================
    #  CONTROL
    # ============================================================
    
    def stop(self) -> None:
        """Stop current operation."""
        self._should_stop = True
    
    @property
    def is_listening(self) -> bool:
        """Check if currently listening."""
        return self._is_listening
    
    @property
    def is_speaking(self) -> bool:
        """Check if currently speaking."""
        return self._is_speaking
    
    def unload_models(self) -> None:
        """Unload models to free memory."""
        self._stt.unload_model()
        self._tts.unload_model()
    
    # ============================================================
    #  STATUS
    # ============================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Get voice I/O status."""
        return {
            "available": self.available,
            "stt_available": self.stt_available,
            "tts_available": self.tts_available,
            "stt_model": self.config.stt_model,
            "tts_voice": self.config.tts_voice,
            "is_listening": self._is_listening,
            "is_speaking": self._is_speaking,
        }


# ============================================================
#  CONVENIENCE FUNCTIONS
# ============================================================

_default_voice_io: Optional[VoiceIO] = None


def get_voice_io() -> VoiceIO:
    """Get default VoiceIO instance."""
    global _default_voice_io
    if _default_voice_io is None:
        _default_voice_io = VoiceIO()
    return _default_voice_io


def listen() -> str:
    """Quick listen function."""
    return get_voice_io().listen()


def speak(text: str) -> bool:
    """Quick speak function."""
    return get_voice_io().speak(text)


def voice_chat(process_fn: Callable[[str], str]) -> None:
    """Start voice conversation."""
    get_voice_io().conversation_loop(process_fn)
