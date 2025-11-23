"""
Audio Recording System
Handles microphone input, audio processing, and streaming for voice recognition.
"""

import asyncio
import logging
import numpy as np
import pyaudio
import threading
import time
import wave
from typing import Callable, Optional, Dict, Any
import webrtcvad


class AudioRecorder:
    """Handles audio recording and processing for voice recognition."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize audio recorder with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Audio settings
        self.sample_rate = config.get("sample_rate", 16000)
        self.channels = config.get("channels", 1)
        self.chunk_duration_ms = config.get("chunk_duration_ms", 1000)
        self.chunk_size = int(self.sample_rate * self.chunk_duration_ms / 1000)
        
        # Audio processing settings
        self.noise_suppression = config.get("noise_suppression", True)
        self.echo_cancellation = config.get("echo_cancellation", True)
        self.auto_gain_control = config.get("auto_gain_control", True)
        self.vad_enabled = config.get("voice_activity_detection", True)
        self.silence_threshold = config.get("silence_threshold", 0.01)
        self.max_duration = config.get("max_recording_duration", 300)  # 5 minutes
        
        # PyAudio setup
        self.audio = None
        self.stream = None
        self.is_recording = False
        self.is_initialized = False
        
        # Voice Activity Detection
        self.vad = None
        if self.vad_enabled:
            try:
                self.vad = webrtcvad.Vad(2)  # Aggressiveness level 0-3
            except Exception as e:
                self.logger.warning(f"Could not initialize VAD: {e}")
                self.vad_enabled = False
        
        # Callbacks
        self.on_audio_chunk: Optional[Callable[[bytes], None]] = None
        self.on_recording_state_change: Optional[Callable[[bool], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
        self.on_volume_change: Optional[Callable[[float], None]] = None
        
        # Recording state
        self.recording_start_time = 0
        self.total_chunks = 0
        self.audio_buffer = []
        
        # Threading
        self.recording_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
    async def initialize(self):
        """Initialize the audio system."""
        try:
            self.logger.info("Initializing audio recorder...")
            
            # Initialize PyAudio
            self.audio = pyaudio.PyAudio()
            
            # Check for available input devices
            self._log_audio_devices()
            
            # Find best input device
            input_device_index = self._find_best_input_device()
            
            # Test microphone access
            if not self._test_microphone_access(input_device_index):
                raise Exception("Could not access microphone. Check permissions.")
            
            self.is_initialized = True
            self.logger.info("Audio recorder initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize audio recorder: {e}")
            raise
    
    def _log_audio_devices(self):
        """Log available audio devices for debugging."""
        try:
            device_count = self.audio.get_device_count()
            self.logger.debug(f"Found {device_count} audio devices:")
            
            for i in range(device_count):
                device_info = self.audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    self.logger.debug(f"  Input Device {i}: {device_info['name']}")
                    
        except Exception as e:
            self.logger.warning(f"Could not enumerate audio devices: {e}")
    
    def _find_best_input_device(self) -> Optional[int]:
        """Find the best available input device."""
        try:
            # Try default input device first
            default_device = self.audio.get_default_input_device_info()
            if default_device['maxInputChannels'] >= self.channels:
                self.logger.info(f"Using default input device: {default_device['name']}")
                return default_device['index']
            
            # Search for suitable device
            device_count = self.audio.get_device_count()
            for i in range(device_count):
                device_info = self.audio.get_device_info_by_index(i)
                if (device_info['maxInputChannels'] >= self.channels and
                    device_info['defaultSampleRate'] >= self.sample_rate):
                    self.logger.info(f"Using input device: {device_info['name']}")
                    return i
            
            self.logger.warning("No suitable input device found, using default")
            return None
            
        except Exception as e:
            self.logger.warning(f"Error finding input device: {e}")
            return None
    
    def _test_microphone_access(self, device_index: Optional[int]) -> bool:
        """Test if we can access the microphone."""
        try:
            # Try to open a stream briefly
            test_stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=1024
            )
            
            # Read a small amount of data
            test_stream.read(1024, exception_on_overflow=False)
            test_stream.stop_stream()
            test_stream.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Microphone access test failed: {e}")
            return False
    
    async def start_recording(self):
        """Start audio recording."""
        if not self.is_initialized:
            raise Exception("Audio recorder not initialized")
        
        if self.is_recording:
            return
        
        try:
            self.logger.info("Starting audio recording...")
            
            # Reset state
            self.stop_event.clear()
            self.recording_start_time = time.time()
            self.total_chunks = 0
            self.audio_buffer = []
            
            # Start recording thread
            self.recording_thread = threading.Thread(
                target=self._recording_loop,
                daemon=True
            )
            self.recording_thread.start()
            
            self.is_recording = True
            
            if self.on_recording_state_change:
                self.on_recording_state_change(True)
            
            self.logger.info("Audio recording started")
            
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            if self.on_error:
                self.on_error(e)
            raise
    
    async def stop_recording(self) -> Optional[bytes]:
        """Stop audio recording and return recorded data."""
        if not self.is_recording:
            return None
        
        try:
            self.logger.info("Stopping audio recording...")
            
            # Signal stop
            self.stop_event.set()
            
            # Wait for recording thread to finish
            if self.recording_thread:
                self.recording_thread.join(timeout=2.0)
            
            self.is_recording = False
            
            if self.on_recording_state_change:
                self.on_recording_state_change(False)
            
            # Combine audio buffer
            if self.audio_buffer:
                combined_audio = b''.join(self.audio_buffer)
                self.logger.info(f"Recording stopped. Captured {len(combined_audio)} bytes")
                return combined_audio
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error stopping recording: {e}")
            if self.on_error:
                self.on_error(e)
            return None
    
    def _recording_loop(self):
        """Main recording loop (runs in separate thread)."""
        stream = None
        
        try:
            # Open audio stream
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=None
            )
            
            stream.start_stream()
            self.logger.debug("Audio stream started")
            
            while not self.stop_event.is_set():
                try:
                    # Check max duration
                    if time.time() - self.recording_start_time > self.max_duration:
                        self.logger.warning("Maximum recording duration reached")
                        break
                    
                    # Read audio chunk
                    audio_data = stream.read(
                        self.chunk_size,
                        exception_on_overflow=False
                    )
                    
                    # Process audio chunk
                    processed_data = self._process_audio_chunk(audio_data)
                    
                    if processed_data:
                        # Add to buffer
                        self.audio_buffer.append(processed_data)
                        self.total_chunks += 1
                        
                        # Send to callback
                        if self.on_audio_chunk:
                            self.on_audio_chunk(processed_data)
                    
                except Exception as e:
                    self.logger.error(f"Error in recording loop: {e}")
                    if self.on_error:
                        self.on_error(e)
                    break
            
        except Exception as e:
            self.logger.error(f"Recording loop error: {e}")
            if self.on_error:
                self.on_error(e)
        
        finally:
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                    self.logger.debug("Audio stream closed")
                except Exception as e:
                    self.logger.error(f"Error closing stream: {e}")
    
    def _process_audio_chunk(self, audio_data: bytes) -> Optional[bytes]:
        """Process raw audio chunk."""
        try:
            # Convert to numpy array for processing
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Calculate volume level
            volume = self._calculate_volume(audio_array)
            
            if self.on_volume_change:
                self.on_volume_change(volume)
            
            # Voice Activity Detection
            if self.vad_enabled and self.vad:
                # VAD requires specific sample rates (8000, 16000, 32000, 48000)
                if self.sample_rate in [8000, 16000, 32000, 48000]:
                    try:
                        # VAD expects 10, 20, or 30ms frames
                        frame_duration = 30  # ms
                        frame_size = int(self.sample_rate * frame_duration / 1000)
                        
                        # Process in VAD-compatible frames
                        has_voice = False
                        for i in range(0, len(audio_array), frame_size):
                            frame = audio_array[i:i + frame_size]
                            if len(frame) == frame_size:
                                frame_bytes = frame.tobytes()
                                if self.vad.is_speech(frame_bytes, self.sample_rate):
                                    has_voice = True
                                    break
                        
                        # Skip chunk if no voice detected
                        if not has_voice and volume < self.silence_threshold:
                            return None
                            
                    except Exception as e:
                        self.logger.debug(f"VAD processing error: {e}")
                        # Fall back to volume-based detection
                        if volume < self.silence_threshold:
                            return None
                else:
                    # Fall back to volume-based detection for unsupported sample rates
                    if volume < self.silence_threshold:
                        return None
            
            # Apply audio processing
            processed_array = self._apply_audio_processing(audio_array)
            
            return processed_array.tobytes()
            
        except Exception as e:
            self.logger.error(f"Error processing audio chunk: {e}")
            return audio_data  # Return original data if processing fails
    
    def _calculate_volume(self, audio_array: np.ndarray) -> float:
        """Calculate RMS volume of audio data."""
        try:
            # Calculate RMS (Root Mean Square)
            rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))
            
            # Normalize to 0-1 range
            max_value = 32767.0  # Max value for 16-bit audio
            volume = min(rms / max_value, 1.0)
            
            return volume
            
        except Exception:
            return 0.0
    
    def _apply_audio_processing(self, audio_array: np.ndarray) -> np.ndarray:
        """Apply audio processing (noise suppression, etc.)."""
        try:
            processed = audio_array.copy()
            
            # Simple noise gate
            if self.noise_suppression:
                # Apply simple noise gate based on volume threshold
                volume = self._calculate_volume(processed)
                if volume < self.silence_threshold:
                    processed = processed * 0.1  # Reduce very quiet audio
            
            # Auto gain control (simple implementation)
            if self.auto_gain_control:
                # Normalize audio level
                max_val = np.max(np.abs(processed))
                if max_val > 0:
                    target_level = 16000  # Target level for 16-bit audio
                    gain = min(target_level / max_val, 4.0)  # Limit gain to 4x
                    processed = (processed * gain).astype(np.int16)
            
            return processed
            
        except Exception as e:
            self.logger.error(f"Audio processing error: {e}")
            return audio_array
    
    def save_recording(self, filename: str, audio_data: bytes):
        """Save recorded audio to WAV file."""
        try:
            with wave.open(filename, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data)
            
            self.logger.info(f"Audio saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving audio: {e}")
            raise
    
    def on_audio_chunk_received(self, callback: Callable[[bytes], None]):
        """Set callback for audio chunk events."""
        self.on_audio_chunk = callback
    
    def on_recording_state_changed(self, callback: Callable[[bool], None]):
        """Set callback for recording state changes."""
        self.on_recording_state_change = callback
    
    def on_error_received(self, callback: Callable[[Exception], None]):
        """Set callback for error events."""
        self.on_error = callback
    
    def on_volume_changed(self, callback: Callable[[float], None]):
        """Set callback for volume level changes."""
        self.on_volume_change = callback
    
    async def cleanup(self):
        """Cleanup audio resources."""
        self.logger.info("Cleaning up audio recorder...")
        
        if self.is_recording:
            await self.stop_recording()
        
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                self.logger.error(f"Error closing stream: {e}")
        
        if self.audio:
            try:
                self.audio.terminate()
            except Exception as e:
                self.logger.error(f"Error terminating PyAudio: {e}")
        
        self.is_initialized = False
        self.logger.info("Audio recorder cleanup complete")


class AudioDeviceManager:
    """Utility class for managing audio devices."""
    
    @staticmethod
    def list_input_devices() -> list:
        """List all available input devices."""
        devices = []
        audio = pyaudio.PyAudio()
        
        try:
            device_count = audio.get_device_count()
            
            for i in range(device_count):
                device_info = audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels'],
                        'sample_rate': device_info['defaultSampleRate']
                    })
        
        finally:
            audio.terminate()
        
        return devices
    
    @staticmethod
    def test_device(device_index: int, sample_rate: int = 16000) -> bool:
        """Test if a device works with given settings."""
        audio = pyaudio.PyAudio()
        
        try:
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=1024
            )
            
            # Try to read some data
            stream.read(1024, exception_on_overflow=False)
            stream.close()
            
            return True
            
        except Exception:
            return False
        
        finally:
            audio.terminate()
