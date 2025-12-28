# ============================================================
# ANM V0-OpenSource — SPEECH-TO-TEXT (WHISPER)
#  Offline speech recognition using OpenAI's Whisper
#  
#  Models (smallest to largest):
#  - tiny: 39M params, ~1GB RAM, fastest
#  - base: 74M params, ~1GB RAM, good balance
#  - small: 244M params, ~2GB RAM, better accuracy
#  - medium: 769M params, ~5GB RAM, high accuracy
#  - large: 1550M params, ~10GB RAM, best accuracy
#  
#  Recommended: "base" for real-time, "small" for accuracy
# ============================================================

from __future__ import annotations
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from pathlib import Path
import os
import io
import tempfile
import time

# Whisper imports
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    whisper = None

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

# For faster-whisper (optional, faster inference)
try:
    from faster_whisper import WhisperModel as FasterWhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    FasterWhisperModel = None


@dataclass
class STTConfig:
    """Speech-to-Text configuration."""
    model_size: str = "base"           # tiny, base, small, medium, large
    language: Optional[str] = None     # Auto-detect if None, or "en", "es", etc.
    task: str = "transcribe"           # transcribe or translate
    use_faster_whisper: bool = True    # Use faster-whisper if available
    device: str = "auto"               # auto, cpu, cuda, mps
    compute_type: str = "auto"         # auto, float32, float16, int8
    beam_size: int = 5                 # Beam search size
    vad_filter: bool = True            # Voice activity detection filter
    word_timestamps: bool = False      # Include word-level timestamps
    
    # Paths
    model_path: Optional[str] = None   # Custom model path
    cache_dir: str = ".anm_cache/whisper"


