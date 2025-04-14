# UI Components Module Pseudocode
# This module defines the UI components for the voice conversation agent

"""
TDD Test Cases:
- test_login_form_validation: Verify login form validation works correctly
- test_registration_form_validation: Verify registration form validation works correctly
- test_conversation_interface_rendering: Verify conversation interface renders correctly
- test_voice_control_state: Verify voice control state management works correctly
- test_theme_application: Verify theme is applied correctly
- test_responsive_layout: Verify layout adapts to different screen sizes
- test_accessibility_compliance: Verify UI components meet accessibility standards
- test_admin_dashboard_rendering: Verify admin dashboard renders correctly
- test_conversation_history_loading: Verify conversation history loads correctly
- test_error_handling_display: Verify error messages are displayed correctly
"""

import os
import logging
from enum import Enum
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)

# Theme mode
class ThemeMode(Enum):
    LIGHT = "light"
    DARK = "dark"

# UI component size
class ComponentSize(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"

# Color palette based on branding guide
class Colors:
    PRIMARY = "#00A99D"  # Aqua/Light Blue
    SECONDARY = "#93278F"  # Dark Purple
    TERTIARY = "#33475B"  # Cello
    ACCENT1 = "#F7931E"  # Carrot Orange
    ACCENT2 = "#29ABE2"  # Summer Sky
    BACKGROUND = "#FBF7F1"  # Floral White
    
    # Additional colors for UI
    TEXT_PRIMARY = "#333333"
    TEXT_SECONDARY = "#666666"
    TEXT_LIGHT = "#FFFFFF"
    BORDER = "#DDDDDD"
    ERROR = "#FF3B30"
    SUCCESS = "#34C759"
    WARNING = "#FFCC00"
    
    # Dark mode variants
    DARK_BACKGROUND = "#222222"
    DARK_SURFACE = "#333333"
    DARK_BORDER = "#444444"

# Font weights
class FontWeight(Enum):
    LIGHT = "light"
    NORMAL = "normal"
    BOLD = "bold"

# UI Theme
@dataclass
class Theme:
    mode: ThemeMode
    font_family: str = "Montserrat, sans-serif"
    border_radius: str = "8px"
    spacing_unit: str = "8px"
    
    @property
    def colors(self) -> Dict[str, str]:
        base_colors = {
            "primary": Colors.PRIMARY,
            "secondary": Colors.SECONDARY,
            "tertiary": Colors.TERTIARY,
            "accent1": Colors.ACCENT1,
            "accent2": Colors.ACCENT2,
            "error": Colors.ERROR,
            "success": Colors.SUCCESS,
            "warning": Colors.WARNING
        }
        
        if self.mode == ThemeMode.LIGHT:
            return {
                **base_colors,
                "background": Colors.BACKGROUND,
                "surface": "#FFFFFF",
                "textPrimary": Colors.TEXT_PRIMARY,
                "textSecondary": Colors.TEXT_SECONDARY,
                "border": Colors.BORDER
            }
        else:
            return {
                **base_colors,
                "background": Colors.DARK_BACKGROUND,
                "surface": Colors.DARK_SURFACE,
                "textPrimary": "#FFFFFF",
                "textSecondary": "#AAAAAA",
                "border": Colors.DARK_BORDER
            }
    
    @property
    def spacing(self) -> Dict[str, str]:
        unit = self.spacing_unit
        return {
            "xs": unit,
            "sm": f"calc({unit} * 2)",
            "md": f"calc({unit} * 3)",
            "lg": f"calc({unit} * 4)",
            "xl": f"calc({unit} * 6)"
        }
    
    @property
    def typography(self) -> Dict[str, Dict[str, Any]]:
        return {
            "h1": {
                "fontFamily": self.font_family,
                "fontWeight": FontWeight.BOLD.value,
                "fontSize": "32px",
                "lineHeight": "40px"
            },
            "h2": {
                "fontFamily": self.font_family,
                "fontWeight": FontWeight.BOLD.value,
                "fontSize": "24px",
                "lineHeight": "32px"
            },
            "h3": {
                "fontFamily": self.font_family,
                "fontWeight": FontWeight.BOLD.value,
                "fontSize": "20px",
                "lineHeight": "28px"
            },
            "body1": {
                "fontFamily": self.font_family,
                "fontWeight": FontWeight.NORMAL.value,
                "fontSize": "16px",
                "lineHeight": "24px"
            },
            "body2": {
                "fontFamily": self.font_family,
                "fontWeight": FontWeight.NORMAL.value,
                "fontSize": "14px",
                "lineHeight": "20px"
            },
            "caption": {
                "fontFamily": self.font_family,
                "fontWeight": FontWeight.LIGHT.value,
                "fontSize": "12px",
                "lineHeight": "16px"
            },
            "button": {
                "fontFamily": self.font_family,
                "fontWeight": FontWeight.BOLD.value,
                "fontSize": "16px",
                "lineHeight": "24px",
                "textTransform": "none"
            }
        }

# UI Components
class UIComponents:
    def __init__(self, theme: Theme):
        """
        Initialize UI components with theme
        
        Args:
            theme: UI theme
        """
        self.theme = theme
    
    def button(
        self, 
        label: str, 
        on_click: Callable[[], None], 
        variant: str = "primary", 
        size: ComponentSize = ComponentSize.MEDIUM,
        disabled: bool = False,
        icon: Optional[str] = None,
        full_width: bool = False
    ) -> Dict[str, Any]:
        """
        Create a button component
        
        Args:
            label: Button text
            on_click: Click handler
            variant: Button style variant (primary, secondary, tertiary, text)
            size: Button size
            disabled: Whether button is disabled
            icon: Optional icon name
            full_width: Whether button should take full width
            
        Returns:
            Button component configuration
        """
        return {
            "type": "button",
            "label": label,
            "on_click": on_click,
            "variant": variant,
            "size": size.value,
            "disabled": disabled,
            "icon": icon,
            "full_width": full_width,
            "style": self._get_button_style(variant, size)
        }
    
    def input(
        self, 
        label: str, 
        value: str, 
        on_change: Callable[[str], None], 
        type: str = "text",
        placeholder: str = "",
        error: Optional[str] = None,
        required: bool = False,
        disabled: bool = False
    ) -> Dict[str, Any]:
        """
        Create an input component
        
        Args:
            label: Input label
            value: Current value
            on_change: Change handler
            type: Input type (text, password, email, etc.)
            placeholder: Placeholder text
            error: Error message
            required: Whether input is required
            disabled: Whether input is disabled
            
        Returns:
            Input component configuration
        """
        return {
            "type": "input",
            "label": label,
            "value": value,
            "on_change": on_change,
            "input_type": type,
            "placeholder": placeholder,
            "error": error,
            "required": required,
            "disabled": disabled,
            "style": self._get_input_style(bool(error))
        }
    
    def card(
        self, 
        children: List[Dict[str, Any]], 
        title: Optional[str] = None,
        elevation: int = 1,
        padding: str = "md"
    ) -> Dict[str, Any]:
        """
        Create a card component
        
        Args:
            children: Child components
            title: Optional card title
            elevation: Card elevation (shadow depth)
            padding: Padding size
            
        Returns:
            Card component configuration
        """
        return {
            "type": "card",
            "title": title,
            "children": children,
            "elevation": elevation,
            "padding": padding,
            "style": self._get_card_style(elevation)
        }
    
    def conversation_bubble(
        self, 
        content: str, 
        is_user: bool, 
        timestamp: str,
        audio_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a conversation bubble component
        
        Args:
            content: Text content
            is_user: Whether bubble is from user (vs. assistant)
            timestamp: Message timestamp
            audio_url: Optional URL to audio recording
            
        Returns:
            Conversation bubble component configuration
        """
        return {
            "type": "conversation_bubble",
            "content": content,
            "is_user": is_user,
            "timestamp": timestamp,
            "audio_url": audio_url,
            "style": self._get_conversation_bubble_style(is_user)
        }
    
    def voice_control(
        self, 
        is_listening: bool, 
        on_toggle: Callable[[bool], None],
        is_muted: bool = False,
        on_mute_toggle: Optional[Callable[[bool], None]] = None
    ) -> Dict[str, Any]:
        """
        Create a voice control component
        
        Args:
            is_listening: Whether microphone is active
            on_toggle: Toggle handler
            is_muted: Whether microphone is muted
            on_mute_toggle: Mute toggle handler
            
        Returns:
            Voice control component configuration
        """
        return {
            "type": "voice_control",
            "is_listening": is_listening,
            "on_toggle": on_toggle,
            "is_muted": is_muted,
            "on_mute_toggle": on_mute_toggle,
            "style": self._get_voice_control_style(is_listening, is_muted)
        }
    
    def conversation_list_item(
        self, 
        title: str, 
        preview: str, 
        timestamp: str,
        on_click: Callable[[], None],
        is_active: bool = False
    ) -> Dict[str, Any]:
        """
        Create a conversation list item component
        
        Args:
            title: Conversation title
            preview: Preview of last message
            timestamp: Last message timestamp
            on_click: Click handler
            is_active: Whether this conversation is active
            
        Returns:
            Conversation list item component configuration
        """
        return {
            "type": "conversation_list_item",
            "title": title,
            "preview": preview,
            "timestamp": timestamp,
            "on_click": on_click,
            "is_active": is_active,
            "style": self._get_conversation_list_item_style(is_active)
        }
    
    def admin_dashboard_card(
        self, 
        title: str, 
        value: str, 
        icon: str,
        change_percent: Optional[float] = None,
        change_label: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an admin dashboard card component
        
        Args:
            title: Card title
            value: Main value to display
            icon: Icon name
            change_percent: Optional percentage change
            change_label: Optional change description
            
        Returns:
            Admin dashboard card component configuration
        """
        return {
            "type": "admin_dashboard_card",
            "title": title,
            "value": value,
            "icon": icon,
            "change_percent": change_percent,
            "change_label": change_label,
            "style": self._get_admin_dashboard_card_style(change_percent)
        }
    
    def modal(
        self, 
        title: str, 
        children: List[Dict[str, Any]], 
        is_open: bool,
        on_close: Callable[[], None],
        actions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Create a modal component
        
        Args:
            title: Modal title
            children: Child components
            is_open: Whether modal is open
            on_close: Close handler
            actions: Optional action buttons
            
        Returns:
            Modal component configuration
        """
        return {
            "type": "modal",
            "title": title,
            "children": children,
            "is_open": is_open,
            "on_close": on_close,
            "actions": actions,
            "style": self._get_modal_style()
        }
    
    def tabs(
        self, 
        tabs: List[Dict[str, Any]], 
        active_tab: int,
        on_tab_change: Callable[[int], None]
    ) -> Dict[str, Any]:
        """
        Create a tabs component
        
        Args:
            tabs: List of tab configurations
            active_tab: Index of active tab
            on_tab_change: Tab change handler
            
        Returns:
            Tabs component configuration
        """
        return {
            "type": "tabs",
            "tabs": tabs,
            "active_tab": active_tab,
            "on_tab_change": on_tab_change,
            "style": self._get_tabs_style()
        }
    
    def _get_button_style(self, variant: str, size: ComponentSize) -> Dict[str, Any]:
        """
        Get button style based on variant and size
        
        Args:
            variant: Button variant
            size: Button size
            
        Returns:
            Button style object
        """
        colors = self.theme.colors
        spacing = self.theme.spacing
        
        # Base styles
        base_style = {
            "borderRadius": self.theme.border_radius,
            "fontFamily": self.theme.font_family,
            "fontWeight": FontWeight.BOLD.value,
            "transition": "all 0.2s ease-in-out",
            "cursor": "pointer"
        }
        
        # Size styles
        if size == ComponentSize.SMALL:
            size_style = {
                "padding": f"{spacing['xs']} {spacing['sm']}",
                "fontSize": "14px"
            }
        elif size == ComponentSize.LARGE:
            size_style = {
                "padding": f"{spacing['md']} {spacing['lg']}",
                "fontSize": "18px"
            }
        else:  # MEDIUM
            size_style = {
                "padding": f"{spacing['sm']} {spacing['md']}",
                "fontSize": "16px"
            }
        
        # Variant styles
        if variant == "primary":
            variant_style = {
                "backgroundColor": colors["primary"],
                "color": colors["textLight"],
                "border": "none",
                "hoverBackgroundColor": self._adjust_color(colors["primary"], -15),
                "activeBackgroundColor": self._adjust_color(colors["primary"], -25)
            }
        elif variant == "secondary":
            variant_style = {
                "backgroundColor": colors["secondary"],
                "color": colors["textLight"],
                "border": "none",
                "hoverBackgroundColor": self._adjust_color(colors["secondary"], -15),
                "activeBackgroundColor": self._adjust_color(colors["secondary"], -25)
            }
        elif variant == "tertiary":
            variant_style = {
                "backgroundColor": "transparent",
                "color": colors["primary"],
                "border": f"1px solid {colors['primary']}",
                "hoverBackgroundColor": self._adjust_color(colors["primary"], 90),
                "activeBackgroundColor": self._adjust_color(colors["primary"], 80)
            }
        else:  # text
            variant_style = {
                "backgroundColor": "transparent",
                "color": colors["primary"],
                "border": "none",
                "hoverBackgroundColor": self._adjust_color(colors["primary"], 90),
                "activeBackgroundColor": self._adjust_color(colors["primary"], 80)
            }
        
        return {**base_style, **size_style, **variant_style}
    
    def _get_input_style(self, has_error: bool) -> Dict[str, Any]:
        """
        Get input style
        
        Args:
            has_error: Whether input has an error
            
        Returns:
            Input style object
        """
        colors = self.theme.colors
        spacing = self.theme.spacing
        
        border_color = colors["error"] if has_error else colors["border"]
        
        return {
            "container": {
                "marginBottom": spacing["md"]
            },
            "label": {
                "display": "block",
                "marginBottom": spacing["xs"],
                "color": colors["textPrimary"],
                "fontSize": "14px",
                "fontWeight": FontWeight.NORMAL.value
            },
            "input": {
                "width": "100%",
                "padding": spacing["sm"],
                "borderRadius": self.theme.border_radius,
                "border": f"1px solid {border_color}",
                "fontSize": "16px",
                "backgroundColor": colors["surface"],
                "color": colors["textPrimary"],
                "transition": "border-color 0.2s ease-in-out",
                "focusBorderColor": colors["primary"]
            },
            "error": {
                "color": colors["error"],
                "fontSize": "12px",
                "marginTop": spacing["xs"]
            }
        }
    
    def _get_card_style(self, elevation: int) -> Dict[str, Any]:
        """
        Get card style based on elevation
        
        Args:
            elevation: Card elevation
            
        Returns:
            Card style object
        """
        colors = self.theme.colors
        spacing = self.theme.spacing
        
        shadow = "none"
        if elevation == 1:
            shadow = "0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)"
        elif elevation == 2:
            shadow = "0 3px 6px rgba(0,0,0,0.16), 0 3px 6px rgba(0,0,0,0.23)"
        elif elevation >= 3:
            shadow = "0 10px 20px rgba(0,0,0,0.19), 0 6px 6px rgba(0,0,0,0.23)"
        
        return {
            "backgroundColor": colors["surface"],
            "borderRadius": self.theme.border_radius,
            "boxShadow": shadow,
            "overflow": "hidden",
            "title": {
                "padding": spacing["md"],
                "borderBottom": f"1px solid {colors['border']}",
                "fontWeight": FontWeight.BOLD.value,
                "fontSize": "18px"
            },
            "content": {
                "padding": spacing["md"]
            }
        }
    
    def _get_conversation_bubble_style(self, is_user: bool) -> Dict[str, Any]:
        """
        Get conversation bubble style
        
        Args:
            is_user: Whether bubble is from user
            
        Returns:
            Conversation bubble style object
        """
        colors = self.theme.colors
        spacing = self.theme.spacing
        
        background_color = colors["primary"] if is_user else colors["surface"]
        text_color = colors["textLight"] if is_user else colors["textPrimary"]
        border = "none" if is_user else f"1px solid {colors['border']}"
        align = "flex-end" if is_user else "flex-start"
        
        return {
            "container": {
                "display": "flex",
                "flexDirection": "column",
                "alignItems": align,
                "marginBottom": spacing["md"]
            },
            "bubble": {
                "maxWidth": "80%",
                "padding": spacing["md"],
                "borderRadius": self.theme.border_radius,
                "backgroundColor": background_color,
                "color": text_color,
                "border": border
            },
            "timestamp": {
                "fontSize": "12px",
                "color": colors["textSecondary"],
                "marginTop": spacing["xs"]
            },
            "audioControls": {
                "marginTop": spacing["sm"]
            }
        }
    
    def _get_voice_control_style(self, is_listening: bool, is_muted: bool) -> Dict[str, Any]:
        """
        Get voice control style
        
        Args:
            is_listening: Whether microphone is active
            is_muted: Whether microphone is muted
            
        Returns:
            Voice control style object
        """
        colors = self.theme.colors
        spacing = self.theme.spacing
        
        button_color = colors["error"] if is_listening else colors["primary"]
        if is_muted:
            button_color = colors["warning"]
        
        return {
            "container": {
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
                "padding": spacing["md"]
            },
            "button": {
                "width": "64px",
                "height": "64px",
                "borderRadius": "50%",
                "backgroundColor": button_color,
                "color": colors["textLight"],
                "border": "none",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
                "cursor": "pointer",
                "transition": "all 0.2s ease-in-out",
                "boxShadow": "0 3px 6px rgba(0,0,0,0.16), 0 3px 6px rgba(0,0,0,0.23)",
                "hoverTransform": "scale(1.05)",
                "activeTransform": "scale(0.95)"
            },
            "muteButton": {
                "width": "40px",
                "height": "40px",
                "borderRadius": "50%",
                "backgroundColor": colors["surface"],
                "color": is_muted ? colors["warning"] : colors["textSecondary"],
                "border": f"1px solid {colors['border']}",
                "marginLeft": spacing["md"],
                "cursor": "pointer"
            }
        }
    
    def _get_conversation_list_item_style(self, is_active: bool) -> Dict[str, Any]:
        """
        Get conversation list item style
        
        Args:
            is_active: Whether this conversation is active
            
        Returns:
            Conversation list item style object
        """
        colors = self.theme.colors
        spacing = self.theme.spacing
        
        background_color = self._adjust_color(colors["primary"], 90) if is_active else colors["surface"]
        border_left = f"4px solid {colors['primary']}" if is_active else "4px solid transparent"
        
        return {
            "container": {
                "padding": spacing["md"],
                "borderBottom": f"1px solid {colors['border']}",
                "backgroundColor": background_color,
                "borderLeft": border_left,
                "cursor": "pointer",
                "transition": "background-color 0.2s ease-in-out",
                "hoverBackgroundColor": self._adjust_color(colors["primary"], 95)
            },
            "title": {
                "fontWeight": FontWeight.BOLD.value,
                "marginBottom": spacing["xs"],
                "color": colors["textPrimary"]
            },
            "preview": {
                "fontSize": "14px",
                "color": colors["textSecondary"],
                "whiteSpace": "nowrap",
                "overflow": "hidden",
                "textOverflow": "ellipsis"
            },
            "timestamp": {
                "fontSize": "12px",
                "color": colors["textSecondary"],
                "marginTop": spacing["xs"]
            }
        }
    
    def _get_admin_dashboard_card_style(self, change_percent: Optional[float]) -> Dict[str, Any]:
        """
        Get admin dashboard card style
        
        Args:
            change_percent: Percentage change
            
        Returns:
            Admin dashboard card style object
        """
        colors = self.theme.colors
        spacing = self.theme.spacing
        
        change_color = colors["textSecondary"]
        if change_percent is not None:
            change_color = colors["success"] if change_percent >= 0 else colors["error"]
        
        return {
            "container": {
                "padding": spacing["md"],
                "borderRadius": self.theme.border_radius,
                "backgroundColor": colors["surface"],
                "boxShadow": "0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)"
            },
            "title": {
                "fontSize": "14px",
                "color": colors["textSecondary"],
                "marginBottom": spacing["xs"]
            },
            "value": {
                "fontSize": "24px",
                "fontWeight": FontWeight.BOLD.value,
                "color": colors["textPrimary"],
                "marginBottom": spacing["sm"]
            },
            "icon": {
                "color": colors["primary"],
                "fontSize": "20px"
            },
            "change": {
                "fontSize": "14px",
                "color": change_color,
                "display": "flex",
                "alignItems": "center"
            }
        }
    
    def _get_modal_style(self) -> Dict[str, Any]:
        """
        Get modal style
        
        Returns:
            Modal style object
        """
        colors = self.theme.colors
        spacing = self.theme.spacing
        
        return {
            "overlay": {
                "position": "fixed",
                "top": 0,
                "left": 0,
                "right": 0,
                "bottom": 0,
                "backgroundColor": "rgba(0, 0, 0, 0.5)",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
                "zIndex": 1000
            },
            "container": {
                "backgroundColor": colors["surface"],
                "borderRadius": self.theme.border_radius,
                "boxShadow": "0 10px 20px rgba(0,0,0,0.19), 0 6px 6px rgba(0,0,0,0.23)",
                "width": "90%",
                "maxWidth": "500px",
                "maxHeight": "90vh",
                "overflow": "auto"
            },
            "header": {
                "padding": spacing["md"],
                "borderBottom": f"1px solid {colors['border']}",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between"
            },
            "title": {
                "fontWeight": FontWeight.BOLD.value,
                "fontSize": "18px"
            },
            "closeButton": {
                "backgroundColor": "transparent",
                "border": "none",
                "cursor": "pointer",
                "color": colors["textSecondary"]
            },
            "content": {
                "padding": spacing["md"]
            },
            "footer": {
                "padding": spacing["md"],
                "borderTop": f"1px solid {colors['border']}",
                "display": "flex",
                "justifyContent": "flex-end",
                "gap": spacing["sm"]
            }
        }
    
    def _get_tabs_style(self) -> Dict[str, Any]:
        """
        Get tabs style
        
        Returns:
            Tabs style object
        """
        colors = self.theme.colors
        spacing = self.theme.spacing
        
        return {
            "container": {
                "borderBottom": f"1px solid {colors['border']}"
            },
            "tabList": {
                "display": "flex",
                "overflow": "auto"
            },
            "tab": {
                "padding": `${spacing["sm"]} ${spacing["md"]}`,
                "cursor": "pointer",
                "borderBottom": "2px solid transparent",
                "transition": "all 0.2s ease-in-out",
                "whiteSpace": "nowrap"
            },
            "activeTab": {
                "borderBottomColor": colors["primary"],
                "color": colors["primary"],
                "fontWeight": FontWeight.BOLD.value
            },
            "tabPanel": {
                "padding": spacing["md"]
            }
        }
    
    def _adjust_color(self, hex_color: str, amount: int) -> str:
        """
        Adjust color brightness
        
        Args:
            hex_color: Hex color code
            amount: Amount to adjust (-100 to 100)
            
        Returns:
            Adjusted hex color
        """
        # This would be implemented with actual color manipulation
        # For pseudocode, we'll just return the original color
        return hex_color


# Factory function to create UI components
def create_ui_components(theme_mode: ThemeMode = ThemeMode.LIGHT) -> UIComponents:
    """
    Create and initialize UI components
    
    Args:
        theme_mode: Theme mode (light or dark)
        
    Returns:
        Initialized UIComponents instance
    """
    theme = Theme(mode=theme_mode)
    return UIComponents(theme)