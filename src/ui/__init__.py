"""
UI Module

This module provides UI components for the voice agent application.
"""

from src.ui.components import (
    UIComponent,
    Container,
    Text,
    Button,
    Icon,
    IconButton,
    Input,
    Card,
    List,
    ListItem,
    Divider,
    CircularProgress,
    Badge,
    Avatar,
    Tabs,
    Dialog,
    Snackbar,
    Menu
)

from src.ui.voice_components import (
    AudioWaveform,
    VoiceButton,
    ConversationBubble,
    ConversationView,
    AudioPlayer,
    VoiceControls,
    ConversationList,
    SystemPromptSelector,
    VoiceSettings
)

__all__ = [
    # Base components
    'UIComponent',
    'Container',
    'Text',
    'Button',
    'Icon',
    'IconButton',
    'Input',
    'Card',
    'List',
    'ListItem',
    'Divider',
    'CircularProgress',
    'Badge',
    'Avatar',
    'Tabs',
    'Dialog',
    'Snackbar',
    'Menu',
    
    # Voice-specific components
    'AudioWaveform',
    'VoiceButton',
    'ConversationBubble',
    'ConversationView',
    'AudioPlayer',
    'VoiceControls',
    'ConversationList',
    'SystemPromptSelector',
    'VoiceSettings'
]