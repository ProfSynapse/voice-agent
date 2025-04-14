# Conversation Management Module Pseudocode
# This module handles conversation state, storage, and retrieval

"""
TDD Test Cases:
- test_create_conversation: Verify a new conversation can be created
- test_save_conversation_turn: Verify conversation turns can be saved
- test_retrieve_conversation: Verify a conversation can be retrieved
- test_list_conversations: Verify conversations can be listed with pagination
- test_search_conversations: Verify conversations can be searched by text
- test_delete_conversation: Verify a conversation can be deleted
- test_export_conversation: Verify a conversation can be exported as text
- test_export_conversation_audio: Verify conversation audio can be exported
- test_conversation_title_generation: Verify titles are automatically generated
- test_conversation_categorization: Verify conversations can be categorized
"""

import os
import json
import logging
import datetime
from enum import Enum
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import uuid

# Configure logging
logger = logging.getLogger(__name__)

# Conversation turn role
class ConversationRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

# Export format
class ExportFormat(Enum):
    TEXT = "text"
    JSON = "json"
    AUDIO = "audio"

# Conversation turn
@dataclass
class ConversationTurn:
    id: str
    conversation_id: str
    role: ConversationRole
    content: str
    audio_url: Optional[str]
    created_at: datetime.datetime

# Conversation
@dataclass
class Conversation:
    id: str
    user_id: str
    title: str
    system_prompt_id: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    is_archived: bool
    turns: List[ConversationTurn]

# Pagination result
@dataclass
class PaginatedResult:
    items: List[Any]
    total: int
    page: int
    page_size: int
    has_more: bool

