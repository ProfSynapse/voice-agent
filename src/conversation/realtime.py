"""
Conversation Realtime Module

This module provides real-time subscription functionality for conversations
using Supabase's real-time features.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Callable, Awaitable
from datetime import datetime

from loguru import logger
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
# Removed import of RealtimeClient and RealtimeChannel as they're not directly accessible

from src.config.config_service import get_config_service
from src.conversation.models import Conversation, ConversationTurn, ConversationRole
from enum import Enum


class SubscriptionEvent(str, Enum):
    """Subscription event types."""
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    SELECT = "SELECT"


class SubscriptionTable(str, Enum):
    """Tables that can be subscribed to."""
    CONVERSATIONS = "conversations"
    CONVERSATION_TURNS = "conversation_turns"
    SYSTEM_PROMPTS = "system_prompts"
    USERS = "users"


class RealtimeSubscriptionService:
    """
    Service for managing real-time subscriptions to Supabase.
    
    This service provides methods to subscribe to changes in Supabase tables
    and receive real-time updates when data changes.
    """
    
    def __init__(self, supabase_client):
        """
        Initialize the real-time subscription service.
        
        Args:
            supabase_client: Initialized Supabase client
        """
        self.supabase = supabase_client
        self.subscriptions = {}
        self.channels = {}
        self.event_handlers = {}
        
        logger.info("Real-time subscription service initialized")
    
    async def subscribe_to_table(
        self,
        table: SubscriptionTable,
        event: SubscriptionEvent,
        callback: Callable[[Dict[str, Any]], Awaitable[None]],
        filter_str: Optional[str] = None
    ) -> str:
        """
        Subscribe to changes in a table.
        
        Args:
            table: Table to subscribe to
            event: Event type to subscribe to
            callback: Callback function to call when an event occurs
            filter_str: Optional filter string (e.g., "user_id=eq.123")
            
        Returns:
            Subscription ID
        """
        try:
            # Generate a unique subscription ID
            subscription_id = f"{table.value}:{event.value}:{filter_str or 'all'}"
            
            # Create a channel if it doesn't exist
            if table.value not in self.channels:
                channel_name = f"{table.value}-changes"
                self.channels[table.value] = self.supabase.channel(channel_name)
            
            channel = self.channels[table.value]
            
            # Set up the filter
            filter_obj = {
                "event": event.value,
                "schema": "public",
                "table": table.value
            }
            
            if filter_str:
                filter_obj["filter"] = filter_str
            
            # Create a wrapper for the callback to handle the event
            async def handle_event(payload):
                try:
                    await callback(payload)
                except Exception as e:
                    logger.error(f"Error in subscription callback: {str(e)}")
            
            # Subscribe to the channel
            channel.on(
                "postgres_changes",
                filter_obj,
                handle_event
            )
            
            # If the channel is not already subscribed, subscribe it
            if not channel.is_subscribed():
                self.subscriptions[subscription_id] = await channel.subscribe()
            else:
                self.subscriptions[subscription_id] = channel
            
            # Store the event handler for later unsubscription
            if subscription_id not in self.event_handlers:
                self.event_handlers[subscription_id] = []
            self.event_handlers[subscription_id].append(handle_event)
            
            logger.info(f"Subscribed to {table.value} {event.value} events with ID {subscription_id}")
            
            return subscription_id
        except Exception as e:
            logger.error(f"Failed to subscribe to {table.value} {event.value} events: {str(e)}")
            raise
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from a subscription.
        
        Args:
            subscription_id: ID of the subscription to unsubscribe from
            
        Returns:
            True if unsubscribed successfully, False otherwise
        """
        if subscription_id not in self.subscriptions:
            logger.warning(f"Subscription {subscription_id} not found")
            return False
        
        try:
            # Get the table name from the subscription ID
            table_name = subscription_id.split(":")[0]
            
            # Unsubscribe from the channel
            channel = self.channels.get(table_name)
            if channel:
                await channel.unsubscribe()
                del self.channels[table_name]
            
            # Remove the subscription
            del self.subscriptions[subscription_id]
            
            # Remove the event handlers
            if subscription_id in self.event_handlers:
                del self.event_handlers[subscription_id]
            
            logger.info(f"Unsubscribed from {subscription_id}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to unsubscribe from {subscription_id}: {str(e)}")
            return False
    
    async def unsubscribe_all(self) -> bool:
        """
        Unsubscribe from all subscriptions.
        
        Returns:
            True if all unsubscribed successfully, False otherwise
        """
        try:
            # Unsubscribe from all channels
            for table_name, channel in self.channels.items():
                await channel.unsubscribe()
            
            # Clear all subscriptions and channels
            self.subscriptions = {}
            self.channels = {}
            self.event_handlers = {}
            
            logger.info("Unsubscribed from all subscriptions")
            
            return True
        except Exception as e:
            logger.error(f"Failed to unsubscribe from all subscriptions: {str(e)}")
            return False


