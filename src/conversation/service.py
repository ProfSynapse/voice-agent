"""
Conversation Service Module

This module provides functionality for managing conversations.
"""

import uuid
import datetime
import logging
from typing import List, Dict, Optional, Any, Tuple

from loguru import logger

from src.conversation.models import (
    Conversation,
    ConversationTurn,
    ConversationStatus,
    ConversationRole,
    ConversationSummary,
    PaginatedResult
)


class ConversationService:
    """Service for managing conversations."""
    
    def __init__(self, supabase_client, storage_service):
        """
        Initialize the conversation service.
        
        Args:
            supabase_client: Initialized Supabase client
            storage_service: Storage service for audio files
        """
        self.supabase = supabase_client
        self.storage = storage_service
    
    async def create_conversation(
        self, 
        user_id: str, 
        title: str,
        system_prompt_id: Optional[str] = None
    ) -> Optional[Conversation]:
        """
        Create a new conversation.
        
        Args:
            user_id: ID of the user creating the conversation
            title: Conversation title
            system_prompt_id: Optional ID of the system prompt to use
            
        Returns:
            Newly created conversation or None if creation failed
        """
        try:
            # Create conversation in database
            conversation_id = str(uuid.uuid4())
            conversation_data = {
                "id": conversation_id,
                "user_id": user_id,
                "title": title,
                "system_prompt_id": system_prompt_id,
                "status": ConversationStatus.ACTIVE.value
            }
            
            response = self.supabase.table("conversations").insert(conversation_data).execute()
            
            if not response.data:
                logger.error("Failed to create conversation")
                return None
                
            # Get the created conversation
            conversation = response.data[0]
            
            # Create conversation object
            result = Conversation(
                id=conversation["id"],
                user_id=conversation["user_id"],
                title=conversation["title"],
                system_prompt_id=conversation.get("system_prompt_id"),
                status=ConversationStatus(conversation["status"]),
                created_at=datetime.datetime.fromisoformat(conversation["created_at"]),
                updated_at=datetime.datetime.fromisoformat(conversation["updated_at"]),
                turns=[]
            )
            
            # If system prompt is provided, add a system turn
            if system_prompt_id:
                # Get the system prompt content
                prompt_response = self.supabase.table("system_prompts").select("content").eq("id", system_prompt_id).single().execute()
                
                if prompt_response.data:
                    prompt_content = prompt_response.data["content"]
                    
                    # Add system turn
                    await self.add_turn(
                        conversation_id=conversation_id,
                        role=ConversationRole.SYSTEM,
                        content=prompt_content
                    )
            
            return result
            
        except Exception as e:
            logger.error(f"Create conversation error: {str(e)}")
            return None
    
    async def get_conversation(
        self, 
        conversation_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Conversation]:
        """
        Get a conversation by ID.
        
        Args:
            conversation_id: ID of the conversation to retrieve
            user_id: Optional user ID for permission check
            
        Returns:
            Conversation or None if not found or not authorized
        """
        try:
            # Get conversation from database
            query = self.supabase.table("conversations").select("*").eq("id", conversation_id)
            
            if user_id:
                query = query.eq("user_id", user_id)
                
            response = query.single().execute()
            
            if not response.data:
                logger.error(f"Conversation not found: {conversation_id}")
                return None
                
            conversation_data = response.data
            
            # Get conversation turns
            turns_response = self.supabase.table("conversation_turns").select("*").eq("conversation_id", conversation_id).order("created_at").execute()
            
            turns_data = turns_response.data if turns_response.data else []
            
            # Create conversation object
            result = Conversation.from_dict(conversation_data, turns_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Get conversation error: {str(e)}")
            return None
    
    async def list_conversations(
        self, 
        user_id: str,
        status: Optional[ConversationStatus] = None,
        page: int = 1, 
        page_size: int = 10
    ) -> PaginatedResult:
        """
        List conversations for a user with pagination.
        
        Args:
            user_id: ID of the user
            status: Optional status to filter by
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            Paginated result with conversation summaries
        """
        try:
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Build query
            query = self.supabase.table("conversations").select("*", count="exact").eq("user_id", user_id)
            
            if status:
                query = query.eq("status", status.value)
                
            # Get total count
            count_response = query.execute()
            total = count_response.count
            
            # Get paginated results
            response = query.order("updated_at", desc=True).range(offset, offset + page_size - 1).execute()
            
            # Get last message for each conversation
            conversation_summaries = []
            for conversation_data in response.data:
                # Get last message
                last_message_response = self.supabase.table("conversation_turns").select("content").eq("conversation_id", conversation_data["id"]).neq("role", ConversationRole.SYSTEM.value).order("created_at", desc=True).limit(1).execute()
                
                last_message = None
                if last_message_response.data:
                    last_message = last_message_response.data[0]["content"]
                
                # Get turn count
                turn_count_response = self.supabase.table("conversation_turns").select("id", count="exact").eq("conversation_id", conversation_data["id"]).execute()
                
                turn_count = turn_count_response.count
                
                # Create summary
                summary_data = {
                    **conversation_data,
                    "turn_count": turn_count,
                    "last_message": last_message
                }
                
                summary = ConversationSummary.from_dict(summary_data)
                conversation_summaries.append(summary)
            
            # Create paginated result
            result = PaginatedResult(
                items=conversation_summaries,
                total=total,
                page=page,
                page_size=page_size,
                has_more=(offset + page_size) < total
            )
            
            return result
            
        except Exception as e:
            logger.error(f"List conversations error: {str(e)}")
            return PaginatedResult([], 0, page, page_size, False)
    
    async def update_conversation(
        self, 
        conversation_id: str, 
        user_id: str,
        title: Optional[str] = None,
        system_prompt_id: Optional[str] = None,
        status: Optional[ConversationStatus] = None
    ) -> Optional[Conversation]:
        """
        Update a conversation.
        
        Args:
            conversation_id: ID of the conversation to update
            user_id: ID of the user making the update
            title: New title (if changing)
            system_prompt_id: New system prompt ID (if changing)
            status: New status (if changing)
            
        Returns:
            Updated conversation or None if update failed
        """
        try:
            # Check if conversation exists and belongs to user
            check_response = self.supabase.table("conversations").select("id").eq("id", conversation_id).eq("user_id", user_id).execute()
            
            if not check_response.data:
                logger.error(f"Conversation not found or not owned by user: {conversation_id}")
                return None
                
            # Build update data
            update_data = {}
            
            if title is not None:
                update_data["title"] = title
                
            if system_prompt_id is not None:
                update_data["system_prompt_id"] = system_prompt_id
                
            if status is not None:
                update_data["status"] = status.value
                
            if not update_data:
                # Nothing to update, get current conversation
                return await self.get_conversation(conversation_id, user_id)
                
            # Update conversation in database
            response = self.supabase.table("conversations").update(update_data).eq("id", conversation_id).execute()
            
            if not response.data:
                logger.error(f"Failed to update conversation: {conversation_id}")
                return None
                
            # If system prompt changed, update system turn
            if system_prompt_id is not None:
                # Get the system prompt content
                prompt_response = self.supabase.table("system_prompts").select("content").eq("id", system_prompt_id).single().execute()
                
                if prompt_response.data:
                    prompt_content = prompt_response.data["content"]
                    
                    # Check if system turn exists
                    system_turn_response = self.supabase.table("conversation_turns").select("id").eq("conversation_id", conversation_id).eq("role", ConversationRole.SYSTEM.value).execute()
                    
                    if system_turn_response.data:
                        # Update existing system turn
                        system_turn_id = system_turn_response.data[0]["id"]
                        self.supabase.table("conversation_turns").update({"content": prompt_content}).eq("id", system_turn_id).execute()
                    else:
                        # Add new system turn
                        await self.add_turn(
                            conversation_id=conversation_id,
                            role=ConversationRole.SYSTEM,
                            content=prompt_content
                        )
            
            # Get updated conversation
            return await self.get_conversation(conversation_id, user_id)
            
        except Exception as e:
            logger.error(f"Update conversation error: {str(e)}")
            return None
    
    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """
        Delete a conversation (mark as deleted).
        
        Args:
            conversation_id: ID of the conversation to delete
            user_id: ID of the user making the deletion
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Check if conversation exists and belongs to user
            check_response = self.supabase.table("conversations").select("id").eq("id", conversation_id).eq("user_id", user_id).execute()
            
            if not check_response.data:
                logger.error(f"Conversation not found or not owned by user: {conversation_id}")
                return False
                
            # Mark conversation as deleted
            response = self.supabase.table("conversations").update(
                {"status": ConversationStatus.DELETED.value}
            ).eq("id", conversation_id).execute()
            
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Delete conversation error: {str(e)}")
            return False
    
    async def add_turn(
        self, 
        conversation_id: str, 
        role: ConversationRole, 
        content: str,
        audio_data: Optional[bytes] = None
    ) -> Optional[ConversationTurn]:
        """
        Add a turn to a conversation.
        
        Args:
            conversation_id: ID of the conversation
            role: Role of the speaker
            content: Turn content
            audio_data: Optional audio data
            
        Returns:
            Newly created turn or None if creation failed
        """
        try:
            # Check if conversation exists
            check_response = self.supabase.table("conversations").select("id").eq("id", conversation_id).execute()
            
            if not check_response.data:
                logger.error(f"Conversation not found: {conversation_id}")
                return None
                
            # Upload audio if provided
            audio_url = None
            if audio_data:
                turn_id = str(uuid.uuid4())
                audio_path = f"conversations/{conversation_id}/{turn_id}.mp3"
                
                upload_result = await self.storage.upload_audio(
                    audio_data=audio_data,
                    path=audio_path
                )
                
                if upload_result:
                    audio_url = upload_result
            
            # Create turn in database
            turn_data = {
                "id": turn_id if audio_data else str(uuid.uuid4()),
                "conversation_id": conversation_id,
                "role": role.value,
                "content": content,
                "audio_url": audio_url
            }
            
            response = self.supabase.table("conversation_turns").insert(turn_data).execute()
            
            if not response.data:
                logger.error("Failed to create conversation turn")
                return None
                
            # Get the created turn
            turn = response.data[0]
            
            # Update conversation updated_at
            self.supabase.table("conversations").update(
                {"updated_at": datetime.datetime.now().isoformat()}
            ).eq("id", conversation_id).execute()
            
            # Create turn object
            result = ConversationTurn(
                id=turn["id"],
                conversation_id=turn["conversation_id"],
                role=ConversationRole(turn["role"]),
                content=turn["content"],
                audio_url=turn.get("audio_url"),
                created_at=datetime.datetime.fromisoformat(turn["created_at"])
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Add turn error: {str(e)}")
            return None
    
    async def get_turn(self, turn_id: str) -> Optional[ConversationTurn]:
        """
        Get a conversation turn by ID.
        
        Args:
            turn_id: ID of the turn to retrieve
            
        Returns:
            Conversation turn or None if not found
        """
        try:
            # Get turn from database
            response = self.supabase.table("conversation_turns").select("*").eq("id", turn_id).single().execute()
            
            if not response.data:
                logger.error(f"Conversation turn not found: {turn_id}")
                return None
                
            turn = response.data
            
            # Create turn object
            result = ConversationTurn(
                id=turn["id"],
                conversation_id=turn["conversation_id"],
                role=ConversationRole(turn["role"]),
                content=turn["content"],
                audio_url=turn.get("audio_url"),
                created_at=datetime.datetime.fromisoformat(turn["created_at"])
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Get turn error: {str(e)}")
            return None
    
    async def search_conversations(
        self, 
        user_id: str,
        query: str,
        page: int = 1, 
        page_size: int = 10
    ) -> PaginatedResult:
        """
        Search conversations by content.
        
        Args:
            user_id: ID of the user
            query: Search query
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            Paginated result with conversation summaries
        """
        try:
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Search conversations using full-text search
            search_response = self.supabase.rpc(
                "search_conversations",
                {
                    "user_id_param": user_id,
                    "query_param": query,
                    "limit_param": page_size,
                    "offset_param": offset
                }
            ).execute()
            
            # Get total count
            count_response = self.supabase.rpc(
                "count_search_conversations",
                {
                    "user_id_param": user_id,
                    "query_param": query
                }
            ).execute()
            
            total = count_response.data[0]["count"] if count_response.data else 0
            
            # Create conversation summaries
            conversation_summaries = []
            for result_data in search_response.data:
                conversation_id = result_data["conversation_id"]
                
                # Get conversation data
                conversation_response = self.supabase.table("conversations").select("*").eq("id", conversation_id).single().execute()
                
                if conversation_response.data:
                    conversation_data = conversation_response.data
                    
                    # Get turn count
                    turn_count_response = self.supabase.table("conversation_turns").select("id", count="exact").eq("conversation_id", conversation_id).execute()
                    
                    turn_count = turn_count_response.count
                    
                    # Create summary
                    summary_data = {
                        **conversation_data,
                        "turn_count": turn_count,
                        "last_message": result_data["content"]  # Use matching content as last message
                    }
                    
                    summary = ConversationSummary.from_dict(summary_data)
                    conversation_summaries.append(summary)
            
            # Create paginated result
            result = PaginatedResult(
                items=conversation_summaries,
                total=total,
                page=page,
                page_size=page_size,
                has_more=(offset + page_size) < total
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Search conversations error: {str(e)}")
            return PaginatedResult([], 0, page, page_size, False)


def create_conversation_service(supabase_client, storage_service):
    """
    Create and initialize the conversation service.
    
    Args:
        supabase_client: Initialized Supabase client
        storage_service: Storage service for audio files
        
    Returns:
        Initialized ConversationService instance
    """
    return ConversationService(supabase_client, storage_service)