"""
Performance Monitoring Module

This module provides performance monitoring functionality for the Voice Agent application.
"""

from src.monitoring.performance.performance_monitor import PerformanceMonitor

performance_monitor = PerformanceMonitor()

__all__ = ['performance_monitor']