class WhisperSTT:
    """
    Speech-to-Text using Whisper.
    
    Features:
    - Fully offline after model download
    - Multiple model sizes for speed/accuracy tradeoff
    - Automatic language detection
    - Support for faster-whisper backend
    - Voice activity detection
    
    Usage:
        stt = WhisperSTT()
        text = stt.transcribe(audio_bytes)
        # or
        text = stt.transcribe_file("audio.wav")
    """
    
    def __init__(self, config: Optional[STTConfig] = None):
        self.config = config or STTConfig()
        self._model = None
        self._use_faster = False
        
        # Create cache directory
        os.makedirs(self.config.cache_dir, exist_ok=True)
    
    @property
    def available(self) -> bool:
        """Check if STT is available."""
        return WHISPER_AVAILABLE or FASTER_WHISPER_AVAILABLE
    
    @property
    def model_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model is not None
    
    def load_model(self) -> bool:
        """
        Load the Whisper model.
        
        Returns:
            True if model loaded successfully
        """
        if self._model is not None:
            return True
        
        # Determine device
        device = self._get_device()
        
        # Try faster-whisper first (if configured and available)
        if self.config.use_faster_whisper and FASTER_WHISPER_AVAILABLE:
            try:
                compute_type = self._get_compute_type()
                
                self._model = FasterWhisperModel(
                    self.config.model_size,
                    device=device if device != "mps" else "cpu",  # faster-whisper doesn't support MPS
                    compute_type=compute_type,
                    download_root=self.config.cache_dir,
                )
                self._use_faster = True
                print(f"✓ Loaded faster-whisper model: {self.config.model_size}")
                return True
                
            except Exception as e:
                print(f"faster-whisper load failed: {e}, falling back to whisper")
        
        # Fallback to standard whisper
        if WHISPER_AVAILABLE:
            try:
                self._model = whisper.load_model(
                    self.config.model_size,
                    device=device,
                    download_root=self.config.cache_dir,
                )
                self._use_faster = False
                print(f"✓ Loaded whisper model: {self.config.model_size}")
                return True
                
            except Exception as e:
                print(f"Whisper load failed: {e}")
                return False
        
        print("Error: No whisper implementation available")
        return False
    
    def transcribe(
        self,
        audio: Union[bytes, str, np.ndarray],
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text.
        
        Args:
            audio: Audio bytes (WAV), file path, or numpy array
            language: Override language detection
        
        Returns:
            Dictionary with:
            - text: Transcribed text
            - language: Detected language
            - segments: Timestamped segments
            - duration: Audio duration
        """
        # Ensure model is loaded
        if not self.load_model():
            return {
                "text": "",
                "error": "Failed to load model",
                "success": False,
            }
        
        # Prepare audio
        audio_array = self._prepare_audio(audio)
        if audio_array is None:
            return {
                "text": "",
                "error": "Failed to prepare audio",
                "success": False,
            }
        
        start_time = time.time()
        
        # Transcribe
        try:
            if self._use_faster:
                result = self._transcribe_faster(audio_array, language)
            else:
                result = self._transcribe_standard(audio_array, language)
            
            result["duration_seconds"] = time.time() - start_time
            result["success"] = True
            return result
            
        except Exception as e:
            return {
                "text": "",
                "error": str(e),
                "success": False,
            }
    
    def transcribe_file(
        self,
        path: str,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Transcribe audio file."""
        return self.transcribe(path, language)
    
    def _transcribe_faster(
        self,
        audio: np.ndarray,
        language: Optional[str],
    ) -> Dict[str, Any]:
        """Transcribe using faster-whisper."""
        lang = language or self.config.language
        
        segments, info = self._model.transcribe(
            audio,
            language=lang,
            task=self.config.task,
            beam_size=self.config.beam_size,
            vad_filter=self.config.vad_filter,
            word_timestamps=self.config.word_timestamps,
        )
        
        # Collect segments
        segment_list = []
        full_text = []
        
        for segment in segments:
            segment_list.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
            })
            full_text.append(segment.text.strip())
        
        return {
            "text": " ".join(full_text),
            "language": info.language,
            "language_probability": info.language_probability,
            "segments": segment_list,
            "audio_duration": info.duration,
        }
    
    def _transcribe_standard(
        self,
        audio: np.ndarray,
        language: Optional[str],
    ) -> Dict[str, Any]:
        """Transcribe using standard whisper."""
        lang = language or self.config.language
        
        result = self._model.transcribe(
            audio,
            language=lang,
            task=self.config.task,
            beam_size=self.config.beam_size,
            word_timestamps=self.config.word_timestamps,
        )
        
        # Format segments
        segment_list = []
        for seg in result.get("segments", []):
            segment_list.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"].strip(),
            })
        
        return {
            "text": result["text"].strip(),
            "language": result.get("language", "unknown"),
            "segments": segment_list,
        }
    
    def _prepare_audio(
        self,
        audio: Union[bytes, str, np.ndarray],
    ) -> Optional[np.ndarray]:
        """Prepare audio for transcription."""
        if not NUMPY_AVAILABLE:
            return None
        
        # If numpy array, ensure correct format
        if isinstance(audio, np.ndarray):
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)
            if audio.max() > 1.0:
                audio = audio / 32767.0
            return audio
        
        # If file path
        if isinstance(audio, str):
            if not os.path.exists(audio):
                print(f"File not found: {audio}")
                return None
            
            # Use whisper's audio loader
            if WHISPER_AVAILABLE:
                try:
                    return whisper.load_audio(audio)
                except Exception:
                    pass
            
            # Fallback: load WAV manually
            return self._load_wav(audio)
        
        # If bytes, save to temp file and load
        if isinstance(audio, bytes):
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    f.write(audio)
                    temp_path = f.name
                
                result = self._prepare_audio(temp_path)
                os.unlink(temp_path)
                return result
                
            except Exception as e:
                print(f"Audio prepare error: {e}")
                return None
        
        return None
    
    def _load_wav(self, path: str) -> Optional[np.ndarray]:
        """Load WAV file manually."""
        try:
            import wave
            
            with wave.open(path, 'rb') as wav:
                sample_rate = wav.getframerate()
                n_frames = wav.getnframes()
                audio_bytes = wav.readframes(n_frames)
                
                # Convert to numpy
                audio = np.frombuffer(audio_bytes, dtype=np.int16)
                audio = audio.astype(np.float32) / 32767.0
                
                # Resample to 16kHz if needed
                if sample_rate != 16000:
                    # Simple resampling (for better quality, use librosa)
                    ratio = 16000 / sample_rate
                    new_length = int(len(audio) * ratio)
                    indices = np.linspace(0, len(audio) - 1, new_length).astype(int)
                    audio = audio[indices]
                
                return audio
                
        except Exception as e:
            print(f"WAV load error: {e}")
            return None
    
    def _get_device(self) -> str:
        """Determine the best device to use."""
        if self.config.device != "auto":
            return self.config.device
        
        # Check for CUDA
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"  # Apple Silicon
        except ImportError:
            pass
        
        return "cpu"
    
    def _get_compute_type(self) -> str:
        """Determine compute type for faster-whisper."""
        if self.config.compute_type != "auto":
            return self.config.compute_type
        
        device = self._get_device()
        
        if device == "cuda":
            return "float16"
        elif device == "cpu":
            return "int8"  # Faster on CPU
        else:
            return "float32"
    
    def unload_model(self) -> None:
        """Unload model to free memory."""
        self._model = None
        self._use_faster = False
        
        # Force garbage collection
        import gc
        gc.collect()
        
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass


# Convenience function
def transcribe(
    audio: Union[bytes, str],
    model_size: str = "base",
) -> str:
    """
    Quick transcribe function.
    
    Args:
        audio: Audio bytes or file path
        model_size: Whisper model size
    
    Returns:
        Transcribed text
    """
    stt = WhisperSTT(STTConfig(model_size=model_size))
    result = stt.transcribe(audio)
    return result.get("text", "")
