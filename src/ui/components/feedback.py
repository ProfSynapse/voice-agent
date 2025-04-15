"""
Feedback UI Components Module

This module provides feedback UI components for the voice agent application.
"""

from typing import Dict, List, Optional, Any, Callable

from src.ui.components.base import UIComponent


class CircularProgress(UIComponent):
    """Circular progress component for indicating loading."""
    
    def __init__(
        self,
        id: str,
        size: str = "medium",
        color: str = "primary",
        value: Optional[float] = None,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a circular progress component.
        
        Args:
            id: Component ID
            size: Progress size (small, medium, large)
            color: Progress color
            value: Optional value (0-100) for determinate progress
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.size = size
        self.color = color
        self.value = value
        
    def render(self) -> str:
        """
        Render the circular progress component as a string.
        
        Returns:
            Circular progress component representation as a string
        """
        value_attr = f'value="{self.value}"' if self.value is not None else ""
        
        return f'<div id="{self.id}" class="circular-progress {self.size} {self.color}" {value_attr}></div>'


class Dialog(UIComponent):
    """Dialog component for displaying a dialog."""
    
    def __init__(
        self,
        id: str = "dialog",
        title: str = "",
        content: str = "",
        is_open: bool = False,
        on_close: Optional[Callable[[], None]] = None,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a dialog component.
        
        Args:
            id: Component ID
            title: Dialog title
            content: Dialog content
            is_open: Whether the dialog is open
            on_close: Close event handler
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.title = title
        self.content = content
        self.is_open = is_open
        self.on_close = on_close
    
    def handle_close(self):
        """Handle dialog close event."""
        self.is_open = False
        if self.on_close:
            self.on_close()
        
    def render(self) -> str:
        """
        Render the dialog component as a string.
        
        Returns:
            Dialog component representation as a string
        """
        display = "block" if self.is_open else "none"
        open_class = "open" if self.is_open else "closed"
        
        return f"""
        <div id="{self.id}" class="dialog {open_class}" style="display: {display}">
            <div class="dialog-content">
                <div class="dialog-header">
                    <h2>{self.title}</h2>
                    <button class="close-button" onclick="handleClose()">×</button>
                </div>
                <div class="dialog-body">
                    {self.content}
                </div>
            </div>
        </div>
        """


class Snackbar(UIComponent):
    """Snackbar component for displaying notifications."""
    
    def __init__(
        self,
        id: str,
        message: str,
        open: bool = False,
        severity: str = "info",
        duration: int = 5000,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a snackbar component.
        
        Args:
            id: Component ID
            message: Snackbar message
            open: Whether the snackbar is open
            severity: Message severity (info, success, warning, error)
            duration: Duration in milliseconds
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.message = message
        self.open = open
        self.severity = severity
        self.duration = duration
        
    def render(self) -> str:
        """
        Render the snackbar component as a string.
        
        Returns:
            Snackbar component representation as a string
        """
        display = "block" if self.open else "none"
        
        return f"""
        <div id="{self.id}" class="snackbar {self.severity}" style="display: {display}" data-duration="{self.duration}">
            <div class="snackbar-content">
                <span class="snackbar-message">{self.message}</span>
                <button class="snackbar-close">×</button>
            </div>
        </div>
        """