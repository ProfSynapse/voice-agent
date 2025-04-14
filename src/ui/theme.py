"""
UI Theme Module

This module provides theme configuration for the voice agent application.
It centralizes all theme-related constants and configurations.
"""

import os
from typing import Dict, Any

from src.security.secrets_manager import get_secrets_manager


class UITheme:
    """UI theme configuration."""
    
    def __init__(self):
        """Initialize the UI theme."""
        self.secrets = get_secrets_manager()
        self._load_theme()
        
    def _load_theme(self):
        """Load theme configuration."""
        # Colors
        self.colors = {
            "primary": self.secrets.get("UI_PRIMARY_COLOR", "#1976d2"),
            "secondary": self.secrets.get("UI_SECONDARY_COLOR", "#dc004e"),
            "error": self.secrets.get("UI_ERROR_COLOR", "#f44336"),
            "warning": self.secrets.get("UI_WARNING_COLOR", "#ff9800"),
            "info": self.secrets.get("UI_INFO_COLOR", "#2196f3"),
            "success": self.secrets.get("UI_SUCCESS_COLOR", "#4caf50"),
            "background": self.secrets.get("UI_BACKGROUND_COLOR", "#ffffff"),
            "surface": self.secrets.get("UI_SURFACE_COLOR", "#ffffff"),
            "text": self.secrets.get("UI_TEXT_COLOR", "#000000"),
            "textSecondary": self.secrets.get("UI_TEXT_SECONDARY_COLOR", "#757575"),
            "divider": self.secrets.get("UI_DIVIDER_COLOR", "#e0e0e0")
        }
        
        # Typography
        self.typography = {
            "fontFamily": self.secrets.get("UI_FONT_FAMILY", "Roboto, Arial, sans-serif"),
            "fontSize": self.secrets.get("UI_FONT_SIZE", "14px"),
            "fontWeightLight": 300,
            "fontWeightRegular": 400,
            "fontWeightMedium": 500,
            "fontWeightBold": 700,
            "h1": {
                "fontSize": "2.5rem",
                "fontWeight": 300,
                "lineHeight": 1.2
            },
            "h2": {
                "fontSize": "2rem",
                "fontWeight": 300,
                "lineHeight": 1.2
            },
            "h3": {
                "fontSize": "1.75rem",
                "fontWeight": 400,
                "lineHeight": 1.2
            },
            "h4": {
                "fontSize": "1.5rem",
                "fontWeight": 400,
                "lineHeight": 1.2
            },
            "h5": {
                "fontSize": "1.25rem",
                "fontWeight": 400,
                "lineHeight": 1.2
            },
            "h6": {
                "fontSize": "1rem",
                "fontWeight": 500,
                "lineHeight": 1.2
            },
            "body1": {
                "fontSize": "1rem",
                "fontWeight": 400,
                "lineHeight": 1.5
            },
            "body2": {
                "fontSize": "0.875rem",
                "fontWeight": 400,
                "lineHeight": 1.5
            },
            "button": {
                "fontSize": "0.875rem",
                "fontWeight": 500,
                "lineHeight": 1.75,
                "textTransform": "uppercase"
            },
            "caption": {
                "fontSize": "0.75rem",
                "fontWeight": 400,
                "lineHeight": 1.66
            },
            "overline": {
                "fontSize": "0.75rem",
                "fontWeight": 400,
                "lineHeight": 2.66,
                "textTransform": "uppercase"
            }
        }
        
        # Spacing
        self.spacing = {
            "unit": self.secrets.get("UI_SPACING_UNIT", "8px"),
            "xs": "4px",
            "sm": "8px",
            "md": "16px",
            "lg": "24px",
            "xl": "32px",
            "xxl": "48px"
        }
        
        # Breakpoints
        self.breakpoints = {
            "xs": "0px",
            "sm": "600px",
            "md": "960px",
            "lg": "1280px",
            "xl": "1920px"
        }
        
        # Shadows
        self.shadows = [
            "none",
            "0px 2px 1px -1px rgba(0,0,0,0.2),0px 1px 1px 0px rgba(0,0,0,0.14),0px 1px 3px 0px rgba(0,0,0,0.12)",
            "0px 3px 1px -2px rgba(0,0,0,0.2),0px 2px 2px 0px rgba(0,0,0,0.14),0px 1px 5px 0px rgba(0,0,0,0.12)",
            "0px 3px 3px -2px rgba(0,0,0,0.2),0px 3px 4px 0px rgba(0,0,0,0.14),0px 1px 8px 0px rgba(0,0,0,0.12)",
            "0px 2px 4px -1px rgba(0,0,0,0.2),0px 4px 5px 0px rgba(0,0,0,0.14),0px 1px 10px 0px rgba(0,0,0,0.12)",
            "0px 3px 5px -1px rgba(0,0,0,0.2),0px 5px 8px 0px rgba(0,0,0,0.14),0px 1px 14px 0px rgba(0,0,0,0.12)"
        ]
        
        # Transitions
        self.transitions = {
            "easing": {
                "easeInOut": "cubic-bezier(0.4, 0, 0.2, 1)",
                "easeOut": "cubic-bezier(0.0, 0, 0.2, 1)",
                "easeIn": "cubic-bezier(0.4, 0, 1, 1)",
                "sharp": "cubic-bezier(0.4, 0, 0.6, 1)"
            },
            "duration": {
                "shortest": "150ms",
                "shorter": "200ms",
                "short": "250ms",
                "standard": "300ms",
                "complex": "375ms",
                "enteringScreen": "225ms",
                "leavingScreen": "195ms"
            }
        }
        
        # Z-index
        self.zIndex = {
            "mobileStepper": 1000,
            "appBar": 1100,
            "drawer": 1200,
            "modal": 1300,
            "snackbar": 1400,
            "tooltip": 1500
        }
        
    def get_theme(self) -> Dict[str, Any]:
        """
        Get the complete theme configuration.
        
        Returns:
            Theme configuration as a dictionary
        """
        return {
            "colors": self.colors,
            "typography": self.typography,
            "spacing": self.spacing,
            "breakpoints": self.breakpoints,
            "shadows": self.shadows,
            "transitions": self.transitions,
            "zIndex": self.zIndex
        }


# Create a singleton instance
_ui_theme = None

def get_ui_theme() -> UITheme:
    """
    Get the singleton UITheme instance.
    
    Returns:
        UITheme instance
    """
    global _ui_theme
    if _ui_theme is None:
        _ui_theme = UITheme()
    return _ui_theme