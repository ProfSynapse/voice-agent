"""
Conversation Search API Module

This module provides API endpoints for searching conversations and turns
using the optimized full-text search capabilities.
"""

import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from pydantic import BaseModel, Field

from src.auth.service import get_current_user, User
from src.conversation.search import create_conversation_search_service, SearchResult
from src.conversation.models import Conversation, ConversationTurn, ConversationRole


# Pydantic models for request and response
class SearchRequest(BaseModel):
    """Search request model."""
    query: str = Field(..., description="Search query")
    limit: int = Field(10, description="Maximum number of results to return")
    offset: int = Field(0, description="Offset for pagination")
    min_similarity: float = Field(0.1, description="Minimum similarity threshold (0-1)")
    order_by: str = Field("relevance", description="Field to order by ('relevance', 'created_at', 'updated_at')")
    include_turns: bool = Field(False, description="Whether to include matching turns in the results")
    date_from: Optional[datetime] = Field(None, description="Optional start date for filtering")
    date_to: Optional[datetime] = Field(None, description="Optional end date for filtering")
    metadata_filters: Optional[Dict[str, Any]] = Field(None, description="Optional metadata filters")


class TurnSearchRequest(BaseModel):
    """Turn search request model."""
    query: str = Field(..., description="Search query")
    conversation_ids: Optional[List[str]] = Field(None, description="Optional list of conversation IDs to filter by")
    limit: int = Field(50, description="Maximum number of results to return")
    offset: int = Field(0, description="Offset for pagination")
    min_similarity: float = Field(0.1, description="Minimum similarity threshold (0-1)")
    order_by: str = Field("relevance", description="Field to order by ('relevance', 'created_at')")
    role: Optional[str] = Field(None, description="Optional role to filter by")
    date_from: Optional[datetime] = Field(None, description="Optional start date for filtering")
    date_to: Optional[datetime] = Field(None, description="Optional end date for filtering")
    metadata_filters: Optional[Dict[str, Any]] = Field(None, description="Optional metadata filters")


class ConversationModel(BaseModel):
    """Conversation model for API responses."""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    user_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationTurnModel(BaseModel):
    """Conversation turn model for API responses."""
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """Search response model."""
    conversations: List[ConversationModel] = Field(default_factory=list)
    turns: List[ConversationTurnModel] = Field(default_factory=list)
    total_conversations: int = 0
    total_turns: int = 0
    query: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Create router
router = APIRouter(
    prefix="/search",
    tags=["search"],
    responses={404: {"description": "Not found"}}
)


@router.post("/conversations", response_model=SearchResponse)
async def search_conversations(
    request: SearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Search for conversations using full-text search.
    
    Args:
        request: Search request
        current_user: Current authenticated user
        
    Returns:
        Search response with matching conversations and turns
    """
    # Create search service
    search_service = create_conversation_search_service()
    
    # Perform search
    result = await search_service.search_conversations(
        query=request.query,
        user_id=current_user.id,
        limit=request.limit,
        offset=request.offset,
        min_similarity=request.min_similarity,
        order_by=request.order_by,
        include_turns=request.include_turns,
        date_from=request.date_from,
        date_to=request.date_to,
        metadata_filters=request.metadata_filters
    )
    
    # Convert to response model
    response = SearchResponse(
        conversations=[
            ConversationModel(
                id=conv.id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                user_id=conv.user_id,
                metadata=conv.metadata
            )
            for conv in result.conversations
        ],
        turns=[
            ConversationTurnModel(
                id=turn.id,
                conversation_id=turn.conversation_id,
                role=turn.role.value,
                content=turn.content,
                created_at=turn.created_at,
                updated_at=turn.updated_at,
                metadata=turn.metadata
            )
            for turn in result.turns
        ],
        total_conversations=result.total_conversations,
        total_turns=result.total_turns,
        query=result.query,
        metadata=result.metadata
    )
    
    return response


@router.post("/turns", response_model=SearchResponse)
async def search_turns(
    request: TurnSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Search for conversation turns using full-text search.
    
    Args:
        request: Turn search request
        current_user: Current authenticated user
        
    Returns:
        Search response with matching turns
    """
    # Create search service
    search_service = create_conversation_search_service()
    
    # Convert role string to enum if provided
    role = None
    if request.role:
        try:
            role = ConversationRole(request.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {request.role}"
            )
    
    # Perform search
    result = await search_service.search_turns(
        query=request.query,
        conversation_ids=request.conversation_ids,
        user_id=current_user.id,
        limit=request.limit,
        offset=request.offset,
        min_similarity=request.min_similarity,
        order_by=request.order_by,
        role=role,
        date_from=request.date_from,
        date_to=request.date_to,
        metadata_filters=request.metadata_filters
    )
    
    # Convert to response model
    response = SearchResponse(
        turns=[
            ConversationTurnModel(
                id=turn.id,
                conversation_id=turn.conversation_id,
                role=turn.role.value,
                content=turn.content,
                created_at=turn.created_at,
                updated_at=turn.updated_at,
                metadata=turn.metadata
            )
            for turn in result.turns
        ],
        total_turns=result.total_turns,
        query=result.query,
        metadata=result.metadata
    )
    
    return response


@router.get("/conversations/{conversation_id}/turns", response_model=SearchResponse)
async def search_turns_in_conversation(
    conversation_id: str = Path(..., description="Conversation ID"),
    query: str = Query(..., description="Search query"),
    limit: int = Query(50, description="Maximum number of results to return"),
    offset: int = Query(0, description="Offset for pagination"),
    min_similarity: float = Query(0.1, description="Minimum similarity threshold (0-1)"),
    order_by: str = Query("relevance", description="Field to order by ('relevance', 'created_at')"),
    role: Optional[str] = Query(None, description="Optional role to filter by"),
    current_user: User = Depends(get_current_user)
):
    """
    Search for turns within a specific conversation using full-text search.
    
    Args:
        conversation_id: Conversation ID
        query: Search query
        limit: Maximum number of results to return
        offset: Offset for pagination
        min_similarity: Minimum similarity threshold (0-1)
        order_by: Field to order by ('relevance', 'created_at')
        role: Optional role to filter by
        current_user: Current authenticated user
        
    Returns:
        Search response with matching turns
    """
    # Create search service
    search_service = create_conversation_search_service()
    
    # Convert role string to enum if provided
    role_enum = None
    if role:
        try:
            role_enum = ConversationRole(role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role}"
            )
    
    # Perform search
    result = await search_service.search_turns(
        query=query,
        conversation_ids=[conversation_id],
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        min_similarity=min_similarity,
        order_by=order_by,
        role=role_enum
    )
    
    # Convert to response model
    response = SearchResponse(
        turns=[
            ConversationTurnModel(
                id=turn.id,
                conversation_id=turn.conversation_id,
                role=turn.role.value,
                content=turn.content,
                created_at=turn.created_at,
                updated_at=turn.updated_at,
                metadata=turn.metadata
            )
            for turn in result.turns
        ],
        total_turns=result.total_turns,
        query=query,
        metadata=result.metadata
    )
    
    return response