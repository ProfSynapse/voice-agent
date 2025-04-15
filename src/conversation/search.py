"""
Conversation Search Module

This module provides optimized full-text search functionality for conversations
and conversation turns using Supabase's tsvector capabilities.
"""

import json
import enum
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime

from loguru import logger
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

from src.config.config_service import get_config_service
from src.conversation.models import Conversation, ConversationTurn, ConversationRole, PaginatedResult, ConversationSummary, ConversationStatus


class SearchSortOrder(enum.Enum):
    """Sort order for search results."""
    RELEVANCE = "relevance"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    NEWEST = "newest"


class SearchFilter(enum.Enum):
    """Filter types for search."""
    USER = "user"
    DATE_RANGE = "date_range"
    METADATA = "metadata"
    ROLE = "role"
    TITLE = "title"
    CONTENT = "content"
    NEWEST = "newest"


class SearchResult(PaginatedResult):
    """
    Search result container.
    
    Attributes:
        items: List of matching items (conversations or turns)
        total: Total number of matching items
        page: Current page number
        page_size: Number of items per page
        has_more: Whether there are more items
        query: Original search query
        metadata: Additional metadata about the search
    """
    
    def __init__(
        self,
        items: List[Any] = None,
        total: int = 0,
        page: int = 1,
        page_size: int = 10,
        query: str = "",
        metadata: Dict[str, Any] = None
    ):
        """
        Initialize a search result.
        
        Args:
            items: List of matching items (conversations or turns)
            total: Total number of matching items
            page: Current page number
            page_size: Number of items per page
            query: Original search query
            metadata: Additional metadata about the search
        """
        has_more = total > (page * page_size)
        super().__init__(
            items=items or [],
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )
        self.query = query
        self.metadata = metadata or {}
        
    @classmethod
    def from_conversations(
        cls,
        conversations: List[Conversation] = None,
        total: int = 0,
        page: int = 1,
        page_size: int = 10,
        query: str = "",
        metadata: Dict[str, Any] = None
    ) -> 'SearchResult':
        """Create a search result from conversations."""
        return cls(
            items=conversations or [],
            total=total,
            page=page,
            page_size=page_size,
            query=query,
            metadata=metadata
        )
        
    @classmethod
    def from_turns(
        cls,
        turns: List[ConversationTurn] = None,
        total: int = 0,
        page: int = 1,
        page_size: int = 10,
        query: str = "",
        metadata: Dict[str, Any] = None
    ) -> 'SearchResult':
        """Create a search result from turns."""
        return cls(
            items=turns or [],
            total=total,
            page=page,
            page_size=page_size,
            query=query,
            metadata=metadata
        )


