"""
Settings Panel UI
Configuration interface for hotkeys, audio settings, and preferences.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import logging
from typing import Dict, Any, Callable, Optional
from pathlib import Path


class SettingsPanel:
    """Settings configuration panel."""
    
    def __init__(self, config: Dict[str, Any], on_config_changed: Optional[Callable[[Dict[str, Any]], None]] = None):
        """Initialize settings panel."""
        self.config = config.copy()
        self.original_config = config.copy()
        self.on_config_changed = on_config_changed
        self.logger = logging.getLogger(__name__)
        
        # UI elements
        self.root: Optional[tk.Toplevel] = None
        self.notebook: Optional[ttk.Notebook] = None
        
        # Setting variables
        self.vars = {}
        
    def show(self, parent: Optional[tk.Tk] = None):
        """Show the settings panel."""
        if self.root and self.root.winfo_exists():
            self.root.lift()
            return
        
        try:
            self._create_settings_ui(parent)
        except Exception as e:
            self.logger.error(f"Error showing settings panel: {e}")
    
    def _create_settings_ui(self, parent: Optional[tk.Tk]):
        """Create the settings UI."""
        # Create window
        if parent:
            self.root = tk.Toplevel(parent)
        else:
            self.root = tk.Tk()
        
        self.root.title("Voice-to-Text Settings")
        self.root.geometry("500x600")
        self.root.resizable(True, True)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs
        self._create_hotkey_tab()
        self._create_audio_tab()
        self._create_voxtral_tab()
        self._create_text_processing_tab()
        self._create_ui_tab()
        self._create_advanced_tab()
        
        # Create button frame
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Buttons
        ttk.Button(
            button_frame,
            text="Reset to Defaults",
            command=self._reset_to_defaults
        ).pack(side="left")
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel
        ).pack(side="right", padx=(5, 0))
        
        ttk.Button(
            button_frame,
            text="Apply",
            command=self._apply_settings
        ).pack(side="right")
        
        ttk.Button(
            button_frame,
            text="OK",
            command=self._ok
        ).pack(side="right", padx=(5, 0))
        
        # Load current settings
        self._load_settings()
        
        # Center window
        self._center_window()
    
    def _create_hotkey_tab(self):
        """Create hotkey configuration tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Hotkeys")
        
        # Main hotkey
        hotkey_frame = ttk.LabelFrame(frame, text="Recording Hotkey", padding=10)
        hotkey_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(hotkey_frame, text="Hotkey combination:").pack(anchor="w")
        
        hotkey_entry_frame = tk.Frame(hotkey_frame)
        hotkey_entry_frame.pack(fill="x", pady=5)
        
        self.vars["hotkey_combination"] = tk.StringVar()
        hotkey_entry = ttk.Entry(
            hotkey_entry_frame,
            textvariable=self.vars["hotkey_combination"],
            width=20
        )
        hotkey_entry.pack(side="left")
        
        ttk.Button(
            hotkey_entry_frame,
            text="Detect",
            command=self._detect_hotkey
        ).pack(side="left", padx=(5, 0))
        
        ttk.Button(
            hotkey_entry_frame,
            text="Test",
            command=self._test_hotkey
        ).pack(side="left", padx=(5, 0))
        
        # Hotkey mode
        mode_frame = tk.Frame(hotkey_frame)
        mode_frame.pack(fill="x", pady=5)
        
        self.vars["hold_to_record"] = tk.BooleanVar()
        ttk.Checkbutton(
            mode_frame,
            text="Hold to record (instead of toggle)",
            variable=self.vars["hold_to_record"]
        ).pack(anchor="w")
        
        # Recommended hotkeys
        rec_frame = ttk.LabelFrame(frame, text="Recommended Hotkeys (macOS)", padding=10)
        rec_frame.pack(fill="x", padx=10, pady=5)
        
        recommendations = [
            "cmd+shift+space (Default)",
            "fn (Function key)",
            "ctrl+opt+space",
            "opt+cmd+space",
            "cmd+right",
            "opt+right"
        ]
        
        for rec in recommendations:
            btn = ttk.Button(
                rec_frame,
                text=rec,
                command=lambda r=rec.split()[0]: self._set_hotkey(r)
            )
            btn.pack(fill="x", pady=1)
    
    def _create_audio_tab(self):
        """Create audio settings tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Audio")
        
        # Audio quality
        quality_frame = ttk.LabelFrame(frame, text="Audio Quality", padding=10)
        quality_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(quality_frame, text="Sample Rate:").pack(anchor="w")
        self.vars["sample_rate"] = tk.StringVar()
        sample_rate_combo = ttk.Combobox(
            quality_frame,
            textvariable=self.vars["sample_rate"],
            values=["8000", "16000", "22050", "44100", "48000"],
            state="readonly"
        )
        sample_rate_combo.pack(fill="x", pady=2)
        
        tk.Label(quality_frame, text="Channels:").pack(anchor="w", pady=(10, 0))
        self.vars["channels"] = tk.StringVar()
        channels_combo = ttk.Combobox(
            quality_frame,
            textvariable=self.vars["channels"],
            values=["1 (Mono)", "2 (Stereo)"],
            state="readonly"
        )
        channels_combo.pack(fill="x", pady=2)
        
        # Audio processing
        processing_frame = ttk.LabelFrame(frame, text="Audio Processing", padding=10)
        processing_frame.pack(fill="x", padx=10, pady=5)
        
        self.vars["noise_suppression"] = tk.BooleanVar()
        ttk.Checkbutton(
            processing_frame,
            text="Noise suppression",
            variable=self.vars["noise_suppression"]
        ).pack(anchor="w")
        
        self.vars["echo_cancellation"] = tk.BooleanVar()
        ttk.Checkbutton(
            processing_frame,
            text="Echo cancellation",
            variable=self.vars["echo_cancellation"]
        ).pack(anchor="w")
        
        self.vars["auto_gain_control"] = tk.BooleanVar()
        ttk.Checkbutton(
            processing_frame,
            text="Automatic gain control",
            variable=self.vars["auto_gain_control"]
        ).pack(anchor="w")
        
        self.vars["voice_activity_detection"] = tk.BooleanVar()
        ttk.Checkbutton(
            processing_frame,
            text="Voice activity detection",
            variable=self.vars["voice_activity_detection"]
        ).pack(anchor="w")
        
        # Sensitivity
        sensitivity_frame = ttk.LabelFrame(frame, text="Sensitivity", padding=10)
        sensitivity_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(sensitivity_frame, text="Silence threshold:").pack(anchor="w")
        self.vars["silence_threshold"] = tk.DoubleVar()
        threshold_scale = ttk.Scale(
            sensitivity_frame,
            from_=0.001,
            to=0.1,
            variable=self.vars["silence_threshold"],
            orient="horizontal"
        )
        threshold_scale.pack(fill="x", pady=2)
        
        # Test audio button
        ttk.Button(
            frame,
            text="Test Microphone",
            command=self._test_microphone
        ).pack(pady=10)
    
    def _create_voxtral_tab(self):
        """Create Voxtral settings tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Speech Recognition")
        
        # Model settings
        model_frame = ttk.LabelFrame(frame, text="Voxtral Model", padding=10)
        model_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(model_frame, text="Model:").pack(anchor="w")
        self.vars["voxtral_model"] = tk.StringVar()
        model_combo = ttk.Combobox(
            model_frame,
            textvariable=self.vars["voxtral_model"],
            values=["voxtral-mini", "voxtral-base", "voxtral-large"],
            state="readonly"
        )
        model_combo.pack(fill="x", pady=2)
        
        tk.Label(model_frame, text="Language:").pack(anchor="w", pady=(10, 0))
        self.vars["language"] = tk.StringVar()
        language_combo = ttk.Combobox(
            model_frame,
            textvariable=self.vars["language"],
            values=["auto", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
            state="readonly"
        )
        language_combo.pack(fill="x", pady=2)
        
        # Advanced features
        features_frame = ttk.LabelFrame(frame, text="Advanced Features", padding=10)
        features_frame.pack(fill="x", padx=10, pady=5)
        
        self.vars["enable_speaker_detection"] = tk.BooleanVar()
        ttk.Checkbutton(
            features_frame,
            text="Speaker detection",
            variable=self.vars["enable_speaker_detection"]
        ).pack(anchor="w")
        
        self.vars["enable_sentiment_analysis"] = tk.BooleanVar()
        ttk.Checkbutton(
            features_frame,
            text="Sentiment analysis",
            variable=self.vars["enable_sentiment_analysis"]
        ).pack(anchor="w")
        
        # Confidence threshold
        tk.Label(features_frame, text="Confidence threshold:").pack(anchor="w", pady=(10, 0))
        self.vars["confidence_threshold"] = tk.DoubleVar()
        confidence_scale = ttk.Scale(
            features_frame,
            from_=0.1,
            to=1.0,
            variable=self.vars["confidence_threshold"],
            orient="horizontal"
        )
        confidence_scale.pack(fill="x", pady=2)
        
        # Local vs Cloud
        deployment_frame = ttk.LabelFrame(frame, text="Deployment", padding=10)
        deployment_frame.pack(fill="x", padx=10, pady=5)
        
        self.vars["local_mode"] = tk.BooleanVar()
        ttk.Checkbutton(
            deployment_frame,
            text="Run locally (recommended for privacy)",
            variable=self.vars["local_mode"]
        ).pack(anchor="w")
        
        # Model management
        ttk.Button(
            frame,
            text="Download/Update Models",
            command=self._manage_models
        ).pack(pady=10)
    
    def _create_text_processing_tab(self):
        """Create text processing settings tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Text Processing")
        
        # Text cleanup
        cleanup_frame = ttk.LabelFrame(frame, text="Text Cleanup", padding=10)
        cleanup_frame.pack(fill="x", padx=10, pady=5)
        
        self.vars["remove_filler_words"] = tk.BooleanVar()
        ttk.Checkbutton(
            cleanup_frame,
            text="Remove filler words (um, uh, etc.)",
            variable=self.vars["remove_filler_words"]
        ).pack(anchor="w")
        
        self.vars["auto_punctuation"] = tk.BooleanVar()
        ttk.Checkbutton(
            cleanup_frame,
            text="Add punctuation automatically",
            variable=self.vars["auto_punctuation"]
        ).pack(anchor="w")
        
        self.vars["auto_capitalization"] = tk.BooleanVar()
        ttk.Checkbutton(
            cleanup_frame,
            text="Auto-capitalize sentences",
            variable=self.vars["auto_capitalization"]
        ).pack(anchor="w")
        
        self.vars["trim_whitespace"] = tk.BooleanVar()
        ttk.Checkbutton(
            cleanup_frame,
            text="Trim extra whitespace",
            variable=self.vars["trim_whitespace"]
        ).pack(anchor="w")
        
        # Custom filler words
        filler_frame = ttk.LabelFrame(frame, text="Custom Filler Words", padding=10)
        filler_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(filler_frame, text="Additional words to remove (comma-separated):").pack(anchor="w")
        self.vars["custom_filler_words"] = tk.StringVar()
        ttk.Entry(
            filler_frame,
            textvariable=self.vars["custom_filler_words"]
        ).pack(fill="x", pady=2)
    
    def _create_ui_tab(self):
        """Create UI settings tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Interface")
        
        # Status window
        status_frame = ttk.LabelFrame(frame, text="Status Window", padding=10)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        self.vars["show_status_window"] = tk.BooleanVar()
        ttk.Checkbutton(
            status_frame,
            text="Show status window",
            variable=self.vars["show_status_window"]
        ).pack(anchor="w")
        
        tk.Label(status_frame, text="Position:").pack(anchor="w", pady=(10, 0))
        self.vars["status_window_position"] = tk.StringVar()
        position_combo = ttk.Combobox(
            status_frame,
            textvariable=self.vars["status_window_position"],
            values=["top-right", "top-left", "bottom-right", "bottom-left", "center"],
            state="readonly"
        )
        position_combo.pack(fill="x", pady=2)
        
        # Notifications
        notif_frame = ttk.LabelFrame(frame, text="Notifications", padding=10)
        notif_frame.pack(fill="x", padx=10, pady=5)
        
        self.vars["show_notifications"] = tk.BooleanVar()
        ttk.Checkbutton(
            notif_frame,
            text="Show system notifications",
            variable=self.vars["show_notifications"]
        ).pack(anchor="w")
        
        self.vars["minimize_to_tray"] = tk.BooleanVar()
        ttk.Checkbutton(
            notif_frame,
            text="Minimize to system tray",
            variable=self.vars["minimize_to_tray"]
        ).pack(anchor="w")
        
        # Theme
        theme_frame = ttk.LabelFrame(frame, text="Appearance", padding=10)
        theme_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(theme_frame, text="Theme:").pack(anchor="w")
        self.vars["theme"] = tk.StringVar()
        theme_combo = ttk.Combobox(
            theme_frame,
            textvariable=self.vars["theme"],
            values=["system", "light", "dark"],
            state="readonly"
        )
        theme_combo.pack(fill="x", pady=2)
    
    def _create_advanced_tab(self):
        """Create advanced settings tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Advanced")
        
        # System integration
        system_frame = ttk.LabelFrame(frame, text="System Integration", padding=10)
        system_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(system_frame, text="Text injection method:").pack(anchor="w")
        self.vars["paste_mode"] = tk.BooleanVar()
        ttk.Checkbutton(
            system_frame,
            text="Use clipboard (faster, recommended)",
            variable=self.vars["paste_mode"]
        ).pack(anchor="w")
        
        tk.Label(system_frame, text="Typing speed (ms per character):").pack(anchor="w", pady=(10, 0))
        self.vars["typing_speed"] = tk.IntVar()
        typing_scale = ttk.Scale(
            system_frame,
            from_=0,
            to=100,
            variable=self.vars["typing_speed"],
            orient="horizontal"
        )
        typing_scale.pack(fill="x", pady=2)
        
        tk.Label(system_frame, text="Focus delay (ms):").pack(anchor="w", pady=(10, 0))
        self.vars["focus_delay_ms"] = tk.IntVar()
        focus_scale = ttk.Scale(
            system_frame,
            from_=0,
            to=1000,
            variable=self.vars["focus_delay_ms"],
            orient="horizontal"
        )
        focus_scale.pack(fill="x", pady=2)
        
        # Logging
        logging_frame = ttk.LabelFrame(frame, text="Logging", padding=10)
        logging_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(logging_frame, text="Log level:").pack(anchor="w")
        self.vars["log_level"] = tk.StringVar()
        log_combo = ttk.Combobox(
            logging_frame,
            textvariable=self.vars["log_level"],
            values=["DEBUG", "INFO", "WARNING", "ERROR"],
            state="readonly"
        )
        log_combo.pack(fill="x", pady=2)
        
        self.vars["file_logging"] = tk.BooleanVar()
        ttk.Checkbutton(
            logging_frame,
            text="Enable file logging",
            variable=self.vars["file_logging"]
        ).pack(anchor="w", pady=(10, 0))
        
        # Configuration management
        config_frame = ttk.LabelFrame(frame, text="Configuration", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)
        
        button_frame = tk.Frame(config_frame)
        button_frame.pack(fill="x")
        
        ttk.Button(
            button_frame,
            text="Export Settings",
            command=self._export_settings
        ).pack(side="left")
        
        ttk.Button(
            button_frame,
            text="Import Settings",
            command=self._import_settings
        ).pack(side="left", padx=(5, 0))
        
        ttk.Button(
            button_frame,
            text="Open Config Folder",
            command=self._open_config_folder
        ).pack(side="right")
    
    def _load_settings(self):
        """Load current settings into UI."""
        try:
            # Hotkey settings
            hotkey_config = self.config.get("hotkey", {})
            self.vars["hotkey_combination"].set(hotkey_config.get("combination", "cmd+shift+space"))
            self.vars["hold_to_record"].set(hotkey_config.get("hold_to_record", False))
            
            # Audio settings
            audio_config = self.config.get("audio", {})
            self.vars["sample_rate"].set(str(audio_config.get("sample_rate", 16000)))
            channels = audio_config.get("channels", 1)
            self.vars["channels"].set(f"{channels} ({'Mono' if channels == 1 else 'Stereo'})")
            self.vars["noise_suppression"].set(audio_config.get("noise_suppression", True))
            self.vars["echo_cancellation"].set(audio_config.get("echo_cancellation", True))
            self.vars["auto_gain_control"].set(audio_config.get("auto_gain_control", True))
            self.vars["voice_activity_detection"].set(audio_config.get("voice_activity_detection", True))
            self.vars["silence_threshold"].set(audio_config.get("silence_threshold", 0.01))
            
            # Voxtral settings
            voxtral_config = self.config.get("voxtral", {})
            self.vars["voxtral_model"].set(voxtral_config.get("model", "voxtral-mini"))
            self.vars["language"].set(voxtral_config.get("language", "auto"))
            self.vars["enable_speaker_detection"].set(voxtral_config.get("enable_speaker_detection", False))
            self.vars["enable_sentiment_analysis"].set(voxtral_config.get("enable_sentiment_analysis", False))
            self.vars["confidence_threshold"].set(voxtral_config.get("confidence_threshold", 0.7))
            self.vars["local_mode"].set(voxtral_config.get("local_mode", True))
            
            # Text processing settings
            text_config = self.config.get("text_processing", {})
            self.vars["remove_filler_words"].set(text_config.get("remove_filler_words", True))
            self.vars["auto_punctuation"].set(text_config.get("auto_punctuation", True))
            self.vars["auto_capitalization"].set(text_config.get("auto_capitalization", True))
            self.vars["trim_whitespace"].set(text_config.get("trim_whitespace", True))
            
            filler_words = text_config.get("filler_words", [])
            custom_words = [w for w in filler_words if w not in ["um", "uh", "er", "ah", "like", "you know"]]
            self.vars["custom_filler_words"].set(", ".join(custom_words))
            
            # UI settings
            ui_config = self.config.get("ui", {})
            self.vars["show_status_window"].set(ui_config.get("show_status_window", True))
            self.vars["status_window_position"].set(ui_config.get("status_window_position", "top-right"))
            self.vars["show_notifications"].set(ui_config.get("show_notifications", True))
            self.vars["minimize_to_tray"].set(ui_config.get("minimize_to_tray", True))
            self.vars["theme"].set(ui_config.get("theme", "system"))
            
            # System settings
            system_config = self.config.get("system", {})
            self.vars["paste_mode"].set(system_config.get("paste_mode", True))
            self.vars["typing_speed"].set(system_config.get("typing_speed", 0))
            self.vars["focus_delay_ms"].set(system_config.get("focus_delay_ms", 100))
            
            # Logging settings
            logging_config = self.config.get("logging", {})
            self.vars["log_level"].set(logging_config.get("level", "INFO"))
            self.vars["file_logging"].set(logging_config.get("file_logging", True))
            
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")
    
    def _apply_settings(self):
        """Apply current settings."""
        try:
            # Build new config
            new_config = self._build_config_from_ui()
            
            # Update config
            self.config = new_config
            
            # Notify callback
            if self.on_config_changed:
                self.on_config_changed(new_config)
            
            messagebox.showinfo("Settings", "Settings applied successfully!")
            
        except Exception as e:
            self.logger.error(f"Error applying settings: {e}")
            messagebox.showerror("Error", f"Failed to apply settings: {e}")
    
    def _build_config_from_ui(self) -> Dict[str, Any]:
        """Build configuration dictionary from UI values."""
        config = {}
        
        # Hotkey settings
        config["hotkey"] = {
            "combination": self.vars["hotkey_combination"].get(),
            "hold_to_record": self.vars["hold_to_record"].get(),
            "toggle_mode": not self.vars["hold_to_record"].get()
        }
        
        # Audio settings
        channels_text = self.vars["channels"].get()
        channels = 1 if "Mono" in channels_text else 2
        
        config["audio"] = {
            "sample_rate": int(self.vars["sample_rate"].get()),
            "channels": channels,
            "noise_suppression": self.vars["noise_suppression"].get(),
            "echo_cancellation": self.vars["echo_cancellation"].get(),
            "auto_gain_control": self.vars["auto_gain_control"].get(),
            "voice_activity_detection": self.vars["voice_activity_detection"].get(),
            "silence_threshold": self.vars["silence_threshold"].get()
        }
        
        # Voxtral settings
        config["voxtral"] = {
            "model": self.vars["voxtral_model"].get(),
            "language": self.vars["language"].get(),
            "enable_speaker_detection": self.vars["enable_speaker_detection"].get(),
            "enable_sentiment_analysis": self.vars["enable_sentiment_analysis"].get(),
            "confidence_threshold": self.vars["confidence_threshold"].get(),
            "local_mode": self.vars["local_mode"].get()
        }
        
        # Text processing settings
        default_filler_words = ["um", "uh", "er", "ah", "like", "you know"]
        custom_words = [w.strip() for w in self.vars["custom_filler_words"].get().split(",") if w.strip()]
        all_filler_words = default_filler_words + custom_words
        
        config["text_processing"] = {
            "remove_filler_words": self.vars["remove_filler_words"].get(),
            "auto_punctuation": self.vars["auto_punctuation"].get(),
            "auto_capitalization": self.vars["auto_capitalization"].get(),
            "trim_whitespace": self.vars["trim_whitespace"].get(),
            "filler_words": all_filler_words
        }
        
        # UI settings
        config["ui"] = {
            "show_status_window": self.vars["show_status_window"].get(),
            "status_window_position": self.vars["status_window_position"].get(),
            "show_notifications": self.vars["show_notifications"].get(),
            "minimize_to_tray": self.vars["minimize_to_tray"].get(),
            "theme": self.vars["theme"].get()
        }
        
        # System settings
        config["system"] = {
            "paste_mode": self.vars["paste_mode"].get(),
            "typing_speed": self.vars["typing_speed"].get(),
            "focus_delay_ms": self.vars["focus_delay_ms"].get()
        }
        
        # Logging settings
        config["logging"] = {
            "level": self.vars["log_level"].get(),
            "file_logging": self.vars["file_logging"].get()
        }
        
        return config
    
    def _ok(self):
        """Apply settings and close."""
        self._apply_settings()
        self.root.destroy()
    
    def _cancel(self):
        """Cancel changes and close."""
        self.root.destroy()
    
    def _reset_to_defaults(self):
        """Reset all settings to defaults."""
        if messagebox.askyesno("Reset Settings", "Reset all settings to defaults?"):
            # Load default config and refresh UI
            from main import VoiceToTextApp
            app = VoiceToTextApp()
            self.config = app.get_default_config()
            self._load_settings()
    
    def _center_window(self):
        """Center the window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    # Placeholder methods for button callbacks
    def _detect_hotkey(self):
        """Detect hotkey by listening for key presses."""
        messagebox.showinfo("Detect Hotkey", "Hotkey detection not yet implemented")
    
    def _test_hotkey(self):
        """Test the current hotkey."""
        hotkey = self.vars["hotkey_combination"].get()
        messagebox.showinfo("Test Hotkey", f"Testing hotkey: {hotkey}")
    
    def _set_hotkey(self, hotkey: str):
        """Set a specific hotkey."""
        self.vars["hotkey_combination"].set(hotkey)
    
    def _test_microphone(self):
        """Test microphone functionality."""
        messagebox.showinfo("Test Microphone", "Microphone test not yet implemented")
    
    def _manage_models(self):
        """Open model management dialog."""
        messagebox.showinfo("Model Management", "Model management not yet implemented")
    
    def _export_settings(self):
        """Export settings to file."""
        filename = filedialog.asksaveasfilename(
            title="Export Settings",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                config = self._build_config_from_ui()
                with open(filename, 'w') as f:
                    json.dump(config, f, indent=2)
                messagebox.showinfo("Export", f"Settings exported to {filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export settings: {e}")
    
    def _import_settings(self):
        """Import settings from file."""
        filename = filedialog.askopenfilename(
            title="Import Settings",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    imported_config = json.load(f)
                
                self.config = imported_config
                self._load_settings()
                messagebox.showinfo("Import", f"Settings imported from {filename}")
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import settings: {e}")
    
    def _open_config_folder(self):
        """Open the configuration folder."""
        import subprocess
        import platform
        
        config_path = Path("config").absolute()
        
        try:
            if platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(config_path)])
            elif platform.system() == "Windows":
                subprocess.run(["explorer", str(config_path)])
            else:  # Linux
                subprocess.run(["xdg-open", str(config_path)])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open config folder: {e}")


def show_settings(config: Dict[str, Any], parent: Optional[tk.Tk] = None) -> Optional[Dict[str, Any]]:
    """Show settings dialog and return updated config."""
    result = {"config": None}
    
    def on_config_changed(new_config: Dict[str, Any]):
        result["config"] = new_config
    
    settings_panel = SettingsPanel(config, on_config_changed)
    settings_panel.show(parent)
    
    return result["config"]
