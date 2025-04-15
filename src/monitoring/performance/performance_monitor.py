"""
Performance Monitor Module

This module provides performance monitoring functionality for the Voice Agent application.
"""

import time
import asyncio
import logging
import os
import platform
import psutil
import functools
from typing import Dict, Any, List, Callable, Optional, Union
from datetime import datetime, timedelta
from collections import deque
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class PerformanceMetric(BaseModel):
    """Model for performance metrics."""
    name: str
    value: float
    unit: str
    timestamp: float
    tags: Dict[str, str] = {}

class PerformanceMonitor:
    """
    Performance Monitor for the Voice Agent application.
    
    This class provides performance monitoring functionality to track response times,
    voice processing latency, database query performance, and resource usage.
    """
    
    def __init__(self):
        """Initialize the performance monitor."""
        self.metrics = {}
        self.metric_history = {}
        self.history_size = 1000  # Number of data points to keep per metric
        self.alert_thresholds = {}
        self.alert_handlers = []
        self.collection_interval = 10  # seconds
        self.is_collecting = False
        self.collection_task = None
        
    def register_with_app(self, app: FastAPI):
        """
        Register performance monitoring middleware and endpoints with the FastAPI application.
        
        Args:
            app: The FastAPI application
        """
        # Add middleware for request timing
        @app.middleware("http")
        async def performance_middleware(request: Request, call_next):
            # Start timer
            start_time = time.time()
            
            # Process request
            response = await call_next(request)
            
            # End timer
            duration = time.time() - start_time
            
            # Record metric
            path = request.url.path
            self.record_metric(
                name=f"http.request.duration",
                value=duration * 1000,  # Convert to ms
                unit="ms",
                tags={
                    "path": path,
                    "method": request.method,
                    "status_code": str(response.status_code)
                }
            )
            
            return response
        
        # Register performance metrics endpoint
        @app.get("/metrics/performance")
        async def get_performance_metrics():
            return {
                "metrics": self.get_current_metrics(),
                "timestamp": time.time()
            }
        
        # Register resource usage endpoint
        @app.get("/metrics/resources")
        async def get_resource_metrics():
            return {
                "metrics": self.get_resource_usage(),
                "timestamp": time.time()
            }
        
        # Register metric history endpoint
        @app.get("/metrics/history/{metric_name}")
        async def get_metric_history(metric_name: str, limit: int = 100):
            if metric_name not in self.metric_history:
                return {"error": f"Metric {metric_name} not found"}
            
            history = list(self.metric_history[metric_name])[-limit:]
            return {
                "metric": metric_name,
                "history": history,
                "count": len(history)
            }
        
        # Start the background collection task
        @app.on_event("startup")
        async def start_collection_task():
            self.start_collection()
    
    def record_metric(self, name: str, value: float, unit: str, tags: Dict[str, str] = {}):
        """
        Record a performance metric.
        
        Args:
            name: The name of the metric
            value: The metric value
            unit: The unit of measurement
            tags: Additional tags for the metric
        """
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=time.time(),
            tags=tags
        )
        
        # Store current value
        self.metrics[name] = metric
        
        # Add to history
        if name not in self.metric_history:
            self.metric_history[name] = deque(maxlen=self.history_size)
        
        self.metric_history[name].append(metric.dict())
        
        # Check for alerts
        self._check_alert(name, value)
        
        return metric
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """
        Get the current values of all metrics.
        
        Returns:
            A dict of current metric values
        """
        return {name: metric.dict() for name, metric in self.metrics.items()}
    
    def get_metric_history(self, name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get the history of a specific metric.
        
        Args:
            name: The name of the metric
            limit: Maximum number of data points to return
            
        Returns:
            A list of historical metric values
        """
        if name not in self.metric_history:
            return []
        
        return list(self.metric_history[name])[-limit:]
    
    def set_alert_threshold(self, metric_name: str, threshold: float, 
                           comparison: str = "gt", duration: int = 0):
        """
        Set an alert threshold for a metric.
        
        Args:
            metric_name: The name of the metric
            threshold: The threshold value
            comparison: The comparison operator ("gt", "lt", "eq", "ne", "ge", "le")
            duration: The duration in seconds the threshold must be exceeded
        """
        self.alert_thresholds[metric_name] = {
            "threshold": threshold,
            "comparison": comparison,
            "duration": duration,
            "first_triggered": None
        }
    
    def add_alert_handler(self, handler: Callable[[str, float, float], None]):
        """
        Add an alert handler to be called when a threshold is exceeded.
        
        Args:
            handler: A function that takes metric name, value, and threshold
        """
        self.alert_handlers.append(handler)
    
    def start_collection(self):
        """Start the background metric collection task."""
        if not self.is_collecting:
            self.is_collecting = True
            self.collection_task = asyncio.create_task(self._collect_metrics())
    
    def stop_collection(self):
        """Stop the background metric collection task."""
        self.is_collecting = False
        if self.collection_task:
            self.collection_task.cancel()
    
    async def _collect_metrics(self):
        """Background task to collect metrics periodically."""
        while self.is_collecting:
            try:
                # Collect resource usage metrics
                self._collect_resource_metrics()
                
                # Collect other system metrics
                self._collect_system_metrics()
                
            except Exception as e:
                logger.error(f"Error collecting metrics: {str(e)}")
            
            await asyncio.sleep(self.collection_interval)
    
    def _collect_resource_metrics(self):
        """Collect resource usage metrics."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=None)
        self.record_metric(
            name="system.cpu.usage",
            value=cpu_percent,
            unit="percent"
        )
        
        # Per-CPU usage
        per_cpu = psutil.cpu_percent(interval=None, percpu=True)
        for i, cpu in enumerate(per_cpu):
            self.record_metric(
                name="system.cpu.core.usage",
                value=cpu,
                unit="percent",
                tags={"core": str(i)}
            )
        
        # Memory usage
        memory = psutil.virtual_memory()
        self.record_metric(
            name="system.memory.usage",
            value=memory.percent,
            unit="percent"
        )
        self.record_metric(
            name="system.memory.available",
            value=memory.available / (1024 * 1024),  # Convert to MB
            unit="MB"
        )
        
        # Disk usage
        disk = psutil.disk_usage('/')
        self.record_metric(
            name="system.disk.usage",
            value=disk.percent,
            unit="percent"
        )
        self.record_metric(
            name="system.disk.free",
            value=disk.free / (1024 * 1024 * 1024),  # Convert to GB
            unit="GB"
        )
        
        # Network I/O
        net_io = psutil.net_io_counters()
        self.record_metric(
            name="system.network.bytes_sent",
            value=net_io.bytes_sent,
            unit="bytes"
        )
        self.record_metric(
            name="system.network.bytes_recv",
            value=net_io.bytes_recv,
            unit="bytes"
        )
        
        # Process-specific metrics
        process = psutil.Process(os.getpid())
        
        # Process CPU usage
        process_cpu = process.cpu_percent(interval=None)
        self.record_metric(
            name="process.cpu.usage",
            value=process_cpu,
            unit="percent"
        )
        
        # Process memory usage
        process_memory = process.memory_info()
        self.record_metric(
            name="process.memory.rss",
            value=process_memory.rss / (1024 * 1024),  # Convert to MB
            unit="MB"
        )
        
        # Process threads
        process_threads = process.num_threads()
        self.record_metric(
            name="process.threads",
            value=process_threads,
            unit="count"
        )
        
        # Process open files
        try:
            process_files = len(process.open_files())
            self.record_metric(
                name="process.open_files",
                value=process_files,
                unit="count"
            )
        except Exception:
            pass  # May not be available on all platforms
    
    def _collect_system_metrics(self):
        """Collect other system metrics."""
        # System load (Linux/Unix only)
        if platform.system() != "Windows":
            load1, load5, load15 = os.getloadavg()
            self.record_metric(
                name="system.load.1min",
                value=load1,
                unit="load"
            )
            self.record_metric(
                name="system.load.5min",
                value=load5,
                unit="load"
            )
            self.record_metric(
                name="system.load.15min",
                value=load15,
                unit="load"
            )
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """
        Get current resource usage metrics.
        
        Returns:
            A dict of resource usage metrics
        """
        # Collect metrics first
        self._collect_resource_metrics()
        
        # Return resource-related metrics
        resource_metrics = {}
        for name, metric in self.metrics.items():
            if name.startswith("system.") or name.startswith("process."):
                resource_metrics[name] = metric.dict()
        
        return resource_metrics
    
    def _check_alert(self, metric_name: str, value: float):
        """
        Check if a metric exceeds its alert threshold.
        
        Args:
            metric_name: The name of the metric
            value: The current value
        """
        if metric_name not in self.alert_thresholds:
            return
        
        threshold_config = self.alert_thresholds[metric_name]
        threshold = threshold_config["threshold"]
        comparison = threshold_config["comparison"]
        duration = threshold_config["duration"]
        
        # Check if threshold is exceeded
        is_exceeded = False
        if comparison == "gt":
            is_exceeded = value > threshold
        elif comparison == "lt":
            is_exceeded = value < threshold
        elif comparison == "eq":
            is_exceeded = value == threshold
        elif comparison == "ne":
            is_exceeded = value != threshold
        elif comparison == "ge":
            is_exceeded = value >= threshold
        elif comparison == "le":
            is_exceeded = value <= threshold
        
        # Handle duration-based alerts
        if is_exceeded:
            if duration > 0:
                # If this is the first time it's exceeded, record the time
                if threshold_config["first_triggered"] is None:
                    threshold_config["first_triggered"] = time.time()
                
                # Check if it's been exceeded for the required duration
                elapsed = time.time() - threshold_config["first_triggered"]
                if elapsed >= duration:
                    self._trigger_alert(metric_name, value, threshold)
            else:
                # No duration requirement, trigger immediately
                self._trigger_alert(metric_name, value, threshold)
        else:
            # Reset the first triggered time
            threshold_config["first_triggered"] = None
    
    def _trigger_alert(self, metric_name: str, value: float, threshold: float):
        """
        Trigger an alert for a metric.
        
        Args:
            metric_name: The name of the metric
            value: The current value
            threshold: The threshold value
        """
        logger.warning(f"Alert: {metric_name} = {value} (threshold: {threshold})")
        
        for handler in self.alert_handlers:
            try:
                handler(metric_name, value, threshold)
            except Exception as e:
                logger.error(f"Error in alert handler: {str(e)}")

    # Decorators for timing functions and methods
    
    @staticmethod
    def time_function(metric_name: str = None, tags: Dict[str, str] = None):
        """
        Decorator to time a function and record the duration as a metric.
        
        Args:
            metric_name: The name of the metric (defaults to function name)
            tags: Additional tags for the metric
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Get the metric name
                name = metric_name or f"function.duration.{func.__name__}"
                
                # Start timer
                start_time = time.time()
                
                # Call the function
                result = func(*args, **kwargs)
                
                # End timer
                duration = time.time() - start_time
                
                # Record metric
                performance_monitor.record_metric(
                    name=name,
                    value=duration * 1000,  # Convert to ms
                    unit="ms",
                    tags=tags or {}
                )
                
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def time_async_function(metric_name: str = None, tags: Dict[str, str] = None):
        """
        Decorator to time an async function and record the duration as a metric.
        
        Args:
            metric_name: The name of the metric (defaults to function name)
            tags: Additional tags for the metric
        """
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # Get the metric name
                name = metric_name or f"function.duration.{func.__name__}"
                
                # Start timer
                start_time = time.time()
                
                # Call the function
                result = await func(*args, **kwargs)
                
                # End timer
                duration = time.time() - start_time
                
                # Record metric
                performance_monitor.record_metric(
                    name=name,
                    value=duration * 1000,  # Convert to ms
                    unit="ms",
                    tags=tags or {}
                )
                
                return result
            return wrapper
        return decorator

# Create a singleton instance
performance_monitor = PerformanceMonitor()