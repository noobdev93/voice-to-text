"""
Global Hotkey Listener
Detects keyboard shortcuts system-wide to trigger voice recording.
"""

import logging
import threading
import time
from typing import Callable, Optional, Set, Dict, Any
from pynput import keyboard
from pynput.keyboard import Key, KeyCode


class HotkeyListener:
    """Global hotkey listener for triggering voice recording."""
    
    def __init__(self, hotkey_combination: str, callback: Callable[[], None]):
        """
        Initialize hotkey listener.
        
        Args:
            hotkey_combination: String representation of hotkey (e.g., "cmd+shift+space")
            callback: Function to call when hotkey is pressed
        """
        self.hotkey_combination = hotkey_combination
        self.callback = callback
        self.logger = logging.getLogger(__name__)
        
        # Parse hotkey combination
        self.hotkey_set = self.parse_hotkey(hotkey_combination)
        
        # State tracking
        self.pressed_keys: Set[Key] = set()
        self.listener: Optional[keyboard.Listener] = None
        self.is_running = False
        
        # Debouncing
        self.last_trigger_time = 0
        self.debounce_delay = 0.2  # 200ms debounce
        
        self.logger.info(f"Hotkey listener initialized for: {hotkey_combination}")
    
    def parse_hotkey(self, combination: str) -> Set[Key]:
        """
        Parse hotkey combination string into set of keys.
        
        Args:
            combination: String like "cmd+shift+space" or "ctrl+alt+v"
            
        Returns:
            Set of Key objects representing the combination
        """
        keys = set()
        parts = combination.lower().split('+')
        
        for part in parts:
            part = part.strip()
            
            # Modifier keys
            if part in ['cmd', 'command']:
                keys.add(Key.cmd)
            elif part in ['ctrl', 'control']:
                keys.add(Key.ctrl)
            elif part in ['alt', 'option']:
                keys.add(Key.alt)
            elif part in ['shift']:
                keys.add(Key.shift)
            elif part == 'fn':
                keys.add(Key.fn)
            
            # Special keys
            elif part == 'space':
                keys.add(Key.space)
            elif part == 'enter':
                keys.add(Key.enter)
            elif part == 'tab':
                keys.add(Key.tab)
            elif part == 'esc':
                keys.add(Key.esc)
            elif part == 'backspace':
                keys.add(Key.backspace)
            elif part == 'delete':
                keys.add(Key.delete)
            elif part in ['up', 'down', 'left', 'right']:
                keys.add(getattr(Key, part))
            elif part.startswith('f') and part[1:].isdigit():
                # Function keys (f1–f19 supported on macOS; higher numbers used for custom remaps)
                fn_num = int(part[1:])
                if 1 <= fn_num <= 19:
                    keys.add(getattr(Key, part))
            
            # Regular character keys
            elif len(part) == 1 and part.isalnum():
                keys.add(KeyCode.from_char(part))
            
            # Page up/down, home, end
            elif part in ['page_up', 'pg_up', 'pgup']:
                keys.add(Key.page_up)
            elif part in ['page_down', 'pg_down', 'pgdown']:
                keys.add(Key.page_down)
            elif part == 'home':
                keys.add(Key.home)
            elif part == 'end':
                keys.add(Key.end)
            
            else:
                self.logger.warning(f"Unknown key in hotkey combination: {part}")
        
        return keys
    
    def start(self):
        """Start listening for hotkey presses."""
        if self.is_running:
            return
        
        try:
            self.listener = keyboard.Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release
            )
            
            self.listener.start()
            self.is_running = True
            
            self.logger.info(f"Hotkey listener started for: {self.hotkey_combination}")
            
        except Exception as e:
            self.logger.error(f"Failed to start hotkey listener: {e}")
            raise
    
    def stop(self):
        """Stop listening for hotkey presses."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.listener:
            self.listener.stop()
            self.listener = None
        
        self.pressed_keys.clear()
        self.logger.info("Hotkey listener stopped")
    
    def on_key_press(self, key):
        """Handle key press events."""
        try:
            # Normalize the key
            normalized_key = self.normalize_key(key)
            if normalized_key:
                self.pressed_keys.add(normalized_key)
                
                # Check if hotkey combination is pressed
                if self.is_hotkey_pressed():
                    self.trigger_callback()
                    
        except Exception as e:
            self.logger.error(f"Error in key press handler: {e}")
    
    def on_key_release(self, key):
        """Handle key release events."""
        try:
            # Normalize the key
            normalized_key = self.normalize_key(key)
            if normalized_key and normalized_key in self.pressed_keys:
                self.pressed_keys.remove(normalized_key)
                
        except Exception as e:
            self.logger.error(f"Error in key release handler: {e}")
    
    def normalize_key(self, key) -> Optional[Key]:
        """
        Normalize key to handle platform differences.
        
        Args:
            key: Key from pynput
            
        Returns:
            Normalized key or None if not recognized
        """
        # Handle special keys
        if hasattr(key, 'name'):
            return key
        
        # Handle character keys
        if hasattr(key, 'char') and key.char:
            return KeyCode.from_char(key.char.lower())
        
        # Handle KeyCode objects
        if isinstance(key, KeyCode):
            if key.char:
                return KeyCode.from_char(key.char.lower())
            return key
        
        return key
    
    def is_hotkey_pressed(self) -> bool:
        """
        Check if the current pressed keys match the hotkey combination.
        
        Returns:
            True if hotkey combination is currently pressed
        """
        # Convert pressed keys to comparable format
        pressed_comparable = set()
        for key in self.pressed_keys:
            if hasattr(key, 'char') and key.char:
                pressed_comparable.add(KeyCode.from_char(key.char.lower()))
            else:
                pressed_comparable.add(key)
        
        # Convert hotkey set to comparable format
        hotkey_comparable = set()
        for key in self.hotkey_set:
            if hasattr(key, 'char') and key.char:
                hotkey_comparable.add(KeyCode.from_char(key.char.lower()))
            else:
                hotkey_comparable.add(key)
        
        # Check if all hotkey keys are pressed
        return hotkey_comparable.issubset(pressed_comparable)
    
    def trigger_callback(self):
        """Trigger the callback with debouncing."""
        current_time = time.time()
        
        # Debounce to prevent multiple rapid triggers
        if current_time - self.last_trigger_time < self.debounce_delay:
            return
        
        self.last_trigger_time = current_time
        
        try:
            self.logger.debug("Hotkey triggered")
            
            # Call the callback in a separate thread to avoid blocking
            threading.Thread(target=self.callback, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Error triggering callback: {e}")
    
    def update_hotkey(self, new_combination: str):
        """
        Update the hotkey combination.
        
        Args:
            new_combination: New hotkey combination string
        """
        was_running = self.is_running
        
        if was_running:
            self.stop()
        
        self.hotkey_combination = new_combination
        self.hotkey_set = self.parse_hotkey(new_combination)
        
        if was_running:
            self.start()
        
        self.logger.info(f"Hotkey updated to: {new_combination}")


class HotkeyValidator:
    """Validator for hotkey combinations."""
    
    # Reserved system shortcuts that should not be used
    RESERVED_SHORTCUTS = {
        'macos': {
            # Common Cmd-based shortcuts
            'cmd+c', 'cmd+v', 'cmd+x', 'cmd+z', 'cmd+shift+z', 'cmd+a', 'cmd+q',
            'cmd+w', 'cmd+r', 'cmd+t', 'cmd+s', 'cmd+p', 'cmd+n', 'cmd+m', 'cmd+h',
            'cmd+f', 'cmd+g', 'cmd+shift+g', 'cmd+comma',
            
            # Navigation & Control
            'cmd+left', 'cmd+right', 'cmd+up', 'cmd+down',
            'cmd+shift+left', 'cmd+shift+right', 'cmd+shift+up', 'cmd+shift+down',
            'cmd+ctrl+f', 'cmd+space', 'cmd+alt+space',
            'cmd+shift+3', 'cmd+shift+4', 'cmd+shift+5',
            'cmd+alt+esc', 'cmd+alt+d', 'cmd+delete', 'cmd+shift+delete', 'cmd+shift+q',
            
            # Browser & Editor Functions
            'cmd+b', 'cmd+i', 'cmd+u', 'cmd+shift+t', 'cmd+=', 'cmd+-',
            'cmd+alt+f', 'cmd+shift+f',
            
            # Function Key Combos
            'fn+f11', 'fn+f12'
        },
        
        'windows': {
            # Ctrl-based shortcuts
            'ctrl+c', 'ctrl+v', 'ctrl+x', 'ctrl+z', 'ctrl+y', 'ctrl+r', 'ctrl+a',
            'ctrl+f', 'ctrl+g', 'ctrl+o', 'ctrl+s', 'ctrl+p', 'ctrl+n', 'ctrl+t',
            'ctrl+w', 'ctrl+home', 'ctrl+end', 'ctrl+alt+del', 'ctrl+shift+esc',
            'ctrl+backspace', 'ctrl+delete', 'ctrl+k', 'ctrl+shift+t', 'ctrl+=', 'ctrl+-',
            
            # Alt-based shortcuts
            'alt+tab', 'alt+f4', 'alt+left', 'alt+right', 'alt+print_screen',
            
            # Function & Navigation Keys
            'f5', 'f11', 'home', 'end', 'print_screen',
            
            # Windows Key Combos
            'win+e', 'win+r', 'win+l', 'win+d', 'win+tab', 'win+i', 'win+s',
            'win+x', 'win+p', 'win+q', 'win+u', 'win+b', 'win+up', 'win+down'
        }
    }
    
    @classmethod
    def validate_hotkey(cls, combination: str, platform: str = 'macos') -> Dict[str, Any]:
        """
        Validate a hotkey combination.
        
        Args:
            combination: Hotkey combination string
            platform: Target platform ('macos' or 'windows')
            
        Returns:
            Dictionary with validation results
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Normalize combination
        normalized = combination.lower().strip()
        parts = [p.strip() for p in normalized.split('+')]
        
        # Check basic rules
        if len(parts) > 3:
            result['valid'] = False
            result['errors'].append("Hotkey cannot have more than 3 keys")
        
        # Check for modifiers
        modifiers = {'cmd', 'ctrl', 'alt', 'shift', 'fn', 'win'}
        has_modifier = any(part in modifiers for part in parts)
        
        if not has_modifier:
            # Check if it has non-alphanumeric keys
            special_keys = {'space', 'enter', 'tab', 'esc', 'backspace', 'delete',
                          'up', 'down', 'left', 'right', 'home', 'end',
                          'page_up', 'page_down',
                          'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9',
                          'f10', 'f11', 'f12', 'f13', 'f14', 'f15', 'f16', 'f17',
                          'f18', 'f19'}
            
            has_special = any(part in special_keys for part in parts)
            
            if not has_special:
                result['valid'] = False
                result['errors'].append("Hotkey must include at least one modifier or special key")
        
        # Check for reserved shortcuts
        reserved = cls.RESERVED_SHORTCUTS.get(platform, set())
        if normalized in reserved:
            result['valid'] = False
            result['errors'].append(f"This shortcut is reserved by {platform}")
        
        # Check for left+right modifier conflicts
        if 'left_ctrl' in parts and 'right_ctrl' in parts:
            result['valid'] = False
            result['errors'].append("Cannot use both left and right versions of the same modifier")
        
        if 'left_alt' in parts and 'right_alt' in parts:
            result['valid'] = False
            result['errors'].append("Cannot use both left and right versions of the same modifier")
        
        # Platform-specific recommendations
        if platform == 'macos':
            if not any(mod in parts for mod in ['cmd', 'fn', 'ctrl+opt', 'opt+cmd']):
                result['warnings'].append("For macOS, consider using Cmd, Fn, or Ctrl+Opt combinations")
        
        elif platform == 'windows':
            if not any(mod in parts for mod in ['ctrl+win', 'ctrl+alt']):
                result['warnings'].append("For Windows, consider using Ctrl+Win or Ctrl+Alt combinations")
        
        return result
    
    @classmethod
    def get_recommended_hotkeys(cls, platform: str = 'macos') -> list:
        """
        Get list of recommended hotkey combinations for platform.
        
        Args:
            platform: Target platform ('macos' or 'windows')
            
        Returns:
            List of recommended hotkey strings
        """
        if platform == 'macos':
            return [
                'fn',
                'cmd+shift+space',
                'ctrl+opt+space',
                'opt+cmd+space',
                'cmd+right',
                'opt+right'
            ]
        
        elif platform == 'windows':
            return [
                'ctrl+win+space',
                'ctrl+alt+space',
                'ctrl+right',
                'alt+right',
                'page_up',
                'ctrl+win+v'
            ]
        
        return []