class ConversationService:
    def __init__(self, supabase_client, storage_service):
        """
        Initialize the conversation service
        
        Args:
            supabase_client: Initialized Supabase client
            storage_service: Storage service for audio files
        """
        self.supabase = supabase_client
        self.storage = storage_service
        self.current_conversation = None
    
    async def create_conversation(
        self, 
        user_id: str, 
        title: Optional[str] = None,
        system_prompt_id: Optional[str] = None
    ) -> Optional[Conversation]:
        """
        Create a new conversation
        
        Args:
            user_id: ID of the user creating the conversation
            title: Optional title for the conversation
            system_prompt_id: Optional ID of the system prompt to use
            
        Returns:
            Newly created conversation or None if creation failed
        """
        try:
            # Generate title if not provided
            if not title:
                title = f"Conversation {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # Create conversation in database
            conversation_data = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "title": title,
                "system_prompt_id": system_prompt_id,
                "is_archived": False
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
                system_prompt_id=conversation["system_prompt_id"],
                created_at=datetime.datetime.fromisoformat(conversation["created_at"]),
                updated_at=datetime.datetime.fromisoformat(conversation["updated_at"]),
                is_archived=conversation["is_archived"],
                turns=[]
            )
            
            # Set as current conversation
            self.current_conversation = result
            
            return result
            
        except Exception as e:
            logger.error(f"Create conversation error: {str(e)}")
            return None
    
    async def add_turn(
        self, 
        conversation_id: str, 
        role: ConversationRole, 
        content: str,
        audio_data: Optional[bytes] = None
    ) -> Optional[ConversationTurn]:
        """
        Add a turn to a conversation
        
        Args:
            conversation_id: ID of the conversation
            role: Role of the speaker (user or assistant)
            content: Text content of the turn
            audio_data: Optional audio data to store
            
        Returns:
            Newly created turn or None if creation failed
        """
        try:
            # Generate turn ID
            turn_id = str(uuid.uuid4())
            
            # Upload audio if provided
            audio_url = None
            if audio_data:
                audio_path = f"audio_recordings/{conversation_id}/{turn_id}.webm"
                upload_result = await self.storage.upload_file(audio_path, audio_data)
                
                if upload_result.success:
                    audio_url = upload_result.url
                    
                    # Create audio file record
                    audio_file_data = {
                        "id": str(uuid.uuid4()),
                        "turn_id": turn_id,
                        "file_path": audio_path,
                        "duration": upload_result.duration
                    }
                    
                    self.supabase.table("audio_files").insert(audio_file_data).execute()
            
            # Create turn in database
            turn_data = {
                "id": turn_id,
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
            
            # Update conversation updated_at timestamp
            self.supabase.table("conversations").update(
                {"updated_at": datetime.datetime.now().isoformat()}
            ).eq("id", conversation_id).execute()
            
            # Create turn object
            result = ConversationTurn(
                id=turn["id"],
                conversation_id=turn["conversation_id"],
                role=ConversationRole(turn["role"]),
                content=turn["content"],
                audio_url=turn["audio_url"],
                created_at=datetime.datetime.fromisoformat(turn["created_at"])
            )
            
            # Add to current conversation if it matches
            if self.current_conversation and self.current_conversation.id == conversation_id:
                self.current_conversation.turns.append(result)
                self.current_conversation.updated_at = datetime.datetime.now()
            
            return result
            
        except Exception as e:
            logger.error(f"Add turn error: {str(e)}")
            return None
    
    async def get_conversation(self, conversation_id: str, user_id: str) -> Optional[Conversation]:
        """
        Get a conversation by ID
        
        Args:
            conversation_id: ID of the conversation to retrieve
            user_id: ID of the user requesting the conversation
            
        Returns:
            Conversation object or None if not found
        """
        try:
            # Get conversation from database
            conversation_response = self.supabase.table("conversations").select("*").eq("id", conversation_id).eq("user_id", user_id).single().execute()
            
            if not conversation_response.data:
                logger.error(f"Conversation not found: {conversation_id}")
                return None
                
            conversation = conversation_response.data
            
            # Get turns for the conversation
            turns_response = self.supabase.table("conversation_turns").select("*").eq("conversation_id", conversation_id).order("created_at").execute()
            
            turns = []
            for turn_data in turns_response.data:
                turn = ConversationTurn(
                    id=turn_data["id"],
                    conversation_id=turn_data["conversation_id"],
                    role=ConversationRole(turn_data["role"]),
                    content=turn_data["content"],
                    audio_url=turn_data["audio_url"],
                    created_at=datetime.datetime.fromisoformat(turn_data["created_at"])
                )
                turns.append(turn)
            
            # Create conversation object
            result = Conversation(
                id=conversation["id"],
                user_id=conversation["user_id"],
                title=conversation["title"],
                system_prompt_id=conversation["system_prompt_id"],
                created_at=datetime.datetime.fromisoformat(conversation["created_at"]),
                updated_at=datetime.datetime.fromisoformat(conversation["updated_at"]),
                is_archived=conversation["is_archived"],
                turns=turns
            )
            
            # Set as current conversation
            self.current_conversation = result
            
            return result
            
        except Exception as e:
            logger.error(f"Get conversation error: {str(e)}")
            return None
    
    async def list_conversations(
        self, 
        user_id: str, 
        page: int = 1, 
        page_size: int = 10,
        archived: Optional[bool] = None
    ) -> PaginatedResult:
        """
        List conversations for a user with pagination
        
        Args:
            user_id: ID of the user
            page: Page number (1-based)
            page_size: Number of items per page
            archived: Filter by archived status (None for all)
            
        Returns:
            Paginated result with conversations
        """
        try:
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Build query
            query = self.supabase.table("conversations").select("*", count="exact").eq("user_id", user_id)
            
            if archived is not None:
                query = query.eq("is_archived", archived)
                
            # Get total count
            count_response = query.execute()
            total = count_response.count
            
            # Get paginated results
            response = query.order("updated_at", desc=True).range(offset, offset + page_size - 1).execute()
            
            conversations = []
            for conversation_data in response.data:
                conversation = Conversation(
                    id=conversation_data["id"],
                    user_id=conversation_data["user_id"],
                    title=conversation_data["title"],
                    system_prompt_id=conversation_data["system_prompt_id"],
                    created_at=datetime.datetime.fromisoformat(conversation_data["created_at"]),
                    updated_at=datetime.datetime.fromisoformat(conversation_data["updated_at"]),
                    is_archived=conversation_data["is_archived"],
                    turns=[]  # Don't load turns for list view
                )
                conversations.append(conversation)
            
            # Create paginated result
            result = PaginatedResult(
                items=conversations,
                total=total,
                page=page,
                page_size=page_size,
                has_more=(offset + page_size) < total
            )
            
            return result
            
        except Exception as e:
            logger.error(f"List conversations error: {str(e)}")
            return PaginatedResult([], 0, page, page_size, False)
    
    async def search_conversations(
        self, 
        user_id: str, 
        query: str, 
        page: int = 1, 
        page_size: int = 10
    ) -> PaginatedResult:
        """
        Search conversations by text content
        
        Args:
            user_id: ID of the user
            query: Search query
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            Paginated result with matching conversations
        """
        try:
            # This would use Supabase's text search capabilities
            # For pseudocode, we'll use a simplified approach
            
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Search in conversation turns
            turn_response = self.supabase.rpc(
                "search_conversation_turns",
                {
                    "search_query": query,
                    "user_id_param": user_id,
                    "limit_param": page_size,
                    "offset_param": offset
                }
            ).execute()
            
            # Get unique conversation IDs from results
            conversation_ids = list(set([turn["conversation_id"] for turn in turn_response.data]))
            
            if not conversation_ids:
                return PaginatedResult([], 0, page, page_size, False)
                
            # Get conversations by IDs
            conversation_response = self.supabase.table("conversations").select("*").in_("id", conversation_ids).eq("user_id", user_id).execute()
            
            conversations = []
            for conversation_data in conversation_response.data:
                conversation = Conversation(
                    id=conversation_data["id"],
                    user_id=conversation_data["user_id"],
                    title=conversation_data["title"],
                    system_prompt_id=conversation_data["system_prompt_id"],
                    created_at=datetime.datetime.fromisoformat(conversation_data["created_at"]),
                    updated_at=datetime.datetime.fromisoformat(conversation_data["updated_at"]),
                    is_archived=conversation_data["is_archived"],
                    turns=[]  # Don't load turns for list view
                )
                conversations.append(conversation)
            
            # Create paginated result
            # Note: This is simplified and doesn't handle total count correctly
            result = PaginatedResult(
                items=conversations,
                total=len(conversations),  # This would be the actual total in a real implementation
                page=page,
                page_size=page_size,
                has_more=False  # This would be calculated correctly in a real implementation
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Search conversations error: {str(e)}")
            return PaginatedResult([], 0, page, page_size, False)
    
    async def update_conversation(
        self, 
        conversation_id: str, 
        user_id: str, 
        title: Optional[str] = None,
        is_archived: Optional[bool] = None
    ) -> bool:
        """
        Update a conversation
        
        Args:
            conversation_id: ID of the conversation to update
            user_id: ID of the user making the update
            title: New title (if changing)
            is_archived: New archived status (if changing)
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Build update data
            update_data = {}
            
            if title is not None:
                update_data["title"] = title
                
            if is_archived is not None:
                update_data["is_archived"] = is_archived
                
            if not update_data:
                return True  # Nothing to update
                
            # Update conversation in database
            response = self.supabase.table("conversations").update(update_data).eq("id", conversation_id).eq("user_id", user_id).execute()
            
            success = bool(response.data)
            
            # Update current conversation if it matches
            if success and self.current_conversation and self.current_conversation.id == conversation_id:
                if title is not None:
                    self.current_conversation.title = title
                    
                if is_archived is not None:
                    self.current_conversation.is_archived = is_archived
                    
                self.current_conversation.updated_at = datetime.datetime.now()
            
            return success
            
        except Exception as e:
            logger.error(f"Update conversation error: {str(e)}")
            return False
    
    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """
        Delete a conversation (soft delete by archiving)
        
        Args:
            conversation_id: ID of the conversation to delete
            user_id: ID of the user making the deletion
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Soft delete by archiving
            response = self.supabase.table("conversations").update(
                {"is_archived": True}
            ).eq("id", conversation_id).eq("user_id", user_id).execute()
            
            success = bool(response.data)
            
            # Clear current conversation if it matches
            if success and self.current_conversation and self.current_conversation.id == conversation_id:
                self.current_conversation.is_archived = True
                self.current_conversation.updated_at = datetime.datetime.now()
            
            return success
            
        except Exception as e:
            logger.error(f"Delete conversation error: {str(e)}")
            return False
    
    async def export_conversation(
        self, 
        conversation_id: str, 
        user_id: str, 
        format: ExportFormat = ExportFormat.TEXT
    ) -> Optional[Dict[str, Any]]:
        """
        Export a conversation in the specified format
        
        Args:
            conversation_id: ID of the conversation to export
            user_id: ID of the user requesting the export
            format: Export format (text, json, or audio)
            
        Returns:
            Export data or None if export failed
        """
        try:
            # Get conversation
            conversation = await self.get_conversation(conversation_id, user_id)
            
            if not conversation:
                return None
                
            if format == ExportFormat.TEXT:
                # Export as text
                text_content = f"# {conversation.title}\n"
                text_content += f"Date: {conversation.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                
                for turn in conversation.turns:
                    speaker = "User" if turn.role == ConversationRole.USER else "Assistant"
                    text_content += f"{speaker}: {turn.content}\n\n"
                    
                return {
                    "content": text_content,
                    "filename": f"conversation_{conversation_id}.txt",
                    "mime_type": "text/plain"
                }
                
            elif format == ExportFormat.JSON:
                # Export as JSON
                json_data = {
                    "id": conversation.id,
                    "title": conversation.title,
                    "created_at": conversation.created_at.isoformat(),
                    "updated_at": conversation.updated_at.isoformat(),
                    "turns": [
                        {
                            "role": turn.role.value,
                            "content": turn.content,
                            "created_at": turn.created_at.isoformat()
                        }
                        for turn in conversation.turns
                    ]
                }
                
                return {
                    "content": json.dumps(json_data, indent=2),
                    "filename": f"conversation_{conversation_id}.json",
                    "mime_type": "application/json"
                }
                
            elif format == ExportFormat.AUDIO:
                # Export as audio (would combine all audio files)
                # This is a simplified placeholder
                audio_urls = [turn.audio_url for turn in conversation.turns if turn.audio_url]
                
                if not audio_urls:
                    return None
                    
                return {
                    "audio_urls": audio_urls,
                    "filename": f"conversation_{conversation_id}.zip",
                    "mime_type": "application/zip"
                }
                
            return None
            
        except Exception as e:
            logger.error(f"Export conversation error: {str(e)}")
            return None
    
    def get_current_conversation(self) -> Optional[Conversation]:
        """
        Get the current active conversation
        
        Returns:
            Current conversation or None if no active conversation
        """
        return self.current_conversation


# Factory function to create conversation service
def create_conversation_service(supabase_client, storage_service):
    """
    Create and initialize the conversation service
    
    Args:
        supabase_client: Initialized Supabase client
        storage_service: Storage service for audio files
        
    Returns:
        Initialized ConversationService instance
    """
    return ConversationService(supabase_client, storage_service)