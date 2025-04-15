"""
Infrastructure Monitoring Module

This module provides infrastructure monitoring functionality for the Voice Agent application.
"""

from src.monitoring.infrastructure.infrastructure_monitor import InfrastructureMonitor

infrastructure_monitor = InfrastructureMonitor()

__all__ = ['infrastructure_monitor']