class ConversationSearchService:
    """
    Service for searching conversations and turns using full-text search.
    
    This service uses Supabase's tsvector capabilities for efficient
    and relevant full-text search across conversations and turns.
    """
    
    def __init__(self, supabase_client: Optional[Client] = None):
        """
        Initialize the conversation search service.
        
        Args:
            supabase_client: Optional Supabase client to use
        """
        self.config = get_config_service()
        
        # Initialize Supabase client if not provided
        if supabase_client:
            self.supabase = supabase_client
        else:
            supabase_config = self.config.supabase_config
            self.supabase = create_client(
                supabase_config["url"],
                supabase_config["anon_key"]
            )
        
        logger.info("Conversation search service initialized")
    
    async def search_conversations(
        self,
        query: str,
        user_id: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
        min_similarity: float = 0.1,
        order_by: Union[str, SearchSortOrder] = SearchSortOrder.RELEVANCE,
        sort_order: Union[str, SearchSortOrder] = None,
        include_turns: bool = False,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        metadata_filters: Optional[Dict[str, Any]] = None,
        filters: Optional[List[Dict[str, Any]]] = None
    ) -> SearchResult:
        """
        Search for conversations using full-text search.
        
        Args:
            query: Search query
            user_id: Optional user ID to filter by
            limit: Maximum number of results to return
            offset: Offset for pagination
            min_similarity: Minimum similarity threshold (0-1)
            order_by: Field to order by ('relevance', 'created_at', 'updated_at')
            include_turns: Whether to include matching turns in the results
            date_from: Optional start date for filtering
            date_to: Optional end date for filtering
            metadata_filters: Optional metadata filters
            
        Returns:
            Search result containing matching conversations and turns
        """
        try:
            # Handle pagination parameters
            if page is not None and page_size is not None:
                offset = (page - 1) * page_size
                limit = page_size
                
            # Prepare search query
            search_query = self._prepare_search_query(query)
            
            # Use sort_order if provided, otherwise use order_by
            effective_order_by = sort_order if sort_order is not None else order_by
            
            # Initialize parameters for RPC call
            rpc_params = {
                "user_id_param": user_id,
                "query_param": search_query,
                "limit_param": limit,
                "offset_param": offset,
                "min_similarity_param": min_similarity
            }
            
            # Add date filters if provided
            if date_from:
                rpc_params["start_date"] = date_from.isoformat()
            if date_to:
                rpc_params["end_date"] = date_to.isoformat()
            
            # Add metadata filters if provided
            if metadata_filters:
                rpc_params["metadata_filters"] = json.dumps(metadata_filters)
            
            # Set ordering
            order_by_value = effective_order_by.value if isinstance(effective_order_by, SearchSortOrder) else effective_order_by
            rpc_params["sort_order"] = order_by_value
            
            # Process filters if provided
            if filters:
                for filter_type, filter_value in filters.items():
                    if filter_type == SearchFilter.TITLE:
                        rpc_params["title_only"] = filter_value
                    elif filter_type == SearchFilter.CONTENT:
                        rpc_params["content_only"] = filter_value
                    elif filter_type == SearchFilter.NEWEST:
                        rpc_params["sort_order"] = "newest"
                    elif filter_type == SearchFilter.DATE_RANGE and isinstance(filter_value, dict):
                        if "start_date" in filter_value:
                            rpc_params["start_date"] = filter_value["start_date"].isoformat()
                        if "end_date" in filter_value:
                            rpc_params["end_date"] = filter_value["end_date"].isoformat()
            
            # Get paginated results
            result = await self.supabase.rpc(
                "search_conversations_enhanced",
                rpc_params
            ).execute()
            
            # Get total count
            count_result = await self.supabase.rpc(
                "count_search_conversations_enhanced",
                {
                    "user_id_param": user_id,
                    "query_param": search_query,
                    **({k: v for k, v in rpc_params.items() if k not in ["limit_param", "offset_param"]})
                }
            ).execute()
            
            total_conversations = count_result.data[0]["count"] if count_result.data else 0
            
            # Parse conversations
            conversations = []
            for record in result.data:
                conversation = ConversationSummary(
                    id=record.get("conversation_id"),
                    user_id=user_id,
                    title=record.get("title"),
                    status=ConversationStatus.ACTIVE,  # Default to active
                    created_at=datetime.fromisoformat(record.get("created_at")),
                    updated_at=datetime.fromisoformat(record.get("updated_at")),
                    turn_count=record.get("turn_count", 0),
                    last_message=record.get("last_message"),
                    relevance=record.get("relevance", 0.0)
                )
                conversations.append(conversation)
            
            # Initialize search result
            page_num = (offset // limit) + 1 if limit > 0 else 1
            search_result = SearchResult.from_conversations(
                conversations=conversations,
                total=total_conversations,
                page=page_num,
                page_size=limit,
                query=query,
                metadata={
                    "min_similarity": min_similarity,
                    "order_by": order_by_value if isinstance(order_by_value, str) else order_by_value.value
                }
            )
            
            # Include matching turns if requested
            if include_turns and conversations:
                conversation_ids = [conv.id for conv in conversations]
                turns_result = await self.search_turns(
                    query=query,
                    conversation_ids=conversation_ids,
                    limit=limit * 5,  # Get more turns than conversations
                    min_similarity=min_similarity
                )
                search_result.turns = turns_result.turns
                search_result.total_turns = turns_result.total_turns
            
            return search_result
            
        except Exception as e:
            logger.error(f"Error searching conversations: {str(e)}")
            return SearchResult(query=query)
    
    async def search_turns(
        self,
        query: str,
        conversation_ids: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
        min_similarity: float = 0.1,
        order_by: Union[str, SearchSortOrder] = SearchSortOrder.RELEVANCE,
        role: Optional[ConversationRole] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        metadata_filters: Optional[Dict[str, Any]] = None
    ) -> SearchResult:
        """
        Search for conversation turns using full-text search.
        
        Args:
            query: Search query
            conversation_ids: Optional list of conversation IDs to filter by
            user_id: Optional user ID to filter by
            page: Optional page number (1-based)
            page_size: Optional number of results per page
            limit: Maximum number of results to return (used if page/page_size not provided)
            offset: Offset for pagination (used if page/page_size not provided)
            min_similarity: Minimum similarity threshold (0-1)
            order_by: Field to order by ('relevance', 'created_at')
            role: Optional role to filter by
            date_from: Optional start date for filtering
            date_to: Optional end date for filtering
            metadata_filters: Optional metadata filters
            
        Returns:
            Search result containing matching turns
        """
        try:
            # Handle pagination parameters
            if page is not None and page_size is not None:
                offset = (page - 1) * page_size
                limit = page_size
                
            # Prepare search query
            search_query = self._prepare_search_query(query)
            
            # Initialize parameters for RPC call
            rpc_params = {
                "query_param": search_query,
                "limit_param": limit,
                "offset_param": offset,
                "min_similarity_param": min_similarity
            }
            
            # Add conversation filter if provided
            if conversation_ids and len(conversation_ids) == 1:
                rpc_params["conversation_id_param"] = conversation_ids[0]
            elif conversation_ids:
                rpc_params["conversation_ids"] = json.dumps(conversation_ids)
            
            # Add user filter if provided
            if user_id:
                rpc_params["user_id_param"] = user_id
            
            # Add role filter if provided
            if role:
                rpc_params["role_param"] = role.value
            
            # Add date filters if provided
            if date_from:
                rpc_params["start_date"] = date_from.isoformat()
            if date_to:
                rpc_params["end_date"] = date_to.isoformat()
            
            # Add metadata filters if provided
            if metadata_filters:
                rpc_params["metadata_filters"] = json.dumps(metadata_filters)
            
            # Set ordering
            order_by_value = order_by.value if isinstance(order_by, SearchSortOrder) else order_by
            rpc_params["sort_order"] = order_by_value
            
            # Get paginated results
            result = await self.supabase.rpc(
                "search_conversation_turns",
                rpc_params
            ).execute()
            
            # Get total count
            count_result = await self.supabase.rpc(
                "count_search_conversation_turns",
                {k: v for k, v in rpc_params.items() if k not in ["limit_param", "offset_param"]}
            ).execute()
            
            total_turns = count_result.data[0]["count"] if count_result.data else 0
            
            # Parse turns
            turns = []
            for record in result.data:
                turn = ConversationTurn(
                    id=record.get("id"),
                    conversation_id=record.get("conversation_id"),
                    role=ConversationRole(record.get("role")),
                    content=record.get("content"),
                    created_at=datetime.fromisoformat(record.get("created_at")),
                    updated_at=datetime.fromisoformat(record.get("updated_at")),
                    metadata=record.get("metadata", {})
                )
                turns.append(turn)
            
            # Create search result
            page_num = (offset // limit) + 1 if limit > 0 else 1
            search_result = SearchResult.from_turns(
                turns=turns,
                total=total_turns,
                page=page_num,
                page_size=limit,
                query=query,
                metadata={
                    "min_similarity": min_similarity,
                    "order_by": order_by
                }
            )
            
            return search_result
            
        except Exception as e:
            logger.error(f"Error searching turns: {str(e)}")
            return SearchResult(query=query)
    
    async def search_conversation_turns(
        self,
        conversation_id: str,
        query: str,
        page: int = 1,
        page_size: int = 10,
        min_similarity: float = 0.1,
        order_by: Union[str, SearchSortOrder] = SearchSortOrder.RELEVANCE,
        role: Optional[ConversationRole] = None,
        filters: Optional[Dict[SearchFilter, Any]] = None
    ) -> SearchResult:
        """
        Search for turns within a specific conversation.
        
        Args:
            conversation_id: ID of the conversation to search within
            query: Search query
            page: Page number (1-based)
            page_size: Number of results per page
            min_similarity: Minimum similarity threshold (0-1)
            order_by: Field to order by
            role: Optional role to filter by
            filters: Optional filters to apply
            
        Returns:
            Search result containing matching turns
        """
        # Initialize parameters for RPC call
        rpc_params = {
            "conversation_id_param": conversation_id,
            "query_param": self._prepare_search_query(query),
            "limit_param": page_size,
            "offset_param": (page - 1) * page_size,
            "min_similarity_param": min_similarity,
            "sort_order": order_by.value if isinstance(order_by, SearchSortOrder) else order_by
        }
        
        if role:
            rpc_params["role_param"] = role.value
            
        # Process filters if provided
        if filters:
            for filter_type, filter_value in filters.items():
                if filter_type == SearchFilter.CONTENT:
                    rpc_params["content_only"] = filter_value
                elif filter_type == SearchFilter.NEWEST:
                    rpc_params["sort_order"] = "newest"
        
        try:
            # Get paginated results
            result = await self.supabase.rpc(
                "search_conversation_turns",
                rpc_params
            ).execute()
            
            # Get total count
            count_result = await self.supabase.rpc(
                "count_search_conversation_turns",
                {k: v for k, v in rpc_params.items() if k not in ["limit_param", "offset_param"]}
            ).execute()
            
            total_turns = count_result.data[0]["count"] if count_result.data else 0
            
            # Parse turns
            turns = []
            for record in result.data:
                turn = ConversationTurn(
                    id=record.get("id"),
                    conversation_id=record.get("conversation_id"),
                    role=ConversationRole(record.get("role")),
                    content=record.get("content"),
                    audio_url=record.get("audio_url"),
                    created_at=datetime.fromisoformat(record.get("created_at"))
                )
                turns.append(turn)
            
            # Create search result
            search_result = SearchResult.from_turns(
                turns=turns,
                total=total_turns,
                page=page,
                page_size=page_size,
                query=query,
                metadata={
                    "min_similarity": min_similarity,
                    "order_by": rpc_params["sort_order"]
                }
            )
            
            return search_result
            
        except Exception as e:
            logger.error(f"Error searching conversation turns: {str(e)}")
            return SearchResult(query=query)
    
    def _prepare_search_query(self, query: str, partial: bool = False) -> str:
        """
        Prepare a search query for use with tsvector.
        
        Args:
            query: Raw search query
            partial: Whether to prepare for partial matching (for suggestions)
            
        Returns:
            Formatted search query for tsvector
        """
        # Remove special characters and convert to lowercase
        clean_query = query.lower()
        clean_query = ''.join(c for c in clean_query if c.isalnum() or c.isspace())
        
        # Split into words
        words = clean_query.split()
        
        # For partial search, add :* to all words for prefix matching
        if words:
            if partial:
                words = [word + ":*" for word in words]
            
            # Join with '&' for AND search
            formatted_query = ' & '.join(words)
            return formatted_query
        
        return ""

    async def get_search_suggestions(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> List[str]:
        """
        Get search suggestions based on a partial query.
        
        Args:
            user_id: User ID to get suggestions for
            query: Partial search query
            limit: Maximum number of suggestions to return
            
        Returns:
            List of search suggestions
        """
        try:
            if not query or len(query.strip()) < 2:
                return []
                
            # Prepare partial search query
            search_query = self._prepare_search_query(query, partial=True)
            
            # Execute suggestion query
            result = await self.supabase.rpc(
                "get_search_suggestions",
                {
                    "user_id_param": user_id,
                    "query_param": search_query,
                    "limit_param": limit
                }
            ).execute()
            
            # Extract suggestions
            suggestions = []
            for item in result.data:
                suggestion = item.get("suggestion")
                if suggestion:
                    suggestions.append(suggestion)
                    
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting search suggestions: {str(e)}")
            return []


def create_conversation_search_service(supabase_client: Optional[Client] = None) -> ConversationSearchService:
    """
    Create a conversation search service.
    
    Args:
        supabase_client: Optional Supabase client to use
        
    Returns:
        Conversation search service
    """
    return ConversationSearchService(supabase_client)

# Alias for backward compatibility with tests
SearchService = ConversationSearchService