"""
Input UI Components Module

This module provides input UI components for the voice agent application.
"""

from typing import Dict, List, Optional, Any, Callable

from src.ui.components.base import UIComponent


class Button(UIComponent):
    """Button component for user interactions."""
    
    def __init__(
        self, 
        id: str, 
        text: str,
        variant: str = "contained",
        color: str = "primary",
        disabled: bool = False,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a button component.
        
        Args:
            id: Component ID
            text: Button text
            variant: Button variant (contained, outlined, text)
            color: Button color
            disabled: Whether the button is disabled
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.text = text
        self.variant = variant
        self.color = color
        self.disabled = disabled
        
    def render(self) -> Dict[str, Any]:
        """
        Render the button component as a dictionary.
        
        Returns:
            Button component representation as a dictionary
        """
        result = super().render()
        result.update({
            "text": self.text,
            "variant": self.variant,
            "color": self.color,
            "disabled": self.disabled
        })
        return result


class IconButton(UIComponent):
    """Icon button component for user interaction."""
    
    def __init__(
        self,
        id: str,
        icon_name: str,
        size: str = "medium",
        color: str = "inherit",
        disabled: bool = False,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize an icon button component.
        
        Args:
            id: Component ID
            icon_name: Icon name
            size: Button size (small, medium, large)
            color: Button color
            disabled: Whether the button is disabled
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.icon_name = icon_name
        self.size = size
        self.color = color
        self.disabled = disabled
        
    def render(self) -> Dict[str, Any]:
        """
        Render the icon button component as a dictionary.
        
        Returns:
            Icon button component representation as a dictionary
        """
        result = super().render()
        result.update({
            "icon_name": self.icon_name,
            "size": self.size,
            "color": self.color,
            "disabled": self.disabled
        })
        return result


class Input(UIComponent):
    """Input component for user text input."""
    
    def __init__(
        self, 
        id: str, 
        label: str,
        value: str = "",
        placeholder: str = "",
        type: str = "text",
        required: bool = False,
        disabled: bool = False,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize an input component.
        
        Args:
            id: Component ID
            label: Input label
            value: Initial value
            placeholder: Placeholder text
            type: Input type (text, password, email, etc.)
            required: Whether the input is required
            disabled: Whether the input is disabled
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.label = label
        self.value = value
        self.placeholder = placeholder
        self.type = type
        self.required = required
        self.disabled = disabled
        
    def render(self) -> Dict[str, Any]:
        """
        Render the input component as a dictionary.
        
        Returns:
            Input component representation as a dictionary
        """
        result = super().render()
        result.update({
            "label": self.label,
            "value": self.value,
            "placeholder": self.placeholder,
            "type": self.type,
            "required": self.required,
            "disabled": self.disabled
        })
        return result