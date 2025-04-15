# Voice Agent Monitoring System

This comprehensive monitoring system provides post-deployment monitoring for the Voice Agent application. It includes health checks, performance monitoring, error tracking, user experience monitoring, security monitoring, infrastructure monitoring, and continuous improvement frameworks.

## Features

### 1. Application Health Monitoring
- Health check endpoints for all critical services
- Uptime monitoring with alerting
- Application startup and initialization monitoring
- Dependency health checks

### 2. Performance Monitoring
- Response time tracking for all endpoints
- Voice processing latency monitoring
- Database query performance tracking
- Resource usage monitoring (CPU, memory, network)
- Slow request identification and alerting

### 3. Error Tracking
- Comprehensive error logging
- Error aggregation and reporting
- Error dashboards
- Critical error alerting

### 4. User Experience Monitoring
- User session metrics
- Voice quality metrics (latency, packet loss, jitter, MOS score)
- User feedback collection
- Feature usage statistics

### 5. Security Monitoring
- Authentication attempt monitoring
- API usage pattern tracking
- Anomaly detection
- Suspicious activity alerting

### 6. Infrastructure Monitoring
- Railway deployment monitoring
- Supabase performance tracking
- LiveKit service availability monitoring
- Dependency health checks

### 7. Continuous Improvement Framework
- Monitoring data feedback loop
- A/B testing capabilities
- Performance benchmarking
- Stakeholder monitoring dashboard

## Getting Started

### Installation

The monitoring system is integrated into the Voice Agent application. No separate installation is required.

### Configuration

Configure the monitoring system in your application by adding the following to your `app.py`:

```python
from fastapi import FastAPI
from src.monitoring.integration import configure_monitoring

app = FastAPI()

# Configure monitoring
configure_monitoring(app)
```

### Environment Variables

The monitoring system can be configured using the following environment variables:

- `SUPABASE_URL`: The URL of your Supabase instance
- `SUPABASE_API_KEY`: The API key for your Supabase instance
- `LIVEKIT_URL`: The URL of your LiveKit instance
- `RAILWAY_PROJECT_ID`: Your Railway project ID
- `RAILWAY_API_KEY`: Your Railway API key
- `ERROR_SAMPLE_RATE`: The percentage of errors to sample (0.0-1.0)
- `SLOW_REQUEST_THRESHOLD`: The threshold for slow requests in seconds
- `ALERT_WEBHOOK_URL`: Webhook URL for sending alerts

### Custom Configuration

For more advanced configuration, you can pass a configuration dictionary to the `configure_monitoring` function:

```python
config = {
    "health": {
        "endpoints": [
            {
                "name": "api",
                "url": "https://api.example.com/health",
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
        "slow_request_threshold": 1.0,
        "memory_warning_threshold": 80,
        "cpu_warning_threshold": 80
    },
    "errors": {
        "error_sample_rate": 0.1,
        "ignored_errors": ["NotFoundError", "ValidationError"]
    },
    "security": {
        "max_failed_logins": 5,
        "failed_login_window": 300,
        "rate_limits": {
            "/api/auth/login": {
                "limit": 10,
                "window": 60
            }
        },
        "ip_blacklist": ["192.168.1.1"],
        "ip_whitelist": ["192.168.1.2"]
    },
    "infrastructure": {
        "dependencies": [
            {
                "type": "http",
                "name": "api",
                "endpoint": "https://api.example.com/health",
                "method": "GET",
                "expected_status": 200,
                "timeout": 5.0,
                "check_interval": 60
            }
        ]
    }
}

configure_monitoring(app, config)
```

## Monitoring Dashboard

The monitoring system includes a web dashboard for viewing monitoring data. Access it at:

```
http://your-app-url/monitoring/dashboard
```

## Alert Handling

The monitoring system can send alerts to various channels:

1. **Logging**: All alerts are logged using the Python logging system.
2. **Webhooks**: Alerts can be sent to a webhook URL specified in the `ALERT_WEBHOOK_URL` environment variable.

To add a custom alert handler:

```python
from src.monitoring.health import health_monitor

def my_alert_handler(alert):
    # Handle the alert
    print(f"Alert: {alert}")

health_monitor.add_alert_handler(my_alert_handler)
```

## API Reference

### Health Monitoring

```python
from src.monitoring.health import health_monitor

# Add a health check endpoint
health_monitor.add_health_check_endpoint(
    name="api",
    endpoint="https://api.example.com/health",
    method="GET",
    headers={},
    expected_status=200,
    timeout=5.0,
    check_interval=60
)

# Set a threshold
health_monitor.set_threshold("cpu_usage", 80)

# Add an alert handler
health_monitor.add_alert_handler(my_alert_handler)
```

### Performance Monitoring

