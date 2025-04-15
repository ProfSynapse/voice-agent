"""
Monitoring Module

This module provides monitoring and logging functionality for the application,
including security monitoring, performance tracking, and audit logging.
"""

from src.monitoring.security_monitoring import get_security_monitor, SecurityMonitor

__all__ = [
    'get_security_monitor',
    'SecurityMonitor'
]