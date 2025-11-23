"""
UI Components for Voice-to-Text Application
"""

from .status_window import StatusWindow, MinimalStatusWindow
from .settings_panel import SettingsPanel, show_settings

__all__ = [
    'StatusWindow',
    'MinimalStatusWindow', 
    'SettingsPanel',
    'show_settings'
]
