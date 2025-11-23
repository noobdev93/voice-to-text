"""
Status Window UI
Shows recording status, transcription preview, and volume levels.
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from typing import Dict, Any, Optional
import logging


class StatusWindow:
    """Simple status window to show recording state and transcription."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize status window with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Window settings
        self.position = config.get("status_window_position", "top-right")
        self.theme = config.get("theme", "system")
        
        # UI elements
        self.root: Optional[tk.Tk] = None
        self.status_label: Optional[tk.Label] = None
        self.transcription_label: Optional[tk.Label] = None
        self.volume_bar: Optional[ttk.Progressbar] = None
        self.time_label: Optional[tk.Label] = None
        
        # State
        self.is_visible = False
        self.current_status = "idle"
        self.current_transcription = ""
        self.recording_start_time = 0
        self.volume_level = 0.0
        
        # Threading
        self.ui_thread: Optional[threading.Thread] = None
        self.update_timer: Optional[str] = None
        
        # Colors and styling
        self.colors = self._get_theme_colors()
        
    def _get_theme_colors(self) -> Dict[str, str]:
        """Get colors based on theme."""
        if self.theme == "dark":
            return {
                "bg": "#2b2b2b",
                "fg": "#ffffff",
                "accent": "#007acc",
                "recording": "#ff4444",
                "idle": "#44ff44",
                "error": "#ff8844"
            }
        else:  # light theme
            return {
                "bg": "#f0f0f0",
                "fg": "#000000",
                "accent": "#0078d4",
                "recording": "#d13438",
                "idle": "#107c10",
                "error": "#ff8c00"
            }
    
    def show(self):
        """Show the status window."""
        if self.is_visible:
            return
        
        # Create UI in separate thread
        self.ui_thread = threading.Thread(target=self._create_ui, daemon=True)
        self.ui_thread.start()
        
        self.is_visible = True
        self.logger.info("Status window shown")
    
    def hide(self):
        """Hide the status window."""
        if not self.is_visible or not self.root:
            return
        
        try:
            self.root.withdraw()
            self.is_visible = False
            self.logger.info("Status window hidden")
        except Exception as e:
            self.logger.error(f"Error hiding status window: {e}")
    
    def close(self):
        """Close the status window."""
        if not self.root:
            return
        
        try:
            if self.update_timer:
                self.root.after_cancel(self.update_timer)
            
            self.root.quit()
            self.root.destroy()
            self.root = None
            self.is_visible = False
            
            self.logger.info("Status window closed")
            
        except Exception as e:
            self.logger.error(f"Error closing status window: {e}")
    
    def _create_ui(self):
        """Create the UI elements."""
        try:
            # Create main window
            self.root = tk.Tk()
            self.root.title("Voice-to-Text")
            self.root.configure(bg=self.colors["bg"])
            
            # Window properties
            self.root.attributes('-topmost', True)  # Always on top
            self.root.resizable(False, False)
            
            # Remove window decorations for minimal look
            self.root.overrideredirect(True)
            
            # Create main frame
            main_frame = tk.Frame(
                self.root,
                bg=self.colors["bg"],
                relief="raised",
                bd=1
            )
            main_frame.pack(padx=5, pady=5, fill="both", expand=True)
            
            # Status indicator
            self.status_label = tk.Label(
                main_frame,
                text="● Idle",
                font=("Arial", 12, "bold"),
                fg=self.colors["idle"],
                bg=self.colors["bg"]
            )
            self.status_label.pack(pady=(5, 2))
            
            # Volume bar
            volume_frame = tk.Frame(main_frame, bg=self.colors["bg"])
            volume_frame.pack(fill="x", padx=10, pady=2)
            
            tk.Label(
                volume_frame,
                text="🎤",
                font=("Arial", 10),
                fg=self.colors["fg"],
                bg=self.colors["bg"]
            ).pack(side="left")
            
            self.volume_bar = ttk.Progressbar(
                volume_frame,
                length=100,
                mode='determinate',
                style="Volume.Horizontal.TProgressbar"
            )
            self.volume_bar.pack(side="left", padx=(5, 0), fill="x", expand=True)
            
            # Time label
            self.time_label = tk.Label(
                main_frame,
                text="00:00",
                font=("Arial", 10),
                fg=self.colors["fg"],
                bg=self.colors["bg"]
            )
            self.time_label.pack(pady=2)
            
            # Transcription preview
            self.transcription_label = tk.Label(
                main_frame,
                text="Press hotkey to start recording...",
                font=("Arial", 9),
                fg=self.colors["fg"],
                bg=self.colors["bg"],
                wraplength=250,
                justify="left",
                height=3
            )
            self.transcription_label.pack(pady=(2, 5), padx=10, fill="x")
            
            # Position window
            self._position_window()
            
            # Configure styles
            self._configure_styles()
            
            # Bind events
            self._bind_events()
            
            # Start update loop
            self._start_update_loop()
            
            # Start main loop
            self.root.mainloop()
            
        except Exception as e:
            self.logger.error(f"Error creating status window: {e}")
    
    def _position_window(self):
        """Position the window based on configuration."""
        if not self.root:
            return
        
        # Update window to get accurate size
        self.root.update_idletasks()
        
        # Get window size
        width = self.root.winfo_reqwidth()
        height = self.root.winfo_reqheight()
        
        # Get screen size
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position based on preference
        if self.position == "top-right":
            x = screen_width - width - 20
            y = 20
        elif self.position == "top-left":
            x = 20
            y = 20
        elif self.position == "bottom-right":
            x = screen_width - width - 20
            y = screen_height - height - 100
        elif self.position == "bottom-left":
            x = 20
            y = screen_height - height - 100
        else:  # center
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def _configure_styles(self):
        """Configure ttk styles."""
        try:
            style = ttk.Style()
            
            # Volume bar style
            style.configure(
                "Volume.Horizontal.TProgressbar",
                background=self.colors["accent"],
                troughcolor=self.colors["bg"],
                borderwidth=1,
                lightcolor=self.colors["accent"],
                darkcolor=self.colors["accent"]
            )
            
        except Exception as e:
            self.logger.debug(f"Could not configure styles: {e}")
    
    def _bind_events(self):
        """Bind window events."""
        if not self.root:
            return
        
        # Allow dragging the window
        self.root.bind("<Button-1>", self._start_drag)
        self.root.bind("<B1-Motion>", self._drag_window)
        
        # Double-click to hide/show transcription
        self.root.bind("<Double-Button-1>", self._toggle_transcription)
    
    def _start_drag(self, event):
        """Start dragging the window."""
        self.root.start_x = event.x
        self.root.start_y = event.y
    
    def _drag_window(self, event):
        """Drag the window."""
        x = self.root.winfo_x() + event.x - self.root.start_x
        y = self.root.winfo_y() + event.y - self.root.start_y
        self.root.geometry(f"+{x}+{y}")
    
    def _toggle_transcription(self, event):
        """Toggle transcription visibility."""
        if self.transcription_label:
            current_height = self.transcription_label.cget("height")
            new_height = 1 if current_height > 1 else 3
            self.transcription_label.configure(height=new_height)
    
    def _start_update_loop(self):
        """Start the UI update loop."""
        self._update_ui()
    
    def _update_ui(self):
        """Update UI elements."""
        try:
            if not self.root:
                return
            
            # Update time if recording
            if self.current_status == "recording" and self.recording_start_time > 0:
                elapsed = time.time() - self.recording_start_time
                minutes = int(elapsed // 60)
                seconds = int(elapsed % 60)
                time_text = f"{minutes:02d}:{seconds:02d}"
                
                if self.time_label:
                    self.time_label.configure(text=time_text)
            
            # Update volume bar
            if self.volume_bar:
                self.volume_bar['value'] = self.volume_level * 100
            
            # Schedule next update
            self.update_timer = self.root.after(100, self._update_ui)
            
        except Exception as e:
            self.logger.error(f"Error updating UI: {e}")
    
    def set_status(self, status: str):
        """Set the current status."""
        self.current_status = status
        
        if not self.status_label:
            return
        
        # Update status text and color
        status_map = {
            "idle": ("● Idle", self.colors["idle"]),
            "recording": ("🔴 Recording", self.colors["recording"]),
            "processing": ("⏳ Processing", self.colors["accent"]),
            "error": ("⚠️ Error", self.colors["error"])
        }
        
        text, color = status_map.get(status, ("● Unknown", self.colors["fg"]))
        
        try:
            self.status_label.configure(text=text, fg=color)
            
            # Set recording start time
            if status == "recording":
                self.recording_start_time = time.time()
            elif status != "recording":
                self.recording_start_time = 0
                if self.time_label:
                    self.time_label.configure(text="00:00")
            
        except Exception as e:
            self.logger.error(f"Error setting status: {e}")
    
    def set_transcription(self, text: str):
        """Set the transcription text."""
        self.current_transcription = text
        
        if not self.transcription_label:
            return
        
        try:
            # Limit text length for display
            display_text = text[:150]
            if len(text) > 150:
                display_text += "..."
            
            # Show "Listening..." if empty and recording
            if not display_text and self.current_status == "recording":
                display_text = "Listening..."
            elif not display_text:
                display_text = "Press hotkey to start recording..."
            
            self.transcription_label.configure(text=display_text)
            
        except Exception as e:
            self.logger.error(f"Error setting transcription: {e}")
    
    def set_volume(self, volume: float):
        """Set the volume level (0.0 to 1.0)."""
        self.volume_level = max(0.0, min(1.0, volume))
    
    def flash_error(self, message: str = "Error occurred"):
        """Flash an error message briefly."""
        if not self.transcription_label:
            return
        
        try:
            # Save current text
            original_text = self.transcription_label.cget("text")
            original_color = self.transcription_label.cget("fg")
            
            # Show error message
            self.transcription_label.configure(
                text=message,
                fg=self.colors["error"]
            )
            
            # Restore after 2 seconds
            self.root.after(2000, lambda: self.transcription_label.configure(
                text=original_text,
                fg=original_color
            ))
            
        except Exception as e:
            self.logger.error(f"Error flashing error message: {e}")


class MinimalStatusWindow:
    """Ultra-minimal status indicator for users who prefer less UI."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize minimal status window."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.root: Optional[tk.Tk] = None
        self.status_indicator: Optional[tk.Label] = None
        self.is_visible = False
        
    def show(self):
        """Show minimal status indicator."""
        if self.is_visible:
            return
        
        threading.Thread(target=self._create_minimal_ui, daemon=True).start()
        self.is_visible = True
    
    def _create_minimal_ui(self):
        """Create minimal UI - just a small colored dot."""
        try:
            self.root = tk.Tk()
            self.root.title("Voice Status")
            
            # Make it tiny and borderless
            self.root.overrideredirect(True)
            self.root.attributes('-topmost', True)
            
            # Just a colored circle
            self.status_indicator = tk.Label(
                self.root,
                text="●",
                font=("Arial", 16),
                fg="#44ff44",  # Green for idle
                bg="#000000"
            )
            self.status_indicator.pack()
            
            # Position in corner
            self.root.geometry("30x30+20+20")
            
            self.root.mainloop()
            
        except Exception as e:
            self.logger.error(f"Error creating minimal status window: {e}")
    
    def set_status(self, status: str):
        """Set status color."""
        if not self.status_indicator:
            return
        
        colors = {
            "idle": "#44ff44",      # Green
            "recording": "#ff4444", # Red
            "processing": "#ffaa44", # Orange
            "error": "#ff8844"      # Orange-red
        }
        
        color = colors.get(status, "#ffffff")
        
        try:
            self.status_indicator.configure(fg=color)
        except Exception as e:
            self.logger.error(f"Error setting minimal status: {e}")
    
    def close(self):
        """Close minimal status window."""
        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
                self.root = None
                self.is_visible = False
            except Exception as e:
                self.logger.error(f"Error closing minimal status window: {e}")
