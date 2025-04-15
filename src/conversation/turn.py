"""
Conversation Turn Module

This module provides functionality for managing conversation turns.
"""

import uuid
import datetime
from typing import List, Dict, Optional, Any

from loguru import logger

from src.conversation.models import (
    ConversationTurn,
    ConversationRole
)


class ConversationTurnService:
    """Service for managing conversation turns."""
    
    def __init__(self, supabase_client, storage_service, field_encryption, error_handler):
        """
        Initialize the conversation turn service.
        
        Args:
            supabase_client: Initialized Supabase client
            storage_service: Storage service for audio files
            field_encryption: Field encryption service
            error_handler: Secure error handler
        """
        self.supabase = supabase_client
        self.storage = storage_service
        self.field_encryption = field_encryption
        self.error_handler = error_handler
        
        # Define fields that should be encrypted
        self.encrypted_fields = ["content"]
    
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
            turn_id = str(uuid.uuid4())
            
            if audio_data and self.storage:
                audio_path = f"conversations/{conversation_id}/{turn_id}.mp3"
                
                upload_result = await self.storage.upload_audio(
                    audio_data=audio_data,
                    path=audio_path
                )
                
                if upload_result:
                    audio_url = upload_result
            
            # Encrypt content
            encrypted_content = self.field_encryption.encrypt_field(content)
            
            # Create turn in database
            turn_data = {
                "id": turn_id,
                "conversation_id": conversation_id,
                "role": role.value,
                "content": encrypted_content,
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
            
            # Create turn object with decrypted content
            result = ConversationTurn(
                id=turn["id"],
                conversation_id=turn["conversation_id"],
                role=ConversationRole(turn["role"]),
                content=content,  # Use original content instead of decrypting
                audio_url=turn.get("audio_url"),
                created_at=datetime.datetime.fromisoformat(turn["created_at"])
            )
            
            return result
            
        except Exception as e:
            error_info = self.error_handler.handle_exception(
                e, 
                context={
                    "conversation_id": conversation_id, 
                    "role": role.value, 
                    "operation": "add_turn"
                }
            )
            logger.error(f"Add turn error: {error_info['error']['message']}")
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
            
            # Decrypt content
            decrypted_content = self.field_encryption.decrypt_field(turn["content"])
            
            # Create turn object
            result = ConversationTurn(
                id=turn["id"],
                conversation_id=turn["conversation_id"],
                role=ConversationRole(turn["role"]),
                content=decrypted_content,
                audio_url=turn.get("audio_url"),
                created_at=datetime.datetime.fromisoformat(turn["created_at"])
            )
            
            return result
            
        except Exception as e:
            error_info = self.error_handler.handle_exception(
                e, 
                context={"turn_id": turn_id, "operation": "get_turn"}
            )
            logger.error(f"Get turn error: {error_info['error']['message']}")
            return None
    
    async def update_turn(
        self, 
        turn_id: str, 
        content: Optional[str] = None,
        audio_data: Optional[bytes] = None
    ) -> Optional[ConversationTurn]:
        """
        Update a conversation turn.
        
        Args:
            turn_id: ID of the turn to update
            content: New content (if changing)
            audio_data: New audio data (if changing)
            
        Returns:
            Updated turn or None if update failed
        """
        try:
            # Get the turn to update
            get_response = self.supabase.table("conversation_turns").select("*").eq("id", turn_id).single().execute()
            
            if not get_response.data:
                logger.error(f"Conversation turn not found: {turn_id}")
                return None
                
            turn = get_response.data
            conversation_id = turn["conversation_id"]
            
            # Build update data
            update_data = {}
            
            if content is not None:
                # Encrypt content
                encrypted_content = self.field_encryption.encrypt_field(content)
                update_data["content"] = encrypted_content
                
            # Upload new audio if provided
            if audio_data and self.storage:
                audio_path = f"conversations/{conversation_id}/{turn_id}.mp3"
                
                upload_result = await self.storage.upload_audio(
                    audio_data=audio_data,
                    path=audio_path
                )
                
                if upload_result:
                    update_data["audio_url"] = upload_result
            
            if not update_data:
                # Nothing to update, return current turn
                return await self.get_turn(turn_id)
                
            # Update turn in database
            response = self.supabase.table("conversation_turns").update(update_data).eq("id", turn_id).execute()
            
            if not response.data:
                logger.error(f"Failed to update conversation turn: {turn_id}")
                return None
                
            # Update conversation updated_at
            self.supabase.table("conversations").update(
                {"updated_at": datetime.datetime.now().isoformat()}
            ).eq("id", conversation_id).execute()
            
            # Get updated turn
            return await self.get_turn(turn_id)
            
        except Exception as e:
            error_info = self.error_handler.handle_exception(
                e, 
                context={"turn_id": turn_id, "operation": "update_turn"}
            )
            logger.error(f"Update turn error: {error_info['error']['message']}")
            return None
    
    async def delete_turn(self, turn_id: str) -> bool:
        """
        Delete a conversation turn.
        
        Args:
            turn_id: ID of the turn to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Get the turn to delete
            get_response = self.supabase.table("conversation_turns").select("*").eq("id", turn_id).single().execute()
            
            if not get_response.data:
                logger.error(f"Conversation turn not found: {turn_id}")
                return False
                
            turn = get_response.data
            conversation_id = turn["conversation_id"]
            
            # Delete audio file if exists
            if turn.get("audio_url") and self.storage:
                audio_path = f"conversations/{conversation_id}/{turn_id}.mp3"
                await self.storage.delete_file(audio_path)
            
            # Delete turn from database
            response = self.supabase.table("conversation_turns").delete().eq("id", turn_id).execute()
            
            if not response.data:
                logger.error(f"Failed to delete conversation turn: {turn_id}")
                return False
                
            # Update conversation updated_at
            self.supabase.table("conversations").update(
                {"updated_at": datetime.datetime.now().isoformat()}
            ).eq("id", conversation_id).execute()
            
            return True
            
        except Exception as e:
            error_info = self.error_handler.handle_exception(
                e, 
                context={"turn_id": turn_id, "operation": "delete_turn"}
            )
            logger.error(f"Delete turn error: {error_info['error']['message']}")
            return False
    
    async def list_turns(
        self, 
        conversation_id: str,
        page: int = 1,
        page_size: int = 50
    ) -> List[ConversationTurn]:
        """
        List turns for a conversation with pagination.
        
        Args:
            conversation_id: ID of the conversation
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            List of conversation turns
        """
        try:
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Get paginated turns
            response = self.supabase.table("conversation_turns").select("*").eq("conversation_id", conversation_id).order("created_at").range(offset, offset + page_size - 1).execute()
            
            if not response.data:
                return []
                
            turns = []
            for turn_data in response.data:
                # Decrypt content
                decrypted_content = self.field_encryption.decrypt_field(turn_data["content"])
                
                # Create turn object
                turn = ConversationTurn(
                    id=turn_data["id"],
                    conversation_id=turn_data["conversation_id"],
                    role=ConversationRole(turn_data["role"]),
                    content=decrypted_content,
                    audio_url=turn_data.get("audio_url"),
                    created_at=datetime.datetime.fromisoformat(turn_data["created_at"])
                )
                
                turns.append(turn)
                
            return turns
            
        except Exception as e:
            error_info = self.error_handler.handle_exception(
                e, 
                context={"conversation_id": conversation_id, "operation": "list_turns"}
            )
            logger.error(f"List turns error: {error_info['error']['message']}")
            return []