```python
from src.monitoring.performance import performance_monitor

# Set thresholds
performance_monitor.set_slow_request_threshold(1.0)
performance_monitor.set_memory_warning_threshold(80)
performance_monitor.set_cpu_warning_threshold(80)

# Track a request
performance_monitor.track_request(
    endpoint="/api/users",
    method="GET",
    response_time=0.5,
    status_code=200
)
```

### Error Monitoring

```python
from src.monitoring.errors import error_monitor

# Configure error monitoring
error_monitor.set_error_sample_rate(0.1)
error_monitor.add_ignored_error("NotFoundError")

# Track an error
error_monitor.track_error(
    error_type="ValidationError",
    message="Invalid input",
    stack_trace="...",
    request_path="/api/users",
    request_method="POST"
)
```

### User Experience Monitoring

```python
from src.monitoring.user_experience import user_experience_monitor

# Track user session
session = user_experience_monitor.start_session(
    session_id="session_123",
    user_id="user_123"
)

# Record feedback
user_experience_monitor.record_feedback(
    rating=5,
    category="voice_quality",
    comment="Great voice quality!",
    user_id="user_123",
    session_id="session_123"
)

# Record voice quality
user_experience_monitor.record_voice_quality(
    conversation_id="conv_123",
    latency_ms=50,
    packet_loss=0.1,
    jitter_ms=5,
    audio_level=0.8,
    noise_level=0.1,
    mos_score=4.5
)

# Track feature usage
user_experience_monitor.track_feature_usage(
    feature_name="voice_command",
    user_id="user_123",
    session_id="session_123",
    duration=5.0
)
```

### Security Monitoring

```python
from src.monitoring.security import security_monitor

# Configure security monitoring
security_monitor.max_failed_logins = 5
security_monitor.failed_login_window = 300

# Set rate limits
security_monitor.set_rate_limit(
    path="/api/auth/login",
    limit=10,
    window=60
)

# Log security events
security_monitor.log_security_event(
    event_type="login_attempt",
    severity="info",
    user_id="user_123",
    ip_address="192.168.1.1"
)

# Log authentication events
security_monitor.log_auth_event(
    event_type="login",
    success=True,
    user_id="user_123",
    ip_address="192.168.1.1"
)

# Track API usage
security_monitor.track_api_usage(
    endpoint="/api/users",
    method="GET",
    status_code=200,
    response_time=0.5,
    user_id="user_123",
    ip_address="192.168.1.1"
)
```

### Infrastructure Monitoring

```python
from src.monitoring.infrastructure import infrastructure_monitor

# Add HTTP dependency
infrastructure_monitor.add_http_dependency(
    name="api",
    endpoint="https://api.example.com/health",
    method="GET",
    expected_status=200,
    timeout=5.0,
    check_interval=60
)

# Add Supabase dependency
infrastructure_monitor.add_supabase_dependency(
    name="supabase",
    endpoint="https://your-supabase-url.supabase.co",
    api_key="your-api-key",
    check_interval=60
)

# Add LiveKit dependency
infrastructure_monitor.add_livekit_dependency(
    name="livekit",
    endpoint="https://your-livekit-url.livekit.cloud",
    check_interval=60
)

# Add Railway dependency
infrastructure_monitor.add_railway_dependency(
    name="railway-deployment",
    project_id="your-project-id",
    api_key="your-api-key",
    check_interval=300
)

# Add custom dependency
infrastructure_monitor.add_custom_dependency(
    name="database-connection-pool",
    check_func=lambda: {
        "status": "healthy",
        "details": {
            "active_connections": 0,
            "idle_connections": 0,
            "max_connections": 20
        }
    },
    check_interval=30
)
```

## Best Practices

1. **Set appropriate thresholds**: Configure thresholds based on your application's normal behavior.
2. **Monitor critical paths**: Focus on monitoring the most critical parts of your application.
3. **Use sampling for high-volume events**: Use sampling for high-volume events like errors to reduce overhead.
4. **Review monitoring data regularly**: Regularly review monitoring data to identify trends and potential issues.
5. **Set up alerts for critical issues**: Configure alerts for critical issues that require immediate attention.
6. **Keep monitoring overhead low**: Ensure that monitoring doesn't significantly impact application performance.

## Troubleshooting

### Common Issues

1. **High monitoring overhead**: If monitoring is causing performance issues, consider reducing the frequency of checks or using sampling.
2. **False positives**: If you're getting too many false positive alerts, adjust your thresholds or add more specific conditions.
3. **Missing data**: If you're not seeing data in the dashboard, check that the monitoring system is properly configured and that the application is running.

## Contributing

Contributions to the monitoring system are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This monitoring system is part of the Voice Agent application and is subject to the same license.