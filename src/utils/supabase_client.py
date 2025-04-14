"""
Supabase Client Utility Module

This module provides a factory function for creating a Supabase client.
"""

import logging
from typing import Optional, Dict, Any

from supabase import create_client, Client
from loguru import logger

def create_supabase_client(
    url: str,
    anon_key: str,
    service_key: Optional[str] = None
) -> Client:
    """
    Create a Supabase client.
    
    Args:
        url: Supabase project URL
        anon_key: Supabase anonymous key
        service_key: Supabase service key (for admin operations)
        
    Returns:
        Configured Supabase client
    """
    logger.info(f"Creating Supabase client for URL: {url}")
    
    try:
        # Create the client with the anonymous key
        client = create_client(url, anon_key)
        
        # Store the service key for admin operations if provided
        if service_key:
            client.service_key = service_key
            
        logger.info("Supabase client created successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {str(e)}")
        raise


class SupabaseTable:
    """
    Utility class for working with Supabase tables.
    """
    
    def __init__(self, supabase_client: Client, table_name: str):
        """
        Initialize a Supabase table utility.
        
        Args:
            supabase_client: Supabase client
            table_name: Name of the table
        """
        self.client = supabase_client
        self.table_name = table_name
        
    async def get_all(self, query_params: Optional[Dict[str, Any]] = None) -> list:
        """
        Get all records from the table.
        
        Args:
            query_params: Optional query parameters
            
        Returns:
            List of records
        """
        query = self.client.table(self.table_name).select("*")
        
        if query_params:
            # Apply filters
            if "filters" in query_params:
                for filter_item in query_params["filters"]:
                    column = filter_item.get("column")
                    operator = filter_item.get("operator", "eq")
                    value = filter_item.get("value")
                    
                    if column and value is not None:
                        if operator == "eq":
                            query = query.eq(column, value)
                        elif operator == "neq":
                            query = query.neq(column, value)
                        elif operator == "gt":
                            query = query.gt(column, value)
                        elif operator == "gte":
                            query = query.gte(column, value)
                        elif operator == "lt":
                            query = query.lt(column, value)
                        elif operator == "lte":
                            query = query.lte(column, value)
                        elif operator == "like":
                            query = query.like(column, value)
                        elif operator == "ilike":
                            query = query.ilike(column, value)
                        elif operator == "in":
                            query = query.in_(column, value)
            
            # Apply order
            if "order" in query_params:
                for order_item in query_params["order"]:
                    column = order_item.get("column")
                    ascending = order_item.get("ascending", True)
                    
                    if column:
                        query = query.order(column, ascending=ascending)
            
            # Apply pagination
            if "limit" in query_params:
                query = query.limit(query_params["limit"])
                
            if "offset" in query_params:
                query = query.offset(query_params["offset"])
        
        response = query.execute()
        return response.data
    
    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """
        Get a record by ID.
        
        Args:
            id: Record ID
            
        Returns:
            Record data or None if not found
        """
        response = self.client.table(self.table_name).select("*").eq("id", id).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new record.
        
        Args:
            data: Record data
            
        Returns:
            Created record data
        """
        response = self.client.table(self.table_name).insert(data).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return {}
    
    async def update(self, id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a record.
        
        Args:
            id: Record ID
            data: Updated record data
            
        Returns:
            Updated record data
        """
        response = self.client.table(self.table_name).update(data).eq("id", id).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return {}
    
    async def delete(self, id: str) -> bool:
        """
        Delete a record.
        
        Args:
            id: Record ID
            
        Returns:
            True if deleted successfully, False otherwise
        """
        response = self.client.table(self.table_name).delete().eq("id", id).execute()
        return response.data is not None