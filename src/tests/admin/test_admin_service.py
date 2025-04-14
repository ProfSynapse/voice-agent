"""
Tests for the admin service.

This module contains tests for the admin service functionality.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
from datetime import datetime

from src.admin.service import AdminService
from src.admin.models import SystemPrompt
from src.auth.models import User, UserRole


class TestAdminService:
    """Test suite for the AdminService class."""

    @pytest.fixture
    def mock_supabase_table(self):
        """Create a mock Supabase table utility."""
        mock_table = AsyncMock()
        mock_table.get_all.return_value = []
        mock_table.get_by_id.return_value = None
        mock_table.create.return_value = {}
        mock_table.update.return_value = {}
        mock_table.delete.return_value = True
        return mock_table

    @pytest.fixture
    def admin_service(self, mock_supabase_client, mock_supabase_table):
        """Create an admin service instance for testing."""
        with patch('src.utils.supabase_client.SupabaseTable', return_value=mock_supabase_table):
            service = AdminService(mock_supabase_client)
            return service

    @pytest.fixture
    def admin_user(self):
        """Create a sample admin user for testing."""
        return User(
            id="admin-user-id",
            email="admin@example.com",
            full_name="Admin User",
            role=UserRole.ADMIN
        )

    @pytest.fixture
    def regular_user(self):
        """Create a sample regular user for testing."""
        return User(
            id="regular-user-id",
            email="user@example.com",
            full_name="Regular User",
            role=UserRole.USER
        )

    @pytest.mark.asyncio
    async def test_create_system_prompt(self, admin_service, mock_supabase_table, admin_user):
        """Test creating a system prompt."""
        # Arrange
        name = "Test Prompt"
        content = "You are a helpful assistant."
        category = "General"
        
        # Mock the create method to return a system prompt
        mock_supabase_table.create.return_value = {
            "id": "test-prompt-id",
            "created_by": admin_user.id,
            "name": name,
            "content": content,
            "category": category,
            "is_default": False,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }
        
        # Act
        prompt = await admin_service.create_system_prompt(
            created_by=admin_user,
            name=name,
            content=content,
            category=category
        )
        
        # Assert
        assert prompt is not None
        assert prompt.id == "test-prompt-id"
        assert prompt.created_by == admin_user.id
        assert prompt.name == name
        assert prompt.content == content
        assert prompt.category == category
        assert prompt.is_default is False
        
        # Verify Supabase table was called correctly
        mock_supabase_table.create.assert_called_once()
        create_args = mock_supabase_table.create.call_args[0][0]
        assert create_args["created_by"] == admin_user.id
        assert create_args["name"] == name
        assert create_args["content"] == content
        assert create_args["category"] == category
        assert create_args["is_default"] is False

    @pytest.mark.asyncio
    async def test_create_system_prompt_non_admin(self, admin_service, mock_supabase_table, regular_user):
        """Test creating a system prompt with a non-admin user."""
        # Arrange
        name = "Test Prompt"
        content = "You are a helpful assistant."
        category = "General"
        
        # Act
        with pytest.raises(PermissionError):
            await admin_service.create_system_prompt(
                created_by=regular_user,
                name=name,
                content=content,
                category=category
            )
        
        # Assert
        mock_supabase_table.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_system_prompt(self, admin_service, mock_supabase_table):
        """Test getting a system prompt by ID."""
        # Arrange
        prompt_id = "test-prompt-id"
        
        # Mock the get_by_id method to return a system prompt
        mock_supabase_table.get_by_id.return_value = {
            "id": prompt_id,
            "created_by": "admin-user-id",
            "name": "Test Prompt",
            "content": "You are a helpful assistant.",
            "category": "General",
            "is_default": False,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }
        
        # Act
        prompt = await admin_service.get_system_prompt(prompt_id)
        
        # Assert
        assert prompt is not None
        assert prompt.id == prompt_id
        assert prompt.name == "Test Prompt"
        assert prompt.content == "You are a helpful assistant."
        
        # Verify Supabase table was called correctly
        mock_supabase_table.get_by_id.assert_called_once_with(prompt_id)

    @pytest.mark.asyncio
    async def test_get_system_prompt_not_found(self, admin_service, mock_supabase_table):
        """Test getting a non-existent system prompt."""
        # Arrange
        prompt_id = "non-existent-id"
        mock_supabase_table.get_by_id.return_value = None
        
        # Act
        prompt = await admin_service.get_system_prompt(prompt_id)
        
        # Assert
        assert prompt is None
        mock_supabase_table.get_by_id.assert_called_once_with(prompt_id)

    @pytest.mark.asyncio
    async def test_get_all_system_prompts(self, admin_service, mock_supabase_table):
        """Test getting all system prompts."""
        # Arrange
        # Mock the get_all method to return system prompts
        mock_supabase_table.get_all.return_value = [
            {
                "id": "prompt-1",
                "created_by": "admin-user-id",
                "name": "Prompt 1",
                "content": "You are a helpful assistant.",
                "category": "General",
                "is_default": True,
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z"
            },
            {
                "id": "prompt-2",
                "created_by": "admin-user-id",
                "name": "Prompt 2",
                "content": "You are a technical assistant.",
                "category": "Technical",
                "is_default": False,
                "created_at": "2023-01-02T00:00:00Z",
                "updated_at": "2023-01-02T00:00:00Z"
            }
        ]
        
        # Act
        prompts = await admin_service.get_all_system_prompts()
        
        # Assert
        assert len(prompts) == 2
        assert prompts[0].id == "prompt-1"
        assert prompts[0].name == "Prompt 1"
        assert prompts[0].is_default is True
        assert prompts[1].id == "prompt-2"
        assert prompts[1].name == "Prompt 2"
        assert prompts[1].category == "Technical"
        
        # Verify Supabase table was called correctly
        mock_supabase_table.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_system_prompts_by_category(self, admin_service, mock_supabase_table):
        """Test getting system prompts by category."""
        # Arrange
        category = "Technical"
        
        # Mock the get_all method to return system prompts
        mock_supabase_table.get_all.return_value = [
            {
                "id": "prompt-2",
                "created_by": "admin-user-id",
                "name": "Prompt 2",
                "content": "You are a technical assistant.",
                "category": "Technical",
                "is_default": False,
                "created_at": "2023-01-02T00:00:00Z",
                "updated_at": "2023-01-02T00:00:00Z"
            }
        ]
        
        # Act
        prompts = await admin_service.get_system_prompts_by_category(category)
        
        # Assert
        assert len(prompts) == 1
        assert prompts[0].id == "prompt-2"
        assert prompts[0].name == "Prompt 2"
        assert prompts[0].category == "Technical"
        
        # Verify Supabase table was called correctly
        mock_supabase_table.get_all.assert_called_once()
        query_params = mock_supabase_table.get_all.call_args[0][0]
        assert query_params["filters"][0]["column"] == "category"
        assert query_params["filters"][0]["value"] == category

    @pytest.mark.asyncio
    async def test_update_system_prompt(self, admin_service, mock_supabase_table, admin_user):
        """Test updating a system prompt."""
        # Arrange
        prompt_id = "test-prompt-id"
        new_name = "Updated Prompt"
        new_content = "You are an updated assistant."
        
        # Mock the update method to return the updated system prompt
        mock_supabase_table.update.return_value = {
            "id": prompt_id,
            "created_by": admin_user.id,
            "name": new_name,
            "content": new_content,
            "category": "General",
            "is_default": False,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-02T00:00:00Z"
        }
        
        # Act
        updated = await admin_service.update_system_prompt(
            prompt_id=prompt_id,
            updated_by=admin_user,
            name=new_name,
            content=new_content
        )
        
        # Assert
        assert updated is not None
        assert updated.id == prompt_id
        assert updated.name == new_name
        assert updated.content == new_content
        
        # Verify Supabase table was called correctly
        mock_supabase_table.update.assert_called_once()
        update_id = mock_supabase_table.update.call_args[0][0]
        update_data = mock_supabase_table.update.call_args[0][1]
        assert update_id == prompt_id
        assert update_data["name"] == new_name
        assert update_data["content"] == new_content

    @pytest.mark.asyncio
    async def test_update_system_prompt_non_admin(self, admin_service, mock_supabase_table, regular_user):
        """Test updating a system prompt with a non-admin user."""
        # Arrange
        prompt_id = "test-prompt-id"
        new_name = "Updated Prompt"
        new_content = "You are an updated assistant."
        
        # Act
        with pytest.raises(PermissionError):
            await admin_service.update_system_prompt(
                prompt_id=prompt_id,
                updated_by=regular_user,
                name=new_name,
                content=new_content
            )
        
        # Assert
        mock_supabase_table.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_system_prompt(self, admin_service, mock_supabase_table, admin_user):
        """Test deleting a system prompt."""
        # Arrange
        prompt_id = "test-prompt-id"
        mock_supabase_table.delete.return_value = True
        
        # Act
        success = await admin_service.delete_system_prompt(
            prompt_id=prompt_id,
            deleted_by=admin_user
        )
        
        # Assert
        assert success is True
        mock_supabase_table.delete.assert_called_once_with(prompt_id)

    @pytest.mark.asyncio
    async def test_delete_system_prompt_non_admin(self, admin_service, mock_supabase_table, regular_user):
        """Test deleting a system prompt with a non-admin user."""
        # Arrange
        prompt_id = "test-prompt-id"
        
        # Act
        with pytest.raises(PermissionError):
            await admin_service.delete_system_prompt(
                prompt_id=prompt_id,
                deleted_by=regular_user
            )
        
        # Assert
        mock_supabase_table.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_default_system_prompt(self, admin_service, mock_supabase_table, admin_user):
        """Test setting a system prompt as default."""
        # Arrange
        prompt_id = "test-prompt-id"
        
        # Mock the get_all method to return existing prompts
        mock_supabase_table.get_all.return_value = [
            {
                "id": "prompt-1",
                "created_by": "admin-user-id",
                "name": "Prompt 1",
                "content": "You are a helpful assistant.",
                "category": "General",
                "is_default": True,
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z"
            },
            {
                "id": prompt_id,
                "created_by": "admin-user-id",
                "name": "Test Prompt",
                "content": "You are a test assistant.",
                "category": "General",
                "is_default": False,
                "created_at": "2023-01-02T00:00:00Z",
                "updated_at": "2023-01-02T00:00:00Z"
            }
        ]
        
        # Mock the update method
        mock_supabase_table.update.return_value = {
            "id": prompt_id,
            "created_by": "admin-user-id",
            "name": "Test Prompt",
            "content": "You are a test assistant.",
            "category": "General",
            "is_default": True,
            "created_at": "2023-01-02T00:00:00Z",
            "updated_at": "2023-01-03T00:00:00Z"
        }
        
        # Act
        success = await admin_service.set_default_system_prompt(
            prompt_id=prompt_id,
            updated_by=admin_user
        )
        
        # Assert
        assert success is True
        
        # Verify Supabase table was called correctly
        # Should have been called twice - once to unset previous default, once to set new default
        assert mock_supabase_table.update.call_count == 2
        
        # First call should unset the previous default
        first_call_id = mock_supabase_table.update.call_args_list[0][0][0]
        first_call_data = mock_supabase_table.update.call_args_list[0][0][1]
        assert first_call_id == "prompt-1"
        assert first_call_data["is_default"] is False
        
        # Second call should set the new default
        second_call_id = mock_supabase_table.update.call_args_list[1][0][0]
        second_call_data = mock_supabase_table.update.call_args_list[1][0][1]
        assert second_call_id == prompt_id
        assert second_call_data["is_default"] is True

    @pytest.mark.asyncio
    async def test_set_default_system_prompt_non_admin(self, admin_service, mock_supabase_table, regular_user):
        """Test setting a system prompt as default with a non-admin user."""
        # Arrange
        prompt_id = "test-prompt-id"
        
        # Act
        with pytest.raises(PermissionError):
            await admin_service.set_default_system_prompt(
                prompt_id=prompt_id,
                updated_by=regular_user
            )
        
        # Assert
        mock_supabase_table.update.assert_not_called()