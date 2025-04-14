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
        
    def render(self) -> Dict[str, Any]:
        """
        Render the circular progress component as a dictionary.
        
        Returns:
            Circular progress component representation as a dictionary
        """
        result = super().render()
        result.update({
            "size": self.size,
            "color": self.color,
            "value": self.value
        })
        return result


class Dialog(UIComponent):
    """Dialog component for displaying a dialog."""
    
    def __init__(
        self,
        id: str,
        title: str,
        open: bool = False,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a dialog component.
        
        Args:
            id: Component ID
            title: Dialog title
            open: Whether the dialog is open
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.title = title
        self.open = open
        
    def render(self) -> Dict[str, Any]:
        """
        Render the dialog component as a dictionary.
        
        Returns:
            Dialog component representation as a dictionary
        """
        result = super().render()
        result.update({
            "title": self.title,
            "open": self.open
        })
        return result


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
        
    def render(self) -> Dict[str, Any]:
        """
        Render the snackbar component as a dictionary.
        
        Returns:
            Snackbar component representation as a dictionary
        """
        result = super().render()
        result.update({
            "message": self.message,
            "open": self.open,
            "severity": self.severity,
            "duration": self.duration
        })
        return result