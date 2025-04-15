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
        
    def render(self) -> str:
        """
        Render the text component as a string.
        
        Returns:
            Text component representation as a string
        """
        tag = "p"
        if self.variant.startswith("h") and len(self.variant) == 2 and self.variant[1].isdigit():
            tag = self.variant
            
        return f'<{tag} id="{self.id}" class="text {self.variant}">{self.text}</{tag}>'


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
        
    def render(self) -> str:
        """
        Render the icon component as a string.
        
        Returns:
            Icon component representation as a string
        """
        return f'<span id="{self.id}" class="icon {self.name} {self.size} {self.color}"></span>'


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
        
    def render(self) -> str:
        """
        Render the badge component as a string.
        
        Returns:
            Badge component representation as a string
        """
        return f'<span id="{self.id}" class="badge {self.color}">{self.content}</span>'


class Avatar(UIComponent):
    """Avatar component for displaying a user avatar."""
    
    def __init__(
        self,
        id: str = "avatar",
        name: str = "",
        image_url: Optional[str] = None,
        size: str = "medium",
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize an avatar component.
        
        Args:
            id: Component ID
            name: User name (used for fallback and alt text)
            image_url: Image source URL
            size: Avatar size (small, medium, large)
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.name = name
        self.image_url = image_url
        self.size = size
    
    def get_initials(self) -> str:
        """Get initials from name."""
        if not self.name:
            return "?"
        
        parts = self.name.split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[-1][0]}".upper()
        elif len(parts) == 1 and parts[0]:
            return parts[0][0].upper()
        else:
            return "?"
        
    def render(self) -> str:
        """
        Render the avatar component as a string.
        
        Returns:
            Avatar component representation as a string
        """
        if self.image_url:
            return f'<div id="{self.id}" class="avatar {self.size}" title="{self.name}"><img src="{self.image_url}" alt="{self.name}" /></div>'
        else:
            initials = self.get_initials()
            return f'<div id="{self.id}" class="avatar {self.size} fallback" title="{self.name}" data-name="{self.name}">{initials}</div>'