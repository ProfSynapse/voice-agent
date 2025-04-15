"""
Mock Helper Utilities

This module provides helper functions for working with mocks in test environments.
"""

from unittest.mock import AsyncMock, MagicMock
import inspect
import sys

def is_mock(obj):
    """
    Check if an object is a mock object.
    
    Args:
        obj: The object to check
        
    Returns:
        True if the object is a mock, False otherwise
    """
    return isinstance(obj, (AsyncMock, MagicMock))

def is_async_mock(obj):
    """
    Check if an object is an AsyncMock.
    
    Args:
        obj: The object to check
        
    Returns:
        True if the object is an AsyncMock, False otherwise
    """
    # Check if the object is an AsyncMock
    if isinstance(obj, AsyncMock):
        return True
    
    # Check if the object has an __class__ attribute and its name is AsyncMock
    if hasattr(obj, "__class__") and obj.__class__.__name__ == "AsyncMock":
        return True
    
    # Check if the object has a _mock_return_value that is a coroutine
    if hasattr(obj, "_mock_return_value") and inspect.iscoroutine(obj._mock_return_value):
        return True
    
    return False

async def execute_with_mock_handling(method, *args, **kwargs):
    """
    Execute a method with proper mock handling.
    
    This function checks if the method is an AsyncMock and handles it appropriately.
    In test environments, AsyncMock objects need to be awaited even if they're mocking
    synchronous methods.
    
    Args:
        method: The method to execute
        *args: Positional arguments to pass to the method
        **kwargs: Keyword arguments to pass to the method
        
    Returns:
        The result of the method execution
    """
    # Check if we're in a test environment
    in_test_environment = 'pytest' in sys.modules
    
    # If we're in a test environment and the method is an AsyncMock
    if in_test_environment and is_async_mock(method):
        return await method(*args, **kwargs)
    
    # If the method is a regular MagicMock (not AsyncMock)
    if is_mock(method) and not is_async_mock(method):
        return method(*args, **kwargs)
    
    # If the method is a coroutine function or an AsyncMock
    if inspect.iscoroutinefunction(method) or is_async_mock(method):
        return await method(*args, **kwargs)
    
    # Otherwise, just call the method normally
    return method(*args, **kwargs)

async def execute_supabase_with_mock_handling(supabase_query):
    """
    Execute a Supabase query with proper mock handling.
    
    This function is specifically designed to handle Supabase queries in test environments.
    It checks if the query's execute method is an AsyncMock and handles it appropriately.
    
    Args:
        supabase_query: The Supabase query to execute
        
    Returns:
        The result of the query execution
    """
    # Check if we're in a test environment
    in_test_environment = 'pytest' in sys.modules
    
    # If we're in a test environment and the query itself is a mock
    if in_test_environment and is_mock(supabase_query):
        # If the query has an execute method
        if hasattr(supabase_query, 'execute'):
            execute_method = supabase_query.execute
            
            # If execute is an AsyncMock, await it
            if is_async_mock(execute_method):
                result = await execute_method()
                return result
            # If execute is a regular MagicMock
            elif is_mock(execute_method):
                return execute_method()
        
        # If the query doesn't have an execute method but is itself an AsyncMock
        elif is_async_mock(supabase_query):
            result = await supabase_query()
            return result
        
        # If the query is a regular MagicMock
        return supabase_query
    
    # If the query doesn't have an execute method, return it as is
    if not hasattr(supabase_query, 'execute'):
        return supabase_query
    
    # Get the execute method
    execute_method = supabase_query.execute
    
    # If we're in a test environment and the execute method is an AsyncMock
    if in_test_environment and is_async_mock(execute_method):
        result = await execute_method()
        return result
    
    # If the execute method is a regular MagicMock (not AsyncMock)
    if is_mock(execute_method) and not is_async_mock(execute_method):
        return execute_method()
    
    # If the execute method is a coroutine function or an AsyncMock
    if inspect.iscoroutinefunction(execute_method) or is_async_mock(execute_method):
        return await execute_method()
    
    # Otherwise, just call the execute method normally
    return execute_method()