class ConversationRealtimeService:
    """
    Service for managing real-time subscriptions to conversations and turns.
    
    This service uses Supabase's real-time features to subscribe to changes
    in conversations and turns, providing real-time updates to clients.
    """
    def __init__(self, supabase_client: Optional[Client] = None, realtime_service: Optional[RealtimeSubscriptionService] = None):
        """
        Initialize the conversation realtime service.
        
        Args:
            supabase_client: Optional Supabase client to use
            realtime_service: Optional RealtimeSubscriptionService instance
        """
        self.config = get_config_service()
        
        # Initialize Supabase client if not provided
        if supabase_client:
            self.supabase = supabase_client
        else:
            supabase_config = self.config.supabase_config
            self.supabase = create_client(
                supabase_config["url"],
                supabase_config["anon_key"],
                options=ClientOptions(
                    schema="public"
                )
            )
        
        # Initialize or store the realtime service
        if realtime_service:
            self.realtime_service = realtime_service
        else:
            self.realtime_service = RealtimeSubscriptionService(self.supabase)
        
        # Active subscriptions
        self.conversation_channels: Dict[str, Any] = {}
        self.turn_channels: Dict[str, Any] = {}
        
        # Subscription tracking
        self.user_subscriptions: Dict[str, List[str]] = {}
        self.conversation_subscriptions: Dict[str, List[str]] = {}
        
        # Callbacks
        self.on_conversation_update: Dict[str, List[Callable[[Conversation], Awaitable[None]]]] = {}
        self.on_turn_insert: Dict[str, List[Callable[[ConversationTurn], Awaitable[None]]]] = {}
        self.on_turn_update: Dict[str, List[Callable[[ConversationTurn], Awaitable[None]]]] = {}
        
        logger.info("Conversation realtime service initialized")
    
    async def subscribe_to_conversation(
        self,
        conversation_id: str,
        on_update: Optional[Callable[[Conversation], Awaitable[None]]] = None
    ) -> bool:
        """
        Subscribe to updates for a specific conversation.
        
        Args:
            conversation_id: ID of the conversation to subscribe to
            on_update: Callback for conversation updates
            
        Returns:
            True if subscribed successfully, False otherwise
        """
        try:
            # Create a channel for this conversation
            channel_name = f"conversation:{conversation_id}"
            
            # Check if we already have a channel for this conversation
            if channel_name in self.conversation_channels:
                logger.info(f"Already subscribed to conversation {conversation_id}")
                
                # Add the callback if provided
                if on_update:
                    if conversation_id not in self.on_conversation_update:
                        self.on_conversation_update[conversation_id] = []
                    self.on_conversation_update[conversation_id].append(on_update)
                
                return True
            
            # Create a new channel
            channel = self.supabase.channel(channel_name)
            
            # Subscribe to conversation updates
            channel.on(
                "postgres_changes",
                event="UPDATE",
                schema="public",
                table="conversations",
                filter=f"id=eq.{conversation_id}",
                callback=lambda payload: asyncio.create_task(
                    self._handle_conversation_update(conversation_id, payload)
                )
            )
            
            # Subscribe
            channel.subscribe()
            
            # Store the channel
            self.conversation_channels[channel_name] = channel
            
            # Store the callback if provided
            if on_update:
                if conversation_id not in self.on_conversation_update:
                    self.on_conversation_update[conversation_id] = []
                self.on_conversation_update[conversation_id].append(on_update)
            
            logger.info(f"Subscribed to conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe to conversation {conversation_id}: {str(e)}")
            return False
    
    async def subscribe_to_turns(
        self,
        conversation_id: str,
        on_insert: Optional[Callable[[ConversationTurn], Awaitable[None]]] = None,
        on_update: Optional[Callable[[ConversationTurn], Awaitable[None]]] = None
    ) -> bool:
        """
        Subscribe to turn updates for a specific conversation.
        
        Args:
            conversation_id: ID of the conversation to subscribe to
            on_insert: Callback for turn inserts
            on_update: Callback for turn updates
            
        Returns:
            True if subscribed successfully, False otherwise
        """
        try:
            # Create a channel for turns in this conversation
            channel_name = f"turns:{conversation_id}"
            
            # Check if we already have a channel for turns in this conversation
            if channel_name in self.turn_channels:
                logger.info(f"Already subscribed to turns for conversation {conversation_id}")
                
                # Add the callbacks if provided
                if on_insert:
                    if conversation_id not in self.on_turn_insert:
                        self.on_turn_insert[conversation_id] = []
                    self.on_turn_insert[conversation_id].append(on_insert)
                
                if on_update:
                    if conversation_id not in self.on_turn_update:
                        self.on_turn_update[conversation_id] = []
                    self.on_turn_update[conversation_id].append(on_update)
                
                return True
            
            # Create a new channel
            channel = self.supabase.channel(channel_name)
            
            # Subscribe to turn inserts
            channel.on(
                "postgres_changes",
                event="INSERT",
                schema="public",
                table="conversation_turns",
                filter=f"conversation_id=eq.{conversation_id}",
                callback=lambda payload: asyncio.create_task(
                    self._handle_turn_insert(conversation_id, payload)
                )
            )
            
            # Subscribe to turn updates
            channel.on(
                "postgres_changes",
                event="UPDATE",
                schema="public",
                table="conversation_turns",
                filter=f"conversation_id=eq.{conversation_id}",
                callback=lambda payload: asyncio.create_task(
                    self._handle_turn_update(conversation_id, payload)
                )
            )
            
            # Subscribe
            channel.subscribe()
            
            # Store the channel
            self.turn_channels[channel_name] = channel
            
            # Store the callbacks if provided
            if on_insert:
                if conversation_id not in self.on_turn_insert:
                    self.on_turn_insert[conversation_id] = []
                self.on_turn_insert[conversation_id].append(on_insert)
            
            if on_update:
                if conversation_id not in self.on_turn_update:
                    self.on_turn_update[conversation_id] = []
                self.on_turn_update[conversation_id].append(on_update)
            
            logger.info(f"Subscribed to turns for conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe to turns for conversation {conversation_id}: {str(e)}")
            return False
    
    async def unsubscribe_from_conversation(self, conversation_id: str) -> bool:
        """
        Unsubscribe from updates for a specific conversation.
        
        Args:
            conversation_id: ID of the conversation to unsubscribe from
            
        Returns:
            True if unsubscribed successfully, False otherwise
        """
        try:
            # Get the channel for this conversation
            channel_name = f"conversation:{conversation_id}"
            
            if channel_name in self.conversation_channels:
                # Unsubscribe
                channel = self.conversation_channels[channel_name]
                channel.unsubscribe()
                
                # Remove the channel
                del self.conversation_channels[channel_name]
                
                # Remove callbacks
                if conversation_id in self.on_conversation_update:
                    del self.on_conversation_update[conversation_id]
                
                logger.info(f"Unsubscribed from conversation {conversation_id}")
                return True
            else:
                logger.warning(f"Not subscribed to conversation {conversation_id}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe from conversation {conversation_id}: {str(e)}")
            return False
    
    async def unsubscribe_from_turns(self, conversation_id: str) -> bool:
        """
        Unsubscribe from turn updates for a specific conversation.
        
        Args:
            conversation_id: ID of the conversation to unsubscribe from
            
        Returns:
            True if unsubscribed successfully, False otherwise
        """
        try:
            # Get the channel for turns in this conversation
            channel_name = f"turns:{conversation_id}"
            
            if channel_name in self.turn_channels:
                # Unsubscribe
                channel = self.turn_channels[channel_name]
                channel.unsubscribe()
                
                # Remove the channel
                del self.turn_channels[channel_name]
                
                # Remove callbacks
                if conversation_id in self.on_turn_insert:
                    del self.on_turn_insert[conversation_id]
                
                if conversation_id in self.on_turn_update:
                    del self.on_turn_update[conversation_id]
                
                logger.info(f"Unsubscribed from turns for conversation {conversation_id}")
                return True
            else:
                logger.warning(f"Not subscribed to turns for conversation {conversation_id}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe from turns for conversation {conversation_id}: {str(e)}")
            return False
    
    async def unsubscribe_all(self) -> bool:
        """
        Unsubscribe from all subscriptions.
        
        Returns:
            True if unsubscribed successfully, False otherwise
        """
        try:
            # Use the realtime service to unsubscribe from all subscriptions
            await self.realtime_service.unsubscribe_all()
            
            # Unsubscribe from all conversation channels
            for channel_name in list(self.conversation_channels.keys()):
                channel = self.conversation_channels[channel_name]
                channel.unsubscribe()
            
            # Unsubscribe from all turn channels
            for channel_name in list(self.turn_channels.keys()):
                channel = self.turn_channels[channel_name]
                channel.unsubscribe()
            
            # Clear all channels and callbacks
            self.conversation_channels = {}
            self.turn_channels = {}
            self.user_subscriptions = {}
            self.conversation_subscriptions = {}
            self.on_conversation_update = {}
            self.on_turn_insert = {}
            self.on_turn_update = {}
            
            logger.info("Unsubscribed from all subscriptions")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe from all subscriptions: {str(e)}")
            return False
    
    async def _handle_conversation_update(self, conversation_id: str, payload: Dict[str, Any]) -> None:
        """
        Handle a conversation update event.
        
        Args:
            conversation_id: ID of the conversation
            payload: Event payload
        """
        try:
            # Extract the conversation data
            record = payload.get("new", {})
            
            # Create a Conversation object
            conversation = Conversation(
                id=record.get("id"),
                title=record.get("title"),
                created_at=datetime.fromisoformat(record.get("created_at")),
                updated_at=datetime.fromisoformat(record.get("updated_at")),
                user_id=record.get("user_id"),
                metadata=record.get("metadata", {})
            )
            
            # Call the callbacks
            if conversation_id in self.on_conversation_update:
                for callback in self.on_conversation_update[conversation_id]:
                    await callback(conversation)
                    
        except Exception as e:
            logger.error(f"Error handling conversation update: {str(e)}")
    
    async def _handle_turn_insert(self, conversation_id: str, payload: Dict[str, Any]) -> None:
        """
        Handle a turn insert event.
        
        Args:
            conversation_id: ID of the conversation
            payload: Event payload
        """
        try:
            # Extract the turn data
            record = payload.get("new", {})
            
            # Create a ConversationTurn object
            turn = ConversationTurn(
                id=record.get("id"),
                conversation_id=record.get("conversation_id"),
                role=ConversationRole(record.get("role")),
                content=record.get("content"),
                created_at=datetime.fromisoformat(record.get("created_at")),
                updated_at=datetime.fromisoformat(record.get("updated_at")),
                metadata=record.get("metadata", {})
            )
            
            # Call the callbacks
            if conversation_id in self.on_turn_insert:
                for callback in self.on_turn_insert[conversation_id]:
                    await callback(turn)
                    
        except Exception as e:
            logger.error(f"Error handling turn insert: {str(e)}")
    
    async def _handle_turn_update(self, conversation_id: str, payload: Dict[str, Any]) -> None:
        """
        Handle a turn update event.
        
        Args:
            conversation_id: ID of the conversation
            payload: Event payload
        """
        try:
            # Extract the turn data
            record = payload.get("new", {})
            
            # Create a ConversationTurn object
            turn = ConversationTurn(
                id=record.get("id"),
                conversation_id=record.get("conversation_id"),
                role=ConversationRole(record.get("role")),
                content=record.get("content"),
                created_at=datetime.fromisoformat(record.get("created_at")),
                updated_at=datetime.fromisoformat(record.get("updated_at")),
                metadata=record.get("metadata", {})
            )
            
            # Call the callbacks
            if conversation_id in self.on_turn_update:
                for callback in self.on_turn_update[conversation_id]:
                    await callback(turn)
                    
        except Exception as e:
            logger.error(f"Error handling turn update: {str(e)}")
    async def subscribe_to_user_conversations(
        self,
        user_id: str,
        on_update: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
        on_insert: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
        on_delete: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
    ) -> str:
        """
        Subscribe to conversations for a specific user.
        
        Args:
            user_id: ID of the user to subscribe to conversations for
            on_update: Callback for conversation updates
            on_insert: Callback for conversation inserts
            on_delete: Callback for conversation deletes
            
        Returns:
            Subscription ID
        """
        try:
            # Generate a subscription ID for this user
            subscription_id = f"user:{user_id}"
            
            # Initialize the subscription list if it doesn't exist
            if subscription_id not in self.user_subscriptions:
                self.user_subscriptions[subscription_id] = []
            
            # Subscribe to the events
            subscriptions = []
            
            if on_update:
                sub_id = await self.realtime_service.subscribe_to_table(
                    table=SubscriptionTable.CONVERSATIONS,
                    event=SubscriptionEvent.UPDATE,
                    callback=on_update,
                    filter_str=f"user_id=eq.{user_id}"
                )
                subscriptions.append(sub_id)
            
            if on_insert:
                sub_id = await self.realtime_service.subscribe_to_table(
                    table=SubscriptionTable.CONVERSATIONS,
                    event=SubscriptionEvent.INSERT,
                    callback=on_insert,
                    filter_str=f"user_id=eq.{user_id}"
                )
                subscriptions.append(sub_id)
            
            if on_delete:
                sub_id = await self.realtime_service.subscribe_to_table(
                    table=SubscriptionTable.CONVERSATIONS,
                    event=SubscriptionEvent.DELETE,
                    callback=on_delete,
                    filter_str=f"user_id=eq.{user_id}"
                )
                subscriptions.append(sub_id)
            
            # Store the subscription IDs
            self.user_subscriptions[subscription_id].extend(subscriptions)
            
            logger.info(f"Subscribed to conversations for user {user_id}")
            return subscription_id
            
        except Exception as e:
            logger.error(f"Failed to subscribe to conversations for user {user_id}: {str(e)}")
            raise
    
    async def subscribe_to_conversation_turns(
        self,
        conversation_id: str,
        on_insert: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
        on_update: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
        on_delete: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
    ) -> str:
        """
        Subscribe to turns for a specific conversation.
        
        Args:
            conversation_id: ID of the conversation to subscribe to turns for
            on_insert: Callback for turn inserts
            on_update: Callback for turn updates
            on_delete: Callback for turn deletes
            
        Returns:
            Subscription ID
        """
        try:
            # Generate a subscription ID for this conversation
            subscription_id = f"conversation:{conversation_id}"
            
            # Initialize the subscription list if it doesn't exist
            if subscription_id not in self.conversation_subscriptions:
                self.conversation_subscriptions[subscription_id] = []
            
            # Subscribe to the events
            subscriptions = []
            
            if on_insert:
                sub_id = await self.realtime_service.subscribe_to_table(
                    table=SubscriptionTable.CONVERSATION_TURNS,
                    event=SubscriptionEvent.INSERT,
                    callback=on_insert,
                    filter_str=f"conversation_id=eq.{conversation_id}"
                )
                subscriptions.append(sub_id)
            
            if on_update:
                sub_id = await self.realtime_service.subscribe_to_table(
                    table=SubscriptionTable.CONVERSATION_TURNS,
                    event=SubscriptionEvent.UPDATE,
                    callback=on_update,
                    filter_str=f"conversation_id=eq.{conversation_id}"
                )
                subscriptions.append(sub_id)
            
            if on_delete:
                sub_id = await self.realtime_service.subscribe_to_table(
                    table=SubscriptionTable.CONVERSATION_TURNS,
                    event=SubscriptionEvent.DELETE,
                    callback=on_delete,
                    filter_str=f"conversation_id=eq.{conversation_id}"
                )
                subscriptions.append(sub_id)
            
            # Store the subscription IDs
            self.conversation_subscriptions[subscription_id].extend(subscriptions)
            
            logger.info(f"Subscribed to turns for conversation {conversation_id}")
            return subscription_id
            
        except Exception as e:
            logger.error(f"Failed to subscribe to turns for conversation {conversation_id}: {str(e)}")
            raise
    
    async def unsubscribe_from_user_conversations(self, user_id: str) -> bool:
        """
        Unsubscribe from conversations for a specific user.
        
        Args:
            user_id: ID of the user to unsubscribe from conversations for
            
        Returns:
            True if unsubscribed successfully, False otherwise
        """
        try:
            # Generate the subscription ID for this user
            subscription_id = f"user:{user_id}"
            
            # Check if we have subscriptions for this user
            if subscription_id not in self.user_subscriptions:
                logger.warning(f"No subscriptions found for user {user_id}")
                return False
            
            # Unsubscribe from all subscriptions for this user
            for sub_id in self.user_subscriptions[subscription_id]:
                await self.realtime_service.unsubscribe(sub_id)
            
            # Remove the subscription list
            del self.user_subscriptions[subscription_id]
            
            logger.info(f"Unsubscribed from conversations for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe from conversations for user {user_id}: {str(e)}")
            return False
    
    async def unsubscribe_from_conversation_turns(self, conversation_id: str) -> bool:
        """
        Unsubscribe from turns for a specific conversation.
        
        Args:
            conversation_id: ID of the conversation to unsubscribe from turns for
            
        Returns:
            True if unsubscribed successfully, False otherwise
        """
        try:
            # Generate the subscription ID for this conversation
            subscription_id = f"conversation:{conversation_id}"
            
            # Check if we have subscriptions for this conversation
            if subscription_id not in self.conversation_subscriptions:
                logger.warning(f"No subscriptions found for conversation {conversation_id}")
                return False
            
            # Unsubscribe from all subscriptions for this conversation
            for sub_id in self.conversation_subscriptions[subscription_id]:
                await self.realtime_service.unsubscribe(sub_id)
            
            # Remove the subscription list
            del self.conversation_subscriptions[subscription_id]
            
            logger.info(f"Unsubscribed from turns for conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe from turns for conversation {conversation_id}: {str(e)}")
            return False


def create_conversation_realtime_service(
    supabase_client: Optional[Client] = None,
    realtime_service: Optional[RealtimeSubscriptionService] = None
) -> ConversationRealtimeService:
    """
    Create a conversation realtime service.
    
    Args:
        supabase_client: Optional Supabase client to use
        realtime_service: Optional RealtimeSubscriptionService instance
        
    Returns:
        Conversation realtime service
    """
    return ConversationRealtimeService(supabase_client, realtime_service)