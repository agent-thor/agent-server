from dotenv import load_dotenv
import os

load_dotenv()

class ApiVerify:
    def __init__(self, dynamo_client, table_name):
        self.dynamo = dynamo_client
        self.table_name = table_name

    def verify(self, api_key):
        try:
            # Scan the table for the provided API key
            result = self.dynamo.scan_table(self.table_name)
            for item in result.get('Items', []):
                if item.get('api_key', {}).get('S') == api_key:
                    return True
        except Exception as e:
            print(f"Error verifying API key: {e}")
        return False
    

class AgentVerify:
    def __init__(self, dynamo_client, table_name):
        self.dynamo = dynamo_client
        self.table_name = table_name
        
    def check_agent_in_agent_list(self, multi_agent_main_name, agent_list):
        multi_agent_list = self.dynamo.extract_field(agent_list, "agent_main_name")
        print(multi_agent_list)
        print(multi_agent_main_name)
        
        if multi_agent_main_name in multi_agent_list:
            return True 
        else:
            return False        

    def verify_agent_name(self, multi_agent_main_name, api_key, multiple_agents_name):
        try:
            user_id = self.dynamo.get_userId_from_APIkey(os.getenv("API_TABLE"), api_key)
            # Scan the table for the provided API key
            key = {"user_id": {"N": str(user_id)}}
            result = self.dynamo.get_item_by_column(self.table_name, "user_id", key)
            print('------')
            print(result)
            
            if result is not None and self.check_agent_in_agent_list(multi_agent_main_name, result):
                print(f"{multi_agent_main_name} already exist.")
                
                return True   #improve here to give similarity search for already existing agents.
                    
            else: 
                return False
            
        except Exception as e:
            print(f"Error verifying agent name: {e}")
        return False, None
            
            
    def save_agent_to_db(self, multi_agent_main_name, api_key, multiple_agents_name):
        try:
            user_id = self.dynamo.get_userId_from_APIkey(os.getenv("API_TABLE"), api_key)
            date_created = self.dynamo.get_date()
            auto_id = self.dynamo.get_auto_increment_id('test_agent_table')
            item = {
                "id": {"N": str(auto_id)},
                "user_id": {"N": str(user_id)},
                "agent_main_name": {"S": multi_agent_main_name},
                "agent_list": {"S": multiple_agents_name},
                "date_created": {"S": date_created},
                "is_active": {"BOOL": True}  # Set to True by default, can be modified as needed
            }
    
            # Add the new API key to the DynamoDB table
            self.dynamo.add_item(self.table_name, item)  #response can be negative handle that 
            # print(response.json())
            print(f"...New agent added succesfully {item}")
            
    
        except Exception as e:
            print(f"Error saving agent to the DB: {e}")
        return False, None