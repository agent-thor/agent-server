import uuid
from datetime import datetime
from datetime import datetime, timedelta

class APIKeyManager:
    def __init__(self, dynamo_client, table_name):
        self.dynamo = dynamo_client
        self.table_name = table_name

    def generate_api_key(self):
        # Generate a unique API key using UUID4
        return str(uuid.uuid4())

    def get_existing_api_key(self, user_id):
        result = self.dynamo.scan_table(self.table_name)
    
        if "Items" in result:
            for item in result["Items"]:
                if item.get("user_id", {}).get("N") == str(user_id):
                    return True  # User ID found
        return False  # User ID not found
    

    def create_api_key(self, user_id):
        # Check if an API key already exists for the user
        existing_key = self.get_existing_api_key(user_id)
        if existing_key:
            return f"You have an existing key for user id {user_id}"

        # Generate a new API key if none exists
        print("...Generating API Key")
        new_api_key = self.generate_api_key()
        date_created = self.dynamo.get_date()
        auto_id = self.dynamo.get_auto_increment_id('test_api_key_table')

        print("...Writing API key to DB")
        item = {
            "id": {"N": str(auto_id)},
            "user_id": {"N": str(user_id)},
            "api_key": {"S": new_api_key},
            "date_created": {"S": date_created},
            "expiration_date": {"S": (datetime.strptime(date_created, "%Y-%m-%d %H:%M:%S") + timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")},
            "is_active": {"BOOL": True}  # Set to True by default, can be modified as needed
        }

        # Add the new API key to the DynamoDB table
        response = self.dynamo.add_item(self.table_name, item)   
        print(f"...New API Key added successfully {item}")

        return new_api_key
        

