import requests
from typing import Dict, Any, Tuple

class AgentRouter:
    """
    A simple router that routes requests to either Eliza or Tools based on the query.
    """
    
    def __init__(self, eliza_url: str, tools_url: str):
        """
        Initialize the router with URLs for Eliza and Tools services.
        
        Args:
            eliza_url: The base URL for Eliza API
            tools_url: The base URL for Tools API
        """
        self.eliza_url = eliza_url
        self.tools_url = tools_url
        
    def route_query(self, query: str) -> Tuple[Dict[str, Any], int]:
        """
        Route the query to either Eliza or Tools based on the content.
        
        Args:
            query: The user's query text
            payload: The complete payload to send to the service
            
        Returns:
            Tuple of (response_data, status_code)
        """
        # Simple keyword check to determine where to route
        tools_keywords = ["search", "find", "weather", "crypto", "price", "bitcoin", 
                          "telegram", "message", "binance", "market"]
        
        # Check if any tool keyword is in the query
        is_tool_query = any(keyword in query.lower() for keyword in tools_keywords)
        
        # Route based on simple condition
        if is_tool_query:
            return "tools"
        else:
            return "eliza"
        
       