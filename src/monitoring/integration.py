"""
LiveKit and Supabase Integration Monitoring Module

This module extends the monitoring system to track metrics specific to the
LiveKit and Supabase integration.
"""

import time
import logging
import asyncio
import os
from typing import Dict, Any, Optional, List

from src.monitoring.performance.performance_monitor import performance_monitor
from src.monitoring.errors.error_monitor import error_monitor
from src.monitoring.security.security_monitor import security_monitor
from src.monitoring.user_experience.user_experience_monitor import user_experience_monitor
from src.monitoring.infrastructure.infrastructure_monitor import infrastructure_monitor
from src.monitoring.improvement.improvement_process import ImprovementProcess

logger = logging.getLogger(__name__)

class LiveKitSupabaseMonitoring:
    """
    Monitoring for the LiveKit and Supabase integration.
    
    This class provides methods to track performance, errors, security events,
    and user experience metrics specific to the LiveKit and Supabase integration.
    """
    
    def __init__(self):
        """Initialize the LiveKit and Supabase monitoring."""
        self.performance = performance_monitor
        self.errors = error_monitor
        self.security = security_monitor
        self.user_experience = user_experience_monitor
        self.infrastructure = infrastructure_monitor
        self.improvement_process = ImprovementProcess()
        
        # Configure alert thresholds
        self._configure_alert_thresholds()
        
        # Start background monitoring tasks
        self.is_monitoring = False
        self.monitoring_task = None
    
    def start_monitoring(self):
        """Start the background monitoring tasks."""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_task = asyncio.create_task(self._monitor_integration())
            logger.info("LiveKit and Supabase integration monitoring started")
    
    def stop_monitoring(self):
        """Stop the background monitoring tasks."""
        if self.is_monitoring:
            self.is_monitoring = False
            if self.monitoring_task:
                self.monitoring_task.cancel()
            logger.info("LiveKit and Supabase integration monitoring stopped")
    
    async def _monitor_integration(self):
        """Background task to monitor the integration."""
        while self.is_monitoring:
            try:
                # Check LiveKit service health
                livekit_health = await self.infrastructure.check_component("livekit")
                
                # Check Supabase service health
                supabase_health = await self.infrastructure.check_component("supabase")
                
                # Check integration health
                integration_health = self._check_integration_health(livekit_health, supabase_health)
                
                # Generate reports if needed
                await self._generate_reports()
                
            except Exception as e:
                logger.error(f"Error in integration monitoring: {str(e)}")
            
            await asyncio.sleep(60)  # Check every minute
    
    def _check_integration_health(self, livekit_health: Dict[str, Any], 
                                 supabase_health: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check the overall integration health.
        
        Args:
            livekit_health: LiveKit health check result
            supabase_health: Supabase health check result
            
        Returns:
            A dict with the integration health status
        """
        is_healthy = (livekit_health.get("status") == "healthy" and 
                      supabase_health.get("status") == "healthy")
        
        status = {
            "status": "healthy" if is_healthy else "unhealthy",
            "components": {
                "livekit": livekit_health,
                "supabase": supabase_health
            },
            "timestamp": time.time()
        }
        
        # Record the status
        self.performance.record_metric(
            name="integration.health.status",
            value=1 if is_healthy else 0,
            unit="status",
            tags={
                "livekit_status": livekit_health.get("status"),
                "supabase_status": supabase_health.get("status")
            }
        )
        
        return status
    
    async def _generate_reports(self):
        """Generate monitoring reports if needed."""
        # Check if it's time to generate reports
        current_hour = time.localtime().tm_hour
        current_minute = time.localtime().tm_min
        current_day = time.localtime().tm_mday
        
        # Daily report at 00:01
        if current_hour == 0 and current_minute == 1:
            await self.improvement_process.generate_daily_report()
        
        # Weekly report on Monday at 00:05
        if time.localtime().tm_wday == 0 and current_hour == 0 and current_minute == 5:
            await self.improvement_process.generate_weekly_report()
        
        # Monthly report on the 1st at 00:10
        if current_day == 1 and current_hour == 0 and current_minute == 10:
            await self.improvement_process.generate_monthly_report()
    
    def _configure_alert_thresholds(self):
        """Configure alert thresholds for the monitoring system."""
        # LiveKit performance thresholds
        self.performance.set_alert_threshold("livekit.latency.ms", 300, "gt", duration=300)
        self.performance.set_alert_threshold("livekit.packet_loss", 5, "gt", duration=120)
        self.performance.set_alert_threshold("livekit.jitter.ms", 50, "gt", duration=300)
        self.performance.set_alert_threshold("livekit.mos_score", 3.5, "lt", duration=300)
        self.performance.set_alert_threshold("livekit.cpu_usage", 80, "gt", duration=600)
        self.performance.set_alert_threshold("livekit.memory_usage", 80, "gt", duration=600)
        self.performance.set_alert_threshold("livekit.room_count", 100, "gt", duration=300)
        self.performance.set_alert_threshold("livekit.participant_count", 500, "gt", duration=300)
        self.performance.set_alert_threshold("livekit.connection_success_rate", 95, "lt", duration=300)
        
        # Supabase performance thresholds
        self.performance.set_alert_threshold("supabase.query.duration.ms", 500, "gt", duration=300)
        self.performance.set_alert_threshold("supabase.query.error_rate", 1, "gt", duration=300)
        self.performance.set_alert_threshold("supabase.realtime.latency.ms", 200, "gt", duration=300)
        self.performance.set_alert_threshold("supabase.auth.failure_rate", 5, "gt", duration=300)
        
        # Integration performance thresholds
        self.performance.set_alert_threshold("integration.voice_to_db.latency.ms", 1000, "gt", duration=300)
        self.performance.set_alert_threshold("integration.db_to_voice.latency.ms", 1000, "gt", duration=300)
        self.performance.set_alert_threshold("integration.end_to_end.latency.ms", 2000, "gt", duration=300)
        self.performance.set_alert_threshold("integration.transaction.success_rate", 98, "lt", duration=120)
        
        # User experience thresholds
        self.performance.set_alert_threshold("voice.quality.mos", 3.5, "lt", duration=300)
        self.performance.set_alert_threshold("user.satisfaction.score", 4.0, "lt", duration=1800)
    
    # LiveKit performance tracking methods
    
    def track_livekit_performance(self, latency_ms: float, packet_loss: float, 
                                 jitter_ms: float, mos_score: Optional[float] = None):
        """
        Track LiveKit performance metrics.
        
        Args:
            latency_ms: End-to-end audio latency in milliseconds
            packet_loss: Percentage of lost audio packets
            jitter_ms: Audio jitter in milliseconds
            mos_score: Mean Opinion Score for audio quality (optional)
        """
        self.performance.record_metric(
            name="livekit.latency.ms",
            value=latency_ms,
            unit="ms"
        )
        self.performance.record_metric(
            name="livekit.packet_loss",
            value=packet_loss,
            unit="percent"
        )
        self.performance.record_metric(
            name="livekit.jitter.ms",
            value=jitter_ms,
            unit="ms"
        )
        if mos_score is not None:
            self.performance.record_metric(
                name="livekit.mos_score",
                value=mos_score,
                unit="score"
            )
    
    def track_livekit_server_metrics(self, cpu_usage: float, memory_usage: float, 
                                    room_count: int, participant_count: int):
        """
        Track LiveKit server metrics.
        
        Args:
            cpu_usage: CPU usage percentage
            memory_usage: Memory usage percentage
            room_count: Number of active rooms
            participant_count: Number of active participants
        """
        self.performance.record_metric(
            name="livekit.cpu_usage",
            value=cpu_usage,
            unit="percent"
        )
        self.performance.record_metric(
            name="livekit.memory_usage",
            value=memory_usage,
            unit="percent"
        )
        self.performance.record_metric(
            name="livekit.room_count",
            value=room_count,
            unit="count"
        )
        self.performance.record_metric(
            name="livekit.participant_count",
            value=participant_count,
            unit="count"
        )
    
    def track_livekit_connection(self, success: bool):
        """
        Track LiveKit connection success.
        
        Args:
            success: Whether the connection was successful
        """
        self.performance.record_metric(
            name="livekit.connection.success",
            value=1 if success else 0,
            unit="count"
        )
        
        # Calculate success rate (last 100 connections)
        if hasattr(self, '_connection_results'):
            self._connection_results.append(1 if success else 0)
            if len(self._connection_results) > 100:
                self._connection_results.pop(0)
            
            success_rate = sum(self._connection_results) / len(self._connection_results) * 100
            self.performance.record_metric(
                name="livekit.connection_success_rate",
                value=success_rate,
                unit="percent"
            )
        else:
            self._connection_results = [1 if success else 0]
    
    # Supabase performance tracking methods
    
    def track_supabase_query(self, query_name: str, duration_ms: float, success: bool = True):
        """
        Track Supabase query performance.
        
        Args:
            query_name: The name of the query
            duration_ms: Query duration in milliseconds
            success: Whether the query was successful
        """
        self.performance.record_metric(
            name="supabase.query.duration.ms",
            value=duration_ms,
            unit="ms",
            tags={
                "query_name": query_name,
                "success": str(success)
            }
        )
        
        # Track error rate
        if hasattr(self, '_query_results'):
            self._query_results.append(1 if success else 0)
            if len(self._query_results) > 100:
                self._query_results.pop(0)
            
            error_rate = (len(self._query_results) - sum(self._query_results)) / len(self._query_results) * 100
            self.performance.record_metric(
                name="supabase.query.error_rate",
                value=error_rate,
                unit="percent"
            )
        else:
            self._query_results = [1 if success else 0]
    
    def track_supabase_realtime(self, latency_ms: float, message_count: int):
        """
        Track Supabase realtime performance.
        
        Args:
            latency_ms: Realtime subscription latency in milliseconds
            message_count: Number of realtime messages
        """
        self.performance.record_metric(
            name="supabase.realtime.latency.ms",
            value=latency_ms,
            unit="ms"
        )
        self.performance.record_metric(
            name="supabase.realtime.message_count",
            value=message_count,
            unit="count"
        )
    
    def track_supabase_auth(self, success: bool, user_id: Optional[str] = None):
        """
        Track Supabase authentication.
        
        Args:
            success: Whether the authentication was successful
            user_id: The user ID (optional)
        """
        self.performance.record_metric(
            name="supabase.auth.success",
            value=1 if success else 0,
            unit="count",
            tags={
                "user_id": user_id or "anonymous"
            }
        )
        
        # Track failure rate
        if hasattr(self, '_auth_results'):
            self._auth_results.append(1 if success else 0)
            if len(self._auth_results) > 100:
                self._auth_results.pop(0)
            
            failure_rate = (len(self._auth_results) - sum(self._auth_results)) / len(self._auth_results) * 100
            self.performance.record_metric(
                name="supabase.auth.failure_rate",
                value=failure_rate,
                unit="percent"
            )
        else:
            self._auth_results = [1 if success else 0]
    
    # Integration performance tracking methods
    
    def track_integration_latency(self, operation: str, latency_ms: float):
        """
        Track integration latency.
        
        Args:
            operation: The operation name (e.g., "voice_to_db", "db_to_voice", "end_to_end")
            latency_ms: Operation latency in milliseconds
        """
        self.performance.record_metric(
            name=f"integration.{operation}.latency.ms",
            value=latency_ms,
            unit="ms"
        )
    
    def track_integration_transaction(self, success: bool, operation: Optional[str] = None):
        """
        Track integration transaction success.
        
        Args:
            success: Whether the transaction was successful
            operation: The operation name (optional)
        """
        tags = {}
        if operation:
            tags["operation"] = operation
            
        self.performance.record_metric(
            name="integration.transaction.success",
            value=1 if success else 0,
            unit="count",
            tags=tags
        )
        
        # Track success rate
        if hasattr(self, '_transaction_results'):
            self._transaction_results.append(1 if success else 0)
            if len(self._transaction_results) > 100:
                self._transaction_results.pop(0)
            
            success_rate = sum(self._transaction_results) / len(self._transaction_results) * 100
            self.performance.record_metric(
                name="integration.transaction.success_rate",
                value=success_rate,
                unit="percent"
            )
        else:
            self._transaction_results = [1 if success else 0]
    
    # Error tracking methods
    
    def track_livekit_error(self, error_type: str, message: str, context: Optional[Dict[str, Any]] = None):
        """
        Track a LiveKit error.
        
        Args:
            error_type: The type of error
            message: The error message
            context: Additional context information (optional)
        """
        self.errors.log_error(
            error_type=f"livekit.{error_type}",
            message=message,
            context=context or {},
            component="livekit"
        )
    
    def track_supabase_error(self, error_type: str, message: str, context: Optional[Dict[str, Any]] = None):
        """
        Track a Supabase error.
        
        Args:
            error_type: The type of error
            message: The error message
            context: Additional context information (optional)
        """
        self.errors.log_error(
            error_type=f"supabase.{error_type}",
            message=message,
            context=context or {},
            component="supabase"
        )
    
    def track_integration_error(self, error_type: str, message: str, context: Optional[Dict[str, Any]] = None):
        """
        Track an integration error.
        
        Args:
            error_type: The type of error
            message: The error message
            context: Additional context information (optional)
        """
        self.errors.log_error(
            error_type=f"integration.{error_type}",
            message=message,
            context=context or {},
            component="integration",
            severity="critical"  # Integration errors are critical by default
        )
    
    # Security monitoring methods
    
    def log_livekit_security_event(self, event_type: str, user_id: str, details: Optional[Dict[str, Any]] = None):
        """
        Log a LiveKit security event.
        
        Args:
            event_type: The type of security event
            user_id: The user ID
            details: Additional details (optional)
        """
        self.security.log_security_event(
            event_type=f"livekit.{event_type}",
            user_id=user_id,
            details=details or {},
            severity="warning"
        )
    
    def log_supabase_security_event(self, event_type: str, user_id: str, details: Optional[Dict[str, Any]] = None):
        """
        Log a Supabase security event.
        
        Args:
            event_type: The type of security event
            user_id: The user ID
            details: Additional details (optional)
        """
        self.security.log_security_event(
            event_type=f"supabase.{event_type}",
            user_id=user_id,
            details=details or {},
            severity="warning"
        )
    
    # User experience monitoring methods
    
    def record_enhanced_voice_quality(self, conversation_id: str, metrics: Dict[str, float]):
        """
        Record enhanced voice quality metrics.
        
        Args:
            conversation_id: The conversation ID
            metrics: A dict of voice quality metrics
        """
        self.user_experience.record_voice_quality(
            conversation_id=conversation_id,
            latency_ms=metrics.get("latency_ms", 0),
            packet_loss=metrics.get("packet_loss", 0),
            jitter_ms=metrics.get("jitter_ms", 0),
            audio_level=metrics.get("audio_level", 0),
            noise_level=metrics.get("noise_level", 0),
            mos_score=metrics.get("mos_score")
        )
        
        # Additional metrics
        if "clarity" in metrics:
            self.performance.record_metric(
                name="voice.quality.clarity",
                value=metrics["clarity"],
                unit="score",
                tags={"conversation_id": conversation_id}
            )
        
        if "transcription_accuracy" in metrics:
            self.performance.record_metric(
                name="voice.transcription.accuracy",
                value=metrics["transcription_accuracy"],
                unit="percent",
                tags={"conversation_id": conversation_id}
            )
        
        if "response_relevance" in metrics:
            self.performance.record_metric(
                name="voice.response.relevance",
                value=metrics["response_relevance"],
                unit="score",
                tags={"conversation_id": conversation_id}
            )
        
        if "interruption_rate" in metrics:
            self.performance.record_metric(
                name="voice.interruption.rate",
                value=metrics["interruption_rate"],
                unit="percent",
                tags={"conversation_id": conversation_id}
            )
    
    def track_conversation_completion(self, conversation_id: str, completed: bool):
        """
        Track whether a conversation was completed successfully.
        
        Args:
            conversation_id: The conversation ID
            completed: Whether the conversation was completed
        """
        self.performance.record_metric(
            name="user.session.completion_rate",
            value=1 if completed else 0,
            unit="count",
            tags={"conversation_id": conversation_id}
        )
    
    def record_user_satisfaction(self, user_id: str, score: float, feedback: Optional[str] = None):
        """
        Record user satisfaction.
        
        Args:
            user_id: The user ID
            score: The satisfaction score (1-5)
            feedback: User feedback (optional)
        """
        self.performance.record_metric(
            name="user.satisfaction.score",
            value=score,
            unit="score",
            tags={"user_id": user_id}
        )
        
        # Record feedback if provided
        if feedback:
            self.user_experience.record_feedback(
                rating=int(score),
                category="voice_quality",
                comment=feedback,
                user_id=user_id
            )


# Create a singleton instance
livekit_supabase_monitoring = LiveKitSupabaseMonitoring()

def configure_livekit_supabase_monitoring():
    """Configure LiveKit and Supabase monitoring."""
    # Start the monitoring
    livekit_supabase_monitoring.start_monitoring()
    
    # Add LiveKit dependency to infrastructure monitoring
    livekit_url = os.environ.get("LIVEKIT_URL")
    if livekit_url:
        infrastructure_monitor.add_livekit_dependency(
            name="livekit",
            endpoint=livekit_url,
            check_interval=60
        )
    
    # Add Supabase dependency to infrastructure monitoring
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_API_KEY")
    if supabase_url and supabase_key:
        infrastructure_monitor.add_supabase_dependency(
            name="supabase",
            endpoint=supabase_url,
            api_key=supabase_key,
            check_interval=60
        )
    
    logger.info("LiveKit and Supabase monitoring configured")