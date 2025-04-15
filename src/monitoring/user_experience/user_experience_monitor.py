"""
User Experience Monitor Module

This module provides user experience monitoring functionality for the Voice Agent application.
"""

import time
import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque, defaultdict
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class UserSession(BaseModel):
    """Model for user session data."""
    session_id: str
    user_id: Optional[str]
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    device_info: Dict[str, Any] = {}
    pages_visited: List[Dict[str, Any]] = []
    features_used: Dict[str, int] = {}

class UserFeedback(BaseModel):
    """Model for user feedback."""
    feedback_id: str
    user_id: Optional[str]
    session_id: Optional[str]
    timestamp: float
    rating: int
    category: Optional[str] = None
    comment: Optional[str] = None

class VoiceQualityMetric(BaseModel):
    """Model for voice quality metrics."""
    metric_id: str
    conversation_id: str
    timestamp: float
    latency_ms: float
    packet_loss: float
    jitter_ms: float
    audio_level: float
    noise_level: float
    mos_score: Optional[float] = None

class UserExperienceMonitor:
    """
    User Experience Monitor for the Voice Agent application.
    """
    
    def __init__(self):
        """Initialize the user experience monitor."""
        self.active_sessions = {}
        self.session_history = deque(maxlen=1000)
        self.feedback_data = deque(maxlen=1000)
        self.voice_quality_metrics = defaultdict(list)
        self.feature_usage = defaultdict(int)
        self.data_dir = "data/user_experience"
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
    
    def register_with_app(self, app: FastAPI):
        """Register endpoints with the FastAPI application."""
        # Session tracking middleware
        @app.middleware("http")
        async def session_middleware(request: Request, call_next):
            session_id = request.cookies.get("session_id")
            is_new_session = False
            
            if not session_id or session_id not in self.active_sessions:
                session_id = f"session_{int(time.time())}"
                is_new_session = True
                self.start_session(session_id, request.cookies.get("user_id"))
            
            self.track_page_visit(session_id, request.url.path)
            response = await call_next(request)
            
            if is_new_session:
                response.set_cookie("session_id", session_id, httponly=True)
            
            return response
        
        # Feedback endpoint
        @app.post("/feedback")
        async def submit_feedback(feedback: Dict[str, Any], request: Request):
            feedback_id = self.record_feedback(
                rating=feedback.get("rating"),
                category=feedback.get("category"),
                comment=feedback.get("comment"),
                user_id=request.cookies.get("user_id"),
                session_id=request.cookies.get("session_id")
            )
            return {"status": "success", "feedback_id": feedback_id}
        
        # Voice quality endpoint
        @app.post("/metrics/voice-quality")
        async def report_voice_quality(metrics: Dict[str, Any]):
            metric_id = self.record_voice_quality(
                conversation_id=metrics.get("conversation_id"),
                latency_ms=metrics.get("latency_ms"),
                packet_loss=metrics.get("packet_loss"),
                jitter_ms=metrics.get("jitter_ms"),
                audio_level=metrics.get("audio_level"),
                noise_level=metrics.get("noise_level"),
                mos_score=metrics.get("mos_score")
            )
            return {"status": "success", "metric_id": metric_id}
        
        # Feature usage endpoint
        @app.post("/metrics/feature-usage")
        async def track_feature(usage: Dict[str, Any], request: Request):
            self.track_feature_usage(
                feature_name=usage.get("feature_name"),
                session_id=request.cookies.get("session_id")
            )
            return {"status": "success"}
        
        # Metrics endpoints
        @app.get("/metrics/sessions")
        async def get_session_metrics():
            return self.get_session_metrics()
        
        @app.get("/metrics/feedback")
        async def get_feedback_metrics():
            return self.get_feedback_metrics()
        
        @app.get("/metrics/voice-quality/{conversation_id}")
        async def get_voice_metrics(conversation_id: str):
            return self.get_voice_quality_metrics(conversation_id)
        
        @app.get("/metrics/feature-usage")
        async def get_feature_metrics():
            return self.get_feature_usage_metrics()
    
    def start_session(self, session_id: str, user_id: Optional[str] = None):
        """Start tracking a user session."""
        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            start_time=time.time()
        )
        
        self.active_sessions[session_id] = session
        logger.info(f"Session started: {session_id}")
        return session
    
    def end_session(self, session_id: str):
        """End a user session."""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        session.end_time = time.time()
        session.duration = session.end_time - session.start_time
        
        del self.active_sessions[session_id]
        self.session_history.append(session.dict())
        
        logger.info(f"Session ended: {session_id} (Duration: {session.duration:.2f}s)")
        return session
    
    def track_page_visit(self, session_id: str, path: str):
        """Track a page visit within a session."""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        page_visit = {
            "path": path,
            "timestamp": time.time()
        }
        
        session.pages_visited.append(page_visit)
        return True
    
    def record_feedback(self, rating: int, category: Optional[str] = None,
                       comment: Optional[str] = None, user_id: Optional[str] = None,
                       session_id: Optional[str] = None) -> str:
        """Record user feedback."""
        feedback_id = f"feedback_{int(time.time())}"
        
        feedback = UserFeedback(
            feedback_id=feedback_id,
            user_id=user_id,
            session_id=session_id,
            timestamp=time.time(),
            rating=rating,
            category=category,
            comment=comment
        )
        
        self.feedback_data.append(feedback.dict())
        logger.info(f"Feedback recorded: {feedback_id} (Rating: {rating})")
        
        return feedback_id
    
    def record_voice_quality(self, conversation_id: str, latency_ms: float,
                            packet_loss: float, jitter_ms: float, audio_level: float,
                            noise_level: float, mos_score: Optional[float] = None) -> str:
        """Record voice quality metrics."""
        metric_id = f"vqm_{int(time.time())}"
        
        metric = VoiceQualityMetric(
            metric_id=metric_id,
            conversation_id=conversation_id,
            timestamp=time.time(),
            latency_ms=latency_ms,
            packet_loss=packet_loss,
            jitter_ms=jitter_ms,
            audio_level=audio_level,
            noise_level=noise_level,
            mos_score=mos_score
        )
        
        self.voice_quality_metrics[conversation_id].append(metric.dict())
        
        # Check for poor quality
        if packet_loss > 5 or jitter_ms > 50 or latency_ms > 300:
            logger.warning(f"Poor voice quality detected: {conversation_id}")
        
        return metric_id
    
    def track_feature_usage(self, feature_name: str, session_id: Optional[str] = None):
        """Track feature usage."""
        self.feature_usage[feature_name] += 1
        
        # Update session feature usage if session exists
        if session_id and session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            if feature_name in session.features_used:
                session.features_used[feature_name] += 1
            else:
                session.features_used[feature_name] = 1
    
    def get_session_metrics(self) -> Dict[str, Any]:
        """Get session metrics."""
        active_count = len(self.active_sessions)
        completed_count = len(self.session_history)
        
        # Calculate average session duration
        if self.session_history:
            durations = [s["duration"] for s in self.session_history if s["duration"] is not None]
            avg_duration = sum(durations) / len(durations) if durations else 0
        else:
            avg_duration = 0
        
        # Count page visits
        page_visits = defaultdict(int)
        for session in self.active_sessions.values():
            for visit in session.pages_visited:
                page_visits[visit["path"]] += 1
        
        for session in self.session_history:
            for visit in session["pages_visited"]:
                page_visits[visit["path"]] += 1
        
        return {
            "active_sessions": active_count,
            "completed_sessions": completed_count,
            "total_sessions": active_count + completed_count,
            "avg_duration": avg_duration,
            "page_visits": dict(page_visits),
            "timestamp": time.time()
        }
    
    def get_feedback_metrics(self) -> Dict[str, Any]:
        """Get feedback metrics."""
        if not self.feedback_data:
            return {
                "total_feedback": 0,
                "avg_rating": 0,
                "timestamp": time.time()
            }
        
        # Count feedback by rating
        rating_counts = defaultdict(int)
        for feedback in self.feedback_data:
            rating_counts[feedback["rating"]] += 1
        
        # Calculate average rating
        avg_rating = sum(f["rating"] for f in self.feedback_data) / len(self.feedback_data)
        
        return {
            "total_feedback": len(self.feedback_data),
            "avg_rating": avg_rating,
            "by_rating": dict(rating_counts),
            "timestamp": time.time()
        }
    
    def get_voice_quality_metrics(self, conversation_id: str) -> Dict[str, Any]:
        """Get voice quality metrics for a conversation."""
        if conversation_id not in self.voice_quality_metrics:
            return {
                "conversation_id": conversation_id,
                "metrics_count": 0,
                "timestamp": time.time()
            }
        
        metrics = self.voice_quality_metrics[conversation_id]
        
        # Calculate averages
        avg_latency = sum(m["latency_ms"] for m in metrics) / len(metrics)
        avg_packet_loss = sum(m["packet_loss"] for m in metrics) / len(metrics)
        avg_jitter = sum(m["jitter_ms"] for m in metrics) / len(metrics)
        
        # Calculate MOS score if available
        mos_metrics = [m for m in metrics if m["mos_score"] is not None]
        avg_mos = sum(m["mos_score"] for m in mos_metrics) / len(mos_metrics) if mos_metrics else None
        
        return {
            "conversation_id": conversation_id,
            "metrics_count": len(metrics),
            "avg_latency_ms": avg_latency,
            "avg_packet_loss": avg_packet_loss,
            "avg_jitter_ms": avg_jitter,
            "avg_mos_score": avg_mos,
            "timestamp": time.time()
        }
    
    def get_feature_usage_metrics(self) -> Dict[str, Any]:
        """Get feature usage metrics."""
        return {
            "feature_usage": dict(self.feature_usage),
            "timestamp": time.time()
        }

# Create a singleton instance
user_experience_monitor = UserExperienceMonitor()
