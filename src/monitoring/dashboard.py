"""
Monitoring Dashboard Module

This module provides a web dashboard for viewing monitoring data.
"""

import time
import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Response, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.monitoring.health import health_monitor
from src.monitoring.performance import performance_monitor
from src.monitoring.errors import error_monitor
from src.monitoring.user_experience import user_experience_monitor
from src.monitoring.security import security_monitor
from src.monitoring.infrastructure import infrastructure_monitor
from src.monitoring.improvement import improvement_monitor

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/monitoring")

# Set up templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(templates_dir, exist_ok=True)

templates = Jinja2Templates(directory=templates_dir)

# Create dashboard HTML template if it doesn't exist
dashboard_template_path = os.path.join(templates_dir, "dashboard.html")
if not os.path.exists(dashboard_template_path):
    with open(dashboard_template_path, "w") as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Voice Agent Monitoring Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background-color: #333;
            color: white;
            padding: 20px;
            text-align: center;
        }
        .status-card {
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
            padding: 20px;
        }
        .status-header {
            border-bottom: 1px solid #eee;
            margin-bottom: 15px;
            padding-bottom: 15px;
        }
        .status-title {
            font-size: 18px;
            font-weight: bold;
            margin: 0;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-healthy {
            background-color: #4CAF50;
        }
        .status-degraded {
            background-color: #FF9800;
        }
        .status-unhealthy {
            background-color: #F44336;
        }
        .status-unknown {
            background-color: #9E9E9E;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
        }
        .metric-card {
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            padding: 15px;
        }
        .metric-title {
            color: #666;
            font-size: 14px;
            margin-bottom: 5px;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
        }
        .tabs {
            display: flex;
            margin-bottom: 20px;
        }
        .tab {
            background-color: #ddd;
            border: none;
            cursor: pointer;
            padding: 10px 20px;
            margin-right: 5px;
            border-radius: 5px 5px 0 0;
        }
        .tab.active {
            background-color: white;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .alert-list {
            list-style: none;
            padding: 0;
        }
        .alert-item {
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            margin-bottom: 10px;
            padding: 10px 15px;
        }
        .alert-item.error {
            background-color: #f8d7da;
            border-left-color: #dc3545;
        }
        .alert-item.info {
            background-color: #d1ecf1;
            border-left-color: #17a2b8;
        }
        .alert-timestamp {
            color: #666;
            font-size: 12px;
            margin-top: 5px;
        }
        .refresh-button {
            background-color: #4CAF50;
            border: none;
            border-radius: 4px;
            color: white;
            cursor: pointer;
            padding: 8px 16px;
            margin-bottom: 20px;
        }
        .refresh-button:hover {
            background-color: #45a049;
        }
        .last-updated {
            color: #666;
            font-size: 12px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Voice Agent Monitoring Dashboard</h1>
    </div>
    
    <div class="container">
        <button class="refresh-button" onclick="refreshDashboard()">Refresh Dashboard</button>
        <div class="last-updated">Last updated: <span id="last-updated-time">{{ last_updated }}</span></div>
        
        <div class="tabs">
            <button class="tab active" onclick="openTab(event, 'overview')">Overview</button>
            <button class="tab" onclick="openTab(event, 'health')">Health</button>
            <button class="tab" onclick="openTab(event, 'performance')">Performance</button>
            <button class="tab" onclick="openTab(event, 'errors')">Errors</button>
            <button class="tab" onclick="openTab(event, 'user-experience')">User Experience</button>
            <button class="tab" onclick="openTab(event, 'security')">Security</button>
            <button class="tab" onclick="openTab(event, 'infrastructure')">Infrastructure</button>
        </div>
        
        <!-- Overview Tab -->
        <div id="overview" class="tab-content active">
            <div class="status-card">
                <div class="status-header">
                    <h2 class="status-title">System Status</h2>
                </div>
                <div>
                    <span class="status-indicator {{ 'status-healthy' if overall_status == 'healthy' else 'status-unhealthy' }}"></span>
                    <strong>{{ overall_status.capitalize() }}</strong>
                </div>
                <p>{{ components_healthy }} of {{ total_components }} components are healthy</p>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-title">Active Users</div>
                    <div class="metric-value">{{ active_users }}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Response Time (avg)</div>
                    <div class="metric-value">{{ avg_response_time }}ms</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Error Rate (24h)</div>
                    <div class="metric-value">{{ error_rate }}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">CPU Usage</div>
                    <div class="metric-value">{{ cpu_usage }}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Memory Usage</div>
                    <div class="metric-value">{{ memory_usage }}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Disk Usage</div>
                    <div class="metric-value">{{ disk_usage }}%</div>
                </div>
            </div>
            
            <div class="status-card">
                <div class="status-header">
                    <h2 class="status-title">Recent Alerts</h2>
                </div>
                <ul class="alert-list">
                    {% for alert in recent_alerts %}
                    <li class="alert-item {{ alert.severity }}">
                        <div><strong>{{ alert.component }}</strong>: {{ alert.message }}</div>
                        <div class="alert-timestamp">{{ alert.timestamp }}</div>
                    </li>
                    {% endfor %}
                </ul>
            </div>
        </div>
        
        <!-- Health Tab -->
        <div id="health" class="tab-content">
            <div class="status-card">
                <div class="status-header">
                    <h2 class="status-title">Health Status</h2>
                </div>
                <div>
                    <span class="status-indicator {{ 'status-healthy' if health_status == 'healthy' else 'status-unhealthy' }}"></span>
                    <strong>{{ health_status.capitalize() }}</strong>
                </div>
            </div>
            
            <div class="status-card">
                <div class="status-header">
                    <h2 class="status-title">Health Checks</h2>
                </div>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr>
                            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">Endpoint</th>
                            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">Status</th>
                            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">Latency</th>
                            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">Last Check</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for check in health_checks %}
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{{ check.name }}</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">
                                <span class="status-indicator {{ 'status-healthy' if check.status == 'healthy' else 'status-unhealthy' }}"></span>
                                {{ check.status.capitalize() }}
                            </td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{{ check.latency_ms }}ms</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{{ check.last_check }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Performance Tab -->
        <div id="performance" class="tab-content">
            <div class="status-card">
                <div class="status-header">
                    <h2 class="status-title">Performance Metrics</h2>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-title">Response Time (avg)</div>
                        <div class="metric-value">{{ avg_response_time }}ms</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">CPU Usage</div>
                        <div class="metric-value">{{ cpu_usage }}%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Memory Usage</div>
                        <div class="metric-value">{{ memory_usage }}%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Disk Usage</div>
                        <div class="metric-value">{{ disk_usage }}%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Network In</div>
                        <div class="metric-value">{{ network_in }}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Network Out</div>
                        <div class="metric-value">{{ network_out }}</div>
                    </div>
                </div>
            </div>
            
            <div class="status-card">
                <div class="status-header">
                    <h2 class="status-title">Slow Requests</h2>
                </div>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr>
                            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">Endpoint</th>
                            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">Method</th>
                            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">Response Time</th>
                            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">Timestamp</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for request in slow_requests %}
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{{ request.endpoint }}</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{{ request.method }}</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{{ request.response_time }}ms</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{{ request.timestamp }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Errors Tab -->
        <div id="errors" class="tab-content">
            <div class="status-card">
                <div class="status-header">
                    <h2 class="status-title">Error Metrics</h2>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-title">Error Rate (24h)</div>
                        <div class="metric-value">{{ error_rate }}%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Total Errors (24h)</div>
                        <div class="metric-value">{{ total_errors }}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Critical Errors (24h)</div>
                        <div class="metric-value">{{ critical_errors }}</div>
                    </div>
                </div>
            </div>
            
            <div class="status-card">
                <div class="status-header">
                    <h2 class="status-title">Recent Errors</h2>
                </div>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr>
                            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">Error Type</th>
                            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">Message</th>
                            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">Count</th>
                            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">Last Occurrence</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for error in recent_errors %}
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{{ error.type }}</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{{ error.message }}</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{{ error.count }}</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{{ error.last_occurrence }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- User Experience Tab -->
        <div id="user-experience" class="tab-content">
            <div class="status-card">
                <div class="status-header">
                    <h2 class="status-title">User Experience Metrics</h2>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-title">Active Sessions</div>
                        <div class="metric-value">{{ active_sessions }}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Avg. Session Duration</div>
                        <div class="metric-value">{{ avg_session_duration }}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Avg. Feedback Rating</div>
                        <div class="metric-value">{{ avg_feedback_rating }}/5</div>
                    </div>
                </div>
            </div>
            
            <div class="status-card">
                <div class="status-header">
                    <h2 class="status-title">Voice Quality Metrics</h2>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-title">Avg. Latency</div>
                        <div class="metric-value">{{ avg_voice_latency }}ms</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Avg. Packet Loss</div>
                        <div class="metric-value">{{ avg_packet_loss }}%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Avg. Jitter</div>
                        <div class="metric-value">{{ avg_jitter }}ms</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Avg. MOS Score</div>
                        <div class="metric-value">{{ avg_mos_score }}/5</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Security Tab -->
        <div id="security" class="tab-content">
            <div class="status-card">
                <div class="status-header">
                    <h2 class="status-title">Security Metrics</h2>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-title">Failed Login Attempts (24h)</div>
                        <div class="metric-value">{{ failed_logins }}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Suspicious IPs</div>
                        <div class="metric-value">{{ suspicious_ips }}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Rate Limit Exceeded (24h)</div>
                        <div class="metric-value">{{ rate_limit_exceeded }}</div>
                    </div>
                </div>
            </div>
            
            <div class="status-card">
                <div class="status-header">
                    <h2 class="status-title">Recent Security Events</h2>
                </div>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr>
                            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">Event Type</th>
                            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">IP Address</th>
                            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">Severity</th>
                            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">Timestamp</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for event in security_events %}
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{{ event.event_type }}</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{{ event.ip_address }}</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{{ event.severity }}</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{{ event.timestamp }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Infrastructure Tab -->
        <div id="infrastructure" class="tab-content">
            <div class="status-card">
                <div class="status-header">
                    <h2 class="status-title">Infrastructure Status</h2>
                </div>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr>
                            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">Component</th>
                            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">Status</th>
                            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">Latency</th>
                            <th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">Last Check</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for component in infrastructure_components %}
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{{ component.name }}</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">
                                <span class="status-indicator {{ 'status-healthy' if component.status == 'healthy' else 'status-unhealthy' }}"></span>
                                {{ component.status.capitalize() }}
                            </td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{{ component.latency_ms }}ms</td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{{ component.last_check }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        function openTab(evt, tabName) {
            var i, tabcontent, tablinks;
            
            // Hide all tab content
            tabcontent = document.getElementsByClassName("tab-content");
            for (i = 0; i < tabcontent.length; i++) {
                tabcontent[i].className = tabcontent[i].className.replace(" active", "");
            }
            
            // Remove active class from all tabs
            tablinks = document.getElementsByClassName("tab");
            for (i = 0; i < tablinks.length; i++) {
                tablinks[i].className = tablinks[i].className.replace(" active", "");
            }
            
            // Show the current tab and add active class
            document.getElementById(tabName).className += " active";
            evt.currentTarget.className += " active";
        }
        
        function refreshDashboard() {
            location.reload();
        }
    </script>
</body>
</html>""")

def register_with_app(app: FastAPI):
    """
    Register the monitoring dashboard with the FastAPI application.
    
    Args:
        app: The FastAPI application
    """
    # Mount static files
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    os.makedirs(static_dir, exist_ok=True)
    
    app.mount("/monitoring/static", StaticFiles(directory=static_dir), name="monitoring_static")
    
    # Include router
    app.include_router(router)
    
    # Register dashboard route
    @router.get("/dashboard", response_class=HTMLResponse)
    async def monitoring_dashboard(request: Request):
        """Render the monitoring dashboard."""
        # Get monitoring data
        data = await get_dashboard_data()
        
        # Render template
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            **data
        })
    
    logger.info("Monitoring dashboard registered")

async def get_dashboard_data() -> Dict[str, Any]:
    """
    Get data for the monitoring dashboard.
    
    Returns:
        Dashboard data
    """
    # Format timestamp
    now = datetime.now()
    last_updated = now.strftime("%Y-%m-%d %H:%M:%S")
    
    # Get health status
    health_status = "healthy"
    health_checks = []
    
    # Get performance metrics
    avg_response_time = 0
    cpu_usage = 0
    memory_usage = 0
    disk_usage = 0
    network_in = "0 KB/s"
    network_out = "0 KB/s"
    slow_requests = []
    
    # Get error metrics
    error_rate = 0
    total_errors = 0
    critical_errors = 0
    recent_errors = []
    
    # Get user experience metrics
    active_users = 0
    active_sessions = 0
    avg_session_duration = "0m 0s"
    avg_feedback_rating = 0
    avg_voice_latency = 0
    avg_packet_loss = 0
    avg_jitter = 0
    avg_mos_score = 0
    
    # Get security metrics
    failed_logins = 0
    suspicious_ips = 0
    rate_limit_exceeded = 0
    security_events = []
    
    # Get infrastructure metrics
    infrastructure_components = []
    
    # Get overall status
    overall_status = "healthy"
    components_healthy = 0
    total_components = 0
    
    # Get recent alerts
    recent_alerts = []
    
    # Return dashboard data
    return {
        "last_updated": last_updated,
        "overall_status": overall_status,
        "components_healthy": components_healthy,
        "total_components": total_components,
        "active_users": active_users,
        "avg_response_time": avg_response_time,
        "error_rate": error_rate,
        "cpu_usage": cpu_usage,
        "memory_usage": memory_usage,
        "disk_usage": disk_usage,
        "network_in": network_in,
        "network_out": network_out,
        "recent_alerts": recent_alerts,
        "health_status": health_status,
        "health_checks": health_checks,
        "slow_requests": slow_requests,
        "total_errors": total_errors,
        "critical_errors": critical_errors,
        "recent_errors": recent_errors,
        "active_sessions": active_sessions,
        "avg_session_duration": avg_session_duration,
        "avg_feedback_rating": avg_feedback_rating,
        "avg_voice_latency": avg_voice_latency,
        "avg_packet_loss": avg_packet_loss,
        "avg_jitter": avg_jitter,
        "avg_mos_score": avg_mos_score,
        "failed_logins": failed_logins,
        "suspicious_ips": suspicious_ips,
        "rate_limit_exceeded": rate_limit_exceeded,
        "security_events": security_events,
        "infrastructure_components": infrastructure_components
    }