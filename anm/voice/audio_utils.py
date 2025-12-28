# ============================================================
# ANM V0-OpenSource — AUDIO UTILITIES
#  Audio recording, playback, and processing utilities
#  Works offline with standard audio libraries
# ============================================================

from __future__ import annotations
from typing import Optional, List, Tuple, Union
from dataclasses import dataclass, field
import os
import io
import wave
import struct
import threading
import time

# Audio library imports (with fallbacks)
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    sd = None

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    pyaudio = None

try:
    from scipy.io import wavfile
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    wavfile = None


@dataclass
class AudioConfig:
    """Audio configuration settings."""
    sample_rate: int = 16000      # 16kHz is standard for speech
    channels: int = 1             # Mono for speech
    chunk_size: int = 1024        # Buffer size
    format_bits: int = 16         # 16-bit audio
    silence_threshold: float = 0.01  # For VAD
    silence_duration: float = 1.0    # Seconds of silence to stop
    max_duration: float = 30.0       # Max recording duration


def get_audio_devices() -> dict:
    """Get available audio input/output devices."""
    devices = {
        "input": [],
        "output": [],
        "default_input": None,
        "default_output": None,
    }
    
    if SOUNDDEVICE_AVAILABLE:
        try:
            all_devices = sd.query_devices()
            default_input = sd.query_devices(kind='input')
            default_output = sd.query_devices(kind='output')
            
            for i, dev in enumerate(all_devices):
                if dev['max_input_channels'] > 0:
                    devices["input"].append({
                        "id": i,
                        "name": dev['name'],
                        "channels": dev['max_input_channels'],
                        "sample_rate": dev['default_samplerate'],
                    })
                if dev['max_output_channels'] > 0:
                    devices["output"].append({
                        "id": i,
                        "name": dev['name'],
                        "channels": dev['max_output_channels'],
                        "sample_rate": dev['default_samplerate'],
                    })
            
            devices["default_input"] = default_input['name']
            devices["default_output"] = default_output['name']
            
        except Exception as e:
            devices["error"] = str(e)
    
    elif PYAUDIO_AVAILABLE:
        try:
            p = pyaudio.PyAudio()
            for i in range(p.get_device_count()):
                dev = p.get_device_info_by_index(i)
                if dev['maxInputChannels'] > 0:
                    devices["input"].append({
                        "id": i,
                        "name": dev['name'],
                        "channels": dev['maxInputChannels'],
                        "sample_rate": dev['defaultSampleRate'],
                    })
                if dev['maxOutputChannels'] > 0:
                    devices["output"].append({
                        "id": i,
                        "name": dev['name'],
                        "channels": dev['maxOutputChannels'],
                        "sample_rate": dev['defaultSampleRate'],
                    })
            
            default_in = p.get_default_input_device_info()
            default_out = p.get_default_output_device_info()
            devices["default_input"] = default_in['name']
            devices["default_output"] = default_out['name']
            p.terminate()
            
        except Exception as e:
            devices["error"] = str(e)
    else:
        devices["error"] = "No audio library available (install sounddevice or pyaudio)"
    
    return devices


def record_audio(
    duration: Optional[float] = None,
    config: Optional[AudioConfig] = None,
    voice_activity_detection: bool = True,
    callback: Optional[callable] = None,
) -> Optional[bytes]:
    """
    Record audio from microphone.
    
    Args:
        duration: Recording duration in seconds (None for VAD-based)
        config: Audio configuration
        voice_activity_detection: Use VAD to auto-stop on silence
        callback: Optional callback for real-time audio level
    
    Returns:
        Audio data as bytes (WAV format)
    """
    if config is None:
        config = AudioConfig()
    
    if not NUMPY_AVAILABLE:
        print("Error: numpy required for audio recording")
        return None
    
    audio_data = []
    is_recording = True
    silence_start = None
    has_speech = False
    
    def audio_callback(indata, frames, time_info, status):
        nonlocal silence_start, has_speech
        
        if status:
            print(f"Audio status: {status}")
        
        audio_data.append(indata.copy())
        
        # Voice activity detection
        if voice_activity_detection:
            level = np.abs(indata).mean()
            
            if callback:
                callback(level)
            
            if level > config.silence_threshold:
                has_speech = True
                silence_start = None
            elif has_speech:
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start > config.silence_duration:
                    raise sd.CallbackStop()
    
    if SOUNDDEVICE_AVAILABLE:
        try:
            # Determine duration
            rec_duration = duration if duration else config.max_duration
            
            with sd.InputStream(
                samplerate=config.sample_rate,
                channels=config.channels,
                dtype='float32',
                callback=audio_callback,
            ):
                start_time = time.time()
                while time.time() - start_time < rec_duration:
                    time.sleep(0.1)
                    if not is_recording:
                        break
            
            if not audio_data:
                return None
            
            # Combine audio chunks
            audio = np.concatenate(audio_data, axis=0)
            
            # Convert to WAV bytes
            return _numpy_to_wav_bytes(audio, config.sample_rate)
            
        except sd.CallbackStop:
            # Normal stop from VAD
            if audio_data:
                audio = np.concatenate(audio_data, axis=0)
                return _numpy_to_wav_bytes(audio, config.sample_rate)
            return None
        except Exception as e:
            print(f"Recording error: {e}")
            return None
    
    elif PYAUDIO_AVAILABLE:
        try:
            p = pyaudio.PyAudio()
            stream = p.open(
                format=pyaudio.paFloat32,
                channels=config.channels,
                rate=config.sample_rate,
                input=True,
                frames_per_buffer=config.chunk_size,
            )
            
            rec_duration = duration if duration else config.max_duration
            start_time = time.time()
            
            while time.time() - start_time < rec_duration:
                data = stream.read(config.chunk_size, exception_on_overflow=False)
                audio_chunk = np.frombuffer(data, dtype=np.float32)
                audio_data.append(audio_chunk)
                
                if voice_activity_detection:
                    level = np.abs(audio_chunk).mean()
                    if callback:
                        callback(level)
                    
                    if level > config.silence_threshold:
                        has_speech = True
                        silence_start = None
                    elif has_speech:
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start > config.silence_duration:
                            break
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            if audio_data:
                audio = np.concatenate(audio_data)
                return _numpy_to_wav_bytes(audio, config.sample_rate)
            return None
            
        except Exception as e:
            print(f"Recording error: {e}")
            return None
    
    else:
        print("Error: No audio library available")
        return None


