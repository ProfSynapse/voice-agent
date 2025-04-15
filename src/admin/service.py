"""
Admin Service Module

This module provides functionality for admin operations.
"""

import logging
import datetime
import uuid
from typing import List, Dict, Optional, Any, Tuple

from loguru import logger

from src.admin.models import (
    SystemPrompt,
    UserSummary,
    PromptCategory,
    UserStatus,
    MetricsPeriod,
    ConversationMetrics
)
from src.conversation.models import PaginatedResult

class AdminService:
    """Service for admin operations."""
    
    def __init__(self, supabase_client, auth_service=None):
        """
        Initialize the admin service.
        
        Args:
            supabase_client: Supabase client
            auth_service: Optional auth service instance
        """
        self.supabase = supabase_client
        self.auth_service = auth_service
        
        if not auth_service:
            from src.auth.service import AuthService
            self.auth_service = AuthService(supabase_client)
            
        # Create a SupabaseTable instance for system_prompts
        from src.utils.supabase_client import SupabaseTable
        self.system_prompts_table = SupabaseTable(self.supabase, "system_prompts")
    
    async def create_system_prompt(
        self,
        created_by,
        name: str,
        content: str,
        category: str,
        is_default: bool = False
    ) -> Optional[SystemPrompt]:
        """
        Create a new system prompt
        
        Args:
            created_by: User creating the prompt
            name: Name/title of the prompt
            content: Prompt content
            category: Prompt category (string or PromptCategory)
            is_default: Whether this is a default prompt
            
        Returns:
            Newly created system prompt or None if creation failed
        """
        # Check admin permissions
        if hasattr(created_by, 'role') and created_by.role.value != 'admin':
            logger.error("Permission denied: User is not an admin")
            raise PermissionError("Only admin users can create system prompts")
            
        try:
            # Handle category - could be string or PromptCategory
            category_value = category
            if hasattr(category, 'value'):
                category_value = category.value
                
            # Create prompt in database
            prompt_data = {
                "created_by": created_by.id,
                "name": name,
                "content": content,
                "category": category_value,
                "is_default": is_default
            }
            
            # Use the table instance created in __init__
            prompt = await self.system_prompts_table.create(prompt_data)
            
            if not prompt:
                logger.error("Failed to create system prompt")
                return None
                
            # Create prompt object
            result = SystemPrompt(
                id=prompt["id"],
                created_by=prompt["created_by"],
                name=prompt["name"],
                content=prompt["content"],
                category=prompt["category"],
                is_default=prompt["is_default"],
                created_at=datetime.datetime.fromisoformat(prompt["created_at"]),
                updated_at=datetime.datetime.fromisoformat(prompt["updated_at"])
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Create system prompt error: {str(e)}")
            return None
    async def update_system_prompt(
        self,
        prompt_id: str,
        updated_by,
        name: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None,
        is_default: Optional[bool] = None
    ) -> Optional[SystemPrompt]:
        """
        Update an existing system prompt
        
        Args:
            prompt_id: ID of the prompt to update
            updated_by: User making the update
            name: New name (if changing)
            content: New content (if changing)
            category: New category (if changing)
            is_default: New default status (if changing)
            
        Returns:
            Updated system prompt or None if update failed
        """
        # Check admin permissions
        if hasattr(updated_by, 'role') and updated_by.role.value != 'admin':
            logger.error("Permission denied: User is not an admin")
            raise PermissionError("Only admin users can update system prompts")
            
        try:
            # Build update data
            update_data = {}
            
            if name is not None:
                update_data["name"] = name
                
            if content is not None:
                update_data["content"] = content
                
            if category is not None:
                # Handle category - could be string or PromptCategory
                category_value = category
                if hasattr(category, 'value'):
                    category_value = category.value
                update_data["category"] = category_value
                
            if is_default is not None:
                update_data["is_default"] = is_default
                
            if not update_data:
                # Nothing to update, get current prompt
                return await self.get_system_prompt(prompt_id)
                
            # Use the table instance created in __init__
            prompt = await self.system_prompts_table.update(prompt_id, update_data)
            
            if not prompt:
                logger.error(f"Failed to update system prompt: {prompt_id}")
                return None
                
            # Create prompt object
            result = SystemPrompt(
                id=prompt["id"],
                created_by=prompt["created_by"],
                name=prompt["name"],
                content=prompt["content"],
                category=prompt["category"],
                is_default=prompt["is_default"],
                created_at=datetime.datetime.fromisoformat(prompt["created_at"]),
                updated_at=datetime.datetime.fromisoformat(prompt["updated_at"])
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Update system prompt error: {str(e)}")
            return None
    
    async def delete_system_prompt(self, prompt_id: str, deleted_by) -> bool:
        """
        Delete a system prompt
        
        Args:
            prompt_id: ID of the prompt to delete
            deleted_by: User making the deletion request
            
        Returns:
            True if deletion was successful, False otherwise
        """
        # Check admin permissions
        if hasattr(deleted_by, 'role') and deleted_by.role.value != 'admin':
            logger.error("Permission denied: User is not an admin")
            raise PermissionError("Only admin users can delete system prompts")
            
        try:
            # Use the table instance created in __init__
            result = await self.system_prompts_table.delete(prompt_id)
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Delete system prompt error: {str(e)}")
            return False
    async def get_system_prompt(self, prompt_id: str) -> Optional[SystemPrompt]:
        """
        Get a system prompt by ID
        
        Args:
            prompt_id: ID of the prompt to retrieve
            
        Returns:
            System prompt or None if not found
        """
        try:
            # Use the table instance created in __init__
            prompt = await self.system_prompts_table.get_by_id(prompt_id)
            
            if not prompt:
                logger.error(f"System prompt not found: {prompt_id}")
                return None
                
            # Create prompt object
            result = SystemPrompt(
                id=prompt["id"],
                created_by=prompt["created_by"],
                name=prompt["name"],
                content=prompt["content"],
                category=prompt["category"],
                is_default=prompt["is_default"],
                created_at=datetime.datetime.fromisoformat(prompt["created_at"]),
                updated_at=datetime.datetime.fromisoformat(prompt["updated_at"])
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Get system prompt error: {str(e)}")
            return None
            
    async def get_all_system_prompts(self) -> List[SystemPrompt]:
        """
        Get all system prompts.
        
        Returns:
            List of all system prompts
        """
        try:
            # Use the table instance created in __init__
            response = await self.system_prompts_table.get_all()
            
            if not response:
                return []
                
            prompts = []
            for prompt_data in response:
                prompt = SystemPrompt(
                    id=prompt_data["id"],
                    created_by=prompt_data["created_by"],
                    name=prompt_data["name"],
                    content=prompt_data["content"],
                    category=prompt_data["category"],
                    is_default=prompt_data["is_default"],
                    created_at=datetime.datetime.fromisoformat(prompt_data["created_at"]),
                    updated_at=datetime.datetime.fromisoformat(prompt_data["updated_at"])
                )
                prompts.append(prompt)
            
            return prompts
            
        except Exception as e:
            logger.error(f"Get all system prompts error: {str(e)}")
            return []
            
    async def get_system_prompts_by_category(self, category: str) -> List[SystemPrompt]:
        """
        Get system prompts by category.
        
        Args:
            category: Category to filter by
            
        Returns:
            List of system prompts in the specified category
        """
        try:
            # Handle category - could be string or PromptCategory
            category_value = category
            if hasattr(category, 'value'):
                category_value = category.value
                
            # Use the table instance created in __init__
            filters = {"filters": [{"column": "category", "value": category_value}]}
            response = await self.system_prompts_table.get_all(filters)
            
            if not response:
                return []
                
            prompts = []
            for prompt_data in response:
                prompt = SystemPrompt(
                    id=prompt_data["id"],
                    created_by=prompt_data["created_by"],
                    name=prompt_data["name"],
                    content=prompt_data["content"],
                    category=prompt_data["category"],
                    is_default=prompt_data["is_default"],
                    created_at=datetime.datetime.fromisoformat(prompt_data["created_at"]),
                    updated_at=datetime.datetime.fromisoformat(prompt_data["updated_at"])
                )
                prompts.append(prompt)
            
            return prompts
            
        except Exception as e:
            logger.error(f"Get system prompts by category error: {str(e)}")
            return []
    
    async def list_system_prompts(
        self, 
        category: Optional[PromptCategory] = None,
        page: int = 1, 
        page_size: int = 10
    ) -> PaginatedResult:
        """
        List system prompts with pagination
        
        Args:
            category: Optional category to filter by
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            Paginated result with system prompts
        """
        try:
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Build query
            query = self.supabase.table("system_prompts").select("*", count="exact")
            
            if category:
                query = query.eq("category", category.value)
                
            # Get total count
            count_response = query.execute()
            total = count_response.count
            
            # Get paginated results
            response = query.order("name").range(offset, offset + page_size - 1).execute()
            
            prompts = []
            for prompt_data in response.data:
                prompt = SystemPrompt(
                    id=prompt_data["id"],
                    created_by=prompt_data["created_by"],
                    name=prompt_data["name"],
                    content=prompt_data["content"],
                    category=PromptCategory(prompt_data["category"]),
                    is_default=prompt_data["is_default"],
                    created_at=datetime.datetime.fromisoformat(prompt_data["created_at"]),
                    updated_at=datetime.datetime.fromisoformat(prompt_data["updated_at"])
                )
                prompts.append(prompt)
            
            # Create paginated result
            result = PaginatedResult(
                items=prompts,
                total=total,
                page=page,
                page_size=page_size,
                has_more=(offset + page_size) < total
            )
            
            return result
            
        except Exception as e:
            logger.error(f"List system prompts error: {str(e)}")
            return PaginatedResult([], 0, page, page_size, False)
    
    async def get_default_prompt(self, category: PromptCategory) -> Optional[SystemPrompt]:
        """
        Get the default prompt for a category
        
        Args:
            category: Prompt category
            
        Returns:
            Default system prompt or None if not found
        """
        try:
            # Get default prompt from database
            response = self.supabase.table("system_prompts").select("*").eq("category", category.value).eq("is_default", True).single().execute()
            
            if not response.data:
                logger.error(f"No default prompt found for category: {category.value}")
                return None
                
            prompt = response.data
            
            # Create prompt object
            result = SystemPrompt(
                id=prompt["id"],
                created_by=prompt["created_by"],
                name=prompt["name"],
                content=prompt["content"],
                category=PromptCategory(prompt["category"]),
                is_default=prompt["is_default"],
                created_at=datetime.datetime.fromisoformat(prompt["created_at"]),
                updated_at=datetime.datetime.fromisoformat(prompt["updated_at"])
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Get default prompt error: {str(e)}")
            return None
    
    async def set_default_system_prompt(self, prompt_id: str, updated_by) -> bool:
        """
        Set a prompt as the default for its category
        
        Args:
            prompt_id: ID of the prompt to set as default
            updated_by: User making the update
            
        Returns:
            True if successful, False otherwise
        """
        # Check admin permissions
        if hasattr(updated_by, 'role') and updated_by.role.value != 'admin':
            logger.error("Permission denied: User is not an admin")
            raise PermissionError("Only admin users can set default system prompts")
            
        try:
            # Get all prompts to find the current default in the same category
            prompts = await self.get_all_system_prompts()
            
            # Find the prompt we want to set as default
            target_prompt = None
            current_default_id = None
            
            for prompt in prompts:
                if prompt.id == prompt_id:
                    target_prompt = prompt
            
            if not target_prompt:
                logger.error(f"System prompt not found: {prompt_id}")
                return False
                
            # Find the current default in the same category
            for prompt in prompts:
                if prompt.is_default and prompt.category == target_prompt.category and prompt.id != prompt_id:
                    current_default_id = prompt.id
                    break
                
            # Use the table instance created in __init__
            
            # First, unset the current default if there is one
            if current_default_id:
                await self.system_prompts_table.update(current_default_id, {"is_default": False})
            
            # Then set the new default
            await self.system_prompts_table.update(prompt_id, {"is_default": True})
            
            return True
            
        except Exception as e:
            logger.error(f"Set default prompt error: {str(e)}")
            return False
    
    async def list_users(
        self, 
        page: int = 1, 
        page_size: int = 10,
        status: Optional[UserStatus] = None
    ) -> PaginatedResult:
        """
        List users with pagination
        
        Args:
            page: Page number (1-based)
            page_size: Number of items per page
            status: Optional status to filter by
            
        Returns:
            Paginated result with user summaries
        """
        try:
            # Check admin permissions
            if not await self.auth.is_admin():
                logger.error("Permission denied: User is not an admin")
                return PaginatedResult([], 0, page, page_size, False)
                
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Build query
            query = self.supabase.rpc(
                "get_user_summaries",
                {
                    "limit_param": page_size,
                    "offset_param": offset
                }
            )
            
            if status:
                query = query.eq("status", status.value)
                
            # Execute query
            response = query.execute()
            
            # Get total count (this would be handled differently in a real implementation)
            total_response = self.supabase.rpc(
                "get_user_count",
                {
                    "status_param": status.value if status else None
                }
            ).execute()
            
            total = total_response.data[0]["count"] if total_response.data else 0
            
            # Create user summaries
            users = []
            for user_data in response.data:
                user = UserSummary(
                    id=user_data["id"],
                    email=user_data["email"],
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                    status=UserStatus(user_data["status"]),
                    created_at=datetime.datetime.fromisoformat(user_data["created_at"]),
                    conversation_count=user_data["conversation_count"]
                )
                users.append(user)
            
            # Create paginated result
            result = PaginatedResult(
                items=users,
                total=total,
                page=page,
                page_size=page_size,
                has_more=(offset + page_size) < total
            )
            
            return result
            
        except Exception as e:
            logger.error(f"List users error: {str(e)}")
            return PaginatedResult([], 0, page, page_size, False)
    
    async def update_user_role(self, user_id: str, role: str) -> bool:
        """
        Update a user's role
        
        Args:
            user_id: ID of the user to update
            role: New role (user or admin)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check admin permissions
            if not await self.auth.is_admin():
                logger.error("Permission denied: User is not an admin")
                return False
                
            # Update user in database
            response = self.supabase.table("users").update(
                {"role": role}
            ).eq("id", user_id).execute()
            
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Update user role error: {str(e)}")
            return False
    
    async def update_user_status(self, user_id: str, status: UserStatus) -> bool:
        """
        Update a user's status (enable/disable account)
        
        Args:
            user_id: ID of the user to update
            status: New status
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check admin permissions
            if not await self.auth.is_admin():
                logger.error("Permission denied: User is not an admin")
                return False
                
            # Update user in database
            response = self.supabase.table("users").update(
                {"status": status.value}
            ).eq("id", user_id).execute()
            
            # If disabling, invalidate all sessions
            if status == UserStatus.DISABLED:
                self.supabase.auth.admin.delete_user(user_id)
            
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Update user status error: {str(e)}")
            return False
    
    async def get_conversation_metrics(
        self, 
        period: MetricsPeriod = MetricsPeriod.MONTH
    ) -> Optional[ConversationMetrics]:
        """
        Get conversation metrics for a time period
        
        Args:
            period: Time period for metrics
            
        Returns:
            Conversation metrics or None if retrieval failed
        """
        try:
            # Check admin permissions
            if not await self.auth.is_admin():
                logger.error("Permission denied: User is not an admin")
                return None
                
            # Calculate date range
            end_date = datetime.datetime.now()
            start_date = self._get_start_date_for_period(end_date, period)
            
            # Get metrics from database
            response = self.supabase.rpc(
                "get_conversation_metrics",
                {
                    "start_date_param": start_date.isoformat(),
                    "end_date_param": end_date.isoformat()
                }
            ).execute()
            
            if not response.data:
                logger.error("Failed to retrieve conversation metrics")
                return None
                
            metrics_data = response.data[0]
            
            # Create metrics object
            result = ConversationMetrics(
                total_conversations=metrics_data["total_conversations"],
                active_users=metrics_data["active_users"],
                total_turns=metrics_data["total_turns"],
                avg_turns_per_conversation=metrics_data["avg_turns_per_conversation"],
                avg_conversation_duration=metrics_data["avg_conversation_duration"],
                period=period,
                start_date=start_date,
                end_date=end_date
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Get conversation metrics error: {str(e)}")
            return None
    
    def _get_start_date_for_period(
        self, 
        end_date: datetime.datetime, 
        period: MetricsPeriod
    ) -> datetime.datetime:
        """
        Calculate the start date for a metrics period
        
        Args:
            end_date: End date of the period
            period: Time period
            
        Returns:
            Start date of the period
        """
        if period == MetricsPeriod.DAY:
            return end_date - datetime.timedelta(days=1)
        elif period == MetricsPeriod.WEEK:
            return end_date - datetime.timedelta(weeks=1)
        elif period == MetricsPeriod.MONTH:
            return end_date - datetime.timedelta(days=30)
        elif period == MetricsPeriod.YEAR:
            return end_date - datetime.timedelta(days=365)
        else:  # ALL
            return datetime.datetime(2000, 1, 1)  # Far in the past


def create_admin_service(supabase_client, auth_service, conversation_service=None):
    """
    Create and initialize the admin service
    
    Args:
        supabase_client: Initialized Supabase client
        auth_service: Authentication service for permission checks
        conversation_service: Optional conversation service for additional functionality
        
    Returns:
        Initialized AdminService instance
    """
    return AdminService(supabase_client, auth_service)