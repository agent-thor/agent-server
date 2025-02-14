from typing import List, Dict, Any

class AgentResponseParser:
    def __init__(self, dynamo_response: Dict[str, Any]):
        """
        Initialize parser with DynamoDB response
        
        Args:
            dynamo_response (Dict[str, Any]): Raw DynamoDB response containing Items
        """
        self.response = dynamo_response

    def extract_agent_names(self) -> List[str]:
        """
        Extract all agent main names from the response
        
        Returns:
            List[str]: List of agent main names
        
        Raises:
            KeyError: If response structure is invalid
            Exception: For any other unexpected errors
        """
        try:
            if 'Items' not in self.response:
                return []
                
            return [item['agent_main_name']['S'] for item in self.response['Items']]
            
        except KeyError as e:
            raise KeyError(f"Invalid response structure: {str(e)}")
        except Exception as e:
            raise Exception(f"Error extracting agent names: {str(e)}")
        
            
    def extract_agent_details(self) -> List[Dict[str, str]]:
        """
        Extract both main names and agent lists
        
        Returns:
            List[Dict[str, str]]: List of dictionaries containing agent details
        """
        if 'Items' not in self.response:
            return []
            
        return [{
            'main_name': item['agent_main_name']['S'],
            'agent_list': item['agent_list']['S']
        } for item in self.response['Items']]
    
    def get_active_agents(self) -> List[str]:
        """
        Extract names of only active agents
        
        Returns:
            List[str]: List of active agent names
        """
        if 'Items' not in self.response:
            return []
            
        return [
            item['agent_main_name']['S'] 
            for item in self.response['Items'] 
            if item.get('is_active', {}).get('BOOL', False)
        ]
    
    @property
    def agent_count(self) -> int:
        """
        Get total number of agents in response
        
        Returns:
            int: Number of agents
        """
        return len(self.response.get('Items', []))
    
    
    def get_id_agent_mapping(self) -> Dict[int, str]:
        """
        Create a dictionary mapping agent IDs to their names
        
        Returns:
            Dict[int, str]: Dictionary with ID as key and agent name as value
            
        Raises:
            KeyError: If response structure is invalid
            Exception: For any other unexpected errors
        """
        try:
            if 'Items' not in self.response:
                return {}
                
            return {
                int(item['id']['N']): item['agent_main_name']['S']
                for item in self.response['Items']
            }
            
        except KeyError as e:
            raise KeyError(f"Invalid response structure: {str(e)}")
        except ValueError as e:
            raise ValueError(f"Error converting ID to integer: {str(e)}")
        except Exception as e:
            raise Exception(f"Error creating ID-agent mapping: {str(e)}")