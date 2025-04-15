"""
Base UI Component Module

This module provides the base UI component class that all other UI components inherit from.
"""

from typing import Dict, Optional, Any, List
import uuid


class UIComponent:
    """Base class for all UI components."""
    
    def __init__(
        self, 
        id: str, 
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a UI component.
        
        Args:
            id: Component ID
            styles: Optional styles for the component
        """
        self.id = id
        self.styles = styles or {}
        self.children: List['UIComponent'] = []
        self.event_handlers: Dict[str, Any] = {}
        
    def add_child(self, child: 'UIComponent') -> 'UIComponent':
        """
        Add a child component to this component.
        
        Args:
            child: Child component to add
            
        Returns:
            Self for chaining
        """
        self.children.append(child)
        return self
        
    def add_style(self, key: str, value: Any) -> 'UIComponent':
        """
        Add a style to this component.
        
        Args:
            key: Style key
            value: Style value
            
        Returns:
            Self for chaining
        """
        self.styles[key] = value
        return self
        
    def on(self, event: str, handler: Any) -> 'UIComponent':
        """
        Add an event handler.
        
        Args:
            event: Event name
            handler: Event handler function or reference
            
        Returns:
            Self for chaining
        """
        self.event_handlers[event] = handler
        return self
        
    def render(self) -> str:
        """
        Render the component as a string.
        
        Returns:
            Component representation as a string
        """
        # This is a base implementation that should be overridden by subclasses
        style_str = ""
        if self.styles:
            style_attrs = "; ".join([f"{k}: {v}" for k, v in self.styles.items()])
            style_str = f' style="{style_attrs}"'
            
        events_str = ""
        if self.event_handlers:
            events_str = " " + " ".join([f'on{event}="handleEvent(\'{self.id}\', \'{event}\')"' for event in self.event_handlers.keys()])
            
        children_str = ""
        if self.children:
            children_str = "".join([child.render() for child in self.children])
            
        return f'<div id="{self.id}" class="ui-component {self.__class__.__name__.lower()}"{style_str}{events_str}>{children_str}</div>'


class ComponentFactory:
    """Factory for creating UI components with unique IDs."""
    
    @staticmethod
    def create_id(prefix: str = "") -> str:
        """
        Create a unique ID for a component.
        
        Args:
            prefix: Optional prefix for the ID
            
        Returns:
            Unique ID string
        """
        unique_id = str(uuid.uuid4())[:8]
        return f"{prefix}-{unique_id}" if prefix else unique_id