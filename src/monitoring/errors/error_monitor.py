"""
Error Monitor Module

This module provides error tracking functionality for the Voice Agent application.
"""

import time
import logging
import traceback
import asyncio
import json
import os
import sys
from typing import Dict, Any, List, Callable, Optional, Union
from datetime import datetime, timedelta
from collections import deque, defaultdict
from fastapi import FastAPI, Request, Response, status
from pydantic import BaseModel
import functools

logger = logging.getLogger(__name__)

class ErrorEvent(BaseModel):
    """Model for error events."""
    error_id: str
    error_type: str
    message: str
    stack_trace: str
    timestamp: float
    context: Dict[str, Any] = {}
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    component: Optional[str] = None
    severity: str = "error"
    resolved: bool = False

class ErrorMonitor:
    """
    Error Monitor for the Voice Agent application.
    
    This class provides error tracking functionality to log, aggregate,
    and report errors in the application.
    """
    
    def __init__(self):
        """Initialize the error monitor."""
        self.errors = []
        self.error_counts = defaultdict(int)
        self.error_history = {}
        self.history_size = 1000  # Number of errors to keep per type
        self.alert_handlers = []
        self.error_thresholds = {}
        self.is_collecting = False
        self.collection_task = None
        self.error_log_path = "logs/errors"
        self.severity_levels = {
            "critical": 50,
            "error": 40,
            "warning": 30,
            "info": 20,
            "debug": 10
        }
        
        # Ensure log directory exists
        os.makedirs(self.error_log_path, exist_ok=True)
    
    def register_with_app(self, app: FastAPI):
        """
        Register error monitoring middleware and endpoints with the FastAPI application.
        
        Args:
            app: The FastAPI application
        """
        # Add middleware for error handling
        @app.middleware("http")
        async def error_middleware(request: Request, call_next):
            try:
                return await call_next(request)
            except Exception as e:
                # Log the error
                error_id = self.log_error(
                    error=e,
                    context={
                        "path": request.url.path,
                        "method": request.method,
                        "headers": dict(request.headers),
                        "client": request.client.host if request.client else None
                    }
                )
                
                # Return error response
                return Response(
                    content=json.dumps({
                        "error": str(e),
                        "error_id": error_id,
                        "timestamp": time.time()
                    }),
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    media_type="application/json"
                )
        
        # Register error endpoints
        @app.get("/errors")
        async def get_errors(limit: int = 100, severity: Optional[str] = None, 
                           component: Optional[str] = None, resolved: Optional[bool] = None):
            """Get recent errors with optional filtering."""
            filtered_errors = self.get_errors(limit, severity, component, resolved)
            return {
                "errors": filtered_errors,
                "count": len(filtered_errors),
                "timestamp": time.time()
            }
        
        @app.get("/errors/{error_id}")
        async def get_error_details(error_id: str):
            """Get details for a specific error."""
            error = self.get_error_by_id(error_id)
            if not error:
                return Response(
                    content=json.dumps({"error": f"Error {error_id} not found"}),
                    status_code=status.HTTP_404_NOT_FOUND,
                    media_type="application/json"
                )
            
            return error
        
        @app.post("/errors/{error_id}/resolve")
        async def resolve_error(error_id: str):
            """Mark an error as resolved."""
            if self.resolve_error(error_id):
                return {"status": "resolved", "error_id": error_id}
            else:
                return Response(
                    content=json.dumps({"error": f"Error {error_id} not found"}),
                    status_code=status.HTTP_404_NOT_FOUND,
                    media_type="application/json"
                )
        
        @app.get("/errors/stats")
        async def get_error_stats(time_period: str = "day"):
            """Get error statistics for a time period."""
            return self.get_error_stats(time_period)
        
        # Start the background error aggregation task
        @app.on_event("startup")
        async def start_error_task():
            self.start_collection()
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None, 
                 user_id: str = None, session_id: str = None, 
                 component: str = None, severity: str = "error") -> str:
        """
        Log an error event.
        
        Args:
            error: The exception that occurred
            context: Additional context information
            user_id: ID of the user who experienced the error
            session_id: ID of the user's session
            component: The component where the error occurred
            severity: Error severity level
            
        Returns:
            The generated error ID
        """
        # Generate error ID
        error_id = f"{int(time.time())}-{hash(str(error))}"
        
        # Create error event
        error_event = ErrorEvent(
            error_id=error_id,
            error_type=type(error).__name__,
            message=str(error),
            stack_trace=traceback.format_exc(),
            timestamp=time.time(),
            context=context or {},
            user_id=user_id,
            session_id=session_id,
            component=component,
            severity=severity
        )
        
        # Add to errors list
        self.errors.append(error_event)
        
        # Update error counts
        self.error_counts[error_event.error_type] += 1
        
        # Add to error history
        if error_event.error_type not in self.error_history:
            self.error_history[error_event.error_type] = deque(maxlen=self.history_size)
        
        self.error_history[error_event.error_type].append(error_event.dict())
        
        # Log to file
        self._log_to_file(error_event)
        
        # Check for alerts
        self._check_alert(error_event)
        
        # Log using standard logger
        log_level = self.severity_levels.get(severity, logging.ERROR)
        logger.log(log_level, f"Error {error_id}: {str(error)}")
        
        return error_id
    
    def get_errors(self, limit: int = 100, severity: Optional[str] = None, 
                  component: Optional[str] = None, resolved: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        Get recent errors with optional filtering.
        
        Args:
            limit: Maximum number of errors to return
            severity: Filter by severity level
            component: Filter by component
            resolved: Filter by resolved status
            
        Returns:
            A list of error events
        """
        filtered_errors = []
        
        for error in reversed(self.errors):  # Most recent first
            if severity and error.severity != severity:
                continue
                
            if component and error.component != component:
                continue
                
            if resolved is not None and error.resolved != resolved:
                continue
                
            filtered_errors.append(error.dict())
            
            if len(filtered_errors) >= limit:
                break
        
        return filtered_errors
    
    def get_error_by_id(self, error_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific error.
        
        Args:
            error_id: The error ID
            
        Returns:
            The error event or None if not found
        """
        for error in self.errors:
            if error.error_id == error_id:
                return error.dict()
        
        return None
    
    def resolve_error(self, error_id: str) -> bool:
        """
        Mark an error as resolved.
        
        Args:
            error_id: The error ID
            
        Returns:
            True if the error was found and resolved, False otherwise
        """
        for error in self.errors:
            if error.error_id == error_id:
                error.resolved = True
                return True
        
        return False
    
    def get_error_stats(self, time_period: str = "day") -> Dict[str, Any]:
        """
        Get error statistics for a time period.
        
        Args:
            time_period: The time period ("hour", "day", "week", "month")
            
        Returns:
            Error statistics
        """
        now = time.time()
        
        if time_period == "hour":
            cutoff = now - 3600
        elif time_period == "day":
            cutoff = now - 86400
        elif time_period == "week":
            cutoff = now - 604800
        elif time_period == "month":
            cutoff = now - 2592000
        else:
            cutoff = now - 86400  # Default to day
        
        # Count errors by type and severity
        type_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        component_counts = defaultdict(int)
        total_count = 0
        resolved_count = 0
        
        for error in self.errors:
            if error.timestamp >= cutoff:
                type_counts[error.error_type] += 1
                severity_counts[error.severity] += 1
                
                if error.component:
                    component_counts[error.component] += 1
                    
                total_count += 1
                
                if error.resolved:
                    resolved_count += 1
        
        return {
            "time_period": time_period,
            "total_errors": total_count,
            "resolved_errors": resolved_count,
            "by_type": dict(type_counts),
            "by_severity": dict(severity_counts),
            "by_component": dict(component_counts),
            "timestamp": now
        }
    
    def set_error_threshold(self, error_type: str, threshold: int, 
                           time_period: int = 3600, severity: str = "error"):
        """
        Set a threshold for alerting on error frequency.
        
        Args:
            error_type: The type of error to monitor
            threshold: Number of errors to trigger alert
            time_period: Time period in seconds
            severity: Minimum severity level
        """
        self.error_thresholds[error_type] = {
            "threshold": threshold,
            "time_period": time_period,
            "severity": severity
        }
    
    def add_alert_handler(self, handler: Callable[[ErrorEvent], None]):
        """
        Add an alert handler to be called when an error threshold is exceeded.
        
        Args:
            handler: A function that takes an error event
        """
        self.alert_handlers.append(handler)
    
    def start_collection(self):
        """Start the background error aggregation task."""
        if not self.is_collecting:
            self.is_collecting = True
            self.collection_task = asyncio.create_task(self._aggregate_errors())
    
    def stop_collection(self):
        """Stop the background error aggregation task."""
        self.is_collecting = False
        if self.collection_task:
            self.collection_task.cancel()
    
    def _log_to_file(self, error_event: ErrorEvent):
        """
        Log an error event to a file.
        
        Args:
            error_event: The error event to log
        """
        try:
            # Create filename based on date
            date_str = datetime.fromtimestamp(error_event.timestamp).strftime("%Y-%m-%d")
            filename = os.path.join(self.error_log_path, f"errors-{date_str}.log")
            
            # Write error to file
            with open(filename, "a") as f:
                f.write(json.dumps(error_event.dict()) + "\n")
        except Exception as e:
            logger.error(f"Failed to log error to file: {str(e)}")
    
    async def _aggregate_errors(self):
        """Background task to aggregate errors and check thresholds."""
        while self.is_collecting:
            try:
                now = time.time()
                
                # Check error thresholds
                for error_type, config in self.error_thresholds.items():
                    threshold = config["threshold"]
                    time_period = config["time_period"]
                    severity = config["severity"]
                    
                    # Count errors in the time period
                    count = 0
                    for error in self.errors:
                        if (error.error_type == error_type and 
                            error.timestamp >= now - time_period and
                            self.severity_levels.get(error.severity, 0) >= 
                            self.severity_levels.get(severity, 0)):
                            count += 1
                    
                    # Trigger alert if threshold exceeded
                    if count >= threshold:
                        self._trigger_threshold_alert(error_type, count, threshold, time_period)
            
            except Exception as e:
                logger.error(f"Error in error aggregation task: {str(e)}")
            
            await asyncio.sleep(60)  # Check every minute
    
    def _check_alert(self, error_event: ErrorEvent):
        """
        Check if an error should trigger an alert.
        
        Args:
            error_event: The error event to check
        """
        # Always alert on critical errors
        if error_event.severity == "critical":
            self._trigger_alert(error_event)
            return
        
        # Check error thresholds
        if error_event.error_type in self.error_thresholds:
            config = self.error_thresholds[error_event.error_type]
            severity = config["severity"]
            
            # Alert if severity matches
            if self.severity_levels.get(error_event.severity, 0) >= self.severity_levels.get(severity, 0):
                self._trigger_alert(error_event)
    
    def _trigger_alert(self, error_event: ErrorEvent):
        """
        Trigger an alert for an error.
        
        Args:
            error_event: The error event that triggered the alert
        """
        logger.warning(f"Error alert: {error_event.error_type} - {error_event.message}")
        
        for handler in self.alert_handlers:
            try:
                handler(error_event)
            except Exception as e:
                logger.error(f"Error in alert handler: {str(e)}")
    
    def _trigger_threshold_alert(self, error_type: str, count: int, threshold: int, time_period: int):
        """
        Trigger an alert for an error threshold.
        
        Args:
            error_type: The type of error
            count: Current error count
            threshold: Threshold value
            time_period: Time period in seconds
        """
        logger.warning(f"Error threshold alert: {error_type} - {count} errors in {time_period/60:.1f} minutes (threshold: {threshold})")
        
        # Create a synthetic error event for the threshold
        error_event = ErrorEvent(
            error_id=f"threshold-{int(time.time())}-{error_type}",
            error_type="ThresholdExceeded",
            message=f"Error threshold exceeded for {error_type}: {count} errors in {time_period/60:.1f} minutes (threshold: {threshold})",
            stack_trace="",
            timestamp=time.time(),
            context={
                "error_type": error_type,
                "count": count,
                "threshold": threshold,
                "time_period": time_period
            },
            severity="warning"
        )
        
        for handler in self.alert_handlers:
            try:
                handler(error_event)
            except Exception as e:
                logger.error(f"Error in alert handler: {str(e)}")

    # Decorators for catching errors in functions and methods
    
    @staticmethod
    def catch_errors(component: str = None, severity: str = "error"):
        """
        Decorator to catch and log errors in a function.
        
        Args:
            component: The component name
            severity: Error severity level
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_monitor.log_error(
                        error=e,
                        component=component or func.__module__,
                        severity=severity
                    )
                    raise
            return wrapper
        return decorator
    
    @staticmethod
    def catch_async_errors(component: str = None, severity: str = "error"):
        """
        Decorator to catch and log errors in an async function.
        
        Args:
            component: The component name
            severity: Error severity level
        """
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    error_monitor.log_error(
                        error=e,
                        component=component or func.__module__,
                        severity=severity
                    )
                    raise
            return wrapper
        return decorator

# Create a singleton instance
error_monitor = ErrorMonitor()