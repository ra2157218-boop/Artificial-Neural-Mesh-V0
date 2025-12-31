# ============================================================
# ANM V0-OpenSource — TEXT-TO-SPEECH (PIPER + ALTERNATIVES)
#  Fast, offline, high-quality neural TTS
#  
#  Primary: Piper TTS (fast, lightweight)
#  Alternatives: Coqui TTS, Silero TTS
#  
#  Piper is designed for:
#  - Real-time synthesis (very fast)
#  - Low memory usage
#  - High quality voices
#  - Fully offline
# ============================================================

from __future__ import annotations
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from pathlib import Path
import os
import io
import subprocess
import tempfile
import time
import json
import urllib.request
import shutil

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

# Piper imports (if installed as library)
try:
    from piper import PiperVoice
    PIPER_LIBRARY_AVAILABLE = True
except ImportError:
    PIPER_LIBRARY_AVAILABLE = False
    PiperVoice = None

# Coqui TTS (alternative)
try:
    from TTS.api import TTS as CoquiTTS
    COQUI_AVAILABLE = True
except ImportError:
    COQUI_AVAILABLE = False
    CoquiTTS = None

# Silero TTS (alternative)
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None


# Available Piper voices (subset of popular ones)
PIPER_VOICES = {
    "en_US": {
        "amy": "en_US-amy-medium",
        "danny": "en_US-danny-low",
        "kathleen": "en_US-kathleen-low",
        "lessac": "en_US-lessac-medium",
        "libritts": "en_US-libritts-high",
        "ryan": "en_US-ryan-medium",
    },
    "en_GB": {
        "alan": "en_GB-alan-medium",
        "alba": "en_GB-alba-medium",
        "jenny": "en_GB-jenny_dioco-medium",
    },
}

# Default voice
DEFAULT_VOICE = "en_US-lessac-medium"


@dataclass
class TTSConfig:
    """Text-to-Speech configuration."""
    voice: str = DEFAULT_VOICE         # Piper voice name
    speed: float = 1.0                  # Speaking speed (0.5 - 2.0)
    pitch: float = 1.0                  # Pitch adjustment
    sample_rate: int = 22050            # Output sample rate
    backend: str = "auto"               # auto, piper, coqui, silero
    
    # Paths
    model_path: Optional[str] = None    # Custom model path
    cache_dir: str = ".anm_cache/tts"
    
    # Piper specific
    piper_executable: Optional[str] = None  # Path to piper binary
    
    # Silero specific
    silero_model: str = "v3_en"         # Silero model
    silero_speaker: str = "en_0"        # Silero speaker


