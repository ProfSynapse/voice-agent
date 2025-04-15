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
        
    def add_child(self, child: UIComponent) -> 'Container':
        """
        Add a child component to the container.
        
        Args:
            child: Child component to add
            
        Returns:
            Self for chaining
        """
        if not hasattr(self, 'children'):
            self.children = []
        self.children.append(child)
        return self
    
    def add_children(self, children: List[UIComponent]) -> 'Container':
        """
        Add multiple child components to the container.
        
        Args:
            children: Child components to add
            
        Returns:
            Self for chaining
        """
        for child in children:
            self.add_child(child)
        return self
    
    def render(self) -> str:
        """
        Render the container as a string.
        
        Returns:
            Container representation as a string
        """
        children_html = ""
        if hasattr(self, 'children'):
            children_html = "".join([child.render() for child in self.children])
            
        return f"""
        <div id="{self.id}" class="container {self.direction}" style="align-items: {self.align}; justify-content: {self.justify}">
            {children_html}
        </div>
        """


class Card(UIComponent):
    """Card component for displaying content in a card."""
    
    def __init__(
        self,
        id: str = "card",
        title: str = "",
        content: str = "",
        footer: str = "",
        elevation: int = 1,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a card component.
        
        Args:
            id: Component ID
            title: Card title
            content: Card content
            footer: Card footer
            elevation: Card elevation (shadow level)
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.title = title
        self.content = content
        self.footer = footer
        self.elevation = elevation
        
    def render(self) -> str:
        """
        Render the card component as a string.
        
        Returns:
            Card component representation as a string
        """
        title_html = f'<div class="card-title">{self.title}</div>' if self.title else ""
        footer_html = f'<div class="card-footer">{self.footer}</div>' if self.footer else ""
        
        return f"""
        <div id="{self.id}" class="card elevation-{self.elevation}">
            {title_html}
            <div class="card-content">{self.content}</div>
            {footer_html}
        </div>
        """


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
        
    def render(self) -> str:
        """
        Render the divider component as a string.
        
        Returns:
            Divider component representation as a string
        """
        return f'<div id="{self.id}" class="divider {self.orientation}"></div>'