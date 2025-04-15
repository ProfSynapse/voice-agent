"""
UI Components Package

This package provides UI components for the voice agent application.
"""
from src.ui.components.base import UIComponent, ComponentFactory
from src.ui.components.display import Text, Icon, Badge, Avatar
from src.ui.components.feedback import CircularProgress, Dialog, Snackbar
from src.ui.components.input import Button, IconButton, Input, TextField
from src.ui.components.layout import Container, Card, Divider
from src.ui.components.navigation import List, ListItem, Tabs, Menu
from src.ui.components.voice import VoiceButton, VoiceWaveform, VoiceIndicator, TranscriptDisplay
from src.ui.theme import ThemeProvider, get_theme
from src.ui.components.voice import VoiceButton, VoiceWaveform, VoiceIndicator, TranscriptDisplay
from src.ui.voice_components import MicrophoneButton, MuteButton, VoiceStatusIndicator

__all__ = [
    # Base
    'UIComponent',
    'ComponentFactory',
    
    # Display
    'Text',
    'Icon',
    'Badge',
    'Avatar',
    
    # Feedback
    'CircularProgress',
    'Dialog',
    'Snackbar',
    
    # Input
    'Button',
    'IconButton',
    'Input',
    'TextField',
    
    # Layout
    'Container',
    'Card',
    'Divider',
    
    # Navigation
    'List',
    'ListItem',
    'Tabs',
    'Menu',
    
    # Voice
    'VoiceButton',
    'VoiceWaveform',
    'VoiceIndicator',
    'TranscriptDisplay',
    'MicrophoneButton',
    'MuteButton',
    'VoiceStatusIndicator',
    
    # Theme
    'ThemeProvider',
    'get_theme'
]