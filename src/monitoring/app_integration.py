"""
Monitoring App Integration Example

This module demonstrates how to integrate the monitoring system with the main application.
"""

import os
import logging
from fastapi import FastAPI, Request, Response
from typing import Dict, Any, Optional

from src.monitoring.integration import configure_monitoring
from src.monitoring.health import health_monitor
from src.monitoring.performance import performance_monitor
from src.monitoring.errors import error_monitor
from src.monitoring.user_experience import user_experience_monitor
from src.monitoring.security import security_monitor
from src.monitoring.infrastructure import infrastructure_monitor
from src.monitoring.improvement import improvement_monitor

logger = logging.getLogger(__name__)

def setup_voice_agent_monitoring(app: FastAPI):
    """
    Set up monitoring for the Voice Agent application.
    
    This function configures the monitoring system with Voice Agent-specific settings.
    
    Args:
        app: The FastAPI application
    """
    logger.info("Setting up Voice Agent monitoring...")
    
    # Configure monitoring with Voice Agent-specific settings
    config = _get_voice_agent_monitoring_config()
    
    # Configure monitoring
    configure_monitoring(app, config)
    
    # Add custom middleware for request tracking
    @app.middleware("http")
    async def monitoring_middleware(request: Request, call_next):
        """Middleware for tracking requests and errors."""
        # Start timer for performance tracking
        import time
        start_time = time.time()
        
        # Get client info
        client_host = request.client.host if request.client else None
        
        # Process request and catch exceptions
        try:
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Track request performance
            performance_monitor.track_request(
                endpoint=request.url.path,
                method=request.method,
                response_time=response_time,
                status_code=response.status_code
            )
            
            # Track API usage for security monitoring
            security_monitor.track_api_usage(
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                response_time=response_time,
                user_id=request.cookies.get("user_id"),
                ip_address=client_host
            )
            
            return response
            
        except Exception as e:
            # Track error
            error_monitor.track_error(
                error_type=type(e).__name__,
                message=str(e),
                stack_trace=_get_stack_trace(),
                request_path=request.url.path,
                request_method=request.method,
                user_id=request.cookies.get("user_id"),
                ip_address=client_host
            )
            
            # Re-raise the exception
            raise
    
    # Set up LiveKit voice quality monitoring
    _setup_livekit_monitoring()
    
    # Set up Supabase monitoring
    _setup_supabase_monitoring()
    
    # Set up Railway monitoring
    _setup_railway_monitoring()
    
    # Set up custom health checks
    _setup_custom_health_checks()
    
    logger.info("Voice Agent monitoring setup complete")
    
    return app

def _get_voice_agent_monitoring_config() -> Dict[str, Any]:
    """
    Get the Voice Agent monitoring configuration.
    
    Returns:
        The monitoring configuration
    """
    return {
        "health": {
            "endpoints": [
                {
                    "name": "api",
                    "url": "/api/health",
                    "method": "GET",
                    "expected_status": 200,
                    "timeout": 5.0,
                    "check_interval": 60
                }
            ],
            "thresholds": {
                "cpu_usage": 80,
                "memory_usage": 80,
                "disk_usage": 80
            }
        },
        "performance": {
            "slow_request_threshold": 1.0,  # 1 second
            "memory_warning_threshold": 80,  # 80%
            "cpu_warning_threshold": 80  # 80%
        },
        "errors": {
            "error_sample_rate": 1.0,  # Sample all errors
            "ignored_errors": ["NotFoundError"]  # Ignore 404 errors
        },
        "security": {
            "max_failed_logins": 5,
            "failed_login_window": 300,  # 5 minutes
            "rate_limits": {
                "/api/auth/login": {
                    "limit": 10,
                    "window": 60  # 10 requests per minute
                },
                "/api/auth/register": {
                    "limit": 5,
                    "window": 60  # 5 requests per minute
                }
            }
        }
    }

def _setup_livekit_monitoring():
    """Set up LiveKit voice quality monitoring."""
    # Add LiveKit dependency
    livekit_url = os.environ.get("LIVEKIT_URL")
    if livekit_url:
        infrastructure_monitor.add_livekit_dependency(
            name="livekit",
            endpoint=livekit_url,
            check_interval=60
        )
    
    # Add custom voice quality monitoring
    def track_voice_quality(conversation_id, metrics):
        """Track voice quality metrics from LiveKit."""
        user_experience_monitor.record_voice_quality(
            conversation_id=conversation_id,
            latency_ms=metrics.get("latency_ms", 0),
            packet_loss=metrics.get("packet_loss", 0),
            jitter_ms=metrics.get("jitter_ms", 0),
            audio_level=metrics.get("audio_level", 0),
            noise_level=metrics.get("noise_level", 0),
            mos_score=metrics.get("mos_score")
        )
    
    # This function would be called by the LiveKit client
    # when voice quality metrics are available
    
    # Example of how to use it:
    # track_voice_quality("conversation_123", {
    #     "latency_ms": 50,
    #     "packet_loss": 0.1,
    #     "jitter_ms": 5,
    #     "audio_level": 0.8,
    #     "noise_level": 0.1,
    #     "mos_score": 4.5
    # })

def _setup_supabase_monitoring():
    """Set up Supabase monitoring."""
    # Add Supabase dependency
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_API_KEY")
    
    if supabase_url and supabase_key:
        infrastructure_monitor.add_supabase_dependency(
            name="supabase",
            endpoint=supabase_url,
            api_key=supabase_key,
            check_interval=60
        )
    
    # Add custom database connection pool monitoring
    def check_db_connection_pool():
        """Check database connection pool health."""
        # This would be replaced with actual code to check the connection pool
        return {
            "status": "healthy",
            "details": {
                "active_connections": 0,  # Replace with actual value
                "idle_connections": 0,  # Replace with actual value
                "max_connections": 20
            }
        }
    
    infrastructure_monitor.add_custom_dependency(
        name="database-connection-pool",
        check_func=check_db_connection_pool,
        check_interval=30
    )

def _setup_railway_monitoring():
    """Set up Railway monitoring."""
    # Add Railway dependency
    railway_project_id = os.environ.get("RAILWAY_PROJECT_ID")
    railway_api_key = os.environ.get("RAILWAY_API_KEY")
    
    if railway_project_id and railway_api_key:
        infrastructure_monitor.add_railway_dependency(
            name="railway-deployment",
            project_id=railway_project_id,
            api_key=railway_api_key,
            check_interval=300  # Check every 5 minutes
        )

def _setup_custom_health_checks():
    """Set up custom health checks."""
    # Add custom health check for voice processing
    def check_voice_processing():
        """Check voice processing health."""
        # This would be replaced with actual code to check voice processing
        return {
            "status": "healthy",
            "details": {
                "active_conversations": 0,  # Replace with actual value
                "processing_latency_ms": 50  # Replace with actual value
            }
        }
    
    health_monitor.add_custom_health_check(
        name="voice-processing",
        check_func=check_voice_processing,
        check_interval=30
    )

def _get_stack_trace() -> str:
    """
    Get the current stack trace.
    
    Returns:
        The stack trace as a string
    """
    import traceback
    return "".join(traceback.format_stack())

# Example of how to use this in app.py:
"""
from fastapi import FastAPI
from src.monitoring.app_integration import setup_voice_agent_monitoring

app = FastAPI()

# Set up monitoring
setup_voice_agent_monitoring(app)

# Rest of your application code...
"""