def play_audio(
    audio_data: Union[bytes, str],
    config: Optional[AudioConfig] = None,
    blocking: bool = True,
) -> bool:
    """
    Play audio data or file.
    
    Args:
        audio_data: WAV bytes or path to audio file
        config: Audio configuration
        blocking: Wait for playback to complete
    
    Returns:
        True if playback started successfully
    """
    if config is None:
        config = AudioConfig()
    
    # Load audio if path
    if isinstance(audio_data, str):
        audio_data = load_audio(audio_data)
        if audio_data is None:
            return False
    
    if not NUMPY_AVAILABLE:
        print("Error: numpy required for audio playback")
        return False
    
    # Parse WAV bytes
    audio_array, sample_rate = _wav_bytes_to_numpy(audio_data)
    if audio_array is None:
        return False
    
    if SOUNDDEVICE_AVAILABLE:
        try:
            sd.play(audio_array, sample_rate)
            if blocking:
                sd.wait()
            return True
        except Exception as e:
            print(f"Playback error: {e}")
            return False
    
    elif PYAUDIO_AVAILABLE:
        try:
            p = pyaudio.PyAudio()
            
            # Determine format
            if audio_array.dtype == np.float32:
                pa_format = pyaudio.paFloat32
            elif audio_array.dtype == np.int16:
                pa_format = pyaudio.paInt16
            else:
                audio_array = audio_array.astype(np.float32)
                pa_format = pyaudio.paFloat32
            
            stream = p.open(
                format=pa_format,
                channels=1,
                rate=sample_rate,
                output=True,
            )
            
            stream.write(audio_array.tobytes())
            
            if blocking:
                time.sleep(len(audio_array) / sample_rate)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            return True
            
        except Exception as e:
            print(f"Playback error: {e}")
            return False
    
    else:
        print("Error: No audio library available")
        return False


def save_audio(
    audio_data: bytes,
    path: str,
) -> bool:
    """Save audio bytes to file."""
    try:
        with open(path, 'wb') as f:
            f.write(audio_data)
        return True
    except Exception as e:
        print(f"Save error: {e}")
        return False


def load_audio(path: str) -> Optional[bytes]:
    """Load audio file to bytes."""
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return None
    
    try:
        with open(path, 'rb') as f:
            return f.read()
    except Exception as e:
        print(f"Load error: {e}")
        return None


def _numpy_to_wav_bytes(
    audio: np.ndarray,
    sample_rate: int,
) -> bytes:
    """Convert numpy array to WAV bytes."""
    if not NUMPY_AVAILABLE:
        return b''
    
    # Ensure float32 to int16 conversion
    if audio.dtype == np.float32 or audio.dtype == np.float64:
        audio = (audio * 32767).astype(np.int16)
    
    # Create WAV in memory
    buffer = io.BytesIO()
    
    with wave.open(buffer, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)  # 16-bit
        wav.setframerate(sample_rate)
        wav.writeframes(audio.tobytes())
    
    return buffer.getvalue()


def _wav_bytes_to_numpy(
    wav_bytes: bytes,
) -> Tuple[Optional[np.ndarray], int]:
    """Convert WAV bytes to numpy array."""
    if not NUMPY_AVAILABLE:
        return None, 0
    
    try:
        buffer = io.BytesIO(wav_bytes)
        
        with wave.open(buffer, 'rb') as wav:
            sample_rate = wav.getframerate()
            n_frames = wav.getnframes()
            audio_bytes = wav.readframes(n_frames)
            
            # Convert to numpy
            audio = np.frombuffer(audio_bytes, dtype=np.int16)
            audio = audio.astype(np.float32) / 32767.0
            
            return audio, sample_rate
            
    except Exception as e:
        print(f"WAV parse error: {e}")
        return None, 0


# Check availability
AUDIO_AVAILABLE = SOUNDDEVICE_AVAILABLE or PYAUDIO_AVAILABLE
