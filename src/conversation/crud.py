"""
Conversation CRUD Module

This module provides CRUD (Create, Read, Update, Delete) operations for conversations.
"""

import uuid
import datetime
from typing import List, Dict, Optional, Any, Tuple

from loguru import logger

from src.conversation.models import (
    Conversation,
    ConversationStatus,
    ConversationRole,
    ConversationSummary,
    PaginatedResult
)


class ConversationCRUDService:
    """Service for CRUD operations on conversations."""
    
    def __init__(self, supabase_client, field_encryption, error_handler):
        """
        Initialize the conversation CRUD service.
        
        Args:
            supabase_client: Initialized Supabase client
            field_encryption: Field encryption service
            error_handler: Secure error handler
        """
        self.supabase = supabase_client
        self.field_encryption = field_encryption
        self.error_handler = error_handler
        
        # Define fields that should be encrypted
        self.encrypted_fields = ["title"]
    
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
            
            # Encrypt sensitive fields
            encrypted_title = self.field_encryption.encrypt_field(title)
            
            conversation_data = {
                "id": conversation_id,
                "user_id": user_id,
                "title": encrypted_title,
                "system_prompt_id": system_prompt_id,
                "status": ConversationStatus.ACTIVE.value
            }
            
            response = self.supabase.table("conversations").insert(conversation_data).execute()
            
            if not response.data:
                logger.error("Failed to create conversation")
                return None
                
            # Get the created conversation
            conversation = response.data[0]
            
            # Decrypt sensitive fields
            decrypted_title = self.field_encryption.decrypt_field(conversation["title"])
            
            # Create conversation object
            result = Conversation(
                id=conversation["id"],
                user_id=conversation["user_id"],
                title=decrypted_title,
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
                    from src.conversation.turn import ConversationTurnService
                    turn_service = ConversationTurnService(self.supabase, None, self.field_encryption, self.error_handler)
                    await turn_service.add_turn(
                        conversation_id=conversation_id,
                        role=ConversationRole.SYSTEM,
                        content=prompt_content
                    )
            
            return result
            
        except Exception as e:
            error_info = self.error_handler.handle_exception(
                e, 
                context={"user_id": user_id, "operation": "create_conversation"}
            )
            logger.error(f"Create conversation error: {error_info['error']['message']}")
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
            
            # Decrypt sensitive fields in conversation data
            decrypted_conversation = conversation_data.copy()
            for field in self.encrypted_fields:
                if field in decrypted_conversation:
                    decrypted_conversation[field] = self.field_encryption.decrypt_field(decrypted_conversation[field])
            
            # Decrypt sensitive fields in turns data
            decrypted_turns = []
            for turn in turns_data:
                decrypted_turn = turn.copy()
                decrypted_turn["content"] = self.field_encryption.decrypt_field(turn["content"])
                decrypted_turns.append(decrypted_turn)
            
            # Create conversation object
            result = Conversation.from_dict(decrypted_conversation, decrypted_turns)
            
            return result
            
        except Exception as e:
            error_info = self.error_handler.handle_exception(
                e, 
                context={"conversation_id": conversation_id, "user_id": user_id, "operation": "get_conversation"}
            )
            logger.error(f"Get conversation error: {error_info['error']['message']}")
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
                # Decrypt sensitive fields
                decrypted_conversation = conversation_data.copy()
                for field in self.encrypted_fields:
                    if field in decrypted_conversation:
                        decrypted_conversation[field] = self.field_encryption.decrypt_field(decrypted_conversation[field])
                
                # Get last message
                last_message_response = self.supabase.table("conversation_turns").select("content").eq("conversation_id", conversation_data["id"]).neq("role", ConversationRole.SYSTEM.value).order("created_at", desc=True).limit(1).execute()
                
                last_message = None
                if last_message_response.data:
                    encrypted_message = last_message_response.data[0]["content"]
                    last_message = self.field_encryption.decrypt_field(encrypted_message)
                
                # Get turn count
                turn_count_response = self.supabase.table("conversation_turns").select("id", count="exact").eq("conversation_id", conversation_data["id"]).execute()
                
                turn_count = turn_count_response.count
                
                # Create summary
                summary_data = {
                    **decrypted_conversation,
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
            error_info = self.error_handler.handle_exception(
                e, 
                context={"user_id": user_id, "operation": "list_conversations"}
            )
            logger.error(f"List conversations error: {error_info['error']['message']}")
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
                # Encrypt title
                encrypted_title = self.field_encryption.encrypt_field(title)
                update_data["title"] = encrypted_title
                
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
                        # Encrypt content
                        encrypted_content = self.field_encryption.encrypt_field(prompt_content)
                        self.supabase.table("conversation_turns").update({"content": encrypted_content}).eq("id", system_turn_id).execute()
                    else:
                        # Add new system turn
                        from src.conversation.turn import ConversationTurnService
                        turn_service = ConversationTurnService(self.supabase, None, self.field_encryption, self.error_handler)
                        await turn_service.add_turn(
                            conversation_id=conversation_id,
                            role=ConversationRole.SYSTEM,
                            content=prompt_content
                        )
            
            # Get updated conversation
            return await self.get_conversation(conversation_id, user_id)
            
        except Exception as e:
            error_info = self.error_handler.handle_exception(
                e, 
                context={"conversation_id": conversation_id, "user_id": user_id, "operation": "update_conversation"}
            )
            logger.error(f"Update conversation error: {error_info['error']['message']}")
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
            error_info = self.error_handler.handle_exception(
                e, 
                context={"conversation_id": conversation_id, "user_id": user_id, "operation": "delete_conversation"}
            )
            logger.error(f"Delete conversation error: {error_info['error']['message']}")
            return False