"""
Text Injection System
Handles injecting transcribed text into the currently active application.
"""

import logging
import time
import subprocess
import platform
from typing import Dict, Any, Optional
from pynput.keyboard import Controller as KeyboardController
from pynput.mouse import Controller as MouseController
import pyperclip


class TextInjector:
    """Handles injecting text into active applications."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize text injector with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Controllers
        self.keyboard = KeyboardController()
        self.mouse = MouseController()
        
        # Settings
        self.typing_speed = config.get("typing_speed", 0)  # 0 = instant
        self.paste_mode = config.get("paste_mode", True)  # Use clipboard by default
        self.focus_delay = config.get("focus_delay_ms", 100) / 1000  # Convert to seconds
        self.retry_attempts = config.get("retry_attempts", 3)
        
        # Platform detection
        self.platform = platform.system().lower()
        
        self.logger.info(f"Text injector initialized for {self.platform}")
    
    def inject_text(self, text: str) -> bool:
        """
        Inject text into the currently focused application.
        
        Args:
            text: Text to inject
            
        Returns:
            True if successful, False otherwise
        """
        if not text.strip():
            return True
        
        # Clean up the text
        cleaned_text = self.clean_text(text)
        
        self.logger.info(f"Injecting text: {cleaned_text[:50]}...")
        
        # Try injection with retries
        for attempt in range(self.retry_attempts):
            try:
                if self.paste_mode:
                    success = self._inject_via_clipboard(cleaned_text)
                else:
                    success = self._inject_via_typing(cleaned_text)
                
                if success:
                    self.logger.info("Text injection successful")
                    return True
                
                self.logger.warning(f"Text injection attempt {attempt + 1} failed")
                time.sleep(0.1)  # Brief delay before retry
                
            except Exception as e:
                self.logger.error(f"Text injection error (attempt {attempt + 1}): {e}")
                time.sleep(0.1)
        
        self.logger.error("All text injection attempts failed")
        return False
    
    def clean_text(self, text: str) -> str:
        """
        Clean and process text before injection.
        
        Args:
            text: Raw text from transcription
            
        Returns:
            Cleaned text ready for injection
        """
        # Remove extra whitespace
        if self.config.get("trim_whitespace", True):
            text = text.strip()
        
        # Remove filler words if enabled
        if self.config.get("remove_filler_words", True):
            filler_words = self.config.get("filler_words", [
                "um", "uh", "er", "ah", "like", "you know"
            ])
            
            words = text.split()
            cleaned_words = []
            
            for word in words:
                # Remove punctuation for comparison
                clean_word = word.lower().strip('.,!?;:')
                if clean_word not in filler_words:
                    cleaned_words.append(word)
            
            text = ' '.join(cleaned_words)
        
        # Auto-capitalization
        if self.config.get("auto_capitalization", True):
            # Capitalize first letter
            if text:
                text = text[0].upper() + text[1:]
            
            # Capitalize after sentence endings
            import re
            text = re.sub(r'([.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)
        
        # Auto-punctuation (basic)
        if self.config.get("auto_punctuation", True):
            # Add period if text doesn't end with punctuation
            if text and text[-1] not in '.!?':
                text += '.'
        
        return text
    
    def _inject_via_clipboard(self, text: str) -> bool:
        """
        Inject text using clipboard and paste.
        
        Args:
            text: Text to inject
            
        Returns:
            True if successful
        """
        try:
            # Save current clipboard content
            original_clipboard = None
            try:
                original_clipboard = pyperclip.paste()
            except:
                pass  # Clipboard might be empty or inaccessible
            
            # Set text to clipboard
            pyperclip.copy(text)
            
            # Small delay to ensure clipboard is set
            time.sleep(0.05)
            
            # Paste using platform-specific shortcut
            if self.platform == "darwin":  # macOS
                self.keyboard.press('cmd')
                self.keyboard.press('v')
                self.keyboard.release('v')
                self.keyboard.release('cmd')
            else:  # Windows/Linux
                self.keyboard.press('ctrl')
                self.keyboard.press('v')
                self.keyboard.release('v')
                self.keyboard.release('ctrl')
            
            # Small delay for paste to complete
            time.sleep(0.1)
            
            # Restore original clipboard content
            if original_clipboard is not None:
                try:
                    pyperclip.copy(original_clipboard)
                except:
                    pass  # Don't fail if we can't restore clipboard
            
            return True
            
        except Exception as e:
            self.logger.error(f"Clipboard injection failed: {e}")
            return False
    
    def _inject_via_typing(self, text: str) -> bool:
        """
        Inject text by simulating typing.
        
        Args:
            text: Text to inject
            
        Returns:
            True if successful
        """
        try:
            # Add delay before starting to type
            time.sleep(self.focus_delay)
            
            # Type each character
            for char in text:
                self.keyboard.type(char)
                
                # Add delay between characters if specified
                if self.typing_speed > 0:
                    time.sleep(self.typing_speed / 1000)  # Convert ms to seconds
            
            return True
            
        except Exception as e:
            self.logger.error(f"Typing injection failed: {e}")
            return False
    
    def get_active_application(self) -> Optional[str]:
        """
        Get the name of the currently active application.
        
        Returns:
            Application name or None if unable to determine
        """
        try:
            if self.platform == "darwin":  # macOS
                script = '''
                tell application "System Events"
                    name of first application process whose frontmost is true
                end tell
                '''
                result = subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                if result.returncode == 0:
                    return result.stdout.strip()
            
            elif self.platform == "windows":
                # Windows implementation would go here
                import win32gui
                window = win32gui.GetForegroundWindow()
                return win32gui.GetWindowText(window)
            
        except Exception as e:
            self.logger.debug(f"Could not get active application: {e}")
        
        return None
    
    def is_text_field_active(self) -> bool:
        """
        Check if a text field is currently active/focused.
        
        Returns:
            True if a text field appears to be active
        """
        # This is a heuristic - we'll assume if we can inject text,
        # then a text field is probably active
        try:
            # Try to get current selection (if any)
            if self.platform == "darwin":  # macOS
                # Try to copy current selection to see if text field is active
                original_clipboard = None
                try:
                    original_clipboard = pyperclip.paste()
                except:
                    pass
                
                # Try to copy (Cmd+C)
                self.keyboard.press('cmd')
                self.keyboard.press('c')
                self.keyboard.release('c')
                self.keyboard.release('cmd')
                
                time.sleep(0.05)
                
                # Check if clipboard changed (indicating text was selected/copied)
                try:
                    new_clipboard = pyperclip.paste()
                    text_field_active = new_clipboard != original_clipboard
                    
                    # Restore original clipboard
                    if original_clipboard is not None:
                        pyperclip.copy(original_clipboard)
                    
                    return text_field_active
                    
                except:
                    return True  # Assume text field is active if we can't determine
            
        except Exception as e:
            self.logger.debug(f"Could not determine text field status: {e}")
        
        # Default to True - assume text field is active
        return True
    
    def focus_text_field(self) -> bool:
        """
        Try to focus a text field in the active application.
        
        Returns:
            True if successful or if already focused
        """
        try:
            # Click at current mouse position to ensure focus
            current_pos = self.mouse.position
            self.mouse.click('left', 1)
            
            # Small delay for focus to take effect
            time.sleep(self.focus_delay)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Could not focus text field: {e}")
            return False


class AccessibilityChecker:
    """Check and request accessibility permissions on macOS."""
    
    @staticmethod
    def check_accessibility_permissions() -> bool:
        """
        Check if accessibility permissions are granted.
        
        Returns:
            True if permissions are granted
        """
        if platform.system().lower() != "darwin":
            return True  # Not needed on non-macOS systems
        
        try:
            # Try to create a keyboard controller and use it
            keyboard = KeyboardController()
            
            # Try a harmless operation
            # If this fails, we likely don't have accessibility permissions
            keyboard.press('shift')
            keyboard.release('shift')
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def request_accessibility_permissions():
        """Request accessibility permissions from the user."""
        if platform.system().lower() != "darwin":
            return
        
        try:
            # Open System Preferences to Privacy & Security
            subprocess.run([
                "open", 
                "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
            ])
            
            print("\n" + "="*60)
            print("ACCESSIBILITY PERMISSIONS REQUIRED")
            print("="*60)
            print("To inject text into applications, this app needs")
            print("accessibility permissions.")
            print("")
            print("Steps:")
            print("1. System Preferences should have opened")
            print("2. Go to Privacy & Security > Accessibility")
            print("3. Click the lock icon and enter your password")
            print("4. Find 'Python' or 'Terminal' in the list")
            print("5. Check the box next to it")
            print("6. Restart this application")
            print("="*60)
            
        except Exception as e:
            print(f"Could not open System Preferences: {e}")
            print("Please manually grant accessibility permissions:")
            print("System Preferences > Privacy & Security > Accessibility")


# Utility functions for text processing
def remove_filler_words(text: str, filler_words: list = None) -> str:
    """Remove common filler words from text."""
    if filler_words is None:
        filler_words = ["um", "uh", "er", "ah", "like", "you know", "so"]
    
    words = text.split()
    cleaned_words = []
    
    for word in words:
        clean_word = word.lower().strip('.,!?;:')
        if clean_word not in filler_words:
            cleaned_words.append(word)
    
    return ' '.join(cleaned_words)


def add_punctuation(text: str) -> str:
    """Add basic punctuation to text."""
    if not text:
        return text
    
    # Add period if no ending punctuation
    if text[-1] not in '.!?':
        text += '.'
    
    return text


def capitalize_sentences(text: str) -> str:
    """Capitalize the first letter of sentences."""
    if not text:
        return text
    
    # Capitalize first letter
    text = text[0].upper() + text[1:]
    
    # Capitalize after sentence endings
    import re
    text = re.sub(r'([.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)
    
    return text
