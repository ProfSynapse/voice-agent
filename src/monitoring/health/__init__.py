"""
Health Monitoring Module

This module provides health check functionality for the Voice Agent application.
"""

from src.monitoring.health.health_monitor import HealthMonitor

health_monitor = HealthMonitor()

__all__ = ['health_monitor']