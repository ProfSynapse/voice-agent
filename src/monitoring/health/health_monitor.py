"""
Health Monitor Module

This module provides health check functionality for the Voice Agent application.
"""

import time
import asyncio
import logging
from typing import Dict, Any, List, Callable, Optional
import httpx
from fastapi import FastAPI, Request, Response, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class HealthCheckResult(BaseModel):
    """Model for health check results."""
    status: str
    components: Dict[str, Dict[str, Any]]
    timestamp: float
    version: str
    uptime: float

class HealthMonitor:
    """
    Health Monitor for the Voice Agent application.
    
    This class provides health check endpoints and functionality to monitor
    the health of the application and its dependencies.
    """
    
    def __init__(self):
        """Initialize the health monitor."""
        self.start_time = time.time()
        self.version = "1.0.0"
        self.dependencies = {}
        self.custom_checks = []
        self.is_healthy = True
        self.last_check_result = None
        self.check_interval = 60  # seconds
        self.alert_threshold = 3  # consecutive failures
        self.consecutive_failures = {}
        self.alert_handlers = []
        
    def register_with_app(self, app: FastAPI):
        """
        Register health check endpoints with the FastAPI application.
        
        Args:
            app: The FastAPI application
        """
        # Register the basic health check endpoint
        app.get("/health", response_model=HealthCheckResult)(self.health_check_handler)
        
        # Register the detailed health check endpoint
        app.get("/health/detailed", response_model=HealthCheckResult)(self.detailed_health_check_handler)
        
        # Register the component-specific health check endpoint
        app.get("/health/{component}", response_model=Dict)(self.component_health_check_handler)
        
        # Start the background health check task
        @app.on_event("startup")
        async def start_health_check_task():
            asyncio.create_task(self._background_health_check())
    
    def add_dependency(self, name: str, check_func: Callable[[], Dict[str, Any]]):
        """
        Add a dependency to be checked during health checks.
        
        Args:
            name: The name of the dependency
            check_func: A function that returns a dict with status information
        """
        self.dependencies[name] = check_func
        self.consecutive_failures[name] = 0
    
    def add_custom_check(self, name: str, check_func: Callable[[], Dict[str, Any]]):
        """
        Add a custom health check.
        
        Args:
            name: The name of the check
            check_func: A function that returns a dict with status information
        """
        self.custom_checks.append((name, check_func))
        self.consecutive_failures[name] = 0
    
    def add_alert_handler(self, handler: Callable[[str, Dict[str, Any]], None]):
        """
        Add an alert handler to be called when a health check fails.
        
        Args:
            handler: A function that takes a component name and status dict
        """
        self.alert_handlers.append(handler)
    
    async def health_check_handler(self, request: Request) -> HealthCheckResult:
        """
        Handle the basic health check endpoint.
        
        Args:
            request: The FastAPI request
            
        Returns:
            A HealthCheckResult with basic health information
        """
        if self.last_check_result and time.time() - self.last_check_result["timestamp"] < 10:
            # Return cached result if it's recent
            status_code = status.HTTP_200_OK if self.is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
            return Response(
                content=self.last_check_result,
                status_code=status_code,
                media_type="application/json"
            )
        
        # Perform a new health check
        result = await self._check_health(detailed=False)
        status_code = status.HTTP_200_OK if self.is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response(
            content=result,
            status_code=status_code,
            media_type="application/json"
        )
    
    async def detailed_health_check_handler(self, request: Request) -> HealthCheckResult:
        """
        Handle the detailed health check endpoint.
        
        Args:
            request: The FastAPI request
            
        Returns:
            A HealthCheckResult with detailed health information
        """
        result = await self._check_health(detailed=True)
        status_code = status.HTTP_200_OK if self.is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response(
            content=result,
            status_code=status_code,
            media_type="application/json"
        )
    
    async def component_health_check_handler(self, request: Request, component: str) -> Dict:
        """
        Handle the component-specific health check endpoint.
        
        Args:
            request: The FastAPI request
            component: The name of the component to check
            
        Returns:
            A dict with component-specific health information
        """
        result = await self._check_health(detailed=True)
        
        if component not in result["components"]:
            return Response(
                content={"error": f"Component {component} not found"},
                status_code=status.HTTP_404_NOT_FOUND,
                media_type="application/json"
            )
        
        component_status = result["components"][component]
        status_code = status.HTTP_200_OK if component_status["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response(
            content=component_status,
            status_code=status_code,
            media_type="application/json"
        )
    
    async def _check_health(self, detailed: bool = False) -> Dict[str, Any]:
        """
        Check the health of the application and its dependencies.
        
        Args:
            detailed: Whether to include detailed information
            
        Returns:
            A dict with health check results
        """
        components = {}
        all_healthy = True
        
        # Check dependencies
        for name, check_func in self.dependencies.items():
            try:
                result = await asyncio.to_thread(check_func)
                is_component_healthy = result.get("status") == "healthy"
                
                if not is_component_healthy:
                    all_healthy = False
                    self.consecutive_failures[name] += 1
                    if self.consecutive_failures[name] >= self.alert_threshold:
                        self._trigger_alert(name, result)
                else:
                    self.consecutive_failures[name] = 0
                
                components[name] = result
            except Exception as e:
                logger.error(f"Error checking dependency {name}: {str(e)}")
                all_healthy = False
                self.consecutive_failures[name] += 1
                if self.consecutive_failures[name] >= self.alert_threshold:
                    self._trigger_alert(name, {"status": "error", "error": str(e)})
                
                components[name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Check custom health checks
        for name, check_func in self.custom_checks:
            try:
                result = await asyncio.to_thread(check_func)
                is_component_healthy = result.get("status") == "healthy"
                
                if not is_component_healthy:
                    all_healthy = False
                    self.consecutive_failures[name] += 1
                    if self.consecutive_failures[name] >= self.alert_threshold:
                        self._trigger_alert(name, result)
                else:
                    self.consecutive_failures[name] = 0
                
                components[name] = result
            except Exception as e:
                logger.error(f"Error in custom health check {name}: {str(e)}")
                all_healthy = False
                self.consecutive_failures[name] += 1
                if self.consecutive_failures[name] >= self.alert_threshold:
                    self._trigger_alert(name, {"status": "error", "error": str(e)})
                
                components[name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Add application info
        components["application"] = {
            "status": "healthy",
            "uptime": time.time() - self.start_time
        }
        
        # Create the result
        result = {
            "status": "healthy" if all_healthy else "unhealthy",
            "components": components,
            "timestamp": time.time(),
            "version": self.version,
            "uptime": time.time() - self.start_time
        }
        
        # Add detailed information if requested
        if detailed:
            for name, component in components.items():
                if "details" in component and not component["details"]:
                    try:
                        if name in self.dependencies:
                            details = await asyncio.to_thread(self.dependencies[name], detailed=True)
                            components[name]["details"] = details
                    except Exception as e:
                        components[name]["details"] = {"error": str(e)}
        
        self.is_healthy = all_healthy
        self.last_check_result = result
        
        return result
    
    def _trigger_alert(self, component: str, status: Dict[str, Any]):
        """
        Trigger alerts for a failing component.
        
        Args:
            component: The name of the failing component
            status: The status information
        """
        logger.warning(f"Health check alert for {component}: {status}")
        
        for handler in self.alert_handlers:
            try:
                handler(component, status)
            except Exception as e:
                logger.error(f"Error in alert handler: {str(e)}")
    
    async def _background_health_check(self):
        """Background task to periodically check health."""
        while True:
            try:
                await self._check_health(detailed=True)
            except Exception as e:
                logger.error(f"Error in background health check: {str(e)}")
            
            await asyncio.sleep(self.check_interval)
    
    # Predefined health check functions for common dependencies
    
    @staticmethod
    async def check_supabase(client, detailed: bool = False) -> Dict[str, Any]:
        """
        Check Supabase health.
        
        Args:
            client: The Supabase client
            detailed: Whether to include detailed information
            
        Returns:
            A dict with health status
        """
        try:
            # Simple query to check if Supabase is accessible
            result = client.table("health_check").select("*").limit(1).execute()
            
            response = {
                "status": "healthy",
                "latency_ms": result.get("duration", 0)
            }
            
            if detailed:
                response["details"] = {
                    "query_result": result,
                    "connection_info": {
                        "url": client.base_url,
                        "auth_status": "authenticated" if client.auth.session() else "unauthenticated"
                    }
                }
            
            return response
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    @staticmethod
    async def check_livekit(url: str, detailed: bool = False) -> Dict[str, Any]:
        """
        Check LiveKit health.
        
        Args:
            url: The LiveKit server URL
            detailed: Whether to include detailed information
            
        Returns:
            A dict with health status
        """
        try:
            async with httpx.AsyncClient() as client:
                start_time = time.time()
                response = await client.get(f"{url}/health")
                latency = (time.time() - start_time) * 1000  # ms
                
                if response.status_code == 200:
                    result = {
                        "status": "healthy",
                        "latency_ms": latency
                    }
                    
                    if detailed:
                        result["details"] = {
                            "response": response.json(),
                            "status_code": response.status_code
                        }
                    
                    return result
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"HTTP {response.status_code}",
                        "response": response.text
                    }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    @staticmethod
    async def check_external_api(url: str, method: str = "GET", headers: Optional[Dict] = None, 
                          data: Optional[Dict] = None, timeout: float = 5.0,
                          expected_status: int = 200, detailed: bool = False) -> Dict[str, Any]:
        """
        Check an external API's health.
        
        Args:
            url: The API URL to check
            method: The HTTP method to use
            headers: Optional headers to include
            data: Optional data to send
            timeout: Request timeout in seconds
            expected_status: Expected HTTP status code
            detailed: Whether to include detailed information
            
        Returns:
            A dict with health status
        """
        try:
            async with httpx.AsyncClient() as client:
                start_time = time.time()
                
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, timeout=timeout)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=data, timeout=timeout)
                else:
                    return {
                        "status": "error",
                        "error": f"Unsupported method: {method}"
                    }
                
                latency = (time.time() - start_time) * 1000  # ms
                
                if response.status_code == expected_status:
                    result = {
                        "status": "healthy",
                        "latency_ms": latency
                    }
                    
                    if detailed:
                        try:
                            response_data = response.json()
                        except:
                            response_data = response.text
                            
                        result["details"] = {
                            "response": response_data,
                            "status_code": response.status_code,
                            "headers": dict(response.headers)
                        }
                    
                    return result
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"HTTP {response.status_code}",
                        "expected": expected_status,
                        "latency_ms": latency,
                        "response": response.text[:200] + "..." if len(response.text) > 200 else response.text
                    }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }