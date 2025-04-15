"""
Error Monitoring Module

This module provides error tracking functionality for the Voice Agent application.
"""

from src.monitoring.errors.error_monitor import ErrorMonitor

error_monitor = ErrorMonitor()

__all__ = ['error_monitor']