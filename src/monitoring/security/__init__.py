"""
Security Monitoring Module

This module provides security monitoring functionality for the Voice Agent application.
"""

from src.monitoring.security.security_monitor import SecurityMonitor

security_monitor = SecurityMonitor()

__all__ = ['security_monitor']