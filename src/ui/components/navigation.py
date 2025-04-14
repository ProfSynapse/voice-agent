"""
Navigation UI Components Module

This module provides navigation UI components for the voice agent application.
"""

from typing import Dict, List, Optional, Any, Callable

from src.ui.components.base import UIComponent


class List(UIComponent):
    """List component for displaying a list of items."""
    
    def __init__(
        self, 
        id: str, 
        dense: bool = False,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a list component.
        
        Args:
            id: Component ID
            dense: Whether the list is dense
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.dense = dense
        
    def render(self) -> Dict[str, Any]:
        """
        Render the list component as a dictionary.
        
        Returns:
            List component representation as a dictionary
        """
        result = super().render()
        result.update({
            "dense": self.dense
        })
        return result


class ListItem(UIComponent):
    """List item component for displaying an item in a list."""
    
    def __init__(
        self,
        id: str,
        text: str,
        secondary_text: Optional[str] = None,
        selected: bool = False,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a list item component.
        
        Args:
            id: Component ID
            text: Primary text
            secondary_text: Optional secondary text
            selected: Whether the item is selected
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.text = text
        self.secondary_text = secondary_text
        self.selected = selected
        
    def render(self) -> Dict[str, Any]:
        """
        Render the list item component as a dictionary.
        
        Returns:
            List item component representation as a dictionary
        """
        result = super().render()
        result.update({
            "text": self.text,
            "secondary_text": self.secondary_text,
            "selected": self.selected
        })
        return result


class Tabs(UIComponent):
    """Tabs component for displaying tabs."""
    
    def __init__(
        self,
        id: str,
        value: int = 0,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a tabs component.
        
        Args:
            id: Component ID
            value: Index of the selected tab
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.value = value
        self.tabs = []
        self.panels = []
        
    def add_tab(self, label: str, icon: Optional[str] = None) -> 'Tabs':
        """
        Add a tab.
        
        Args:
            label: Tab label
            icon: Optional tab icon
            
        Returns:
            Self for chaining
        """
        self.tabs.append({
            "label": label,
            "icon": icon
        })
        return self
        
    def add_panel(self, component: UIComponent) -> 'Tabs':
        """
        Add a tab panel.
        
        Args:
            component: Panel content
            
        Returns:
            Self for chaining
        """
        self.panels.append(component)
        return self
        
    def render(self) -> Dict[str, Any]:
        """
        Render the tabs component as a dictionary.
        
        Returns:
            Tabs component representation as a dictionary
        """
        result = super().render()
        result.update({
            "value": self.value,
            "tabs": self.tabs,
            "panels": [panel.render() for panel in self.panels]
        })
        return result


class Menu(UIComponent):
    """Menu component for displaying a menu."""
    
    def __init__(
        self,
        id: str,
        anchor_id: str,
        open: bool = False,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a menu component.
        
        Args:
            id: Component ID
            anchor_id: ID of the anchor element
            open: Whether the menu is open
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.anchor_id = anchor_id
        self.open = open
        self.items = []
        
    def add_item(
        self,
        text: str,
        icon: Optional[str] = None,
        disabled: bool = False
    ) -> 'Menu':
        """
        Add a menu item.
        
        Args:
            text: Item text
            icon: Optional item icon
            disabled: Whether the item is disabled
            
        Returns:
            Self for chaining
        """
        self.items.append({
            "text": text,
            "icon": icon,
            "disabled": disabled
        })
        return self
        
    def render(self) -> Dict[str, Any]:
        """
        Render the menu component as a dictionary.
        
        Returns:
            Menu component representation as a dictionary
        """
        result = super().render()
        result.update({
            "anchor_id": self.anchor_id,
            "open": self.open,
            "items": self.items
        })
        return result