"""
Infrastructure Monitor Module

This module provides infrastructure monitoring functionality for the Voice Agent application.
"""

import time
import logging
import json
import os
import asyncio
import httpx
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from collections import deque, defaultdict
from fastapi import FastAPI
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class InfrastructureStatus(BaseModel):
    """Model for infrastructure status."""
    component: str
    status: str  # "healthy", "degraded", "unhealthy"
    latency_ms: Optional[float] = None
    last_check: float
    details: Dict[str, Any] = {}
    error: Optional[str] = None

class DependencyCheck(BaseModel):
    """Model for dependency check configuration."""
    name: str
    check_type: str  # "http", "supabase", "livekit", "railway", "custom"
    endpoint: Optional[str] = None
    method: str = "GET"
    headers: Dict[str, str] = {}
    body: Optional[Dict[str, Any]] = None
    expected_status: int = 200
    timeout: float = 5.0
    check_interval: int = 60  # seconds
    custom_check: Optional[Callable[[], Dict[str, Any]]] = None

class InfrastructureMonitor:
    """
    Infrastructure Monitor for the Voice Agent application.
    
    This class provides infrastructure monitoring functionality to track
    Railway deployment, Supabase performance, LiveKit service availability,
    and dependency health checks.
    """
    
    def __init__(self):
        """Initialize the infrastructure monitor."""
        self.component_status = {}
        self.status_history = defaultdict(lambda: deque(maxlen=1000))
        self.dependencies = {}
        self.check_tasks = {}
        self.alert_handlers = []
        self.data_dir = "data/infrastructure"
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
    
    def register_with_app(self, app: FastAPI):
        """
        Register infrastructure monitoring endpoints with the FastAPI application.
        
        Args:
            app: The FastAPI application
        """
        # Register infrastructure status endpoint
        @app.get("/infrastructure/status")
        async def get_infrastructure_status():
            """Get the current status of all infrastructure components."""
            return {
                "status": "healthy" if self._is_healthy() else "unhealthy",
                "components": self.component_status,
                "timestamp": time.time()
            }
        
        # Register component status endpoint
        @app.get("/infrastructure/status/{component}")
        async def get_component_status(component: str):
            """Get the status of a specific component."""
            if component not in self.component_status:
                return {"error": f"Component {component} not found"}
            
            return self.component_status[component]
        
        # Register component history endpoint
        @app.get("/infrastructure/history/{component}")
        async def get_component_history(component: str, limit: int = 100):
            """Get the status history of a specific component."""
            if component not in self.status_history:
                return {"error": f"Component {component} not found"}
            
            history = list(self.status_history[component])[-limit:]
            return {
                "component": component,
                "history": history,
                "count": len(history)
            }
        
        # Start the background check tasks
        @app.on_event("startup")
        async def start_check_tasks():
            await self.start_all_checks()
        
        # Stop the background check tasks
        @app.on_event("shutdown")
        async def stop_check_tasks():
            self.stop_all_checks()
    
    def add_dependency(self, dependency: DependencyCheck):
        """
        Add a dependency to monitor.
        
        Args:
            dependency: The dependency check configuration
        """
        self.dependencies[dependency.name] = dependency
        logger.info(f"Added dependency: {dependency.name}")
    
    def add_http_dependency(self, name: str, endpoint: str, method: str = "GET",
                           headers: Dict[str, str] = None, body: Dict[str, Any] = None,
                           expected_status: int = 200, timeout: float = 5.0,
                           check_interval: int = 60):
        """
        Add an HTTP dependency to monitor.
        
        Args:
            name: The name of the dependency
            endpoint: The HTTP endpoint to check
            method: The HTTP method to use
            headers: The HTTP headers to include
            body: The request body for POST requests
            expected_status: The expected HTTP status code
            timeout: The request timeout in seconds
            check_interval: How often to check the dependency in seconds
        """
        dependency = DependencyCheck(
            name=name,
            check_type="http",
            endpoint=endpoint,
            method=method,
            headers=headers or {},
            body=body,
            expected_status=expected_status,
            timeout=timeout,
            check_interval=check_interval
        )
        
        self.add_dependency(dependency)
    
    def add_supabase_dependency(self, name: str, endpoint: str, api_key: str,
                               check_interval: int = 60):
        """
        Add a Supabase dependency to monitor.
        
        Args:
            name: The name of the dependency
            endpoint: The Supabase endpoint
            api_key: The Supabase API key
            check_interval: How often to check the dependency in seconds
        """
        headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}"
        }
        
        dependency = DependencyCheck(
            name=name,
            check_type="supabase",
            endpoint=f"{endpoint}/rest/v1/health",
            method="GET",
            headers=headers,
            expected_status=200,
            timeout=5.0,
            check_interval=check_interval
        )
        
        self.add_dependency(dependency)
    
    def add_livekit_dependency(self, name: str, endpoint: str, check_interval: int = 60):
        """
        Add a LiveKit dependency to monitor.
        
        Args:
            name: The name of the dependency
            endpoint: The LiveKit endpoint
            check_interval: How often to check the dependency in seconds
        """
        dependency = DependencyCheck(
            name=name,
            check_type="livekit",
            endpoint=f"{endpoint}/health",
            method="GET",
            expected_status=200,
            timeout=5.0,
            check_interval=check_interval
        )
        
        self.add_dependency(dependency)
    
    def add_railway_dependency(self, name: str, project_id: str, api_key: str,
                              check_interval: int = 60):
        """
        Add a Railway deployment to monitor.
        
        Args:
            name: The name of the dependency
            project_id: The Railway project ID
            api_key: The Railway API key
            check_interval: How often to check the dependency in seconds
        """
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        dependency = DependencyCheck(
            name=name,
            check_type="railway",
            endpoint=f"https://backboard.railway.app/graphql/v2",
            method="POST",
            headers=headers,
            body={
                "query": """
                query GetProject($id: String!) {
                    project(id: $id) {
                        id
                        name
                        deployments {
                            nodes {
                                id
                                status
                                createdAt
                            }
                        }
                    }
                }
                """,
                "variables": {
                    "id": project_id
                }
            },
            expected_status=200,
            timeout=10.0,
            check_interval=check_interval
        )
        
        self.add_dependency(dependency)
    
    def add_custom_dependency(self, name: str, check_func: Callable[[], Dict[str, Any]],
                             check_interval: int = 60):
        """
        Add a custom dependency check.
        
        Args:
            name: The name of the dependency
            check_func: A function that performs the check and returns a dict
            check_interval: How often to check the dependency in seconds
        """
        dependency = DependencyCheck(
            name=name,
            check_type="custom",
            custom_check=check_func,
            check_interval=check_interval
        )
        
        self.add_dependency(dependency)
    
    def add_alert_handler(self, handler: Callable[[InfrastructureStatus], None]):
        """
        Add an alert handler to be called when a component status changes.
        
        Args:
            handler: A function that takes an InfrastructureStatus object
        """
        self.alert_handlers.append(handler)
    
    async def start_all_checks(self):
        """Start all dependency check tasks."""
        for name, dependency in self.dependencies.items():
            await self.start_check(name)
    
    async def start_check(self, name: str):
        """
        Start a dependency check task.
        
        Args:
            name: The name of the dependency
        """
        if name not in self.dependencies:
            logger.error(f"Dependency {name} not found")
            return
        
        if name in self.check_tasks and not self.check_tasks[name].done():
            logger.warning(f"Check task for {name} is already running")
            return
        
        dependency = self.dependencies[name]
        self.check_tasks[name] = asyncio.create_task(self._check_dependency_loop(dependency))
        logger.info(f"Started check task for {name}")
    
    def stop_all_checks(self):
        """Stop all dependency check tasks."""
        for name in self.check_tasks:
            self.stop_check(name)
    
    def stop_check(self, name: str):
        """
        Stop a dependency check task.
        
        Args:
            name: The name of the dependency
        """
        if name in self.check_tasks and not self.check_tasks[name].done():
            self.check_tasks[name].cancel()
            logger.info(f"Stopped check task for {name}")
    
    async def _check_dependency_loop(self, dependency: DependencyCheck):
        """
        Background task to check a dependency periodically.
        
        Args:
            dependency: The dependency check configuration
        """
        while True:
            try:
                await self._check_dependency(dependency)
            except asyncio.CancelledError:
                logger.info(f"Check task for {dependency.name} cancelled")
                break
            except Exception as e:
                logger.error(f"Error in check task for {dependency.name}: {str(e)}")
            
            await asyncio.sleep(dependency.check_interval)
    
    async def _check_dependency(self, dependency: DependencyCheck):
        """
        Check a dependency and update its status.
        
        Args:
            dependency: The dependency check configuration
        """
        start_time = time.time()
        error = None
        details = {}
        status = "healthy"
        
        try:
            if dependency.check_type == "http":
                result = await self._check_http(
                    endpoint=dependency.endpoint,
                    method=dependency.method,
                    headers=dependency.headers,
                    body=dependency.body,
                    expected_status=dependency.expected_status,
                    timeout=dependency.timeout
                )
                details = result.get("details", {})
                status = "healthy" if result.get("status") == "healthy" else "unhealthy"
                error = result.get("error")
            
            elif dependency.check_type == "supabase":
                result = await self._check_supabase(
                    endpoint=dependency.endpoint,
                    headers=dependency.headers,
                    timeout=dependency.timeout
                )
                details = result.get("details", {})
                status = "healthy" if result.get("status") == "healthy" else "unhealthy"
                error = result.get("error")
            
            elif dependency.check_type == "livekit":
                result = await self._check_livekit(
                    endpoint=dependency.endpoint,
                    timeout=dependency.timeout
                )
                details = result.get("details", {})
                status = "healthy" if result.get("status") == "healthy" else "unhealthy"
                error = result.get("error")
            
            elif dependency.check_type == "railway":
                result = await self._check_railway(
                    endpoint=dependency.endpoint,
                    headers=dependency.headers,
                    body=dependency.body,
                    timeout=dependency.timeout
                )
                details = result.get("details", {})
                status = "healthy" if result.get("status") == "healthy" else "unhealthy"
                error = result.get("error")
            
            elif dependency.check_type == "custom":
                if dependency.custom_check:
                    result = await asyncio.to_thread(dependency.custom_check)
                    details = result.get("details", {})
                    status = result.get("status", "healthy")
                    error = result.get("error")
                else:
                    status = "unhealthy"
                    error = "No custom check function provided"
            
            else:
                status = "unhealthy"
                error = f"Unknown check type: {dependency.check_type}"
        
        except Exception as e:
            status = "unhealthy"
            error = str(e)
            logger.error(f"Error checking {dependency.name}: {error}")
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Create status object
        infra_status = InfrastructureStatus(
            component=dependency.name,
            status=status,
            latency_ms=latency_ms,
            last_check=time.time(),
            details=details,
            error=error
        )
        
        # Update status
        self._update_status(infra_status)
    
    async def _check_http(self, endpoint: str, method: str = "GET",
                         headers: Dict[str, str] = None, body: Dict[str, Any] = None,
                         expected_status: int = 200, timeout: float = 5.0) -> Dict[str, Any]:
        """
        Check an HTTP endpoint.
        
        Args:
            endpoint: The HTTP endpoint to check
            method: The HTTP method to use
            headers: The HTTP headers to include
            body: The request body for POST requests
            expected_status: The expected HTTP status code
            timeout: The request timeout in seconds
            
        Returns:
            A dict with the check result
        """
        try:
            async with httpx.AsyncClient() as client:
                if method.upper() == "GET":
                    response = await client.get(
                        endpoint,
                        headers=headers,
                        timeout=timeout
                    )
                elif method.upper() == "POST":
                    response = await client.post(
                        endpoint,
                        headers=headers,
                        json=body,
                        timeout=timeout
                    )
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"Unsupported method: {method}"
                    }
                
                if response.status_code == expected_status:
                    try:
                        response_data = response.json()
                    except:
                        response_data = response.text
                    
                    return {
                        "status": "healthy",
                        "details": {
                            "status_code": response.status_code,
                            "response": response_data
                        }
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"Unexpected status code: {response.status_code} (expected {expected_status})",
                        "details": {
                            "status_code": response.status_code,
                            "response": response.text
                        }
                    }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_supabase(self, endpoint: str, headers: Dict[str, str],
                             timeout: float = 5.0) -> Dict[str, Any]:
        """
        Check a Supabase endpoint.
        
        Args:
            endpoint: The Supabase endpoint
            headers: The HTTP headers with API key
            timeout: The request timeout in seconds
            
        Returns:
            A dict with the check result
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    endpoint,
                    headers=headers,
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "details": {
                            "status_code": response.status_code,
                            "response": response.json()
                        }
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"Unexpected status code: {response.status_code}",
                        "details": {
                            "status_code": response.status_code,
                            "response": response.text
                        }
                    }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_livekit(self, endpoint: str, timeout: float = 5.0) -> Dict[str, Any]:
        """
        Check a LiveKit endpoint.
        
        Args:
            endpoint: The LiveKit health endpoint
            timeout: The request timeout in seconds
            
        Returns:
            A dict with the check result
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    endpoint,
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "details": {
                            "status_code": response.status_code,
                            "response": response.json()
                        }
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"Unexpected status code: {response.status_code}",
                        "details": {
                            "status_code": response.status_code,
                            "response": response.text
                        }
                    }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_railway(self, endpoint: str, headers: Dict[str, str],
                            body: Dict[str, Any], timeout: float = 10.0) -> Dict[str, Any]:
        """
        Check a Railway deployment.
        
        Args:
            endpoint: The Railway GraphQL endpoint
            headers: The HTTP headers with API key
            body: The GraphQL query
            timeout: The request timeout in seconds
            
        Returns:
            A dict with the check result
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    headers=headers,
                    json=body,
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "errors" in data:
                        return {
                            "status": "unhealthy",
                            "error": str(data["errors"]),
                            "details": {
                                "status_code": response.status_code,
                                "response": data
                            }
                        }
                    
                    project = data.get("data", {}).get("project")
                    if not project:
                        return {
                            "status": "unhealthy",
                            "error": "Project not found",
                            "details": {
                                "status_code": response.status_code,
                                "response": data
                            }
                        }
                    
                    deployments = project.get("deployments", {}).get("nodes", [])
                    if not deployments:
                        return {
                            "status": "unhealthy",
                            "error": "No deployments found",
                            "details": {
                                "status_code": response.status_code,
                                "response": data
                            }
                        }
                    
                    # Check if the latest deployment is healthy
                    latest = deployments[0]
                    if latest["status"] != "SUCCESS":
                        return {
                            "status": "unhealthy",
                            "error": f"Latest deployment status: {latest['status']}",
                            "details": {
                                "status_code": response.status_code,
                                "deployment": latest,
                                "response": data
                            }
                        }
                    
                    return {
                        "status": "healthy",
                        "details": {
                            "status_code": response.status_code,
                            "deployment": latest,
                            "response": data
                        }
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"Unexpected status code: {response.status_code}",
                        "details": {
                            "status_code": response.status_code,
                            "response": response.text
                        }
                    }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def _update_status(self, status: InfrastructureStatus):
        """
        Update the status of a component.
        
        Args:
            status: The new status
        """
        # Get previous status
        prev_status = self.component_status.get(status.component)
        
        # Update status
        self.component_status[status.component] = status.dict()
        
        # Add to history
        self.status_history[status.component].append(status.dict())
        
        # Save to file
        self._save_status(status)
        
        # Check if status changed
        if prev_status and prev_status["status"] != status.status:
            # Log status change
            if status.status == "healthy":
                logger.info(f"Component {status.component} is now healthy")
            else:
                logger.warning(f"Component {status.component} is now {status.status}: {status.error}")
            
            # Trigger alerts if status degraded
            if status.status != "healthy":
                self._trigger_alert(status)
    
    def _is_healthy(self) -> bool:
        """
        Check if all components are healthy.
        
        Returns:
            True if all components are healthy, False otherwise
        """
        return all(s["status"] == "healthy" for s in self.component_status.values())
    
    def _trigger_alert(self, status: InfrastructureStatus):
        """
        Trigger an alert for a component status change.
        
        Args:
            status: The component status
        """
        for handler in self.alert_handlers:
            try:
                handler(status)
            except Exception as e:
                logger.error(f"Error in alert handler: {str(e)}")
    
    def _save_status(self, status: InfrastructureStatus):
        """
        Save a component status to a file.
        
        Args:
            status: The component status
        """
        try:
            # Create filename based on date
            date_str = datetime.fromtimestamp(status.last_check).strftime("%Y-%m-%d")
            filename = os.path.join(self.data_dir, f"infrastructure-{date_str}.jsonl")
            
            # Write status to file
            with open(filename, "a") as f:
                f.write(json.dumps(status.dict()) + "\n")
        except Exception as e:
            logger.error(f"Failed to save infrastructure status to file: {str(e)}")

# Create a singleton instance
infrastructure_monitor = InfrastructureMonitor()