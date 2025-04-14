"""
Layout UI Components Module

This module provides layout UI components for the voice agent application.
"""

from typing import Dict, List, Optional, Any, Callable

from src.ui.components.base import UIComponent


class Container(UIComponent):
    """Container component for grouping other components."""
    
    def __init__(
        self, 
        id: str, 
        direction: str = "column",
        align: str = "stretch",
        justify: str = "flex-start",
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a container.
        
        Args:
            id: Component ID
            direction: Flex direction (column or row)
            align: Alignment of items
            justify: Justification of items
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.direction = direction
        self.align = align
        self.justify = justify
        
    def render(self) -> Dict[str, Any]:
        """
        Render the container as a dictionary.
        
        Returns:
            Container representation as a dictionary
        """
        result = super().render()
        result.update({
            "direction": self.direction,
            "align": self.align,
            "justify": self.justify
        })
        return result


class Card(UIComponent):
    """Card component for displaying content in a card."""
    
    def __init__(
        self, 
        id: str, 
        elevation: int = 1,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a card component.
        
        Args:
            id: Component ID
            elevation: Card elevation (shadow level)
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.elevation = elevation
        
    def render(self) -> Dict[str, Any]:
        """
        Render the card component as a dictionary.
        
        Returns:
            Card component representation as a dictionary
        """
        result = super().render()
        result.update({
            "elevation": self.elevation
        })
        return result


class Divider(UIComponent):
    """Divider component for separating content."""
    
    def __init__(
        self, 
        id: str, 
        orientation: str = "horizontal",
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a divider component.
        
        Args:
            id: Component ID
            orientation: Divider orientation (horizontal or vertical)
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.orientation = orientation
        
    def render(self) -> Dict[str, Any]:
        """
        Render the divider component as a dictionary.
        
        Returns:
            Divider component representation as a dictionary
        """
        result = super().render()
        result.update({
            "orientation": self.orientation
        })
        return result