class PiperTTS:
    """
    Text-to-Speech using Piper.
    
    Piper is a fast, local neural TTS system.
    Falls back to Coqui TTS or Silero if Piper unavailable.
    
    Features:
    - Fully offline after model download
    - Very fast synthesis (real-time factor < 0.1)
    - High quality neural voices
    - Multiple voice options
    - Low memory footprint
    
    Usage:
        tts = PiperTTS()
        audio = tts.synthesize("Hello, I am ANM")
        # or
        tts.speak("Hello world")  # Direct playback
    """
    
    PIPER_RELEASE_URL = "https://github.com/rhasspy/piper/releases/latest/download"
    VOICE_URL_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
    
    def __init__(self, config: Optional[TTSConfig] = None):
        self.config = config or TTSConfig()
        self._model = None
        self._backend = None
        self._piper_exe = None
        
        # Create cache directory
        os.makedirs(self.config.cache_dir, exist_ok=True)
    
    @property
    def available(self) -> bool:
        """Check if any TTS backend is available."""
        return (
            PIPER_LIBRARY_AVAILABLE or
            self._check_piper_binary() or
            COQUI_AVAILABLE or
            (TORCH_AVAILABLE and self._check_silero())
        )
    
    def _check_piper_binary(self) -> bool:
        """Check if piper binary is available."""
        if self.config.piper_executable:
            return os.path.exists(self.config.piper_executable)
        
        # Check if piper is in PATH
        return shutil.which("piper") is not None
    
    def _check_silero(self) -> bool:
        """Check if Silero models can be loaded."""
        if not TORCH_AVAILABLE:
            return False
        try:
            # This is a light check
            return True
        except Exception:
            return False
    
    def load_model(self) -> bool:
        """Load the TTS model."""
        if self._model is not None:
            return True
        
        backend = self.config.backend
        
        # Auto-detect backend
        if backend == "auto":
            if PIPER_LIBRARY_AVAILABLE:
                backend = "piper_lib"
            elif self._check_piper_binary():
                backend = "piper_bin"
            elif COQUI_AVAILABLE:
                backend = "coqui"
            elif TORCH_AVAILABLE:
                backend = "silero"
            else:
                print("Error: No TTS backend available")
                return False
        
        # Load based on backend
        if backend == "piper_lib":
            return self._load_piper_library()
        elif backend == "piper_bin":
            return self._load_piper_binary()
        elif backend == "coqui":
            return self._load_coqui()
        elif backend == "silero":
            return self._load_silero()
        else:
            print(f"Unknown backend: {backend}")
            return False
    
    def _load_piper_library(self) -> bool:
        """Load Piper as Python library."""
        try:
            model_path = self._ensure_piper_model()
            if not model_path:
                return False
            
            self._model = PiperVoice.load(model_path)
            self._backend = "piper_lib"
            print(f"✓ Loaded Piper library: {self.config.voice}")
            return True
            
        except Exception as e:
            print(f"Piper library load failed: {e}")
            return False
    
    def _load_piper_binary(self) -> bool:
        """Use Piper binary for synthesis."""
        try:
            # Find piper executable
            if self.config.piper_executable:
                self._piper_exe = self.config.piper_executable
            else:
                self._piper_exe = shutil.which("piper")
            
            if not self._piper_exe:
                return False
            
            # Ensure model is downloaded
            model_path = self._ensure_piper_model()
            if not model_path:
                return False
            
            self._model = model_path  # Store model path
            self._backend = "piper_bin"
            print(f"✓ Using Piper binary: {self.config.voice}")
            return True
            
        except Exception as e:
            print(f"Piper binary setup failed: {e}")
            return False
    
    def _load_coqui(self) -> bool:
        """Load Coqui TTS."""
        try:
            # Use a fast model
            self._model = CoquiTTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
            self._backend = "coqui"
            print("✓ Loaded Coqui TTS")
            return True
            
        except Exception as e:
            print(f"Coqui TTS load failed: {e}")
            return False
    
    def _load_silero(self) -> bool:
        """Load Silero TTS."""
        try:
            device = torch.device('cpu')
            
            # Load from torch hub
            model, example_text = torch.hub.load(
                repo_or_dir='snakers4/silero-models',
                model='silero_tts',
                language='en',
                speaker=self.config.silero_model,
            )
            model.to(device)
            
            self._model = model
            self._backend = "silero"
            print("✓ Loaded Silero TTS")
            return True
            
        except Exception as e:
            print(f"Silero TTS load failed: {e}")
            return False
    
    def _ensure_piper_model(self) -> Optional[str]:
        """Ensure Piper voice model is downloaded."""
        voice = self.config.voice
        
        # Model files
        model_dir = os.path.join(self.config.cache_dir, "piper_models")
        os.makedirs(model_dir, exist_ok=True)
        
        model_file = os.path.join(model_dir, f"{voice}.onnx")
        config_file = os.path.join(model_dir, f"{voice}.onnx.json")
        
        # Check if already downloaded
        if os.path.exists(model_file) and os.path.exists(config_file):
            return model_file
        
        # Download model
        print(f"Downloading Piper voice: {voice}...")
        
        try:
            # Construct URLs
            # Voice format: en_US-lessac-medium
            parts = voice.split("-")
            lang = parts[0]  # en_US
            
            model_url = f"{self.VOICE_URL_BASE}/{lang}/{voice}/{voice}.onnx"
            config_url = f"{self.VOICE_URL_BASE}/{lang}/{voice}/{voice}.onnx.json"
            
            # Download model
            print(f"  Downloading model...")
            urllib.request.urlretrieve(model_url, model_file)
            
            # Download config
            print(f"  Downloading config...")
            urllib.request.urlretrieve(config_url, config_file)
            
            print(f"✓ Downloaded {voice}")
            return model_file
            
        except Exception as e:
            print(f"Failed to download voice {voice}: {e}")
            return None
    
    def synthesize(
        self,
        text: str,
        speed: Optional[float] = None,
    ) -> Optional[bytes]:
        """
        Synthesize text to speech.
        
        Args:
            text: Text to synthesize
            speed: Override speaking speed
        
        Returns:
            Audio bytes (WAV format)
        """
        if not self.load_model():
            return None
        
        actual_speed = speed or self.config.speed
        
        try:
            if self._backend == "piper_lib":
                return self._synthesize_piper_lib(text, actual_speed)
            elif self._backend == "piper_bin":
                return self._synthesize_piper_bin(text, actual_speed)
            elif self._backend == "coqui":
                return self._synthesize_coqui(text, actual_speed)
            elif self._backend == "silero":
                return self._synthesize_silero(text, actual_speed)
            else:
                return None
                
        except Exception as e:
            print(f"Synthesis error: {e}")
            return None
    
    def _synthesize_piper_lib(
        self,
        text: str,
        speed: float,
    ) -> Optional[bytes]:
        """Synthesize using Piper library."""
        import wave
        
        buffer = io.BytesIO()
        
        with wave.open(buffer, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(self.config.sample_rate)
            
            # Synthesize
            for audio_chunk in self._model.synthesize_stream_raw(text):
                wav.writeframes(audio_chunk)
        
        return buffer.getvalue()
    
    def _synthesize_piper_bin(
        self,
        text: str,
        speed: float,
    ) -> Optional[bytes]:
        """Synthesize using Piper binary."""
        try:
            # Create temp output file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                output_path = f.name
            
            # Run piper
            cmd = [
                self._piper_exe,
                "--model", self._model,
                "--output_file", output_path,
            ]
            
            # Add speed if not 1.0
            if speed != 1.0:
                cmd.extend(["--length_scale", str(1.0 / speed)])
            
            # Run with text input
            process = subprocess.run(
                cmd,
                input=text.encode('utf-8'),
                capture_output=True,
            )
            
            if process.returncode != 0:
                print(f"Piper error: {process.stderr.decode()}")
                return None
            
            # Read output
            with open(output_path, 'rb') as f:
                audio = f.read()
            
            os.unlink(output_path)
            return audio
            
        except Exception as e:
            print(f"Piper binary error: {e}")
            return None
    
    def _synthesize_coqui(
        self,
        text: str,
        speed: float,
    ) -> Optional[bytes]:
        """Synthesize using Coqui TTS."""
        try:
            # Create temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                output_path = f.name
            
            # Synthesize
            self._model.tts_to_file(
                text=text,
                file_path=output_path,
                speed=speed,
            )
            
            # Read output
            with open(output_path, 'rb') as f:
                audio = f.read()
            
            os.unlink(output_path)
            return audio
            
        except Exception as e:
            print(f"Coqui synthesis error: {e}")
            return None
    
    def _synthesize_silero(
        self,
        text: str,
        speed: float,
    ) -> Optional[bytes]:
        """Synthesize using Silero TTS."""
        try:
            # Generate audio
            audio = self._model.apply_tts(
                text=text,
                speaker=self.config.silero_speaker,
                sample_rate=self.config.sample_rate,
            )
            
            # Convert to WAV bytes
            if NUMPY_AVAILABLE:
                import wave
                
                # Convert tensor to numpy
                audio_np = audio.numpy()
                audio_int16 = (audio_np * 32767).astype(np.int16)
                
                buffer = io.BytesIO()
                with wave.open(buffer, 'wb') as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(self.config.sample_rate)
                    wav.writeframes(audio_int16.tobytes())
                
                return buffer.getvalue()
            
            return None
            
        except Exception as e:
            print(f"Silero synthesis error: {e}")
            return None
    
    def speak(
        self,
        text: str,
        speed: Optional[float] = None,
        blocking: bool = True,
    ) -> bool:
        """
        Synthesize and play text.
        
        Args:
            text: Text to speak
            speed: Override speaking speed
            blocking: Wait for playback to complete
        
        Returns:
            True if successful
        """
        audio = self.synthesize(text, speed)
        if audio is None:
            return False
        
        from anm.voice.audio_utils import play_audio
        return play_audio(audio, blocking=blocking)
    
    def synthesize_to_file(
        self,
        text: str,
        path: str,
        speed: Optional[float] = None,
    ) -> bool:
        """Synthesize text to audio file."""
        audio = self.synthesize(text, speed)
        if audio is None:
            return False
        
        try:
            with open(path, 'wb') as f:
                f.write(audio)
            return True
        except Exception as e:
            print(f"Save error: {e}")
            return False
    
    def list_voices(self) -> Dict[str, List[str]]:
        """List available voices."""
        return PIPER_VOICES
    
    def unload_model(self) -> None:
        """Unload model to free memory."""
        self._model = None
        self._backend = None
        
        import gc
        gc.collect()
        
        if TORCH_AVAILABLE:
            torch.cuda.empty_cache()


# Convenience function
def speak(
    text: str,
    voice: str = DEFAULT_VOICE,
    speed: float = 1.0,
) -> bool:
    """
    Quick speak function.
    
    Args:
        text: Text to speak
        voice: Voice name
        speed: Speaking speed
    
    Returns:
        True if successful
    """
    tts = PiperTTS(TTSConfig(voice=voice, speed=speed))
    return tts.speak(text)
