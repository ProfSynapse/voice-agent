"""
Display UI Components Module

This module provides display UI components for the voice agent application.
"""

from typing import Dict, List, Optional, Any, Callable

from src.ui.components.base import UIComponent


class Text(UIComponent):
    """Text component for displaying text."""
    
    def __init__(
        self, 
        id: str, 
        text: str,
        variant: str = "body1",
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a text component.
        
        Args:
            id: Component ID
            text: Text content
            variant: Text variant (e.g., body1, h1, h2)
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.text = text
        self.variant = variant
        
    def render(self) -> Dict[str, Any]:
        """
        Render the text component as a dictionary.
        
        Returns:
            Text component representation as a dictionary
        """
        result = super().render()
        result.update({
            "text": self.text,
            "variant": self.variant
        })
        return result


class Icon(UIComponent):
    """Icon component for displaying icons."""
    
    def __init__(
        self, 
        id: str, 
        name: str,
        size: str = "medium",
        color: str = "inherit",
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize an icon component.
        
        Args:
            id: Component ID
            name: Icon name
            size: Icon size (small, medium, large)
            color: Icon color
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.name = name
        self.size = size
        self.color = color
        
    def render(self) -> Dict[str, Any]:
        """
        Render the icon component as a dictionary.
        
        Returns:
            Icon component representation as a dictionary
        """
        result = super().render()
        result.update({
            "name": self.name,
            "size": self.size,
            "color": self.color
        })
        return result


class Badge(UIComponent):
    """Badge component for displaying a badge."""
    
    def __init__(
        self, 
        id: str, 
        content: str,
        color: str = "primary",
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a badge component.
        
        Args:
            id: Component ID
            content: Badge content
            color: Badge color
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.content = content
        self.color = color
        
    def render(self) -> Dict[str, Any]:
        """
        Render the badge component as a dictionary.
        
        Returns:
            Badge component representation as a dictionary
        """
        result = super().render()
        result.update({
            "content": self.content,
            "color": self.color
        })
        return result


class Avatar(UIComponent):
    """Avatar component for displaying a user avatar."""
    
    def __init__(
        self, 
        id: str, 
        src: Optional[str] = None,
        alt: str = "",
        size: str = "medium",
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize an avatar component.
        
        Args:
            id: Component ID
            src: Image source URL
            alt: Alternative text
            size: Avatar size (small, medium, large)
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.src = src
        self.alt = alt
        self.size = size
        
    def render(self) -> Dict[str, Any]:
        """
        Render the avatar component as a dictionary.
        
        Returns:
            Avatar component representation as a dictionary
        """
        result = super().render()
        result.update({
            "src": self.src,
            "alt": self.alt,
            "size": self.size
        })
        return result