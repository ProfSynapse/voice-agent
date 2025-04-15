"""
LiveKit Agents Service Module

This module provides a re-export of the LiveKitAgentsService as VoiceService
and other necessary classes for backward compatibility with tests.
"""

from src.voice.livekit_agents import LiveKitAgentsService as VoiceService
from src.voice.livekit_agents import VoiceAssistant
from livekit.agents import Agent, Worker, AgentSession, RoomInputOptions

__all__ = ["VoiceService", "VoiceAssistant", "Agent", "Worker", "AgentSession", "RoomInputOptions"]