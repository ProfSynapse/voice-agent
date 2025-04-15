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
        id: str = "button",
        text: str = "",
        variant: str = "contained",
        color: str = "primary",
        disabled: bool = False,
        on_click: Optional[Callable[[], None]] = None,
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
            on_click: Click event handler
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.text = text
        self.variant = variant
        self.color = color
        self.disabled = disabled
        self.on_click = on_click
        
    def handle_click(self):
        """Handle button click event."""
        if self.on_click and not self.disabled:
            self.on_click()
    
    def render(self) -> str:
        """
        Render the button component as a string.
        
        Returns:
            Button component representation as a string
        """
        disabled_attr = "disabled" if self.disabled else ""
        return f"<button id='{self.id}' class='button {self.variant} {self.color}' {disabled_attr}>{self.text}</button>"


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
        id: str = "input",
        label: str = "",
        value: str = "",
        placeholder: str = "",
        type: str = "text",
        required: bool = False,
        disabled: bool = False,
        on_change: Optional[Callable[[str], None]] = None,
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
            on_change: Change event handler
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.label = label
        self.value = value
        self.placeholder = placeholder
        self.type = type
        self.required = required
        self.disabled = disabled
        self.on_change = on_change
        
    def handle_change(self, new_value: str):
        """
        Handle value change.
        
        Args:
            new_value: New input value
        """
        self.value = new_value
        if self.on_change:
            self.on_change(new_value)
    
    def render(self) -> str:
        """
        Render the input component as a string.
        
        Returns:
            Input component representation as a string
        """
        required_attr = "required" if self.required else ""
        disabled_attr = "disabled" if self.disabled else ""
        return f"""
        <div class="input-container">
            <label for="{self.id}">{self.label}</label>
            <input
                id="{self.id}"
                type="{self.type}"
                value="{self.value}"
                placeholder="{self.placeholder}"
                {required_attr}
                {disabled_attr}
            />
        </div>
        """


class TextField(Input):
    """TextField component for user text input with additional features."""
    
    def __init__(
        self,
        label: str = "",
        value: str = "",
        placeholder: str = "",
        multiline: bool = False,
        rows: int = 1,
        helper_text: Optional[str] = None,
        error: bool = False,
        on_change: Optional[Callable[[str], None]] = None,
        id: str = "text-field",
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a text field component.
        
        Args:
            label: Input label
            value: Initial value
            placeholder: Placeholder text
            multiline: Whether the text field is multiline
            rows: Number of rows for multiline text fields
            helper_text: Helper text to display below the input
            error: Whether the input has an error
            on_change: Callback function when the value changes
            id: Component ID
            styles: Optional styles for the component
        """
        super().__init__(
            id=id,
            label=label,
            value=value,
            placeholder=placeholder,
            type="text",
            on_change=on_change,
            styles=styles
        )
        self.multiline = multiline
        self.rows = rows
        self.helper_text = helper_text
        self.error = error
        
    def render(self) -> str:
        """
        Render the text field component as a string.
        
        Returns:
            Text field component representation as a string
        """
        error_class = "error" if self.error else ""
        helper_text_html = f'<div class="helper-text">{self.helper_text}</div>' if self.helper_text else ""
        
        if self.multiline:
            return f"""
            <div class="text-field-container {error_class}">
                <label for="{self.id}">{self.label}</label>
                <textarea
                    id="{self.id}"
                    rows="{self.rows}"
                    placeholder="{self.placeholder}"
                    {self._get_common_attrs()}
                >{self.value}</textarea>
                {helper_text_html}
            </div>
            """
        else:
            return f"""
            <div class="text-field-container {error_class}">
                <label for="{self.id}">{self.label}</label>
                <input
                    id="{self.id}"
                    type="text"
                    value="{self.value}"
                    placeholder="{self.placeholder}"
                    {self._get_common_attrs()}
                />
                {helper_text_html}
            </div>
            """
    
    def _get_common_attrs(self) -> str:
        """Get common HTML attributes."""
        required_attr = "required" if self.required else ""
        disabled_attr = "disabled" if self.disabled else ""
        return f"{required_attr} {disabled_attr}"