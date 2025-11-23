#!/usr/bin/env python3
"""
Minimal Voice-to-Text App
Clean, simple interface that relies on macOS built-in microphone indicator
"""

import sys
import os
import json
import tkinter as tk
from tkinter import messagebox
import threading
import time
import pyaudio
import wave
import numpy as np
from pathlib import Path
import queue
import speech_recognition as sr
import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.text_injector import TextInjector

class MinimalVoiceToTextApp:
    def __init__(self):
        # Load config
        self.config = self.load_config()
        
        # Create minimal window
        self.root = tk.Tk()
        self.root.title("🎤 Voice-to-Text")
        self.root.geometry("320x200")
        
        # Position in top-right corner
        self.root.geometry("+{}+{}".format(
            self.root.winfo_screenwidth() - 340, 20
        ))
        
        # Window settings for background use
        self.root.attributes('-topmost', True)
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_background)
        
        # State
        self.is_recording = False
        self.f13_held = False
        self.last_transcription = ""
        self.recording_count = 0
        
        # Audio components
        self.audio = None
        self.audio_queue = queue.Queue()
        self.stop_event = threading.Event()
        
        # Speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = None
        
        # Text injection
        self.text_injector = None
        
        # Setup components
        self.setup_audio()
        self.setup_speech_recognition()
        self.setup_text_injection()
        
        # Create minimal UI
        self.create_minimal_ui()
        
        # Setup F13 key listener
        self.setup_f13_listener()
        
        # Start background tasks
        self.start_background_tasks()
        
        print("✅ Minimal Voice-to-Text app ready!")
    
    def load_config(self):
        """Load configuration"""
        try:
            with open("config/settings.json", 'r') as f:
                return json.load(f)
        except:
            return {
                "hotkey": {"combination": "f13", "hold_to_record": True},
                "audio": {"sample_rate": 16000, "channels": 1},
                "system": {"paste_mode": True, "typing_speed": 0}
            }
    
    def setup_audio(self):
        """Setup audio system"""
        try:
            self.audio = pyaudio.PyAudio()
            self.sample_rate = self.config["audio"]["sample_rate"]
            self.channels = self.config["audio"]["channels"]
            self.chunk_size = 1024
            print("✅ Audio ready")
        except Exception as e:
            print(f"⚠️ Audio setup issue: {e}")
            self.audio = None
    
    def setup_speech_recognition(self):
        """Setup speech recognition"""
        try:
            self.microphone = sr.Microphone()
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("✅ Speech recognition ready")
        except Exception as e:
            print(f"⚠️ Speech recognition setup issue: {e}")
            self.microphone = None
    
    def setup_text_injection(self):
        """Setup text injection"""
        try:
            self.text_injector = TextInjector(self.config.get("system", {}))
            print("✅ Text injection ready")
        except Exception as e:
            print(f"⚠️ Text injection setup issue: {e}")
            self.text_injector = None
    
    def create_minimal_ui(self):
        """Create truly minimal UI"""
        # App title
        title = tk.Label(self.root, text="🎤 Voice-to-Text", 
                        font=("Arial", 14, "bold"), fg="darkgreen")
        title.pack(pady=8)
        
        # Simple status (no animation needed - macOS shows mic indicator)
        self.status_label = tk.Label(self.root, text="🟢 Ready", 
                                    font=("Arial", 12, "bold"), fg="green")
        self.status_label.pack(pady=8)
        
        # Usage info
        usage_frame = tk.Frame(self.root)
        usage_frame.pack(pady=5)
        
        tk.Label(usage_frame, text="Hold Globe/Fn to dictate", 
                font=("Arial", 10), fg="blue").pack()
        
        self.counter_label = tk.Label(usage_frame, text="Dictations: 0", 
                                     font=("Arial", 9), fg="gray")
        self.counter_label.pack()
        
        # Last result (compact)
        self.result_label = tk.Label(self.root, text="Ready for dictation", 
                                    font=("Arial", 9), wraplength=300, 
                                    justify=tk.LEFT, fg="darkblue")
        self.result_label.pack(pady=8, padx=10)
        
        # Minimal controls (small buttons)
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=8)
        
        tk.Button(control_frame, text="📋", command=self.copy_last,
                 font=("Arial", 8), width=2, height=1).pack(side=tk.LEFT, padx=3)
        
        tk.Button(control_frame, text="🗑️", command=self.clear_result,
                 font=("Arial", 8), width=2, height=1).pack(side=tk.LEFT, padx=3)
        
        tk.Button(control_frame, text="ℹ️", command=self.show_info,
                 font=("Arial", 8), width=2, height=1).pack(side=tk.LEFT, padx=3)
        
        tk.Button(control_frame, text="❌", command=self.quit_app,
                 font=("Arial", 8), width=2, height=1).pack(side=tk.RIGHT, padx=3)
    
    def setup_f13_listener(self):
        """Setup F13 key listener (no animation)"""
        try:
            from pynput import keyboard
            
            def on_key_press(key):
                try:
                    if (hasattr(key, 'name') and key.name == 'f13') or str(key) == 'Key.f13':
                        if not self.f13_held and not self.is_recording:
                            print("🎯 Globe/Fn PRESSED - Recording (macOS mic indicator will show)")
                            self.f13_held = True
                            
                            # Simple status update
                            self.status_label.config(text="🔴 Recording", fg="red")
                            self.root.after(0, self.start_recording)
                            
                except Exception as e:
                    print(f"Key press error: {e}")
            
            def on_key_release(key):
                try:
                    if (hasattr(key, 'name') and key.name == 'f13') or str(key) == 'Key.f13':
                        if self.f13_held and self.is_recording:
                            print("🎯 Globe/Fn RELEASED - Processing")
                            self.f13_held = False
                            
                            # Simple status update
                            self.status_label.config(text="🟡 Processing", fg="orange")
                            self.root.after(0, self.stop_and_inject)
                            
                except Exception as e:
                    print(f"Key release error: {e}")
            
            self.f13_listener = keyboard.Listener(
                on_press=on_key_press,
                on_release=on_key_release
            )
            self.f13_listener.start()
            
            print("✅ Globe/Fn key listener active")
            return True
            
        except Exception as e:
            print(f"⚠️ F13 listener failed: {e}")
            return False
    
    def start_recording(self):
        """Start recording"""
        if self.is_recording:
            return
        
        try:
            self.stop_event.clear()
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break
            
            self.is_recording = True
            
            # Start recording thread
            self.recording_thread = threading.Thread(target=self.record_audio, daemon=True)
            self.recording_thread.start()
            
        except Exception as e:
            print(f"Failed to start recording: {e}")
            self.reset_status()
    
    def stop_and_inject(self):
        """Stop recording and inject text"""
        if not self.is_recording:
            return
        
        try:
            self.is_recording = False
            self.stop_event.set()
            
            # Wait for recording thread
            if hasattr(self, 'recording_thread') and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=2.0)
            
            # Process in background thread
            processing_thread = threading.Thread(target=self.process_and_inject, daemon=True)
            processing_thread.start()
            
        except Exception as e:
            print(f"Failed to stop recording: {e}")
            self.reset_status()
    
    def process_and_inject(self):
        """Process speech and inject text"""
        try:
            # Collect audio data
            audio_data = []
            while not self.audio_queue.empty():
                try:
                    data = self.audio_queue.get_nowait()
                    audio_chunk = np.frombuffer(data, dtype=np.int16)
                    audio_data.extend(audio_chunk)
                except queue.Empty:
                    break
            
            if not audio_data:
                self.root.after(0, lambda: self.show_result("❌ No audio - hold key longer"))
                self.root.after(0, self.reset_status)
                return
            
            # Check audio quality
            audio_array = np.array(audio_data, dtype=np.int16)
            duration = len(audio_array) / self.sample_rate
            max_amplitude = np.max(np.abs(audio_array))
            
            # Save audio file
            audio_file = self.save_audio_file(audio_array)
            
            # Check if audio is too quiet
            if max_amplitude < 1000:
                self.root.after(0, lambda: self.show_result("❌ Audio too quiet - speak louder"))
                self.root.after(0, self.reset_status)
                return
            
            # Check if recording is too short
            if duration < 0.5:
                self.root.after(0, lambda: self.show_result("❌ Recording too short - hold key longer"))
                self.root.after(0, self.reset_status)
                return
            
            # Speech recognition
            transcription = self.recognize_speech(audio_file)
            
            if transcription:
                # Update UI and inject
                self.recording_count += 1
                self.root.after(0, lambda: self.show_result(f"✅ {transcription}"))
                self.root.after(0, lambda: self.counter_label.config(text=f"Dictations: {self.recording_count}"))
                self.root.after(0, lambda: self.inject_text(transcription))
            else:
                self.root.after(0, lambda: self.show_result("❌ Could not understand - try again"))
            
            self.root.after(0, self.reset_status_success)
            
        except Exception as e:
            print(f"Processing error: {e}")
            self.root.after(0, lambda: self.show_result(f"❌ Error: {e}"))
            self.root.after(0, self.reset_status)
    
    def recognize_speech(self, audio_file):
        """Recognize speech from audio file"""
        try:
            with sr.AudioFile(audio_file) as source:
                audio = self.recognizer.record(source)
            
            text = self.recognizer.recognize_google(audio)
            print(f"✅ Transcribed: {text}")
            return text.strip()
            
        except sr.UnknownValueError:
            print("❌ Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"❌ Recognition error: {e}")
            return None
        except Exception as e:
            print(f"❌ Recognition failed: {e}")
            return None
    
    def inject_text(self, text):
        """Inject text into active application"""
        try:
            if self.text_injector and text:
                time.sleep(0.2)
                success = self.text_injector.inject_text(text)
                
                if success:
                    print(f"✅ Injected: {text}")
                else:
                    print(f"⚠️ Injection failed: {text}")
                    
        except Exception as e:
            print(f"Injection error: {e}")
    
    def save_audio_file(self, audio_array):
        """Save audio file with timestamp"""
        try:
            recordings_dir = Path("recordings")
            recordings_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dictation_{timestamp}.wav"
            filepath = recordings_dir / filename
            
            with wave.open(str(filepath), 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_array.tobytes())
            
            return str(filepath)
            
        except Exception as e:
            print(f"Save error: {e}")
            return None
    
    def record_audio(self):
        """Record audio (macOS will show mic indicator)"""
        stream = None
        try:
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                start=False
            )
            
            stream.start_stream()
            
            while self.is_recording and not self.stop_event.is_set():
                try:
                    if stream.get_read_available() >= self.chunk_size:
                        data = stream.read(self.chunk_size, exception_on_overflow=False)
                        self.audio_queue.put(data)
                    else:
                        time.sleep(0.01)
                except Exception as e:
                    print(f"Audio read error: {e}")
                    break
            
        except Exception as e:
            print(f"Recording error: {e}")
        finally:
            if stream:
                try:
                    if stream.is_active():
                        stream.stop_stream()
                    stream.close()
                except Exception as e:
                    print(f"Stream cleanup error: {e}")
    
    def start_background_tasks(self):
        """Start background maintenance"""
        self.cleanup_old_recordings()
        self.root.after(3600000, self.start_background_tasks)  # Every hour
    
    def cleanup_old_recordings(self):
        """Clean up recordings older than 24 hours"""
        try:
            recordings_dir = Path("recordings")
            if not recordings_dir.exists():
                return
            
            now = datetime.datetime.now()
            cutoff_time = now - datetime.timedelta(hours=24)
            
            deleted_count = 0
            for audio_file in recordings_dir.glob("*.wav"):
                try:
                    file_time = datetime.datetime.fromtimestamp(audio_file.stat().st_mtime)
                    if file_time < cutoff_time:
                        audio_file.unlink()
                        deleted_count += 1
                except Exception as e:
                    print(f"Error deleting {audio_file}: {e}")
            
            if deleted_count > 0:
                print(f"🗑️ Cleaned up {deleted_count} old recordings")
                
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def show_result(self, text):
        """Show result in minimal UI"""
        self.result_label.config(text=text)
        if "✅" in text:
            self.last_transcription = text.replace("✅ ", "")
    
    def copy_last(self):
        """Copy last transcription"""
        if self.last_transcription:
            clean_text = self.last_transcription.replace("✅ ", "").replace("❌ ", "")
            self.root.clipboard_clear()
            self.root.clipboard_append(clean_text)
            self.status_label.config(text="📋 Copied", fg="blue")
            self.root.after(1500, self.reset_status)
    
    def clear_result(self):
        """Clear result"""
        self.result_label.config(text="Ready for dictation")
    
    def show_info(self):
        """Show app info"""
        info_msg = f"""
🎤 VOICE-TO-TEXT INFO

✅ STATUS: Ready for dictation
🌐 HOTKEY: Globe/Fn key (hold-to-record)
🎙️ INDICATOR: macOS mic indicator in menu bar
🗑️ CLEANUP: Auto-delete recordings after 24hrs

📊 USAGE:
Dictations completed: {self.recording_count}

💡 TIP: 
Watch for macOS microphone indicator in menu bar
when holding Globe/Fn key - that's your visual cue!

🔧 BACKGROUND MODE:
Leave this window open in corner.
Globe/Fn works from any application.
        """
        
        messagebox.showinfo("Info", info_msg)
    
    def minimize_to_background(self):
        """Handle window closing"""
        if messagebox.askyesno("Background Mode", 
                              "Minimize to background?\n\n✅ Globe/Fn key will still work\n✅ macOS mic indicator shows recording\n\nClick 'No' to quit."):
            self.root.iconify()
        else:
            self.quit_app()
    
    def reset_status(self):
        """Reset to ready state"""
        self.status_label.config(text="🟢 Ready", fg="green")
    
    def reset_status_success(self):
        """Reset after successful operation"""
        self.status_label.config(text="✅ Done", fg="green")
        self.root.after(2000, self.reset_status)
    
    def quit_app(self):
        """Quit application"""
        try:
            if self.is_recording:
                self.is_recording = False
                self.stop_event.set()
            
            if hasattr(self, 'f13_listener'):
                self.f13_listener.stop()
            
            if self.audio:
                self.audio.terminate()
            
            self.root.quit()
            self.root.destroy()
            
        except Exception as e:
            print(f"Quit error: {e}")
    
    def run(self):
        """Run the application"""
        print("🎤 Minimal Voice-to-Text App")
        print("=" * 35)
        print("✅ Clean, minimal interface")
        print("🌐 Globe/Fn hold-to-record")
        print("🎙️ macOS mic indicator shows recording")
        print("🗑️ 24hr auto-cleanup")
        print("📱 Perfect for background use")
        print()
        print("Ready! Watch menu bar for mic indicator when recording.")
        
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"App error: {e}")

def main():
    try:
        app = MinimalVoiceToTextApp()
        app.run()
    except Exception as e:
        print(f"Failed to start app: {e}")

if __name__ == "__main__":
    main()
